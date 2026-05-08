"""
Page: dashboard.py
Purpose: Main dashboard — spatial-grade glass panels, staggered animations, aurora aesthetics.
         Integrated with live charts, SVG icons, sound alerts, and AI suggestions.
Version: 3.0.0
"""

from __future__ import annotations

import streamlit as st
from frontend.components.chart_builder import build_daily_trend, build_subject_donut
from frontend.ui.icons import icon, icon_stat, icon_with_label
from frontend.components.toasts import process_alert_toasts
from frontend.components.suggestions import render_suggestion_card


def render_dashboard():
    """Render the premium dashboard page."""

    # Header with Lucide icon
    st.markdown(f"""
<div class="animate-rise">
<h1 style="display: flex; align-items: center; gap: 12px;">
    {icon('bar-chart', 28, '#8B5CF6')}
    Dashboard
</h1>
<p style="color: #64748B; margin-top: -8px; font-size: 0.92rem; letter-spacing: -0.01em;">
Your study performance at a glance
</p>
</div>
""", unsafe_allow_html=True)

    db = st.session_state.get("db_manager")
    aggregator = st.session_state.get("aggregator")

    if not db or not aggregator:
        st.warning("Backend not fully initialized. Some features may be unavailable.")
        return

    # ── Overview Metrics (Icon Stats) ────────────────────
    try:
        overview = aggregator.get_overview(days=7)
    except Exception:
        overview = {"total_study_hours": 0, "avg_focus_percentage": 0, "total_sessions": 0, "streak_days": 0}

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            icon_stat("book-open", f"{overview['total_study_hours']:.1f}h", "Study Hours", "#8B5CF6"),
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            icon_stat("target", f"{overview['avg_focus_percentage']:.0f}%", "Avg Focus", "#22D3EE"),
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            icon_stat("activity", str(overview["total_sessions"]), "Sessions", "#34D399"),
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            icon_stat("flame", f"{overview['streak_days']}d", "Streak", "#F59E0B"),
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ── Quick Start — Hero Card ─────────────────────
    sm = st.session_state.get("session_manager")
    if not sm or not sm.is_active:
        st.markdown(f"""
<div class="hero-card animate-scale delay-2" style="position: relative; overflow: hidden; background: linear-gradient(145deg, rgba(30,41,59,0.5), rgba(15,23,42,0.8)); border: 1px solid rgba(255,255,255,0.05); border-radius: 24px; padding: 48px 32px; box-shadow: 0 20px 40px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.05);">
<div style="position: absolute; top: -50px; right: -50px; width: 200px; height: 200px; background: rgba(34, 211, 238, 0.15); filter: blur(60px); border-radius: 50%; animation: aurora-drift 12s infinite alternate;"></div>
<div style="position: relative; z-index: 2;">
<div style="
width: 64px; height: 64px; margin: 0 auto 20px;
background: rgba(255,255,255,0.03);
border: 1px solid rgba(255,255,255,0.08);
border-radius: 18px;
display: flex; align-items: center; justify-content: center;
box-shadow: 0 10px 25px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.1);
animation: orb-breathe 4s ease-in-out infinite;
">
    {icon('play', 32, '#34D399', 1.5)}
</div>
<div style="
font-size: 1.6rem;
font-weight: 800;
color: #F8FAFC;
letter-spacing: -0.03em;
margin-bottom: 6px;
font-family: 'Inter', sans-serif;
">Ready to dive in?</div>
<div style="
color: #94A3B8;
font-size: 0.95rem;
max-width: 440px;
margin: 0 auto;
line-height: 1.6;
font-weight: 400;
">Start a live session to experience real-time AI focus tracking. Your personal space is 100% private and processed on-device.</div>
</div>
</div>
""", unsafe_allow_html=True)

        st.markdown("")
        col_s1, col_s2, col_s3 = st.columns([1.2, 1, 1])
        with col_s1:
            subject = st.selectbox(
                "Subject",
                ["General", "Mathematics", "Physics", "Computer Science",
                 "Chemistry", "Biology", "English", "History", "Economics"],
                key="dash_subject",
            )
        with col_s2:
            st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
            if st.button("Start Session", icon=":material/play_arrow:", key="dash_start", use_container_width=True):
                st.session_state.current_page = "session"
                st.rerun()
        with col_s3:
            st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
            if st.button("Analytics", icon=":material/insights:", key="dash_analytics", use_container_width=True):
                st.session_state.current_page = "analytics"
                st.rerun()

    # ── Active session: live suggestion card ────────
    if sm.is_active:
        metrics = sm.get_metrics()
        last_result = getattr(metrics, 'last_inference_result', None)

        # Toast notifications for alerts
        if hasattr(metrics, 'alerts') and metrics.alerts:
            process_alert_toasts(metrics.alerts)

        # Sound alerts
        _trigger_sound_alerts(metrics)

        # AI Suggestion card
        elapsed = getattr(metrics, 'session_duration_minutes', 0)
        render_suggestion_card(last_result, elapsed)

    st.markdown("---")

    # ── Charts ──────────────────────────────────────
    chart_col1, chart_col2 = st.columns([3, 2])

    with chart_col1:
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
    {icon('trending-up', 18, '#8B5CF6')}
    <span style="font-size:0.85rem;font-weight:700;color:#F8FAFC;">Daily Study Trend</span>
