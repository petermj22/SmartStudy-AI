"""
Module: focus_indicator.py
Purpose: Real-time focus state indicator — Orb-style animated component.
Author: SmartStudy Team
Version: 2.0.0
"""

from __future__ import annotations

import streamlit as st


def render_focus_indicator(
    focus_state: int,
    focus_label: str,
    confidence: float,
    attention_score: float,
) -> None:
    """Render the animated orb focus indicator with glassmorphism panel."""

    state_config = {
        1: {
            "color": "#34D399",
            "glow": "rgba(16, 185, 129, 0.25)",
            "orb_class": "focus-orb-focused",
            "label": "FOCUSED",
            "icon": "✦",
            "ring_color": "#10B981",
            "status_text": "Deep focus detected",
        },
        0: {
            "color": "#FB7185",
            "glow": "rgba(244, 63, 94, 0.25)",
            "orb_class": "focus-orb-distracted",
            "label": "DISTRACTED",
            "icon": "⚡",
            "ring_color": "#F43F5E",
            "status_text": "Attention drifting",
        },
        2: {
            "color": "#FBBF24",
            "glow": "rgba(245, 158, 11, 0.25)",
            "orb_class": "focus-orb-fatigued",
            "label": "FATIGUED",
            "icon": "◑",
            "ring_color": "#F59E0B",
            "status_text": "Mental fatigue rising",
        },
    }
    cfg = state_config.get(focus_state, state_config[1])
    conf_pct = int(confidence * 100)
    attn_pct = int(attention_score * 100)

    # Animated gradient ring around the orb
    st.markdown(f"""
<div class="glass-card animate-scale" style="padding: 28px 20px; text-align: center;">
<!-- Animated Orb -->
<div class="focus-orb {cfg['orb_class']}" style="margin: 0 auto 20px;">
<div style="
position: relative;
z-index: 2;
font-size: 2.8rem;
line-height: 1;
filter: drop-shadow(0 0 12px {cfg['glow']});
">{cfg['icon']}</div>
</div>
<!-- State Label -->
<div style="
font-size: 1.1rem;
font-weight: 800;
color: {cfg['color']};
letter-spacing: 0.15em;
text-transform: uppercase;
text-shadow: 0 0 20px {cfg['glow']};
margin-bottom: 4px;
">{cfg['label']}</div>
<div style="
font-size: 0.78rem;
color: #64748B;
margin-bottom: 16px;
">{cfg['status_text']}</div>
<!-- Metrics Row -->
<div style="display: flex; justify-content: center; gap: 24px;">
<div>
<div style="
font-size: 1.6rem;
font-weight: 700;
color: #F8FAFC;
font-family: 'JetBrains Mono', monospace;
">{conf_pct}<span style="font-size: 0.7rem; color: #64748B;">%</span></div>
<div style="font-size: 0.68rem; color: #475569; text-transform: uppercase; letter-spacing: 0.1em;">
Confidence
</div>
</div>
<div style="width: 1px; background: rgba(139, 92, 246, 0.15);"></div>
<div>
<div style="
font-size: 1.6rem;
font-weight: 700;
color: #F8FAFC;
font-family: 'JetBrains Mono', monospace;
">{attn_pct}<span style="font-size: 0.7rem; color: #64748B;">%</span></div>
<div style="font-size: 0.68rem; color: #475569; text-transform: uppercase; letter-spacing: 0.1em;">
Attention
</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)


def render_mini_indicator(focus_state: int) -> str:
    """Return a small HTML badge for the focus state."""
    config = {
        1: ("focus-badge-high", "Focused", "●"),
        0: ("focus-badge-low", "Distracted", "●"),
        2: ("focus-badge-medium", "Fatigued", "●"),
    }
    cls, label, dot = config.get(focus_state, config[1])
    return f'<span class="focus-badge {cls}">{dot} {label}</span>'
