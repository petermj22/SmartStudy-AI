"""
Module: chart_builder.py
Purpose: Plotly chart builders — premium dark theme with Aurora-inspired color palettes.
Author: SmartStudy Team
Version: 2.0.0
"""

from __future__ import annotations

from typing import Any, Dict, List

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ─── Aurora-Inspired Theme Tokens ────────────────────
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
    "grid": "rgba(139, 92, 246, 0.04)",
    "grid_line": "rgba(255, 255, 255, 0.03)",
}

CHART_PALETTE = [
    COLORS["violet"], COLORS["cyan"], COLORS["emerald"],
    COLORS["rose"], COLORS["amber"], COLORS["lavender"],
    COLORS["sky"], COLORS["pink"],
]

LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, -apple-system, sans-serif", color=COLORS["text"], size=12),
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


def build_focus_timeline(frames: List[Dict]) -> go.Figure:
    """Build focus state timeline chart with gradient fills."""
    if not frames:
        return _empty_chart("No session data yet")

    timestamps = [f.get("timestamp", i) for i, f in enumerate(frames)]
    states = [f.get("focus_state", 1) for f in frames]
    confidence = [f.get("confidence", 0.5) for f in frames]

    color_map = {0: COLORS["rose"], 1: COLORS["emerald"], 2: COLORS["amber"]}
    colors = [color_map.get(s, COLORS["text_muted"]) for s in states]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(states))), y=states,
        mode="markers",
        marker=dict(color=colors, size=5, opacity=0.8,
                    line=dict(width=0)),
        name="Focus State",
    ))
    fig.add_trace(go.Scatter(
        x=list(range(len(confidence))), y=confidence,
        mode="lines",
        line=dict(color=COLORS["violet"], width=2,
                  shape="spline", smoothing=1.3),
        fill="tozeroy",
        fillcolor="rgba(139, 92, 246, 0.06)",
        name="Confidence", yaxis="y2",
    ))

    layout_cfg = LAYOUT.copy()
    yaxis_cfg = layout_cfg.pop("yaxis", {}).copy()
    yaxis_cfg.update(
        title="State", tickvals=[0, 1, 2],
        ticktext=["Distracted", "Focused", "Fatigued"]
    )
    fig.update_layout(
        layout_cfg, height=320,
        title_text="Focus Timeline",
        yaxis=yaxis_cfg,
        yaxis2=dict(
            title="Confidence", overlaying="y", side="right",
            range=[0, 1], gridcolor=COLORS["grid_line"],
            tickfont=dict(color=COLORS["text_muted"], size=11),
        ),
    )
    return fig


def build_daily_trend(daily_data: List[Dict]) -> go.Figure:
    """Build daily study trend — bar + area overlay."""
    if not daily_data:
        return _empty_chart("Start studying to see trends")

    dates = [d["date"] for d in daily_data]
    minutes = [d.get("study_minutes", 0) for d in daily_data]
    focus = [d.get("focus_percentage", 0) for d in daily_data]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Study time bars with gradient-like effect
    fig.add_trace(go.Bar(
        x=dates, y=minutes, name="Study Time",
        marker=dict(
            color=minutes,
            colorscale=[
                [0, "rgba(139, 92, 246, 0.3)"],
                [0.5, "rgba(139, 92, 246, 0.6)"],
                [1, COLORS["violet"]],
            ],
            cornerradius=6,
            line=dict(width=0),
        ),
        opacity=0.85,
    ), secondary_y=False)

    # Focus % as smooth area
    fig.add_trace(go.Scatter(
        x=dates, y=focus, name="Focus %",
        line=dict(color=COLORS["emerald"], width=2.5, shape="spline", smoothing=1.3),
        mode="lines+markers",
        marker=dict(size=6, color=COLORS["emerald"],
                    line=dict(color="rgba(18,18,30,0.9)", width=2)),
        fill="tozeroy",
        fillcolor="rgba(16, 185, 129, 0.05)",
    ), secondary_y=True)

    fig.update_layout(
        LAYOUT, height=380,
        title_text="Daily Study Trend",
        barmode="group",
        bargap=0.3,
    )
    fig.update_yaxes(
        title_text="Minutes", secondary_y=False,
        gridcolor=COLORS["grid_line"],
        tickfont=dict(color=COLORS["text_muted"]),
    )
    fig.update_yaxes(
        title_text="Focus %", secondary_y=True,
        range=[0, 100],
        gridcolor=COLORS["grid_line"],
        tickfont=dict(color=COLORS["text_muted"]),
    )
    return fig


