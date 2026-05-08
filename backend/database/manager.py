"""
Module: manager.py
Purpose: Production-ready database operations with connection pooling,
         transaction management, and comprehensive CRUD operations.
Author: SmartStudy Team
Version: 1.0.0
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import numpy as np
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import (
    Base, BreakRecord, DailyStatistics, SessionFrame, StudySession, User,
)


class DatabaseManager:
    """
    Production database manager with SQLite WAL mode,
    connection pooling, and context-managed transactions.
    """

    DEFAULT_USER_ID = "default_user"

    def __init__(self, db_path: str = "data/smartstudy.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=False,
            connect_args={"check_same_thread": False, "timeout": 30},
            pool_pre_ping=True,
        )
        self._SessionFactory = sessionmaker(
            bind=self.engine, autocommit=False, autoflush=False,
        )
        self._initialize_database()
        logger.info(f"Database initialized at {self.db_path}")

    def _initialize_database(self) -> None:
        with self.engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            conn.commit()
        Base.metadata.create_all(self.engine)
        self._ensure_default_user()

    def _ensure_default_user(self) -> None:
        with self.get_db_session() as session:
            user = session.query(User).filter_by(id=self.DEFAULT_USER_ID).first()
            if not user:
                default_prefs = {
                    "break_interval": 25, "break_duration": 5,
                    "sensitivity": "medium", "notifications": True,
                    "sound": True, "theme": "light", "weekly_goal_hours": 20,
                }
                user = User(
                    id=self.DEFAULT_USER_ID, name="Student",
                    preferences=json.dumps(default_prefs), calibration="{}",
                )
                session.add(user)
                logger.info("Default user created")

    @contextmanager
    def get_db_session(self) -> Generator[Session, None, None]:
        session = self._SessionFactory()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error in DB session: {e}")
            raise
        finally:
            session.close()

    # ── USER OPERATIONS ──────────────────────────────────

    def get_user(self, user_id: str = DEFAULT_USER_ID) -> Optional[User]:
        with self.get_db_session() as session:
            result = session.query(User).filter_by(id=user_id).first()
            if result:
                session.expunge(result)
            return result

    def update_user_preferences(
        self, preferences: Dict[str, Any], user_id: str = DEFAULT_USER_ID,
    ) -> bool:
        with self.get_db_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.set_preferences(preferences)
                return True
            return False

    def update_calibration(
        self, calibration: Dict[str, Any], user_id: str = DEFAULT_USER_ID,
    ) -> bool:
        with self.get_db_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.set_calibration(calibration)
                return True
            return False

    # ── SESSION OPERATIONS ───────────────────────────────

    def create_session(
        self, subject: str = "General", tags: Optional[List[str]] = None,
        user_id: str = DEFAULT_USER_ID,
    ) -> StudySession:
        with self.get_db_session() as session:
            study_session = StudySession(
                user_id=user_id, start_time=datetime.now(timezone.utc).replace(tzinfo=None),
                subject=subject, tags=json.dumps(tags or []),
            )
            session.add(study_session)
            session.flush()
            logger.info(f"Session created: {study_session.id} subject={subject!r}")
            session.expunge(study_session)
            return study_session

    def end_session(
        self, session_id: str, metrics: Dict[str, Any],
    ) -> Optional[StudySession]:
        with self.get_db_session() as session:
            study_session = session.query(StudySession).filter_by(id=session_id).first()
            if not study_session:
                logger.warning(f"Session not found: {session_id}")
                return None

            study_session.end_time = datetime.now(timezone.utc).replace(tzinfo=None)
            study_session.duration_minutes = (
                study_session.end_time - study_session.start_time
            ).total_seconds() / 60

            allowed_fields = {
                "focus_percentage", "avg_attention_score", "distraction_count",
                "fatigue_events", "break_count", "focused_seconds",
                "distracted_seconds", "fatigued_seconds", "avg_ear",
                "avg_blink_rate", "peak_focus_hour", "notes",
            }
            for key, value in metrics.items():
                if key in allowed_fields and hasattr(study_session, key):
                    setattr(study_session, key, value)

            logger.info(
                f"Session ended: {session_id} "
                f"duration={study_session.duration_minutes:.1f}m "
                f"focus={metrics.get('focus_percentage', 0):.1f}%"
            )
            session.flush()
            session.expunge(study_session)
            return study_session

    def get_session(self, session_id: str) -> Optional[StudySession]:
        with self.get_db_session() as session:
            result = session.query(StudySession).filter_by(id=session_id).first()
            if result:
                session.expunge(result)
            return result

    def get_sessions_by_date_range(
        self, start_date: datetime, end_date: datetime,
        user_id: str = DEFAULT_USER_ID,
    ) -> List[Dict[str, Any]]:
        with self.get_db_session() as session:
            sessions = (
                session.query(StudySession)
                .filter(
                    StudySession.user_id == user_id,
                    StudySession.start_time >= start_date,
                    StudySession.start_time <= end_date,
                    StudySession.end_time.isnot(None),
                )
                .order_by(StudySession.start_time.desc())
                .all()
            )
            return [self._session_to_dict(s) for s in sessions]

    def get_recent_sessions(
        self, limit: int = 10, user_id: str = DEFAULT_USER_ID,
    ) -> List[Dict[str, Any]]:
        with self.get_db_session() as session:
            sessions = (
                session.query(StudySession)
                .filter(
                    StudySession.user_id == user_id,
                    StudySession.end_time.isnot(None),
                )
                .order_by(StudySession.start_time.desc())
                .limit(limit)
                .all()
            )
            return [self._session_to_dict(s) for s in sessions]

    # ── FRAME OPERATIONS ─────────────────────────────────

    def add_frame_sample(self, session_id: str, frame_data: Dict[str, Any]) -> None:
        with self.get_db_session() as session:
            frame = SessionFrame(
                session_id=session_id,
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                frame_number=frame_data.get("frame_number", 0),
                focus_state=int(frame_data.get("focus_state", 0)),
                confidence=float(frame_data.get("confidence", 0.0)),
                attention_score=float(frame_data.get("attention_score", 0.0)),
                fatigue_score=float(frame_data.get("fatigue_score", 0.0)),
                ear=float(frame_data.get("ear", 0.0)),
                mar=float(frame_data.get("mar", 0.0)),
                head_pitch=float(frame_data.get("head_pitch", 0.0)),
                head_yaw=float(frame_data.get("head_yaw", 0.0)),
                head_roll=float(frame_data.get("head_roll", 0.0)),
                gaze_x=float(frame_data.get("gaze_x", 0.0)),
                gaze_y=float(frame_data.get("gaze_y", 0.0)),
                blink_rate=float(frame_data.get("blink_rate", 0.0)),
                alerts=json.dumps(frame_data.get("alerts", [])),
                thumbnail_bytes=frame_data.get("thumbnail_bytes"),
            )
            session.add(frame)

    def save_thumbnails(self, session_id: str, frames: list) -> None:
        """Batch insert thumbnails as frame samples."""
        with self.get_db_session() as session:
            from datetime import datetime, timezone
            for f in frames:
                frame = SessionFrame(
                    session_id=session_id,
                    timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                    frame_number=f.frame_number,
                    focus_state=f.focus_state,
                    attention_score=f.attention_score,
                    fatigue_score=f.fatigue_score,
                    ear=f.ear,
                    thumbnail_bytes=f.thumbnail_bytes,
                )
                session.add(frame)

    def get_session_frames(
        self, session_id: str, limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        with self.get_db_session() as session:
            query = (
                session.query(SessionFrame)
                .filter_by(session_id=session_id)
                .order_by(SessionFrame.timestamp.asc())
            )
            if limit:
                query = query.limit(limit)
            return [self._frame_to_dict(f) for f in query.all()]

    # ── BREAK OPERATIONS ─────────────────────────────────

    def record_break_start(
        self, session_id: str, break_type: str = "manual",
        was_recommended: bool = False, trigger_type: Optional[str] = None,
    ) -> int:
        with self.get_db_session() as session:
            break_record = BreakRecord(
                session_id=session_id, break_start=datetime.now(timezone.utc).replace(tzinfo=None),
                break_type=break_type, was_recommended=was_recommended,
                trigger_type=trigger_type,
            )
            session.add(break_record)
            session.flush()
            return break_record.id

    def record_break_end(self, break_id: int) -> None:
        with self.get_db_session() as session:
            br = session.query(BreakRecord).filter_by(id=break_id).first()
            if br:
                br.break_end = datetime.now(timezone.utc).replace(tzinfo=None)
                br.duration_minutes = (br.break_end - br.break_start).total_seconds() / 60

    # ── ANALYTICS QUERIES ────────────────────────────────

    def get_daily_statistics(
        self, date: Optional[datetime] = None, user_id: str = DEFAULT_USER_ID,
    ) -> Dict[str, Any]:
        if date is None:
            date = datetime.now(timezone.utc).replace(tzinfo=None)
        date_str = date.strftime("%Y-%m-%d")

        with self.get_db_session() as session:
            daily = (
                session.query(DailyStatistics)
                .filter_by(user_id=user_id, date=date_str)
                .first()
            )
            if daily:
                return {
                    "date": date_str,
                    "total_study_minutes": daily.total_study_minutes,
                    "session_count": daily.session_count,
                    "avg_focus_percentage": daily.avg_focus_percentage,
                    "total_breaks": daily.total_breaks,
                    "subject_distribution": daily.get_subject_distribution(),
                    "hourly_distribution": daily.get_hourly_distribution(),
                }
        return self._compute_daily_stats(date, user_id)

    def _compute_daily_stats(self, date: datetime, user_id: str) -> Dict[str, Any]:
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        sessions = self.get_sessions_by_date_range(start, end, user_id)

        if not sessions:
            return {
                "date": date.strftime("%Y-%m-%d"), "total_study_minutes": 0,
                "session_count": 0, "avg_focus_percentage": 0,
                "total_breaks": 0, "subject_distribution": {},
                "hourly_distribution": {},
            }

        total_minutes = sum(s.get("duration_minutes", 0) or 0 for s in sessions)
        focus_vals = [s["focus_percentage"] for s in sessions if s.get("focus_percentage") is not None]
        avg_focus = float(np.mean(focus_vals)) if focus_vals else 0.0
        total_breaks = sum(s.get("break_count", 0) or 0 for s in sessions)

        subject_dist: Dict[str, float] = {}
        hourly_dist: Dict[str, float] = {}
        for s in sessions:
            subj = s.get("subject", "General")
            dur = s.get("duration_minutes", 0) or 0
            subject_dist[subj] = subject_dist.get(subj, 0) + dur
            hour = s.get("start_hour", 12)
            hourly_dist[str(hour)] = hourly_dist.get(str(hour), 0) + dur

        return {
            "date": date.strftime("%Y-%m-%d"),
            "total_study_minutes": total_minutes,
            "session_count": len(sessions),
            "avg_focus_percentage": avg_focus,
            "total_breaks": total_breaks,
            "subject_distribution": subject_dist,
            "hourly_distribution": hourly_dist,
        }

    def update_daily_statistics(
        self, date: Optional[datetime] = None, user_id: str = DEFAULT_USER_ID,
    ) -> None:
        if date is None:
            date = datetime.now(timezone.utc).replace(tzinfo=None)
        date_str = date.strftime("%Y-%m-%d")
        computed = self._compute_daily_stats(date, user_id)

        with self.get_db_session() as session:
            daily = session.query(DailyStatistics).filter_by(user_id=user_id, date=date_str).first()
            if daily:
                daily.total_study_minutes = computed["total_study_minutes"]
                daily.session_count = computed["session_count"]
                daily.avg_focus_percentage = computed["avg_focus_percentage"]
                daily.total_breaks = computed["total_breaks"]
                daily.subject_distribution = json.dumps(computed["subject_distribution"])
                daily.hourly_distribution = json.dumps(computed["hourly_distribution"])
                daily.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            else:
                daily = DailyStatistics(
                    user_id=user_id, date=date_str,
                    total_study_minutes=computed["total_study_minutes"],
                    session_count=computed["session_count"],
                    avg_focus_percentage=computed["avg_focus_percentage"],
                    total_breaks=computed["total_breaks"],
                    subject_distribution=json.dumps(computed["subject_distribution"]),
                    hourly_distribution=json.dumps(computed["hourly_distribution"]),
                )
                session.add(daily)

    def get_weekly_stats(self, user_id: str = DEFAULT_USER_ID) -> List[Dict[str, Any]]:
        stats = []
        today = datetime.now(timezone.utc).replace(tzinfo=None)
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            stats.append(self.get_daily_statistics(day, user_id))
        return stats

    def get_subject_stats(
        self, days: int = 30, user_id: str = DEFAULT_USER_ID,
    ) -> Dict[str, Dict[str, Any]]:
        end = datetime.now(timezone.utc).replace(tzinfo=None)
        start = end - timedelta(days=days)
        sessions = self.get_sessions_by_date_range(start, end, user_id)

        subject_data: Dict[str, Dict[str, Any]] = {}
        for s in sessions:
            subj = s.get("subject", "General")
            if subj not in subject_data:
                subject_data[subj] = {"total_minutes": 0, "session_count": 0, "focus_values": [], "hours": []}
            subject_data[subj]["total_minutes"] += s.get("duration_minutes", 0) or 0
            subject_data[subj]["session_count"] += 1
            if s.get("focus_percentage") is not None:
                subject_data[subj]["focus_values"].append(s["focus_percentage"])
            if s.get("start_hour") is not None:
                subject_data[subj]["hours"].append(s["start_hour"])

        result = {}
        for subj, data in subject_data.items():
            fv = data["focus_values"]
            hrs = data["hours"]
            result[subj] = {
                "total_minutes": data["total_minutes"],
                "session_count": data["session_count"],
                "avg_focus_percentage": float(np.mean(fv)) if fv else 0,
                "best_hour": int(np.bincount(hrs).argmax()) if hrs else 10,
            }
        return result

    def get_productivity_heatmap(
        self, days: int = 30, user_id: str = DEFAULT_USER_ID,
    ) -> Dict[str, List[float]]:
        end = datetime.now(timezone.utc).replace(tzinfo=None)
        start = end - timedelta(days=days)
        sessions = self.get_sessions_by_date_range(start, end, user_id)

        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        heatmap: Dict[str, List[float]] = {d: [0.0] * 24 for d in day_names}
        counts: Dict[str, List[int]] = {d: [0] * 24 for d in day_names}

        for s in sessions:
            st = s.get("start_time")
            if not st:
                continue
            if isinstance(st, str):
                st = datetime.fromisoformat(st)
            day = st.strftime("%A").lower()
            hour = st.hour
            focus = s.get("focus_percentage", 0) or 0
            if day in heatmap:
                heatmap[day][hour] += focus
                counts[day][hour] += 1

        for d in day_names:
            for h in range(24):
                if counts[d][h] > 0:
                    heatmap[d][h] /= counts[d][h]
        return heatmap

    def delete_all_data(self, user_id: str = DEFAULT_USER_ID) -> None:
        with self.get_db_session() as session:
            for s in session.query(StudySession).filter_by(user_id=user_id).all():
                session.delete(s)
            for d in session.query(DailyStatistics).filter_by(user_id=user_id).all():
                session.delete(d)
        logger.warning(f"All data deleted for user: {user_id}")

    def export_data(
        self, start_date: datetime, end_date: datetime,
        user_id: str = DEFAULT_USER_ID,
    ) -> Dict[str, Any]:
        sessions = self.get_sessions_by_date_range(start_date, end_date, user_id)
        return {
            "export_date": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "user_id": user_id, "session_count": len(sessions), "sessions": sessions,
        }

    # ── THUMBNAIL OPERATIONS ─────────────────────────────

    def save_thumbnails(
        self, session_id: str, frames: list,
    ) -> None:
        """Save thumbnail frames to database in batch."""
        from datetime import datetime as dt
        with self.get_db_session() as session:
            for frame in frames:
                db_frame = SessionFrame(
                    session_id=session_id,
                    timestamp=dt.utcfromtimestamp(frame.timestamp),
                    frame_number=frame.frame_number,
                    focus_state=frame.focus_state,
                    attention_score=frame.attention_score,
                    ear=frame.ear,
                    fatigue_score=frame.fatigue_score,
                    thumbnail_bytes=frame.thumbnail_bytes,
                )
                session.add(db_frame)

    # ── HELPERS ───────────────────────────────────────────

    @staticmethod
    def _session_to_dict(s: StudySession) -> Dict[str, Any]:
        return {
            "id": s.id, "user_id": s.user_id, "start_time": s.start_time,
            "start_hour": s.start_time.hour if s.start_time else None,
            "end_time": s.end_time, "duration_minutes": s.duration_minutes,
            "subject": s.subject, "tags": s.get_tags(), "notes": s.notes,
            "focus_percentage": s.focus_percentage,
            "avg_attention_score": s.avg_attention_score,
            "distraction_count": s.distraction_count,
            "fatigue_events": s.fatigue_events, "break_count": s.break_count,
            "focused_seconds": s.focused_seconds,
            "distracted_seconds": s.distracted_seconds,
            "fatigued_seconds": s.fatigued_seconds,
        }

    @staticmethod
    def _frame_to_dict(f: SessionFrame) -> Dict[str, Any]:
        alerts = []
        if getattr(f, "alerts", None):
            try:
                alerts = json.loads(f.alerts)
            except Exception:
                pass
        return {
            "id": f.id, "session_id": f.session_id, "timestamp": f.timestamp,
            "frame_number": f.frame_number, "focus_state": f.focus_state,
            "confidence": f.confidence, "attention_score": f.attention_score,
            "fatigue_score": f.fatigue_score, "ear": f.ear, "mar": f.mar,
            "head_pitch": f.head_pitch, "head_yaw": f.head_yaw,
            "head_roll": f.head_roll, "gaze_x": f.gaze_x, "gaze_y": f.gaze_y,
            "blink_rate": f.blink_rate, "alerts": alerts,
            "thumbnail_bytes": f.thumbnail_bytes,
        }
