"""
Page: analytics.py
Purpose: Deep analytics — heatmaps, trends, and subject breakdowns with aurora aesthetics.
Version: 2.0.0
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import streamlit as st
from frontend.components.chart_builder import (
    build_daily_trend, build_heatmap, build_subject_donut, build_hourly_pattern,
    build_weekly_comparison, build_focus_stability,
)


def render_analytics():
    """Render the analytics page."""
    st.markdown("""
<div class="animate-rise">
<h1 style="display: flex; align-items: center;"><span class="material-symbols-rounded" style="font-size: 1.1em; color: #38BDF8; margin-right: 12px;">insights</span> Analytics</h1>
<p style="color: #64748B; margin-top: -8px; font-size: 0.92rem;">
Deep dive into your study patterns
</p>
</div>
""", unsafe_allow_html=True)

    db = st.session_state.get("db_manager")
    aggregator = st.session_state.get("aggregator")

    if not db or not aggregator:
        st.warning("Backend not fully initialized. Analytics unavailable.")
        return

    # Time range selector
    col_range, _ = st.columns([1, 3])
    with col_range:
        days = st.selectbox(
            "Time Range", [7, 14, 30, 90], index=2,
            format_func=lambda x: f"Last {x} days",
        )

    try:
        overview = aggregator.get_overview(days=days)
    except Exception:
        overview = {
            "total_study_hours": 0, "avg_focus_percentage": 0,
            "total_sessions": 0, "avg_session_duration_min": 0, "total_breaks": 0,
        }

    # ── Top Metrics ─────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Total Hours", f"{overview['total_study_hours']:.1f}h")
    with m2:
        st.metric("Avg Focus", f"{overview['avg_focus_percentage']:.0f}%")
    with m3:
        st.metric("Sessions", overview["total_sessions"])
    with m4:
        st.metric("Avg Duration", f"{overview['avg_session_duration_min']:.0f}m")
    with m5:
        st.metric("Total Breaks", overview["total_breaks"])

    st.markdown("---")

    # ── Charts ──────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Daily Trend", "Heatmap", "Subjects", "Sessions", "Long-Term Trends"
    ])

    with tab1:
        daily_data = aggregator.get_daily_trend(days=days)
        fig = build_daily_trend(daily_data)
        st.plotly_chart(fig, use_container_width=True, key="analytics_daily")

    with tab2:
        heatmap_data = db.get_productivity_heatmap(days=days)
        fig = build_heatmap(heatmap_data)
        st.plotly_chart(fig, use_container_width=True, key="analytics_heatmap")

        st.markdown("""
<div style="
color: #475569;
font-size: 0.78rem;
text-align: center;
margin-top: -8px;
">
Brighter cells = higher focus. Use this to plan your optimal study schedule.
</div>
""", unsafe_allow_html=True)

    with tab3:
        subject_stats = db.get_subject_stats(days=days)
        if subject_stats:
            fig = build_subject_donut(subject_stats)
            st.plotly_chart(fig, use_container_width=True, key="analytics_subjects")

            st.markdown("""
<div class="animate-rise">
<h4 style="margin: 16px 0 12px; color: #E2E8F0;">Subject Breakdown</h4>
</div>
""", unsafe_allow_html=True)

            for subj, data in sorted(
                subject_stats.items(),
                key=lambda x: x[1]["total_minutes"],
                reverse=True,
            ):
                focus = data.get("avg_focus_percentage", 0)
                if focus >= 70:
                    badge_cls = "focus-badge-high"
                elif focus >= 40:
                    badge_cls = "focus-badge-medium"
                else:
                    badge_cls = "focus-badge-low"

                st.markdown(f"""
