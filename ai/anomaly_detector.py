"""
Phase 3 — Step 3: Runtime anomaly scoring.

Import this from app.py and call score_anomaly(engine) once per telemetry
cycle. The model is loaded from disk ONCE (module-level cache), not on
every call — loading a pickle every second would be wasteful and would
also add latency to your /telemetry endpoint.

If the model file doesn't exist yet (you haven't run the two training
scripts), this fails SAFE: it returns a neutral placeholder instead of
crashing Flask. That matters mid-demo more than it matters right now.
"""

import os
import joblib
import numpy as np

_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "anomaly_model.pkl")
_bundle = None
_load_attempted = False


def _get_bundle():
    global _bundle, _load_attempted
    if _bundle is None and not _load_attempted:
        _load_attempted = True
        try:
            _bundle = joblib.load(_MODEL_PATH)
        except FileNotFoundError:
            _bundle = None
    return _bundle


def score_anomaly(engine):
    """
    engine: the live engine dict (same shape as SYSTEM_STATE["engine"]).

    Returns a dict:
        {
            "anomaly_score": float 0-100 (higher = more anomalous),
            "is_anomaly": bool,
            "model_ready": bool  # False if .pkl hasn't been trained yet
        }
    """
    bundle = _get_bundle()

    if bundle is None:
        return {"anomaly_score": 0.0, "is_anomaly": False, "model_ready": False}

    features = bundle["features"]
    x = np.array([[engine[feat] for feat in features]])

    raw_score = bundle["model"].score_samples(x)[0]
    score_min = bundle["score_min"]
    score_max = bundle["score_max"]

    # Rescale so higher = more anomalous, clipped to 0-100 since live
    # readings can exceed the training set's observed range.
    span = score_max - score_min
    normalized = ((score_max - raw_score) / span) * 100 if span > 0 else 0.0
    normalized = float(np.clip(normalized, 0, 100))

    # Starting threshold — after Phase 3 is wired up, watch what scores
    # look like during a real fault injection and adjust if 60 feels
    # too sensitive or not sensitive enough. Don't tune this blind.
    is_anomaly = normalized > 60

    return {
        "anomaly_score": round(normalized, 1),
        "is_anomaly": is_anomaly,
        "model_ready": True,
    }