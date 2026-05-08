"""
Script: train_ensemble.py
Purpose: Train the ensemble classifier (RF + XGBoost + LightGBM) on collected data.
Usage:   python ml_training/train_ensemble.py --data ml_training/datasets/

Author: SmartStudy Team
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.ml.model_loader import ModelLoader
from backend.data.data_validator import DataValidator


def load_training_data(data_dir: str) -> pd.DataFrame:
    """Load and merge all CSV training files."""
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    if not csv_files:
        logger.error(f"No CSV files found in {data_dir}")
        sys.exit(1)

    dfs = []
    for f in csv_files:
        try:
            df = pd.read_csv(f)
            dfs.append(df)
            logger.info(f"Loaded: {f} ({len(df)} rows)")
        except Exception as e:
            logger.warning(f"Skipped {f}: {e}")

    if not dfs:
        logger.error("No valid data loaded")
        sys.exit(1)

    combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total samples: {len(combined)}")
    return combined


def train_models(df: pd.DataFrame, version: str = "v1.0") -> None:
    """Train and save all three ensemble models."""
    loader = ModelLoader()
    feature_columns = loader.get_feature_columns()

    # Validate data
    validator = DataValidator()
    report = validator.validate_dataframe(df)
    for issue in report.issues:
        logger.warning(f"Data issue: {issue}")

    # Clean data
    df = validator.clean_dataframe(df)

    # Prepare features and labels
    available_cols = [c for c in feature_columns if c in df.columns]
    if not available_cols:
        logger.error("No matching feature columns found in data")
        sys.exit(1)

    X = df[available_cols].values.astype(np.float32)
    y = df["label"].values.astype(np.int32)

    logger.info(f"Features: {len(available_cols)} | Samples: {len(X)}")
    logger.info(f"Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    loader.save_model(scaler, "feature_scaler", version)

    # 1. Random Forest
    logger.info("Training Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=15, min_samples_split=5,
        min_samples_leaf=2, random_state=42, n_jobs=-1,
        class_weight="balanced",
    )
    rf.fit(X_scaled, y)
    rf_score = cross_val_score(rf, X_scaled, y, cv=5, scoring="f1_macro").mean()
    loader.save_model(rf, "random_forest", version, {"f1_macro": rf_score})
    logger.info(f"Random Forest F1: {rf_score:.4f}")

    # 2. XGBoost
    logger.info("Training XGBoost...")
    try:
        import xgboost as xgb
        xgb_model = xgb.XGBClassifier(
            n_estimators=200, max_depth=8, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, n_jobs=-1, eval_metric="mlogloss",
        )
        xgb_model.fit(X_scaled, y)
        xgb_score = cross_val_score(xgb_model, X_scaled, y, cv=5, scoring="f1_macro").mean()
        loader.save_model(xgb_model, "xgboost", version, {"f1_macro": xgb_score})
        logger.info(f"XGBoost F1: {xgb_score:.4f}")
    except ImportError:
        logger.warning("XGBoost not installed — skipping")

    # 3. LightGBM
    logger.info("Training LightGBM...")
    try:
        import lightgbm as lgb
        lgb_model = lgb.LGBMClassifier(
            n_estimators=200, max_depth=8, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, n_jobs=-1, verbose=-1,
            class_weight="balanced",
        )
        lgb_model.fit(X_scaled, y)
        lgb_score = cross_val_score(lgb_model, X_scaled, y, cv=5, scoring="f1_macro").mean()
        loader.save_model(lgb_model, "lightgbm", version, {"f1_macro": lgb_score})
        logger.info(f"LightGBM F1: {lgb_score:.4f}")
    except ImportError:
        logger.warning("LightGBM not installed — skipping")

    # Final evaluation
    logger.info("=" * 50)
    logger.info("Training complete!")
    logger.info(f"Models saved to: {loader.models_dir}")
    logger.info(f"Available models: {loader.list_models()}")

    # Classification report on full data
    y_pred = rf.predict(X_scaled)
    print("\n=== Random Forest Classification Report ===")
    print(classification_report(y, y_pred, target_names=["distracted", "focused", "fatigued"]))


def main():
    parser = argparse.ArgumentParser(description="Train SmartStudy ensemble classifier")
    parser.add_argument("--data", default="ml_training/datasets", help="Training data directory")
    parser.add_argument("--version", default="v1.0", help="Model version string")
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("SmartStudy Ensemble Training Pipeline")
    logger.info("=" * 50)

    df = load_training_data(args.data)
    train_models(df, version=args.version)


if __name__ == "__main__":
    main()
