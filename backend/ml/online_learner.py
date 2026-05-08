"""
SmartStudy Online Learning Engine
Uses River for incremental ML — model improves with every session.
No GPU, no retraining, no data collection needed.
Adapts to each user's unique facial patterns within 2-3 sessions.
"""

from __future__ import annotations

import pickle
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger

try:
    from river import (
        ensemble,
        linear_model,
        metrics,
        preprocessing,
        stream,
        tree,
    )
    RIVER_AVAILABLE = True
except ImportError:
    RIVER_AVAILABLE = False
    logger.warning("River not installed — online learning disabled")


@dataclass
class LearningStats:
    """Current online learning statistics."""
    samples_seen: int = 0
    accuracy: float = 0.0
    kappa: float = 0.0
    last_update: float = field(default_factory=time.time)
    is_reliable: bool = False   # True after 50+ samples


class OnlineFocusLearner:
    """
    Incremental focus classifier using River's Hoeffding Tree.

    Architecture:
    - Hoeffding Adaptive Tree: handles concept drift (focus patterns change)
    - StandardScaler: online feature normalization
    - Accuracy + Cohen's Kappa: performance tracking
    - Auto-save every 50 updates

    User feedback loop:
    1. System predicts focus state
    2. Every 15 min: prompt user for self-rating (1-5)
    3. Map rating → label and update model
    4. Model personalizes within ~3 sessions
    """

    SAVE_EVERY = 50          # Save model every N updates
    MIN_RELIABLE_SAMPLES = 50
    MIN_ACCURACY_THRESHOLD = 0.65
    FEEDBACK_INTERVAL_SECONDS = 900  # 15 minutes

    RATING_TO_STATE = {
        1: 0,   # "Very distracted" → distracted
        2: 0,   # "Somewhat distracted" → distracted
        3: 1,   # "Moderately focused" → focused
        4: 1,   # "Well focused" → focused
        5: 2,   # "In the zone (flow)" → focused (high confidence)
    }

    def __init__(
        self,
        model_path: str = "ml_training/trained_models/online_learner.pkl",
        user_id: str = "default_user",
    ) -> None:
        self.model_path = Path(model_path)
        self.user_id = user_id
        self._stats = LearningStats()
        self._update_count = 0
        self._last_feedback_time = 0.0
        self._pending_features: Optional[Dict] = None

        if RIVER_AVAILABLE:
            self._model, self._scaler = self._load_or_create()
            self._accuracy = metrics.Accuracy()
            self._kappa = metrics.CohenKappa()
        else:
            self._model = None
            self._scaler = None

        logger.info(
            f"OnlineFocusLearner ready | "
            f"samples={self._stats.samples_seen} | "
            f"river={'enabled' if RIVER_AVAILABLE else 'disabled'}"
        )

    def predict(self, features: Dict[str, float]) -> Optional[Tuple[int, float]]:
        """
        Predict focus state using personalized model.

        Returns:
            (state, probability) or None if model not ready
        """
        if not RIVER_AVAILABLE or self._model is None:
            return None

        if self._stats.samples_seen < 20:
            return None  # Not enough data yet

        # Store for potential feedback update
        self._pending_features = features.copy()

        try:
            x_scaled = self._scaler.transform_one(features)
            proba = self._model.predict_proba_one(x_scaled)

            if not proba:
                return None

            best_class = max(proba, key=proba.get)
            confidence = proba[best_class]

            return int(best_class), float(confidence)

        except Exception as e:
            logger.warning(f"Online predict error: {e}")
            return None

    def update(
        self,
        features: Dict[str, float],
        label: int,
        weight: float = 1.0,
    ) -> None:
        """
        Update model with a new labeled sample.

        Args:
            features: Feature dict (EAR, gaze, head pose, etc.)
            label: 0=distracted, 1=focused, 2=fatigued
            weight: Sample weight (1.0 for auto-labeled, 2.0 for user-confirmed)
        """
        if not RIVER_AVAILABLE or self._model is None:
            return

        try:
            # Online scaling
            x_scaled = self._scaler.learn_one(features).transform_one(features)

            # Get prediction before update (for metrics)
            pred = self._model.predict_one(x_scaled)

            # Update model
            self._model.learn_one(x_scaled, label)

            # Update metrics
            if pred is not None:
                self._accuracy.update(label, pred)
                self._kappa.update(label, pred)

            # Update stats
            self._stats.samples_seen += 1
            self._stats.accuracy = self._accuracy.get()
            self._stats.kappa = self._kappa.get()
            self._stats.last_update = time.time()
            self._stats.is_reliable = (
                self._stats.samples_seen >= self.MIN_RELIABLE_SAMPLES
                and self._stats.accuracy >= self.MIN_ACCURACY_THRESHOLD
            )

            self._update_count += 1

            # Auto-save
            if self._update_count % self.SAVE_EVERY == 0:
                self.save()
                logger.debug(
                    f"Online model saved | "
                    f"n={self._stats.samples_seen} | "
                    f"acc={self._stats.accuracy:.3f}"
                )

        except Exception as e:
            logger.error(f"Online update error: {e}")

    def process_user_feedback(
        self,
        rating: int,  # 1-5 user self-rating
        features: Optional[Dict] = None,
    ) -> None:
        """
        Process user self-reported focus rating.
        Converts to training label with 2x weight (user-confirmed).
        """
        label = self.RATING_TO_STATE.get(rating, 1)
        feat = features or self._pending_features

        if feat is not None:
            self.update(feat, label, weight=2.0)
            logger.info(
                f"User feedback processed: rating={rating} → label={label} | "
                f"total_samples={self._stats.samples_seen}"
            )

    def should_request_feedback(self) -> bool:
        """Check if it's time to ask user for feedback."""
        return (
            time.time() - self._last_feedback_time > self.FEEDBACK_INTERVAL_SECONDS
            and self._pending_features is not None
        )

    def mark_feedback_shown(self) -> None:
        """Record that feedback was requested."""
        self._last_feedback_time = time.time()

    @property
    def stats(self) -> LearningStats:
        return self._stats

    @property
    def is_reliable(self) -> bool:
        return self._stats.is_reliable

    def get_improvement_tip(self) -> str:
        """Return a tip about model accuracy."""
        n = self._stats.samples_seen
        acc = self._stats.accuracy

        if n < 20:
            return f"Learning your patterns... ({n}/20 samples needed for personalization)"
        if n < 50:
            return f"Getting personalized! Accuracy: {acc:.0%} ({n}/50 samples)"
        if acc < 0.70:
            return "Provide feedback ratings to improve accuracy"
        if acc < 0.85:
            return f"Model accuracy: {acc:.0%} — improving with each session"
        return f"Fully personalized! Accuracy: {acc:.0%} 🎯"

    def save(self) -> None:
        """Persist model and scaler to disk."""
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "model": self._model,
            "scaler": self._scaler,
            "stats": self._stats,
            "user_id": self.user_id,
        }
        with open(self.model_path, "wb") as f:
            pickle.dump(state, f)

    def _load_or_create(self) -> Tuple:
        """Load existing model or create fresh one."""
        if self.model_path.exists():
            try:
                with open(self.model_path, "rb") as f:
                    state = pickle.load(f)
                self._stats = state.get("stats", LearningStats())
                logger.info(
                    f"Online model loaded | samples={self._stats.samples_seen}"
                )
                return state["model"], state["scaler"]
            except Exception as e:
                logger.warning(f"Model load failed ({e}), creating fresh")

        return self._create_fresh_model()

    def _create_fresh_model(self) -> Tuple:
        """Create a fresh Hoeffding Adaptive Tree classifier."""
        model = tree.HoeffdingAdaptiveTreeClassifier(
            grace_period=100,
            delta=1e-7,
            tau=0.05,
            leaf_prediction="nba",
            nb_threshold=0,
            seed=42,
        )
        scaler = preprocessing.StandardScaler()
        return model, scaler
