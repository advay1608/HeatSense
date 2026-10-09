"""
test_pipeline.py
-----------------
Automated test suite verifying HeatSense end-to-end data ingestion,
statistical computation contracts, schema integrity, and frontend snapshot sync.

Usage:
    python backend/scripts/test_pipeline.py
"""

import json
import os
import sys
import unittest
import numpy as np
import pandas as pd

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(THIS_DIR)
DATA_PATH = os.path.join(BACKEND_DIR, "data", "dataset.csv")
META_PATH = os.path.join(BACKEND_DIR, "data", "dataset_metadata.json")
RESULTS_PATH = os.path.join(BACKEND_DIR, "output", "results.json")
FIGURES_DIR = os.path.join(BACKEND_DIR, "output", "figures")
FRONTEND_SNAPSHOT = os.path.join(THIS_DIR, "..", "..", "frontend", "results.snapshot.json")


class TestHeatSensePipeline(unittest.TestCase):

    def test_01_dataset_integrity(self):
        """Verifies dataset.csv exists, has valid schema, and non-empty records."""
        self.assertTrue(os.path.exists(DATA_PATH), f"Missing {DATA_PATH}")
        df = pd.read_csv(DATA_PATH)
        self.assertIn("date", df.columns)
        self.assertIn("max_temp_c", df.columns)
        self.assertGreaterEqual(len(df), 30, "Dataset must have at least 30 observations")
        self.assertFalse(df["max_temp_c"].isna().any(), "Dataset has missing temperatures")
        
        # Verify chronological ordering
        dates = pd.to_datetime(df["date"])
        self.assertTrue(dates.is_monotonic_increasing, "Dataset dates must be monotonically increasing")
        
        # Verify reasonable meteorological ranges
        temps = df["max_temp_c"].to_numpy()
        self.assertGreater(float(np.min(temps)), -50.0)
        self.assertLess(float(np.max(temps)), 65.0)

    def test_02_metadata_integrity(self):
        """Verifies dataset_metadata.json has required fields and Open-Meteo citation."""
        self.assertTrue(os.path.exists(META_PATH), f"Missing {META_PATH}")
        with open(META_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
        required_keys = ["location_name", "latitude", "longitude", "source", "start_date", "end_date", "citation"]
        for k in required_keys:
            self.assertIn(k, meta, f"Metadata missing required key '{k}'")
        self.assertIn("Open-Meteo", meta["source"])

    def test_03_results_json_schema(self):
        """Verifies results.json contains all 7 team sections plus metadata."""
        self.assertTrue(os.path.exists(RESULTS_PATH), f"Missing {RESULTS_PATH}")
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            res = json.load(f)

        required_sections = [
            "core_stats",
            "distribution_fit",
            "simulation",
            "trend",
            "dependence",
            "synthesis",
            "dataset_info"
        ]
        for section in required_sections:
            self.assertIn(section, res, f"results.json missing section '{section}'")

        # 1. core_stats checks (Person 1)
        cs = res["core_stats"]
        self.assertIn("mean", cs)
        self.assertIn("std_dev", cs)
        self.assertIn("cv_percent", cs)
        self.assertIn("mean_ci95", cs)
        self.assertIn("shapiro_wilk", cs)
        self.assertGreater(cs["std_dev"], 0)

        # 2. distribution_fit checks (Person 1)
        dfit = res["distribution_fit"]
        self.assertIn("best_model", dfit)
        self.assertIn("threshold_c", dfit)
        self.assertIn("candidates", dfit)
        self.assertGreaterEqual(len(dfit["candidates"]), 4)
        self.assertIn("theoretical_probability", dfit)
        self.assertTrue(0 <= dfit["theoretical_probability"] <= 1)

        # 3. simulation checks (Person 5)
        sim = res["simulation"]
        self.assertIn("monte_carlo", sim)
        self.assertIn("bootstrap_probability", sim)
        self.assertIn("comparison", sim)
        self.assertIn("return_period_days", sim)
        self.assertIn("threshold_sensitivity", sim)
        self.assertTrue(0 <= sim["bootstrap_probability"] <= 1)
        self.assertGreater(sim["return_period_days"], 0)

        # 4. trend checks (Person 6)
        trend = res["trend"]
        self.assertIn("slope_c_per_day", trend)
        self.assertIn("slope_c_per_decade", trend)
        self.assertIn("r_squared", trend)
        self.assertIn("is_statistically_significant", trend)
        self.assertIn("residuals", trend)
        self.assertEqual(len(trend["residuals"]), cs["n_days"])

        # 5. dependence checks (Person 7)
        dep = res["dependence"]
        self.assertIn("lag1_autocorrelation", dep)
        self.assertIn("multilag_autocorrelations", dep)
        self.assertIn("transition_probabilities", dep)
        self.assertIn("interpretation", dep)
        self.assertTrue(-1 <= dep["lag1_autocorrelation"] <= 1)

        # 6. synthesis checks (Person 1)
        synth = res["synthesis"]
        self.assertIn("heat_risk_index", synth)
        self.assertIn("risk_band", synth)
        self.assertIn(synth["risk_band"], ["low", "moderate", "high"])
        self.assertTrue(0 <= synth["heat_risk_index"] <= 1)

    def test_04_all_figures_generated(self):
        """Verifies all 6 required publication PNG figures are generated."""
        expected_figs = [
            "01_histogram.png",
            "02_boxplot.png",
            "03_qqplot.png",
            "04_convergence.png",
            "05_sensitivity.png",
            "06_autocorrelation.png"
        ]
        for fig_name in expected_figs:
            fig_path = os.path.join(FIGURES_DIR, fig_name)
            self.assertTrue(os.path.exists(fig_path), f"Missing figure {fig_path}")
            self.assertGreater(os.path.getsize(fig_path), 1000, f"Figure {fig_name} is empty or corrupted")

    def test_05_frontend_snapshot_sync(self):
        """Verifies frontend/results.snapshot.json is synchronized with backend results.json."""
        self.assertTrue(os.path.exists(FRONTEND_SNAPSHOT), "Missing frontend snapshot")
        with open(RESULTS_PATH, "r", encoding="utf-8") as f1, open(FRONTEND_SNAPSHOT, "r", encoding="utf-8") as f2:
            backend_data = json.load(f1)
            frontend_data = json.load(f2)
        self.assertEqual(backend_data["core_stats"]["n_days"], frontend_data["core_stats"]["n_days"])
        self.assertEqual(backend_data["distribution_fit"]["best_model"], frontend_data["distribution_fit"]["best_model"])
        self.assertEqual(backend_data["synthesis"]["heat_risk_index"], frontend_data["synthesis"]["heat_risk_index"])


if __name__ == "__main__":
    unittest.main()
