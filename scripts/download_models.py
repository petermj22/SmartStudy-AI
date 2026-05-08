"""
SmartStudy — Download Pre-trained Models
Downloads placeholder model files for first-run experience.
In production, this would pull from a model registry.
"""

import os
import json
from pathlib import Path


MODELS_DIR = Path("ml_training/trained_models")


def create_model_metadata():
    """Create metadata files for model versioning."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    metadata = {
        "ensemble": {
            "version": "v1.0",
            "status": "not_trained",
            "models": ["random_forest", "xgboost", "lightgbm"],
            "accuracy": None,
            "description": "Train with: python ml_training/train_ensemble.py",
        },
        "lstm": {
            "version": "v1.0",
            "status": "not_trained",
            "architecture": "BiLSTM(128) → BiLSTM(64) → Dense(1)",
            "accuracy": None,
            "description": "Train with: python ml_training/train_lstm.py",
        },
    }

    metadata_path = MODELS_DIR / "model_registry.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Model registry created at {metadata_path}")

    # Create .gitkeep for empty directories
    datasets_dir = Path("ml_training/datasets")
    datasets_dir.mkdir(parents=True, exist_ok=True)
    (datasets_dir / ".gitkeep").touch()
    print(f"✅ Datasets directory ready at {datasets_dir}")


if __name__ == "__main__":
    print("🤖 SmartStudy — Model Setup")
    print("=" * 40)
    create_model_metadata()
    print()
    print("ℹ️  No pre-trained models available yet.")
    print("   The app uses rule-based fallback by default.")
    print("   Collect data via study sessions, then train:")
    print("     python ml_training/train_ensemble.py")
    print("     python ml_training/train_lstm.py")
