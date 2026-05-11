"""
Page: insights.py
Purpose: AI-generated study insights and schedule recommendations — premium glass panels.
Version: 2.0.0
"""

from __future__ import annotations

import streamlit as st
from backend.analytics.scheduler import StudyScheduler


def render_insights():
    """Render the AI insights page."""
    st.markdown("""
<div class="animate-rise">
<h1 style="display: flex; align-items: center;"><span class="material-symbols-rounded" style="font-size: 1.1em; color: #FBBF24; margin-right: 12px;">lightbulb</span> AI Insights</h1>
<p style="color: #64748B; margin-top: -8px; font-size: 0.92rem;">
Personalized recommendations powered by your data
</p>
</div>
""", unsafe_allow_html=True)

    insight_engine = st.session_state.get("insight_engine")

    # ── Insights ────────────────────────────────────
    try:
        insights = insight_engine.generate_insights(days=30) if insight_engine else []
    except Exception:
        insights = []

    for i, insight in enumerate(insights):
        icon = insight.get("icon", "info")
        title = insight.get("title", "")
        message = insight.get("message", "")
        itype = insight.get("type", "info")

        color_map = {
            "trend_up": "#34D399",
            "peak_hour": "#8B5CF6",
            "break_benefit": "#FBBF24",
            "trend_down": "#FB7185",
        }
        border_color = color_map.get(itype, "#8B5CF6")
        delay = f"delay-{min(i + 1, 6)}"

        st.markdown(f"""
<div class="glass-card animate-slide-right {delay}" style="
border-left: 3px solid {border_color};
border-radius: 0 {int(20)}px {int(20)}px 0;
margin-bottom: 12px;
padding: 20px 24px;
">
<div style="display: flex; align-items: flex-start; gap: 14px;">
<div style="
flex-shrink: 0;
width: 44px;
height: 44px;
border-radius: 12px;
background: {border_color}15;
display: flex;
align-items: center;
justify-content: center;
"><span style="display:block;width:10px;height:10px;border-radius:50%;background:{border_color};"></span></div>
<div style="flex: 1;">
<div style="
font-weight: 700;
color: #F8FAFC;
font-size: 0.95rem;
margin-bottom: 4px;
letter-spacing: -0.01em;
">{title}</div>
<div style="
color: #94A3B8;
font-size: 0.85rem;
line-height: 1.55;
">{message}</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)

    # ── Optimal Schedule ────────────────────────────
    st.markdown("---")
    st.markdown("""
<div class="animate-rise delay-3">
<h3 style="display: flex; align-items: center;"><span class="material-symbols-rounded" style="margin-right: 8px; color: #38BDF8;">calendar_month</span> Recommended Study Schedule</h3>
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        target_hours = st.slider(
            "Target hours/day", 1.0, 8.0, 4.0, 0.5, key="sched_hours",
        )
        subjects = st.multiselect(
            "Subjects",
            ["Mathematics", "Physics", "Computer Science", "Chemistry",
             "Biology", "English", "History", "Economics"],
            default=["Mathematics", "Computer Science"],
            key="sched_subjects",
        )

    db = st.session_state.get("db_manager")
    scheduler = StudyScheduler(db) if db else None
    if scheduler:
        schedule = scheduler.get_optimal_schedule(
            target_hours=target_hours, subjects=subjects or None,
        )
    else:
        schedule = []

    with col2:
        if schedule:
            for block in schedule:
                focus = block.get("predicted_focus", 50)
                if focus >= 70:
                    focus_color, badge_cls = "#34D399", "focus-badge-high"
                elif focus >= 50:
                    focus_color, badge_cls = "#A78BFA", "focus-badge-medium"
                else:
                    focus_color, badge_cls = "#FBBF24", "focus-badge-medium"

                st.markdown(f"""
<div class="schedule-block">
<div style="display: flex; align-items: center; gap: 14px;">
<span style="
color: #A78BFA;
font-weight: 700;
font-size: 0.88rem;
font-family: 'JetBrains Mono', monospace;
min-width: 110px;
">{block['start_time']} – {block['end_time']}</span>
<span style="
color: #F8FAFC;
font-weight: 500;
font-size: 0.92rem;
">{block['subject']}</span>
</div>
<span class="focus-badge {badge_cls}">~{focus:.0f}%</span>
</div>
<div style="
color: #475569;
font-size: 0.72rem;
margin: -4px 0 8px 24px;
font-style: italic;
">{block.get('recommendation', '')}</div>
""", unsafe_allow_html=True)
        else:
            st.info("Add subjects to generate a schedule recommendation.")

    # ── Study Tips ──────────────────────────────────
    st.markdown("---")
    st.markdown("""
<div class="animate-rise delay-4">
<h3 style="display: flex; align-items: center;"><span class="material-symbols-rounded" style="margin-right: 8px; color: #34D399;">psychology</span> Science-Backed Study Tips</h3>
</div>
""", unsafe_allow_html=True)

    tips = [
        ("timer", "Pomodoro Technique",
         "25 min focus + 5 min break. After 4 cycles, take a 15-30 min break."),
        ("replay", "Spaced Repetition",
         "Review material at increasing intervals: 1 day, 3 days, 7 days, 14 days."),
        ("ads_click", "Active Recall",
         "Close notes and try to recall. Testing yourself beats re-reading by 50%."),
        ("bedtime", "Sleep & Memory",
         "7-9 hours of sleep consolidates memory. Never sacrifice sleep for study."),
        ("water_drop", "Hydration",
         "Even mild dehydration impairs cognitive function by up to 25%."),
        ("directions_run", "Exercise",
         "20 min of aerobic exercise before studying improves focus by ~20%."),
    ]

    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(tips):
        with cols[i % 3]:
            st.markdown(f"""
<div class="tip-card">
<div class="tip-icon material-symbols-rounded" style="color: #A78BFA; font-size: 1.5rem; margin-bottom: 8px;">{icon}</div>
<div style="
font-weight: 700;
color: #F8FAFC;
font-size: 0.88rem;
margin-bottom: 6px;
letter-spacing: -0.01em;
">{title}</div>
<div style="
color: #94A3B8;
font-size: 0.78rem;
line-height: 1.45;
">{desc}</div>
</div>
""", unsafe_allow_html=True)
