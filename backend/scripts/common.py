"""
common.py
---------
Shared utilities used by EVERY script in backend/scripts/.

THIS FILE IS THE INTEGRATION CONTRACT FOR THE WHOLE PROJECT.
Do not fork it, copy it, or write your own version. Import from it.

What it gives you:
  - load_dataset()        -> reads backend/data/dataset.csv into a numpy array
  - write_result(section, data)  -> merges your results into the ONE shared
                                     backend/output/results.json file, under
                                     your own top-level key, without wiping
                                     out anyone else's key.
  - read_results()         -> reads the current merged results.json (useful if
                               your script depends on someone else's output,
                               e.g. distribution fit needs core_stats' mean).

Why this exists:
  Seven people are writing seven scripts independently. If everyone writes
  their own JSON/CSV export format, the frontend and report have to special-
  case every person's file. Instead, every script writes into ONE shared file
  (results.json), each person owning exactly one top-level key that matches
  their assignment doc. Person 2's dashboard and Person 4's report then read ONE
  file and know exactly where to find everything.

  If you follow your assignment doc's schema exactly, your work is
  automatically integrable the moment you run your script. That is the
  entire point of this file existing.
"""

import json
import os
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Centralized Configuration & Paths (imported from config.py)
# ---------------------------------------------------------------------------
from config import (
    CITY,
    STATE,
    COUNTRY,
    LOCATION_NAME,
    SHORT_LOCATION_NAME,
    REQUESTED_LATITUDE,
    REQUESTED_LONGITUDE,
    TIMEZONE,
    VARIABLE,
    UNITS,
    UNITS_SYMBOL,
    DEFAULT_START_DATE,
    DEFAULT_THRESHOLD_C,
    EXCEEDANCE_RULE,
    THIS_DIR,
    BACKEND_DIR,
    DATA_DIR,
    OUTPUT_DIR,
    FIGURES_DIR,
    FRONTEND_DIR,
    DATA_PATH,
    DATASET_METADATA_PATH,
    MUMBAI_CACHE_PATH,
    DELHI_ARCHIVE_PATH,
    RESULTS_PATH,
    SNAPSHOT_PATH,
    FORECAST_HISTORY_PATH,
)


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------
def load_dataset(path: str = DATA_PATH) -> pd.DataFrame:
    """
    Loads backend/data/dataset.csv.

    REQUIRED SCHEMA (Person 3 owns producing this file):
        date,max_temp_c
        2026-08-06,33.4
        2026-08-07,32.3
        ...

    - 'date' must be ISO format (YYYY-MM-DD), sorted ascending, no duplicates.
    - 'max_temp_c' must be numeric, no missing values (drop or document any
      gap days explicitly instead of leaving blanks).
    - Minimum 30 rows.

    Returns a pandas DataFrame with columns ['date', 'max_temp_c'], 'date'
    parsed as datetime64.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"\n\nCould not find {path}\n"
            "This means backend/data/dataset.csv does not exist yet.\n"
            "That file is Person 3's deliverable — see "
            "assignments/PERSON3.md. Until it exists, run "
            "backend/scripts/00_generate_sample_data.py to create a "
            "placeholder so you can develop and test your own script.\n"
        )
    df = pd.read_csv(path)
    required_cols = {"date", "max_temp_c"}
    if not required_cols.issubset(df.columns):
        raise ValueError(
            f"dataset.csv is missing required columns. "
            f"Expected {required_cols}, found {set(df.columns)}."
        )
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    if df["max_temp_c"].isna().any():
        raise ValueError(
            "dataset.csv contains missing max_temp_c values. "
            "Clean or explicitly document gaps before this is used downstream."
        )
    if len(df) < 30:
        print(
            f"WARNING: dataset.csv has only {len(df)} rows. "
            "Assignment minimum is 20, recommended is 30+."
        )
    return df


def load_temps(path: str = DATA_PATH) -> np.ndarray:
    """Convenience wrapper -> just the temperature values as a numpy array."""
    return load_dataset(path)["max_temp_c"].to_numpy()


# ---------------------------------------------------------------------------
# Shared results file (THE integration mechanism)
# ---------------------------------------------------------------------------
def read_results(path: str = RESULTS_PATH) -> dict:
    """
    Reads the current merged results.json. Returns {} if it doesn't exist yet
    (i.e. you are the first script to run).
    """
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def write_result(section: str, data: dict, path: str = RESULTS_PATH) -> None:
    """
    Merges `data` into results.json under the top-level key `section`,
    WITHOUT touching any other section another script already wrote.

    Example (from a Person 1 script):
        write_result("core_stats", {
            "mean": 32.97,
            "mean_ci": [32.31, 33.62],
            "std_dev": 2.10,
            "std_dev_ci": [1.78, 2.39],
            "cv_percent": 6.44,
            "cv_percent_ci": [5.5, 7.3],
            "n_days": 45
        })

    This is SAFE to call multiple times (e.g. re-running your script during
    development) — it always overwrites only your own section, and always
    re-reads the latest file first so you never clobber a teammate's section
    that was written after you last read the file.

    `section` MUST exactly match the key name given in your assignment doc
    (assignments/PERSON<N>.md) — the frontend and report code look up
    results[section] literally by that string.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    current = read_results(path)
    current[section] = data
    current["_meta"] = current.get("_meta", {})
    current["_meta"]["last_updated_section"] = section
    with open(path, "w") as f:
        json.dump(current, f, indent=2, default=_json_default)
    print(f"[common.write_result] wrote section '{section}' -> {path}")


def _json_default(obj):
    """Lets json.dump handle numpy types without extra boilerplate everywhere."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


if __name__ == "__main__":
    # Quick self-test: run `python3 common.py` to sanity-check your setup.
    print(f"BACKEND_DIR = {BACKEND_DIR}")
    print(f"DATA_PATH   = {DATA_PATH}  (exists: {os.path.exists(DATA_PATH)})")
    print(f"RESULTS_PATH = {RESULTS_PATH}  (exists: {os.path.exists(RESULTS_PATH)})")
    try:
        df = load_dataset()
        print(f"Loaded dataset OK — {len(df)} rows, "
              f"{df['date'].min().date()} to {df['date'].max().date()}")
    except FileNotFoundError as e:
        print(e)
