"""
Module: blink_detector.py
Purpose: Temporal blink detection with rate calculation and microsleep detection.
Author: SmartStudy Team
Version: 1.0.0
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Deque

from loguru import logger


@dataclass
class BlinkStats:
    """Statistics from blink detector."""

    blink_detected: bool = False
    blink_duration_frames: int = 0
    blink_duration_seconds: float = 0.0
    total_blinks: int = 0
    blink_rate_per_minute: float = 15.0
    is_eyes_closed: bool = False
    consecutive_closed_frames: int = 0
    is_microsleep: bool = False
    avg_blink_duration: float = 0.15


class BlinkDetector:
    """
    Real-time blink detection and analysis.

    Algorithm:
    1. Detect EAR drops below threshold for N consecutive frames
    2. Confirm blink when EAR returns above threshold
    3. Track blink timestamps for rate calculation
    4. Detect microsleep when eyes closed > 3 seconds
    """

    def __init__(
        self,
        ear_threshold: float = 0.21,
        consecutive_frames_for_blink: int = 3,
        microsleep_frames: int = 90,
        fps: int = 30,
        history_seconds: int = 60,
    ) -> None:
        self.ear_threshold = ear_threshold
        self.consecutive_frames_for_blink = consecutive_frames_for_blink
        self.microsleep_frames = microsleep_frames
        self.fps = fps
        self.history_seconds = history_seconds

        self._counter: int = 0
        self._total_blinks: int = 0
        self._in_blink: bool = False
        self._blink_start_frame: int = 0
        self._blink_durations: Deque[float] = deque(maxlen=50)
        self._blink_timestamps: Deque[float] = deque()

    def update(self, ear: float, frame_number: int) -> BlinkStats:
        """
        Update detector with new EAR value.

        Args:
            ear: Current Eye Aspect Ratio
            frame_number: Current frame index

        Returns:
            BlinkStats with current blink state
        """
        stats = BlinkStats()
        stats.total_blinks = self._total_blinks

        if ear < self.ear_threshold:
            self._counter += 1
            if not self._in_blink and self._counter >= self.consecutive_frames_for_blink:
                self._in_blink = True
                self._blink_start_frame = frame_number
        else:
            if self._in_blink:
                duration_frames = frame_number - self._blink_start_frame
                duration_seconds = duration_frames / self.fps

                self._total_blinks += 1
                self._blink_timestamps.append(time.time())
                self._blink_durations.append(duration_seconds)

                stats.blink_detected = True
                stats.blink_duration_frames = duration_frames
                stats.blink_duration_seconds = duration_seconds
                self._in_blink = False

            self._counter = 0

        # Prune old timestamps
        current_time = time.time()
        cutoff = current_time - self.history_seconds
        while self._blink_timestamps and self._blink_timestamps[0] < cutoff:
            self._blink_timestamps.popleft()

        # Compute blink rate (blinks per minute)
        recent_window = 60
        recent_cutoff = current_time - recent_window
        recent_count = sum(1 for t in self._blink_timestamps if t >= recent_cutoff)
        elapsed = min(
            recent_window,
            current_time - (self._blink_timestamps[0] if self._blink_timestamps else current_time),
        )
        if elapsed > 5:
            stats.blink_rate_per_minute = (recent_count / elapsed) * 60
        else:
            stats.blink_rate_per_minute = 15.0

        stats.total_blinks = self._total_blinks
        stats.is_eyes_closed = self._in_blink
        stats.consecutive_closed_frames = self._counter if self._in_blink else 0
        stats.is_microsleep = self._counter >= self.microsleep_frames
        stats.avg_blink_duration = (
            float(sum(self._blink_durations) / len(self._blink_durations))
            if self._blink_durations else 0.15
        )

        return stats

    def reset(self) -> None:
        """Reset detector state for new session."""
        self._counter = 0
        self._total_blinks = 0
        self._in_blink = False
        self._blink_start_frame = 0
        self._blink_durations.clear()
        self._blink_timestamps.clear()
        logger.debug("BlinkDetector reset")

    @property
    def total_blinks(self) -> int:
        return self._total_blinks