</div>
""", unsafe_allow_html=True)
        daily_data = aggregator.get_daily_trend(days=14)
        fig = build_daily_trend(daily_data)
        st.plotly_chart(fig, use_container_width=True, key="dash_daily_trend")

    with chart_col2:
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
    {icon('target', 18, '#22D3EE')}
    <span style="font-size:0.85rem;font-weight:700;color:#F8FAFC;">Subject Distribution</span>
</div>
""", unsafe_allow_html=True)
        subject_stats = db.get_subject_stats(days=30)
        fig = build_subject_donut(subject_stats)
        st.plotly_chart(fig, use_container_width=True, key="dash_subject_donut")

    # ── Recent Sessions ─────────────────────────────
    st.markdown(f"""
<div class="animate-rise delay-3">
<h3 style="margin-bottom: 16px; display: flex; align-items: center; gap: 10px;">
    {icon('clock', 20, '#38BDF8')}
    Recent Sessions
</h3>
</div>
""", unsafe_allow_html=True)

    recent = db.get_recent_sessions(limit=5)

    if not recent:
        st.markdown(f"""
<div class="glass-card animate-scale" style="text-align: center; padding: 48px 24px;">
<div style="margin-bottom: 12px; opacity: 0.5;">
    {icon('book-open', 48, '#475569')}
</div>
<div style="color: #64748B; font-size: 0.92rem;">
No sessions yet. Start your first study session above!
</div>
</div>
""", unsafe_allow_html=True)
    else:
        for s in recent:
            focus = s.get("focus_percentage", 0) or 0
            duration = s.get("duration_minutes", 0) or 0
            subj = s.get("subject", "General")
            start = s.get("start_time")
            date_str = start.strftime("%b %d, %H:%M") if start else "Unknown"

            if focus >= 70:
                badge_cls = "focus-badge-high"
            elif focus >= 40:
                badge_cls = "focus-badge-medium"
            else:
                badge_cls = "focus-badge-low"

            st.markdown(f"""
<div class="session-row">
<div style="display: flex; align-items: center; gap: 14px;">
<div style="
width: 38px; height: 38px;
border-radius: 10px;
background: rgba(139, 92, 246, 0.1);
display: flex; align-items: center; justify-content: center;
">
    {icon('book-open', 18, '#8B5CF6')}
</div>
<div>
<div style="font-weight: 600; color: #F8FAFC; font-size: 0.92rem;">{subj}</div>
<div style="color: #475569; font-size: 0.75rem;">{date_str}</div>
</div>
</div>
<div style="display: flex; gap: 20px; align-items: center;">
<span style="color: #94A3B8; font-size: 0.82rem; font-family: 'JetBrains Mono', monospace;">
{duration:.0f}m
</span>
<span class="focus-badge {badge_cls}">● {focus:.0f}%</span>
</div>
</div>
""", unsafe_allow_html=True)

    # ── Insights Preview ────────────────────────────
    st.markdown("---")
    st.markdown(f"""
<div class="animate-rise delay-4">
<h3 style="margin-bottom: 16px; display: flex; align-items: center; gap: 10px;">
    {icon('lightbulb', 20, '#FBBF24')}
    Quick Insights
</h3>
</div>
""", unsafe_allow_html=True)

    try:
        insights = st.session_state.get("insight_engine")
        insights = insights.generate_insights(days=30) if insights else []
    except Exception:
        insights = []

    insight_icons = ["brain", "trending-up", "zap", "award", "target"]
    cols = st.columns(min(len(insights), 3)) if insights else []
    for i, insight in enumerate(insights[:3]):
        with cols[i]:
            title = insight.get('title', '')
            msg = insight.get('message', '')[:110]
            ico = insight_icons[i % len(insight_icons)]

            st.markdown(f"""
<div class="insight-card">
<div style="margin-bottom: 10px;">
    {icon(ico, 28, '#34D399')}
</div>
<div style="
font-weight: 700;
color: #F8FAFC;
font-size: 0.9rem;
margin-bottom: 6px;
letter-spacing: -0.01em;
">{title}</div>
<div style="
color: #94A3B8;
font-size: 0.78rem;
line-height: 1.45;
">{msg}</div>
</div>
""", unsafe_allow_html=True)


def _trigger_sound_alerts(metrics) -> None:
    """Play sound alerts based on session metrics (rate-limited)."""
    import time
    alerts = getattr(metrics, 'alerts', [])
    if not alerts:
        return

    sound_enabled = st.session_state.get("_pref_sound", True)
    if not sound_enabled:
        return

    for alert in alerts:
        atype = getattr(alert, 'type', '')
        severity = getattr(alert, 'severity', 'info')
        key = f"_snd_{atype}_{int(time.time()) // 30}"  # 30s cooldown
        if key in st.session_state:
            continue
        st.session_state[key] = True

        from frontend.components.sound_system import (
            play_critical_alert, play_fatigue_warning,
            play_distraction_alert, play_break_reminder,
        )

        if atype == "microsleep":
            play_critical_alert()
        elif atype == "fatigue":
            play_fatigue_warning()
        elif atype == "looking_away":
            play_distraction_alert()
        elif atype == "yawn":
            play_break_reminder()
