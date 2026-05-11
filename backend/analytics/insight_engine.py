"""
Module: insight_engine.py
Purpose: Generate personalized AI insights from study session data.
Author: SmartStudy Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger

from backend.database.manager import DatabaseManager


class InsightEngine:
    """
    Generates actionable study insights from historical session data.
    Requires 5+ sessions before producing meaningful recommendations.
    """

    MIN_SESSIONS_FOR_INSIGHTS = 5

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self._db = db_manager or DatabaseManager()

    def generate_insights(self, days: int = 30) -> List[Dict[str, Any]]:
        """Generate personalized insights from recent sessions."""
        end = datetime.now(timezone.utc).replace(tzinfo=None)
        start = end - timedelta(days=days)
        sessions = self._db.get_sessions_by_date_range(start, end)

        if len(sessions) < self.MIN_SESSIONS_FOR_INSIGHTS:
            return [{
                "type": "info", "icon": "info",
                "title": "Keep going!",
                "message": f"Complete {self.MIN_SESSIONS_FOR_INSIGHTS - len(sessions)} more sessions to unlock personalized insights.",
                "priority": 0,
            }]

        insights = []
        insights.extend(self._peak_hour_insight(sessions))
        insights.extend(self._focus_trend_insight(sessions))
        insights.extend(self._break_effectiveness_insight(sessions))
        insights.extend(self._subject_insight(sessions))
        insights.extend(self._session_duration_insight(sessions))
        insights.extend(self._consistency_insight(sessions))

        insights.sort(key=lambda x: x.get("priority", 0), reverse=True)
        return insights[:7]

    def _peak_hour_insight(self, sessions: List[Dict]) -> List[Dict]:
        hourly_focus: Dict[int, List[float]] = {}
        for s in sessions:
            h = s.get("start_hour")
            f = s.get("focus_percentage")
            if h is not None and f is not None:
                hourly_focus.setdefault(h, []).append(f)

        if not hourly_focus:
            return []

        avg_by_hour = {h: float(np.mean(v)) for h, v in hourly_focus.items() if len(v) >= 2}
        if not avg_by_hour:
            return []

        best_hour = max(avg_by_hour, key=avg_by_hour.get)
        best_focus = avg_by_hour[best_hour]

        period = "morning" if best_hour < 12 else "afternoon" if best_hour < 17 else "evening"
        return [{
            "type": "peak_hour", "icon": "schedule",
            "title": f"Your peak focus time is {best_hour}:00",
            "message": f"You average {best_focus:.0f}% focus during the {period}. Schedule important subjects here.",
            "priority": 3,
        }]

    def _focus_trend_insight(self, sessions: List[Dict]) -> List[Dict]:
        if len(sessions) < 6:
            return []

        recent = sessions[:len(sessions) // 2]
        older = sessions[len(sessions) // 2:]

        recent_avg = float(np.mean([s.get("focus_percentage", 0) for s in recent if s.get("focus_percentage")]))
        older_avg = float(np.mean([s.get("focus_percentage", 0) for s in older if s.get("focus_percentage")]))

        diff = recent_avg - older_avg
        if abs(diff) < 3:
            return []

        if diff > 0:
            return [{
                "type": "trend_up", "icon": "trending_up",
                "title": f"Focus improved by {diff:.0f}%!",
                "message": f"Your recent sessions average {recent_avg:.0f}% focus vs {older_avg:.0f}% before. Keep it up!",
                "priority": 4,
            }]
        else:
            return [{
                "type": "trend_down", "icon": "trending_down",
                "title": f"Focus dropped by {abs(diff):.0f}%",
                "message": f"Recent: {recent_avg:.0f}% vs earlier: {older_avg:.0f}%. Try shorter sessions with more breaks.",
                "priority": 4,
            }]

    def _break_effectiveness_insight(self, sessions: List[Dict]) -> List[Dict]:
        with_breaks = [s for s in sessions if (s.get("break_count") or 0) > 0]
        without_breaks = [s for s in sessions if (s.get("break_count") or 0) == 0]

        if len(with_breaks) < 3 or len(without_breaks) < 3:
            return []

        focus_with = float(np.mean([s.get("focus_percentage", 0) for s in with_breaks]))
        focus_without = float(np.mean([s.get("focus_percentage", 0) for s in without_breaks]))

        diff = focus_with - focus_without
        if diff > 5:
            return [{
                "type": "break_benefit", "icon": "coffee",
                "title": "Breaks boost your focus!",
                "message": f"Sessions with breaks: {focus_with:.0f}% focus vs without: {focus_without:.0f}%. Don't skip breaks!",
                "priority": 3,
            }]
        return []

    def _subject_insight(self, sessions: List[Dict]) -> List[Dict]:
        subject_focus: Dict[str, List[float]] = {}
        for s in sessions:
            subj = s.get("subject", "General")
            f = s.get("focus_percentage")
            if f is not None:
                subject_focus.setdefault(subj, []).append(f)

        if len(subject_focus) < 2:
            return []

        avgs = {subj: float(np.mean(v)) for subj, v in subject_focus.items() if len(v) >= 2}
        if len(avgs) < 2:
            return []

        best = max(avgs, key=avgs.get)
        worst = min(avgs, key=avgs.get)

        if avgs[best] - avgs[worst] > 10:
            return [{
                "type": "subject_gap", "icon": "menu_book",
                "title": f"You focus best on {best}",
                "message": f"{best}: {avgs[best]:.0f}% focus vs {worst}: {avgs[worst]:.0f}%. Try studying {worst} during your peak hours.",
                "priority": 2,
            }]
        return []

    def _session_duration_insight(self, sessions: List[Dict]) -> List[Dict]:
        durations = [s.get("duration_minutes", 0) for s in sessions if s.get("duration_minutes")]
        if not durations:
            return []

        avg_dur = float(np.mean(durations))

        short = [s for s in sessions if (s.get("duration_minutes") or 0) < 30]
        long_sessions = [s for s in sessions if (s.get("duration_minutes") or 0) > 60]

        if len(short) >= 2 and len(long_sessions) >= 2:
            short_focus = float(np.mean([s.get("focus_percentage", 0) for s in short]))
            long_focus = float(np.mean([s.get("focus_percentage", 0) for s in long_sessions]))

            if short_focus > long_focus + 10:
                return [{
                    "type": "duration", "icon": "timer",
                    "title": "Shorter sessions work better for you",
                    "message": f"Under 30min: {short_focus:.0f}% focus vs over 60min: {long_focus:.0f}%. Try Pomodoro technique.",
                    "priority": 2,
                }]
        return []

    def _consistency_insight(self, sessions: List[Dict]) -> List[Dict]:
        study_dates = set()
        for s in sessions:
            st = s.get("start_time")
            if st and isinstance(st, datetime):
                study_dates.add(st.date())

        total_days = 30
        active_days = len(study_dates)
        consistency = (active_days / total_days) * 100

        if consistency >= 70:
            return [{
                "type": "consistency", "icon": "local_fire_department",
                "title": f"Great consistency — {active_days} active days!",
                "message": f"You studied {consistency:.0f}% of the last {total_days} days. Consistency beats intensity!",
                "priority": 2,
            }]
        elif consistency < 30:
            return [{
                "type": "consistency", "icon": "event",
                "title": "Build a study habit",
                "message": f"You studied {active_days}/{total_days} days. Try scheduling fixed study times.",
                "priority": 1,
            }]
        return []
