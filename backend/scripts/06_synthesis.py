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

    write_result("synthesis", result)
    return result


if __name__ == "__main__":
    main()
