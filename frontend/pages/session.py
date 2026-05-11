"""
Page: session.py
Purpose: Live study session — real-time focus tracking with spatial-grade UI.
         Integrates WebRTC camera, live analytics charts, sound alerts,
         toast notifications, and AI suggestion cards.
Version: 3.0.0
"""

from __future__ import annotations

import time

import streamlit as st

from backend.core.session_manager import SessionState
from frontend.components.focus_indicator import render_focus_indicator
from frontend.components.timer_display import (
    render_session_timer,
    render_fatigue_meter,
    render_break_countdown,
)
from frontend.components.alert_popup import render_alerts
from frontend.ui.icons import icon
from frontend.components.toasts import process_alert_toasts
from frontend.components.suggestions import render_suggestion_card
from frontend.components.webrtc_camera import render_webrtc_camera, _HAS_WEBRTC
from frontend.components.live_dashboard import (
    LiveDataStore,
    render_attention_gauge,
    render_live_timeline,
    render_fatigue_ring,
)


def render_session():
    """Render the live study session page."""
    sm = st.session_state.get("session_manager")

    st.markdown(f"""
<div class="animate-rise">
<h1 style="display: flex; align-items: center; gap: 12px;">
    {icon('camera', 28, '#EF4444')}
    Live Session
</h1>
<p style="color: #64748B; margin-top: -8px; font-size: 0.92rem;">
Real-time AI focus tracking · 100% on-device
</p>
</div>
""", unsafe_allow_html=True)

    if not sm:
        st.warning("Session manager not available. Check backend initialization.")
        return

    if not sm.is_active:
        _render_session_setup()
    elif sm.state == SessionState.ON_BREAK:
        _render_break_mode()
    else:
        _render_active_session()


