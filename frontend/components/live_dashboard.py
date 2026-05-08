"""
SmartStudy Live Dashboard Component
Real-time animated charts — gauge, timeline, fatigue ring.
Uses Plotly with the Aurora dark theme.
"""

from __future__ import annotations

from typing import List

import plotly.graph_objects as go

from frontend.ui.theme import PLOTLY_THEME, COLORS


class LiveDataStore:
    """Rolling data store for live chart data."""

    def __init__(self, max_len: int = 180):
        self.max_len = max_len
        self.attention_history: List[float] = []
        self.ear_history: List[float] = []
        self.fatigue_history: List[float] = []
        self.state_history: List[int] = []

    def push(self, attention: float, ear: float, fatigue: float, state: int) -> None:
        for arr in [self.attention_history, self.ear_history,
                    self.fatigue_history, self.state_history]:
            if len(arr) >= self.max_len:
                arr.pop(0)

        self.attention_history.append(max(0, min(100, attention)))
        self.ear_history.append(max(0, min(1, ear)) * 100)
        self.fatigue_history.append(max(0, min(1, fatigue)) * 100)
        self.state_history.append(state)


def render_attention_gauge(
    attention_score: float,
    height: int = 220,
) -> go.Figure:
    """Animated gauge chart showing current attention score."""
    score = max(0, min(100, attention_score))

    if score >= 70:
        bar_color = COLORS["emerald_deep"]
    elif score >= 45:
        bar_color = COLORS["amber_deep"]
    else:
        bar_color = COLORS["rose_deep"]

    layout_cfg = PLOTLY_THEME.copy()
    # Remove keys that don't apply to indicator charts or will be overridden
    layout_cfg.pop("xaxis", None)
    layout_cfg.pop("yaxis", None)
    layout_cfg.pop("margin", None)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        delta={
            "reference": 70,
            "increasing": {"color": COLORS["emerald"]},
            "decreasing": {"color": COLORS["rose"]},
            "font": {"size": 14},
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": COLORS["text_dim"],
                "tickvals": [0, 25, 50, 75, 100],
                "ticktext": ["0", "25", "50", "75", "100"],
                "tickfont": {"color": COLORS["text_muted"], "size": 10},
            },
            "bar": {"color": bar_color, "thickness": 0.7},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40],  "color": "rgba(248,113,113,0.12)"},
                {"range": [40, 65], "color": "rgba(251,191,36,0.08)"},
                {"range": [65, 100], "color": "rgba(52,211,153,0.10)"},
            ],
            "threshold": {
                "line": {"color": COLORS["text"], "width": 3},
                "thickness": 0.85,
                "value": 70,
            },
        },
        number={
            "font": {
                "size": 42,
                "family": "JetBrains Mono, monospace",
                "color": COLORS["text"],
            },
            "suffix": "",
        },
        title={
            "text": "Attention Score",
            "font": {"size": 14, "color": COLORS["text_muted"], "family": "Inter"},
        },
    ))

    fig.update_layout(
        **layout_cfg,
        height=height,
        margin=dict(l=20, r=20, t=40, b=10),
    )

    return fig


def render_live_timeline(
    data_store: LiveDataStore,
    height: int = 200,
) -> go.Figure:
    """Rolling focus + EAR + fatigue timeline."""
    if not data_store.attention_history:
        return _empty("Start a session to see live data", height)

    x = list(range(len(data_store.attention_history)))
    layout_cfg = PLOTLY_THEME.copy()
    layout_cfg.pop("margin", None)

    fig = go.Figure()

    # Attention area
    fig.add_trace(go.Scatter(
        x=x, y=data_store.attention_history,
        name="Attention",
        fill="tozeroy",
        fillcolor="rgba(139,92,246,0.08)",
        line=dict(color=COLORS["violet"], width=2.5, shape="spline"),
        hovertemplate="%{y:.0f}%<extra>Attention</extra>",
    ))

    # EAR×100 dotted
    fig.add_trace(go.Scatter(
        x=x, y=data_store.ear_history,
        name="EAR×100",
        line=dict(color=COLORS["emerald"], width=1.5, dash="dot", shape="spline"),
        opacity=0.8,
        hovertemplate="%{y:.1f}<extra>EAR×100</extra>",
    ))

    # Fatigue
    fig.add_trace(go.Scatter(
        x=x, y=data_store.fatigue_history,
        name="Fatigue%",
        line=dict(color=COLORS["rose"], width=1.5, shape="spline"),
        opacity=0.7,
        hovertemplate="%{y:.0f}%<extra>Fatigue</extra>",
    ))

    # Threshold line
    fig.add_hline(
        y=60, line_dash="dash",
        line_color="rgba(239,68,68,0.3)",
        annotation_text="Focus threshold",
        annotation_font=dict(size=10, color=COLORS["rose"]),
    )

    layout_cfg["xaxis"] = dict(visible=False, showgrid=False)
    layout_cfg["yaxis"] = dict(
        range=[0, 105], ticksuffix="%",
        gridcolor=COLORS["grid_line"],
        tickfont=dict(color=COLORS["text_muted"], size=10),
    )

    fig.update_layout(
        **layout_cfg,
        height=height,
        margin=dict(l=40, r=10, t=20, b=30),
        legend=dict(
            orientation="h", y=-0.25, x=0.5, xanchor="center",
            font=dict(size=11, color=COLORS["text_muted"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
    )

    return fig


def render_fatigue_ring(
    fatigue_score: float,
    minutes_until_break: float,
    height: int = 180,
) -> go.Figure:
    """Countdown ring for break timing."""
    fatigue_pct = max(0, min(100, fatigue_score * 100))
    fresh_pct = 100 - fatigue_pct

    color = (
        COLORS["emerald"] if fatigue_pct < 40
        else COLORS["amber"] if fatigue_pct < 70
        else COLORS["rose"]
    )

    layout_cfg = PLOTLY_THEME.copy()
    layout_cfg.pop("xaxis", None)
    layout_cfg.pop("yaxis", None)
    layout_cfg.pop("margin", None)

    fig = go.Figure(go.Pie(
        values=[fresh_pct, fatigue_pct],
        labels=["Fresh", "Fatigued"],
        hole=0.72,
        marker=dict(
            colors=["rgba(255,255,255,0.04)", color],
            line=dict(color="rgba(0,0,0,0.3)", width=2),
        ),
        textinfo="none",
        hoverinfo="skip",
        direction="clockwise",
        rotation=90,
    ))

    # Center label
    break_text = f"{minutes_until_break:.0f}m" if minutes_until_break > 0 else "NOW"
    fig.add_annotation(
        text=(
            f'<b style="font-size:22px;color:{COLORS["text"]}">{fatigue_pct:.0f}%</b><br>'
            f'<span style="font-size:11px;color:{COLORS["text_muted"]}">fatigue</span><br>'
            f'<b style="font-size:14px;color:{color}">Break: {break_text}</b>'
        ),
        x=0.5, y=0.5,
        showarrow=False,
        align="center",
        font=dict(family="Inter", size=12, color=COLORS["text"]),
    )

    fig.update_layout(
        **layout_cfg,
        height=height,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
    )

    return fig


def _empty(msg: str, height: int) -> go.Figure:
    layout_cfg = PLOTLY_THEME.copy()
    layout_cfg.pop("xaxis", None)
    layout_cfg.pop("yaxis", None)
    fig = go.Figure()
    fig.add_annotation(
        text=msg, x=0.5, y=0.5,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=13, color=COLORS["text_muted"], family="Inter"),
    )
    fig.update_layout(**layout_cfg, height=height)
    return fig
