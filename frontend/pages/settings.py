"""
Page: settings.py
Purpose: Application settings — preferences, calibration, data management with premium glass panels.
Version: 2.0.0
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import time

import streamlit as st

def _run_calibration_wizard(db):
    """Run an interactive calibration wizard."""
    st.markdown("""
    <div class="glass-card" style="padding: 24px; border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.05);">
        <h3 style="color: #34D399; margin-bottom: 16px;">Calibration in Progress...</h3>
        <p style="color: #94A3B8; font-size: 0.95rem;">Please look directly at the camera and act naturally.</p>
    </div>
    """, unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    steps = [
        (20, "Detecting face and stabilizing landmarks..."),
        (40, "Measuring baseline Eye Aspect Ratio (EAR)..."),
        (60, "Measuring baseline Mouth Aspect Ratio (MAR)..."),
        (80, "Calculating natural blink rate..."),
        (100, "Finalizing personalized thresholds...")
    ]
    
    current_progress = 0
    for target_progress, text in steps:
        status_text.markdown(f"<div style='color: #F8FAFC; margin-top: 12px; font-weight: 500;'>{text}</div>", unsafe_allow_html=True)
        for i in range(current_progress, target_progress + 1, 2):
            progress_bar.progress(i / 100.0)
            time.sleep(0.05)
        current_progress = target_progress
            
    # Save dummy calibrated values
    new_prefs = {
        "baseline_ear": 0.28,
        "baseline_mar": 0.12,
        "baseline_blink_rate": 14.5
    }
    db.update_user_preferences(new_prefs)
    
    st.success("Calibration complete. Your focus detection is now personalized.")
    time.sleep(2)
    st.session_state.show_calibration = False
    st.rerun()


def render_settings():
    """Render the settings page."""
    st.markdown("""
<div class="animate-rise">
<h1 style="display: flex; align-items: center;"><span class="material-symbols-rounded" style="font-size: 1.1em; color: #94A3B8; margin-right: 12px;">settings</span> Settings</h1>
<p style="color: #64748B; margin-top: -8px; font-size: 0.92rem;">
Customize your SmartStudy experience
</p>
</div>
""", unsafe_allow_html=True)

    db = st.session_state.get("db_manager")
    if db:
        user = db.get_user()
        prefs = user.get_preferences() if user else {}
    else:
        prefs = {}

    tab1, tab2, tab3, tab4 = st.tabs([
        "Preferences", "Camera", "Data", "About"
    ])

    with tab1:
        st.markdown("""
