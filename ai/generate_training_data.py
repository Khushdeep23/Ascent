"""
Phase 3 — Step 1: Generate nominal training data.

Runs the REAL update_engine() simulator (same one your live dashboard
uses) for N_CYCLES steps with NO fault active, and records the 5 core
telemetry readings each cycle. This becomes the "what does normal look
like" dataset the Isolation Forest learns from.

Run this from the ASCENT project root:
    python ai/generate_training_data.py

Output: ai/training_data.csv
"""

import os
import sys
import csv
import json

# Make sure "telemetry" package is importable regardless of where this
# script is invoked from, since it lives one level up from ai/.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from telemetry.simulator import update_engine  # noqa: E402

# These 5 fields are the ONLY ones update_engine() actively randomizes.
# Everything else in the engine dict (throttle_percent, thrust_kN, etc.)
# is either static or only changes as a RESPONSE to an AI decision, not
# as a raw physical symptom — so it's excluded from the feature set.
FEATURES = [
    "chamber_pressure_bar",
    "temperature_K",
    "rpm",
    "fuel_flow_kg_s",
    "vibration_mm_s",
]

N_CYCLES = 3000


def main():
    engine_data_path = os.path.join(PROJECT_ROOT, "telemetry", "engine_data.json")
    with open(engine_data_path, "r") as f:
        seed_state = json.load(f)

    engine = dict(seed_state["engine"])  # working copy

    output_path = os.path.join(os.path.dirname(__file__), "training_data.csv")

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(FEATURES)

        for _ in range(N_CYCLES):
            engine = update_engine(engine)
            writer.writerow([engine[feat] for feat in FEATURES])

    print(f"Wrote {N_CYCLES} nominal readings to {output_path}")


if __name__ == "__main__":
    main()