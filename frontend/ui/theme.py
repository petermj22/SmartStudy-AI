"""
SmartStudy Design System — Theme Tokens
Centralized theme tokens for Plotly charts and UI components.
Mirrors the Aurora-inspired dark theme from chart_builder.
"""

from __future__ import annotations


# ── Color Palette ─────────────────────────────────────────
COLORS = {
    "violet": "#8B5CF6",
    "violet_light": "#A78BFA",
    "cyan": "#22D3EE",
    "cyan_deep": "#06B6D4",
    "emerald": "#34D399",
    "emerald_deep": "#10B981",
    "rose": "#FB7185",
    "rose_deep": "#F43F5E",
    "amber": "#FBBF24",
    "amber_deep": "#F59E0B",
    "lavender": "#C4B5FD",
    "sky": "#38BDF8",
    "pink": "#F472B6",
    "text": "#F8FAFC",
    "text_muted": "#64748B",
    "text_dim": "#475569",
    "bg": "#09090B",
    "bg_card": "#12121E",
    "grid": "rgba(139, 92, 246, 0.04)",
    "grid_line": "rgba(255, 255, 255, 0.03)",
}

CHART_PALETTE = [
    COLORS["violet"], COLORS["cyan"], COLORS["emerald"],
    COLORS["rose"], COLORS["amber"], COLORS["lavender"],
    COLORS["sky"], COLORS["pink"],
]

# ── Plotly Base Layout ─────────────────────────────────────
PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        family="Inter, -apple-system, sans-serif",
        color=COLORS["text"],
        size=12,
    ),
    margin=dict(l=48, r=24, t=48, b=48),
    xaxis=dict(
        gridcolor=COLORS["grid_line"],
        zerolinecolor=COLORS["grid_line"],
        tickfont=dict(color=COLORS["text_muted"], size=11),
    ),
    yaxis=dict(
        gridcolor=COLORS["grid_line"],
        zerolinecolor=COLORS["grid_line"],
        tickfont=dict(color=COLORS["text_muted"], size=11),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_muted"], size=11),
        bordercolor="rgba(139, 92, 246, 0.1)",
        borderwidth=1,
    ),
    hoverlabel=dict(
        bgcolor="rgba(18, 18, 30, 0.95)",
        bordercolor="rgba(139, 92, 246, 0.3)",
        font=dict(color=COLORS["text"], family="Inter", size=13),
    ),
    title_font=dict(color=COLORS["text"], size=16, family="Inter"),
    title_x=0, title_xanchor="left", title_y=0.98,
)
