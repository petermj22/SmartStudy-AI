"""
Unit Tests: Database operations, ML models, and vision components.
"""

import json

import numpy as np
import pytest


class TestDatabaseManager:
    """Tests for DatabaseManager CRUD operations."""

    def test_default_user_exists(self, db_manager):
        user = db_manager.get_user()
        assert user is not None
        assert user.id == "default_user"
        assert user.name == "Student"

    def test_create_session(self, db_manager):
        session = db_manager.create_session(subject="Physics", tags=["midterm"])
        assert session is not None
        assert session.subject == "Physics"
        assert session.is_active

    def test_end_session(self, db_manager):
        session = db_manager.create_session(subject="Math")
        result = db_manager.end_session(session.id, {
            "focus_percentage": 75.5,
            "distraction_count": 3,
        })
        assert result is not None
        assert result.end_time is not None
        assert result.focus_percentage == 75.5

    def test_add_frame_sample(self, db_manager, sample_session):
        db_manager.add_frame_sample(sample_session.id, {
            "frame_number": 1,
            "focus_state": 1,
            "confidence": 0.85,
            "ear": 0.28,
        })
        frames = db_manager.get_session_frames(sample_session.id)
        assert len(frames) == 1
        assert frames[0]["focus_state"] == 1

    def test_break_operations(self, db_manager, sample_session):
        break_id = db_manager.record_break_start(
            sample_session.id, break_type="manual",
        )
        assert break_id is not None

        db_manager.record_break_end(break_id)

    def test_update_preferences(self, db_manager):
        prefs = {"break_interval": 30, "sound": False}
        result = db_manager.update_user_preferences(prefs)
        assert result is True

        user = db_manager.get_user()
        loaded_prefs = user.get_preferences()
        assert loaded_prefs["break_interval"] == 30

    def test_get_recent_sessions(self, db_manager):
        db_manager.create_session(subject="English")
        db_manager.create_session(subject="History")
        # Sessions are still active (no end_time), so recent completed = 0
        recent = db_manager.get_recent_sessions(limit=5)
        assert isinstance(recent, list)


class TestFeatureBuffer:
    """Tests for FeatureBuffer."""

    def test_add_and_size(self, feature_buffer):
        assert feature_buffer.size == 50

    def test_get_recent(self, feature_buffer):
        recent = feature_buffer.get_recent(10)
        assert len(recent) == 10

    def test_get_sequence(self, feature_buffer):
        seq = feature_buffer.get_sequence(["avg_ear", "mar"], length=30)
        assert seq is not None
        assert seq.shape == (30, 2)

    def test_compute_stats(self, feature_buffer):
        stats = feature_buffer.compute_stats("avg_ear", window=20)
        assert stats.count == 20
        assert stats.mean > 0
        assert stats.std >= 0

    def test_temporal_features(self, feature_buffer):
        temporal = feature_buffer.compute_temporal_features(window=20)
        assert "avg_ear_mean" in temporal
        assert "head_movement_magnitude" in temporal

    def test_max_size_limit(self):
        from backend.ml.feature_buffer import FeatureBuffer
        buf = FeatureBuffer(max_size=5)
        for i in range(10):
            buf.add({"val": i})
        assert buf.size == 5


class TestEnsembleClassifier:
    """Tests for EnsembleClassifier (rule-based fallback)."""

    def test_predict_returns_result(self, feature_dict):
        from backend.ml.ensemble_classifier import EnsembleClassifier
        classifier = EnsembleClassifier()
        result = classifier.predict(feature_dict)
        assert result.predicted_class in [0, 1, 2]
        assert result.class_label in ["distracted", "focused", "fatigued"]
        assert 0 <= result.confidence <= 1
        assert result.inference_time_ms >= 0

    def test_rule_based_focused(self):
        from backend.ml.ensemble_classifier import EnsembleClassifier
        classifier = EnsembleClassifier()
        features = {
            "avg_ear": 0.30, "mar": 0.3, "head_yaw": 5.0,
            "head_pitch": 0.0, "gaze_stability": 0.9,
            "blink_rate": 15.0, "yawn_detected": 0.0,
        }
        result = classifier._rule_based_predict(features)
        assert result.class_label == "focused"

    def test_rule_based_fatigued(self):
        from backend.ml.ensemble_classifier import EnsembleClassifier
        classifier = EnsembleClassifier()
        features = {
            "avg_ear": 0.18, "mar": 0.7, "head_yaw": 5.0,
            "head_pitch": 0.0, "gaze_stability": 0.5,
            "blink_rate": 30.0, "yawn_detected": 1.0,
        }
        result = classifier._rule_based_predict(features)
        assert result.class_label == "fatigued"

    def test_rule_based_distracted(self):
        from backend.ml.ensemble_classifier import EnsembleClassifier
        classifier = EnsembleClassifier()
        features = {
            "avg_ear": 0.30, "mar": 0.3, "head_yaw": 40.0,
            "head_pitch": 0.0, "gaze_stability": 0.2,
            "blink_rate": 15.0, "yawn_detected": 0.0,
        }
        result = classifier._rule_based_predict(features)
        assert result.class_label == "distracted"


