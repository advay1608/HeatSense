"""
01_core_stats.py
-----------------
OWNER: Person 1  (see assignments/PERSON1.md)
WRITES: results.json["core_stats"]
READS:  backend/data/dataset.csv, backend/data/dataset_metadata.json

Computes unbiased sample statistics:
- Record count, missing observations, valid observations
- Mean, median, minimum, maximum, and range
- Q1 (25th pct), Q3 (75th pct), IQR, variance (ddof=1), standard deviation (ddof=1)
- 95% bootstrap confidence intervals for mean and standard deviation
- Heat exceedance count and proportion at canonical threshold (36.0°C) with explicit rule: temp > threshold
- Monthly and seasonal breakdowns of temperature and heat-exceedance frequencies
- Coefficient of variation with explicit interval-scale warning for Celsius (and thermodynamic Kelvin CV)
- Normality tests (Shapiro-Wilk and D'Agostino-Pearson) with appropriately formatted p-values
- Step-by-step manual calculation walkthrough for one sample point
"""

import json
import os
import numpy as np
import pandas as pd
from scipy import stats
from common import DATA_PATH, load_dataset, write_result

RANDOM_SEED = 42
BOOTSTRAP_RESAMPLES = 10_000
DEFAULT_THRESHOLD_C = 36.0


def bootstrap_ci(data: np.ndarray, stat_fn, n_resamples: int = BOOTSTRAP_RESAMPLES,
                 seed: int = RANDOM_SEED) -> list:
    """Generic bootstrap 95% CI for any statistic function."""
    rng = np.random.default_rng(seed)
    n = len(data)
    estimates = np.empty(n_resamples)
    for i in range(n_resamples):
        resample = rng.choice(data, size=n, replace=True)
        estimates[i] = stat_fn(resample)
    lower, upper = np.percentile(estimates, [2.5, 97.5])
    return [round(float(lower), 3), round(float(upper), 3)]


def format_p_value(p: float) -> str:
    """Formats p-values so extremely small numerical values are never rendered as literal zero."""
    if p < 1e-4:
        return f"< 0.0001 (approx {p:.2e})" if p > 0 else "< 0.0001"
    return f"{p:.4f}"


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


def compute_monthly_summary(df: pd.DataFrame, threshold_c: float = DEFAULT_THRESHOLD_C) -> list:
    """Computes monthly temperature stats and heat-exceedance frequencies across the historical record."""
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    summary = []
    df_copy = df.copy()
    df_copy["month"] = df_copy["date"].dt.month

    for m in range(1, 13):
        m_temps = df_copy[df_copy["month"] == m]["max_temp_c"].to_numpy()
        n_m = len(m_temps)
        exceed_m = int(np.sum(m_temps > threshold_c)) if n_m > 0 else 0
        rate_m = round(float(exceed_m / n_m), 4) if n_m > 0 else 0.0

        summary.append({
            "month_num": m,
            "month_name": month_names[m - 1],
            "n_days": int(n_m),
            "mean_c": round(float(np.mean(m_temps)), 2) if n_m > 0 else 0.0,
            "std_c": round(float(np.std(m_temps, ddof=1)), 2) if n_m > 1 else 0.0,
            "min_c": round(float(np.min(m_temps)), 1) if n_m > 0 else 0.0,
            "max_c": round(float(np.max(m_temps)), 1) if n_m > 0 else 0.0,
            "exceedance_count": exceed_m,
            "exceedance_rate": rate_m,
        })
    return summary


