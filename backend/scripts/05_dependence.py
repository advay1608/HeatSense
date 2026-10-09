"""
05_dependence.py
------------------
OWNER: Person 7  (see assignments/PERSON7.md)
WRITES: results.json["dependence"]
READS:  backend/data/dataset.csv, results.json["distribution_fit"]
        (for the canonical threshold — falls back to a default if not
        yet available, but should be rerun once it is)

Lag-1 autocorrelation and run-length (heatwave clustering) analysis.
"""

import numpy as np
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

    threshold = (
        results.get("distribution_fit", {}).get("threshold_c", DEFAULT_THRESHOLD_C)
    )
    if "distribution_fit" not in results:
        print(f"NOTE: distribution_fit section not found yet — using default "
              f"threshold {DEFAULT_THRESHOLD_C}C. Rerun this script once "
              f"02_distribution_fit.py has run.")

    autocorr = lag1_autocorrelation(temps)
    n = len(temps)
    significance_bound = 1.96 / np.sqrt(n)
    is_significant = bool(abs(autocorr) > significance_bound)

    # Multi-lag autocorrelations
    multilag = {}
    for lag in [1, 2, 3, 5, 7, 14]:
        multilag[f"lag_{lag}"] = round(float(np.corrcoef(temps[:-lag], temps[lag:])[0, 1]), 4)

    is_extreme = temps > threshold
    runs = run_lengths(is_extreme)

    max_run = max(runs) if runs else 0
    mean_run = round(float(np.mean(runs)), 2) if runs else 0.0
    median_run = round(float(np.median(runs)), 1) if runs else 0.0
    n_runs = len(runs)
    total_extreme_days = int(np.sum(is_extreme))
    days_in_multiday_clusters = sum(r for r in runs if r >= 2)
    pct_clustered = round((days_in_multiday_clusters / total_extreme_days * 100), 1) if total_extreme_days > 0 else 0.0

    # Markovian state transition probabilities
    ext_curr = is_extreme[:-1]
    ext_next = is_extreme[1:]
    n_hot_today = int(np.sum(ext_curr))
    n_cool_today = int(np.sum(~ext_curr))
    p_hot_given_hot = round(float(np.sum(ext_curr & ext_next) / n_hot_today), 4) if n_hot_today > 0 else 0.0
    p_hot_given_cool = round(float(np.sum((~ext_curr) & ext_next) / n_cool_today), 4) if n_cool_today > 0 else 0.0
    p_base_unconditional = round(float(np.mean(is_extreme)), 4)

    if is_significant and max_run > 1:
        interpretation = (
            f"Extreme days show severe serial clustering (lag-1 autocorrelation={autocorr:.2f}, "
            f"longest run={max_run} consecutive days, mean run={mean_run:.1f} days). "
            f"Crucially, P(Hot tomorrow | Hot today) = {p_hot_given_hot*100:.1f}%, versus just "
            f"{p_hot_given_cool*100:.1f}% if today is cool. Over {pct_clustered}% of extreme days occur "
            f"as part of multi-day heatwaves, proving extreme heat is persistent, not isolated."
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
            f"{autocorr:.2f}, not significant at the 5% level). The per-day "
            f"probability estimate is a reasonable description of real-world risk."
        )

    result = {
        "threshold_c": threshold,
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
        },
        "interpretation": interpretation,
    }

    print("=== DEPENDENCE & CLUSTERING ===")
    print(f"Lag-1 autocorrelation: {result['lag1_autocorrelation']} (bound: +/-{significance_bound:.4f}, significant: {is_significant})")
    print(f"Weekly persistence (Lag-7): {multilag['lag_7']}")
    print(f"Runs above {threshold}C: {n_runs} discrete clusters | Max length: {max_run} days | Mean: {mean_run} days (Median: {median_run} days)")
    print(f"P(Hot tomorrow | Hot today): {p_hot_given_hot*100:.1f}% vs P(Hot tomorrow | Cool today): {p_hot_given_cool*100:.1f}% (Base: {p_base_unconditional*100:.1f}%)")
    print(f"Clustered extreme days: {pct_clustered}% of all extreme days belong to multi-day runs.")
    print(interpretation)

    write_result("dependence", result)
    return result


if __name__ == "__main__":
    main()