class TestLSTMPredictor:
    """Tests for LSTMPredictor (fallback mode)."""

    def test_exponential_fallback(self):
        from backend.ml.lstm_predictor import LSTMPredictor
        predictor = LSTMPredictor()
        result = predictor.predict(
            session_duration_minutes=30,
            current_ear=0.22,
            current_blink_rate=25,
            time_since_break_minutes=25,
        )
        assert 0 <= result.fatigue_score <= 1
        assert result.fatigue_level in ["low", "moderate", "high"]
        assert result.minutes_until_break >= 0
        assert result.recommended_break_duration > 0

    def test_low_fatigue(self):
        from backend.ml.lstm_predictor import LSTMPredictor
        predictor = LSTMPredictor()
        result = predictor.predict(
            session_duration_minutes=5,
            current_ear=0.32,
            current_blink_rate=14,
            time_since_break_minutes=5,
        )
        assert result.fatigue_level == "low"


class TestBlinkDetector:
    """Tests for BlinkDetector."""

    def test_no_blink(self):
        from backend.vision.blink_detector import BlinkDetector
        detector = BlinkDetector()
        result = detector.update(ear=0.30, frame_number=1)
        assert result.blink_detected is False
        assert result.total_blinks == 0

    def test_blink_detection(self):
        from backend.vision.blink_detector import BlinkDetector
        detector = BlinkDetector(ear_threshold=0.21, consecutive_frames_for_blink=3)

        # Eyes open
        for i in range(5):
            detector.update(0.30, i)

        # Eyes closed for 5 frames
        for i in range(5, 10):
            detector.update(0.18, i)

        # Eyes open — blink should be detected
        result = detector.update(0.30, 10)
        assert result.blink_detected is True
        assert detector.total_blinks == 1

    def test_reset(self):
        from backend.vision.blink_detector import BlinkDetector
        detector = BlinkDetector()
        detector.update(0.18, 1)
        detector.reset()
        assert detector.total_blinks == 0


class TestGazeTracker:
    """Tests for GazeTracker."""

    def test_center_gaze(self):
        from backend.vision.gaze_tracker import GazeTracker
        tracker = GazeTracker()
        result = tracker.update(0.0, 0.0)
        assert result.direction_label == "center"
        assert result.is_on_screen

    def test_stability(self):
        from backend.vision.gaze_tracker import GazeTracker
        tracker = GazeTracker()
        for _ in range(20):
            tracker.update(0.01, 0.01)
        stability = tracker.get_stability()
        assert stability > 0.9

    def test_unstable_gaze(self):
        from backend.vision.gaze_tracker import GazeTracker
        tracker = GazeTracker()
        import random
        for _ in range(30):
            tracker.update(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5))
        stability = tracker.get_stability()
        assert stability < 0.8


class TestAutoLabeler:
    """Tests for AutoLabeler."""

    def test_focused_label(self):
        from backend.data.auto_labeler import AutoLabeler
        labeler = AutoLabeler()
        features = {
            "avg_ear": 0.30, "head_yaw": 5.0, "head_pitch": 0.0,
            "gaze_stability": 0.8, "mar": 0.3, "blink_rate": 15.0,
            "yawn_detected": 0.0,
        }
        label = labeler.label_frame(features)
        assert label == 1

    def test_fatigued_label(self):
        from backend.data.auto_labeler import AutoLabeler
        labeler = AutoLabeler()
        features = {
            "avg_ear": 0.20, "head_yaw": 5.0, "head_pitch": 0.0,
            "gaze_stability": 0.5, "mar": 0.7, "blink_rate": 30.0,
            "yawn_detected": 1.0,
        }
        label = labeler.label_frame(features)
        assert label == 2
