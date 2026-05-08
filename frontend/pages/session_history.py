"""
SmartStudy Session History & Replay Page
Browse past sessions, replay focus timeline, export reports.
"""

from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from backend.core.session_replay import SessionReplayEngine
from backend.database.manager import DatabaseManager
from frontend.ui.icons import icon
from frontend.ui.theme import PLOTLY_THEME


def render_session_history() -> None:
    """Render the session history and replay page."""
    db = st.session_state.get("db_manager")
    if not db:
        st.warning("Database not available.")
        return
    replay_engine = SessionReplayEngine(db)

    st.markdown(
        f"""
        <div class="animate-rise" style="margin-bottom:20px;">
            <div style="display:flex;align-items:center;gap:10px;">
                {icon('book-open', 24, '#8B5CF6')}
                <div>
                    <div style="font-size:22px;font-weight:800;color:#F8FAFC;
                                letter-spacing:-0.02em;">Session History</div>
                    <div style="font-size:12px;color:#64748B;margin-top:2px;">
                        Review, replay, and export your study sessions</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_list, col_detail = st.columns([1, 2], gap="large")

    with col_list:
        _render_session_list(db)

    with col_detail:
        selected_id = st.session_state.get("selected_session_id")
        if selected_id:
            _render_session_detail(db, replay_engine, selected_id)
        else:
            st.markdown(
                f"""
                <div class="glass-card" style="text-align:center;padding:60px 20px;">
                    <div style="font-size:48px;margin-bottom:16px;">📼</div>
                    <div style="font-size:16px;font-weight:600;color:#F8FAFC;">
                        Select a Session to Replay</div>
                    <div style="font-size:13px;color:#64748B;margin-top:8px;">
                        Click any session from the list to view its timeline and export reports.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_session_list(db: DatabaseManager) -> None:
    """Render sortable session list."""
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
            {icon('clock', 18, '#22D3EE')}
            <span style="font-weight:700;font-size:15px;color:#F8FAFC;">Past Sessions</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sessions = db.get_recent_sessions(limit=30)

    if not sessions:
        st.info("No sessions yet. Start studying to build your history!")
        return

    for s in sessions:
        session_id = s.get("id", "")
        start_time = s.get("start_time")
        subject = s.get("subject", "General")
        duration = s.get("duration_minutes", 0) or 0
        focus = s.get("focus_percentage", 0) or 0

        date_str = start_time.strftime("%b %d") if start_time else "—"
        time_str = start_time.strftime("%H:%M") if start_time else "—"

        focus_color = "#34D399" if focus >= 70 else "#FBBF24" if focus >= 50 else "#FB7185"
        focus_dot = "🟢" if focus >= 70 else "🟡" if focus >= 50 else "🔴"

        is_selected = st.session_state.get("selected_session_id") == session_id
        bg = "rgba(139,92,246,0.08)" if is_selected else "rgba(255,255,255,0.02)"
        border = "rgba(139,92,246,0.4)" if is_selected else "rgba(255,255,255,0.06)"

        col_info, col_btn = st.columns([5, 1])
        with col_info:
            st.markdown(
                f"""
                <div style="background:{bg};border:1px solid {border};border-radius:10px;
                            padding:10px 12px;margin-bottom:6px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <div style="font-weight:700;font-size:13px;color:#F8FAFC;">
                                {subject}</div>
                            <div style="font-size:11px;color:#64748B;margin-top:2px;">
                                {date_str} · {time_str} · {duration:.0f}min</div>
                        </div>
                        <div style="font-size:14px;font-weight:800;color:{focus_color};">
                            {focus_dot} {focus:.0f}%</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_btn:
            if st.button("▶", key=f"sel_{session_id}", help="View session"):
                st.session_state["selected_session_id"] = session_id
                st.rerun()


def _render_session_detail(
    db: DatabaseManager, replay_engine: SessionReplayEngine, session_id: str,
) -> None:
    """Render full session detail with replay."""
    session = db.get_session(session_id)
    if not session:
        st.error("Session not found")
        return

    frames = replay_engine.get_session_frames(session_id)
    raw_frames = db.get_session_frames(session_id)

    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
            {icon('activity', 20, '#8B5CF6')}
            <span style="font-size:18px;font-weight:800;color:#F8FAFC;">
                {session.subject} — {session.start_time.strftime('%B %d, %Y') if session.start_time else '—'}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Key metrics row
    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in [
        (c1, f"{session.duration_minutes or 0:.0f}m", "Duration"),
        (c2, f"{session.focus_percentage or 0:.0f}%", "Focus"),
        (c3, str(session.break_count or 0), "Breaks"),
        (c4, str(session.distraction_count or 0), "Distractions"),
    ]:
        with col:
            st.markdown(
                f"""
                <div class="glass-card" style="text-align:center;padding:12px;">
                    <div style="font-size:24px;font-weight:800;color:#F8FAFC;
                                font-family:'JetBrains Mono',monospace;">{val}</div>
                    <div style="font-size:11px;color:#64748B;font-weight:600;
                                text-transform:uppercase;letter-spacing:0.06em;">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # Focus Timeline Chart
    if raw_frames:
        st.markdown(
            f"<div style='font-weight:700;margin-bottom:8px;color:#F8FAFC;'>"
            f"{icon('trending-up', 16, '#3B82F6')} Focus Timeline</div>",
            unsafe_allow_html=True,
        )

        attention_vals = [f.get("attention_score", 0) for f in raw_frames]
        fatigue_vals = [f.get("fatigue_score", 0) * 100 for f in raw_frames]
        states = [f.get("focus_state", -1) for f in raw_frames]
        x = list(range(len(raw_frames)))

        state_colors_map = {0: "#FBBF24", 1: "#34D399", 2: "#FB7185", -1: "#64748B"}
        marker_colors = [state_colors_map.get(s, "#64748B") for s in states]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x, y=attention_vals, name="Attention",
            fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
            line=dict(color="#3B82F6", width=2, shape="spline"),
            hovertemplate="Attention: <b>%{y:.0f}%</b><extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=x, y=fatigue_vals, name="Fatigue",
            line=dict(color="#FB7185", width=1.5, dash="dot"), opacity=0.7,
            hovertemplate="Fatigue: <b>%{y:.0f}%</b><extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=x, y=attention_vals, name="State", mode="markers",
            marker=dict(color=marker_colors, size=5, opacity=0.8),
            showlegend=False,
        ))
        layout_cfg = {**PLOTLY_THEME}
        layout_cfg.pop("margin", None)
        yaxis_cfg = layout_cfg.pop("yaxis", {}).copy()
        yaxis_cfg.update(range=[0, 105], ticksuffix="%")
        
        xaxis_cfg = layout_cfg.pop("xaxis", {}).copy()
        xaxis_cfg.update(visible=False)
        
        fig.update_layout(
            layout_cfg, height=220,
            margin=dict(l=40, r=10, t=20, b=30),
            hovermode="x unified",
            yaxis=yaxis_cfg,
            xaxis=xaxis_cfg,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Thumbnail Replay
    if frames:
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='font-weight:700;margin-bottom:12px;color:#F8FAFC;'>"
            f"{icon('camera', 16, '#8B5CF6')} "
            f"Session Replay ({len(frames)} snapshots)</div>",
            unsafe_allow_html=True,
        )

        frame_idx = st.slider(
            "Timeline", min_value=0, max_value=max(0, len(frames) - 1),
            value=0, key=f"replay_scrubber_{session_id}", label_visibility="collapsed",
        )

        current_frame = frames[frame_idx]
        img = replay_engine.decode_thumbnail(current_frame)

        col_img, col_meta = st.columns([2, 1])
        with col_img:
            st.image(img, use_container_width=True, caption=f"Frame {frame_idx + 1}/{len(frames)}")

        with col_meta:
            state_labels = {0: "😵 Distracted", 1: "🎯 Focused", 2: "😴 Fatigued"}
            state = state_labels.get(current_frame.focus_state, "❓ Unknown")
            st.markdown(
                f"""
                <div class="glass-card" style="padding:16px;font-size:13px;">
                    <div style="font-weight:700;margin-bottom:10px;color:#F8FAFC;">Frame Info</div>
                    <div style="margin-bottom:6px;">
                        <span style="color:#64748B;">State</span><br>
                        <span style="font-weight:700;color:#F8FAFC;">{state}</span></div>
                    <div style="margin-bottom:6px;">
                        <span style="color:#64748B;">Attention</span><br>
                        <span style="font-weight:700;color:#F8FAFC;">{current_frame.attention_score:.0f}%</span></div>
                    <div style="margin-bottom:6px;">
                        <span style="color:#64748B;">EAR</span><br>
                        <span style="font-weight:700;color:#F8FAFC;font-family:monospace;">
                            {current_frame.ear:.3f}</span></div>
                    <div>
                        <span style="color:#64748B;">Fatigue</span><br>
                        <span style="font-weight:700;color:#F8FAFC;">{current_frame.fatigue_score*100:.0f}%</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Export Buttons
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-weight:700;margin-bottom:12px;color:#F8FAFC;'>"
        f"{icon('award', 16, '#FBBF24')} Export</div>",
        unsafe_allow_html=True,
    )

    exp1, exp2, exp3 = st.columns(3)

    with exp1:
        import pandas as pd
        if raw_frames:
            df = pd.DataFrame(raw_frames)
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📊 Export CSV", data=csv_data,
                file_name=f"session_{session_id[:8]}.csv",
                mime="text/csv", use_container_width=True,
            )

    with exp2:
        if st.button("📄 Generate PDF", use_container_width=True):
            with st.spinner("Generating PDF report..."):
                metrics_dict = {
                    "duration_minutes": session.duration_minutes,
                    "focus_percentage": session.focus_percentage,
                    "avg_attention_score": session.avg_attention_score,
                    "break_count": session.break_count,
                    "distraction_count": session.distraction_count,
                    "subject": session.subject,
                }
                output_path = f"data/reports/session_{session_id[:8]}_report.pdf"
                pdf_path = replay_engine.generate_pdf_report(
                    session_id, frames, metrics_dict, output_path)
                if pdf_path and pdf_path.exists():
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download PDF", data=f.read(),
                            file_name=f"session_{session_id[:8]}_report.pdf",
                            mime="application/pdf", use_container_width=True,
                        )
                else:
                    st.error("PDF export requires: pip install reportlab")

    with exp3:
        if frames and st.button("🎬 Export Video", use_container_width=True):
            with st.spinner("Generating summary video..."):
                output_path = f"data/replays/session_{session_id[:8]}_replay.mp4"
                video_path = replay_engine.generate_summary_video(frames, output_path)
                if video_path.exists():
                    with open(video_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download MP4", data=f.read(),
                            file_name=f"session_{session_id[:8]}_replay.mp4",
                            mime="video/mp4", use_container_width=True,
                        )
