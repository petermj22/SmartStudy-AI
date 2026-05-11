"""
SmartStudy v2.0 — Universal Launcher
Works on Windows, macOS, Linux.
Usage:  python run.py
        python run.py --check-only
        python run.py --port 8502
        python run.py --demo
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


# ── ANSI colours (work on all modern terminals) ────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

OK   = f"{GREEN}[OK]{RESET}"
WARN = f"{YELLOW}[WARN]{RESET}"
FAIL = f"{RED}[FAIL]{RESET}"


def banner() -> None:
    """Prints the application banner."""
    # Use ASCII safely
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    # Safe printing that handles unicode encoding errors gracefully on Windows
    banner_text = f"""
    {BOLD}{'-'*52}
       [Target]  SmartStudy v2.0 | AI Focus Assistant
    {'-'*52}{RESET}
    """
    try:
        print(banner_text)
    except UnicodeEncodeError:
        print(banner_text.encode('ascii', 'ignore').decode('ascii'))


def check_python() -> bool:
    v = sys.version_info
    if v < (3, 10):
        print(f"{FAIL} Python 3.10+ required (found {v.major}.{v.minor})")
        return False
    print(f"{OK} Python {v.major}.{v.minor}.{v.micro}")
    return True


def create_directories() -> None:
    dirs = [
        "data", "data/reports", "data/replays",
        "logs",
        "ml_training/trained_models",
        "ml_training/datasets/labeled_sessions",
        "backend/reports",
        "frontend/assets",
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    print(f"{OK} Directories ready")


def check_env() -> None:
    env = ROOT / ".env"
    example = ROOT / ".env.example"
    if not env.exists() and example.exists():
        import shutil
        shutil.copy(example, env)
        print(f"{OK} .env created from .env.example")
    else:
        print(f"{OK} Environment config ready")


def check_dependencies() -> bool:
    critical = [
        ("streamlit",   "streamlit"),
        ("cv2",         "opencv-python"),
        ("mediapipe",   "mediapipe"),
        ("sqlalchemy",  "sqlalchemy"),
        ("numpy",       "numpy"),
        ("pandas",      "pandas"),
        ("plotly",      "plotly"),
        ("sklearn",     "scikit-learn"),
        ("loguru",      "loguru"),
    ]
    optional = [
        ("streamlit_webrtc", "streamlit-webrtc"),
        ("av",               "av"),
        ("river",            "river"),
        ("plyer",            "plyer"),
        ("reportlab",        "reportlab"),
        ("cryptography",     "cryptography"),
    ]

    missing_critical = []
    for module, pkg in critical:
        try:
            __import__(module)
        except ImportError:
            missing_critical.append(pkg)

    missing_optional = []
    for module, pkg in optional:
        try:
            __import__(module)
        except ImportError:
            missing_optional.append(pkg)

    if missing_critical:
        print(f"\n{FAIL} Missing critical packages:")
        for pkg in missing_critical:
            print(f"     pip install {pkg}")
        print(f"\n   Or run:  pip install -r requirements.txt\n")
        return False

    print(f"{OK} All critical packages installed")

    if missing_optional:
        print(f"{WARN} Optional packages missing (some features disabled):")
        for pkg in missing_optional:
            print(f"     pip install {pkg}")

    return True


def initialize_database() -> bool:
    try:
        from backend.database.manager import DatabaseManager
        from sqlalchemy import inspect, text

        db = DatabaseManager(db_path="data/smartstudy.db")

        # Auto-migration: add thumbnail_bytes if missing
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
                print(f"{OK} Database migrated (thumbnail_bytes added)")

        print(f"{OK} Database ready → data/smartstudy.db")
        return True
    except Exception as e:
        print(f"{WARN} Database init warning: {e}")
        return True  # Non-fatal


def check_models() -> None:
    models_dir = ROOT / "ml_training" / "trained_models"
    ensemble   = models_dir / "ensemble_classifier_v1.0"
    lstm       = models_dir / "lstm_fatigue_v1.0.tflite"

    if not ensemble.exists() and not lstm.exists():
        print(
            f"{WARN} No trained models found.\n"
            "   App will use rule-based fallback (lower accuracy).\n"
            "   Train models: make train-ensemble"
        )
    else:
        print(f"{OK} ML models found")


def run_demo_data() -> None:
    print("\n[+] Creating demo data...")
    result = subprocess.run(
        [sys.executable, "scripts/create_demo_data.py"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"{OK} Demo data created")
    else:
        print(f"{WARN} Demo data creation failed: {result.stderr[:200]}")


def launch(port: int = 8501) -> None:
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "frontend/app.py",
        f"--server.port={port}",
        "--server.headless=false",
        "--server.runOnSave=false",
        "--browser.gatherUsageStats=false",
        "--theme.base=dark",
        "--theme.primaryColor=#8B5CF6",
        "--theme.backgroundColor=#09090B",
        "--theme.secondaryBackgroundColor=#12121E",
        "--theme.textColor=#E2E8F0",
        "--theme.font=sans serif",
    ]
    msg = f"\n{BOLD}[LAUNCH] Launching -> http://localhost:{port}{RESET}"
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'ignore').decode('ascii'))
    print(f"   Press Ctrl+C to stop\n{'-'*52}\n")
    subprocess.run(cmd, cwd=str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="SmartStudy Launcher")
    parser.add_argument("--port",       type=int,  default=8501)
    parser.add_argument("--check-only", action="store_true",
                        help="Run checks only, don't launch")
    parser.add_argument("--demo",       action="store_true",
                        help="Create demo data before launching")
    args = parser.parse_args()

    banner()

    # Run all checks
    ok = True
    ok &= check_python()
    check_env()
    create_directories()
    ok &= check_dependencies()
    initialize_database()
    check_models()

    if not ok:
        print(f"\n{FAIL} Startup checks failed. Fix issues above and retry.\n")
        sys.exit(1)

    print(f"\n{GREEN}{BOLD}All checks passed!{RESET}")

    if args.check_only:
        print("   --check-only mode: not launching.\n")
        return

    if args.demo:
        run_demo_data()

    launch(port=args.port)


if __name__ == "__main__":
    main()
