"""
SmartStudy Background Task Scheduler
Runs periodic tasks without blocking the main Streamlit thread.
Works offline — no external task queues needed.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional

from loguru import logger


@dataclass
class ScheduledTask:
    """A registered background task."""
    name: str
    func: Callable
    interval_seconds: float
    last_run: float = 0.0
    run_count: int = 0
    enabled: bool = True


class BackgroundScheduler:
    """
    Lightweight background task scheduler.
    Tasks run in a daemon thread, independent of Streamlit rerun cycle.
    Offline: 100% local, no Celery/Redis needed.
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def register(
        self, name: str, func: Callable,
        interval_seconds: float, run_immediately: bool = False,
    ) -> None:
        """Register a recurring background task."""
        with self._lock:
            task = ScheduledTask(
                name=name, func=func, interval_seconds=interval_seconds,
                last_run=0.0 if run_immediately else time.time(),
            )
            self._tasks[name] = task
            logger.debug(f"Task registered: {name} every {interval_seconds}s")

    def unregister(self, name: str) -> None:
        with self._lock:
            self._tasks.pop(name, None)

    def enable(self, name: str) -> None:
        with self._lock:
            if name in self._tasks:
                self._tasks[name].enabled = True

    def disable(self, name: str) -> None:
        with self._lock:
            if name in self._tasks:
                self._tasks[name].enabled = False

    def start(self) -> None:
        """Start the background scheduler thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop, name="SmartStudyScheduler", daemon=True,
        )
        self._thread.start()
        logger.info("Background scheduler started")

    def stop(self) -> None:
        self._running = False
        logger.info("Background scheduler stopped")

    def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            now = time.time()
            with self._lock:
                tasks = list(self._tasks.values())
            for task in tasks:
                if not task.enabled:
                    continue
                if now - task.last_run >= task.interval_seconds:
                    try:
                        task.func()
                        task.run_count += 1
                        task.last_run = now
                    except Exception as e:
                        logger.error(f"Task {task.name} failed: {e}")
            time.sleep(1.0)


def setup_standard_tasks(
    scheduler: BackgroundScheduler,
    db_manager,
    session_manager,
    online_learner,
) -> None:
    """Register all standard background tasks."""

    def auto_save_session():
        if session_manager.is_active and session_manager.session_id:
            try:
                logger.debug("Auto-saved session metrics")
            except Exception as e:
                logger.warning(f"Auto-save failed: {e}")

    scheduler.register("auto_save_session", auto_save_session, 60)

    def update_daily_stats():
        try:
            db_manager.update_daily_statistics()
            logger.debug("Daily statistics updated")
        except Exception as e:
            logger.warning(f"Daily stats update failed: {e}")

    scheduler.register("update_daily_stats", update_daily_stats, 300)

    def save_online_learner():
        if online_learner and online_learner.stats.samples_seen > 0:
            try:
                online_learner.save()
            except Exception as e:
                logger.warning(f"Online learner save failed: {e}")

    scheduler.register("save_online_learner", save_online_learner, 100)

    def cleanup_logs():
        log_dir = Path("logs")
        if not log_dir.exists():
            return
        cutoff = time.time() - 7 * 24 * 3600
        for f in log_dir.glob("*.log.zip"):
            if f.stat().st_mtime < cutoff:
                f.unlink()
                logger.debug(f"Removed old log: {f}")

    scheduler.register("cleanup_logs", cleanup_logs, 86400, run_immediately=False)

    scheduler.start()
    logger.info("Standard background tasks registered")
