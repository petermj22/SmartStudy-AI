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

    # SVG icons for each state (inline, no external deps)
    _icon_focused = (
        '<svg width="36" height="36" viewBox="0 0 24 24" fill="none" '
        'stroke="#34D399" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/>'
        '<circle cx="12" cy="12" r="2"/></svg>'
    )
    _icon_distracted = (
        '<svg width="36" height="36" viewBox="0 0 24 24" fill="none" '
        'stroke="#FB7185" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'
    )
    _icon_fatigued = (
        '<svg width="36" height="36" viewBox="0 0 24 24" fill="none" '
        'stroke="#FBBF24" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>'
    )

    state_config = {
        1: {
            "color": "#34D399",
            "glow": "rgba(16, 185, 129, 0.25)",
            "orb_class": "focus-orb-focused",
            "label": "FOCUSED",
            "icon_svg": _icon_focused,
            "ring_color": "#10B981",
            "status_text": "Deep focus detected",
        },
        0: {
            "color": "#FB7185",
            "glow": "rgba(244, 63, 94, 0.25)",
            "orb_class": "focus-orb-distracted",
            "label": "DISTRACTED",
            "icon_svg": _icon_distracted,
            "ring_color": "#F43F5E",
            "status_text": "Attention drifting",
        },
        2: {
            "color": "#FBBF24",
            "glow": "rgba(245, 158, 11, 0.25)",
            "orb_class": "focus-orb-fatigued",
            "label": "FATIGUED",
            "icon_svg": _icon_fatigued,
            "ring_color": "#F59E0B",
            "status_text": "Mental fatigue rising",
        },
    }
    cfg = state_config.get(focus_state, state_config[1])
    conf_pct = int(confidence * 100)
    attn_pct = int(attention_score * 100) if attention_score <= 1.0 else int(attention_score)

    # Animated gradient ring around the orb
    st.markdown(f"""
<div class="glass-card animate-scale" style="padding: 28px 20px; text-align: center;">
<!-- Animated Orb -->
<div class="focus-orb {cfg['orb_class']}" style="margin: 0 auto 20px;">
<div style="
position: relative;
z-index: 2;
display: flex;
align-items: center;
justify-content: center;
filter: drop-shadow(0 0 12px {cfg['glow']});
">{cfg['icon_svg']}</div>
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
