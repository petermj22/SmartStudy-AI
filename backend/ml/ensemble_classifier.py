"""
Module: ensemble_classifier.py
Purpose: Production ensemble classifier (RF + XGBoost + LightGBM)
         for real-time focus state classification.
Author: SmartStudy Team
Version: 1.0.0

Dependencies:
    - scikit-learn>=1.3.2
    - xgboost>=2.0.2
    - lightgbm>=4.1.0
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

from backend.ml.model_loader import ModelLoader


@dataclass
class ClassificationResult:
    """Result from ensemble classification."""

    predicted_class: int = 1          # 0=distracted, 1=focused, 2=fatigued
    class_label: str = "focused"
    confidence: float = 0.5
    probabilities: Dict[str, float] = None
    individual_predictions: Dict[str, int] = None
    inference_time_ms: float = 0.0

    def __post_init__(self):
        if self.probabilities is None:
            self.probabilities = {"distracted": 0.0, "focused": 1.0, "fatigued": 0.0}
        if self.individual_predictions is None:
            self.individual_predictions = {}


class EnsembleClassifier:
    """
    Production ensemble classifier using weighted soft voting
    across Random Forest, XGBoost, and LightGBM.

    Features:
    - Graceful degradation if any model unavailable
    - Configurable weights from model_config.yaml
    - Rule-based fallback when no models trained
    - Smoothing via temporal median filter
    """

    CLASS_LABELS = {0: "distracted", 1: "focused", 2: "fatigued"}

    def __init__(
        self,
        model_loader: Optional[ModelLoader] = None,
        version: str = "v1.0",
    ) -> None:
        self._loader = model_loader or ModelLoader()
        self._version = version

        self._rf_model: Optional[Any] = None
        self._xgb_model: Optional[Any] = None
        self._lgb_model: Optional[Any] = None

        self._feature_columns: List[str] = self._loader.get_feature_columns()
        self._weights: Dict[str, float] = self._loader.get_ensemble_weights()
        self._models_loaded: bool = False

        self._load_models()

    def _load_models(self) -> None:
        """Attempt to load all three ensemble models."""
        self._rf_model = self._loader.load_model("random_forest", self._version)
        self._xgb_model = self._loader.load_model("xgboost", self._version)
        self._lgb_model = self._loader.load_model("lightgbm", self._version)

        loaded = sum(1 for m in [self._rf_model, self._xgb_model, self._lgb_model] if m is not None)
        self._models_loaded = loaded > 0

        if self._models_loaded:
            logger.info(f"Ensemble classifier: {loaded}/3 models loaded")
        else:
            logger.warning(
                "No trained models found — using rule-based fallback. "
                "Train models with: python ml_training/train_ensemble.py"
            )

    def predict(self, features: Dict[str, float]) -> ClassificationResult:
        """
        Predict focus state from feature dict.

        Args:
            features: Dict of feature_name -> value

        Returns:
            ClassificationResult with class, confidence, and probabilities
        """
        t0 = time.perf_counter()

        if not self._models_loaded:
            result = self._rule_based_predict(features)
            result.inference_time_ms = (time.perf_counter() - t0) * 1000
            return result

        # Build feature vector in correct column order
        feature_vector = np.array(
            [features.get(col, 0.0) for col in self._feature_columns],
            dtype=np.float32,
        ).reshape(1, -1)

        # Collect probability predictions from available models
        all_probs = []
        weights = []
        individual_preds = {}

        for name, model, weight_key in [
            ("random_forest", self._rf_model, "random_forest"),
            ("xgboost", self._xgb_model, "xgboost"),
            ("lightgbm", self._lgb_model, "lightgbm"),
        ]:
            if model is not None:
                try:
                    probs = model.predict_proba(feature_vector)[0]
                    # Ensure we have 3 classes
                    if len(probs) == 2:
                        probs = np.array([probs[0], probs[1], 0.0])
                    elif len(probs) == 1:
                        probs = np.array([0.0, probs[0], 0.0])

                    all_probs.append(probs)
                    weights.append(self._weights.get(weight_key, 0.33))
                    individual_preds[name] = int(np.argmax(probs))
                except Exception as e:
                    logger.warning(f"Model {name} prediction error: {e}")

        if not all_probs:
            result = self._rule_based_predict(features)
            result.inference_time_ms = (time.perf_counter() - t0) * 1000
            return result

        # Weighted average of probabilities (soft voting)
        weights_arr = np.array(weights)
        weights_arr = weights_arr / weights_arr.sum()
        probs_stack = np.array(all_probs)
        combined_probs = np.average(probs_stack, axis=0, weights=weights_arr)

        predicted_class = int(np.argmax(combined_probs))
        confidence = float(combined_probs[predicted_class])
        class_label = self.CLASS_LABELS.get(predicted_class, "unknown")

        result = ClassificationResult(
            predicted_class=predicted_class,
            class_label=class_label,
            confidence=confidence,
            probabilities={
                "distracted": float(combined_probs[0]),
                "focused": float(combined_probs[1]) if len(combined_probs) > 1 else 0.0,
                "fatigued": float(combined_probs[2]) if len(combined_probs) > 2 else 0.0,
            },
            individual_predictions=individual_preds,
            inference_time_ms=(time.perf_counter() - t0) * 1000,
        )

        return result

    def _rule_based_predict(self, features: Dict[str, float]) -> ClassificationResult:
        """
        Rule-based focus classification fallback.
        Uses physiological thresholds when no ML models are available.
        """
        ear = features.get("avg_ear", 0.3)
        mar = features.get("mar", 0.3)
        head_yaw = abs(features.get("head_yaw", 0.0))
        head_pitch = features.get("head_pitch", 0.0)
        gaze_stability = features.get("gaze_stability", 1.0)
        blink_rate = features.get("blink_rate", 15.0)
        yawn = features.get("yawn_detected", 0.0)

        # Fatigue indicators
        fatigue_score = 0.0
        if ear < 0.25:
            fatigue_score += 0.3
        if ear < 0.21:
            fatigue_score += 0.4
        if blink_rate > 25:
            fatigue_score += 0.2
        if yawn > 0:
            fatigue_score += 0.3

        # Distraction indicators
        distraction_score = 0.0
        if head_yaw > 30:
            distraction_score += 0.4
        if head_yaw > 20:
            distraction_score += 0.2
        if gaze_stability < 0.5:
            distraction_score += 0.3
        if head_pitch < -20:
            distraction_score += 0.2

        # Classify
        if fatigue_score > 0.6:
            predicted = 2
            label = "fatigued"
            conf = min(fatigue_score, 1.0)
        elif distraction_score > 0.5:
            predicted = 0
            label = "distracted"
            conf = min(distraction_score, 1.0)
        else:
            predicted = 1
            label = "focused"
            conf = max(0.5, 1.0 - fatigue_score - distraction_score)

        return ClassificationResult(
            predicted_class=predicted,
            class_label=label,
            confidence=conf,
            probabilities={
                "distracted": distraction_score,
                "focused": max(0, 1.0 - fatigue_score - distraction_score),
                "fatigued": fatigue_score,
            },
            individual_predictions={"rule_engine": predicted},
        )

    @property
    def is_loaded(self) -> bool:
        return self._models_loaded

    @property
    def feature_columns(self) -> List[str]:
        return self._feature_columns
