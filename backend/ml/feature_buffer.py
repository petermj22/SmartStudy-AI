"""
Module: feature_buffer.py
Purpose: Thread-safe circular buffer for temporal feature storage.
         Provides efficient sliding-window statistics for ML inference.
Author: SmartStudy Team
Version: 1.0.0
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Optional

import numpy as np
from loguru import logger


@dataclass
class BufferStats:
    """Rolling statistics for a feature."""
    mean: float = 0.0
    std: float = 0.0
    min_val: float = 0.0
    max_val: float = 0.0
    trend: float = 0.0
    count: int = 0


class FeatureBuffer:
    """
    Thread-safe circular feature buffer with rolling statistics.

    Features:
    - O(1) append via deque
    - Efficient rolling statistics
    - Sequence extraction for LSTM input
    - Auto-timestamping
    """

    def __init__(self, max_size: int = 900) -> None:
        self.max_size = max_size
        self._buffer: Deque[Dict[str, Any]] = deque(maxlen=max_size)
        self._lock = threading.RLock()

    def add(self, features: Dict[str, Any]) -> None:
        """Thread-safe feature addition."""
        with self._lock:
            self._buffer.append({**features, "_timestamp": time.time()})

    def get_recent(self, n: int) -> List[Dict[str, Any]]:
        """Get n most recent feature dicts."""
        with self._lock:
            buf = list(self._buffer)
        return buf[-n:] if n < len(buf) else buf

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all buffered features."""
        with self._lock:
            return list(self._buffer)

    def get_sequence(
        self, feature_keys: List[str], length: int,
    ) -> Optional[np.ndarray]:
        """
        Extract a feature sequence for LSTM input.

        Returns:
            np.ndarray of shape (length, n_features) or None
        """
        with self._lock:
            buf = list(self._buffer)

        if len(buf) < length:
            return None

        recent = buf[-length:]
        try:
            return np.array(
                [[frame.get(k, 0.0) for k in feature_keys] for frame in recent],
                dtype=np.float32,
            )
        except (TypeError, ValueError) as e:
            logger.warning(f"Sequence extraction error: {e}")
            return None

    def compute_stats(self, feature_name: str, window: int = 30) -> BufferStats:
        """Compute rolling statistics for a single feature."""
        with self._lock:
            buf = list(self._buffer)

        values = [
            float(f[feature_name])
            for f in buf[-window:]
            if feature_name in f and f[feature_name] is not None
        ]

        if not values:
            return BufferStats()

        arr = np.array(values, dtype=np.float64)
        stats = BufferStats(
            mean=float(np.mean(arr)),
            std=float(np.std(arr)),
            min_val=float(np.min(arr)),
            max_val=float(np.max(arr)),
            count=len(arr),
        )

        # Compute linear trend (slope)
        if len(arr) >= 5:
            x = np.arange(len(arr), dtype=np.float64)
            coeffs = np.polyfit(x, arr, 1)
            stats.trend = float(coeffs[0])

        return stats

    def compute_temporal_features(self, window: int = 30) -> Dict[str, float]:
        """Compute temporal features (means, stds, trends) over window."""
        result: Dict[str, float] = {}
        with self._lock:
            buf = list(self._buffer)

        if len(buf) < 5:
            return result

        recent = buf[-window:]
        keys_to_track = ["avg_ear", "mar", "head_pitch", "head_yaw", "gaze_x", "gaze_y"]

        for key in keys_to_track:
            values = [float(f.get(key, 0.0)) for f in recent if key in f]
            if values:
                arr = np.array(values)
                result[f"{key}_mean"] = float(np.mean(arr))
                result[f"{key}_std"] = float(np.std(arr))
                if len(arr) >= 3:
                    x = np.arange(len(arr), dtype=np.float64)
                    coeffs = np.polyfit(x, arr, 1)
                    result[f"{key}_trend"] = float(coeffs[0])

        # Head movement magnitude
        pitch_vals = [float(f.get("head_pitch", 0)) for f in recent if "head_pitch" in f]
        yaw_vals = [float(f.get("head_yaw", 0)) for f in recent if "head_yaw" in f]
        if len(pitch_vals) >= 2:
            pitch_diff = np.diff(pitch_vals)
            yaw_diff = np.diff(yaw_vals) if len(yaw_vals) >= 2 else [0]
            movement = np.sqrt(np.array(pitch_diff) ** 2 + np.array(yaw_diff[:len(pitch_diff)]) ** 2)
            result["head_movement_magnitude"] = float(np.mean(movement))
            result["head_stability"] = float(1.0 / (1.0 + np.std(movement)))

        return result

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._buffer)

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()
        logger.debug("FeatureBuffer cleared")
