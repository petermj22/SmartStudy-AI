"""
SmartStudy Toast Notification Queue
Non-blocking notification system using st.toast.
"""

from __future__ import annotations
import time
import streamlit as st


def show_toast(message: str, type: str = "info", duration: int = 4) -> None:
    icons = {"success": "✅", "warning": "⚠️", "error": "🚨", "info": "💡"}
    st.toast(message, icon=icons.get(type, "ℹ️"))


def process_alert_toasts(alerts: list) -> None:
    if not alerts:
        return
    now = time.time()
    history = st.session_state.get("_toast_hist", {})
    cooldown = 45

    for alert in alerts:
        atype = getattr(alert, "type", "unknown")
        if now - history.get(atype, 0) < cooldown:
            continue
        history[atype] = now
        if atype == "microsleep":
            show_toast("Microsleep detected! Immediate break needed.", "error")
        elif atype == "fatigue":
            show_toast("Fatigue level high — break recommended.", "warning")
        elif atype == "yawn":
            show_toast("Yawning detected — consider rest.", "info")
        elif atype == "looking_away":
            show_toast("Stay focused on your screen!", "info")
        elif atype == "eye_strain":
            show_toast("Eye strain detected — try 20-20-20 rule.", "warning")

    st.session_state["_toast_hist"] = history
