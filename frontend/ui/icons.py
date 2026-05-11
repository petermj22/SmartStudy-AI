"""
SmartStudy Lucide-style SVG Icon Library
Professional stroke-based icons matching Linear/Vercel aesthetic.
All icons are inline SVG — no external dependencies.
"""

from __future__ import annotations

from typing import Optional


def _svg(
    path: str,
    size: int = 24,
    color: str = "currentColor",
    stroke_width: float = 2.0,
    fill: str = "none",
    extra_attrs: str = "",
    view_box: str = "0 0 24 24",
) -> str:
    """Base SVG wrapper."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{size}" height="{size}" viewBox="{view_box}" '
        f'fill="{fill}" stroke="{color}" '
        f'stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'{extra_attrs}>'
        f'{path}'
        f'</svg>'
    )


# ══════════════════════════════════════════════════════════
# ICON DEFINITIONS — Lucide-compatible SVG paths
# ══════════════════════════════════════════════════════════

def icon_brain(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/>'
        '<path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/>'
        '<path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/>'
        '<path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/>'
        '<path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/>'
        '<path d="M3.477 10.896a4 4 0 0 1 .585-.396"/>'
        '<path d="M19.938 10.5a4 4 0 0 1 .585.396"/>'
        '<path d="M6 18a4 4 0 0 1-1.967-.516"/>'
        '<path d="M19.967 17.484A4 4 0 0 1 18 18"/>',
        size, color, stroke_width,
    )


def icon_eye(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>'
        '<circle cx="12" cy="12" r="3"/>',
        size, color, stroke_width,
    )


def icon_eye_off(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/>'
        '<path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/>'
        '<path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/>'
        '<line x1="2" x2="22" y1="2" y2="22"/>',
        size, color, stroke_width,
    )


def icon_clock(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<circle cx="12" cy="12" r="10"/>'
        '<polyline points="12 6 12 12 16 14"/>',
        size, color, stroke_width,
    )


def icon_coffee(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<path d="M17 8h1a4 4 0 1 1 0 8h-1"/>'
        '<path d="M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z"/>'
        '<line x1="6" x2="6" y1="2" y2="4"/>'
        '<line x1="10" x2="10" y1="2" y2="4"/>'
        '<line x1="14" x2="14" y1="2" y2="4"/>',
        size, color, stroke_width,
    )


def icon_alert_triangle(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>'
        '<path d="M12 9v4"/>'
        '<path d="M12 17h.01"/>',
        size, color, stroke_width,
    )


def icon_zap(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
        size, color, stroke_width,
    )


def icon_target(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<circle cx="12" cy="12" r="10"/>'
        '<circle cx="12" cy="12" r="6"/>'
        '<circle cx="12" cy="12" r="2"/>',
        size, color, stroke_width,
    )


def icon_trending_up(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>'
        '<polyline points="16 7 22 7 22 13"/>',
        size, color, stroke_width,
    )


def icon_trending_down(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/>'
        '<polyline points="16 17 22 17 22 11"/>',
        size, color, stroke_width,
    )


def icon_activity(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
        size, color, stroke_width,
    )


def icon_bar_chart(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<line x1="18" x2="18" y1="20" y2="10"/>'
        '<line x1="12" x2="12" y1="20" y2="4"/>'
        '<line x1="6" x2="6" y1="20" y2="14"/>',
        size, color, stroke_width,
    )


def icon_camera(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/>'
        '<circle cx="12" cy="13" r="3"/>',
        size, color, stroke_width,
    )


def icon_settings(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>'
        '<circle cx="12" cy="12" r="3"/>',
        size, color, stroke_width,
    )


def icon_shield(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
        size, color, stroke_width,
    )


def icon_user(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>'
        '<circle cx="12" cy="7" r="4"/>',
        size, color, stroke_width,
    )


def icon_award(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<circle cx="12" cy="8" r="6"/>'
        '<path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>',
        size, color, stroke_width,
    )


def icon_sun(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<circle cx="12" cy="12" r="4"/>'
        '<path d="M12 2v2"/><path d="M12 20v2"/>'
        '<path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/>'
        '<path d="M2 12h2"/><path d="M20 12h2"/>'
        '<path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
        size, color, stroke_width,
    )


def icon_moon(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
        size, color, stroke_width,
    )


def icon_check_circle(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
        '<path d="m9 11 3 3L22 4"/>',
        size, color, stroke_width,
    )


def icon_x_circle(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="m15 9-6 6"/>'
        '<path d="m9 9 6 6"/>',
        size, color, stroke_width,
    )


def icon_flame(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
        size, color, stroke_width,
    )


def icon_book_open(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>'
        '<path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
        size, color, stroke_width,
    )


def icon_lightbulb(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/>'
        '<path d="M9 18h6"/>'
        '<path d="M10 22h4"/>',
        size, color, stroke_width,
    )


def icon_wifi_off(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<line x1="2" x2="22" y1="2" y2="22"/>'
        '<path d="M8.5 16.5a5 5 0 0 1 7 0"/>'
        '<path d="M2 8.82a15 15 0 0 1 4.17-2.65"/>'
        '<path d="M10.66 5c4.01-.36 8.14.9 11.34 3.76"/>'
        '<path d="M16.85 11.25a10 10 0 0 1 2.22 1.68"/>'
        '<path d="M5 13a10 10 0 0 1 5.24-2.76"/>'
        '<line x1="12" x2="12.01" y1="20" y2="20"/>',
        size, color, stroke_width,
    )


def icon_play(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<polygon points="5 3 19 12 5 21 5 3"/>',
        size, color, stroke_width,
    )


def icon_pause(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<rect x="6" y="4" width="4" height="16"/>'
        '<rect x="14" y="4" width="4" height="16"/>',
        size, color, stroke_width,
    )


def icon_volume(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>'
        '<path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>'
        '<path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>',
        size, color, stroke_width,
    )


def icon_volume_off(size=24, color="currentColor", stroke_width=2.0) -> str:
    return _svg(
        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>'
        '<line x1="22" x2="16" y1="9" y2="15"/>'
        '<line x1="16" x2="22" y1="9" y2="15"/>',
        size, color, stroke_width,
    )


# ══════════════════════════════════════════════════════════
# ICON REGISTRY & HELPERS
# ══════════════════════════════════════════════════════════

ICON_REGISTRY = {
    "brain": icon_brain,
    "eye": icon_eye,
    "eye-off": icon_eye_off,
    "clock": icon_clock,
    "coffee": icon_coffee,
    "alert-triangle": icon_alert_triangle,
    "zap": icon_zap,
    "target": icon_target,
    "trending-up": icon_trending_up,
    "trending-down": icon_trending_down,
    "activity": icon_activity,
    "bar-chart": icon_bar_chart,
    "camera": icon_camera,
    "settings": icon_settings,
    "shield": icon_shield,
    "user": icon_user,
    "award": icon_award,
    "sun": icon_sun,
    "moon": icon_moon,
    "check-circle": icon_check_circle,
    "x-circle": icon_x_circle,
    "flame": icon_flame,
    "book-open": icon_book_open,
    "lightbulb": icon_lightbulb,
    "wifi-off": icon_wifi_off,
    "play": icon_play,
    "pause": icon_pause,
    "volume": icon_volume,
    "volume-off": icon_volume_off,
}


def icon(
    name: str,
    size: int = 24,
    color: str = "currentColor",
    stroke_width: float = 2.0,
) -> str:
    """Get an icon SVG by name."""
    fn = ICON_REGISTRY.get(name)
    if fn:
        return fn(size=size, color=color, stroke_width=stroke_width)
    return f'<span title="unknown icon: {name}">[?]</span>'


def icon_with_label(
    icon_name: str,
    label: str,
    icon_size: int = 18,
    icon_color: str = "#8B5CF6",
    label_color: str = "#F8FAFC",
    font_size: str = "0.95rem",
    gap: str = "8px",
) -> str:
    """Render an icon + label inline."""
    ico = icon(icon_name, icon_size, icon_color)
    return (
        f'<span style="display:inline-flex;align-items:center;gap:{gap};">'
        f'{ico}'
        f'<span style="color:{label_color};font-size:{font_size};font-weight:600;">{label}</span>'
        f'</span>'
    )


def icon_stat(
    icon_name: str,
    value: str,
    label: str,
    icon_color: str = "#8B5CF6",
    value_color: str = "#F8FAFC",
    bg: str = "rgba(139,92,246,0.06)",
    border: str = "rgba(139,92,246,0.12)",
) -> str:
    """Render icon + value + label stat block (dark theme)."""
    ico = icon(icon_name, 20, icon_color)
    return f"""
    <div style="display:flex;align-items:center;gap:12px;
                padding:14px 16px;background:{bg};
                border:1px solid {border};border-radius:14px;">
        <div style="width:40px;height:40px;background:rgba(255,255,255,0.04);border-radius:10px;
                    display:flex;align-items:center;justify-content:center;flex-shrink:0;
                    border:1px solid rgba(255,255,255,0.06);">
            {ico}
        </div>
        <div>
            <div style="font-size:20px;font-weight:800;color:{value_color};
                        letter-spacing:-0.5px;line-height:1;
                        font-family:'JetBrains Mono',monospace;">{value}</div>
            <div style="font-size:11px;font-weight:600;color:#64748B;
                        text-transform:uppercase;letter-spacing:0.06em;margin-top:3px;">{label}</div>
        </div>
    </div>
    """
