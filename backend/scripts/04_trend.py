"""
04_trend.py
------------
OWNER: Person 6  (see assignments/PERSON6.md)
WRITES: results.json["trend"]
READS:  backend/data/dataset.csv

Performs linear regression of temperature against time, estimates long-term trend
expressed in °C per decade, computes residual diagnostics, separates statistical
vs. practical significance, and calculates comprehensive annual summaries.
"""

import numpy as np
import pandas as pd
from scipy import stats
from common import load_dataset, write_result

DEFAULT_THRESHOLD_C = 36.0


def compute_annual_summaries(df: pd.DataFrame, threshold_c: float = DEFAULT_THRESHOLD_C) -> list:
    """Computes year-by-year temperature statistics and heat-exceedance counts,

    clearly distinguishing complete calendar years from partial years.
    """
    df_copy = df.copy()
    df_copy["year"] = df_copy["date"].dt.year
    years = sorted(df_copy["year"].unique())

    summaries = []
    for y in years:
        y_df = df_copy[df_copy["year"] == y]
        y_temps = y_df["max_temp_c"].to_numpy()
        n_y = len(y_temps)
        exceed_y = int(np.sum(y_temps > threshold_c))
        rate_y = round(float(exceed_y / n_y), 4) if n_y > 0 else 0.0

        # Complete year check: 365 or 366 days (leap years)
        is_leap = (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)
        expected_days = 366 if is_leap else 365
        is_complete = bool(n_y >= expected_days)

        coverage_note = "complete calendar year" if is_complete else f"partial year ({n_y} days observed)"

        summaries.append({
            "year": int(y),
            "n_days": int(n_y),
            "is_complete_year": is_complete,
            "coverage_note": coverage_note,
            "mean_c": round(float(np.mean(y_temps)), 2),
            "min_c": round(float(np.min(y_temps)), 1),
            "max_c": round(float(np.max(y_temps)), 1),
            "exceedance_count": exceed_y,
            "exceedance_rate": rate_y,
        })
    return summaries


