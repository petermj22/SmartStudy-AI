"""
Module: timer_display.py
Purpose: Session timer, break countdown, and fatigue meter — premium glassmorphism components.
Author: SmartStudy Team
Version: 2.0.0
"""

from __future__ import annotations

import streamlit as st


def render_session_timer(elapsed_seconds: float, is_active: bool = True) -> None:
    """Render the premium session timer with digit morphism."""
    hours = int(elapsed_seconds // 3600)
    minutes = int((elapsed_seconds % 3600) // 60)
    seconds = int(elapsed_seconds % 60)

    status_color = "#34D399" if is_active else "#FB7185"
    status_glow = "rgba(16,185,129,0.3)" if is_active else "rgba(244,63,94,0.3)"
    status_text = "RECORDING" if is_active else "PAUSED"
    pulse_anim = "animation: orb-breathe 2s ease-in-out infinite;" if is_active else ""

    st.markdown(f"""
<div class="timer-display animate-rise">
<!-- Status dot -->
<div style="
display: flex;
align-items: center;
justify-content: center;
gap: 8px;
margin-bottom: 16px;
">
<div style="
width: 8px;
height: 8px;
border-radius: 50%;
background: {status_color};
box-shadow: 0 0 12px {status_glow};
{pulse_anim}
"></div>
<span style="
font-size: 0.68rem;
color: {status_color};
text-transform: uppercase;
letter-spacing: 0.18em;
font-weight: 600;
">{status_text}</span>
</div>
<!-- Time digits -->
<div class="timer-digits">{hours:02d}:{minutes:02d}:{seconds:02d}</div>
<!-- Subtle label -->
<div style="
font-size: 0.7rem;
color: #475569;
text-transform: uppercase;
letter-spacing: 0.12em;
margin-top: 12px;
">Session Duration</div>
</div>
""", unsafe_allow_html=True)


def render_break_countdown(remaining_seconds: float, total_seconds: float) -> None:
    """Render break countdown timer with zen breathing effect."""
    minutes = int(remaining_seconds // 60)
    seconds = int(remaining_seconds % 60)
    progress = 1.0 - (remaining_seconds / max(total_seconds, 1))

    st.markdown(f"""
<div class="glass-card animate-scale" style="
text-align: center;
border-color: rgba(16, 185, 129, 0.2);
background: linear-gradient(135deg,
rgba(16, 185, 129, 0.06) 0%,
rgba(6, 182, 212, 0.04) 100%
);
">
<div style="
font-size: 0.72rem;
color: #34D399;
text-transform: uppercase;
letter-spacing: 0.15em;
font-weight: 600;
margin-bottom: 12px;
">☕ Break Time</div>
<div style="
font-size: 3.2rem;
font-weight: 200;
color: #F8FAFC;
font-family: 'JetBrains Mono', monospace;
letter-spacing: 0.06em;
text-shadow: 0 0 20px rgba(16, 185, 129, 0.15);
">{minutes:02d}:{seconds:02d}</div>
<!-- Progress bar -->
<div style="margin-top: 16px;">
<div class="fatigue-bar-track">
<div class="fatigue-bar-fill" style="
width: {progress * 100:.1f}%;
background: linear-gradient(90deg, #10B981, #06B6D4);
"></div>
</div>
</div>
</div>
""", unsafe_allow_html=True)


def render_fatigue_meter(fatigue_score: float, minutes_until_break: float) -> None:
    """Render fatigue level meter with animated bar and dynamic theming."""
    if fatigue_score > 0.8:
        color, label, desc = "#FB7185", "CRITICAL", "Take a break now"
        bar_gradient = "linear-gradient(90deg, #F43F5E, #FB7185)"
    elif fatigue_score > 0.6:
        color, label, desc = "#FBBF24", "ELEVATED", "Break recommended soon"
        bar_gradient = "linear-gradient(90deg, #F59E0B, #FBBF24)"
    elif fatigue_score > 0.3:
        color, label, desc = "#A78BFA", "MODERATE", "Pace yourself"
        bar_gradient = "linear-gradient(90deg, #7C3AED, #A78BFA)"
    else:
        color, label, desc = "#34D399", "FRESH", "Optimal mental state"
        bar_gradient = "linear-gradient(90deg, #10B981, #34D399)"

    st.markdown(f"""
<div class="glass-card animate-rise delay-2" style="padding: 18px 22px;">
<!-- Header row -->
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
<div style="display: flex; align-items: center; gap: 8px;">
<span style="font-size: 1rem;">🧠</span>
<span style="
color: #94A3B8;
font-size: 0.72rem;
text-transform: uppercase;
letter-spacing: 0.1em;
font-weight: 500;
">Fatigue Level</span>
</div>
<span style="
color: {color};
font-weight: 700;
font-size: 0.78rem;
letter-spacing: 0.05em;
text-shadow: 0 0 12px {color}44;
">{label}</span>
</div>
<!-- Animated bar -->
<div class="fatigue-bar-track">
<div class="fatigue-bar-fill" style="
width: {fatigue_score * 100:.1f}%;
background: {bar_gradient};
box-shadow: 0 0 12px {color}33;
"></div>
</div>
<!-- Footer -->
<div style="
display: flex;
justify-content: space-between;
align-items: center;
margin-top: 10px;
">
<span style="color: #475569; font-size: 0.72rem;">{desc}</span>
<span style="color: #64748B; font-size: 0.72rem;">
Break in ~{minutes_until_break:.0f}m
</span>
</div>
</div>
""", unsafe_allow_html=True)