def build_subject_donut(subject_data: Dict[str, Dict]) -> go.Figure:
    """Build subject distribution — premium donut with center text."""
    if not subject_data:
        return _empty_chart("No subject data")

    labels = list(subject_data.keys())
    values = [d.get("total_minutes", 0) for d in subject_data.values()]
    total = sum(values)

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.65,
        marker=dict(
            colors=CHART_PALETTE[:len(labels)],
            line=dict(color="rgba(9,9,11,0.8)", width=2),
        ),
        textinfo="label+percent",
        textfont=dict(size=11, color=COLORS["text"]),
        textposition="outside",
        pull=[0.03] * len(labels),
        hovertemplate="<b>%{label}</b><br>%{value:.0f} min (%{percent})<extra></extra>",
    ))

    # Center annotation
    fig.add_annotation(
        text=f"<b>{total:.0f}</b><br><span style='font-size:11px;color:{COLORS['text_muted']}'>min total</span>",
        showarrow=False, font=dict(size=22, color=COLORS["text"]),
    )

    layout_cfg = LAYOUT.copy()
    layout_cfg["legend"] = dict(
        orientation="h", yanchor="bottom", y=-0.15,
        xanchor="center", x=0.5,
        font=dict(size=11, color=COLORS["text_muted"]),
    )
    fig.update_layout(
        layout_cfg, height=380,
        title_text="Subject Distribution",
        showlegend=True,
    )
    return fig


def build_heatmap(heatmap_data: Dict[str, List[float]]) -> go.Figure:
    """Build weekly productivity heatmap — Aurora gradient."""
    if not heatmap_data:
        return _empty_chart("Study more to see patterns")

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours = list(range(6, 23))
    z_data = []
    for day_lower in [d.lower() for d in days]:
        row = heatmap_data.get(day_lower, [0] * 24)
        z_data.append([row[h] for h in hours])

    fig = go.Figure(go.Heatmap(
        z=z_data,
        x=[f"{h:02d}:00" for h in hours],
        y=days,
        colorscale=[
            [0, "rgba(9, 9, 11, 0.9)"],
            [0.2, "rgba(109, 40, 217, 0.15)"],
            [0.4, "rgba(139, 92, 246, 0.35)"],
            [0.6, "rgba(6, 182, 212, 0.5)"],
            [0.8, "rgba(16, 185, 129, 0.65)"],
            [1, "#34D399"],
        ],
        hovertemplate="<b>%{y}</b> at %{x}<br>Focus: %{z:.0f}%<extra></extra>",
        showscale=True,
        colorbar=dict(
            title=dict(text="Focus %", side="right", font=dict(color=COLORS["text_muted"])),
            tickfont=dict(color=COLORS["text_muted"]),
        ),
        xgap=3, ygap=3,
    ))

    fig.update_layout(
        LAYOUT, height=380,
        title_text="Productivity Heatmap",
        xaxis_title="Hour of Day",
    )
    return fig


def build_hourly_pattern(hourly_data: Dict[int, Dict]) -> go.Figure:
    """Build hourly focus pattern with colored bars."""
    hours = list(range(6, 23))
    focus_vals = [hourly_data.get(h, {}).get("avg_focus", 0) for h in hours]

    colors = []
    for f in focus_vals:
        if f >= 70:
            colors.append(COLORS["emerald"])
        elif f >= 50:
            colors.append(COLORS["violet"])
        elif f >= 30:
            colors.append(COLORS["amber"])
        elif f > 0:
            colors.append(COLORS["rose"])
        else:
            colors.append("rgba(139, 92, 246, 0.1)")

    fig = go.Figure(go.Bar(
        x=[f"{h}:00" for h in hours],
        y=focus_vals,
        marker=dict(
            color=colors,
            cornerradius=4,
            line=dict(width=0),
        ),
        hovertemplate="<b>%{x}</b><br>Avg Focus: %{y:.0f}%<extra></extra>",
    ))

    layout_cfg = LAYOUT.copy()
    yaxis_cfg = layout_cfg.pop("yaxis", {}).copy()
    yaxis_cfg.update(title="Avg Focus %", range=[0, 100])
    
    xaxis_cfg = layout_cfg.pop("xaxis", {}).copy()
    
    fig.update_layout(
        layout_cfg, height=320,
        title_text="Hourly Focus Pattern",
        yaxis=yaxis_cfg,
        xaxis=xaxis_cfg,
    )
    return fig


