"""
06_synthesis.py
-----------------
OWNER: Person 1  (see assignments/PERSON1.md)
WRITES: results.json["synthesis"]
READS:  results.json["distribution_fit"], ["simulation"], ["trend"], ["dependence"], ["forecast"]

Synthesizes multiple statistical evidence streams into an exploratory
operational Heat Risk Index:
- Audited to ensure composite multipliers are NOT presented as calibrated probabilities.
- Transparently breaks down empirical baseline, heatwave clustering amplification,
  and long-term climate drift.
- Does not generate synthetic forecasts; preserves genuine numerical weather predictions
  from the Open-Meteo forecast endpoint.
"""

import importlib
import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
from common import read_results, write_result

REQUIRED_SECTIONS = ["distribution_fit", "simulation", "trend", "dependence"]

# Operational risk bands for the exploratory composite index
RISK_BANDS = [
    (10.0, "low"),
    (25.0, "moderate"),
    (float("inf"), "high"),
]


def classify_risk(score: float) -> str:
    for cutoff, label in RISK_BANDS:
        if score <= cutoff:
            return label
    return "high"


def main():
    results = read_results()
    missing = [s for s in REQUIRED_SECTIONS if s not in results]
    if missing:
        raise RuntimeError(
            f"Cannot run synthesis - missing required sections: {missing}. "
            "Execute upstream pipeline scripts first."
        )

    dist_fit = results["distribution_fit"]
    trend = results["trend"]
    dep = results["dependence"]

    core_stats = results.get("core_stats", {})
    # Baseline empirical exceedance probability computed from exact unrounded counts
    if core_stats.get("n_days", 0) > 0 and "exceedance_count" in core_stats:
        empirical_prob = core_stats["exceedance_count"] / core_stats["n_days"]
    else:
        empirical_prob = dist_fit.get("empirical_probability", dist_fit.get("theoretical_probability", 0.00945))
    theoretical_prob = dist_fit.get("theoretical_probability", empirical_prob)

    # Trend adjustment: if long-term secular drift is positive and significant,
    # apply a bounded operational penalty factor; if cooling or non-significant, 0.0
    if trend.get("is_statistically_significant") and trend.get("total_drift_c", 0.0) > 0:
        trend_adjustment = min(trend["total_drift_c"] / 10.0, 0.25)
    else:
        trend_adjustment = 0.0

    # Clustering adjustment: scales with mean consecutive heatwave duration
    # reflecting that multi-day runs compound biological and grid thermal strain
    mean_run = dep.get("mean_run_length_above_threshold", 1.0)
    if dep.get("is_significant") and mean_run > 1:
        clustering_adjustment = min((mean_run - 1.0) * 0.03, 0.35)
    else:
        clustering_adjustment = 0.0

    # Exploratory Composite Heat Risk Index (scored on a 0-100 severity scale)
    raw_composite = empirical_prob * (1.0 + trend_adjustment) * (1.0 + clustering_adjustment)
    heat_risk_score = round(min(100.0, raw_composite * 100.0), 2)
    risk_band = classify_risk(heat_risk_score)

    synthesis_result = {
        "is_calibrated_probability": False,
        "index_name": "Exploratory Heat Risk Index",
        "score_range": "0 to 100",
        "heat_risk_index": heat_risk_score,
        "raw_index_fraction": round(raw_composite, 4),
        "risk_band": risk_band,
        "formula_note": (
            "index_score (0-100) = [empirical_exceedance_rate * (1 + trend_adjustment) * (1 + clustering_adjustment)] * 100. "
            "This metric is an exploratory composite decision-support indicator, NOT a formal calibrated statistical probability."
        ),
        "components_used": {
            "base_probability": round(float(empirical_prob), 4),
            "base_probability_type": "empirical_exceedance_rate",
            "theoretical_model_probability": round(float(theoretical_prob), 4),
            "trend_adjustment": round(float(trend_adjustment), 4),
            "clustering_adjustment": round(float(clustering_adjustment), 4),
        },
        "transparent_indicators": {
            "empirical_exceedance_rate_pct": round(float(empirical_prob * 100), 2),
            "theoretical_model_probability_pct": round(float(theoretical_prob * 100), 2),
            "heatwave_clustering_multiplier": round(float(1.0 + clustering_adjustment), 3),
            "mean_heatwave_duration_days": round(float(mean_run), 2),
            "markov_p_hot_given_hot_pct": round(float(dep.get("transition_probabilities", {}).get("p_hot_tomorrow_given_hot_today", 0) * 100), 1),
            "decadal_trend_c_per_decade": round(float(trend.get("slope_c_per_decade", 0.0)), 3),
            "trend_drift_multiplier": round(float(1.0 + trend_adjustment), 3),
        },
        "risk_bands_reference": [
            {"max": 10.0, "label": "low"},
            {"max": 25.0, "label": "moderate"},
            {"max": None, "label": "high"},
        ],
    }

    # Verify forecast section exists from real Open-Meteo API; if not present, fetch it
    if "forecast" not in results or not results["forecast"].get("days"):
        try:
            fetcher = importlib.import_module("00_fetch_weather_data")
            fetcher.fetch_open_meteo_forecast()
        except Exception as e:
            print(f"[synthesis] Notice: Forecast fetch notice: {e}")

    print("=== SYNTHESIS: EXPLORATORY HEAT RISK INDEX ===")
    print(f"Empirical base exceedance rate: {empirical_prob*100:.2f}% (Theoretical model: {theoretical_prob*100:.2f}%)")
    print(f"Clustering multiplier: x{1.0 + clustering_adjustment:.3f} (Mean heatwave: {mean_run:.1f} days)")
    print(f"Trend multiplier: x{1.0 + trend_adjustment:.3f} (Decadal slope: {trend.get('slope_c_per_decade', 0.0)} C/decade)")
    print(f"Composite Heat Risk Score: {heat_risk_score} / 100 -> Band: {risk_band.upper()}")
    print("Audit note: Composite score is an exploratory operational index, not a calibrated probability.")

    write_result("synthesis", synthesis_result)
    return synthesis_result


if __name__ == "__main__":
    main()
