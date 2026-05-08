"""SmartStudy Core Package — Camera, Inference, Session, Notifications, Scheduler."""

from backend.core.camera_manager import CameraManager, CameraConfig, CameraStatus
from backend.core.session_manager import SessionManager
from backend.core.notification_manager import DesktopNotificationManager, NotificationConfig
from backend.core.background_scheduler import BackgroundScheduler
from backend.core.session_replay import SessionThumbnailRecorder, SessionReplayEngine

__all__ = [
    "CameraManager", "CameraConfig", "CameraStatus",
    "SessionManager",
    "DesktopNotificationManager", "NotificationConfig",
    "BackgroundScheduler",
    "SessionThumbnailRecorder", "SessionReplayEngine",
]
