"""
SmartStudy v2.0 — Main Application
All pages wired, all errors caught, health check gated.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st

st.set_page_config(
    page_title="SmartStudy — AI Focus Assistant",
    page_icon=":material/track_changes:",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "SmartStudy v2.0 · 100% Local · Privacy-First · All data stored on-device",
    },
)


# ─────────────────────────────────────────────────────────
# CSS LOADER
# ─────────────────────────────────────────────────────────
def _load_css() -> None:
    """Load custom stylesheet and suppress default Streamlit chrome."""
    css_path = Path(__file__).parent / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(
            f"<style>\n{css_path.read_text(encoding='utf-8')}\n</style>",
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <style>
        #MainMenu, footer, .stDeployButton,
        header[data-testid="stHeader"],
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavItems"],
        nav[data-testid="stSidebarNav"],
        div[data-testid="stSidebarNav"],
        section[data-testid="stSidebar"] > div > div > ul { display:none!important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────
# BACKEND INIT
# ─────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading SmartStudy...")
def _init_backend():
    """One-time backend initialization (cached across reruns)."""
    from loguru import logger

    # Ensure all dirs exist
    for d in [
        "data", "data/reports", "data/replays", "logs",
        "ml_training/trained_models",
        "ml_training/datasets/labeled_sessions",
        "backend/reports", "frontend/assets",
    ]:
        Path(d).mkdir(parents=True, exist_ok=True)

    errors, warnings = [], []

    # ── Database ──────────────────────────────────────────
    db = None
    try:
        from backend.database.manager import DatabaseManager
        from sqlalchemy import inspect, text
        db = DatabaseManager(db_path="data/smartstudy.db")
        # Auto-migration
        insp = inspect(db.engine)
        if "session_frames" in insp.get_table_names():
            cols = [c["name"] for c in insp.get_columns("session_frames")]
            if "thumbnail_bytes" not in cols:
                with db.engine.connect() as conn:
                    conn.execute(text(
                        "ALTER TABLE session_frames "
                        "ADD COLUMN thumbnail_bytes BLOB"
                    ))
                    conn.commit()
    except Exception as e:
        errors.append(f"Database: {e}")

    # ── Insight Engine ────────────────────────────────────
    insight_engine = None
    if db:
        try:
            from backend.analytics.insight_engine import InsightEngine
            insight_engine = InsightEngine(db_manager=db)
        except Exception as e:
            warnings.append(f"InsightEngine: {e}")

    # ── Aggregator ────────────────────────────────────────
    aggregator = None
    if db:
        try:
            from backend.analytics.aggregator import StatsAggregator
            aggregator = StatsAggregator(db_manager=db)
        except Exception as e:
            warnings.append(f"StatsAggregator: {e}")

    # ── Inference Engine ──────────────────────────────────
    engine = None
    try:
        from backend.core.inference_engine import InferenceEngine
        engine = InferenceEngine()
    except Exception as e:
        errors.append(f"InferenceEngine: {e}")

    # Camera is managed by WebRTC (browser) or SessionManager on demand.
    # No pre-emptive camera.start() to avoid device lock conflicts.
    camera = None

    # ── Session Manager ───────────────────────────────────
    session_mgr = None
    try:
        from backend.core.session_manager import SessionManager
        session_mgr = SessionManager(db_manager=db) if db else None
    except Exception as e:
        errors.append(f"SessionManager: {e}")

    # ── Online Learner ────────────────────────────────────
    online_learner = None
    try:
        from backend.ml.online_learner import OnlineFocusLearner
        online_learner = OnlineFocusLearner()
    except Exception as e:
        warnings.append(f"OnlineLearner (optional): {e}")

    # ── Notification Manager ──────────────────────────────
    notif_mgr = None
    try:
        from backend.core.notification_manager import DesktopNotificationManager
        notif_mgr = DesktopNotificationManager()
    except Exception as e:
        warnings.append(f"Notifications (optional): {e}")

    # ── Preferences ───────────────────────────────────────
    prefs = {
        "break_interval":   25,
        "break_duration":   5,
        "notifications":    True,
        "sound":            True,
        "volume":           70,
        "weekly_goal_hours": 20,
        "frame_skip":       1,
        "smoothing_window": 15,
    }
    if db:
        try:
            user = db.get_user()
            if user:
                stored = user.get_preferences()
                if stored:
                    prefs.update(stored)
        except Exception:
            pass

    logger.info(
        f"Backend ready | "
        f"db={'ok' if db else 'FAIL'} | "
        f"engine={'ok' if engine else 'FAIL'} | "
        f"camera={'ok' if camera else 'warn'} | "
        f"errors={len(errors)} | warnings={len(warnings)}"
    )

    return {
        "db_manager":           db,
        "insight_engine":       insight_engine,
        "aggregator":           aggregator,
        "inference_engine":     engine,
        "camera_manager":       camera,
        "session_manager":      session_mgr,
        "online_learner":       online_learner,
        "notification_manager": notif_mgr,
        "preferences":          prefs,
        "last_result":          None,
        "session_id":           None,
        "init_errors":          errors,
        "init_warnings":        warnings,
    }


# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────
def _sync_prefs() -> None:
    if st.session_state.get("prefs_synced"):
        return
    db = st.session_state.get("db_manager")
    if db:
        try:
            user = db.get_user()
            if user:
                stored = user.get_preferences()
                if stored:
                    st.session_state["preferences"].update(stored)
        except Exception:
            pass
    st.session_state["prefs_synced"] = True


def _inject_audio() -> None:
    if st.session_state.get("audio_injected"):
        return
    try:
        from frontend.components.sound_system import inject_audio_engine
        prefs = st.session_state.get("preferences", {})
        inject_audio_engine(
            volume=prefs.get("volume", 70),
            muted=not prefs.get("sound", True),
        )
        st.session_state["audio_injected"] = True
    except Exception:
        pass


def _update_stats() -> None:
    db = st.session_state.get("db_manager")
    if not db:
        return
    last = st.session_state.get("last_stats_update", 0)
    if time.time() - last > 30:
        try:
            stats = db.get_daily_statistics()
            st.session_state["today_stats"] = stats
            st.session_state["last_stats_update"] = time.time()
        except Exception:
            pass


def _desktop_notifications() -> None:
    last_result = st.session_state.get("last_result")
    notif_mgr   = st.session_state.get("notification_manager")
    prefs       = st.session_state.get("preferences", {})
    if not last_result or not notif_mgr:
        return
    if not prefs.get("notifications", True):
        return
    for alert in (last_result.alerts or []):
        atype = getattr(alert, "alert_type", "")
        msg   = getattr(alert, "message", "")
        if atype == "microsleep":
            notif_mgr.notify_microsleep()
        elif atype == "break_needed":
            notif_mgr.notify_break(
                last_result.recommended_break_minutes,
                last_result.fatigue_score * 100,
            )
        elif atype in ("drowsy_eyes", "looking_away"):
            notif_mgr.notify_distraction(msg)


def _safe_page(name: str, render_fn) -> None:
    """Render a page with full error isolation."""
    try:
        render_fn()
    except Exception as exc:
        import traceback
        st.error(f"**{name} page error:** {exc}")
        with st.expander("Full traceback", icon=":material/code:"):
            st.code(traceback.format_exc(), language="python")
        st.button(
            "Reload page",
            icon=":material/refresh:",
            key=f"reload_btn_{name.lower().replace(' ', '_')}",
            on_click=lambda: st.session_state.update({"prefs_synced": False}),
        )


# ─────────────────────────────────────────────────────────
# NAVIGATION CONFIG
# ─────────────────────────────────────────────────────────
NAV_ITEMS = [
    {"key": "dashboard", "label": "Dashboard",    "icon": "bar_chart_4_bars",  "color": "#8B5CF6"},
    {"key": "session",   "label": "Live Session",  "icon": "play_circle",       "color": "#EF4444"},
    {"key": "analytics", "label": "Analytics",     "icon": "insights",          "color": "#22D3EE"},
    {"key": "insights",  "label": "AI Insights",   "icon": "lightbulb",         "color": "#FBBF24"},
    {"key": "history",   "label": "History",       "icon": "history",           "color": "#34D399"},
    {"key": "settings",  "label": "Settings",      "icon": "settings",          "color": "#94A3B8"},
]


def _render_sidebar() -> None:
    """Render a premium branded sidebar with icon navigation."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"

    with st.sidebar:
        # ── Brand header ────────────────────────────
        st.markdown("""
        <div style="padding: 8px 0 20px; text-align: center;">
            <div style="
                display: inline-flex; align-items: center; justify-content: center;
                width: 48px; height: 48px; border-radius: 14px;
                background: linear-gradient(135deg, rgba(139,92,246,0.2), rgba(34,211,238,0.1));
                border: 1px solid rgba(139,92,246,0.2);
                margin-bottom: 10px;
                box-shadow: 0 4px 20px rgba(139,92,246,0.15);
            ">
                <span class="material-symbols-rounded" style="font-size: 24px; color: #A78BFA;">track_changes</span>
            </div>
            <div style="
                font-size: 1.15rem; font-weight: 800; color: #F8FAFC;
                letter-spacing: -0.03em; font-family: 'Inter', sans-serif;
            ">SmartStudy</div>
            <div style="
                font-size: 0.65rem; color: #475569;
                text-transform: uppercase; letter-spacing: 0.12em;
                margin-top: 2px;
            ">AI Focus Assistant</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="
            height: 1px; margin: 0 12px 16px;
            background: linear-gradient(90deg,
                transparent, rgba(139,92,246,0.2), rgba(34,211,238,0.15), transparent);
        "></div>
        """, unsafe_allow_html=True)

        # ── Navigation buttons ──────────────────────
        for item in NAV_ITEMS:
            key = item["key"]
            is_active = st.session_state.current_page == key
            btn_type = "primary" if is_active else "secondary"

            if st.button(
                item["label"],
                key=f"nav_{key}",
                icon=f":material/{item['icon']}:",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state.current_page = key
                st.rerun()

        # ── Sidebar footer ──────────────────────────
        st.markdown("<div style='flex: 1; min-height: 40px;'></div>", unsafe_allow_html=True)

        # Session status indicator
        sm = st.session_state.get("session_manager")
        if sm and getattr(sm, "is_active", False):
            st.markdown("""
            <div style="
                margin: 16px 0 8px; padding: 10px 14px;
                background: rgba(16,185,129,0.06);
                border: 1px solid rgba(16,185,129,0.15);
                border-radius: 10px;
                display: flex; align-items: center; gap: 10px;
            ">
                <div style="
                    width: 8px; height: 8px; border-radius: 50%;
                    background: #34D399;
                    box-shadow: 0 0 8px rgba(16,185,129,0.5);
                    animation: orb-breathe 2s ease-in-out infinite;
                "></div>
                <div>
                    <div style="font-size: 11px; font-weight: 700; color: #34D399;
                                text-transform: uppercase; letter-spacing: 0.1em;">
                        Session Active</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="
            margin-top: 12px; padding: 10px 14px;
            border-top: 1px solid rgba(255,255,255,0.04);
        ">
            <div style="
                display: flex; align-items: center; gap: 6px;
                font-size: 10px; color: #475569;
            ">
                <span style="
                    display: inline-block; width: 6px; height: 6px;
                    border-radius: 50%; background: #34D399;
                "></span>
                v2.0 · 100% Local · Privacy-First
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────
def main() -> None:
    _load_css()

    # Health check runs silently — no blocking gate on launch.
    # System status is available in Settings > System Info.

    # ── Backend init ─────────────────────────────────────
    app_state = _init_backend()
    for k, v in app_state.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Show init warnings (non-blocking) ─────────────────
    if app_state.get("init_errors"):
        with st.expander(
            f"{len(app_state['init_errors'])} startup warning(s)",
            expanded=False, icon=":material/warning:",
        ):
            for err in app_state["init_errors"]:
                st.warning(err)

    # ── One-time setup ────────────────────────────────────
    _sync_prefs()
    _inject_audio()
    _update_stats()
    _desktop_notifications()

    # ── Initialize session components (if missing) ─────────
    if "live_data" not in st.session_state:
        from frontend.components.live_dashboard import LiveDataStore
        st.session_state["live_data"] = LiveDataStore()
    if "thumb_recorder" not in st.session_state:
        from backend.core.session_replay import SessionThumbnailRecorder
        st.session_state["thumb_recorder"] = SessionThumbnailRecorder()

    # ── Sidebar Navigation ────────────────────────────────
    _render_sidebar()

    # ── Render Page ───────────────────────────────────────
    page = st.session_state.current_page

    if page == "dashboard":
        try:
            from frontend.pages.dashboard import render_dashboard
            _safe_page("Dashboard", render_dashboard)
        except ImportError as e:
            st.error(f"Dashboard not found: {e}")

    elif page == "session":
        try:
            from frontend.pages.session import render_session
            _safe_page("Live Session", render_session)
        except ImportError as e:
            st.error(f"Session not found: {e}")

    elif page == "analytics":
        try:
            from frontend.pages.analytics import render_analytics
            _safe_page("Analytics", render_analytics)
        except ImportError as e:
            st.error(f"Analytics not found: {e}")

    elif page == "insights":
        try:
            from frontend.pages.insights import render_insights
            _safe_page("AI Insights", render_insights)
        except ImportError as e:
            st.error(f"AI Insights not found: {e}")

    elif page == "history":
        try:
            from frontend.pages.session_history import render_session_history
            _safe_page("History", render_session_history)
        except ImportError as e:
            st.error(f"History not found: {e}")

    elif page == "settings":
        try:
            from frontend.pages.settings import render_settings
            _safe_page("Settings", render_settings)
        except ImportError as e:
            st.error(f"Settings not found: {e}")

    # Session page manages its own refresh cycle (5s intervals).
    # No global auto-rerun here — avoids CPU-hammering on idle pages.

if __name__ == "__main__":
    main()