def main():
    df = load_dataset()
    temps = df["max_temp_c"].to_numpy()
    day_index = (df["date"] - df["date"].min()).dt.days.to_numpy()

    # 1. Full Record Daily Regression (1950 to present)
    reg = stats.linregress(day_index, temps)
    slope, intercept, r_value, p_value = reg.slope, reg.intercept, reg.rvalue, reg.pvalue
    r_squared = r_value ** 2

    predicted = intercept + slope * day_index
    residuals = temps - predicted

    # Randomness check: count sign changes in residuals
    signs = np.sign(residuals)
    signs = signs[signs != 0]
    sign_changes = np.sum(np.diff(signs) != 0)
    expected_changes = (len(signs) - 1) / 2
    residuals_pattern_ok = bool(sign_changes > expected_changes * 0.5)

    total_drift = slope * (day_index.max() - day_index.min())
    is_significant = bool(p_value < 0.05)

    # Conversion to °C per decade (365.25 days per calendar year)
    slope_per_decade = slope * 365.25 * 10
    slope_stderr = float(reg.stderr) if reg.stderr is not None else 0.0
    slope_stderr_decade = slope_stderr * 365.25 * 10

    slope_ci95 = [
        round(float(slope - 1.96 * slope_stderr), 6),
        round(float(slope + 1.96 * slope_stderr), 6)
    ]
    slope_ci95_decade = [
        round(float(slope_per_decade - 1.96 * slope_stderr_decade), 4),
        round(float(slope_per_decade + 1.96 * slope_stderr_decade), 4)
    ]

    p_val_formatted = f"< 0.0001 (approx {p_value:.2e})" if p_value < 1e-4 else f"{p_value:.4f}"

    # 2. Complete Calendar Years Analysis (1950 - 2025)
    # Critical statistical correction: 2026 is incomplete (ends Oct 10), omitting cold winter months.
    # Annual mean regression on complete years avoids seasonal truncation bias and daily autocorrelation inflating df.
    df_complete = df[df["date"].dt.year < 2026].copy()
    annual_means = df_complete.groupby(df_complete["date"].dt.year)["max_temp_c"].mean()
    years_arr = annual_means.index.to_numpy()
    means_arr = annual_means.to_numpy()

    reg_annual = stats.linregress(years_arr, means_arr)
    annual_slope_per_decade = reg_annual.slope * 10.0
    annual_stderr_decade = reg_annual.stderr * 10.0
    annual_p_val = reg_annual.pvalue
    annual_ci95_decade = [
        round(float(annual_slope_per_decade - 1.96 * annual_stderr_decade), 4),
        round(float(annual_slope_per_decade + 1.96 * annual_stderr_decade), 4)
    ]
    annual_p_val_formatted = f"< 0.0001 (approx {annual_p_val:.2e})" if annual_p_val < 1e-4 else f"{annual_p_val:.4f}"

    complete_years_trend = {
        "period": f"{int(years_arr.min())}-{int(years_arr.max())} ({len(years_arr)} complete calendar years)",
        "n_years": int(len(years_arr)),
        "excluded_partial_year": "2026 (partial record through Oct 10, excluded from annual trend to prevent seasonal bias)",
        "slope_c_per_decade": round(float(annual_slope_per_decade), 4),
        "slope_stderr_per_decade": round(float(annual_stderr_decade), 4),
        "slope_ci95_per_decade": annual_ci95_decade,
        "intercept_c": round(float(reg_annual.intercept), 3),
        "r_value": round(float(reg_annual.rvalue), 4),
        "r_squared": round(float(reg_annual.rvalue ** 2), 4),
        "p_value": float(annual_p_val),
        "p_value_formatted": annual_p_val_formatted,
        "methodology": "OLS regression on annual mean daily maximum temperatures across complete calendar years only",
        "limitations_note": "While complete-year annual aggregation removes intra-annual seasonality and daily autocorrelation, annual means may still exhibit low-frequency inter-annual climatic persistence (e.g., ENSO, decadal oscillations); OLS inference should be interpreted with caution.",
    }

    if is_significant and abs(total_drift) < 1.0:
        practical_note = (
            f"Daily slope statistically significant (p={p_val_formatted}) but total drift "
            f"over the window is only {total_drift:+.2f} C - practically modest relative to annual variance. "
            f"Complete calendar years (1950-2025) annual trend is {annual_slope_per_decade:+.4f} C/decade (p={annual_p_val_formatted})."
        )
    elif is_significant:
        practical_note = (
            f"Slope statistically significant (p={p_val_formatted}) with total drift "
            f"of {total_drift:+.2f} C over the window - practically meaningful secular shift. "
            f"Complete calendar years (1950-2025) annual trend is {annual_slope_per_decade:+.4f} C/decade (p={annual_p_val_formatted})."
        )
    else:
        practical_note = (
            f"No statistically significant linear trend detected (p={p_val_formatted}); "
            "observed variation is consistent with natural noise around a stationary mean."
        )

    # Compute year-by-year annual summaries
    annual_summaries = compute_annual_summaries(df, DEFAULT_THRESHOLD_C)

    result = {
        "slope_c_per_day": round(float(slope), 6),
        "slope_c_per_decade": round(float(slope_per_decade), 4),
        "slope_stderr_per_decade": round(float(slope_stderr_decade), 4),
        "slope_ci95_per_decade": slope_ci95_decade,
        "slope_stderr": round(slope_stderr, 6),
        "slope_ci95": slope_ci95,
        "intercept_c": round(float(intercept), 3),
        "slope_p_value": float(p_value),
        "slope_p_value_formatted": p_val_formatted,
        "r_squared": round(float(r_squared), 6),
        "degrees_of_freedom": int(len(temps) - 2),
        "is_statistically_significant": is_significant,
        "total_drift_c": round(float(total_drift), 3),
        "practical_note": practical_note,
        "residuals_pattern_ok": residuals_pattern_ok,
        "residuals": [round(float(r), 3) for r in residuals],
        "day_index": [int(d) for d in day_index],
        "dates": df["date"].dt.strftime("%Y-%m-%d").tolist(),
        "daily_temperatures": [round(float(t), 1) for t in temps],
        "annual_summaries": annual_summaries,
        "complete_years_trend": complete_years_trend,
    }

    print("=== TREND ANALYSIS ===")
    print(f"Daily drift slope: {result['slope_c_per_decade']:+.4f} C/decade (95% CI: [{slope_ci95_decade[0]:+.4f}, {slope_ci95_decade[1]:+.4f}] C/decade)")
    print(f"Complete calendar years trend (1950-2025, N=76): {annual_slope_per_decade:+.4f} C/decade (p={annual_p_val_formatted}, 95% CI: [{annual_ci95_decade[0]:+.4f}, {annual_ci95_decade[1]:+.4f}] C/decade)")
    print(f"p-value: {p_val_formatted} | R^2: {result['r_squared']:.5f} | Total drift: {result['total_drift_c']:+.2f} C")
    print(f"Annual records evaluated: {len(annual_summaries)} years (from {annual_summaries[0]['year']} to {annual_summaries[-1]['year']})")
    print(f"2026 status: {annual_summaries[-1]['coverage_note']}")
    print(f"Practical note: {practical_note}")

    write_result("trend", result)
    return result


if __name__ == "__main__":
    main()