def build_weekly_comparison(comparison_data: Dict[str, Any]) -> go.Figure:
    """Build comparison chart between this week and last week."""
    this_w = comparison_data["this_week"]
    last_w = comparison_data["last_week"]
    
    categories = ["Hours Studied", "Sessions", "Avg Focus %"]
    this_vals = [this_w["hours"], this_w["sessions"], this_w["avg_focus"]]
    last_vals = [last_w["hours"], last_w["sessions"], last_w["avg_focus"]]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Last Week",
        x=categories, y=last_vals,
        marker_color="rgba(255, 255, 255, 0.1)",
        marker_line=dict(color=COLORS["text_dim"], width=1),
        offsetgroup=0,
    ))
    fig.add_trace(go.Bar(
        name="This Week",
        x=categories, y=this_vals,
        marker_color=COLORS["violet"],
        marker_line=dict(color=COLORS["violet_light"], width=1),
        offsetgroup=1,
    ))
    
    fig.update_layout(
        LAYOUT, height=320,
        title_text="Weekly Growth Comparison",
        barmode="group",
        bargap=0.3,
        bargroupgap=0.1
    )
    return fig


def build_focus_stability(stability_data: List[Dict]) -> go.Figure:
    """Build focus stability chart — focus avg with stability ribbons."""
    if not stability_data:
        return _empty_chart("No stability data yet")
        
    dates = [d["date"] for d in stability_data]
    focus = [d["avg_focus"] for d in stability_data]
    stability = [d["stability"] for d in stability_data]
    
    fig = go.Figure()
    
    # Stability Ribbon (Confidence Interval-like)
    upper = [f + s for f, s in zip(focus, stability)]
    lower = [f - s for f, s in zip(focus, stability)]
    
    fig.add_trace(go.Scatter(
        x=dates + dates[::-1],
        y=upper + lower[::-1],
        fill="toself",
        fillcolor="rgba(139, 92, 246, 0.08)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip",
        showlegend=False,
        name="Focus Variance"
    ))
    
    fig.add_trace(go.Scatter(
        x=dates, y=focus,
        mode="lines+markers",
        line=dict(color=COLORS["cyan"], width=3, shape="spline"),
        marker=dict(size=8, color=COLORS["cyan"], line=dict(color=COLORS["text"], width=1)),
        name="Avg Focus"
    ))
    
    layout_cfg = LAYOUT.copy()
    yaxis_cfg = layout_cfg.pop("yaxis", {}).copy()
    yaxis_cfg.update(range=[0, 105], title="Focus Score")
    
    fig.update_layout(
        layout_cfg, height=320,
        title_text="Focus Stability & Consistency",
        yaxis=yaxis_cfg
    )
    return fig


def build_ear_timeline(frames: List[Dict]) -> go.Figure:
    """Build EAR timeline with threshold zones."""
    if not frames:
        return _empty_chart("No data")

    ears = [f.get("ear", 0.3) for f in frames]

    fig = go.Figure()

    # Drowsy zone
    fig.add_hrect(y0=0, y1=0.21,
                  fillcolor="rgba(244, 63, 94, 0.04)", line_width=0)

    fig.add_trace(go.Scatter(
        y=ears, mode="lines",
        line=dict(color=COLORS["violet"], width=2, shape="spline", smoothing=1.2),
        fill="tozeroy",
        fillcolor="rgba(139, 92, 246, 0.04)",
        name="EAR",
    ))

    fig.add_hline(y=0.21, line_dash="dash", line_color=COLORS["rose"],
                  annotation_text="Drowsy", annotation_position="right",
                  annotation_font_color=COLORS["rose"])
    fig.add_hline(y=0.25, line_dash="dot", line_color=COLORS["amber"],
                  annotation_text="Alert", annotation_position="right",
                  annotation_font_color=COLORS["amber"])

    fig.update_layout(LAYOUT, height=280, title_text="Eye Aspect Ratio")
    return fig


def _empty_chart(message: str) -> go.Figure:
    """Return elegant empty chart."""
    fig = go.Figure()
    fig.add_annotation(
        text=f"{message}",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color=COLORS["text_muted"]),
    )
    fig.update_layout(LAYOUT, height=280)
    return fig