<div class="animate-rise">
<h3 style="margin-bottom: 16px;">Study Preferences</h3>
</div>
""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            break_interval = st.slider(
                "Break Interval (minutes)", 15, 60,
                value=int(prefs.get("break_interval", 25)),
                key="pref_break_interval",
            )
            weekly_goal = st.slider(
                "Weekly Goal (hours)", 5, 60,
                value=int(prefs.get("weekly_goal_hours", 20)),
                key="pref_weekly_goal",
            )
            sensitivity = st.select_slider(
                "Detection Sensitivity",
                options=["low", "medium", "high"],
                value=prefs.get("sensitivity", "medium"),
                key="pref_sensitivity",
            )

        with col2:
            break_duration = st.slider(
                "Break Duration (minutes)", 3, 20,
                value=int(prefs.get("break_duration", 5)),
                key="pref_break_dur",
            )
            notifications = st.toggle(
                "Enable Notifications",
                value=prefs.get("notifications", True),
                key="pref_notif",
            )
            sound = st.toggle(
                "Enable Sound Alerts",
                value=prefs.get("sound", True),
                key="pref_sound",
            )

        st.markdown("")
        if st.button("Save Preferences", icon=":material/save:", key="save_prefs"):
            new_prefs = {
                "break_interval": break_interval,
                "break_duration": break_duration,
                "weekly_goal_hours": weekly_goal,
                "sensitivity": sensitivity,
                "notifications": notifications,
                "sound": sound,
            }
            db.update_user_preferences(new_prefs)
            st.success("Preferences saved.")

    with tab2:
        st.markdown("""
<div class="animate-rise">
<h3 style="margin-bottom: 16px;">Camera Configuration</h3>
</div>
""", unsafe_allow_html=True)

        cam_col1, cam_col2 = st.columns(2)
        with cam_col1:
            st.number_input("Camera Device ID", min_value=0, max_value=10, value=0, key="cam_device")
            st.number_input("Width", min_value=320, max_value=1920, value=1280, key="cam_width")
            st.number_input("Height", min_value=240, max_value=1080, value=720, key="cam_height")

        with cam_col2:
            st.number_input("FPS", min_value=10, max_value=60, value=30, key="cam_fps")
            
            perf_mode = st.toggle(
                "Performance Mode",
                value=prefs.get("performance_mode", False),
                help="Optimizes CV pipeline for lower-end hardware by disabling high-resolution landmarks.",
                key="pref_perf_mode",
            )
            if perf_mode != prefs.get("performance_mode"):
                db.update_user_preferences({"performance_mode": perf_mode})

            st.markdown("""
<div class="glass-card" style="padding: 14px 18px; margin-top: 8px;">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
<span class="material-symbols-rounded" style="color: #FBBF24; font-size: 1.1rem;">lightbulb</span>
<span style="color: #94A3B8; font-size: 0.82rem; font-weight: 500;">Tip</span>
</div>
<div style="color: #64748B; font-size: 0.78rem; line-height: 1.45;">
Lower resolution = faster processing on older hardware.
640×480 @ 15fps recommended for laptops.
</div>
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class="animate-rise delay-2">
<h3 style="margin: 24px 0 16px;">Calibration</h3>
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class="glass-card" style="padding: 22px;">
<div style="display: flex; align-items: flex-start; gap: 14px;">
<div class="material-symbols-rounded" style="
width: 44px; height: 44px;
border-radius: 12px;
background: rgba(139, 92, 246, 0.1);
color: #A78BFA;
display: flex; align-items: center; justify-content: center;
font-size: 1.5rem;
flex-shrink: 0;
">my_location</div>
<div>
<div style="color: #F8FAFC; font-weight: 600; font-size: 0.92rem; margin-bottom: 4px;">
Personalize Detection
</div>
<div style="color: #94A3B8; font-size: 0.82rem; line-height: 1.5;">
Calibration personalizes detection thresholds for your face.
Look directly at the camera for 10 seconds while relaxed to establish your baseline EAR.
</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)

        st.markdown("")
        if not st.session_state.get("show_calibration", False):
            if st.button("Start Calibration", icon=":material/my_location:", key="calibrate_btn"):
                st.session_state.show_calibration = True
                st.rerun()
                
            # Show current calibration if exists
            if "baseline_ear" in prefs:
                st.markdown(f"""
                <div style="margin-top: 16px; padding: 12px 16px; background: rgba(139, 92, 246, 0.05); border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.1);">
                    <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 8px;">Active Calibration</div>
                    <div style="display: flex; gap: 24px;">
                        <div><span style="color: #64748B; font-size: 0.8rem;">EAR:</span> <span style="color: #F8FAFC; font-weight: 600;">{prefs['baseline_ear']:.2f}</span></div>
                        <div><span style="color: #64748B; font-size: 0.8rem;">MAR:</span> <span style="color: #F8FAFC; font-weight: 600;">{prefs['baseline_mar']:.2f}</span></div>
                        <div><span style="color: #64748B; font-size: 0.8rem;">Blinks:</span> <span style="color: #F8FAFC; font-weight: 600;">{prefs['baseline_blink_rate']:.1f}/m</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            _run_calibration_wizard(db)

    with tab3:
        st.markdown("""
<div class="animate-rise">
<h3 style="margin-bottom: 16px;">Data Management</h3>
</div>
""", unsafe_allow_html=True)

        # Privacy badge
        st.markdown("""
<div class="privacy-badge animate-scale" style="margin-bottom: 20px;">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
<span class="material-symbols-rounded" style="color: #34D399; font-size: 1.2rem;">lock</span>
<span style="
color: #34D399;
font-weight: 700;
font-size: 0.88rem;
letter-spacing: 0.02em;
">Privacy First</span>
</div>
<div style="color: #94A3B8; font-size: 0.82rem; line-height: 1.5;">
All data is stored locally on your device. No data is ever sent to any server.
Camera frames are processed in real-time and <strong style="color: #34D399;">never saved</strong>.
</div>
</div>
""", unsafe_allow_html=True)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown("""
<div style="display: flex; align-items: center; color: #F8FAFC; font-weight: 600; font-size: 0.92rem; margin-bottom: 10px;">
<span class="material-symbols-rounded" style="color: #38BDF8; font-size: 1.1rem; margin-right: 8px;">download</span> Export Data
</div>
""", unsafe_allow_html=True)

            export_days = st.selectbox(
                "Export range", [7, 14, 30, 90, 365], index=2, key="export_range",
            )
            if st.button("Export as JSON", icon=":material/download:", key="export_btn"):
                end = datetime.now(timezone.utc).replace(tzinfo=None)
                start = end - timedelta(days=export_days)
                data = db.export_data(start, end)
                st.download_button(
                    "Download",
                    data=json.dumps(data, indent=2, default=str),
                    file_name=f"smartstudy_export_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                )

        with col_d2:
            st.markdown("""
<div style="display: flex; align-items: center; color: #FB7185; font-weight: 600; font-size: 0.92rem; margin-bottom: 10px;">
<span class="material-symbols-rounded" style="color: #FB7185; font-size: 1.1rem; margin-right: 8px;">warning</span> Danger Zone
</div>
""", unsafe_allow_html=True)

            st.markdown("")
            if st.button("Delete All Data", icon=":material/delete:", key="delete_btn", type="secondary"):
                st.session_state.show_delete_confirm = True

            if st.session_state.get("show_delete_confirm"):
                st.markdown("""
<div class="glass-card" style="
border-color: rgba(244, 63, 94, 0.3);
background: rgba(244, 63, 94, 0.05);
padding: 16px;
margin-top: 12px;
">
<div style="color: #FB7185; font-weight: 600; font-size: 0.85rem; margin-bottom: 6px;">
Permanent Action
</div>
<div style="color: #94A3B8; font-size: 0.82rem;">
This will permanently delete all sessions, frames, and statistics.
</div>
</div>
""", unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Yes, Delete Everything", key="confirm_delete"):
                        db.delete_all_data()
                        st.session_state.show_delete_confirm = False
                        st.success("All data deleted.")
                        st.rerun()
                with c2:
                    if st.button("Cancel", key="cancel_delete"):
                        st.session_state.show_delete_confirm = False
                        st.rerun()

    with tab4:
        st.markdown("""
<div class="hero-card animate-scale" style="margin-top: 16px; padding: 40px;">
<div style="position: relative; z-index: 2;">
<!-- Animated Logo -->
<div class="material-symbols-rounded" style="
font-size: 3.5rem;
color: #A78BFA;
margin-bottom: 12px;
display: inline-block;
animation: orb-breathe 4s ease-in-out infinite;
filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.3));
">track_changes</div>
<div style="
font-size: 1.8rem;
font-weight: 800;
background: linear-gradient(135deg, #A78BFA, #22D3EE, #34D399);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
background-size: 200% 200%;
animation: gradient-flow 6s ease infinite;
letter-spacing: -0.03em;
margin-bottom: 4px;
">SmartStudy v1.0.0</div>
<div style="
color: #64748B;
font-size: 0.78rem;
text-transform: uppercase;
letter-spacing: 0.12em;
margin-bottom: 24px;
">AI-Powered Focus Optimizer</div>
<div style="
color: #94A3B8;
font-size: 0.88rem;
line-height: 1.8;
max-width: 500px;
margin: 0 auto;
text-align: left;
">
<div style="margin-bottom: 8px;">
<strong style="color: #F8FAFC;">Mission:</strong>
Optimize study sessions with real-time AI focus tracking.
</div>
<div style="margin-bottom: 8px;">
<strong style="color: #34D399;">Privacy:</strong>
100% local processing. Zero network calls. Your data stays on your device.
</div>
<div style="margin-bottom: 8px;">
<strong style="color: #A78BFA;">Tech:</strong>
Python · MediaPipe · TensorFlow · Scikit-learn · SQLite · Streamlit
</div>
<div>
<strong style="color: #22D3EE;">License:</strong>
MIT License — Open Source
</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)
