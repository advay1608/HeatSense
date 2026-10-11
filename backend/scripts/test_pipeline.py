"""
test_pipeline.py
-----------------
Automated test suite verifying HeatSense end-to-end data ingestion,
canonical Mumbai location configuration, statistical computation contracts,
schema integrity, distribution modelling honesty, forecast validation,
safeguard against unverified cache reuse, threshold consistency, and
frontend snapshot synchronization.

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
sys.path.insert(0, THIS_DIR)

from config import (
    CITY,
    STATE,
    COUNTRY,
    LOCATION_NAME,
    REQUESTED_LATITUDE,
    REQUESTED_LONGITUDE,
    TIMEZONE,
    DEFAULT_THRESHOLD_C,
    DEFAULT_START_DATE,
    DATA_PATH,
    DATA_DIR,
    FORECAST_HISTORY_PATH,
    META_PATH,
    RESULTS_PATH,
    FIGURES_DIR,
    EXPORTS_DIR,
    SNAPSHOT_PATH,
    BACKEND_DIR,
)

from common import read_results


class TestHeatSensePipeline(unittest.TestCase):

    def setUp(self):
        self.assertTrue(os.path.exists(RESULTS_PATH), f"Missing {RESULTS_PATH}. Run run_pipeline.py first.")
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            self.res = json.load(f)

    def test_01_canonical_location_configuration(self):
        """Verifies canonical project location is centralized as Mumbai, Maharashtra, India."""
        self.assertEqual(CITY, "Mumbai")
        self.assertEqual(STATE, "Maharashtra")
        self.assertEqual(COUNTRY, "India")
        self.assertEqual(LOCATION_NAME, "Mumbai, Maharashtra, India")
        self.assertAlmostEqual(REQUESTED_LATITUDE, 19.0760, places=4)
        self.assertAlmostEqual(REQUESTED_LONGITUDE, 72.8777, places=4)
        self.assertEqual(TIMEZONE, "Asia/Kolkata")
        self.assertEqual(DEFAULT_THRESHOLD_C, 36.0)
        self.assertEqual(DEFAULT_START_DATE, "1950-01-01")

    def test_02_dataset_integrity_and_mumbai_provenance(self):
        """Verifies dataset.csv exists, has valid schema, continuous valid Mumbai records."""
        self.assertTrue(os.path.exists(DATA_PATH), f"Missing {DATA_PATH}")
        df = pd.read_csv(DATA_PATH)
        self.assertIn("date", df.columns)
        self.assertIn("max_temp_c", df.columns)
        self.assertEqual(len(df), 28042, "Mumbai dataset must have exactly 28,042 observations (1950-01-01 to 2026-10-10)")
        self.assertFalse(df["max_temp_c"].isna().any(), "Dataset contains missing temperature values")

        # Verify chronological ordering and uniqueness
        dates = pd.to_datetime(df["date"])
        self.assertTrue(dates.is_monotonic_increasing, "Dataset dates must be monotonically increasing")
        self.assertEqual(len(dates), len(dates.drop_duplicates()), "Duplicate dates detected in dataset")

        # Verify Mumbai coastal temperature range
        temps = df["max_temp_c"].to_numpy()
        self.assertAlmostEqual(float(np.min(temps)), 22.1, places=1)
        self.assertAlmostEqual(float(np.max(temps)), 41.3, places=1)

    def test_03_metadata_integrity_and_era5_grid_point(self):
        """Verifies dataset_metadata.json records Mumbai provenance, grid point, coverage, and limitations."""
        self.assertTrue(os.path.exists(META_PATH), f"Missing {META_PATH}")
        with open(META_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)

        required_keys = [
            "location_name", "requested_latitude", "requested_longitude",
            "latitude", "longitude", "elevation_m", "source", "underlying_model",
            "selected_variable", "units", "requested_period", "actual_data_coverage",
            "retrieval_timestamp", "is_cached", "limitations", "citation"
        ]
        for k in required_keys:
            self.assertIn(k, meta, f"Metadata missing required key '{k}'")

        self.assertIn("Mumbai", meta["location_name"])
        self.assertEqual(meta["selected_variable"], "temperature_2m_max")
        self.assertEqual(meta["units"], "degrees Celsius")
        self.assertAlmostEqual(meta["requested_latitude"], 19.0760, places=3)
        self.assertAlmostEqual(meta["requested_longitude"], 72.8777, places=3)
        # ERA5 returned grid point for Mumbai: lat ~19.086, lon ~72.853, elevation ~6.0m
        self.assertAlmostEqual(meta["latitude"], 19.086115, places=2)
        self.assertAlmostEqual(meta["longitude"], 72.85291, places=2)
        self.assertAlmostEqual(meta["elevation_m"], 6.0, places=1)
        self.assertIsInstance(meta["limitations"], list)
        self.assertGreaterEqual(len(meta["limitations"]), 2)

    def test_04_mumbai_cache_integrity_safeguard(self):
        """Ensures that only genuine Mumbai datasets with matching coordinates can pass cache validation."""
        import tempfile
        from importlib import import_module
        fetcher = import_module("00_fetch_weather_data")

        # Test cache validation function
        self.assertTrue(hasattr(fetcher, "is_valid_mumbai_cache"))

        # Verify that current dataset passes Mumbai validation
        self.assertTrue(fetcher.is_valid_mumbai_cache(DATA_PATH, META_PATH))

        # Verify that non-Mumbai metadata fails cache validation
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            json.dump({"location_name": "External Station", "latitude": 28.61}, tf)
            invalid_meta_path = tf.name
        try:
            self.assertFalse(
                fetcher.is_valid_mumbai_cache(DATA_PATH, invalid_meta_path),
                "Security check failed: Non-Mumbai metadata was accepted as valid Mumbai cache!"
            )
        finally:
            if os.path.exists(invalid_meta_path):
                os.remove(invalid_meta_path)

    def test_05_core_statistical_formulas_mumbai(self):
        """Validates all mathematical and statistical formulas against raw Mumbai observations."""
        df = pd.read_csv(DATA_PATH)
        temps = df["max_temp_c"].to_numpy()
        n = len(temps)
        cs = self.res["core_stats"]

        # 1. Sample size
        self.assertEqual(cs["n_days"], n)
        self.assertEqual(cs["n_missing"], 0)

        # 2. Mean
        expected_mean = float(np.mean(temps))
        self.assertAlmostEqual(cs["mean"], expected_mean, places=2)
        self.assertAlmostEqual(cs["mean"], 30.237, places=2)

        # 3. Variance and Standard Deviation (unbiased ddof=1)
        expected_var = float(np.var(temps, ddof=1))
        expected_std = float(np.std(temps, ddof=1))
        self.assertAlmostEqual(cs["variance"], expected_var, places=2)
        self.assertAlmostEqual(cs["std_dev"], expected_std, places=2)
        self.assertAlmostEqual(cs["std_dev"], 2.387, places=2)

        # 4. Range, Min, Max
        self.assertAlmostEqual(cs["min_temp"], float(np.min(temps)), places=1)
        self.assertAlmostEqual(cs["max_temp"], float(np.max(temps)), places=1)
        self.assertAlmostEqual(cs["range_c"], float(np.max(temps) - np.min(temps)), places=1)

        # 5. Median and Quartiles
        self.assertAlmostEqual(cs["median_temp"], float(np.median(temps)), places=1)
        self.assertAlmostEqual(cs["median_temp"], 30.2, places=1)
        self.assertAlmostEqual(cs["iqr"], float(cs["q3"] - cs["q1"]), places=1)

        # 6. Exceedance Count and Proportion Consistency (> 36.0°C)
        thresh = cs["threshold_c"]
        self.assertEqual(thresh, 36.0)
        self.assertEqual(cs["exceedance_rule"], "temperature > threshold_c")
        expected_crossings = int(np.sum(temps > thresh))
        expected_prop = float(expected_crossings / n)
        self.assertEqual(expected_crossings, 265, "Mumbai must have exactly 265 days > 36.0°C")
        self.assertEqual(cs["exceedance_count"], expected_crossings)
        self.assertAlmostEqual(cs["exceedance_proportion"], expected_prop, places=4)
        self.assertAlmostEqual(cs["exceedance_proportion"], 0.00945, places=3)

        # 7. Coefficient of Variation honesty
        self.assertIn("cv_kelvin_percent", cs)
        self.assertIn("cv_interpretation_warning", cs)
        kelvin_cv = (expected_std / (expected_mean + 273.15)) * 100
        self.assertAlmostEqual(cs["cv_kelvin_percent"], kelvin_cv, places=1)

        # 8. Monthly and Seasonal Summaries consistency
        self.assertIn("monthly_summary", cs)
        self.assertIn("seasonal_summary", cs)
        self.assertEqual(len(cs["monthly_summary"]), 12)
        self.assertEqual(len(cs["seasonal_summary"]), 4)
        sum_monthly_crossings = sum(m["exceedance_count"] for m in cs["monthly_summary"])
        self.assertEqual(sum_monthly_crossings, expected_crossings)

    def test_06_distribution_modelling_mumbai(self):
        """Verifies candidate models, Log-Normal ranking for Mumbai, and GoF diagnostics."""
        dfit = self.res["distribution_fit"]
        self.assertIn("best_model", dfit)
        # Log-Normal is the best model for Mumbai (AIC: 128,123.52)
        self.assertEqual(dfit["best_model"], "lognorm")
        self.assertIn("candidates", dfit)
        self.assertGreaterEqual(len(dfit["candidates"]), 4)

        candidate_names = [c["name"] for c in dfit["candidates"]]
        for expected in ["lognorm", "gamma", "normal", "gumbel_r"]:
            self.assertIn(expected, candidate_names)

        # Goodness-of-fit checks
        for c in dfit["candidates"]:
            self.assertIn("goodness_of_fit", c)
            gof = c["goodness_of_fit"]
            self.assertIn("ks_statistic", gof)
            self.assertIn("ks_p_value", gof)
            self.assertIn("ks_p_value_formatted", gof)
            self.assertNotEqual(gof["ks_p_value_formatted"], "0.0")

        # Disclose that formal KS rejects single unimodal distribution across coastal seasons
        self.assertTrue(dfit["all_candidates_inadequate"])
        self.assertIn("diagnostics_summary", dfit)

        # Empirical baseline is present and matches 265 / 28042
        self.assertEqual(dfit["empirical_exceedance_count"], 265)
        self.assertAlmostEqual(dfit["empirical_probability"], 0.0095, places=4)

    def test_07_threshold_and_denominator_consistency(self):
        """Verifies threshold and empirical denominators match across all sections for Mumbai."""
        cs = self.res["core_stats"]
        dfit = self.res["distribution_fit"]
        dep = self.res["dependence"]
        synth = self.res["synthesis"]

        self.assertEqual(cs["threshold_c"], dfit["threshold_c"])
        self.assertEqual(dfit["threshold_c"], dep["threshold_c"])
        self.assertEqual(cs["exceedance_count"], dfit["empirical_exceedance_count"])
        self.assertEqual(cs["exceedance_count"], dep["total_extreme_days"])
        self.assertEqual(cs["exceedance_count"], 265)
        self.assertAlmostEqual(cs["exceedance_proportion"], dfit["empirical_probability"], places=4)
        self.assertAlmostEqual(cs["exceedance_proportion"], synth["components_used"]["base_probability"], places=4)

    def test_08_real_forecast_mumbai(self):
        """Verifies forecast is from real Open-Meteo forecast API for Mumbai with honest timing and date separation."""
        self.assertIn("forecast", self.res)
        fc = self.res["forecast"]
        self.assertEqual(fc["status"], "available")
        self.assertIn("Open-Meteo", fc["source"])
        self.assertIn("Mumbai", fc.get("location_name", ""))
        self.assertAlmostEqual(fc["latitude"], 19.08, places=1)
        self.assertAlmostEqual(fc["longitude"], 72.85, places=1)
        self.assertEqual(len(fc["days"]), 7, "Forecast must contain 7 daily forecasts")

        # Must record retrieval timestamp and explicit timing disclosure
        self.assertIn("retrieval_timestamp_ist", fc)
        self.assertIn("timing_disclosure", fc)
        self.assertIn("client data retrieval time", fc["timing_disclosure"])

        # First day must be flagged as today (current-day diagnostic cycle)
        first_day = fc["days"][0]
        self.assertTrue(first_day.get("is_today", False))
        self.assertEqual(first_day.get("phase"), "today_current_cycle")

        # Days 2-7 must be flagged as genuinely future projections
        for d in fc["days"][1:]:
            self.assertFalse(d.get("is_today", False))
            self.assertTrue(d.get("is_future", False))
            self.assertEqual(d.get("phase"), "future_nwp_projection")

        for d in fc["days"]:
            self.assertIn("date", d)
            self.assertIn("forecast_max_temp_c", d)
            self.assertGreater(d["forecast_max_temp_c"], 20.0)
            self.assertLess(d["forecast_max_temp_c"], 45.0)
            # Pseudo confidence intervals must not be attached to NWP items
            self.assertNotIn("confidence_interval_95", d)

    def test_09_heat_risk_index_audit(self):
        """Verifies Heat Risk Index is explicitly labeled as uncalibrated operational indicator."""
        synth = self.res["synthesis"]
        self.assertFalse(synth["is_calibrated_probability"], "Heat Risk Index must NOT be presented as a calibrated probability")
        self.assertIn("Exploratory", synth["index_name"])
        self.assertIn("transparent_indicators", synth)
        self.assertEqual(synth["risk_band"].upper(), "LOW")
        self.assertEqual(synth["heat_risk_index"], 1.05)

    def test_10_figures_and_snapshot_sync(self):
        """Verifies 6 figures exist and frontend snapshot is synchronized with Mumbai results."""
        expected_figs = [
            "01_histogram.png", "02_boxplot.png", "03_qqplot.png",
            "04_convergence.png", "05_sensitivity.png", "06_autocorrelation.png"
        ]
        for fig_name in expected_figs:
            p = os.path.join(FIGURES_DIR, fig_name)
            self.assertTrue(os.path.exists(p), f"Missing figure {fig_name}")
            self.assertGreater(os.path.getsize(p), 1000)

        # Snapshot synchronization check
        self.assertTrue(os.path.exists(SNAPSHOT_PATH))
        with open(RESULTS_PATH, "r", encoding="utf-8") as f1, open(SNAPSHOT_PATH, "r", encoding="utf-8") as f2:
            b_data = json.load(f1)
            f_data = json.load(f2)
        self.assertEqual(b_data["core_stats"]["n_days"], f_data["core_stats"]["n_days"])
        self.assertEqual(b_data["core_stats"]["exceedance_count"], 265)
        self.assertEqual(f_data["core_stats"]["exceedance_count"], 265)
        self.assertEqual(b_data["distribution_fit"]["best_model"], f_data["distribution_fit"]["best_model"])
        self.assertEqual(b_data["synthesis"]["heat_risk_index"], 1.05)
        self.assertEqual(f_data["synthesis"]["heat_risk_index"], 1.05)
        self.assertEqual(len(b_data["forecast"]["days"]), len(f_data["forecast"]["days"]))

    def test_11_complete_years_trend_and_partial_year_handling(self):
        """Verifies annual trend strictly uses complete calendar years (1950-2025) and labels partial 2026."""
        tr = self.res["trend"]
        self.assertIn("complete_years_trend", tr)
        cy = tr["complete_years_trend"]

        self.assertEqual(cy["n_years"], 76, "Complete years trend must evaluate exactly 76 full calendar years (1950-2025)")
        self.assertIn("1950-2025", cy["period"])
        self.assertIn("2026", cy["excluded_partial_year"])
        # Mumbai complete calendar years trend: +0.1128 °C/decade, R^2 = 0.2892
        self.assertAlmostEqual(cy["slope_c_per_decade"], 0.1128, places=2)
        self.assertAlmostEqual(cy["r_squared"], 0.2892, places=3)
        self.assertLess(cy["slope_ci95_per_decade"][0], cy["slope_c_per_decade"])
        self.assertGreater(cy["slope_ci95_per_decade"][1], cy["slope_c_per_decade"])
        self.assertLess(cy["p_value"], 0.001)

        # Annual summaries check
        ann = tr["annual_summaries"]

        self.assertEqual(len(ann), 77)
        last_year = ann[-1]
        self.assertEqual(last_year["year"], 2026)
        self.assertFalse(last_year["is_complete_year"], "2026 must be labeled as partial year")
        self.assertIn("partial", last_year["coverage_note"])
        self.assertEqual(last_year["n_days"], 283)

        for y_sum in ann[:-1]:
            self.assertTrue(y_sum["is_complete_year"], f"Year {y_sum['year']} should be a complete calendar year")

    def test_12_export_deliverables_and_daily_temperatures(self):
        """Verifies export deliverables exist and daily_temperatures array matches core stats exact count."""
        tr = self.res["trend"]
        self.assertIn("daily_temperatures", tr)
        daily_temps = tr["daily_temperatures"]
        self.assertEqual(len(daily_temps), self.res["core_stats"]["n_days"])
        exact_exceedances = sum(1 for t in daily_temps if t > 36.0)
        self.assertEqual(exact_exceedances, self.res["core_stats"]["exceedance_count"])
        self.assertEqual(exact_exceedances, 265)

        # Check export files exist
        csv_export = os.path.join(BACKEND_DIR, "output", "heatsense_cleaned_historical_temperatures.csv")
        json_export = os.path.join(BACKEND_DIR, "output", "heatsense_statistical_summary.json")
        stats_csv = os.path.join(BACKEND_DIR, "output", "heatsense_statistical_summary.csv")
        html_report = os.path.join(BACKEND_DIR, "output", "heatsense_project_report.html")
        frontend_report = os.path.join(BACKEND_DIR, "..", "frontend", "report.html")

        self.assertTrue(os.path.exists(csv_export), "Cleaned CSV export must exist")
        self.assertTrue(os.path.exists(json_export), "Statistical summary JSON must exist")
        self.assertTrue(os.path.exists(stats_csv), "Statistical summary CSV must exist")
        self.assertTrue(os.path.exists(html_report), "HTML report must exist in backend/output/")
        self.assertTrue(os.path.exists(frontend_report), "HTML report must exist in frontend/")

        # Verify cleaned CSV row count (header comments + 28,042 rows + header line)
        with open(csv_export, "r", encoding="utf-8") as f:
            lines = [l for l in f if not l.startswith("#")]
        self.assertEqual(len(lines), 28043, "Cleaned CSV must contain 1 header line + 28,042 observations")

        # Verify HTML report identifies Mumbai
        with open(html_report, "r", encoding="utf-8") as f:
            report_text = f.read()
        self.assertIn("Mumbai", report_text)
        self.assertIn("265", report_text)

    def test_13_multi_threshold_and_boundary_behavior(self):
        """Verifies boundary behavior and threshold tests at 20°C, 36°C, and 42°C for Mumbai."""
        df = pd.read_csv(DATA_PATH)
        temps = df["max_temp_c"].to_numpy()
        n = len(temps)

        # At 20°C: 100% of days exceed in tropical Mumbai (all-time minimum is 22.1°C)
        p_20 = float(np.sum(temps > 20.0) / n)
        self.assertEqual(p_20, 1.0)

        # At 36°C: canonical baseline
        count_36 = int(np.sum(temps > 36.0))
        self.assertEqual(count_36, 265)

        # Boundary equality test: days where temp == 36.0 must NOT be counted as exceedance
        count_strict = int(np.sum(temps > 36.0))
        count_nonstrict = int(np.sum(temps >= 36.0))
        exact_equal_36 = int(np.sum(temps == 36.0))
        self.assertEqual(count_nonstrict - count_strict, exact_equal_36)
        self.assertEqual(exact_equal_36, 23, "There are exactly 23 days with max_temp_c == 36.0 in Mumbai")
        self.assertEqual(count_nonstrict, 288)

        # At 42°C: 0 days exceed (all-time recorded peak in Mumbai is 41.3°C)
        count_42 = int(np.sum(temps > 42.0))
        self.assertEqual(count_42, 0)

    def test_14_api_failure_honesty_safeguard(self):
        """Verifies that API failures produce honest errors, never fabricated data or silent invalid fallbacks."""
        from importlib import import_module
        fetcher = import_module("00_fetch_weather_data")

        # Test invalid coordinates request
        with self.assertRaises(Exception):
            fetcher.fetch_archive_data(latitude=999.0, longitude=999.0, start_date="1950-01-01", end_date="1950-01-05")

    def test_15_consistency_audit_regressions(self):
        """Regression tests for seasonal breakdown, trend R^2, Kelvin mean conversion, and unrounded risk index."""
        cs = self.res["core_stats"]
        tr = self.res["trend"]
        synth = self.res["synthesis"]
        df = pd.read_csv(DATA_PATH)
        df["date"] = pd.to_datetime(df["date"])
        df["month"] = df["date"].dt.month

        # 1. Seasonal counts and exact denominators
        # Winter: Dec, Jan, Feb
        w_df = df[df["month"].isin([12, 1, 2])]
        self.assertEqual(len(w_df), 6918)
        self.assertEqual(int(np.sum(w_df["max_temp_c"] > 36.0)), 5)

        # Summer: Mar, Apr, May
        s_df = df[df["month"].isin([3, 4, 5])]
        self.assertEqual(len(s_df), 7084)
        self.assertEqual(int(np.sum(s_df["max_temp_c"] > 36.0)), 253)

        # Monsoon: Jun, Jul, Aug, Sep
        m_df = df[df["month"].isin([6, 7, 8, 9])]
        self.assertEqual(len(m_df), 9394)
        self.assertEqual(int(np.sum(m_df["max_temp_c"] > 36.0)), 0)

        # Post-Monsoon: Oct, Nov
        pm_df = df[df["month"].isin([10, 11])]
        self.assertEqual(len(pm_df), 4646)
        self.assertEqual(int(np.sum(pm_df["max_temp_c"] > 36.0)), 7)

        # Total sums without overlaps or gaps
        self.assertEqual(len(w_df) + len(s_df) + len(m_df) + len(pm_df), 28042)
        self.assertEqual(5 + 253 + 0 + 7, 265)

        # Verify seasonal summary in results.json matches row-level calculation
        seas_dict = {s["season_name"]: s for s in cs["seasonal_summary"]}
        self.assertEqual(seas_dict["Winter"]["n_days"], 6918)
        self.assertEqual(seas_dict["Winter"]["exceedance_count"], 5)
        self.assertEqual(seas_dict["Summer (Pre-Monsoon)"]["n_days"], 7084)
        self.assertEqual(seas_dict["Summer (Pre-Monsoon)"]["exceedance_count"], 253)
        self.assertEqual(seas_dict["Monsoon"]["n_days"], 9394)
        self.assertEqual(seas_dict["Monsoon"]["exceedance_count"], 0)
        self.assertEqual(seas_dict["Post-Monsoon"]["n_days"], 4646)
        self.assertEqual(seas_dict["Post-Monsoon"]["exceedance_count"], 7)

        # 2. Kelvin absolute temperature conversion
        mean_c = cs["mean"]
        self.assertAlmostEqual(mean_c, 30.237, places=2)
        expected_kelvin = mean_c + 273.15
        self.assertAlmostEqual(expected_kelvin, 303.387, places=2)
        self.assertEqual(cs.get("kelvin_mean"), 303.387)
        # CV on Kelvin scale
        std_c = cs["std_dev"]
        kelvin_cv = (std_c / expected_kelvin) * 100
        self.assertAlmostEqual(cs["cv_kelvin_percent"], kelvin_cv, places=2)
        self.assertAlmostEqual(cs["cv_kelvin_percent"], 0.79, places=2)

        # 3. Secular trend R^2 consistency
        cy = tr["complete_years_trend"]
        self.assertIn("r_squared", cy)
        self.assertAlmostEqual(cy["r_squared"], 0.2892, places=3)
        self.assertAlmostEqual(cy["slope_c_per_decade"], 0.1128, places=3)

        # 4. Unrounded Heat Risk Index calculation evaluates to exact 1.05
        self.assertEqual(synth["heat_risk_index"], 1.05)

    def test_16_forecast_scientific_validation_audit(self):
        """
        Audits forecast validation ledger, verification source transparency, and statistical discipline:
        - Current-day diagnostic retrieval (11 Oct) is strictly excluded from out-of-sample validation.
        - Pending future dates (12–17 Oct) cannot be scored prematurely.
        - Uncalibrated Markov results and confidence intervals are not presented as validated forecasts.
        - Verification target nature explicitly discloses ECMWF ERA5 reanalysis proxy limitations.
        """
        fc = self.res["forecast"]
        days = fc["days"]
        self.assertEqual(len(days), 7)

        # 1. Day 1 Audit: Current-Day Diagnostic Retrieval
        day1 = days[0]
        retrieval_date = fc.get("retrieval_timestamp_ist", "")[:10] if fc.get("retrieval_timestamp_ist") else day1["date"]
        self.assertEqual(day1["date"], retrieval_date)
        self.assertTrue(day1["is_today"])
        self.assertEqual(day1["phase"], "today_current_cycle")
        # Strict exclusion from out-of-sample validation ledger
        self.assertFalse(day1["validation"]["is_validated"], "Current-day diagnostic must NOT be counted as validated forecast")
        self.assertEqual(day1["validation"]["status"], "same_day_diagnostic_excluded")
        self.assertIn("Excluded from Out-of-Sample Validation", day1["validation"]["note"])
        # Markov scenario for Day 1: must be conditioning state S_0, NOT 100% forward transition probability
        self.assertIn("historical_markov_scenario", day1)
        self.assertTrue(day1["historical_markov_scenario"]["is_conditioning_state"])
        self.assertIsNone(day1["historical_markov_scenario"]["conditional_exceedance_probability"], "Day 1 must not have a forward transition probability")

        # 2. Days 2–7 Audit: Future Forecasts Pending Verification
        for d in days[1:]:
            self.assertTrue(d["is_future"])
            self.assertEqual(d["phase"], "future_nwp_projection")
            self.assertFalse(d["validation"]["is_validated"], "Future date cannot be scored before observation cycle completes")
            self.assertEqual(d["validation"]["status"], "pending_future_observation")
            self.assertIsNone(d["validation"]["observed_proxy_max_temp_c"])
            self.assertIsNone(d["validation"]["difference_c"])
            # Historical Markov scenario overlay must be labeled exploratory with seasonality disclaimer
            self.assertIn("historical_markov_scenario", d)
            hms = d["historical_markov_scenario"]
            self.assertFalse(hms["is_conditioning_state"])
            self.assertIsNotNone(hms["conditional_exceedance_probability"])
            self.assertIn("Exploratory", hms["disclaimer"])
            self.assertIn("NOT a calibrated future weather probability", hms["disclaimer"])

        # 3. Validation Summary Audit
        self.assertIn("validation_summary", fc)
        vs = fc["validation_summary"]
        self.assertEqual(vs["total_target_days"], 7)
        self.assertEqual(vs["n_validated_pairs"], 0, "Out-of-sample validated pairs must be exactly 0")
        self.assertEqual(vs["n_out_of_sample_validated"], 0)
        self.assertEqual(vs["n_same_day_diagnostic_excluded"], 1)
        self.assertEqual(vs["n_pending_future_days"], 6)
        self.assertEqual(vs["validated_dates"], [], "No out-of-sample dates may be marked as validated")
        self.assertEqual(vs["same_day_diagnostic_dates"], [day1["date"]])
        self.assertEqual(len(vs["pending_dates"]), 6)
        # MAE and Bias must be None (not 0.0°C) when 0 valid out-of-sample pairs exist
        self.assertIsNone(vs["mae_c"], "MAE must be None when no out-of-sample verification pairs exist")
        self.assertIsNone(vs["bias_c"], "Bias must be None when no out-of-sample verification pairs exist")

        # 4. Explicit Verification Target Disclosure (ERA5 Reanalysis Proxy)
        self.assertIn("verification_target_nature", vs)
        self.assertIn("ERA5", vs["verification_target_nature"])
        self.assertIn("Reanalysis", vs["verification_target_nature"])
        self.assertIn("do not constitute independent physical station verification", vs["verification_target_nature"])

        # 5. Meteorological Context Disclosure (IMD Santacruz vs Colaba)
        self.assertIn("meteorological_comparison", fc)
        mc = fc["meteorological_comparison"]
        self.assertIn("imd_santacruz_station", mc)
        self.assertIn("imd_colaba_station", mc)
        self.assertIn("open_meteo_nwp_grid", mc)

        # 6. History Ledger snapshot validation
        history_path = os.path.join(DATA_DIR, "forecast_history.json")
        self.assertTrue(os.path.exists(history_path))
        with open(history_path, "r", encoding="utf-8") as f:
            hist = json.load(f)
        self.assertIn("forecast_runs", hist)
        last_run = hist["forecast_runs"][-1]
        self.assertEqual(len(last_run["predictions"]), 7)
        self.assertFalse(last_run["predictions"][0]["is_pre_target_snapshot"])
        self.assertFalse(last_run["predictions"][0]["eligible_for_out_of_sample_validation"])
        self.assertTrue(last_run["predictions"][1]["is_pre_target_snapshot"])
        self.assertTrue(last_run["predictions"][1]["eligible_for_out_of_sample_validation"])


if __name__ == "__main__":
    unittest.main()