def _render_session_setup():
    """Render session configuration before starting."""
    sm = st.session_state.get("session_manager")

    st.markdown(f"""
<div class="hero-card animate-scale" style="position: relative; overflow: hidden; background: linear-gradient(145deg, rgba(30,41,59,0.5), rgba(15,23,42,0.8)); border: 1px solid rgba(255,255,255,0.05); border-radius: 24px; padding: 48px 32px; box-shadow: 0 20px 40px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.05);">
<!-- Floating ambient blobs -->
<div style="position: absolute; top: -50px; left: -50px; width: 200px; height: 200px; background: rgba(139, 92, 246, 0.2); filter: blur(60px); border-radius: 50%; animation: aurora-drift 15s infinite alternate;"></div>
<div style="position: absolute; bottom: -50px; right: -50px; width: 200px; height: 200px; background: rgba(34, 211, 238, 0.2); filter: blur(60px); border-radius: 50%; animation: aurora-drift 12s infinite alternate-reverse;"></div>

<div style="position: relative; z-index: 2; text-align: center;">
<div style="
width: 80px; height: 80px; margin: 0 auto 24px;
background: rgba(255,255,255,0.03);
border: 1px solid rgba(255,255,255,0.08);
border-radius: 20px;
display: flex; align-items: center; justify-content: center;
box-shadow: 0 10px 25px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.1);
animation: orb-breathe 4s ease-in-out infinite;
">
    {icon('brain', 36, '#A78BFA', 1.5)}
</div>
<div style="
font-size: 2.2rem;
font-weight: 800;
color: #F8FAFC;
letter-spacing: -0.03em;
margin-bottom: 12px;
font-family: 'Inter', sans-serif;
">Begin Your Session</div>
<div style="
color: #94A3B8;
font-size: 1.05rem;
max-width: 480px;
margin: 0 auto;
line-height: 1.6;
font-weight: 400;
">Position yourself naturally in front of the camera. The AI will securely and privately analyze your focus state, tracking fatigue and optimizing your workflow entirely on-device.</div>
</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("")

    col1, col2 = st.columns(2)
    with col1:
        subject = st.selectbox(
            "Subject",
            ["General", "Mathematics", "Physics", "Computer Science",
             "Chemistry", "Biology", "English", "History", "Economics"],
            key="session_subject",
        )
    with col2:
        tags_input = st.text_input("Tags (comma-separated)", key="session_tags")
        tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []

    st.markdown("")

    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("Start Study Session", icon=":material/play_arrow:", key="start_session", use_container_width=True):
            session_id = sm.start_session(subject=subject, tags=tags, use_webrtc=_HAS_WEBRTC)
            if session_id:
                # Play session start sound
                from frontend.components.sound_system import play_session_start
                if st.session_state.get("_pref_sound", True):
                    play_session_start()
                st.success(f"Session started. ID: {session_id[:8]}")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Failed to start session. Check camera connection.")

    # Camera check
    with st.expander("Camera Setup", icon=":material/videocam:"):
        st.markdown(f"""
<div class="glass-card" style="padding: 16px;">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
    {icon('lightbulb', 20, '#FBBF24')}
    <span style="color: #94A3B8; font-size: 0.85rem;">
    Ensure good lighting and sit facing the camera for accurate detection.
    </span>
</div>
</div>
""", unsafe_allow_html=True)

        # WebRTC availability check
        if _HAS_WEBRTC:
            st.markdown(f"""
<div style="display:flex;align-items:center;gap:8px;padding:8px 12px;margin-top:8px;
            background:rgba(16,185,129,0.06);border-radius:8px;border:1px solid rgba(16,185,129,0.15);">
    {icon('check-circle', 16, '#10B981')}
    <span style="font-size:12px;color:#34D399;font-weight:600;">WebRTC available · Live overlay enabled</span>
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div style="display:flex;align-items:center;gap:8px;padding:8px 12px;margin-top:8px;
            background:rgba(251,191,36,0.06);border-radius:8px;border:1px solid rgba(251,191,36,0.15);">
    {icon('alert-triangle', 16, '#FBBF24')}
    <span style="font-size:12px;color:#FBBF24;font-weight:600;">WebRTC not installed · Using OpenCV capture</span>
</div>
""", unsafe_allow_html=True)

        from backend.core.camera_manager import CameraManager
        cam = CameraManager()
        cameras = cam.get_available_cameras()
        if cameras:
            for c in cameras:
                st.markdown(f"""
<div class="session-row" style="margin-bottom: 6px;">
<div style="display: flex; align-items: center; gap: 10px;">
<div style="width: 8px; height: 8px; border-radius: 50%; background: #34D399;
box-shadow: 0 0 8px rgba(16,185,129,0.4);"></div>
<span style="color: #F8FAFC; font-weight: 500;">Camera {c['id']}</span>
</div>
<span style="color: #64748B; font-size: 0.82rem; font-family: 'JetBrains Mono', monospace;">
{c['width']}×{c['height']} @ {c['fps']}fps
</span>
</div>
""", unsafe_allow_html=True)
        else:
            st.warning("No cameras detected. Please connect a webcam.")


def _render_active_session():
    """Render the active session monitoring view with live charts."""
    sm = st.session_state.get("session_manager")
    metrics = sm.get_metrics()

    # Initialize live data store
    if "live_data" not in st.session_state:
        st.session_state["live_data"] = LiveDataStore(max_len=180)

    # Layout: control panel + main view + analytics
    info_col, main_col, chart_col = st.columns([1.2, 2.2, 1.6], gap="medium")

    with info_col:
        # Timer
        elapsed = metrics.session_duration_minutes * 60
        render_session_timer(elapsed, is_active=(sm.state == SessionState.RUNNING))

        # Focus indicator
        render_focus_indicator(
            focus_state=metrics.current_focus_state,
            focus_label=metrics.current_focus_label,
            confidence=metrics.current_confidence,
            attention_score=metrics.current_attention_score,
        )

        # Fatigue meter
        render_fatigue_meter(
            fatigue_score=metrics.current_fatigue_score,
            minutes_until_break=max(0, 25 - (metrics.session_duration_minutes % 25)),
        )

        # Controls
        st.markdown("---")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if sm.state == SessionState.RUNNING:
                if st.button("Pause", icon=":material/pause:", key="pause_btn", use_container_width=True):
                    sm.pause_session()
                    st.rerun()
            else:
                if st.button("Resume", icon=":material/play_arrow:", key="resume_btn", use_container_width=True):
                    sm.resume_session()
                    st.rerun()
        with col_c2:
            if st.button("Break", icon=":material/coffee:", key="break_btn", use_container_width=True):
                sm.start_break(break_type="manual")
                st.rerun()

        if st.button("End Session", icon=":material/stop:", key="end_btn", use_container_width=True, type="secondary"):
            # Save captured thumbnails before ending the session
            session_id = sm._session_id
            thumb_recorder = st.session_state.get("thumb_recorder")
            if thumb_recorder and session_id:
                try:
                    captured_frames = thumb_recorder.get_frames()
                    if captured_frames:
                        db = st.session_state.get("db_manager")
                        if db:
                            db.save_thumbnails(session_id, captured_frames)
                    thumb_recorder.clear()
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Thumbnail save error: {e}")

            result = sm.end_session()
            if result:
                # Play session end sound
                from frontend.components.sound_system import play_session_end
                if st.session_state.get("_pref_sound", True):
                    play_session_end()
                st.success(f"Session complete. Focus: {result.get('focus_percentage', 0):.0f}%")
                time.sleep(1)
                st.session_state.current_page = "dashboard"
                st.rerun()

        # AI Suggestion card
        render_suggestion_card(
            getattr(metrics, 'last_inference_result', None),
            metrics.session_duration_minutes,
        )

    with main_col:
        # Live metrics strip
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Focus", f"{metrics.focus_percentage:.0f}%")
        with m2:
            st.metric("Distractions", metrics.distraction_count)
        with m3:
            st.metric("Breaks", metrics.break_count)
        with m4:
            st.metric("Fatigue Events", metrics.fatigue_events)

        st.markdown("")

        # Camera feed — WebRTC if available, else simulation
        if _HAS_WEBRTC:
            result = render_webrtc_camera(key="session_camera")
            if result:
                # Update session manager metrics from WebRTC result
                # (in non-WebRTC mode this happens in the processing thread)
                try:
                    sm._update_metrics(result)
                except Exception:
                    pass

                # Save frame sample to database
                try:
                    if result.frame_number % sm._frame_sample_rate == 0:
                        sm._save_frame_sample(result)
                except Exception:
                    pass

                # Push to live data store for charts
                store = st.session_state.get("live_data")
                if store:
                    att = getattr(result, 'attention_score', 0)
                    store.push(
                        attention=att * 100 if att <= 1.0 else att,
                        ear=result.features.avg_ear if result.features else 0,
                        fatigue=getattr(result, 'fatigue_score', 0),
                        state=getattr(result, 'smoothed_focus_state', -1),
                    )
        else:
            _render_camera_simulation()

        # Alerts
        if metrics.alerts:
            # Toast notifications
            process_alert_toasts(metrics.alerts)

            # Sound alerts
            _trigger_session_sounds(metrics.alerts)

            st.markdown(f"""
<div class="animate-rise delay-2">
<h3 style="margin: 20px 0 12px; display: flex; align-items: center; gap: 8px;">
    {icon('alert-triangle', 20, '#FBBF24')}
    Alerts
</h3>
</div>
""", unsafe_allow_html=True)
            render_alerts(metrics.alerts, max_display=3)

    with chart_col:
        # Live analytics panel
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
    {icon('activity', 18, '#8B5CF6')}
    <span style="font-size:14px;font-weight:700;color:#F8FAFC;">Live Analytics</span>
</div>
""", unsafe_allow_html=True)

        # Attention gauge — convert 0-1 score to 0-100 for display
        att_raw = getattr(metrics, 'current_attention_score', 0)
        att_score = att_raw * 100 if att_raw <= 1.0 else att_raw
        st.plotly_chart(
            render_attention_gauge(att_score, height=190),
            use_container_width=True,
            config={"displayModeBar": False, "staticPlot": True},
            key="sess_gauge",
        )

        # Live timeline
        store = st.session_state.get("live_data")
        if store and len(store.attention_history) > 3:
            st.plotly_chart(
                render_live_timeline(store, height=170),
                use_container_width=True,
                config={"displayModeBar": False},
                key="sess_timeline",
            )

        # Fatigue ring
        fatigue = getattr(metrics, 'current_fatigue_score', 0)
        mins_break = max(0, 25 - (metrics.session_duration_minutes % 25))
        st.plotly_chart(
            render_fatigue_ring(fatigue, mins_break, height=160),
            use_container_width=True,
            config={"displayModeBar": False},
            key="sess_fatigue_ring",
        )

        # Detailed metrics
        with st.expander("Detailed Metrics", icon=":material/bar_chart:"):
            det_c1, det_c2 = st.columns(2)
            with det_c1:
                st.metric("Avg EAR", f"{metrics.avg_ear:.3f}")
                st.metric("Focused Time", f"{metrics.focused_seconds:.0f}s")
                st.metric("Total Frames", metrics.total_frames)
            with det_c2:
                st.metric("Blink Rate", f"{metrics.avg_blink_rate:.1f}/min")
                st.metric("Distracted Time", f"{metrics.distracted_seconds:.0f}s")
                st.metric("Fatigued Time", f"{metrics.fatigued_seconds:.0f}s")

    # Auto-refresh
    if sm.state == SessionState.RUNNING:
        time.sleep(5)
        st.rerun()


