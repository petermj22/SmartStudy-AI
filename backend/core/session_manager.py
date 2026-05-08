"""
Module: session_manager.py
Purpose: Study session lifecycle management — start, monitor, pause, end.
         Coordinates camera, inference engine, and database operations.
Author: SmartStudy Team
Version: 1.0.0
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from backend.core.camera_manager import CameraManager, CameraConfig, CameraStatus, FrameData
from backend.core.inference_engine import InferenceEngine, InferenceResult
from backend.database.manager import DatabaseManager


class SessionState(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    ON_BREAK = auto()
    ENDED = auto()


@dataclass
class SessionMetrics:
    """Live session metrics."""
    total_frames: int = 0
    focused_frames: int = 0
    distracted_frames: int = 0
    fatigued_frames: int = 0
    no_face_frames: int = 0

    focus_percentage: float = 0.0
    avg_attention_score: float = 0.0
    distraction_count: int = 0
    fatigue_events: int = 0
    break_count: int = 0

    current_focus_state: int = 1
    current_focus_label: str = "focused"
    current_confidence: float = 0.5
    current_fatigue_score: float = 0.0
    current_attention_score: float = 1.0

    session_duration_minutes: float = 0.0
    focused_seconds: float = 0.0
    distracted_seconds: float = 0.0
    fatigued_seconds: float = 0.0

    avg_ear: float = 0.3
    avg_blink_rate: float = 15.0
    alerts: List[Dict[str, str]] = field(default_factory=list)


class SessionManager:
    """
    Orchestrates a complete study session lifecycle.

    Responsibilities:
    - Start/stop camera and inference engine
    - Process frames in background thread
    - Track session metrics in real-time
    - Auto-save to database at configurable intervals
    - Manage break notifications
    """

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        camera_config: Optional[CameraConfig] = None,
        auto_save_interval: int = 60,
        frame_sample_rate: int = 30,
    ) -> None:
        self._db = db_manager or DatabaseManager()
        self._camera = CameraManager(camera_config)
        self._engine = InferenceEngine()

        self._state = SessionState.IDLE
        self._session_id: Optional[str] = None
        self._auto_save_interval = auto_save_interval
        self._frame_sample_rate = frame_sample_rate

        # Threading
        self._processing_thread: Optional[threading.Thread] = None
        self._is_processing = False

        # Metrics
        self._metrics = SessionMetrics()
        self._start_time: float = 0.0
        self._last_save_time: float = 0.0
        self._last_state: int = -1
        self._distraction_start: Optional[float] = None

        # Callbacks
        self._on_result_callbacks: List[Callable] = []
        self._on_alert_callbacks: List[Callable] = []
        self._on_break_callbacks: List[Callable] = []

        # Break management
        self._current_break_id: Optional[int] = None
        self._break_requested: bool = False

        # EAR/blink accumulation
        self._ear_sum: float = 0.0
        self._blink_rate_sum: float = 0.0
        self._metric_count: int = 0

    # ── PUBLIC API ──────────────────────────────────────

    def start_session(
        self, subject: str = "General", tags: Optional[List[str]] = None,
        use_webrtc: bool = False,
    ) -> str:
        """Start a new study session.

        Args:
            subject: Study subject name.
            tags: Optional list of tags.
            use_webrtc: If True, camera is handled by WebRTC (browser).
                        Skips backend CameraManager to avoid device lock conflict.
        """
        if self._state == SessionState.RUNNING:
            logger.warning("Session already running")
            return self._session_id or ""

        # Create database session
        session = self._db.create_session(subject=subject, tags=tags)
        self._session_id = session.id

        # Reset state
        self._metrics = SessionMetrics()
        self._engine.reset_session()
        self._start_time = time.time()
        self._last_save_time = time.time()
        self._ear_sum = 0.0
        self._blink_rate_sum = 0.0
        self._metric_count = 0
        self._distraction_start = None
        self._last_state = -1

        self._use_webrtc = use_webrtc

        if use_webrtc:
            # Camera managed by browser WebRTC — don't open OpenCV capture
            logger.info("Session using WebRTC camera (browser-managed)")
        else:
            # Start backend camera (OpenCV)
            if not self._camera.start():
                logger.error("Failed to start camera")
                self._state = SessionState.IDLE
                return ""

            # Start processing thread (only needed in non-WebRTC mode)
            self._is_processing = True
            self._processing_thread = threading.Thread(
                target=self._processing_loop, name="SessionProcessing", daemon=True,
            )
            self._processing_thread.start()

        self._state = SessionState.RUNNING
        logger.info(f"Session started: {self._session_id} subject={subject!r} webrtc={use_webrtc}")
        return self._session_id

    def end_session(self) -> Optional[Dict[str, Any]]:
        """End the current session and save final metrics."""
        if self._state not in (SessionState.RUNNING, SessionState.PAUSED, SessionState.ON_BREAK):
            logger.warning("No active session to end")
            return None

        self._is_processing = False
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=5.0)

        if not getattr(self, '_use_webrtc', False):
            self._camera.stop()
        self._engine.close()

        # Compute final metrics
        self._update_duration()
        final_metrics = {
            "focus_percentage": self._metrics.focus_percentage,
            "avg_attention_score": self._metrics.avg_attention_score,
            "distraction_count": self._metrics.distraction_count,
            "fatigue_events": self._metrics.fatigue_events,
            "break_count": self._metrics.break_count,
            "focused_seconds": self._metrics.focused_seconds,
            "distracted_seconds": self._metrics.distracted_seconds,
            "fatigued_seconds": self._metrics.fatigued_seconds,
            "avg_ear": self._metrics.avg_ear,
            "avg_blink_rate": self._metrics.avg_blink_rate,
            "peak_focus_hour": datetime.now().hour,
        }

        # Save to database
        if self._session_id:
            self._db.end_session(self._session_id, final_metrics)
            self._db.update_daily_statistics()

        self._state = SessionState.ENDED
        logger.info(
            f"Session ended: {self._session_id} "
            f"duration={self._metrics.session_duration_minutes:.1f}m "
            f"focus={self._metrics.focus_percentage:.1f}%"
        )

        session_id = self._session_id
        self._session_id = None
        return {"session_id": session_id, **final_metrics}

    def pause_session(self) -> None:
        """Pause session (camera stays open but processing stops)."""
        if self._state == SessionState.RUNNING:
            self._camera.pause()
            self._state = SessionState.PAUSED
            logger.info("Session paused")

    def resume_session(self) -> None:
        """Resume a paused session."""
        if self._state == SessionState.PAUSED:
            self._camera.resume()
            self._state = SessionState.RUNNING
            logger.info("Session resumed")

    def start_break(self, break_type: str = "manual") -> None:
        """Start a break within the session."""
        if self._state != SessionState.RUNNING:
            return

        self._state = SessionState.ON_BREAK
        self._camera.pause()
        self._engine.record_break()
        self._metrics.break_count += 1

        if self._session_id:
            self._current_break_id = self._db.record_break_start(
                self._session_id, break_type=break_type,
                was_recommended=(break_type != "manual"),
                trigger_type=break_type,
            )

        for cb in self._on_break_callbacks:
            try:
                cb("start", break_type)
            except Exception:
                pass

        logger.info(f"Break started: type={break_type}")

    def end_break(self) -> None:
        """End the current break."""
        if self._state != SessionState.ON_BREAK:
            return

        if self._current_break_id:
            self._db.record_break_end(self._current_break_id)
            self._current_break_id = None

        self._camera.resume()
        self._state = SessionState.RUNNING

        for cb in self._on_break_callbacks:
            try:
                cb("end", "")
            except Exception:
                pass

        logger.info("Break ended")

    def get_metrics(self) -> SessionMetrics:
        """Get current live session metrics."""
        self._update_duration()
        return self._metrics

    def get_latest_result(self) -> Optional[InferenceResult]:
        """Get the most recent inference result."""
        return self._engine._last_result

    def on_result(self, callback: Callable) -> None:
        self._on_result_callbacks.append(callback)

    def on_alert(self, callback: Callable) -> None:
        self._on_alert_callbacks.append(callback)

    def on_break_event(self, callback: Callable) -> None:
        self._on_break_callbacks.append(callback)

    @property
    def state(self) -> SessionState:
        return self._state

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    @property
    def is_active(self) -> bool:
        return self._state in (SessionState.RUNNING, SessionState.PAUSED, SessionState.ON_BREAK)

    # ── INTERNAL ────────────────────────────────────────

    def _processing_loop(self) -> None:
        """Background thread: process frames continuously."""
        while self._is_processing:
            if self._state != SessionState.RUNNING:
                time.sleep(0.05)
                continue

            frame_data = self._camera.get_frame()
            if frame_data is None:
                time.sleep(0.01)
                continue

            try:
                result = self._engine.process_frame(frame_data.frame)
                self._update_metrics(result)

                # Sample frames to database
                if (
                    self._session_id
                    and result.frame_number % self._frame_sample_rate == 0
                ):
                    self._save_frame_sample(result)

                # Auto-save
                if time.time() - self._last_save_time > self._auto_save_interval:
                    self._auto_save()
                    self._last_save_time = time.time()

                # Notify callbacks
                for cb in self._on_result_callbacks:
                    try:
                        cb(result)
                    except Exception:
                        pass

                # Alert callbacks
                if result.alerts:
                    for cb in self._on_alert_callbacks:
                        try:
                            cb(result.alerts)
                        except Exception:
                            pass

            except Exception as e:
                logger.error(f"Processing error: {e}")
                time.sleep(0.01)

    def _update_metrics(self, result: InferenceResult) -> None:
        """Update running session metrics from inference result."""
        self._metrics.total_frames += 1

        state = result.smoothed_focus_state
        if state == 1:
            self._metrics.focused_frames += 1
        elif state == 0:
            self._metrics.distracted_frames += 1
        elif state == 2:
            self._metrics.fatigued_frames += 1

        if not result.face_detected:
            self._metrics.no_face_frames += 1

        # Track distraction events (state transitions)
        if state == 0 and self._last_state != 0:
            self._metrics.distraction_count += 1
        if state == 2 and self._last_state != 2:
            self._metrics.fatigue_events += 1
        self._last_state = state

        # Running averages
        total = self._metrics.total_frames
        if total > 0:
            self._metrics.focus_percentage = (self._metrics.focused_frames / total) * 100

        self._metrics.current_focus_state = state
        self._metrics.current_focus_label = result.smoothed_focus_label
        self._metrics.current_confidence = result.focus_confidence
        self._metrics.current_fatigue_score = result.fatigue_score
        self._metrics.current_attention_score = result.attention_score

        # EAR/blink rate accumulation
        if result.features:
            self._ear_sum += result.features.avg_ear
            self._blink_rate_sum += result.features.blink_rate
            self._metric_count += 1
            self._metrics.avg_ear = self._ear_sum / self._metric_count
            self._metrics.avg_blink_rate = self._blink_rate_sum / self._metric_count

        # Alerts
        if result.alerts:
            for a in result.alerts:
                self._metrics.alerts.append({
                    "type": a.type, "severity": a.severity,
                    "message": a.message, "timestamp": a.timestamp,
                })
            # Keep last 50 alerts
            if len(self._metrics.alerts) > 50:
                self._metrics.alerts = self._metrics.alerts[-50:]

    def _update_duration(self) -> None:
        """Update time-based metrics."""
        if self._start_time > 0:
            elapsed = time.time() - self._start_time
            self._metrics.session_duration_minutes = elapsed / 60.0

            total = self._metrics.total_frames
            if total > 0:
                fps = total / max(elapsed, 1)
                self._metrics.focused_seconds = self._metrics.focused_frames / max(fps, 1)
                self._metrics.distracted_seconds = self._metrics.distracted_frames / max(fps, 1)
                self._metrics.fatigued_seconds = self._metrics.fatigued_frames / max(fps, 1)
                self._metrics.avg_attention_score = self._metrics.focused_frames / total

    def _save_frame_sample(self, result: InferenceResult) -> None:
        """Save a frame sample to database."""
        if not self._session_id or not result.features:
            return

        try:
            self._db.add_frame_sample(self._session_id, {
                "frame_number": result.frame_number,
                "focus_state": result.smoothed_focus_state,
                "confidence": result.focus_confidence,
                "attention_score": result.attention_score,
                "fatigue_score": result.fatigue_score,
                "ear": result.features.avg_ear,
                "mar": result.features.mar,
                "head_pitch": result.features.head_pitch,
                "head_yaw": result.features.head_yaw,
                "head_roll": result.features.head_roll,
                "gaze_x": result.features.gaze_x,
                "gaze_y": result.features.gaze_y,
                "blink_rate": result.features.blink_rate,
                "alerts": [{"type": a.type, "msg": a.message} for a in result.alerts],
            })
        except Exception as e:
            logger.warning(f"Frame sample save error: {e}")

    def _auto_save(self) -> None:
        """Auto-save session metrics to database."""
        if not self._session_id:
            return
        self._update_duration()
        logger.debug(f"Auto-save: focus={self._metrics.focus_percentage:.1f}%")
