"""
Module: model_loader.py
Purpose: Load/save ML models with versioning and validation.
Author: SmartStudy Team
Version: 1.0.0
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import yaml
from loguru import logger


class ModelLoader:
    """
    Model loading and saving utility.
    Handles versioned model files with metadata tracking.
    """

    def __init__(self, models_dir: str = "ml_training/trained_models") -> None:
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._config = self._load_config()
        logger.debug(f"ModelLoader initialized: {self.models_dir}")

    def _load_config(self) -> Dict[str, Any]:
        config_path = Path("config/model_config.yaml")
        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f) or {}
        return {}

    def save_model(
        self, model: Any, name: str, version: str = "v1.0",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Save a model with versioning."""
        filename = f"{name}_{version}.pkl"
        filepath = self.models_dir / filename
        joblib.dump(model, filepath)

        if metadata:
            meta_path = self.models_dir / f"{name}_{version}_meta.pkl"
            joblib.dump(metadata, meta_path)

        logger.info(f"Model saved: {filepath}")
        return filepath

    def load_model(self, name: str, version: str = "v1.0") -> Optional[Any]:
        """Load a model by name and version."""
        filename = f"{name}_{version}.pkl"
        filepath = self.models_dir / filename

        if not filepath.exists():
            logger.warning(f"Model not found: {filepath}")
            return None

        try:
            model = joblib.load(filepath)
            logger.info(f"Model loaded: {filepath}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model {filepath}: {e}")
            return None

    def load_metadata(self, name: str, version: str = "v1.0") -> Dict[str, Any]:
        """Load model metadata."""
        meta_path = self.models_dir / f"{name}_{version}_meta.pkl"
        if meta_path.exists():
            try:
                return joblib.load(meta_path)
            except Exception:
                pass
        return {}

    def model_exists(self, name: str, version: str = "v1.0") -> bool:
        """Check if a model file exists."""
        filepath = self.models_dir / f"{name}_{version}.pkl"
        return filepath.exists()

    def list_models(self) -> list:
        """List all available models."""
        models = []
        for f in self.models_dir.glob("*.pkl"):
            if not f.stem.endswith("_meta"):
                models.append(f.stem)
        return sorted(models)

    def get_feature_columns(self) -> list:
        """Get configured feature columns for ensemble classifier."""
        ensemble_config = self._config.get("ensemble_classifier", {})
        return ensemble_config.get("feature_columns", [])

    def get_lstm_features(self) -> list:
        """Get configured temporal features for LSTM."""
        lstm_config = self._config.get("lstm_predictor", {})
        return lstm_config.get("temporal_features", [])

    def get_ensemble_weights(self) -> Dict[str, float]:
        """Get configured ensemble model weights."""
        ensemble_config = self._config.get("ensemble_classifier", {})
        return ensemble_config.get("weights", {
            "random_forest": 0.33, "xgboost": 0.34, "lightgbm": 0.33,
        })
