"""
run_pipeline.py
-----------------
Runs the full backend analysis pipeline in the correct dependency order.
See ARCHITECTURE.md SS6 for why this exact order is required.

Usage:
    python3 backend/scripts/run_pipeline.py

If backend/data/dataset.csv does not exist yet, generates placeholder data
first so the pipeline can still be tested end-to-end.
"""

import os
import sys
import importlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "dataset.csv")

PIPELINE = [
    "01_core_stats",
    "02_distribution_fit",
    "03_simulation",
    "04_trend",
    "05_dependence",
    "06_synthesis",
    "07_visualizations",
]


def main():
    if not os.path.exists(DATA_PATH):
        print("No dataset.csv found — generating placeholder data first.\n")
        gen = importlib.import_module("00_generate_sample_data")
        gen.generate_sample_data().to_csv(os.path.abspath(DATA_PATH), index=False)

    for step in PIPELINE:
        print(f"\n{'='*60}\nRunning {step}.py\n{'='*60}")
        module = importlib.import_module(step)
        module.main()

    print(f"\n{'='*60}\nPipeline complete. See backend/output/results.json "
          f"and backend/output/figures/\n{'='*60}")


if __name__ == "__main__":
    main()
