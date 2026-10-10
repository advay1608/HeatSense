"""
05_dependence.py
------------------
OWNER: Person 7  (see assignments/PERSON7.md)
WRITES: results.json["dependence"]
READS:  backend/data/dataset.csv, results.json["distribution_fit"]

Evaluates serial persistence, multi-lag autocorrelation, and heatwave clustering:
- Lag-1 through Lag-14 autocorrelations
- Strict exceedance rule: temperature > threshold_c
- Consecutive run-length analysis (clustering duration and frequency)
- First-order Markov chain transition probabilities:
    P(Hot tomorrow | Hot today) vs. P(Hot tomorrow | Cool today)
"""

import os
import sys
import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
from common import load_temps, read_results, write_result

DEFAULT_THRESHOLD_C = 36.0


def lag1_autocorrelation(temps: np.ndarray) -> float:
    x = temps[:-1]
    y = temps[1:]
    return float(np.corrcoef(x, y)[0, 1])


def run_lengths(is_extreme: np.ndarray) -> list:
    """Returns a list of consecutive-True run lengths in a boolean array."""
    runs = []
    current = 0
    for val in is_extreme:
        if val:
            current += 1
        else:
            if current > 0:
                runs.append(current)
            current = 0
    if current > 0:
        runs.append(current)
    return runs


def main():
    temps = load_temps()
    results = read_results()

    threshold = float(
        results.get("distribution_fit", {}).get("threshold_c", DEFAULT_THRESHOLD_C)
    )

    autocorr = lag1_autocorrelation(temps)
    n = len(temps)
    significance_bound = 1.96 / np.sqrt(n)
    is_significant = bool(abs(autocorr) > significance_bound)

    # Multi-lag autocorrelations
    multilag = {}
    for lag in [1, 2, 3, 5, 7, 14]:
        multilag[f"lag_{lag}"] = round(float(np.corrcoef(temps[:-lag], temps[lag:])[0, 1]), 4)

    # Rule: temperature > threshold
    is_extreme = temps > threshold
    runs = run_lengths(is_extreme)

    max_run = max(runs) if runs else 0
    mean_run = round(float(np.mean(runs)), 2) if runs else 0.0
    median_run = round(float(np.median(runs)), 1) if runs else 0.0
    n_runs = len(runs)
    total_extreme_days = int(np.sum(is_extreme))
    days_in_multiday_clusters = sum(r for r in runs if r >= 2)
    pct_clustered = round((days_in_multiday_clusters / total_extreme_days * 100), 1) if total_extreme_days > 0 else 0.0

    # Markov transition probabilities
    ext_curr = is_extreme[:-1]
    ext_next = is_extreme[1:]
    n_hot_today = int(np.sum(ext_curr))
    n_cool_today = int(np.sum(~ext_curr))
    p_hot_given_hot = round(float(np.sum(ext_curr & ext_next) / n_hot_today), 4) if n_hot_today > 0 else 0.0
    p_hot_given_cool = round(float(np.sum((~ext_curr) & ext_next) / n_cool_today), 4) if n_cool_today > 0 else 0.0
    p_base_unconditional = round(float(np.mean(is_extreme)), 4)

    if is_significant and max_run > 1:
        interpretation = (
            f"Extreme days exhibit pronounced serial persistence (lag-1 autocorrelation={autocorr:.4f}, "
            f"longest run={max_run} consecutive days, mean run={mean_run:.1f} days). "
            f"Crucially, P(Hot tomorrow | Hot today) = {p_hot_given_hot*100:.1f}%, compared to only "
            f"{p_hot_given_cool*100:.1f}% if today is cool. Furthermore, {pct_clustered}% of all extreme days occur "
            "as part of multi-day heatwave episodes, demonstrating that extreme heat arrives in persistent waves rather than isolated events."
        )
    elif n_runs == 0:
        interpretation = (
            "No days in the record exceeded the threshold, so no clustering "
            "could be assessed. Consider this when interpreting the exceedance "
            "probability from other sections."
        )
    else:
        interpretation = (
            f"Extreme days appear largely independent (lag-1 autocorrelation="
            f"{autocorr:.4f}, not statistically significant). The per-day "
            "probability estimate is a reasonable description of real-world risk."
        )

    result = {
        "threshold_c": threshold,
        "exceedance_rule": "temperature > threshold_c",
        "lag1_autocorrelation": round(autocorr, 4),
        "is_significant": is_significant,
        "significance_bound": round(float(significance_bound), 4),
        "multilag_autocorrelations": multilag,
        "max_run_length_above_threshold": int(max_run),
        "mean_run_length_above_threshold": mean_run,
        "median_run_length_above_threshold": median_run,
        "n_exceedance_runs": int(n_runs),
        "total_extreme_days": total_extreme_days,
        "pct_extreme_days_in_multiday_clusters": pct_clustered,
        "transition_probabilities": {
            "unconditional_base_probability": p_base_unconditional,
            "p_hot_tomorrow_given_hot_today": p_hot_given_hot,
            "p_hot_tomorrow_given_cool_today": p_hot_given_cool,
            "limitations_note": "Transition probabilities and clustering metrics reflect combined synoptic weather persistence and strong seasonal concentration (summer). They must not be interpreted as stationary, time-invariant physical constants across all calendar seasons.",
        },
        "interpretation": interpretation,
    }

    print("=== DEPENDENCE & CLUSTERING ===")
    print(f"Lag-1 autocorrelation: {result['lag1_autocorrelation']} (bound: +/-{significance_bound:.4f}, significant: {is_significant})")
    print(f"Weekly persistence (Lag-7): {multilag['lag_7']}")
    print(f"Runs above {threshold} C: {n_runs} clusters | Max run: {max_run} days | Mean run: {mean_run} days")
    print(f"Markov transition: P(Hot|Hot)={p_hot_given_hot*100:.1f}% vs P(Hot|Cool)={p_hot_given_cool*100:.1f}% (Base: {p_base_unconditional*100:.1f}%)")
    print(f"Clustering: {pct_clustered}% of extreme days occur in multi-day runs (>=2 days).")

    write_result("dependence", result)
    return result


if __name__ == "__main__":
    main()
