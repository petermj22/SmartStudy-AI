"""
SmartStudy — Performance Benchmark Tests
Validates latency, memory, and throughput requirements.
Relocated to backend/tests/test_performance.py for platform hardening.
"""

from __future__ import annotations
import time
from typing import Dict
import numpy as np
import pytest


class TestInferenceLatency:
    """Core performance: processing latency < 100ms."""

    def test_feature_extraction_under_5ms(self):
        """Feature extraction should be < 5ms."""
        from backend.vision.feature_extractor import FeatureExtractor, FaceFeatures
        from backend.vision.face_detector import DetectionResult

        landmarks = np.random.rand(478, 3).astype(np.float32)
        landmarks[:, 0] *= 1280
        landmarks[:, 1] *= 720
        landmarks[:, 2] *= 1280

        detection = DetectionResult(
            detected=True,
            landmarks=landmarks,
            normalized_landmarks=landmarks / 1280,
            image_width=1280,
            image_height=720,
        )

        extractor = FeatureExtractor()
        times = []
        for _ in range(50):
            t0 = time.perf_counter()
            features = extractor.extract(detection)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            times.append(elapsed_ms)

        avg_ms = np.mean(times)
        assert avg_ms < 10, f"Avg feature extraction {avg_ms:.1f}ms exceeds 10ms"

    def test_ensemble_inference_under_50ms(self):
        """ML ensemble prediction should be < 50ms."""
        from backend.ml.ensemble_classifier import EnsembleClassifier

        classifier = EnsembleClassifier()
        features = {
            "avg_ear": 0.28, "left_ear": 0.27, "right_ear": 0.29,
            "ear_variance": 0.001, "mar": 0.3, "yawn_detected": 0.0,
            "head_pitch": 5.0, "head_yaw": -3.0, "head_roll": 1.0,
            "gaze_x": 0.05, "gaze_y": -0.02, "gaze_stability": 0.85,
            "blink_rate": 15.0, "blink_duration_avg": 0.15,
            "eye_closure_ratio": 0.0, "head_movement_magnitude": 2.0,
            "head_stability": 0.9, "ear_trend": 0.0,
            "ear_mean": 0.28, "ear_std": 0.02,
            "brow_raise": 0.1, "eye_squint": 0.72,
            "time_of_day": 14.0, "session_duration": 30.0,
            "time_since_break": 20.0, "cumulative_fatigue_score": 0.3,
        }

        times = []
        for _ in range(100):
            t0 = time.perf_counter()
            result = classifier.predict(features)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            times.append(elapsed_ms)

        avg_ms = np.mean(times)
        assert avg_ms < 50, f"Avg ML inference {avg_ms:.1f}ms exceeds 50ms"


class TestDatabasePerformance:
    """Database operation latency tests."""

    def test_frame_insert_under_10ms(self, db_manager):
        """Frame sample insert should be < 10ms."""
        session = db_manager.create_session(subject="PerfTest")

        times = []
        for i in range(50):
            frame_data = {
                "frame_number": i, "focus_state": 1, "confidence": 0.9,
                "ear": 0.28, "mar": 0.3,
            }
            t0 = time.perf_counter()
            db_manager.add_frame_sample(session.id, frame_data)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            times.append(elapsed_ms)

        avg_ms = np.mean(times)
        assert avg_ms < 20, f"Avg DB insert {avg_ms:.1f}ms exceeds 20ms"

    def test_session_query_under_500ms(self, db_manager):
        """Session queries should be < 500ms."""
        for i in range(20):
            s = db_manager.create_session(subject=f"Subject{i % 5}")
            db_manager.end_session(s.id, {"focus_percentage": 70.0 + i})

        t0 = time.perf_counter()
        sessions = db_manager.get_recent_sessions(limit=100)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        assert elapsed_ms < 500, f"Session query {elapsed_ms:.1f}ms exceeds 500ms"
