"""
Module: camera_manager.py
Purpose: Production-grade webcam management with multi-threaded capture,
         auto-reconnection, and lighting quality analysis.
Author: SmartStudy Team
Version: 1.0.0
"""

from __future__ import annotations

import platform
import threading
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, List, Optional

import cv2
import numpy as np
from loguru import logger


class CameraStatus(Enum):
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    ERROR = auto()
    PAUSED = auto()


@dataclass
class CameraConfig:
    device_id: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30
    buffer_size: int = 2
    auto_reconnect: bool = True
    reconnect_delay_seconds: float = 2.0
    backend: int = cv2.CAP_ANY


@dataclass
class FrameData:
    frame: np.ndarray
    frame_number: int
    timestamp: float
    width: int
    height: int


@dataclass
class LightingAnalysis:
    brightness: float
    contrast: float
    quality: str
    recommendation: Optional[str]
    is_stable: bool = True


class CameraManager:
    """
    Production webcam manager with background capture thread,
    auto-reconnect, and lighting analysis.
    """

    def __init__(self, config: Optional[CameraConfig] = None) -> None:
        self.config = config or CameraConfig()
        self.status = CameraStatus.DISCONNECTED

        self._cap: Optional[cv2.VideoCapture] = None
        self._current_frame_data: Optional[FrameData] = None
        self._frame_lock = threading.Lock()

        self._is_running = False
        self._capture_thread: Optional[threading.Thread] = None
        self._frame_count = 0
        self._actual_fps: float = 0.0
        self._brightness_history: List[float] = []

        self._status_callbacks: List[Callable] = []
        self._frame_callbacks: List[Callable] = []

    def start(self) -> bool:
        if self._is_running:
            return True

        success = self._initialize_camera()
        if success:
            self._is_running = True
            self._capture_thread = threading.Thread(
                target=self._capture_loop, name="CameraCapture", daemon=True,
            )
            self._capture_thread.start()
            logger.info(
                f"Camera started: {self.config.width}x{self.config.height}"
                f"@{self.config.fps}fps device={self.config.device_id}"
            )
        return success

    def stop(self) -> None:
        self._is_running = False
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=3.0)
        if self._cap:
            self._cap.release()
            self._cap = None
        self._set_status(CameraStatus.DISCONNECTED)
        logger.info("Camera stopped")

    def pause(self) -> None:
        self._set_status(CameraStatus.PAUSED)

    def resume(self) -> None:
        if self._cap and self._cap.isOpened():
            self._set_status(CameraStatus.CONNECTED)

    def get_frame(self) -> Optional[FrameData]:
        with self._frame_lock:
            return self._current_frame_data

    def get_frame_blocking(self, timeout: float = 1.0) -> Optional[FrameData]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            frame_data = self.get_frame()
            if frame_data is not None:
                return frame_data
            time.sleep(0.01)
        return None

    def analyze_lighting(self, frame: np.ndarray) -> LightingAnalysis:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        contrast = float(np.std(gray))

        self._brightness_history.append(brightness)
        if len(self._brightness_history) > 30:
            self._brightness_history.pop(0)

        is_stable = (
            float(np.std(self._brightness_history)) < 15
            if len(self._brightness_history) > 10 else True
        )

        if brightness < 60:
            quality, rec = "too_dark", "Increase room lighting"
        elif brightness > 200:
            quality, rec = "too_bright", "Reduce background light"
        elif contrast < 25:
            quality, rec = "low_contrast", "Improve lighting direction"
        else:
            quality, rec = "good", None

        return LightingAnalysis(
            brightness=brightness, contrast=contrast,
            quality=quality, recommendation=rec, is_stable=is_stable,
        )

    def get_available_cameras(self) -> List[Dict]:
        cameras = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cameras.append({
                    "id": i,
                    "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    "fps": int(cap.get(cv2.CAP_PROP_FPS)),
                    "name": f"Camera {i}",
                })
                cap.release()
        return cameras

    def on_status_change(self, callback: Callable) -> None:
        self._status_callbacks.append(callback)

    @property
    def is_connected(self) -> bool:
        return self.status == CameraStatus.CONNECTED

    @property
    def actual_fps(self) -> float:
        return self._actual_fps

    @property
    def frame_count(self) -> int:
        return self._frame_count

    def _initialize_camera(self) -> bool:
        self._set_status(CameraStatus.CONNECTING)

        backends = [self.config.backend]
        if self.config.backend == cv2.CAP_ANY:
            sys_platform = platform.system()
            if sys_platform == "Windows":
                backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]
            elif sys_platform == "Linux":
                backends = [cv2.CAP_V4L2, cv2.CAP_ANY]

        for backend in backends:
            try:
                cap = cv2.VideoCapture(self.config.device_id, backend)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
                    cap.set(cv2.CAP_PROP_FPS, self.config.fps)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    self._cap = cap
                    self._set_status(CameraStatus.CONNECTED)
                    return True
                cap.release()
            except Exception as e:
                logger.warning(f"Backend {backend} failed: {e}")

        self._set_status(CameraStatus.ERROR)
        logger.error(f"Failed to open camera device {self.config.device_id}")
        return False

    def _capture_loop(self) -> None:
        frame_times: List[float] = []

        while self._is_running:
            if self.status == CameraStatus.PAUSED:
                time.sleep(0.05)
                continue

            if self.status != CameraStatus.CONNECTED or self._cap is None:
                if self.config.auto_reconnect:
                    logger.info("Attempting camera reconnect...")
                    time.sleep(self.config.reconnect_delay_seconds)
                    self._initialize_camera()
                else:
                    time.sleep(0.1)
                continue

            try:
                ret, frame = self._cap.read()
                if not ret or frame is None:
                    logger.warning("Frame read failed")
                    self._set_status(CameraStatus.DISCONNECTED)
                    if self._cap:
                        self._cap.release()
                        self._cap = None
                    continue

                current_time = time.time()
                self._frame_count += 1

                frame_times.append(current_time)
                if len(frame_times) > 30:
                    frame_times.pop(0)
                if len(frame_times) >= 2:
                    elapsed = frame_times[-1] - frame_times[0]
                    if elapsed > 0:
                        self._actual_fps = len(frame_times) / elapsed

                frame_data = FrameData(
                    frame=frame, frame_number=self._frame_count,
                    timestamp=current_time,
                    width=frame.shape[1], height=frame.shape[0],
                )

                with self._frame_lock:
                    self._current_frame_data = frame_data

            except Exception as e:
                logger.error(f"Capture loop error: {e}")
                self._set_status(CameraStatus.ERROR)
                time.sleep(0.5)

    def _set_status(self, new_status: CameraStatus) -> None:
        old_status = self.status
        self.status = new_status
        if old_status != new_status:
            logger.debug(f"Camera: {old_status.name} → {new_status.name}")
            for cb in self._status_callbacks:
                try:
                    cb(old_status, new_status)
                except Exception as e:
                    logger.error(f"Status callback error: {e}")

    def __enter__(self) -> "CameraManager":
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()
