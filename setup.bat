@echo off
REM SmartStudy Windows Setup Script
echo.
echo  =======================================
echo   SmartStudy v2.0 - Windows Setup
echo  =======================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found!
    echo  Install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo  [1/4] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo  [2/4] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo  [3/4] Creating directories...
mkdir data 2>nul
mkdir logs 2>nul
mkdir data\reports 2>nul
mkdir data\replays 2>nul
mkdir ml_training\trained_models 2>nul
mkdir ml_training\datasets\labeled_sessions 2>nul
mkdir frontend\assets 2>nul

echo  [4/4] Initializing database...
python -c "import sys; sys.path.insert(0,'.'); from backend.database.manager import DatabaseManager; DatabaseManager()"

echo.
echo  =======================================
echo   Setup Complete!
echo   Run: python run.py
echo  =======================================
pause
