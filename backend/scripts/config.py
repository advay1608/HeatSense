"""
config.py
---------
Centralized project configuration for HeatSense.
Single source of truth for the canonical study location, reference coordinates,
time zone, meteorological variables, and default analysis thresholds.

Study Location: Mumbai, Maharashtra, India
"""

import os

# ---------------------------------------------------------------------------
# Canonical Location Settings
# ---------------------------------------------------------------------------
CITY = "Mumbai"
STATE = "Maharashtra"
COUNTRY = "India"
LOCATION_NAME = "Mumbai, Maharashtra, India"
SHORT_LOCATION_NAME = "Mumbai, India"

# Reference Coordinates (Mumbai City Center / Municipal reference)
REQUESTED_LATITUDE = 19.0760
REQUESTED_LONGITUDE = 72.8777

# Local Timezone for Meteorological Aggregation
TIMEZONE = "Asia/Kolkata"

# Primary Analysis Variable
VARIABLE = "temperature_2m_max"
UNITS = "degrees Celsius"
UNITS_SYMBOL = "°C"

# Temporal Coverage Defaults
DEFAULT_START_DATE = "1950-01-01"

# Analytical Heat Threshold Default
# Selected analytical threshold for extreme temperature exceedance
DEFAULT_THRESHOLD_C = 36.0
EXCEEDANCE_RULE = "temperature > threshold_c"

# ---------------------------------------------------------------------------
# Directory Paths
# ---------------------------------------------------------------------------
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(THIS_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, "data")
OUTPUT_DIR = os.path.join(BACKEND_DIR, "output")
FIGURES_DIR = os.path.join(OUTPUT_DIR, "figures")
FRONTEND_DIR = os.path.join(BACKEND_DIR, "..", "frontend")

# Dataset and Metadata Paths
DATA_PATH = os.path.join(DATA_DIR, "dataset.csv")
DATASET_METADATA_PATH = os.path.join(DATA_DIR, "dataset_metadata.json")
META_PATH = DATASET_METADATA_PATH
MUMBAI_CACHE_PATH = os.path.join(DATA_DIR, "dataset_mumbai.csv")
DELHI_ARCHIVE_PATH = os.path.join(DATA_DIR, "dataset_delhi_archive.csv")

# Results Paths
RESULTS_PATH = os.path.join(OUTPUT_DIR, "results.json")
SNAPSHOT_PATH = os.path.join(FRONTEND_DIR, "results.snapshot.json")
EXPORTS_DIR = OUTPUT_DIR
FORECAST_HISTORY_PATH = os.path.join(DATA_DIR, "forecast_history.json")


# Export File Paths
EXPORT_CLEANED_CSV = os.path.join(OUTPUT_DIR, "heatsense_cleaned_historical_temperatures.csv")
EXPORT_STATS_JSON = os.path.join(OUTPUT_DIR, "heatsense_statistical_summary.json")
EXPORT_STATS_CSV = os.path.join(OUTPUT_DIR, "heatsense_statistical_summary.csv")
EXPORT_REPORT_HTML = os.path.join(OUTPUT_DIR, "heatsense_project_report.html")

# Frontend Mirror Paths
FRONTEND_CLEANED_CSV = os.path.join(FRONTEND_DIR, "heatsense_cleaned_historical_temperatures.csv")
FRONTEND_STATS_JSON = os.path.join(FRONTEND_DIR, "heatsense_statistical_summary.json")
FRONTEND_STATS_CSV = os.path.join(FRONTEND_DIR, "heatsense_statistical_summary.csv")
FRONTEND_REPORT_HTML = os.path.join(FRONTEND_DIR, "report.html")