def compute_seasonal_summary(df: pd.DataFrame, threshold_c: float = DEFAULT_THRESHOLD_C) -> list:
    """
    Computes seasonal temperature summaries and heat-exceedance frequencies
    according to standard meteorological/IMD seasons for North India:
    - Winter: Dec, Jan, Feb
    - Summer / Pre-Monsoon: Mar, Apr, May
    - Monsoon: Jun, Jul, Aug, Sep
    - Post-Monsoon: Oct, Nov
    """
    seasons = [
        {"name": "Winter", "months": [12, 1, 2], "desc": "Mild coastal winter moderated by land and sea breezes"},
        {"name": "Summer (Pre-Monsoon)", "months": [3, 4, 5], "desc": "Pre-monsoon warm period with escalating humidity"},
        {"name": "Monsoon", "months": [6, 7, 8, 9], "desc": "Southwest monsoon overcast and heavy rains suppressing maximums"},
        {"name": "Post-Monsoon", "months": [10, 11], "desc": "Post-monsoon retreat characterized by 'October heat' surge"},
    ]
    summary = []
    df_copy = df.copy()
    df_copy["month"] = df_copy["date"].dt.month

    for s in seasons:
        s_temps = df_copy[df_copy["month"].isin(s["months"])]["max_temp_c"].to_numpy()
        n_s = len(s_temps)
        exceed_s = int(np.sum(s_temps > threshold_c)) if n_s > 0 else 0
        rate_s = round(float(exceed_s / n_s), 4) if n_s > 0 else 0.0

        summary.append({
            "season_name": s["name"],
            "description": s["desc"],
            "months": s["months"],
            "n_days": int(n_s),
            "mean_c": round(float(np.mean(s_temps)), 2) if n_s > 0 else 0.0,
            "std_c": round(float(np.std(s_temps, ddof=1)), 2) if n_s > 1 else 0.0,
            "min_c": round(float(np.min(s_temps)), 1) if n_s > 0 else 0.0,
            "max_c": round(float(np.max(s_temps)), 1) if n_s > 0 else 0.0,
            "exceedance_count": exceed_s,
            "exceedance_rate": rate_s,
        })
    return summary


