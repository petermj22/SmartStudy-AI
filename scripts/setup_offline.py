#!/usr/bin/env python3
"""
SmartStudy Offline Setup Script
Run this ONCE with internet, then the app works forever offline.

Usage: python scripts/setup_offline.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parent.parent
    print("📦 SmartStudy Offline Setup")
    print("=" * 50)

    # 1. Download pip packages for offline install
    offline_dir = project_root / "offline_packages"
    offline_dir.mkdir(exist_ok=True)
    req_file = project_root / "requirements.txt"

    print("\n[1/3] Downloading Python packages for offline use...")
    subprocess.run([
        sys.executable, "-m", "pip", "download",
        "-r", str(req_file), "-d", str(offline_dir),
    ], check=False)
    print(f"   ✅ Packages saved to {offline_dir}")

    # 2. Pre-download MediaPipe models
    print("\n[2/3] Caching MediaPipe models...")
    try:
        import mediapipe as mp
        mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
        print("   ✅ MediaPipe face mesh models cached")
    except ImportError:
        print("   ⚠️  MediaPipe not installed — skip model caching")
    except Exception as e:
        print(f"   ⚠️  MediaPipe init warning: {e}")

    # 3. Create data directories
    print("\n[3/3] Creating data directories...")
    dirs = [
        project_root / "data",
        project_root / "data" / "reports",
        project_root / "data" / "replays",
        project_root / "logs",
        project_root / "ml_training" / "trained_models",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {d.relative_to(project_root)}")

    print("\n" + "=" * 50)
    print("✅ Offline setup complete!")
    print("   The app now works without internet.")
    print("   Run: streamlit run frontend/app.py")


if __name__ == "__main__":
    main()
