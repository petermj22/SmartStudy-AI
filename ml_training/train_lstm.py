"""
Script: train_lstm.py
Purpose: Train LSTM fatigue predictor and export to TFLite for on-device inference.
Usage:   python ml_training/train_lstm.py --data ml_training/datasets/

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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.ml.model_loader import ModelLoader
from backend.data.data_validator import DataValidator


def build_sequences(
    df: pd.DataFrame, feature_cols: list, seq_length: int = 300,
) -> tuple:
    """Build LSTM-ready sequences from time-series data."""
    X_sequences, y_labels = [], []

    for session_id in df.get("session_id", pd.Series(range(len(df)))).unique():
        if "session_id" in df.columns:
            session_data = df[df["session_id"] == session_id].sort_index()
        else:
            session_data = df

        if len(session_data) < seq_length:
            continue

        features = session_data[feature_cols].values.astype(np.float32)

        for i in range(0, len(features) - seq_length, seq_length // 4):
            seq = features[i: i + seq_length]
            if len(seq) == seq_length:
                # Label = average fatigue in the NEXT window
                next_start = i + seq_length
                next_end = min(next_start + 150, len(features))
                if next_end > next_start and "cumulative_fatigue_score" in feature_cols:
                    fidx = feature_cols.index("cumulative_fatigue_score")
                    future_fatigue = features[next_start:next_end, fidx].mean()
                else:
                    # Use EAR-based proxy
                    ear_idx = feature_cols.index("avg_ear") if "avg_ear" in feature_cols else 0
                    future_ear = features[next_start:next_end, ear_idx].mean() if next_end > next_start else 0.3
                    future_fatigue = max(0, (0.3 - future_ear) / 0.1)

                X_sequences.append(seq)
                y_labels.append(np.clip(future_fatigue, 0, 1))

    if not X_sequences:
        return np.array([]), np.array([])

    return np.array(X_sequences), np.array(y_labels)


def train_lstm(X: np.ndarray, y: np.ndarray, version: str = "v1.0") -> None:
    """Train LSTM model and export to TFLite."""
    try:
        import tensorflow as tf
        from tensorflow.keras import layers, models, callbacks
    except ImportError:
        logger.error("TensorFlow not installed. Install with: pip install tensorflow")
        return

    loader = ModelLoader()
    seq_length, n_features = X.shape[1], X.shape[2]

    logger.info(f"Building LSTM: seq_length={seq_length}, features={n_features}")

    # Split
    split = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    # Build model
    model = models.Sequential([
        layers.LSTM(64, return_sequences=True, input_shape=(seq_length, n_features)),
        layers.Dropout(0.3),
        layers.LSTM(32, return_sequences=False),
        layers.Dropout(0.2),
        layers.Dense(16, activation="relu"),
        layers.Dense(1, activation="sigmoid"),
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="mse", metrics=["mae"],
    )

    model.summary()

    # Train
    early_stop = callbacks.EarlyStopping(
        monitor="val_loss", patience=10, restore_best_weights=True,
    )
    reduce_lr = callbacks.ReduceLROnPlateau(
        monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6,
    )

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=100, batch_size=32,
        callbacks=[early_stop, reduce_lr],
        verbose=1,
    )

    # Evaluate
    val_loss, val_mae = model.evaluate(X_val, y_val, verbose=0)
    logger.info(f"Validation — Loss: {val_loss:.4f}, MAE: {val_mae:.4f}")

    # Save Keras model
    keras_path = loader.models_dir / f"lstm_fatigue_{version}.h5"
    model.save(str(keras_path))
    logger.info(f"Keras model saved: {keras_path}")

    # Convert to TFLite
    try:
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        tflite_model = converter.convert()

        tflite_path = loader.models_dir / f"lstm_fatigue_{version}.tflite"
        with open(tflite_path, "wb") as f:
            f.write(tflite_model)
        logger.info(f"TFLite model saved: {tflite_path} ({len(tflite_model) / 1024:.0f} KB)")
    except Exception as e:
        logger.warning(f"TFLite conversion failed: {e}")

    logger.info("LSTM training complete!")


def main():
    parser = argparse.ArgumentParser(description="Train SmartStudy LSTM fatigue predictor")
    parser.add_argument("--data", default="ml_training/datasets", help="Training data directory")
    parser.add_argument("--version", default="v1.0", help="Model version")
    parser.add_argument("--seq-length", type=int, default=300, help="Sequence length")
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("SmartStudy LSTM Training Pipeline")
    logger.info("=" * 50)

    loader = ModelLoader()
    temporal_features = loader.get_lstm_features()
    if not temporal_features:
        temporal_features = ["avg_ear", "blink_rate", "mar", "head_pitch", "head_yaw", "gaze_stability", "cumulative_fatigue_score"]

    # Load data
    csv_files = glob.glob(os.path.join(args.data, "*.csv"))
    if not csv_files:
        logger.error(f"No CSV files found in {args.data}")
        logger.info("Record sessions first using the data recorder, then re-run.")
        sys.exit(1)

    dfs = [pd.read_csv(f) for f in csv_files]
    df = pd.concat(dfs, ignore_index=True)

    validator = DataValidator()
    df = validator.clean_dataframe(df)

    # Build sequences
    available_features = [f for f in temporal_features if f in df.columns]
    logger.info(f"Using features: {available_features}")

    X, y = build_sequences(df, available_features, seq_length=args.seq_length)
    if len(X) == 0:
        logger.error("Not enough data for sequences. Need longer recordings.")
        sys.exit(1)

    logger.info(f"Sequences: {X.shape} | Labels: {y.shape}")
    train_lstm(X, y, version=args.version)


if __name__ == "__main__":
    main()