def main():
    df = load_dataset()
    temps = df["max_temp_c"].to_numpy()

    # Read metadata for missing observations tracking
    meta_path = os.path.join(os.path.dirname(DATA_PATH), "dataset_metadata.json")
    missing_count = 0
    duplicate_count = 0
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                coverage = meta.get("actual_data_coverage", {})
                missing_count = coverage.get("missing_observations", 0)
                duplicate_count = coverage.get("duplicate_dates_removed", 0)
        except Exception:
            pass

    n = len(temps)
    total_records = n + missing_count

    # Moments and spread
    mean = np.mean(temps)
    variance = np.var(temps, ddof=1)
    std_dev = np.std(temps, ddof=1)
    min_temp = np.min(temps)
    max_temp = np.max(temps)
    range_temp = max_temp - min_temp

    # Quantiles
    median = np.median(temps)
    q1 = np.percentile(temps, 25)
    q3 = np.percentile(temps, 75)
    iqr = q3 - q1

    # Bootstrap 95% confidence intervals
    mean_ci = bootstrap_ci(temps, lambda d: np.mean(d))
    std_ci = bootstrap_ci(temps, lambda d: np.std(d, ddof=1))

    # Coefficient of variation analysis
    cv_celsius_ratio = std_dev / mean
    cv_percent = cv_celsius_ratio * 100
    cv_ci = bootstrap_ci(temps, lambda d: (np.std(d, ddof=1) / np.mean(d)) * 100)

    # Physical absolute thermodynamic CV (in Kelvin)
    kelvin_mean = mean + 273.15
    cv_kelvin_percent = (std_dev / kelvin_mean) * 100

    cv_warning = (
        "Celsius is an interval temperature scale with an arbitrary zero point (0°C = 273.15 K). "
        "Therefore, presenting CV = (s / mean_C) * 100% as a physically meaningful relative variability "
        "percentage is statistically invalid, as its numerical value changes arbitrarily under affine shifts. "
        "On the true ratio Kelvin scale, relative dispersion is "
        f"{cv_kelvin_percent:.2f}% (s / mean_K, where mean_K = {kelvin_mean:.2f} K)."
    )

    # Threshold exceedance (canonical 36.0°C default)
    # Strictly defined as: temperature > threshold_c
    exceedance_count = int(np.sum(temps > DEFAULT_THRESHOLD_C))
    exceedance_proportion = exceedance_count / n

    # Normality tests
    if n > 5000:
        rng = np.random.default_rng(RANDOM_SEED)
        shapiro_sample = rng.choice(temps, size=5000, replace=False)
        shapiro_stat, shapiro_p = stats.shapiro(shapiro_sample)
    else:
        shapiro_stat, shapiro_p = stats.shapiro(temps)

    dag_stat, dag_p = stats.normaltest(temps)

    # Monthly and seasonal breakdowns
    monthly_summary = compute_monthly_summary(df, DEFAULT_THRESHOLD_C)
    seasonal_summary = compute_seasonal_summary(df, DEFAULT_THRESHOLD_C)

    result = {
        "n_days": int(n),
        "n_missing": int(missing_count),
        "n_total_records": int(total_records),
        "missing_rate_percent": round(float((missing_count / total_records) * 100), 3) if total_records > 0 else 0.0,
        "duplicate_dates_count": int(duplicate_count),
        "mean": round(float(mean), 3),
        "mean_ci95": mean_ci,
        "median_temp": round(float(median), 2),
        "min_temp": round(float(min_temp), 2),
        "max_temp": round(float(max_temp), 2),
        "range_c": round(float(range_temp), 2),
        "q1": round(float(q1), 2),
        "q3": round(float(q3), 2),
        "iqr": round(float(iqr), 2),
        "variance": round(float(variance), 3),
        "std_dev": round(float(std_dev), 3),
        "std_dev_ci95": std_ci,
        "cv_percent": round(float(cv_percent), 2),
        "cv_percent_ci95": cv_ci,
        "kelvin_mean": round(float(kelvin_mean), 3),
        "cv_kelvin_percent": round(float(cv_kelvin_percent), 2),
        "cv_interpretation_warning": cv_warning,
        "threshold_c": DEFAULT_THRESHOLD_C,
        "exceedance_rule": "temperature > threshold_c",
        "exceedance_count": exceedance_count,
        "exceedance_proportion": round(float(exceedance_proportion), 4),
        "shapiro_wilk": {
            "statistic": round(float(shapiro_stat), 4),
            "p_value": float(shapiro_p),
            "p_value_formatted": format_p_value(shapiro_p),
            "is_normal_at_5pct": bool(shapiro_p >= 0.05),
            "note": "Evaluated on N=5000 subsample per statistical standards" if n > 5000 else "Evaluated on full sample",
        },
        "dagostino_pearson": {
            "statistic": round(float(dag_stat), 4),
            "p_value": float(dag_p),
            "p_value_formatted": format_p_value(dag_p),
            "is_normal_at_5pct": bool(dag_p >= 0.05),
        },
        "monthly_summary": monthly_summary,
        "seasonal_summary": seasonal_summary,
        "manual_walkthrough": manual_walkthrough(temps, mean),
    }

    print("=== CORE STATISTICS ===")
    print(f"Sample size: {result['n_days']:,d} valid days (Missing: {missing_count}, Duplicates: {duplicate_count})")
    print(f"Mean = {result['mean']}°C (95% CI: {mean_ci}) | Median = {result['median_temp']}°C | Range = {result['range_c']}°C")
    print(f"IQR = {result['iqr']}°C (Q1: {result['q1']}°C, Q3: {result['q3']}°C)")
    print(f"Variance = {result['variance']} | Std Dev = {result['std_dev']}°C (95% CI: {std_ci})")
    print(f"Exceedance count (> {DEFAULT_THRESHOLD_C}°C): {exceedance_count:,d} / {n:,d} days ({exceedance_proportion*100:.2f}%)")
    print(f"Thermodynamic CV (Kelvin): {result['cv_kelvin_percent']}% | Celsius CV: {result['cv_percent']}% (see interval-scale warning)")
    print(f"Shapiro-Wilk p: {result['shapiro_wilk']['p_value_formatted']} (Normal at 5%: {result['shapiro_wilk']['is_normal_at_5pct']})")

    write_result("core_stats", result)
    return result


if __name__ == "__main__":
    main()
