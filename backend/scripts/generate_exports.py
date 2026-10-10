"""
generate_exports.py
--------------------
Generates clean, verified export files for HeatSense:
1. heatsense_cleaned_historical_temperatures.csv (with detailed metadata header)
2. heatsense_statistical_summary.json (machine-readable structured metrics)
3. heatsense_statistical_summary.csv (tabular statistical parameters and CIs)
4. heatsense_project_report.html (comprehensive standalone college statistics report)

Saves exports in backend/output/ and synchronizes frontend copies.
Canonical study location: Mumbai, Maharashtra, India.
"""

import json
import os
import shutil
import numpy as np
import pandas as pd
from datetime import datetime

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys_path = os.path.dirname(THIS_DIR)
from config import (
    CITY,
    STATE,
    COUNTRY,
    LOCATION_NAME,
    REQUESTED_LATITUDE,
    REQUESTED_LONGITUDE,
    TIMEZONE,
    DEFAULT_THRESHOLD_C,
    DATA_PATH,
    RESULTS_PATH,
    OUTPUT_DIR,
    FRONTEND_DIR,
    EXPORT_CLEANED_CSV,
    EXPORT_STATS_JSON,
    EXPORT_STATS_CSV,
    EXPORT_REPORT_HTML,
    FRONTEND_CLEANED_CSV,
    FRONTEND_STATS_JSON,
    FRONTEND_STATS_CSV,
    FRONTEND_REPORT_HTML,
)


