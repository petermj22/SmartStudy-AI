"""
Module: inference_engine.py
Purpose: Real-time inference pipeline orchestrating CV, ML, and alert systems.
         Processes frames end-to-end in <100ms with temporal smoothing.
Author: SmartStudy Team
Version: 1.0.0
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional

import cv2
import numpy as np
from loguru import logger

from backend.vision.face_detector import FaceDetector
from backend.vision.feature_extractor import FeatureExtractor, FaceFeatures
from backend.vision.blink_detector import BlinkDetector
from backend.vision.gaze_tracker import GazeTracker
from backend.ml.ensemble_classifier import EnsembleClassifier, ClassificationResult
from backend.ml.lstm_predictor import LSTMPredictor, FatiguePrediction
from backend.ml.feature_buffer import FeatureBuffer
from backend.ml.kalman_fusion import KalmanFocusFusion


@dataclass
class Alert:
    """Real-time alert triggered by the inference engine."""
    type: str           # "microsleep", "yawn", "looking_away", "eye_strain", "fatigue"
    severity: str       # "info", "warning", "critical"
    message: str
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class InferenceResult:
    """Complete result from a single frame inference."""

    # Face detection
    face_detected: bool = False

    # Features
    features: Optional[FaceFeatures] = None

    # Classification
    focus_state: int = 1                       # 0/1/2
    focus_label: str = "focused"
    focus_confidence: float = 0.5

    # Fatigue
    fatigue_score: float = 0.0
    fatigue_level: str = "low"
    minutes_until_break: float = 25.0
    recommended_break_duration: float = 5.0

    # Smoothed state (temporal median)
    smoothed_focus_state: int = 1
    smoothed_focus_label: str = "focused"
    attention_score: float = 1.0

    # Alerts
    alerts: List[Alert] = field(default_factory=list)

    # Performance
    total_inference_ms: float = 0.0
    frame_number: int = 0
    timestamp: float = 0.0


class InferenceEngine:
    """
    Real-time inference pipeline.

    Pipeline: Frame → RGB → FaceMesh → Features → ML → Smooth → Alerts

    Features:
    - Frame skipping for performance on slower hardware
    - Temporal smoothing (median filter) to reduce flickering
    - Rule-based safety alerts as ML complement
    - Configurable alert thresholds
    """

    def __init__(
        self,
        smoothing_window: int = 15,
        frame_skip: int = 1,
        feature_buffer_size: int = 900,
        calibration: Optional[Dict] = None,
    ) -> None:
        # Vision components
        self._face_detector = FaceDetector()
        self._feature_extractor = FeatureExtractor(self._face_detector)
        self._blink_detector = BlinkDetector()
        self._gaze_tracker = GazeTracker()

        # ML components
        self._classifier = EnsembleClassifier()
        self._lstm_predictor = LSTMPredictor()
        self._feature_buffer = FeatureBuffer(max_size=feature_buffer_size)

        # Kalman focus fusion (multi-signal Bayesian estimator)
        self._kalman = KalmanFocusFusion(calibration=calibration)

        # Temporal smoothing
        self._smoothing_window = smoothing_window
        self._state_history: Deque[int] = deque(maxlen=smoothing_window)
        self._confidence_history: Deque[float] = deque(maxlen=smoothing_window)

        # Frame skipping
        self._frame_skip = frame_skip
        self._frame_count = 0
        self._last_result: Optional[InferenceResult] = None

        # Session context
        self._session_start_time: float = time.time()
        self._last_break_time: float = time.time()

        # Alert state
        self._consecutive_looking_away: int = 0
        self._consecutive_eyes_closed: int = 0
        self._yawn_cooldown: float = 0.0

        # Performance tracking
        self._ear_history: Deque[float] = deque(maxlen=300)

        logger.info("InferenceEngine initialized")

    def process_frame(self, bgr_frame: np.ndarray) -> InferenceResult:
        """
        Process a single BGR frame through the full pipeline.

        Args:
            bgr_frame: Input frame in BGR format (from OpenCV)

        Returns:
            InferenceResult with all analysis data
        """
        t0 = time.perf_counter()
        self._frame_count += 1

        # Frame skipping
        if self._frame_skip > 1 and self._frame_count % self._frame_skip != 0:
            if self._last_result is not None:
                return self._last_result
            return InferenceResult(frame_number=self._frame_count)

        result = InferenceResult(
            frame_number=self._frame_count,
            timestamp=time.time(),
        )

        # 1. Convert to RGB
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)

        # 2. Face detection + landmarks
        detection = self._face_detector.detect(rgb_frame)
        result.face_detected = detection.detected

        if not detection.detected:
            self._consecutive_looking_away += 1
            result.focus_state = 0
            result.focus_label = "no_face"
            result.attention_score = 0.0
            result.total_inference_ms = (time.perf_counter() - t0) * 1000
            self._last_result = result
            return result

        self._consecutive_looking_away = 0

        # 3. Feature extraction
        features = self._feature_extractor.extract(detection)
        if features is None:
            result.total_inference_ms = (time.perf_counter() - t0) * 1000
            self._last_result = result
            return result

        # 4. Update blink detector
        blink_stats = self._blink_detector.update(features.avg_ear, self._frame_count)
        features.blink_rate = blink_stats.blink_rate_per_minute
        features.blink_duration_avg = blink_stats.avg_blink_duration
        features.eye_closure_ratio = float(blink_stats.is_eyes_closed)

        # 5. Update gaze tracker
        gaze = self._gaze_tracker.update(features.gaze_x, features.gaze_y)
        features.gaze_stability = gaze.stability

        # 6. Add temporal/session context
        now = time.time()
        features.time_of_day = datetime.now().hour + datetime.now().minute / 60.0
        features.session_duration = (now - self._session_start_time) / 60.0
        features.time_since_break = (now - self._last_break_time) / 60.0

        # 7. Update EAR history and compute temporal features
        self._ear_history.append(features.avg_ear)
        ear_arr = np.array(self._ear_history)
        features.ear_mean = float(np.mean(ear_arr))
        features.ear_std = float(np.std(ear_arr))
        if len(ear_arr) >= 10:
            x = np.arange(len(ear_arr[-30:]), dtype=np.float64)
            y = ear_arr[-30:]
            if len(x) == len(y) and len(x) >= 2:
                coeffs = np.polyfit(x, y, 1)
                features.ear_trend = float(coeffs[0])

        # 8. Compute head movement from buffer
        temporal = self._feature_buffer.compute_temporal_features(window=30)
        features.head_movement_magnitude = temporal.get("head_movement_magnitude", 0.0)
        features.head_stability = temporal.get("head_stability", 1.0)

        # 9. Store features in buffer
        feature_dict = features.to_dict()
        self._feature_buffer.add(feature_dict)

        result.features = features

        # 10. ML Classification
        classification = self._classifier.predict(feature_dict)
        result.focus_state = classification.predicted_class
        result.focus_label = classification.class_label
        result.focus_confidence = classification.confidence

        # 10b. Kalman-enhanced multi-signal fusion
        focused_ratio = sum(1 for s in self._state_history if s == 1) / max(len(self._state_history), 1)
        ml_attention = focused_ratio * 100
        try:
            fusion = self._kalman.update(
                ear=features.avg_ear,
                blink_rate=features.blink_rate,
                head_yaw=features.head_yaw,
                head_pitch=features.head_pitch,
                gaze_stability=features.gaze_stability,
                mar=features.mar,
                brow_raise=getattr(features, 'brow_raise', 0.0),
                attention_score_ml=ml_attention,
            )
            # Override with Kalman-fused state (more accurate)
            result.focus_state = fusion.predicted_state
            result.focus_label = EnsembleClassifier.CLASS_LABELS.get(fusion.predicted_state, "unknown")
            result.focus_confidence = fusion.confidence
        except Exception:
            pass  # Fallback to ensemble classification

        # 11. Temporal smoothing (median filter)
        self._state_history.append(result.focus_state)
        self._confidence_history.append(result.focus_confidence)

        if len(self._state_history) >= 5:
            states = list(self._state_history)
            result.smoothed_focus_state = int(np.median(states))
            result.smoothed_focus_label = EnsembleClassifier.CLASS_LABELS.get(
                result.smoothed_focus_state, "unknown"
            )
        else:
            result.smoothed_focus_state = result.focus_state
            result.smoothed_focus_label = result.focus_label

        # 12. Compute attention score (0-1)
        focused_ratio = sum(1 for s in self._state_history if s == 1) / max(len(self._state_history), 1)
        result.attention_score = focused_ratio

        # 13. LSTM Fatigue prediction
        sequence = self._feature_buffer.get_sequence(
            self._lstm_predictor.temporal_features,
            self._lstm_predictor.sequence_length,
        )
        fatigue = self._lstm_predictor.predict(
            sequence=sequence,
            session_duration_minutes=features.session_duration,
            current_ear=features.avg_ear,
            current_blink_rate=features.blink_rate,
            time_since_break_minutes=features.time_since_break,
        )
        result.fatigue_score = fatigue.fatigue_score
        result.fatigue_level = fatigue.fatigue_level
        result.minutes_until_break = fatigue.minutes_until_break
        result.recommended_break_duration = fatigue.recommended_break_duration
        features.cumulative_fatigue_score = fatigue.fatigue_score

        # 14. Rule-based alerts
        result.alerts = self._check_alerts(features, blink_stats, fatigue)

        result.total_inference_ms = (time.perf_counter() - t0) * 1000
        self._last_result = result
        return result

    def _check_alerts(
        self, features: FaceFeatures, blink_stats: Any, fatigue: FatiguePrediction,
    ) -> List[Alert]:
        """Generate rule-based safety alerts."""
        alerts = []

        # Microsleep detection
        if blink_stats.is_microsleep:
            alerts.append(Alert(
                type="microsleep", severity="critical",
                message="⚠️ Microsleep detected! Consider a break immediately.",
            ))

        # Yawn detection (with cooldown)
        if features.yawn_detected and time.time() > self._yawn_cooldown:
            alerts.append(Alert(
                type="yawn", severity="warning",
                message="😴 Yawn detected — you might be getting tired.",
            ))
            self._yawn_cooldown = time.time() + 30  # 30s cooldown

        # Looking away too long
        if abs(features.head_yaw) > 30:
            self._consecutive_looking_away += 1
            if self._consecutive_looking_away > 300:  # 10s at 30fps
                alerts.append(Alert(
                    type="looking_away", severity="info",
                    message="👀 You've been looking away for a while.",
                ))
        else:
            self._consecutive_looking_away = 0

        # High blink rate (eye strain)
        if features.blink_rate > 30:
            alerts.append(Alert(
                type="eye_strain", severity="warning",
                message="👁️ High blink rate — consider the 20-20-20 rule.",
            ))

        # Fatigue-based break recommendation
        if fatigue.fatigue_score > 0.7:
            alerts.append(Alert(
                type="fatigue", severity="warning",
                message=f"🧠 Fatigue level high — break recommended in {fatigue.minutes_until_break:.0f} min.",
            ))

        return alerts

    def reset_session(self) -> None:
        """Reset all state for a new session."""
        self._session_start_time = time.time()
        self._last_break_time = time.time()
        self._blink_detector.reset()
        self._gaze_tracker.reset()
        self._feature_buffer.clear()
        self._state_history.clear()
        self._confidence_history.clear()
        self._ear_history.clear()
        self._kalman.reset()
        self._frame_count = 0
        self._last_result = None
        self._consecutive_looking_away = 0
        self._consecutive_eyes_closed = 0
        self._yawn_cooldown = 0.0
        logger.info("InferenceEngine reset for new session")

    def record_break(self) -> None:
        """Record that a break was taken."""
        self._last_break_time = time.time()

    def close(self) -> None:
        """Release all resources."""
        self._face_detector.close()
        logger.info("InferenceEngine closed")
