"""
SmartStudy Model Evaluator
Run: python ml_training/evaluate_models.py
"""

from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from loguru import logger


def evaluate_ensemble(data_path: str = "ml_training/datasets/labeled_sessions") -> None:
    from backend.ml.ensemble_classifier import EnsembleFocusClassifier, FEATURE_COLUMNS
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, confusion_matrix

    data_dir = Path(data_path)
    csvs = list(data_dir.glob("**/*.csv"))

    if not csvs:
        logger.warning(f"No CSV files found in {data_path}")
        logger.info("Creating synthetic evaluation data...")
        rng = np.random.default_rng(42)
        n = 500
        X = rng.uniform(0, 1, (n, len(FEATURE_COLUMNS)))
        y = rng.integers(0, 3, n)
    else:
        dfs = []
        for f in csvs:
            try:
                df = pd.read_csv(f)
                if "focus_state" in df.columns:
                    dfs.append(df)
            except Exception:
                pass
        combined = pd.concat(dfs, ignore_index=True)
        for col in FEATURE_COLUMNS:
            if col not in combined.columns:
                combined[col] = 0.0
        X = combined[FEATURE_COLUMNS].fillna(0).values.astype(np.float32)
        y = combined["focus_state"].values.astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = EnsembleFocusClassifier()

    if not clf._is_trained:
        logger.info("Training ensemble on evaluation data...")
        clf.train(X_train, y_train, optimize=False)

    metrics = clf.evaluate(X_test, y_test)

    print("\n" + "=" * 50)
    print("  ENSEMBLE CLASSIFIER EVALUATION")
    print("=" * 50)
    print(f"  Accuracy:    {metrics['accuracy']:.4f}")
    print(f"  F1 Weighted: {metrics['f1_weighted']:.4f}")
    print(f"\n  Per-Class F1: {metrics['f1_per_class']}")
    print(f"\n  Confusion Matrix:")
    cm = np.array(metrics["confusion_matrix"])
    print(f"  {cm}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="ml_training/datasets/labeled_sessions")
    args = parser.parse_args()
    evaluate_ensemble(args.data)
