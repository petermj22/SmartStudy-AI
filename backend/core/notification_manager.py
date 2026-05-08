"""
SmartStudy Desktop Notification Manager
Sends OS-level notifications using plyer.
Works offline, appears in system tray on Windows/macOS/Linux.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

from loguru import logger

try:
    from plyer import notification as plyer_notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


@dataclass
class NotificationConfig:
    """Notification appearance and behavior config."""
    app_name: str = "SmartStudy"
    app_icon: Optional[str] = None
    timeout: int = 10
    enable_break: bool = True
    enable_distraction: bool = True
    enable_fatigue: bool = True
    enable_achievement: bool = True
    cooldown_seconds: int = 60


class DesktopNotificationManager:
    """Cross-platform desktop notification manager using plyer."""

    def __init__(self, config: Optional[NotificationConfig] = None) -> None:
        self.config = config or NotificationConfig()
        self._cooldowns: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._queue: List[Dict] = []
        self._running = True
        self._callbacks: List[Callable] = []
        self._worker = threading.Thread(
            target=self._notification_worker, daemon=True, name="NotificationWorker",
        )
        self._worker.start()

        for p in [Path("frontend/assets/icon.ico"), Path("frontend/assets/icon.png")]:
            if p.exists():
                self.config.app_icon = str(p)
                break

        logger.info(f"NotificationManager ready | plyer={'yes' if PLYER_AVAILABLE else 'no'}")

    def notify_break(self, minutes: float, fatigue_pct: float) -> None:
        if not self.config.enable_break or not self._can_send("break"):
            return
        self._enqueue("☕ Time for a Break!",
            f"AI detected {fatigue_pct:.0f}% fatigue. A {minutes:.0f}-min break will help.", "normal")

    def notify_distraction(self, detail: str) -> None:
        if not self.config.enable_distraction or not self._can_send("distraction"):
            return
        self._enqueue("👀 Stay Focused!", detail, "low")

    def notify_microsleep(self) -> None:
        self._enqueue("🚨 Wake Up! Microsleep Detected",
            "Your eyes were closed for too long. Take an immediate break.", "critical")

    def notify_achievement(self, title: str, message: str) -> None:
        if not self.config.enable_achievement:
            return
        self._enqueue(f"🏆 {title}", message, "low")

    def notify_session_complete(self, duration_minutes: float, focus_pct: float) -> None:
        grade = "🌟 Excellent" if focus_pct > 80 else "✅ Good" if focus_pct > 60 else "📈 Keep going"
        self._enqueue("📚 Session Complete!",
            f"{grade} — {duration_minutes:.0f}min | {focus_pct:.0f}% focus", "low")

    def on_notification(self, callback: Callable) -> None:
        self._callbacks.append(callback)

    def shutdown(self) -> None:
        self._running = False

    def _can_send(self, notification_type: str) -> bool:
        with self._lock:
            last = self._cooldowns.get(notification_type, 0)
            if time.time() - last < self.config.cooldown_seconds:
                return False
            self._cooldowns[notification_type] = time.time()
            return True

    def _enqueue(self, title: str, message: str, urgency: str) -> None:
        with self._lock:
            self._queue.append({"title": title, "message": message,
                                "urgency": urgency, "timestamp": time.time()})

    def _notification_worker(self) -> None:
        while self._running:
            with self._lock:
                queue_copy = self._queue.copy()
                self._queue.clear()
            for notif in queue_copy:
                self._send(notif)
                for cb in self._callbacks:
                    try:
                        cb(notif)
                    except Exception:
                        pass
            time.sleep(0.5)

    def _send(self, notif: Dict) -> None:
        if PLYER_AVAILABLE:
            try:
                plyer_notification.notify(
                    title=notif["title"], message=notif["message"],
                    app_name=self.config.app_name,
                    app_icon=self.config.app_icon or "", timeout=self.config.timeout,
                )
                logger.debug(f"Desktop notification sent: {notif['title']}")
                return
            except Exception as e:
                logger.warning(f"plyer notification failed: {e}")
        logger.info(f"[NOTIFICATION] {notif['title']}: {notif['message']}")
