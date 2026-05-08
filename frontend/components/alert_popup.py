"""
Module: alert_popup.py
Purpose: Alert notification display — premium glass panels with entrance animations.
Author: SmartStudy Team
Version: 2.0.0
"""

from __future__ import annotations

from typing import Dict, List

import streamlit as st


def render_alerts(alerts: List[Dict[str, str]], max_display: int = 3) -> None:
    """Render alert notifications with staggered entrance animation."""
    if not alerts:
        return

    recent = alerts[-max_display:]

    for i, alert in enumerate(recent):
        severity = alert.get("severity", "info")
        message = alert.get("message", "")
        delay_class = f"delay-{i + 1}"

        severity_config = {
            "critical": {
                "border": "#F43F5E",
                "bg": "rgba(244, 63, 94, 0.08)",
                "glow": "rgba(244, 63, 94, 0.15)",
                "icon": "🚨",
                "label": "CRITICAL",
            },
            "warning": {
                "border": "#F59E0B",
                "bg": "rgba(245, 158, 11, 0.08)",
                "glow": "rgba(245, 158, 11, 0.12)",
                "icon": "⚠️",
                "label": "WARNING",
            },
            "info": {
                "border": "#8B5CF6",
                "bg": "rgba(139, 92, 246, 0.08)",
                "glow": "rgba(139, 92, 246, 0.1)",
                "icon": "ℹ️",
                "label": "INFO",
            },
        }
        cfg = severity_config.get(severity, severity_config["info"])

        st.markdown(f"""
<div class="animate-slide-right {delay_class}" style="
background: {cfg['bg']};
backdrop-filter: blur(16px);
border-left: 3px solid {cfg['border']};
border-radius: 0 14px 14px 0;
padding: 14px 18px;
margin-bottom: 8px;
display: flex;
align-items: flex-start;
gap: 12px;
box-shadow: 0 2px 12px {cfg['glow']};
transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
">
<div style="
font-size: 1.1rem;
flex-shrink: 0;
margin-top: 1px;
">{cfg['icon']}</div>
<div style="flex: 1;">
<div style="
font-size: 0.65rem;
color: {cfg['border']};
text-transform: uppercase;
letter-spacing: 0.12em;
font-weight: 700;
margin-bottom: 3px;
">{cfg['label']}</div>
<div style="
color: #E2E8F0;
font-size: 0.85rem;
line-height: 1.45;
">{message}</div>
</div>
</div>
""", unsafe_allow_html=True)


def render_break_notification(
    fatigue_score: float,
    recommended_duration: float,
) -> bool:
    """Render break notification with hero card styling. Returns True if accepted."""
    fatigue_pct = int(fatigue_score * 100)

    st.markdown(f"""
<div class="hero-card animate-scale" style="margin: 20px 0;">
<div style="position: relative; z-index: 2;">
<!-- Zen icon with breathing animation -->
<div style="
font-size: 3.5rem;
margin-bottom: 16px;
animation: orb-breathe 3s ease-in-out infinite;
display: inline-block;
">🧘</div>
<div style="
font-size: 1.5rem;
font-weight: 800;
color: #F8FAFC;
letter-spacing: -0.02em;
margin-bottom: 6px;
">Time for a Break</div>
<div style="
font-size: 0.88rem;
color: #94A3B8;
margin-bottom: 20px;
">
Fatigue: <span style="color: #FBBF24; font-weight: 600;">{fatigue_pct}%</span>
&nbsp;·&nbsp;
Suggested: <span style="color: #34D399; font-weight: 600;">{recommended_duration:.0f} min</span>
</div>
</div>
</div>
""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        accepted = st.button("✅ Take Break", key="break_accept", use_container_width=True)
    with col2:
        st.button("⏰ 5 min snooze", key="break_snooze_5", use_container_width=True)
    with col3:
        st.button("⏰ 10 min snooze", key="break_snooze_10", use_container_width=True)

    return accepted
