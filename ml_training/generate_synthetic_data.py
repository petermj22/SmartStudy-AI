import os
import sys
from pathlib import Path
import yaml
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def get_feature_columns():
    config_path = Path("config/model_config.yaml")
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
            ensemble_config = config.get("ensemble_classifier", {})
            return ensemble_config.get("feature_columns", [])
    return []

def main():
    features = get_feature_columns()
    if not features:
        print("No features found in config.")
        return

    n_samples_per_class = 2000
    classes = [0, 1, 2] # 0: distracted, 1: focused, 2: fatigued
    data = []

    for c in classes:
        for _ in range(n_samples_per_class):
            row = {}
            for feature in features:
                # Add some class-specific logic
                mean = 0.5
                std = 0.1
                if feature == "avg_ear":
                    if c == 1: mean = 0.3
                    elif c == 2: mean = 0.2
                    elif c == 0: mean = 0.25
                elif feature == "gaze_stability":
                    if c == 1: mean = 0.9
                    elif c == 2: mean = 0.5
                    elif c == 0: mean = 0.3
                elif feature == "blink_rate":
                    if c == 1: mean = 15
                    elif c == 2: mean = 30
                    elif c == 0: mean = 20
                elif feature == "mar":
                    if c == 1: mean = 0.2
                    elif c == 2: mean = 0.4 # yawning
                    elif c == 0: mean = 0.3
                else:
                    mean = np.random.rand() * 0.5 + 0.2
                
                # Sample
                val = np.random.normal(mean, std)
                row[feature] = max(0.0, val) # mostly positive values
            row["label"] = c
            data.append(row)

    df = pd.DataFrame(data)
    
    out_dir = Path("ml_training/datasets")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "synthetic_data.csv"
    
    df.to_csv(out_file, index=False)
    print(f"Saved {len(df)} synthetic samples to {out_file}")

if __name__ == "__main__":
    main()
