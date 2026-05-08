#!/bin/bash
# SmartStudy macOS/Linux Setup

set -e
echo ""
echo "======================================="
echo "  SmartStudy v2.0 - Setup"
echo "======================================="
echo ""

# Python check
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Install Python 3.10+"
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Python $PY_VERSION"

# Virtual environment
echo "[1/5] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Dependencies
echo "[2/5] Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Directories
echo "[3/5] Creating directories..."
mkdir -p data/reports data/replays logs \
         ml_training/trained_models \
         ml_training/datasets/labeled_sessions \
         frontend/assets

# Database
echo "[4/5] Initializing database..."
python3 -c "import sys; sys.path.insert(0,'.'); from backend.database.manager import DatabaseManager; DatabaseManager()"

# MediaPipe models
echo "[5/5] Pre-downloading MediaPipe models..."
python3 -c "
try:
    import mediapipe as mp
    mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
    print('MediaPipe models cached')
except Exception:
    print('MediaPipe models will download on first run')
" 2>/dev/null

echo ""
echo "======================================="
echo "  Setup Complete!"
echo "  Run: python run.py"
echo "======================================="
