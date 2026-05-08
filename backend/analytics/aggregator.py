"""
Module: aggregator.py
Purpose: Aggregate session data into meaningful statistics and trends.
Author: SmartStudy Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger

from backend.database.manager import DatabaseManager


class StatsAggregator:
    """
    Computes aggregated statistics across sessions for the analytics dashboard.
    Provides daily, weekly, monthly trends and subject-level breakdowns.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self._db = db_manager or DatabaseManager()

    def get_overview(self, days: int = 7) -> Dict[str, Any]:
        """Get high-level overview statistics."""
        end = datetime.now(timezone.utc).replace(tzinfo=None)
        start = end - timedelta(days=days)
        sessions = self._db.get_sessions_by_date_range(start, end)

        if not sessions:
            return {
                "total_study_hours": 0, "total_sessions": 0,
                "avg_focus_percentage": 0, "total_breaks": 0,
                "avg_session_duration_min": 0, "streak_days": 0,
                "best_day": None, "most_focused_subject": None,
            }

        total_minutes = sum(s.get("duration_minutes", 0) or 0 for s in sessions)
        focus_vals = [s["focus_percentage"] for s in sessions if s.get("focus_percentage")]
        total_breaks = sum(s.get("break_count", 0) or 0 for s in sessions)

        # Find best day
        daily_totals: Dict[str, float] = {}
        for s in sessions:
            if s.get("start_time"):
                day = s["start_time"].strftime("%A") if isinstance(s["start_time"], datetime) else "Unknown"
                daily_totals[day] = daily_totals.get(day, 0) + (s.get("duration_minutes", 0) or 0)
        best_day = max(daily_totals, key=daily_totals.get) if daily_totals else None

        # Most focused subject
        subject_focus: Dict[str, List[float]] = {}
        for s in sessions:
            subj = s.get("subject", "General")
            if s.get("focus_percentage"):
                subject_focus.setdefault(subj, []).append(s["focus_percentage"])
        most_focused = None
        best_avg = 0
        for subj, vals in subject_focus.items():
            avg = float(np.mean(vals))
            if avg > best_avg:
                best_avg = avg
                most_focused = subj

        # Streak (consecutive days with study)
        study_dates = set()
        for s in sessions:
            if s.get("start_time"):
                st = s["start_time"]
                if isinstance(st, datetime):
                    study_dates.add(st.date())
        streak = self._compute_streak(study_dates)

        return {
            "total_study_hours": round(total_minutes / 60, 1),
            "total_sessions": len(sessions),
            "avg_focus_percentage": round(float(np.mean(focus_vals)), 1) if focus_vals else 0,
            "total_breaks": total_breaks,
            "avg_session_duration_min": round(total_minutes / len(sessions), 1),
            "streak_days": streak,
            "best_day": best_day,
            "most_focused_subject": most_focused,
        }

    def get_daily_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily study trend for charting."""
        trend = []
        today = datetime.now(timezone.utc).replace(tzinfo=None)
        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            stats = self._db.get_daily_statistics(date)
            trend.append({
                "date": stats["date"],
                "study_minutes": stats["total_study_minutes"],
                "session_count": stats["session_count"],
                "focus_percentage": stats["avg_focus_percentage"],
            })
        return trend

    def get_hourly_pattern(self, days: int = 30) -> Dict[int, Dict[str, float]]:
        """Compute study patterns by hour of day."""
        end = datetime.now(timezone.utc).replace(tzinfo=None)
        start = end - timedelta(days=days)
        sessions = self._db.get_sessions_by_date_range(start, end)

        hourly: Dict[int, Dict[str, List]] = {
            h: {"durations": [], "focus": []} for h in range(24)
        }

        for s in sessions:
            hour = s.get("start_hour")
            if hour is not None:
                dur = s.get("duration_minutes", 0) or 0
                focus = s.get("focus_percentage", 0) or 0
                hourly[hour]["durations"].append(dur)
                hourly[hour]["focus"].append(focus)

        result = {}
        for h in range(24):
            durs = hourly[h]["durations"]
            focs = hourly[h]["focus"]
            result[h] = {
                "avg_duration_min": float(np.mean(durs)) if durs else 0,
                "total_sessions": len(durs),
                "avg_focus": float(np.mean(focs)) if focs else 0,
            }
        return result

    def get_weekly_comparison(self, user_id: str = "default_user") -> Dict[str, Any]:
        """Compare this week's performance with last week."""
        today = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # This week (last 7 days)
        this_week_start = today - timedelta(days=7)
        this_week_sessions = self._db.get_sessions_by_date_range(this_week_start, today, user_id)
        
        # Last week (7 to 14 days ago)
        last_week_end = this_week_start
        last_week_start = last_week_end - timedelta(days=7)
        last_week_sessions = self._db.get_sessions_by_date_range(last_week_start, last_week_end, user_id)
        
        def summarize(sessions):
            total_min = sum(s.get("duration_minutes", 0) or 0 for s in sessions)
            focus_vals = [s["focus_percentage"] for s in sessions if s.get("focus_percentage")]
            return {
                "hours": round(total_min / 60, 1),
                "sessions": len(sessions),
                "avg_focus": round(float(np.mean(focus_vals)), 1) if focus_vals else 0
            }
            
        return {
            "this_week": summarize(this_week_sessions),
            "last_week": summarize(last_week_sessions)
        }

    def get_focus_stability(self, days: int = 30, user_id: str = "default_user") -> List[Dict[str, Any]]:
        """Compute focus stability (variance) over time."""
        end = datetime.now(timezone.utc).replace(tzinfo=None)
        start = end - timedelta(days=days)
        sessions = self._db.get_sessions_by_date_range(start, end, user_id)
        
        # Group sessions by date
        daily_focus: Dict[str, List[float]] = {}
        for s in sessions:
            if s.get("start_time") and s.get("focus_percentage"):
                d_str = s["start_time"].strftime("%Y-%m-%d")
                daily_focus.setdefault(d_str, []).append(s["focus_percentage"])
        
        stability_trend = []
        for d_str in sorted(daily_focus.keys()):
            vals = daily_focus[d_str]
            stability_trend.append({
                "date": d_str,
                "avg_focus": float(np.mean(vals)),
                "stability": float(np.std(vals)) if len(vals) > 1 else 0
            })
        return stability_trend

    def get_break_impact(self, days: int = 30, user_id: str = "default_user") -> List[Dict[str, Any]]:
        """Analyze correlation between break duration and subsequent session focus."""
        end = datetime.now(timezone.utc).replace(tzinfo=None)
        start = end - timedelta(days=days)
        sessions = self._db.get_sessions_by_date_range(start, end, user_id)
        
        # We need to find sessions that happened on the same day and look at the gap between them
        impact_data = []
        sessions_sorted = sorted([s for s in sessions if s.get("start_time")], key=lambda x: x["start_time"])
        
        for i in range(len(sessions_sorted) - 1):
            s1 = sessions_sorted[i]
            s2 = sessions_sorted[i+1]
            
            # Only consider sessions on the same day
            if s1["start_time"].date() == s2["start_time"].date():
                gap = (s2["start_time"] - s1["end_time"]).total_seconds() / 60
                if 0 < gap < 120: # Focus on gaps less than 2 hours (breaks)
                    impact_data.append({
                        "break_duration": gap,
                        "subsequent_focus": s2.get("focus_percentage", 0)
                    })
        return impact_data

    def _compute_streak(self, study_dates: set) -> int:
        """Compute current study streak in consecutive days."""
        if not study_dates:
            return 0
        today = datetime.now(timezone.utc).replace(tzinfo=None).date()
        streak = 0
        current = today
        while current in study_dates:
            streak += 1
            current -= timedelta(days=1)
        return streak
