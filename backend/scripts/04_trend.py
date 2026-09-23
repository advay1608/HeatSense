"""
04_trend.py
------------
OWNER: Person 6  (see assignments/PERSON6.md)
WRITES: results.json["trend"]
READS:  backend/data/dataset.csv only — no dependency on other sections.

Linear regression of temperature against time, with residual diagnostics
and an explicit separation of statistical vs. practical significance.
"""

import numpy as np
from scipy import stats
from common import load_dataset, write_result


def main():
    df = load_dataset()
    temps = df["max_temp_c"].to_numpy()
    day_index = (df["date"] - df["date"].min()).dt.days.to_numpy()

    reg = stats.linregress(day_index, temps)
    slope, intercept, r_value, p_value = reg.slope, reg.intercept, reg.rvalue, reg.pvalue
    r_squared = r_value ** 2

    predicted = intercept + slope * day_index
    residuals = temps - predicted

    # simple randomness check: count sign changes in residuals; too few
    # relative to n suggests a non-random (patterned) residual sequence
    signs = np.sign(residuals)
    signs = signs[signs != 0]
    sign_changes = np.sum(np.diff(signs) != 0)
    expected_changes = (len(signs) - 1) / 2
    residuals_pattern_ok = bool(sign_changes > expected_changes * 0.5)

    total_drift = slope * (day_index.max() - day_index.min())
    is_significant = bool(p_value < 0.05)

    if is_significant and abs(total_drift) < 1.0:
        practical_note = (
            f"Slope statistically significant (p={p_value:.3f}) but total drift "
            f"over the window is only {total_drift:.2f}C — practically small."
        )
    elif is_significant:
        practical_note = (
            f"Slope statistically significant (p={p_value:.3f}) with total drift "
            f"of {total_drift:.2f}C over the window — practically meaningful."
        )
    else:
        practical_note = (
            f"No statistically significant trend detected (p={p_value:.3f}); "
            f"observed variation is consistent with noise around a flat mean."
        )

    result = {
        "slope_c_per_day": round(float(slope), 4),
        "slope_p_value": round(float(p_value), 4),
        "r_squared": round(float(r_squared), 4),
        "is_statistically_significant": is_significant,
        "total_drift_c": round(float(total_drift), 3),
        "practical_note": practical_note,
        "residuals_pattern_ok": residuals_pattern_ok,
        "residuals": [round(float(r), 3) for r in residuals],
        "day_index": [int(d) for d in day_index],
    }

    print("=== TREND ANALYSIS ===")
    print(f"Slope: {result['slope_c_per_day']} C/day  (p={result['slope_p_value']}, "
          f"R^2={result['r_squared']})")
    print(f"Significant: {is_significant}")
    print(practical_note)

    write_result("trend", result)
    return result


if __name__ == "__main__":
    main()