<div class="session-row">
<div style="display: flex; align-items: center; gap: 12px;">
<div style="
width: 36px; height: 36px;
border-radius: 8px;
background: rgba(139, 92, 246, 0.1);
display: flex; align-items: center; justify-content: center;
font-size: 1.2rem;
font-family: 'Material Symbols Rounded';
color: #8B5CF6;
">book</div>
<span style="font-weight: 600; color: #F8FAFC; font-size: 0.9rem;">{subj}</span>
</div>
<div style="display: flex; gap: 20px; align-items: center;">
<span style="
color: #64748B;
font-size: 0.8rem;
font-family: 'JetBrains Mono', monospace;
">{data['total_minutes']:.0f}m · {data['session_count']} sess</span>
<span class="focus-badge {badge_cls}">● {focus:.0f}%</span>
</div>
</div>
""", unsafe_allow_html=True)
        else:
            st.info("No subject data yet. Start studying to see breakdowns.")

    with tab4:
        end = datetime.now(timezone.utc).replace(tzinfo=None)
        start = end - timedelta(days=days)
        sessions = db.get_sessions_by_date_range(start, end)

        if sessions:
            st.markdown(f"""
<div style="color: #94A3B8; font-size: 0.85rem; margin-bottom: 12px;">
<strong style="color: #F8FAFC;">{len(sessions)}</strong> sessions in the last {days} days
</div>
""", unsafe_allow_html=True)

            for s in sessions[:20]:
                focus = s.get("focus_percentage", 0) or 0
                duration = s.get("duration_minutes", 0) or 0
                subject = s.get("subject", "General")
                start_t = s.get("start_time")
                date_str = (
                    start_t.strftime("%Y-%m-%d %H:%M")
                    if isinstance(start_t, datetime)
                    else str(start_t)
                )

                if focus >= 70:
                    badge_cls = "focus-badge-high"
                elif focus >= 40:
                    badge_cls = "focus-badge-medium"
                else:
                    badge_cls = "focus-badge-low"

                st.markdown(f"""
<div class="session-row">
<div style="flex: 1;">
<span style="font-weight: 600; color: #F8FAFC;">{subject}</span>
<span style="color: #475569; font-size: 0.78rem; margin-left: 10px;">{date_str}</span>
</div>
<div style="display: flex; gap: 16px; align-items: center;">
<span style="
color: #64748B;
font-size: 0.82rem;
font-family: 'JetBrains Mono', monospace;
">{duration:.0f}m</span>
<span class="focus-badge {badge_cls}">● {focus:.0f}%</span>
</div>
</div>
""", unsafe_allow_html=True)
        else:
            st.info("No completed sessions found in this time range.")

    with tab5:
        st.markdown("""
<div class="animate-rise">
<h3 style="color: #A78BFA; margin-bottom: 20px;">Growth & Stability Insights</h3>
</div>
""", unsafe_allow_html=True)
        
        # Weekly Comparison
        comp_data = aggregator.get_weekly_comparison()
        fig_comp = build_weekly_comparison(comp_data)
        st.plotly_chart(fig_comp, use_container_width=True, key="weekly_growth")
        
        # Stability Trend
        stability_data = aggregator.get_focus_stability(days=days)
        fig_stab = build_focus_stability(stability_data)
        st.plotly_chart(fig_stab, use_container_width=True, key="focus_stability")
        
        st.markdown("""
<div class="glass-card" style="margin-top: 20px; border-left: 4px solid #06B6D4;">
<h4 style="color: #F8FAFC; margin-bottom: 8px;">💡 Study Insight</h4>
<p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.5;">
Your focus stability ribbon indicates how consistent your attention is. 
A <b>narrower ribbon</b> means you're reaching a "flow state" more consistently across different study sessions.
</p>
</div>
""", unsafe_allow_html=True)

    # ── Hourly Pattern ──────────────────────────────
    st.markdown("---")
    st.markdown("""
<div class="animate-rise delay-3">
<h3 style="display: flex; align-items: center;"><span class="material-symbols-rounded" style="margin-right: 8px; color: #F87171;">schedule</span> Hourly Focus Pattern</h3>
</div>
""", unsafe_allow_html=True)

    hourly = aggregator.get_hourly_pattern(days=days)
    fig = build_hourly_pattern(hourly)
    st.plotly_chart(fig, use_container_width=True, key="hourly_pattern")