def _render_camera_simulation():
    """Render HUD-style camera simulation when WebRTC is unavailable."""
    st.markdown("""
<style>
@keyframes scanline {
    0% { transform: translateY(-20px); }
    100% { transform: translateY(400px); }
}
@keyframes pulse-dot {
    0%, 100% { opacity: 0.3; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.2); }
}
.corner { position: absolute; width: 30px; height: 30px; border: 2px solid rgba(56,189,248,0.4); z-index: 4; }
.corner.tl { top: 20px; left: 20px; border-right: none; border-bottom: none; border-top-left-radius: 8px; }
.corner.tr { top: 20px; right: 20px; border-left: none; border-bottom: none; border-top-right-radius: 8px; }
.corner.bl { bottom: 20px; left: 20px; border-right: none; border-top: none; border-bottom-left-radius: 8px; }
.corner.br { bottom: 20px; right: 20px; border-left: none; border-top: none; border-bottom-right-radius: 8px; }
</style>
<div class="camera-feed animate-scale delay-1" style="position: relative; overflow: hidden; background: #0B0F19; border: 1px solid rgba(255,255,255,0.05); border-radius: 20px; box-shadow: inset 0 0 40px rgba(0,0,0,0.5);">
    
    <!-- Video Feed Ambient Background -->
    <div style="position: absolute; inset: 0; background: radial-gradient(circle at center, rgba(30,41,59,0.3) 0%, rgba(15,23,42,0.9) 100%); z-index: 1;"></div>
    
    <!-- Grid overlay -->
    <div style="position: absolute; inset: 0; background-image: linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px); background-size: 30px 30px; z-index: 1; opacity: 0.6;"></div>

    <!-- Scanner Line -->
    <div style="position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, transparent, rgba(56,189,248,0.8), transparent); z-index: 3; box-shadow: 0 0 20px rgba(56,189,248,0.6); animation: scanline 4s linear infinite;"></div>
    
    <!-- HUD Corners -->
    <div class="corner tl"></div><div class="corner tr"></div>
    <div class="corner bl"></div><div class="corner br"></div>
    
    <!-- Center Content -->
    <div style="position: relative; z-index: 5; text-align: center; padding: 80px 20px;">
        <div style="display: flex; justify-content: center; align-items: center; gap: 10px; margin-bottom: 24px;">
            <div style="width: 10px; height: 10px; background-color: #EF4444; border-radius: 50%; animation: pulse-dot 2s infinite; box-shadow: 0 0 10px rgba(239,68,68,0.6);"></div>
            <span style="color: #F8FAFC; letter-spacing: 0.15em; font-weight: 600; font-size: 0.8rem; font-family: 'Inter', sans-serif; text-transform: uppercase;">Live Feed Active</span>
        </div>
        
        <div style="width: 72px; height: 72px; margin: 0 auto 24px; border-radius: 50%; background: rgba(56,189,248,0.05); border: 1px solid rgba(56,189,248,0.2); display: flex; align-items: center; justify-content: center; animation: orb-breathe 4s ease-in-out infinite; box-shadow: inset 0 0 15px rgba(56,189,248,0.1);">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="rgba(56,189,248,0.9)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <circle cx="12" cy="12" r="3"></circle>
            </svg>
        </div>
        
        <div style="color: #94A3B8; font-size: 0.8rem; font-family: 'JetBrains Mono', monospace; display: flex; flex-direction: column; gap: 10px; background: rgba(0,0,0,0.3); padding: 16px; border-radius: 12px; max-width: 260px; margin: 0 auto; border: 1px solid rgba(255,255,255,0.05);">
            <div style="display: flex; justify-content: space-between; width: 100%;">
                <span style="color: #64748B;">&gt; SYS.DETECTION</span>
                <span style="color: #34D399; font-weight: 600;">[OK]</span>
            </div>
            <div style="display: flex; justify-content: space-between; width: 100%;">
                <span style="color: #64748B;">&gt; SYS.LANDMARKS</span>
                <span style="color: #8B5CF6; font-weight: 600;">[SYNC]</span>
            </div>
            <div style="display: flex; justify-content: space-between; width: 100%;">
                <span style="color: #64748B;">&gt; SYS.INFERENCE</span>
                <span style="color: #38BDF8; font-weight: 600;">[ACTIVE]</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


def _trigger_session_sounds(alerts: list) -> None:
    """Play sound alerts based on alert list (rate-limited)."""
    sound_enabled = st.session_state.get("_pref_sound", True)
    if not sound_enabled or not alerts:
        return

    for alert in alerts:
        atype = getattr(alert, 'type', '')
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


def _render_break_mode():
    """Render break mode with zen breathing effect."""
    sm = st.session_state.get("session_manager")

    st.markdown(f"""
<div class="break-mode animate-scale">
<div style="position: relative; z-index: 2; text-align: center;">
<div style="margin-bottom: 16px;">{icon('coffee', 64, '#34D399', 1.5)}</div>
<div style="
font-size: 2rem;
font-weight: 800;
background: linear-gradient(135deg, #34D399, #22D3EE);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
letter-spacing: -0.02em;
margin-bottom: 8px;
">Break Time</div>
<div style="
color: #94A3B8;
font-size: 1rem;
max-width: 400px;
margin: 0 auto;
line-height: 1.6;
">Rest your eyes, stretch, hydrate.<br>Your brain will thank you.</div>
</div>
</div>
""", unsafe_allow_html=True)

    tips = [
        "20-20-20 Rule: Look at something 20 feet away for 20 seconds",
        "Stretch your shoulders, neck, and wrists",
        "Drink some water — dehydration hurts focus",
        "Take a short walk to boost circulation",
        "Deep breathing: 4 in, 7 hold, 8 out",
    ]
    import random
    st.info(random.choice(tips), icon=":material/lightbulb:")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("End Break & Resume", icon=":material/check_circle:", key="end_break", use_container_width=True):
            from frontend.components.sound_system import play_break_end
            if st.session_state.get("_pref_sound", True):
                play_break_end()
            sm.end_break()
            st.rerun()
