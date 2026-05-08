"""
Module: scheduler.py
Purpose: Optimal study schedule recommendations based on historical patterns.
Author: SmartStudy Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger

from backend.database.manager import DatabaseManager


class StudyScheduler:
    """
    Recommends optimal study schedules based on user's historical
    focus patterns and preferred subjects.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self._db = db_manager or DatabaseManager()

    def get_optimal_schedule(
        self, target_hours: float = 4.0, subjects: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate an optimal daily study schedule.

        Args:
            target_hours: Target study hours per day
            subjects: List of subjects to schedule

        Returns:
            List of time blocks with subject recommendations
        """
        # Get historical hourly patterns
        heatmap = self._db.get_productivity_heatmap(days=30)
        subject_stats = self._db.get_subject_stats(days=30)

        # Find peak hours
        today_name = datetime.now().strftime("%A").lower()
        today_pattern = heatmap.get(today_name, [0.0] * 24)

        # Rank hours by historical focus percentage
        hour_scores = [(h, today_pattern[h]) for h in range(6, 23)]
        hour_scores.sort(key=lambda x: x[1], reverse=True)

        # Select top hours to fill target
        blocks_needed = int(target_hours * 2)  # 30-min blocks
        schedule = []
        selected_hours = set()

        for hour, score in hour_scores:
            if len(schedule) >= blocks_needed:
                break
            if hour not in selected_hours:
                selected_hours.add(hour)

                # Assign subject based on difficulty match
                subject = self._assign_subject(hour, subjects, subject_stats)

                schedule.append({
                    "start_hour": hour,
                    "start_time": f"{hour:02d}:00",
                    "end_time": f"{hour:02d}:50",
                    "subject": subject,
                    "predicted_focus": max(score, 50),
                    "recommendation": self._get_time_recommendation(hour),
                })

        schedule.sort(key=lambda x: x["start_hour"])
        return schedule

    def _assign_subject(
        self, hour: int, subjects: Optional[List[str]],
        subject_stats: Dict[str, Dict[str, Any]],
    ) -> str:
        """Assign the best subject for a given hour."""
        if not subjects:
            return "General"

        # Hard subjects in peak hours, easier ones later
        if subject_stats:
            sorted_subjects = sorted(
                subjects,
                key=lambda s: subject_stats.get(s, {}).get("avg_focus_percentage", 50),
            )
            # Hardest subject (lowest focus) goes to best hour slot
            if 8 <= hour <= 11:
                return sorted_subjects[0] if sorted_subjects else "General"
            elif len(sorted_subjects) > 1:
                return sorted_subjects[-1]

        return subjects[0] if subjects else "General"

    def _get_time_recommendation(self, hour: int) -> str:
        if 6 <= hour <= 9:
            return "🌅 Fresh mind — tackle challenging material"
        elif 10 <= hour <= 12:
            return "☀️ Peak alertness — deep focus work"
        elif 13 <= hour <= 14:
            return "🥱 Post-lunch dip — lighter review work"
        elif 15 <= hour <= 17:
            return "📝 Second wind — practice problems"
        elif 18 <= hour <= 20:
            return "🌙 Evening — revision and recall practice"
        else:
            return "💤 Late study — keep sessions short"

    def get_break_recommendation(
        self, session_duration_min: float, fatigue_score: float,
    ) -> Dict[str, Any]:
        """Get break timing recommendation."""
        if fatigue_score > 0.8:
            return {
                "should_break": True,
                "urgency": "high",
                "break_duration_min": 15,
                "message": "🛑 Take a long break now — high fatigue detected",
            }
        elif fatigue_score > 0.6:
            return {
                "should_break": True,
                "urgency": "medium",
                "break_duration_min": 10,
                "message": "⚠️ Break recommended — fatigue building up",
            }
        elif session_duration_min > 50:
            return {
                "should_break": True,
                "urgency": "low",
                "break_duration_min": 5,
                "message": "⏰ Good time for a short Pomodoro break",
            }
        else:
            remaining = max(0, 25 - (session_duration_min % 25))
            return {
                "should_break": False,
                "urgency": "none",
                "break_duration_min": 0,
                "message": f"✅ Going strong — next break in ~{remaining:.0f} min",
            }
