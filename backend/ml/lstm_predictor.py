"""
Module: lstm_predictor.py
Purpose: LSTM-based fatigue prediction with TFLite optimization.
         Predicts fatigue 5 minutes ahead for proactive break recommendations.
Author: SmartStudy Team
Version: 1.0.0
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger

from backend.ml.model_loader import ModelLoader


@dataclass
class FatiguePrediction:
    """Result from LSTM fatigue prediction."""

    fatigue_score: float = 0.0
    fatigue_level: str = "low"
    minutes_until_break: float = 25.0
    recommended_break_duration: float = 5.0
    confidence: float = 0.5
    inference_time_ms: float = 0.0


class LSTMPredictor:
    """
    LSTM-based fatigue predictor.

    Uses a sequence of temporal features to predict fatigue score
    and recommend optimal break timing.

    Falls back to exponential fatigue model when no trained LSTM available.
    """

    FATIGUE_THRESHOLDS = {"low": 0.3, "moderate": 0.6, "high": 0.8}
    BREAK_TIMING = {
        "low": 25.0, "moderate": 15.0, "high": 5.0, "critical": 0.0,
    }
    BREAK_DURATION = {"low": 5.0, "moderate": 10.0, "high": 15.0}

    def __init__(
        self,
        model_loader: Optional[ModelLoader] = None,
        version: str = "v1.0",
        sequence_length: int = 300,
    ) -> None:
        self._loader = model_loader or ModelLoader()
        self._version = version
        self.sequence_length = sequence_length

        self._model: Optional[Any] = None
        self._tflite_interpreter: Optional[Any] = None
        self._temporal_features: List[str] = self._loader.get_lstm_features()
        self._model_loaded: bool = False

        self._load_model()

    def _load_model(self) -> None:
        """Attempt to load LSTM model (TFLite preferred, then Keras)."""
        # Try TFLite first (faster inference)
        tflite_path = self._loader.models_dir / f"lstm_fatigue_{self._version}.tflite"
        if tflite_path.exists():
            try:
                import tensorflow as tf
                self._tflite_interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
                self._tflite_interpreter.allocate_tensors()
                self._model_loaded = True
                logger.info(f"LSTM TFLite model loaded: {tflite_path}")
                return
            except Exception as e:
                logger.warning(f"TFLite load failed: {e}")

        # Try Keras model
        keras_path = self._loader.models_dir / f"lstm_fatigue_{self._version}.h5"
        if keras_path.exists():
            try:
                import tensorflow as tf
                self._model = tf.keras.models.load_model(str(keras_path))
                self._model_loaded = True
                logger.info(f"LSTM Keras model loaded: {keras_path}")
                return
            except Exception as e:
                logger.warning(f"Keras model load failed: {e}")

        logger.warning(
            "No LSTM model found — using exponential fatigue fallback. "
            "Train with: python ml_training/train_lstm.py"
        )

    def predict(
        self,
        sequence: Optional[np.ndarray] = None,
        session_duration_minutes: float = 0.0,
        current_ear: float = 0.3,
        current_blink_rate: float = 15.0,
        time_since_break_minutes: float = 0.0,
    ) -> FatiguePrediction:
        """
        Predict fatigue from temporal sequence or current metrics.

        Args:
            sequence: np.ndarray of shape (seq_len, n_features) or None
            session_duration_minutes: How long the session has been active
            current_ear: Current Eye Aspect Ratio
            current_blink_rate: Current blinks per minute
            time_since_break_minutes: Minutes since last break

        Returns:
            FatiguePrediction with score and break recommendations
        """
        t0 = time.perf_counter()

        if self._model_loaded and sequence is not None:
            prediction = self._model_predict(sequence)
        else:
            prediction = self._exponential_fallback(
                session_duration_minutes, current_ear,
                current_blink_rate, time_since_break_minutes,
            )

        prediction.inference_time_ms = (time.perf_counter() - t0) * 1000
        return prediction

    def _model_predict(self, sequence: np.ndarray) -> FatiguePrediction:
        """Run LSTM model inference."""
        try:
            input_data = sequence.reshape(1, sequence.shape[0], sequence.shape[1]).astype(np.float32)

            if self._tflite_interpreter is not None:
                input_details = self._tflite_interpreter.get_input_details()
                output_details = self._tflite_interpreter.get_output_details()

                # Resize if needed
                if input_data.shape != tuple(input_details[0]["shape"]):
                    self._tflite_interpreter.resize_tensor_input(
                        input_details[0]["index"], list(input_data.shape)
                    )
                    self._tflite_interpreter.allocate_tensors()

                self._tflite_interpreter.set_tensor(input_details[0]["index"], input_data)
                self._tflite_interpreter.invoke()
                fatigue_score = float(
                    self._tflite_interpreter.get_tensor(output_details[0]["index"])[0][0]
                )
            elif self._model is not None:
                output = self._model.predict(input_data, verbose=0)
                fatigue_score = float(output[0][0])
            else:
                return self._exponential_fallback(0, 0.3, 15.0, 0)

            fatigue_score = float(np.clip(fatigue_score, 0, 1))
            return self._score_to_prediction(fatigue_score, confidence=0.8)

        except Exception as e:
            logger.warning(f"LSTM prediction error: {e}")
            return self._exponential_fallback(0, 0.3, 15.0, 0)

    def _exponential_fallback(
        self,
        session_minutes: float,
        ear: float,
        blink_rate: float,
        time_since_break: float,
    ) -> FatiguePrediction:
        """
        Exponential fatigue model fallback.
        Models cognitive fatigue as an exponential function of study duration,
        modulated by physiological signals.
        """
        # Base fatigue from time (exponential growth)
        time_factor = 1.0 - np.exp(-time_since_break / 30.0)

        # Physiological modifiers
        ear_factor = max(0, (0.3 - ear) / 0.1) if ear < 0.3 else 0
        blink_factor = max(0, (blink_rate - 20) / 20) if blink_rate > 20 else 0

        # Weighted combination
        fatigue_score = float(np.clip(
            0.5 * time_factor + 0.3 * ear_factor + 0.2 * blink_factor,
            0, 1,
        ))

        return self._score_to_prediction(fatigue_score, confidence=0.5)

    def _score_to_prediction(
        self, score: float, confidence: float,
    ) -> FatiguePrediction:
        """Convert fatigue score to full prediction with recommendations."""
        if score >= self.FATIGUE_THRESHOLDS["high"]:
            level = "high"
        elif score >= self.FATIGUE_THRESHOLDS["moderate"]:
            level = "moderate"
        else:
            level = "low"

        return FatiguePrediction(
            fatigue_score=score,
            fatigue_level=level,
            minutes_until_break=self.BREAK_TIMING.get(level, 25.0),
            recommended_break_duration=self.BREAK_DURATION.get(level, 5.0),
            confidence=confidence,
        )

    @property
    def is_loaded(self) -> bool:
        return self._model_loaded

    @property
    def temporal_features(self) -> List[str]:
        return self._temporal_features
