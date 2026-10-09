"""
run_pipeline.py
-----------------
Runs the full backend analysis pipeline in the correct dependency order.
See ARCHITECTURE.md §6 for why this exact order is required.

Usage:
    python backend/scripts/run_pipeline.py
    python backend/scripts/run_pipeline.py --fetch-api
    python backend/scripts/run_pipeline.py --fetch-api --city mumbai
    python backend/scripts/run_pipeline.py --fetch-api --city delhi --start-date 1950-01-01

If --fetch-api is specified (or if backend/data/dataset.csv does not exist yet),
fetches real all-time meteorological records via Open-Meteo Archive API.
After execution, automatically syncs results to frontend/results.snapshot.json.
"""

import argparse
import importlib
import os
import shutil
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)

DATA_PATH = os.path.join(THIS_DIR, "..", "data", "dataset.csv")
RESULTS_PATH = os.path.join(THIS_DIR, "..", "output", "results.json")
SNAPSHOT_PATH = os.path.join(THIS_DIR, "..", "..", "frontend", "results.snapshot.json")

PIPELINE = [
    "01_core_stats",
    "02_distribution_fit",
    "03_simulation",
    "04_trend",
    "05_dependence",
    "06_synthesis",
    "07_visualizations",
]


def sync_frontend_snapshot():
    """Copies backend/output/results.json to frontend/results.snapshot.json."""
    if os.path.exists(RESULTS_PATH):
        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        shutil.copyfile(RESULTS_PATH, SNAPSHOT_PATH)
        print(f"\n[Snapshot Sync] Copied {RESULTS_PATH} -> {SNAPSHOT_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Execute full HeatSense statistical pipeline.")
    parser.add_argument("--fetch-api", action="store_true", help="Fetch live all-time data from Open-Meteo API first")
    parser.add_argument("--city", default="delhi", help="City preset for API fetch (e.g. delhi, mumbai, phoenix, london)")
    parser.add_argument("--lat", type=float, default=None, help="Custom latitude")
    parser.add_argument("--lon", type=float, default=None, help="Custom longitude")
    parser.add_argument("--start-date", default="1950-01-01", help="Start date for API fetch (default: 1950-01-01)")
    parser.add_argument("--end-date", default=None, help="End date for API fetch (default: latest available)")

    args = parser.parse_args()

    # Step 0: Ingest live data if requested or if dataset does not exist
    if args.fetch_api or not os.path.exists(DATA_PATH):
        print("\n" + "=" * 60)
        print("Ingesting live real-world data from Open-Meteo Archive API")
        print("=" * 60)
        fetcher = importlib.import_module("00_fetch_weather_data")
        fetcher.ingest_data(
            city_key=args.city,
            latitude=args.lat,
            longitude=args.lon,
            start_date=args.start_date,
            end_date=args.end_date,
        )

    # Step 1 through 7: Sequential analytical pipeline execution
    for step in PIPELINE:
        print(f"\n{'='*60}\nRunning {step}.py\n{'='*60}")
        module = importlib.import_module(step)
        module.main()

    # Automatic snapshot sync to frontend
    sync_frontend_snapshot()

    print(f"\n{'='*60}\nPipeline complete. See backend/output/results.json "
          f"and backend/output/figures/\n{'='*60}")


if __name__ == "__main__":
    main()