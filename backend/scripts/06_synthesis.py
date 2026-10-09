"""
06_synthesis.py
-----------------
OWNER: Person 1  (see assignments/PERSON1.md)
WRITES: results.json["synthesis"]
READS:  results.json["distribution_fit"], ["simulation"], ["trend"], ["dependence"]
        — ALL FOUR must exist. This script runs LAST in the pipeline.

Combines every other section into one composite Heat Risk Index and a
plain risk-band classification — the project's "engineering decision"
output.
"""

from common import read_results, write_result

REQUIRED_SECTIONS = ["distribution_fit", "simulation", "trend", "dependence"]

# Risk band cutoffs — documented here as the single source of truth.
# The frontend gauge (Person 2) must reuse these exact cutoffs.
RISK_BANDS = [
    (0.05, "low"),
    (0.15, "moderate"),
    (float("inf"), "high"),
]


def classify(index: float) -> str:
    for cutoff, label in RISK_BANDS:
        if index <= cutoff:
            return label
    return "high"


def main():
    results = read_results()
    missing = [s for s in REQUIRED_SECTIONS if s not in results]
    if missing:
        raise RuntimeError(
            f"Cannot run synthesis — missing sections: {missing}.\n"
            f"Run the corresponding scripts first (see ARCHITECTURE.md §6 "
            f"for pipeline order), or just run run_pipeline.py."
        )

    base_probability = results["distribution_fit"]["theoretical_probability"]

    # Trend adjustment: scale total drift relative to the base probability.
    # A larger, statistically significant upward drift nudges risk up;
    # a flat or cooling trend contributes ~0.
    trend = results["trend"]
    if trend["is_statistically_significant"] and trend["total_drift_c"] > 0:
        trend_adjustment = min(trend["total_drift_c"] / 10.0, 0.25)
    else:
        trend_adjustment = 0.0

    # Clustering adjustment: scale with how much longer extreme runs are
    # than a single isolated day, capped to avoid runaway multipliers.
    dep = results["dependence"]
    if dep["is_significant"] and dep["mean_run_length_above_threshold"] > 1:
        clustering_adjustment = min((dep["mean_run_length_above_threshold"] - 1) * 0.15, 0.3)
    else:
        clustering_adjustment = 0.0

    heat_risk_index = base_probability * (1 + trend_adjustment) * (1 + clustering_adjustment)
    risk_band = classify(heat_risk_index)

    result = {
        "heat_risk_index": round(heat_risk_index, 4),
        "risk_band": risk_band,
        "formula_note": "index = exceedance_probability * (1 + trend_adjustment) * (1 + clustering_adjustment)",
        "components_used": {
            "base_probability": base_probability,
            "trend_adjustment": round(trend_adjustment, 4),
            "clustering_adjustment": round(clustering_adjustment, 4),
        },
        "risk_bands_reference": [{"max": c if c != float("inf") else None, "label": l}
                                  for c, l in RISK_BANDS],
    }

    print("=== SYNTHESIS: HEAT RISK INDEX ===")
    print(f"Base probability: {base_probability}")
    print(f"Trend adjustment: {trend_adjustment:.4f}  Clustering adjustment: {clustering_adjustment:.4f}")
    print(f"Heat Risk Index: {result['heat_risk_index']}  ->  Band: {risk_band}")

    # 7-Day Autoregressive Weather Forecast (combining Person 6 trend & Person 7 AR(1) dependence)
    import numpy as np
    import pandas as pd
    from common import load_dataset
    df = load_dataset()
    temps = df["max_temp_c"].to_numpy()
    dates = df["date"]
    last_date = dates.iloc[-1]
    last_temp = float(temps[-1])

    # Recent 14-day momentum slope
    window = min(14, len(temps))
    recent_slope = float(np.polyfit(np.arange(window), temps[-window:], 1)[0])

    rho = float(dep.get("lag1_autocorrelation", 0.95))
    mu = float(results["core_stats"]["mean"])
    std_dev = float(results["core_stats"]["std_dev"])

    forecast_days = []
    for k in range(1, 8):
        proj_date = last_date + pd.Timedelta(days=k)
        # AR(1) mean reversion anchored to last observed temperature + seasonal momentum damping
        expected_t = mu + (rho ** k) * (last_temp - mu) + k * recent_slope * np.exp(-k / 5.0)
        spread = std_dev * np.sqrt(max(0.05, 1.0 - (rho ** (2 * k)))) + k * 0.20
        forecast_days.append({
            "day": k,
            "date": proj_date.strftime("%Y-%m-%d"),
            "expected_c": round(float(expected_t), 1),
            "spread_c": round(float(spread), 1),
            "min_projected_c": round(float(max(0.0, expected_t - spread)), 1),
            "max_projected_c": round(float(expected_t + spread), 1),
        })

    forecast_data = {
        "anchor_date": last_date.strftime("%Y-%m-%d"),
        "anchor_temp_c": round(last_temp, 1),
        "recent_trend_c_per_day": round(recent_slope, 3),
        "persistence_rho": round(rho, 4),
        "days": forecast_days,
    }
    write_result("forecast", forecast_data)

    write_result("synthesis", result)
    return result


if __name__ == "__main__":
    main()
