"""
run_pipeline.py
-----------------
Runs the full backend analysis pipeline in the correct dependency order.
See ARCHITECTURE.md §6 for why this exact order is required.

Usage:
    python backend/scripts/run_pipeline.py
    python backend/scripts/run_pipeline.py --fetch-api
    python backend/scripts/run_pipeline.py --fetch-api --start-date 1950-01-01

If --fetch-api is specified (or if backend/data/dataset.csv does not exist yet),
fetches real all-time meteorological records via Open-Meteo Archive API and NWP forecast.
After execution, automatically syncs results to frontend/results.snapshot.json.
"""

import argparse
import importlib
import json
import os
import shutil
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)

from config import (
    REQUESTED_LATITUDE,
    REQUESTED_LONGITUDE,
    LOCATION_NAME,
    DEFAULT_START_DATE,
    DATA_PATH,
    RESULTS_PATH,
    SNAPSHOT_PATH,
)

PIPELINE = [
    "01_core_stats",
    "02_distribution_fit",
    "03_simulation",
    "04_trend",
    "05_dependence",
    "06_synthesis",
    "07_visualizations",
    "generate_exports",
]


def sync_frontend_snapshot():
    """Copies backend/output/results.json to frontend/results.snapshot.json."""
    if os.path.exists(RESULTS_PATH):
        os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
        shutil.copyfile(RESULTS_PATH, SNAPSHOT_PATH)
        print(f"\n[Snapshot Sync] Copied {RESULTS_PATH} -> {SNAPSHOT_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Execute full HeatSense statistical pipeline for Mumbai.")
    parser.add_argument("--fetch-api", action="store_true", help="Fetch live all-time data from Open-Meteo API first")
    parser.add_argument("--lat", type=float, default=REQUESTED_LATITUDE, help=f"Latitude (default: {REQUESTED_LATITUDE} for Mumbai)")
    parser.add_argument("--lon", type=float, default=REQUESTED_LONGITUDE, help=f"Longitude (default: {REQUESTED_LONGITUDE} for Mumbai)")
    parser.add_argument("--name", type=str, default=LOCATION_NAME, help="Location name")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE, help="Start date for API fetch (default: 1950-01-01)")
    parser.add_argument("--end-date", default=None, help="End date for API fetch (default: latest available)")

    args = parser.parse_args()

    # Step 0: Ingest live data if requested or if dataset does not exist
    if args.fetch_api or not os.path.exists(DATA_PATH):
        print("\n" + "=" * 60)
        print("Ingesting live real-world data from Open-Meteo Archive API")
        print("=" * 60)
        fetcher = importlib.import_module("00_fetch_weather_data")
        fetcher.ingest_data(
            latitude=args.lat,
            longitude=args.lon,
            location_name=args.name,
            start_date=args.start_date,
            end_date=args.end_date,
            force_fetch=args.fetch_api,
        )

    # Ensure dataset_info is present in results.json from dataset_metadata.json if available
    meta_path = os.path.join(os.path.dirname(DATA_PATH), "dataset_metadata.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta_data = json.load(f)
                from common import write_result
                write_result("dataset_info", meta_data)
        except Exception as e:
            print(f"Warning: Could not sync dataset_metadata.json: {e}")

    # Ensure forecast data is present and synchronized with audited validation rules
    try:
        from common import read_results
        curr_res = read_results()
        fc_val = curr_res.get("forecast", {}).get("validation_summary", {})
        if "forecast" not in curr_res or "validation_summary" not in curr_res.get("forecast", {}) or fc_val.get("n_validated_pairs") != 0:
            fetcher = importlib.import_module("00_fetch_weather_data")
            fetcher.fetch_open_meteo_forecast(latitude=args.lat, longitude=args.lon)
    except Exception as e:
        print(f"Warning: Could not sync forecast: {e}")

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