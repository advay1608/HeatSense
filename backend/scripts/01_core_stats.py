"""
01_core_stats.py
-----------------
OWNER: Person 1  (see assignments/PERSON1.md)
WRITES: results.json["core_stats"]
READS:  backend/data/dataset.csv only

Computes mean, variance, SD, CV with bootstrap 95% confidence intervals,
a Shapiro-Wilk normality test, and a manual step-by-step calculation for
one sample point (assignment requirement).
"""

import numpy as np
from scipy import stats
from common import load_temps, write_result

RANDOM_SEED = 42
BOOTSTRAP_RESAMPLES = 10_000


def bootstrap_ci(data: np.ndarray, stat_fn, n_resamples: int = BOOTSTRAP_RESAMPLES,
                  seed: int = RANDOM_SEED) -> list:
    """Generic bootstrap 95% CI for any statistic function (np.mean, np.std, cv...)."""
    rng = np.random.default_rng(seed)
    n = len(data)
    estimates = np.empty(n_resamples)
    for i in range(n_resamples):
        resample = rng.choice(data, size=n, replace=True)
        estimates[i] = stat_fn(resample)
    lower, upper = np.percentile(estimates, [2.5, 97.5])
    return [round(float(lower), 3), round(float(upper), 3)]


def cv_percent(data: np.ndarray) -> float:
    return (np.std(data, ddof=1) / np.mean(data)) * 100


def manual_walkthrough(temps: np.ndarray, mean: float, sample_index: int = 0) -> dict:
    x_i = temps[sample_index]
    deviation = x_i - mean
    return {
        "sample_index": sample_index,
        "x_i": round(float(x_i), 2),
        "mean": round(float(mean), 4),
        "deviation": round(float(deviation), 4),
        "squared_deviation": round(float(deviation ** 2), 4),
    }


def main():
    temps = load_temps()

    n = len(temps)
    mean = np.mean(temps)
    variance = np.var(temps, ddof=1)
    std_dev = np.std(temps, ddof=1)
    cv = cv_percent(temps)

    mean_ci = bootstrap_ci(temps, lambda d: np.mean(d))
    std_ci = bootstrap_ci(temps, lambda d: np.std(d, ddof=1))
    cv_ci = bootstrap_ci(temps, cv_percent)

    shapiro_stat, shapiro_p = stats.shapiro(temps)

    result = {
        "n_days": int(n),
        "mean": round(float(mean), 3),
        "mean_ci95": mean_ci,
        "variance": round(float(variance), 3),
        "std_dev": round(float(std_dev), 3),
        "std_dev_ci95": std_ci,
        "cv_percent": round(float(cv), 2),
        "cv_percent_ci95": cv_ci,
        "shapiro_wilk": {
            "statistic": round(float(shapiro_stat), 4),
            "p_value": round(float(shapiro_p), 4),
            "is_normal_at_5pct": bool(shapiro_p >= 0.05),
        },
        "manual_walkthrough": manual_walkthrough(temps, mean),
    }

    print("=== CORE STATISTICS ===")
    print(f"n = {result['n_days']}")
    print(f"Mean = {result['mean']} C  (95% CI: {mean_ci})")
    print(f"Std Dev = {result['std_dev']} C  (95% CI: {std_ci})")
    print(f"CV = {result['cv_percent']}%  (95% CI: {cv_ci})")
    print(f"Shapiro-Wilk p = {result['shapiro_wilk']['p_value']} "
          f"(Normal at 5%: {result['shapiro_wilk']['is_normal_at_5pct']})")

    write_result("core_stats", result)
    return result


if __name__ == "__main__":
    main()
