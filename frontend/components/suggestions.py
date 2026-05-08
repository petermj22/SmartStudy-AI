"""
SmartStudy Real-Time Suggestion Engine
Generates contextual study suggestions based on current state.
"""

from __future__ import annotations
import time
from typing import Optional, Tuple
import streamlit as st
from frontend.ui.icons import icon

SUGGESTIONS_DB = {
    "focused_long": ("award", "Excellent Focus!", "You've maintained focus for over 15 minutes. Deep work state!", None),
    "distracted_head": ("eye", "Head Turned Away", "Try repositioning to face your screen directly.", "Reposition camera"),
    "drowsy_ear": ("moon", "Drowsiness Detected", "Eye openness below normal. Try splashing water or 10 jumping jacks.", "Take a 5-min active break"),
    "yawning": ("coffee", "Yawning Detected", "Your brain needs oxygen! Deep breathing: inhale 4s, hold 4s, exhale 6s.", "Try box breathing"),
    "high_blink": ("zap", "Eye Strain Warning", "High blink rate. Practice 20-20-20: every 20 min, look 20ft away for 20s.", "Apply 20-20-20 rule"),
    "break_needed": ("coffee", "Break Time!", "A 5-10 minute break now boosts your next session by 40%.", "Start 5-min break"),
    "low_fatigue": ("flame", "Peak Performance!", "Low fatigue, high attention — tackle your hardest material now!", None),
    "milestone_30": ("award", "30 Min Milestone!", "Deep learning begins at 30 minutes. Great work!", None),
    "milestone_60": ("award", "1 Hour Strong!", "One full hour of studying! Great discipline.", None),
}

def get_current_suggestion(result, session_minutes: float) -> Optional[Tuple]:
    if result is None or not getattr(result, "face_detected", False):
        return None
    fatigue = getattr(result, "fatigue_score", 0)
    ear = getattr(result, "avg_ear", getattr(result, "ear", 0.3))
    blink = getattr(result, "blink_rate", 15)
    yaw = getattr(result, "head_yaw", 0)
    att = getattr(result, "attention_score", 0.5)
    if att <= 1.0: att *= 100
    if 59 < session_minutes < 62: return SUGGESTIONS_DB["milestone_60"]
    if 29 < session_minutes < 32: return SUGGESTIONS_DB["milestone_30"]
    if fatigue > 0.7: return SUGGESTIONS_DB["break_needed"]
    if ear < 0.23: return SUGGESTIONS_DB["drowsy_ear"]
    if blink > 30: return SUGGESTIONS_DB["high_blink"]
    if abs(yaw) > 28: return SUGGESTIONS_DB["distracted_head"]
    if fatigue < 0.2 and att > 75: return SUGGESTIONS_DB["low_fatigue"]
    if att > 85 and session_minutes > 15: return SUGGESTIONS_DB["focused_long"]
    return None

def render_suggestion_card(last_result, session_minutes: float) -> None:
    now = time.time()
    if now - st.session_state.get("_sug_t", 0) < 30:
        cached = st.session_state.get("_sug_c")
        if cached: _render_card(*cached)
        return
    sug = get_current_suggestion(last_result, session_minutes)
    if sug is None: return
    st.session_state["_sug_c"] = sug
    st.session_state["_sug_t"] = now
    _render_card(*sug)

def _render_card(icon_name, title, message, action):
    ico = icon(icon_name, 22, "#8B5CF6")
    act = f'<div style="margin-top:10px;font-size:12px;font-weight:700;color:#8B5CF6;">→ {action}</div>' if action else ""
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(139,92,246,0.06),rgba(34,211,238,0.04));
                border:1px solid rgba(139,92,246,0.15);border-radius:14px;padding:16px;
                box-shadow:0 4px 12px rgba(0,0,0,0.2);">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <div style="background:rgba(139,92,246,0.1);border-radius:8px;width:36px;height:36px;
                        display:flex;align-items:center;justify-content:center;">{ico}</div>
            <div style="font-size:14px;font-weight:700;color:#F8FAFC;">{title}</div>
        </div>
        <div style="font-size:13px;color:#94A3B8;line-height:1.6;">{message}</div>
        {act}
    </div>""", unsafe_allow_html=True)