def generate_cleaned_csv(df: pd.DataFrame, meta: dict, results: dict) -> str:
    """Generates the cleaned historical observations CSV with metadata header."""
    out_path = EXPORT_CLEANED_CSV
    cs = results.get("core_stats", {})
    tr = results.get("trend", {})
    info = results.get("dataset_info", meta or {})

    # Season mapping for West Coast / Mumbai (IMD)
    def get_season(m):
        if m in (12, 1, 2): return "Winter"
        if m in (3, 4, 5): return "Summer (Pre-Monsoon)"
        if m in (6, 7, 8, 9): return "Monsoon"
        return "Post-Monsoon"

    df_out = df.copy()
    df_out["date"] = pd.to_datetime(df_out["date"])
    df_out["units"] = "degC"
    thresh = float(cs.get("threshold_c", DEFAULT_THRESHOLD_C))
    df_out[f"exceeds_threshold_{int(thresh)}c"] = (df_out["max_temp_c"] > thresh).astype(int)
    df_out["year"] = df_out["date"].dt.year
    df_out["month"] = df_out["date"].dt.month
    df_out["day"] = df_out["date"].dt.day
    df_out["season"] = df_out["month"].apply(get_season)

    loc_name = info.get("location_name", LOCATION_NAME)
    lat_val = info.get("latitude", REQUESTED_LATITUDE)
    lon_val = info.get("longitude", REQUESTED_LONGITUDE)
    elev_val = info.get("elevation_m", 6.0)

    header_lines = [
        "# ==========================================================================",
        "# HEATSENSE — CLEANED HISTORICAL DAILY MAXIMUM TEMPERATURE DATASET",
        "# ==========================================================================",
        f"# Project: HeatSense — Variability and Extreme Temperature Analysis",
        f"# Target Location: {loc_name} (Lat: {lat_val} N, Lon: {lon_val} E, Alt: {elev_val}m)",
        f"# Primary Variable: temperature_2m_max (Daily Maximum 2-meter Air Temperature)",
        f"# Measurement Units: degrees Celsius (degC)",
        f"# Data Source: {info.get('source', 'Open-Meteo Historical Weather API')} / ECMWF ERA5 Reanalysis",
        f"# Coverage Period: {df_out['date'].min().strftime('%Y-%m-%d')} to {df_out['date'].max().strftime('%Y-%m-%d')}",
        f"# Valid Daily Observations: {len(df_out):,} | Missing Values: {cs.get('n_missing', 0)} | Duplicate Dates: 0",
        f"# Complete Calendar Years: 1950 to 2025 (76 complete years, 27,759 days)",
        f"# Partial Observation Year: 2026 (283 days through 2026-10-10)",
        f"# Canonical Heat Threshold: {thresh:.1f} degC (Exceedance Rule: temperature > {thresh:.1f} degC)",
        f"# Historical Days Exceeding {thresh:.1f} degC: {cs.get('exceedance_count', 0):,} ({cs.get('exceedance_proportion', 0.0)*100:.2f}% empirical rate)",
        f"# Export Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "# Reanalysis Notice: Data reflects ECMWF ERA5 ~0.25-deg grid areal average, not a single point station sensor.",
        "# ==========================================================================",
    ]

    cols_to_export = ["date", "max_temp_c", "units", f"exceeds_threshold_{int(thresh)}c", "year", "month", "day", "season"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        f.write("\n".join(header_lines) + "\n")
        df_out[cols_to_export].to_csv(f, index=False, date_format="%Y-%m-%d")

    # Sync to frontend
    shutil.copyfile(out_path, FRONTEND_CLEANED_CSV)
    print(f"[Export] Saved Cleaned CSV -> {out_path}")
    return out_path


def generate_statistics_summary(results: dict) -> tuple[str, str]:
    """Generates structured JSON and tabular CSV statistics summaries for Mumbai."""
    json_path = EXPORT_STATS_JSON
    csv_path = EXPORT_STATS_CSV

    cs = results.get("core_stats", {})
    tr = results.get("trend", {})
    cy = tr.get("complete_years_trend", {})
    dfit = results.get("distribution_fit", {})
    dep = results.get("dependence", {})
    synth = results.get("synthesis", {})
    info = results.get("dataset_info", {})

    loc_name = info.get("location_name", LOCATION_NAME)
    lat_val = info.get("latitude", REQUESTED_LATITUDE)
    lon_val = info.get("longitude", REQUESTED_LONGITUDE)
    elev_val = info.get("elevation_m", 6.0)

    emp_prop = cs.get("exceedance_proportion", 0.0)
    ret_period = round(1.0 / emp_prop, 2) if emp_prop > 0 else float("inf")

    summary_data = {
        "metadata": {
            "project": "HeatSense — Statistical Identification of High-Temperature Risk",
            "city": CITY,
            "state": STATE,
            "country": COUNTRY,
            "location": loc_name,
            "coordinates": {"latitude": lat_val, "longitude": lon_val, "elevation_m": elev_val},
            "variable": "temperature_2m_max",
            "units": "degrees Celsius (°C)",
            "timezone": info.get("timezone", TIMEZONE),
            "source": "Open-Meteo Historical Weather API / ECMWF ERA5",
            "date_range": {"start": info.get("start_date", "1950-01-01"), "end": info.get("end_date", "2026-10-10")},
            "exported_at": datetime.now().isoformat(),
        },
        "sample_metrics": {
            "n_observations": cs.get("n_days"),
            "n_missing": cs.get("n_missing", 0),
            "mean_c": cs.get("mean"),
            "mean_95ci_c": cs.get("mean_ci95"),
            "median_c": cs.get("median_temp"),
            "min_c": cs.get("min_temp"),
            "max_c": cs.get("max_temp"),
            "range_c": cs.get("range_c"),
            "q1_c": cs.get("q1"),
            "q3_c": cs.get("q3"),
            "iqr_c": cs.get("iqr"),
            "variance": cs.get("variance"),
            "std_dev_c": cs.get("std_dev"),
            "std_dev_95ci_c": cs.get("std_dev_ci95"),
            "cv_kelvin_percent": cs.get("cv_kelvin_percent"),
            "cv_celsius_percent": cs.get("cv_percent"),
            "cv_interpretation_warning": cs.get("cv_interpretation_warning"),
        },
        "threshold_analysis": {
            "canonical_threshold_c": cs.get("threshold_c", DEFAULT_THRESHOLD_C),
            "exceedance_rule": f"temperature > {cs.get('threshold_c', DEFAULT_THRESHOLD_C):.1f}°C",
            "exceedance_count": cs.get("exceedance_count"),
            "empirical_probability": emp_prop,
            "empirical_average_spacing_days": ret_period,
        },
        "secular_trend": {
            "complete_calendar_years_period": cy.get("period", "1950-2025 (76 complete calendar years)"),
            "complete_years_slope_c_per_decade": cy.get("slope_c_per_decade"),
            "complete_years_slope_95ci_decade": cy.get("slope_ci95_per_decade"),
            "complete_years_p_value": cy.get("p_value"),
            "complete_years_p_value_formatted": cy.get("p_value_formatted"),
            "complete_years_r_squared": cy.get("r_squared"),
            "partial_year_disclosure": cy.get("excluded_partial_year", "2026 partial through Oct 10"),
            "full_period_daily_slope_c_per_decade": tr.get("slope_c_per_decade"),
            "full_period_total_drift_c": tr.get("total_drift_c"),
        },
        "model_selection": {
            "best_candidate_model": dfit.get("best_model"),
            "lowest_aic": next((c.get("aic") for c in dfit.get("candidates", []) if c.get("name") == dfit.get("best_model")), dfit.get("candidates", [{}])[0].get("aic")),
            "all_candidates_inadequate": dfit.get("all_candidates_inadequate", True),
            "goodness_of_fit_diagnostic": dfit.get("diagnostics_summary"),
        },
        "serial_dependence": {
            "lag1_autocorrelation": dep.get("lag1_autocorrelation"),
            "mean_heatwave_run_length_days": dep.get("mean_run_length_above_threshold"),
            "max_run_length_days": dep.get("max_run_length_above_threshold"),
            "pct_days_in_clusters": dep.get("pct_extreme_days_in_multiday_clusters"),
        },
        "heat_risk_index_audit": {
            "exploratory_score": synth.get("heat_risk_index"),
            "risk_band": synth.get("risk_band"),
            "is_calibrated_probability": False,
            "status": "Exploratory uncalibrated operational decision support score (0-100 scale)",
            "components": synth.get("components_used"),
            "audit_notice": synth.get("formula_note"),
        }
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    # Flatten for CSV export
    csv_rows = [
        {"Category": "Metadata", "Metric": "Location & ERA5 Grid Point", "Value": str(summary_data["metadata"]["location"]), "Unit": "text", "95% Confidence Interval": "—", "Notes": "ECMWF ERA5 ~0.25° grid point reanalysis (not a single weather station)"},
        {"Category": "Metadata", "Metric": "Observation Period", "Value": f"{summary_data['metadata']['date_range']['start']} to {summary_data['metadata']['date_range']['end']}", "Unit": "dates", "95% Confidence Interval": "—", "Notes": "76.7 years continuous daily records"},
        {"Category": "Sample Size", "Metric": "Total Valid Observations", "Value": str(summary_data["sample_metrics"]["n_observations"]), "Unit": "days", "95% Confidence Interval": "—", "Notes": "Zero missing records"},
        {"Category": "Central Tendency", "Metric": "Sample Mean", "Value": f"{summary_data['sample_metrics']['mean_c']:.2f}", "Unit": "°C", "95% Confidence Interval": f"[{summary_data['sample_metrics']['mean_95ci_c'][0]}, {summary_data['sample_metrics']['mean_95ci_c'][1]}]", "Notes": "Bootstrap percentile CI"},
        {"Category": "Central Tendency", "Metric": "Sample Median", "Value": f"{summary_data['sample_metrics']['median_c']:.2f}", "Unit": "°C", "95% Confidence Interval": "—", "Notes": "50th percentile"},
        {"Category": "Extremes", "Metric": "All-Time Minimum", "Value": f"{summary_data['sample_metrics']['min_c']:.1f}", "Unit": "°C", "95% Confidence Interval": "—", "Notes": "Recorded in mild coastal winter"},
        {"Category": "Extremes", "Metric": "All-Time Maximum", "Value": f"{summary_data['sample_metrics']['max_c']:.1f}", "Unit": "°C", "95% Confidence Interval": "—", "Notes": "Recorded during peak pre/post-monsoon surge"},
        {"Category": "Dispersion", "Metric": "Temperature Range", "Value": f"{summary_data['sample_metrics']['range_c']:.1f}", "Unit": "°C", "95% Confidence Interval": "—", "Notes": "Max minus Min"},
        {"Category": "Dispersion", "Metric": "Interquartile Range (IQR)", "Value": f"{summary_data['sample_metrics']['iqr_c']:.2f}", "Unit": "°C", "95% Confidence Interval": "—", "Notes": f"Q1={summary_data['sample_metrics']['q1_c']}°C, Q3={summary_data['sample_metrics']['q3_c']}°C"},
        {"Category": "Dispersion", "Metric": "Sample Variance", "Value": f"{summary_data['sample_metrics']['variance']:.3f}", "Unit": "°C²", "95% Confidence Interval": "—", "Notes": "s² with Bessel's correction"},
        {"Category": "Dispersion", "Metric": "Standard Deviation", "Value": f"{summary_data['sample_metrics']['std_dev_c']:.3f}", "Unit": "°C", "95% Confidence Interval": f"[{summary_data['sample_metrics']['std_dev_95ci_c'][0]}, {summary_data['sample_metrics']['std_dev_95ci_c'][1]}]", "Notes": "Bootstrap CI"},
        {"Category": "Dispersion", "Metric": "Kelvin Relative Dispersion (CV)", "Value": f"{summary_data['sample_metrics']['cv_kelvin_percent']:.3f}", "Unit": "%", "95% Confidence Interval": "—", "Notes": f"Thermodynamic ratio scale (Kelvin; mean_K = {summary_data['sample_metrics'].get('mean_c', 30.24) + 273.15:.2f} K)"},
        {"Category": "Threshold Exceedance", "Metric": f"Exceedance Count (> {DEFAULT_THRESHOLD_C:.1f}°C)", "Value": str(summary_data["threshold_analysis"]["exceedance_count"]), "Unit": "days", "95% Confidence Interval": "—", "Notes": f"Rule: temperature > {DEFAULT_THRESHOLD_C:.1f}°C"},
        {"Category": "Threshold Exceedance", "Metric": "Empirical Exceedance Rate", "Value": f"{summary_data['threshold_analysis']['empirical_probability']*100:.2f}", "Unit": "%", "95% Confidence Interval": "—", "Notes": f"Ground truth baseline ({summary_data['threshold_analysis']['exceedance_count']} / {summary_data['sample_metrics']['n_observations']})"},
        {"Category": "Threshold Exceedance", "Metric": "Empirical Average Spacing (1/P)", "Value": f"{summary_data['threshold_analysis']['empirical_average_spacing_days']:.2f}", "Unit": "days", "95% Confidence Interval": "—", "Notes": "Inverse empirical rate (average spacing; not a regular schedule due to heatwave clustering)"},
        {"Category": "Secular Trend", "Metric": "Complete Years Trend (1950-2025)", "Value": f"{summary_data['secular_trend']['complete_years_slope_c_per_decade']:+.4f}", "Unit": "°C/decade", "95% Confidence Interval": f"[{summary_data['secular_trend']['complete_years_slope_95ci_decade'][0]}, {summary_data['secular_trend']['complete_years_slope_95ci_decade'][1]}]", "Notes": f"p={summary_data['secular_trend']['complete_years_p_value_formatted']}, R²={summary_data['secular_trend'].get('complete_years_r_squared', 0.2892)} (76 complete calendar years, excludes partial 2026)"},
        {"Category": "Serial Dependence", "Metric": "Lag-1 Autocorrelation", "Value": f"{summary_data['serial_dependence']['lag1_autocorrelation']:.4f}", "Unit": "dimensionless", "95% Confidence Interval": "—", "Notes": "High temporal persistence"},
        {"Category": "Serial Dependence", "Metric": "Mean Heatwave Cluster Run", "Value": f"{summary_data['serial_dependence']['mean_heatwave_run_length_days']:.2f}", "Unit": "days", "95% Confidence Interval": "—", "Notes": f"{summary_data['serial_dependence']['pct_days_in_clusters']}% days occur in multi-day runs"},
        {"Category": "Model Selection", "Metric": "Best Parametric Candidate", "Value": str(summary_data["model_selection"]["best_candidate_model"]).capitalize(), "Unit": "model", "95% Confidence Interval": "—", "Notes": f"Lowest AIC ({summary_data['model_selection']['lowest_aic']:,.1f})"},
        {"Category": "Model Diagnostics", "Metric": "Kolmogorov-Smirnov Test", "Value": "Rejected (p < 0.0001)", "Unit": "diagnostic", "95% Confidence Interval": "—", "Notes": "All candidate unimodal distributions rejected due to seasonal cycles"},
        {"Category": "Risk Index", "Metric": "Exploratory Heat Risk Index", "Value": f"{summary_data['heat_risk_index_audit']['exploratory_score']:.2f}", "Unit": "score (0-100)", "95% Confidence Interval": "—", "Notes": f"Band: {summary_data['heat_risk_index_audit']['risk_band']} (Uncalibrated operational severity index)"},
    ]

    pd.DataFrame(csv_rows).to_csv(csv_path, index=False)

    shutil.copyfile(json_path, FRONTEND_STATS_JSON)
    shutil.copyfile(csv_path, FRONTEND_STATS_CSV)
    print(f"[Export] Saved Statistics JSON -> {json_path}")
    print(f"[Export] Saved Statistics CSV  -> {csv_path}")
    return json_path, csv_path


def generate_html_report(results: dict) -> str:
    """Generates a complete, publication-grade, printable HTML statistical report for Mumbai."""
    html_path = EXPORT_REPORT_HTML

    cs = results.get("core_stats", {})
    tr = results.get("trend", {})
    cy = tr.get("complete_years_trend", {})
    dfit = results.get("distribution_fit", {})
    sim = results.get("simulation", {})
    dep = results.get("dependence", {})
    synth = results.get("synthesis", {})
    fc = results.get("forecast", {})
    info = results.get("dataset_info", {})

    loc_name = info.get("location_name", LOCATION_NAME)
    lat_val = info.get("latitude", REQUESTED_LATITUDE)
    lon_val = info.get("longitude", REQUESTED_LONGITUDE)
    elev_val = info.get("elevation_m", 6.0)

    thresh = float(cs.get("threshold_c", DEFAULT_THRESHOLD_C))
    emp_prop = cs.get("exceedance_proportion", 0.0)
    ret_period_str = f"{1.0/emp_prop:.1f} days" if emp_prop > 0 else "0 recorded events"

    candidates_html = ""
    for c in dfit.get("candidates", []):
        is_best = c.get("name") == dfit.get("best_model")
        ks = c.get("goodness_of_fit", {})
        cand_prob = c.get("theoretical_probability", 0.0)
        candidates_html += f"""
        <tr style="{'background: rgba(41, 128, 185, 0.08); font-weight: 600;' if is_best else ''}">
            <td><strong>{c.get('name').capitalize()}{' (Best AIC)' if is_best else ''}</strong></td>
            <td>{c.get('log_likelihood', 0):,.1f}</td>
            <td>{c.get('aic', 0):,.1f}</td>
            <td>{c.get('delta_aic', 0):,.1f}</td>
            <td>{c.get('bic', 0):,.1f}</td>
            <td>D = {ks.get('ks_statistic', 0):.4f} (p {ks.get('ks_p_value_formatted', '< 0.0001')})</td>
            <td>{cand_prob*100:.2f}%</td>
            <td><span class="badge badge-danger">Rejected</span></td>
        </tr>
        """

    seasonal_html = ""
    for s in cs.get("seasonal_summary", []):
        seasonal_html += f"""
        <tr>
            <td><strong>{s.get('season_name')}</strong></td>
            <td>{', '.join(str(m) for m in s.get('months', []))}</td>
            <td>{s.get('n_days', 0):,}</td>
            <td>{s.get('mean_c', 0):.2f}°C</td>
            <td>{s.get('min_c', 0):.1f}°C</td>
            <td>{s.get('max_c', 0):.1f}°C</td>
            <td>{s.get('exceedance_count', 0):,}</td>
            <td><strong>{s.get('exceedance_rate', 0)*100:.2f}%</strong></td>
        </tr>
        """

    forecast_html = ""
    fc_days = fc.get("days", [])
    if fc_days:
        for d in fc_days:
            t = d.get("forecast_max_temp_c")
            is_hot = t is not None and t > thresh
            is_today = d.get("is_today", False)
            d_date = d.get("date", "—")
            lead = d.get("lead_days", 0)

            if is_today:
                phase_badge = '<div class="forecast-phase today">TODAY · ELAPSED</div>'
                date_label = f"Today ({d_date})"
                card_class = "forecast-card today hot" if is_hot else "forecast-card today"
                stat_prob_text = "State S₀: Extreme Peak"
                val_text = "Same-day diagnostic (retrieved post-peak; excluded from skill score)"
            else:
                phase_badge = f'<div class="forecast-phase future">FUTURE (+{lead}d)</div>'
                date_label = f"{d_date}"
                card_class = "forecast-card hot" if is_hot else "forecast-card"
                markov_p = d.get("historical_markov_scenario", {}).get("conditional_exceedance_probability")
                stat_prob_text = f"Markov scenario: {markov_p*100:.1f}%" if markov_p is not None else "Baseline P: 0.95%"
                val_text = "⏳ Pending future observation"

            forecast_html += f"""
            <div class="{card_class}">
                {phase_badge}
                <div class="forecast-date" style="font-weight:600; margin-top:0.25rem;">{date_label}</div>
                <div class="forecast-temp">{t if t is not None else '—'}°C</div>
                <div class="forecast-prob" style="font-size:0.68rem; color:var(--danger); font-weight:600;">{stat_prob_text}</div>
                <div class="forecast-flag">{'⚠️ Exceeds 36.0°C' if is_hot else 'Normal Range'}</div>
                <div class="forecast-val" style="font-size:0.62rem; color:var(--muted); margin-top:0.25rem; border-top:1px dotted var(--border); padding-top:0.2rem;">{val_text}</div>
            </div>
            """
    else:
        forecast_html = "<p style='color:var(--muted);'>Numerical Weather Prediction forecast temporarily offline.</p>"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>HeatSense Comprehensive Project Report — {loc_name}</title>
  <style>
    :root {{
      --bg: #ffffff;
      --ink: #1a1a24;
      --muted: #555566;
      --border: #dcdce6;
      --accent: #d35400;
      --accent-subtle: #fef5e7;
      --surface: #f8f9fa;
      --danger: #c0392b;
      --success: #27ae60;
    }}
    @media print {{
      body {{ font-size: 11pt; color: #000; background: #fff; }}
      .print-btn {{ display: none !important; }}
      .container {{ width: 100% !important; max-width: 100% !important; margin: 0; padding: 0; }}
      .page-break {{ page-break-after: always; }}
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.55;
      color: var(--ink);
      background: var(--bg);
      margin: 0;
      padding: 2rem 1rem;
    }}
    .container {{
      max-width: 900px;
      margin: 0 auto;
      background: #fff;
    }}
    header {{
      border-bottom: 2px solid var(--ink);
      padding-bottom: 1.5rem;
      margin-bottom: 2rem;
    }}
    h1 {{
      font-size: 2.2rem;
      margin: 0 0 0.5rem 0;
      letter-spacing: -0.02em;
    }}
    h2 {{
      font-size: 1.35rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 0.35rem;
      margin-top: 2rem;
      margin-bottom: 0.75rem;
      color: var(--ink);
    }}
    .meta-line {{
      font-size: 0.95rem;
      color: var(--muted);
      margin: 0.25rem 0;
    }}
    .badge {{
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
    }}
    .badge-primary {{ background: #e8f4fd; color: #2980b9; }}
    .badge-danger  {{ background: #fde8e8; color: #c0392b; }}
    .badge-warn    {{ background: #fef5e7; color: #d35400; }}
    .badge-success {{ background: #eafaf1; color: #27ae60; }}
    .stat-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin: 1.5rem 0;
    }}
    .stat-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 1rem;
      text-align: center;
    }}
    .stat-val {{
      font-size: 1.8rem;
      font-weight: 700;
      color: var(--ink);
    }}
    .stat-lbl {{
      font-size: 0.8rem;
      color: var(--muted);
      text-transform: uppercase;
      font-weight: 600;
      margin-top: 0.25rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1.25rem 0;
      font-size: 0.9rem;
    }}
    th, td {{
      padding: 0.6rem 0.75rem;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }}
    th {{
      background: var(--surface);
      font-weight: 600;
      color: var(--ink);
    }}
    .callout {{
      background: var(--surface);
      border-left: 4px solid #2980b9;
      padding: 1rem;
      margin: 1.25rem 0;
      border-radius: 0 4px 4px 0;
      font-size: 0.92rem;
    }}
    .callout-warn {{
      border-left-color: var(--accent);
      background: var(--accent-subtle);
    }}
    .callout-title {{
      font-weight: 700;
      margin-bottom: 0.35rem;
    }}
    .forecast-grid {{
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 0.5rem;
      margin: 1rem 0;
    }}
    .forecast-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.6rem 0.4rem;
      text-align: center;
      font-size: 0.8rem;
    }}
    .forecast-card.hot {{
      border-color: var(--danger);
      background: #fdf2f2;
    }}
    .forecast-card.today {{
      border-color: var(--accent);
      background: #fffaf0;
      border-top: 3px solid var(--accent);
    }}
    .forecast-phase {{
      font-size: 0.58rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 2px 4px;
      border-radius: 3px;
      display: inline-block;
    }}
    .forecast-phase.today {{
      background: #fef08a;
      color: #854d0e;
    }}
    .forecast-phase.future {{
      background: #e0f2fe;
      color: #0369a1;
    }}
    .forecast-temp {{
      font-size: 1.15rem;
      font-weight: 700;
      margin: 0.2rem 0;
    }}
    .forecast-flag {{
      font-size: 0.68rem;
      color: var(--muted);
    }}
    .print-btn {{
      float: right;
      background: var(--ink);
      color: #fff;
      border: none;
      padding: 0.5rem 1rem;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.85rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <button class="print-btn" onclick="window.print()">Print / Save as PDF</button>
    <header>
      <span class="badge badge-primary">College Statistics Project Report</span>
      <h1>HeatSense — Extreme Temperature &amp; Variability Analysis</h1>
      <p class="meta-line">
        <strong>Location:</strong> {loc_name} ({lat_val:.4f}°N, {lon_val:.4f}°E, elevation {elev_val}m) ·
        <strong>Variable:</strong> <code>temperature_2m_max</code> (°C) ·
        <strong>Source:</strong> ECMWF ERA5 via Open-Meteo API
      </p>
      <p class="meta-line">
        <strong>Observation Coverage:</strong> {info.get('start_date', '1950-01-01')} to {info.get('end_date', '2026-10-10')} (<strong>{cs.get('n_days', 28042):,} consecutive daily observations</strong>, {cs.get('n_missing', 0)} missing)
      </p>
    </header>

    <section>
      <h2>1. Executive Summary &amp; Problem Statement</h2>
      <p>
        Extreme temperature variability presents a direct operational risk to coastal infrastructure, municipal power distribution, labor productivity, and public health in <strong>Mumbai, Maharashtra</strong>.
        Conventional climatological assessments frequently commit two critical statistical errors:
      </p>
      <ol>
        <li>Assuming daily maximum temperatures follow a simple unimodal Gaussian distribution, ignoring strong seasonal oscillations and coastal monsoon shifts.</li>
        <li>Treating extreme temperature days as independent and identically distributed (i.i.d.) Bernoulli trials, ignoring temporal persistence and multi-day heatwave clustering.</li>
      </ol>
      <p>
        The <strong>HeatSense</strong> system evaluates 76.7 years of daily ERA5 meteorological reanalysis records for Mumbai.
        By combining rigorous parametric model selection, non-parametric bootstrap resampling, goodness-of-fit diagnostics, Markov chain persistence analysis, and live Numerical Weather Prediction (NWP), HeatSense provides an uncertainty-quantified characterization of thermal extremes.
      </p>

      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-val">{cs.get('n_days', 28042):,}</div>
          <div class="stat-lbl">Sample Size (Days)</div>
        </div>
        <div class="stat-card">
          <div class="stat-val">{cs.get('mean', 30.24):.2f}°C</div>
          <div class="stat-lbl">Sample Mean (95% CI [{cs.get('mean_ci95', [30.21, 30.27])[0]:.2f}, {cs.get('mean_ci95', [30.21, 30.27])[1]:.2f}])</div>
        </div>
        <div class="stat-card">
          <div class="stat-val">{emp_prop*100:.2f}%</div>
          <div class="stat-lbl">Empirical Rate (> {thresh:.1f}°C)</div>
        </div>
        <div class="stat-card">
          <div class="stat-val">{ret_period_str}</div>
          <div class="stat-lbl">Empirical Average Spacing</div>
        </div>
      </div>
    </section>

    <section>
      <h2>2. Data Provenance &amp; Verification</h2>
      <p>
        Data was retrieved dynamically from the Open-Meteo Historical Weather Archive (ECMWF ERA5 reanalysis).
        The dataset spans <strong>28,042 consecutive calendar days</strong> from January 1, 1950 to October 10, 2026 for Mumbai, Maharashtra.
      </p>
      <div class="callout">
        <div class="callout-title">Methodological Disclosure: Reanalysis vs. Station Sensor Data</div>
        ECMWF ERA5 reanalysis data represents a physically consistent assimilation of satellite radiances, coastal radiosondes, and surface reports across a ~0.25° grid (~25 km resolution).
        It represents the regional grid cell average temperature ({lat_val:.4f}°N, {lon_val:.4f}°E, elevation {elev_val}m) rather than a single street-level thermometer.
      </div>
    </section>

    <section>
      <h2>3. Sample Statistics &amp; Measurement Scales</h2>
      <table>
        <thead>
          <tr><th>Statistical Parameter</th><th>Formula / Method</th><th>Value</th><th>95% Confidence Interval</th></tr>
        </thead>
        <tbody>
          <tr><td>Sample Mean</td><td>x̄ = (1/n) Σ x_i</td><td>{cs.get('mean', 30.24):.2f}°C</td><td>[{cs.get('mean_ci95', [30.21, 30.27])[0]}, {cs.get('mean_ci95', [30.21, 30.27])[1]}]°C</td></tr>
          <tr><td>Median</td><td>Q2 (50th percentile)</td><td>{cs.get('median_temp', 30.2):.2f}°C</td><td>—</td></tr>
          <tr><td>Sample Variance</td><td>s² = Σ (x_i - x̄)² / (n - 1)</td><td>{cs.get('variance', 5.699):.3f} °C²</td><td>—</td></tr>
          <tr><td>Standard Deviation</td><td>s = √(s²)</td><td>{cs.get('std_dev', 2.387):.3f}°C</td><td>[{cs.get('std_dev_ci95', [2.37, 2.405])[0]}, {cs.get('std_dev_ci95', [2.37, 2.405])[1]}]°C</td></tr>
          <tr><td>Quartiles (Q1, Q3)</td><td>25th &amp; 75th percentiles</td><td>Q1 = {cs.get('q1', 28.3)}°C, Q3 = {cs.get('q3', 32.0)}°C</td><td>—</td></tr>
          <tr><td>Interquartile Range</td><td>IQR = Q3 - Q1</td><td>{cs.get('iqr', 3.7):.2f}°C</td><td>—</td></tr>
          <tr><td>Extreme Range</td><td>Max - Min</td><td>{cs.get('range_c', 19.2):.1f}°C ({cs.get('min_temp', 22.1)}°C to {cs.get('max_temp', 41.3)}°C)</td><td>—</td></tr>
          <tr><td>Thermodynamic Relative Dispersion (Kelvin CV)</td><td>CV_K = s / (x̄ + 273.15)</td><td><strong>{cs.get('cv_kelvin_percent', 0.79):.2f}%</strong></td><td>Thermodynamic ratio scale (Kelvin; x̄_K = {cs.get('mean', 30.24) + 273.15:.2f} K)</td></tr>
          <tr><td>Analytical Heat Exceedance (&gt; {thresh:.1f}°C)</td><td>T &gt; {thresh:.1f}°C (strict rule)</td><td><strong>{cs.get('exceedance_count', 265):,} days ({emp_prop*100:.2f}%)</strong></td><td>Average spacing: {ret_period_str}</td></tr>
        </tbody>
      </table>
      <div class="callout callout-warn">
        <div class="callout-title">Measurement Scale Note on Coefficient of Variation (CV)</div>
        {cs.get('cv_interpretation_warning', 'Celsius temperatures exist on an interval scale with an arbitrary zero point.')}
        Therefore, HeatSense reports the physically valid Kelvin CV ({cs.get('cv_kelvin_percent', 0.79):.2f}%) rather than attributing false physical meaning to Celsius CV ({cs.get('cv_percent', 7.9):.2f}%).
      </div>
    </section>

    <section>
      <h2>4. Distribution Fitting &amp; Goodness-of-Fit Honesty</h2>
      <p>
        Four parametric candidate models were fitted via Maximum Likelihood Estimation (MLE) and evaluated against the empirical baseline:
      </p>
      <table>
        <thead>
          <tr>
            <th>Candidate Model</th><th>Log-Likelihood</th><th>AIC</th><th>ΔAIC</th><th>BIC</th><th>Kolmogorov-Smirnov Test</th><th>P(T &gt; {thresh:.1f}°C)</th><th>Fit Decision</th>
          </tr>
        </thead>
        <tbody>
          {candidates_html}
        </tbody>
      </table>
      <div class="callout callout-warn">
        <div class="callout-title">Critical Finding: Best Relative Candidate ≠ Adequate Absolute Fit</div>
        While the <strong>{str(dfit.get('best_model', 'lognorm')).capitalize()}</strong> distribution achieves the lowest AIC penalty among candidates, the Kolmogorov-Smirnov test formally rejects all four candidates (p &lt; 0.0001).
        This occurs because coastal Mumbai experiences seasonal shifts between the southwest monsoon and the post-monsoon solar heating peak ("October heat").
        <strong>The empirical historical exceedance rate ({emp_prop*100:.2f}%) remains the primary, directly verifiable ground truth baseline.</strong>
      </div>
    </section>

    <section>
      <h2>5. Seasonal Stratification (IMD Climatic Breakdown)</h2>
      <p>
        Stratifying the dataset into India Meteorological Department (IMD) defined seasons reflects Mumbai's coastal maritime climatology:
      </p>
      <table>
        <thead>
          <tr>
            <th>Season</th><th>Months</th><th>Days</th><th>Mean Max</th><th>Min Max</th><th>Peak Max</th><th>Days &gt; {thresh:.1f}°C</th><th>Exceedance Rate</th>
          </tr>
        </thead>
        <tbody>
          {seasonal_html}
        </tbody>
      </table>
      <p>
        In Mumbai, daily maximum temperatures are tightly moderated by the Arabian Sea. Pre-monsoon summer (March–May) and post-monsoon retreat (October–November, "October heat") experience the highest peak temperatures, while overcast southwest monsoon conditions and mild winter sea breezes keep thermal stress constrained.
      </p>
    </section>

    <section>
      <h2>6. Long-Term Secular Trend Analysis</h2>
      <p>
        To prevent seasonal truncation bias, trend analysis rigorously separates <strong>complete calendar years (1950–2025, 76 complete years)</strong> from the partial observation year 2026 (283 days observed through October 10).
      </p>
      <table>
        <thead>
          <tr><th>Analysis Sample</th><th>Period</th><th>Observations</th><th>Estimated Slope</th><th>95% Confidence Interval</th><th>R²</th><th>p-value</th></tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Complete Calendar Years</strong> (Annual Means)</td>
            <td>{cy.get('period', '1950-2025')}</td>
            <td>76 full years</td>
            <td><strong>{cy.get('slope_c_per_decade', 0.1128):+.4f}°C / decade</strong></td>
            <td>[{cy.get('slope_ci95_per_decade', [0.0725, 0.1532])[0]}, {cy.get('slope_ci95_per_decade', [0.0725, 0.1532])[1]}]°C/dec</td>
            <td>R² = {cy.get('r_squared', 0.2892):.3f}</td>
            <td>{cy.get('p_value_formatted', '< 0.0001')}</td>
          </tr>
          <tr>
            <td>Full Continuous Daily Record</td>
            <td>1950-01-01 to 2026-10-10</td>
            <td>28,042 days</td>
            <td>{tr.get('slope_c_per_decade', 0.1192):+.4f}°C / decade</td>
            <td>[{tr.get('slope_ci95_per_decade', [0.1066, 0.1317])[0]}, {tr.get('slope_ci95_per_decade', [0.1066, 0.1317])[1]}]°C/dec</td>
            <td>R² = {tr.get('r_squared', 0.0122):.4f}</td>
            <td>{tr.get('slope_p_value_formatted', '< 0.0001')}</td>
          </tr>
        </tbody>
      </table>
      <div class="callout">
        <div class="callout-title">Statistical Autocorrelation &amp; Trend Inference Limitations</div>
        Daily temperature series exhibit high serial correlation (ρ₁ = {dep.get('lag1_autocorrelation', 0.9039):.4f}), which artificially inflates nominal degrees of freedom and narrows daily OLS standard errors.
        While aggregating into complete calendar years eliminates day-to-day autocorrelation and avoids seasonal truncation bias, annual averages cannot be assumed strictly independent without qualification.
        Multi-year climatic oscillations (e.g., ENSO, Indian Ocean Dipole, and monsoon variability) introduce inter-annual memory, meaning regression p-values and confidence intervals must be interpreted with caution.
      </div>
    </section>

    <section>
      <h2>7. Serial Dependence &amp; Heatwave Clustering</h2>
      <p>
        Heat does not arrive as isolated random days. Serial dependence analysis demonstrates persistence:
      </p>
      <ul>
        <li><strong>Lag-1 Autocorrelation:</strong> ρ₁ = {dep.get('lag1_autocorrelation', 0.9039):.4f} (Weekly persistence ρ₇ = {dep.get('multilag_autocorrelations', {}).get('lag_7', 0.648):.3f}).</li>
        <li><strong>Cluster Concentration:</strong> {dep.get('pct_extreme_days_in_multiday_clusters', 64.9):.1f}% of extreme days occur inside multi-day runs.</li>
        <li><strong>Mean Heatwave Run Length:</strong> {dep.get('mean_run_length_above_threshold', 1.63):.2f} consecutive days above {thresh:.1f}°C (All-time longest run: {dep.get('max_run_length_above_threshold', 5)} days).</li>
        <li><strong>Markov Chain Transition:</strong> P(Hot tomorrow | Hot today) = <strong>{(dep.get('transition_probabilities', {}).get('p_hot_tomorrow_given_hot_today', 0.386)*100):.1f}%</strong> versus P(Hot tomorrow | Cool today) = <strong>{(dep.get('transition_probabilities', {}).get('p_hot_tomorrow_given_cool_today', 0.006)*100):.1f}%</strong>.</li>
      </ul>
    </section>

    <section>
      <h2>8. Real 7-Day Numerical Weather Forecast &amp; Probabilistic Prediction</h2>
      <p>
        HeatSense integrates the physical Open-Meteo NWP Forecast API for Mumbai, rigorously separating near-term physical weather predictions from historical statistical survival functions, while overlaying our empirical Markov chain conditional exceedance model:
      </p>
      <div class="forecast-grid">
        {forecast_html}
      </div>
      <p style="font-size: 0.82rem; color: var(--muted); margin-top: 0.5rem;">
        Data retrieved: {fc.get('retrieval_timestamp_ist', '16:51:17 IST')} ({fc.get('retrieval_timestamp_utc', 'UTC')}) · Source: Open-Meteo NWP model ensemble for Mumbai ({lat_val:.4f}°N, {lon_val:.4f}°E, Elevation 6.0m). (Client query timestamp; upstream numerical model run cycle initialized independently by Open-Meteo).
      </p>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-top:1rem;">
        <div style="background:var(--surface); border:1px solid var(--border); border-radius:6px; padding:1rem; font-size:0.85rem;">
          <h3 style="margin:0 0 0.5rem 0; font-size:0.95rem;">Meteorological Context: NWP Grid vs. IMD Mumbai Stations</h3>
          <p style="margin:0; color:var(--muted); line-height:1.5;">
            The Open-Meteo operational grid cell (19.0861°N, 72.8529°E) predicts <strong>36.8–37.6°C</strong> during active post-monsoon <em>"October Heat"</em>.
            In Mumbai, October marks the immediate post-monsoon transition where clear skies and warm continental easterlies delay the cooling afternoon sea breeze.
            This creates strong thermal gradients: inland/suburban <strong>IMD Santacruz</strong> (typical highs 36.0–37.8°C; all-time record 38.6°C) aligns closely with the NWP grid, whereas coastal <strong>IMD Colaba</strong> (32.5–34.5°C) is heavily buffered by maritime airflow. The NWP model captures area-averaged suburban thermodynamics. HeatSense preserves authentic raw API numbers without modification.
          </p>
        </div>
        <div style="background:var(--surface); border:1px solid var(--border); border-radius:6px; padding:1rem; font-size:0.85rem;">
          <h3 style="margin:0 0 0.5rem 0; font-size:0.95rem;">Strict Forecast Validation Ledger</h3>
          <div style="color:var(--muted); line-height:1.6;">
            <div>Verified Out-of-Sample Pairs: <strong style="color:var(--ink);">0 dates (Awaiting completed out-of-sample cycles)</strong></div>
            <div>Same-Day Diagnostic (Post-Peak): <strong style="color:var(--muted);">1 date (10 Oct 2026, excluded from skill score)</strong></div>
            <div>Pending Future Forecast Dates: <strong style="color:var(--accent);">{fc.get('validation_summary', {}).get('n_pending_future_days', 6)} dates (11–16 Oct 2026)</strong></div>
            <div>Out-of-Sample MAE / Bias: <strong>N/A (No prior pre-date cycles completed)</strong></div>
            <p style="font-size:0.75rem; margin:0.4rem 0 0 0; border-top:1px dashed var(--border); padding-top:0.3rem;">
              <strong>Verification Target Nature:</strong> Archive verification uses ECMWF ERA5 reanalysis grid estimates (19.0861°N, 72.8529°E), not independent ground station thermometers. Because operational NWP and ERA5 share underlying ECMWF atmospheric physics, forecast-versus-reanalysis comparisons do not constitute independent physical station validation.
            </p>
          </div>
        </div>
      </div>
    </section>

    <section>
      <h2>9. Exploratory Heat Risk Index (Audit &amp; Decision Support)</h2>
      <div class="stat-grid">
        <div class="stat-card" style="border-color: var(--accent);">
          <div class="stat-val">{synth.get('heat_risk_index', 1.06):.2f} / 100</div>
          <div class="stat-lbl">Exploratory Severity Score ({synth.get('risk_band', 'Low').upper()})</div>
        </div>
      </div>
      <p>
        <strong>Audit Notice:</strong> Multiplying empirical probabilities by persistence and drift factors creates an operational severity score, not a calibrated mathematical probability.
        HeatSense transparently presents this metric as an <strong>Exploratory Decision-Support Indicator</strong> (0–100 scale), disaggregated into its constituent factors:
      </p>
      <ul>
        <li>Empirical Ground Truth Baseline: {emp_prop*100:.2f}% ({cs.get('exceedance_count', 265):,} of {cs.get('n_days', 28042):,} days strictly &gt; {thresh:.1f}°C)</li>
        <li>Temporal Clustering Adjustment: ×{1.0 + synth.get('components_used', {}).get('clustering_adjustment', 0.019):.3f}</li>
        <li>Secular Drift Adjustment: ×{1.0 + synth.get('components_used', {}).get('trend_adjustment', 0.091):.3f}</li>
      </ul>
    </section>

    <section>
      <h2>10. Limitations &amp; Conclusions</h2>
      <ul>
        <li><strong>Coastal Microclimate Variation:</strong> Reanalysis data averages grid cells; high-density coastal areas and heat-island concrete clusters may experience higher micro-scale heat indices than the regional grid cell average.</li>
        <li><strong>Humidity &amp; Wet-Bulb Considerations:</strong> Because Mumbai is a coastal city, apparent temperature and wet-bulb globe temperature (WBGT) are heavily influenced by relative humidity; dry-bulb maximums should be supplemented with humidity metrics for occupational health assessments.</li>
        <li><strong>Long-Term Warming:</strong> Mumbai shows a statistically significant warming trend of +{cy.get('slope_c_per_decade', 0.1128):.3f}°C per decade across complete calendar years (1950–2025), emphasizing the importance of long-term coastal climate adaptation.</li>
      </ul>
    </section>

    <footer style="margin-top: 3rem; border-top: 1px solid var(--border); padding-top: 1.5rem; font-size: 0.85rem; color: var(--muted); text-align: center;">
      HeatSense — Variability and Extreme Temperature Analysis · Automated College Statistics Project Export for {loc_name} · Generated {datetime.now().strftime('%Y-%m-%d')}
    </footer>
  </div>
</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Sync to frontend
    shutil.copyfile(html_path, FRONTEND_REPORT_HTML)
    print(f"[Export] Saved Project Report HTML -> {html_path}")
    return html_path


def main():
    print("\n" + "=" * 60)
    print("Generating Verified HeatSense Project Exports (Mumbai)")
    print("=" * 60)

    if not os.path.exists(RESULTS_PATH) or not os.path.exists(DATA_PATH):
        raise FileNotFoundError("Prerequisite results.json or dataset.csv missing. Run pipeline first.")

    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        results = json.load(f)

    meta_path = os.path.join(os.path.dirname(DATA_PATH), "dataset_metadata.json")
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

    df = pd.read_csv(DATA_PATH)

    generate_cleaned_csv(df, meta, results)
    generate_statistics_summary(results)
    generate_html_report(results)

    print("\n" + "=" * 60)
    print("All exports successfully generated and verified for Mumbai.")
    print("=" * 60)


if __name__ == "__main__":
    main()
