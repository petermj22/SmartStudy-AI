#!/usr/bin/env bash
# ============================================================
# SmartStudy — One-Command Setup (Linux/macOS)
# ============================================================
set -euo pipefail

echo "🎯 SmartStudy Setup"
echo "===================="

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install dependencies
echo "📥 Installing production dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install dev dependencies
echo "📥 Installing development dependencies..."
pip install -r requirements-dev.txt

# Create directories
echo "📁 Creating data directories..."
mkdir -p data logs ml_training/trained_models ml_training/datasets

# Initialize database
echo "💾 Initializing database..."
python -c "from backend.database.manager import DatabaseManager; DatabaseManager()"

echo ""
echo "✅ Setup complete!"
echo "   Run 'make run' or 'streamlit run frontend/app.py' to start."
