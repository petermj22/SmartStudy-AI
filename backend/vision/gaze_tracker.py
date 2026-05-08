"""
Module: gaze_tracker.py
Purpose: Gaze stability analysis and attention direction classification.
Author: SmartStudy Team
Version: 1.0.0
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque

import numpy as np
from loguru import logger


@dataclass
class GazeDirection:
    """Classified gaze direction with stability metrics."""

    x: float = 0.0
    y: float = 0.0
    stability: float = 1.0
    drift: float = 0.0
    direction_label: str = "center"

    @property
    def is_on_screen(self) -> bool:
        return abs(self.x) < 0.3 and abs(self.y) < 0.3

    @property
    def looking_away(self) -> bool:
        return abs(self.x) > 0.5 or abs(self.y) > 0.5


class GazeTracker:
    """
    Rolling gaze stability tracker.
    Maintains history and computes stability score, drift, and direction.
    """

    def __init__(self, window_size: int = 90) -> None:
        self.window_size = window_size
        self._gaze_x_history: Deque[float] = deque(maxlen=window_size)
        self._gaze_y_history: Deque[float] = deque(maxlen=window_size)

    def update(self, gaze_x: float, gaze_y: float) -> GazeDirection:
        """Update tracker with new gaze coordinates."""
        self._gaze_x_history.append(gaze_x)
        self._gaze_y_history.append(gaze_y)

        direction = GazeDirection(x=gaze_x, y=gaze_y)

        if len(self._gaze_x_history) >= 10:
            x_arr = np.array(self._gaze_x_history)
            y_arr = np.array(self._gaze_y_history)

            x_var = float(np.var(x_arr))
            y_var = float(np.var(y_arr))
            total_var = x_var + y_var
            direction.stability = float(1.0 / (1.0 + total_var * 10))

            if len(x_arr) >= 2:
                direction.drift = float(
                    np.sqrt((x_arr[-1] - x_arr[0]) ** 2 + (y_arr[-1] - y_arr[0]) ** 2)
                )

        direction.direction_label = self._classify(gaze_x, gaze_y)
        return direction

    def _classify(self, x: float, y: float) -> str:
        threshold = 0.3
        if abs(x) < threshold and abs(y) < threshold:
            return "center"
        if abs(x) > abs(y):
            return "right" if x > 0 else "left"
        return "down" if y > 0 else "up"

    def get_stability(self) -> float:
        if len(self._gaze_x_history) < 5:
            return 1.0
        x_arr = np.array(self._gaze_x_history)
        y_arr = np.array(self._gaze_y_history)
        total_var = float(np.var(x_arr)) + float(np.var(y_arr))
        return float(1.0 / (1.0 + total_var * 10))

    def reset(self) -> None:
        self._gaze_x_history.clear()
        self._gaze_y_history.clear()
