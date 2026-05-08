@echo off
REM ============================================================
REM SmartStudy — One-Command Setup (Windows)
REM ============================================================

echo 🎯 SmartStudy Setup
echo ====================

REM Create virtual environment
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate
call venv\Scripts\activate

REM Install dependencies
echo 📥 Installing production dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Install dev dependencies
echo 📥 Installing development dependencies...
pip install -r requirements-dev.txt

REM Create directories
echo 📁 Creating data directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "ml_training\trained_models" mkdir ml_training\trained_models
if not exist "ml_training\datasets" mkdir ml_training\datasets

REM Initialize database
echo 💾 Initializing database...
python -c "from backend.database.manager import DatabaseManager; DatabaseManager()"

echo.
echo ✅ Setup complete!
echo    Run 'streamlit run frontend/app.py' to start.
