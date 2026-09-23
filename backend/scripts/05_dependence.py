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

    is_extreme = temps > threshold
    runs = run_lengths(is_extreme)

    max_run = max(runs) if runs else 0
    mean_run = round(float(np.mean(runs)), 2) if runs else 0.0
    n_runs = len(runs)

    if is_significant and max_run > 1:
        interpretation = (
            f"Extreme days show clustering (lag-1 autocorrelation={autocorr:.2f}, "
            f"longest run={max_run} consecutive days). Per-day probability "
            f"underestimates real-world heatwave risk — extreme conditions "
            f"tend to persist once they start."
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
        "max_run_length_above_threshold": int(max_run),
        "mean_run_length_above_threshold": mean_run,
        "n_exceedance_runs": int(n_runs),
        "interpretation": interpretation,
    }

    print("=== DEPENDENCE & CLUSTERING ===")
    print(f"Lag-1 autocorrelation: {result['lag1_autocorrelation']} "
          f"(significant: {is_significant})")
    print(f"Runs above {threshold}C: {n_runs}, max length {max_run}, mean length {mean_run}")
    print(interpretation)

    write_result("dependence", result)
    return result


if __name__ == "__main__":
    main()
