"""
Phase 3 — Step 2: Train the Isolation Forest, once, offline.

Run this AFTER generate_training_data.py, from the ASCENT project root:
    python ai/train_anomaly_model.py

Output: ai/anomaly_model.pkl

Why we save score_min/score_max alongside the model:
Isolation Forest's raw score_samples() output is an unbounded, not very
human-readable number (roughly -0.5 to 0.5, more negative = more
anomalous). Judges won't find that intuitive on a dashboard. So at
training time we record the min/max raw score seen on KNOWN-NOMINAL data,
and save it with the model. At inference time (anomaly_detector.py) we
use those bounds to rescale any new reading into a 0-100 "anomaly score"
that's actually readable at a glance.
"""

import os
import csv
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

#s1 fetaures add kare hai yha me
FEATURES = [
    "chamber_pressure_bar",
    "temperature_K",
    "rpm",
    "fuel_flow_kg_s",
    "vibration_mm_s",
]

#yha pe training data add kara
#training_data.csv se sara normal telemetry data ek numpy array
# mein le aata hai — ye wo file hai jo generate_training_data.py ne
# banayi (fake, normal-range readings, bahut saari).

def load_training_data(csv_path):
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        rows = [[float(row[feat]) for feat in FEATURES] for row in reader]
    return np.array(rows)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(here, "training_data.csv")
    model_path = os.path.join(here, "anomaly_model.pkl")

    X = load_training_data(csv_path)
    print(f"Loaded {X.shape[0]} training rows, {X.shape[1]} features")


  #yha model train hora
    model = IsolationForest(
        n_estimators=200,
        contamination="auto",
        random_state=42,
    )
    model.fit(X)

    # Raw anomaly scores on the training set itself, used only to set
    # the normalization range described above.
    raw_scores = model.score_samples(X)
    score_min = float(raw_scores.min())
    score_max = float(raw_scores.max())

    bundle = {
        "model": model,
        "features": FEATURES,
        "score_min": score_min,
        "score_max": score_max,
    }

    joblib.dump(bundle, model_path)
    print(f"Saved trained model to {model_path}")
    print(f"score_min={score_min:.4f} score_max={score_max:.4f}")


if __name__ == "__main__":
    main()