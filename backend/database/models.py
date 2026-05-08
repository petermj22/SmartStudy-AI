"""
Module: models.py
Purpose: SQLAlchemy ORM model definitions for SmartStudy database.
Author: SmartStudy Team
Version: 1.0.0

Defines: User, StudySession, SessionFrame, BreakRecord, DailyStatistics
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _json_default() -> str:
    return "{}"


def _json_list_default() -> str:
    return "[]"


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    """User profile model."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(
        DateTime, default=_now, onupdate=_now, nullable=False,
    )
    preferences = Column(Text, default=_json_default)
    calibration = Column(Text, default=_json_default)

    sessions = relationship(
        "StudySession", back_populates="user",
        cascade="all, delete-orphan", lazy="dynamic",
    )
    daily_statistics = relationship(
        "DailyStatistics", back_populates="user",
        cascade="all, delete-orphan", lazy="dynamic",
    )

    def get_preferences(self) -> Dict[str, Any]:
        try:
            return json.loads(self.preferences or "{}")
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_preferences(self, prefs: Dict[str, Any]) -> None:
        self.preferences = json.dumps(prefs)

    def get_calibration(self) -> Dict[str, Any]:
        try:
            return json.loads(self.calibration or "{}")
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_calibration(self, calib: Dict[str, Any]) -> None:
        self.calibration = json.dumps(calib)

    def __repr__(self) -> str:
        return f"<User id={self.id!r} name={self.name!r}>"


class StudySession(Base):
    """Study session model."""

    __tablename__ = "study_sessions"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    start_time = Column(DateTime, nullable=False, default=_now)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Float, nullable=True)
    subject = Column(String(100), default="General", nullable=False)
    tags = Column(Text, default=_json_list_default)
    notes = Column(Text, default="")
    focus_percentage = Column(Float, default=0.0)
    avg_attention_score = Column(Float, default=0.0)
    distraction_count = Column(Integer, default=0)
    fatigue_events = Column(Integer, default=0)
    break_count = Column(Integer, default=0)
    focused_seconds = Column(Float, default=0.0)
    distracted_seconds = Column(Float, default=0.0)
    fatigued_seconds = Column(Float, default=0.0)
    avg_ear = Column(Float, nullable=True)
    avg_blink_rate = Column(Float, nullable=True)
    peak_focus_hour = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    user = relationship("User", back_populates="sessions")
    frames = relationship(
        "SessionFrame", back_populates="session",
        cascade="all, delete-orphan", lazy="dynamic",
    )
    breaks = relationship(
        "BreakRecord", back_populates="session",
        cascade="all, delete-orphan", lazy="dynamic",
    )

    def get_tags(self) -> List[str]:
        try:
            return json.loads(self.tags or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    def set_tags(self, tags: List[str]) -> None:
        self.tags = json.dumps(tags)

    @property
    def is_active(self) -> bool:
        return self.end_time is None

    def __repr__(self) -> str:
        return (
            f"<StudySession id={self.id!r} subject={self.subject!r}"
            f" focus={self.focus_percentage:.1f}%>"
        )


class SessionFrame(Base):
    """Individual frame sample model (stored at ~1fps)."""

    __tablename__ = "session_frames"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String(36), ForeignKey("study_sessions.id", ondelete="CASCADE"), nullable=False,
    )
    timestamp = Column(DateTime, nullable=False, default=_now)
    frame_number = Column(Integer, nullable=True)
    focus_state = Column(Integer, nullable=False)
    confidence = Column(Float, default=0.0)
    attention_score = Column(Float, default=0.0)
    fatigue_score = Column(Float, default=0.0)
    ear = Column(Float, default=0.0)
    mar = Column(Float, default=0.0)
    head_pitch = Column(Float, default=0.0)
    head_yaw = Column(Float, default=0.0)
    head_roll = Column(Float, default=0.0)
    gaze_x = Column(Float, default=0.0)
    gaze_y = Column(Float, default=0.0)
    blink_rate = Column(Float, default=0.0)
    alerts = Column(Text, default=_json_list_default)
    thumbnail_bytes = Column(LargeBinary, nullable=True)  # JPEG bytes for replay

    session = relationship("StudySession", back_populates="frames")

    def get_alerts(self) -> List[Dict]:
        try:
            return json.loads(self.alerts or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    def __repr__(self) -> str:
        return f"<SessionFrame id={self.id} state={self.focus_state}>"


class BreakRecord(Base):
    """Break record model."""

    __tablename__ = "break_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String(36), ForeignKey("study_sessions.id", ondelete="CASCADE"), nullable=False,
    )
    break_start = Column(DateTime, nullable=False, default=_now)
    break_end = Column(DateTime, nullable=True)
    duration_minutes = Column(Float, nullable=True)
    break_type = Column(String(20), default="manual")
    was_recommended = Column(Boolean, default=False)
    trigger_type = Column(String(50), nullable=True)
    user_accepted = Column(Boolean, default=True)

    session = relationship("StudySession", back_populates="breaks")

    def __repr__(self) -> str:
        return f"<BreakRecord id={self.id} type={self.break_type!r}>"


class DailyStatistics(Base):
    """Pre-aggregated daily statistics model."""

    __tablename__ = "daily_statistics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    date = Column(String(10), nullable=False)
    total_study_minutes = Column(Float, default=0.0)
    session_count = Column(Integer, default=0)
    avg_focus_percentage = Column(Float, default=0.0)
    total_breaks = Column(Integer, default=0)
    subject_distribution = Column(Text, default=_json_default)
    hourly_distribution = Column(Text, default=_json_default)
    best_session_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    user = relationship("User", back_populates="daily_statistics")

    def get_subject_distribution(self) -> Dict[str, float]:
        try:
            return json.loads(self.subject_distribution or "{}")
        except (json.JSONDecodeError, TypeError):
            return {}

    def get_hourly_distribution(self) -> Dict[str, float]:
        try:
            return json.loads(self.hourly_distribution or "{}")
        except (json.JSONDecodeError, TypeError):
            return {}

    def __repr__(self) -> str:
        return f"<DailyStatistics date={self.date!r} study={self.total_study_minutes:.0f}m>"


# Composite indexes
Index("idx_sessions_user_date", StudySession.user_id, StudySession.start_time)
Index("idx_daily_stats_user_date", DailyStatistics.user_id, DailyStatistics.date, unique=True)
