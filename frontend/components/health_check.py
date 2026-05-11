"""
SmartStudy Health Check Component
Shows system status on first load — verifies all dependencies are available.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Dict, Tuple

import streamlit as st


CHECKS = [
    ("cv2",              "OpenCV",            True,  "Camera processing"),
    ("sklearn",          "Scikit-learn",      True,  "ML classifiers"),
    ("xgboost",          "XGBoost",           True,  "Gradient boosting"),
    ("sqlalchemy",       "SQLAlchemy",        True,  "Database"),
    ("plotly",           "Plotly",            True,  "Charts"),
    ("mediapipe",        "MediaPipe",         False, "Face detection (mock if absent)"),
    ("streamlit_webrtc", "streamlit-webrtc",  False, "Live camera overlay"),
    ("river",            "River",             False, "Online learning"),
    ("plyer",            "Plyer",             False, "Desktop notifications"),
    ("reportlab",        "ReportLab",         False, "PDF export"),
    ("cryptography",     "Cryptography",      False, "Data encryption"),
]


def run_health_check() -> Tuple[bool, Dict]:
    """Run all health checks. Returns (all_critical_ok, results)."""
    results = {}
    all_critical_ok = True

    for module, name, is_critical, description in CHECKS:
        try:
            importlib.import_module(module)
            results[name] = {
                "status": "ok",
                "critical": is_critical,
                "description": description,
            }
        except ImportError:
            results[name] = {
                "status": "missing",
                "critical": is_critical,
                "description": description,
            }
            if is_critical:
                all_critical_ok = False

    # Ensure required directories exist
    required_dirs = ["data", "logs", "ml_training/trained_models"]
    for d in required_dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

    # Camera check
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            results["Camera"] = {
                "status": "ok",
                "critical": False,
                "description": "Webcam hardware",
            }
            cap.release()
        else:
            results["Camera"] = {
                "status": "warning",
                "critical": False,
                "description": "Webcam (no camera found — will use simulation)",
            }
    except Exception:
        results["Camera"] = {
            "status": "missing",
            "critical": False,
            "description": "Webcam",
        }

    return all_critical_ok, results


def render_health_check() -> bool:
    """
    Render health check panel.
    Returns True if app can proceed, False to block until user confirms.
    """
    if st.session_state.get("health_check_passed"):
        return True

    all_ok, results = run_health_check()

    # Count totals
    total = len(results)
    ok_count = sum(1 for v in results.values() if v["status"] == "ok")
    progress = ok_count / max(total, 1)

    st.markdown(
        f"""
        <div style="max-width:640px;margin:48px auto;padding:0 24px;">
            <div style="text-align:center;margin-bottom:36px;">
                <div style="
                    display:inline-flex;align-items:center;justify-content:center;
                    width:64px;height:64px;border-radius:18px;
                    background:linear-gradient(135deg,rgba(139,92,246,0.15),rgba(34,211,238,0.08));
                    border:1px solid rgba(139,92,246,0.2);
                    margin-bottom:16px;
                    box-shadow:0 8px 32px rgba(139,92,246,0.15);
                ">
                    <span class="material-symbols-rounded" style="font-size:28px;color:#A78BFA;">verified</span>
                </div>
                <h1 style="font-size:24px;font-weight:800;
                           letter-spacing:-0.03em;margin-bottom:6px;
                           background:linear-gradient(135deg,#A78BFA,#22D3EE);
                           -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                           background-clip:text;color:transparent;">
                    System Check
                </h1>
                <p style="color:#64748B;font-size:14px;">
                    Verifying components before launch &middot; {ok_count}/{total} ready
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Progress bar
    st.progress(progress)

    critical_missing = []
    optional_missing = []

    for name, info in results.items():
        status = info["status"]
        critical = info["critical"]
        desc = info["description"]

        if status == "ok":
            status_text = "Ready"
            status_color = "#34D399"
            row_bg = "rgba(16,185,129,0.06)"
            border = "rgba(16,185,129,0.1)"
        elif status == "warning":
            status_text = "Warning"
            status_color = "#FBBF24"
            row_bg = "rgba(251,191,36,0.06)"
            border = "rgba(251,191,36,0.1)"
        else:
            if critical:
                status_text = "Missing"
                status_color = "#FB7185"
                row_bg = "rgba(239,68,68,0.06)"
                border = "rgba(239,68,68,0.1)"
                critical_missing.append(name)
            else:
                status_text = "Skipped"
                status_color = "#64748B"
                row_bg = "rgba(100,116,139,0.04)"
                border = "rgba(100,116,139,0.06)"
                optional_missing.append(name)

        badge = (
            '<span style="background:rgba(239,68,68,0.12);color:#F87171;font-size:10px;'
            'padding:2px 8px;border-radius:10px;font-weight:700;">REQUIRED</span>'
            if critical
            else '<span style="background:rgba(148,163,184,0.1);color:#94A3B8;font-size:10px;'
            'padding:2px 8px;border-radius:10px;">OPTIONAL</span>'
        )

        st.markdown(
            f"""
            <div style="display:flex;align-items:center;justify-content:space-between;
                        padding:10px 16px;background:{row_bg};border-radius:10px;
                        margin-bottom:6px;border:1px solid {border};
                        transition:all 0.2s ease;">
                <div style="display:flex;align-items:center;gap:10px;">
                    {badge}
                    <span style="font-weight:600;font-size:13px;color:#E2E8F0;">{name}</span>
                    <span style="color:#475569;font-size:12px;"> &mdash; {desc}</span>
                </div>
                <span style="font-size:12px;font-weight:600;color:{status_color};">{status_text}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Fix instructions
    if critical_missing:
        st.error(
            f"Critical packages missing: {', '.join(critical_missing)}\n\n"
            f"**Fix:** `pip install -r requirements.txt`"
        )

    if optional_missing:
        st.info(
            f"Optional packages not installed: {', '.join(optional_missing)}\n\n"
            f"Some features will be disabled. Install with: "
            f"`pip install -r requirements.txt`"
        )

    st.markdown("")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "Launch SmartStudy" if all_ok else "Launch Anyway",
            type="primary",
            use_container_width=True,
            icon=":material/rocket_launch:" if all_ok else ":material/warning:",
        ):
            st.session_state["health_check_passed"] = True
            st.rerun()

    with col2:
        if st.button("Re-check", use_container_width=True, icon=":material/refresh:"):
            st.rerun()

    return False
