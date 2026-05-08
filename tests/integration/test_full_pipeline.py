"""
SmartStudy — Integration Tests
Tests for full pipeline interactions between modules.
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ─────────────────────────────────────────────────────
# Database + Analytics Integration
# ─────────────────────────────────────────────────────


class TestDatabaseAnalyticsIntegration:
    """Test analytics queries against real database."""

    def test_session_create_and_retrieve(self, db_manager):
        """Create session, end it, and verify retrieval."""
        session = db_manager.create_session(subject="Math", tags=["exam"])
        assert session.id is not None
        assert session.subject == "Math"

        metrics = {
            "focus_percentage": 75.0,
            "avg_attention_score": 0.8,
            "distraction_count": 5,
            "fatigue_events": 2,
            "break_count": 1,
            "focused_seconds": 1200.0,
            "distracted_seconds": 300.0,
            "fatigued_seconds": 100.0,
        }
        ended = db_manager.end_session(session.id, metrics)
        assert ended is not None
        assert ended.focus_percentage == 75.0

        retrieved = db_manager.get_session(session.id)
        assert retrieved is not None
        assert retrieved.id == session.id

    def test_daily_statistics_computation(self, db_manager):
        """Verify daily stats computed from sessions."""
        # Create two sessions today
        s1 = db_manager.create_session(subject="Math")
        db_manager.end_session(s1.id, {"focus_percentage": 80.0})

        s2 = db_manager.create_session(subject="Physics")
        db_manager.end_session(s2.id, {"focus_percentage": 60.0})

        stats = db_manager.get_daily_statistics()
        assert stats["session_count"] >= 2

    def test_weekly_stats_returns_seven_days(self, db_manager):
        """Weekly stats should cover 7 days."""
        weekly = db_manager.get_weekly_stats()
        assert len(weekly) == 7

    def test_frame_sampling_persists(self, db_manager):
        """Frame samples should persist and be retrievable."""
        session = db_manager.create_session(subject="Test")
        frame_data = {
            "frame_number": 1,
            "focus_state": 1,
            "confidence": 0.95,
            "attention_score": 0.85,
            "ear": 0.28,
            "mar": 0.35,
            "head_pitch": 5.0,
            "head_yaw": -3.0,
        }
        db_manager.add_frame_sample(session.id, frame_data)
        frames = db_manager.get_session_frames(session.id)
        assert len(frames) >= 1
        assert frames[0]["focus_state"] == 1


# ─────────────────────────────────────────────────────
# Vision + ML Pipeline Integration
# ─────────────────────────────────────────────────────


class TestVisionMLPipeline:
    """Test vision features feeding into ML classifier."""

    def test_feature_extractor_output_matches_classifier_input(self):
        """FeatureExtractor output keys must match classifier expected columns."""
        from backend.vision.feature_extractor import FaceFeatures

        features = FaceFeatures()
        feature_dict = features.to_dict()

        expected_keys = {
            "avg_ear", "left_ear", "right_ear", "ear_variance",
            "mar", "yawn_detected", "head_pitch", "head_yaw", "head_roll",
            "gaze_x", "gaze_y", "gaze_stability", "blink_rate",
            "blink_duration_avg", "eye_closure_ratio",
            "head_movement_magnitude", "head_stability",
            "ear_trend", "ear_mean", "ear_std",
            "brow_raise", "eye_squint",
            "time_of_day", "session_duration", "time_since_break",
            "cumulative_fatigue_score",
        }
        assert expected_keys.issubset(set(feature_dict.keys()))

    def test_feature_buffer_sequence_extraction(self):
        """Buffer should produce valid LSTM sequences."""
        from backend.ml.feature_buffer import FeatureBuffer

        buf = FeatureBuffer(max_size=100)
        for i in range(50):
            buf.add({"avg_ear": 0.28 + i * 0.001, "mar": 0.3, "blink_rate": 15.0})

        seq = buf.get_sequence(["avg_ear", "mar", "blink_rate"], length=30)
        assert seq is not None
        assert seq.shape == (30, 3)

    def test_ensemble_rule_based_fallback(self):
        """Ensemble should work without trained models (rule-based)."""
        from backend.ml.ensemble_classifier import EnsembleClassifier

        classifier = EnsembleClassifier()
        features = {
            "avg_ear": 0.28,
            "head_yaw": 5.0,
            "mar": 0.3,
            "blink_rate": 15.0,
            "gaze_stability": 0.8,
        }
        result = classifier.predict(features)
        assert result is not None
        assert hasattr(result, "predicted_class")
        assert result.predicted_class in [0, 1, 2]


# ─────────────────────────────────────────────────────
# Data Pipeline Integration
# ─────────────────────────────────────────────────────


class TestDataPipeline:
    """Test data recording → labeling → validation flow."""

    def test_recorder_creates_csv(self, tmp_path):
        """SessionRecorder should create valid CSV files."""
        from backend.data.session_recorder import SessionRecorder

        recorder = SessionRecorder(output_dir=str(tmp_path))
        recorder.start_recording("test_session")

        for i in range(10):
            recorder.record_frame(
                features={"avg_ear": 0.28, "mar": 0.3},
                label=1
            )

        recorder.stop_recording()
        csv_files = list(tmp_path.glob("*.csv"))
        assert len(csv_files) >= 1

    def test_auto_labeler_produces_valid_labels(self):
        """AutoLabeler should produce valid focus labels."""
        from backend.data.auto_labeler import AutoLabeler

        labeler = AutoLabeler()

        # Focused state
        label = labeler.label_frame({
            "avg_ear": 0.30,
            "head_yaw": 5.0,
            "mar": 0.25,
            "gaze_stability": 0.9,
            "blink_rate": 15.0,
        })
        assert label in [0, 1, 2]
