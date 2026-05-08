"""
SmartStudy — Test Configuration (conftest.py)
Shared fixtures for all tests.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def db_manager():
    """Create a temporary in-memory database manager."""
    from backend.database.manager import DatabaseManager
    manager = DatabaseManager(db_path=":memory:")
    yield manager


@pytest.fixture
def feature_dict():
    """Create a sample feature dictionary for testing."""
    return {
        "avg_ear": 0.29, "left_ear": 0.30, "right_ear": 0.28,
        "ear_variance": 0.001, "mar": 0.35, "yawn_detected": 0.0,
        "head_pitch": 5.0, "head_yaw": -3.0, "head_roll": 1.0,
        "gaze_x": 0.05, "gaze_y": -0.02, "gaze_stability": 0.85,
        "blink_rate": 16.0, "blink_duration_avg": 0.15,
        "eye_closure_ratio": 0.0, "head_movement_magnitude": 0.5,
        "head_stability": 0.9, "ear_trend": -0.001,
        "ear_mean": 0.29, "ear_std": 0.02,
        "brow_raise": 0.3, "eye_squint": 0.71,
        "time_of_day": 14.5, "session_duration": 25.0,
        "time_since_break": 20.0, "cumulative_fatigue_score": 0.3,
    }


@pytest.fixture
def sample_session(db_manager):
    """Create a sample study session."""
    session = db_manager.create_session(subject="Mathematics", tags=["exam_prep"])
    return session


@pytest.fixture
def feature_buffer():
    """Create a feature buffer with sample data."""
    from backend.ml.feature_buffer import FeatureBuffer
    buf = FeatureBuffer(max_size=100)
    for i in range(50):
        buf.add({
            "avg_ear": 0.28 + (i * 0.001),
            "mar": 0.3 + (i * 0.002),
            "head_pitch": 5.0 + (i * 0.1),
            "head_yaw": -3.0 + (i * 0.05),
            "gaze_x": 0.05, "gaze_y": -0.02,
        })
    return buf
