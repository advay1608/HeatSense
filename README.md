# HeatSense — Variability and Extreme Temperature Analysis

**College Statistics & Applied Probability Project**  
An empirical statistical engine and interactive dark-themed decision dashboard for quantifying urban extreme heat risk in **Mumbai, Maharashtra, India**, using **over 76 years of validated daily meteorological records (1950–2026, 28,042 observations)**.

---

## 1. Project Overview

HeatSense models high-temperature exceedance risk without making unverified statistical assumptions. The project:
- **Analyzes 28,042 real daily observations** from the Open-Meteo Historical Weather API (ECMWF ERA5 atmospheric reanalysis grid point for Mumbai: $19.0861^\circ\text{N}, 72.8529^\circ\text{E}$, elevation $6.0\text{ m}$).
- **Centralizes canonical location configuration**: unified coordinates ($19.0760^\circ\text{N}, 72.8777^\circ\text{E}$ requested reference point), timezone (`Asia/Kolkata`), analytical threshold ($36.0^\circ\text{C}$), and strict cache validation.
- **Quantifies dispersion on valid physical scales**: reports thermodynamic Kelvin CV ($0.79\%$) and discloses why Celsius CV ($7.89\%$) is interval-dependent.
- **Evaluates 4 parametric candidate distributions**: Log-Normal, Gamma, Normal, and Gumbel via MLE and AIC/BIC model selection (Log-Normal ranked #1 with AIC $128,123.52$).
- **Demonstrates goodness-of-fit honesty**: conducts Kolmogorov-Smirnov tests proving that all candidate unimodal models fail ($p < 0.0001$) due to coastal Arabian Sea monsoon seasonality and bimodal "October heat" surges, establishing the **Empirical Exceedance Rate ($0.95\%$ at $36.0^\circ\text{C}$, 265 days)** as the primary ground truth.
- **Stratifies by IMD climatic seasons**: demonstrates coastal Konkan thermal dynamics (hot pre-monsoon and post-monsoon peaks vs. monsoon cloud/rain depression).
- **Rigorously analyzes secular trend**: calculates decadal drift on **complete calendar years (1950–2025, 76 full years: $+0.1128^\circ\text{C}/\text{decade}$, $p < 0.0001$)**, preventing seasonal truncation bias from partial year 2026.
- **Measures temporal persistence**: documents high lag-1 autocorrelation ($\rho_1 = 0.9039$) with $64.9\%$ of extreme days occurring in heatwaves averaging $1.63$ consecutive days (max run: $5$ days; Markov transition $P(\text{Hot}\mid\text{Hot}) = 38.6\%$).
- **Integrates real 7-day NWP physical weather forecasts**: consumes live Mumbai forecasts directly from Open-Meteo ($19.0760^\circ\text{N}, 72.8777^\circ\text{E}$), strictly separating physical forecasting from historical statistical survival models.
- **Audits the Heat Risk Index**: clearly labels the composite index as an **Exploratory, Uncalibrated Operational Severity Indicator (Score: 1.06 / 100, Low Band)** rather than a false calibrated probability.
- **Generates verifiable exports**: provides downloadable cleaned historical CSVs, structured statistical JSON/CSV summaries, and a publication-grade HTML report.

---

## 2. Prerequisites & Installation

### Python Environment
- Python 3.10 or higher.
- Standard scientific packages:
```bash
pip install numpy pandas scipy matplotlib requests
```

No external server frameworks (Node.js, Express, React, Flask) are required. The frontend runs on vanilla HTML5, CSS3, and modern JavaScript, with Chart.js loaded via CDN.

---

## 3. Quickstart & Application Startup

### Step 1: Start the Local Dashboard Server
To view the live dashboard in your web browser, start a lightweight Python HTTP server from the repository root:

```bash
python -m http.server 8000 --directory frontend
```

### Step 2: Open in Browser
Navigate to:
```
http://localhost:8000/
```
The dashboard loads `frontend/results.snapshot.json` and client-evaluates all 28,042 Mumbai observations as you drag the Danger Threshold slider.

---

## 4. Analysis Pipeline, Tests, & Exports

### Run the Full Statistical Pipeline
Executes the sequential statistical pipeline (`01_core_stats` through `07_visualizations`), regenerates figures in `backend/output/figures/`, writes `backend/output/results.json`, generates all exports, and synchronizes `frontend/results.snapshot.json`:

```bash
python backend/scripts/run_pipeline.py
```

### Run the Automated Test Suite
Runs the 14-part unit and integration test suite verifying data integrity, canonical Mumbai coordinates, statistical formulas, bootstrap CIs, uniform exceedance rules, goodness-of-fit diagnostics, NWP forecast structure, cache integrity safeguard, risk index auditing, snapshot synchronization, presentation wording contracts, simulation intervals, and multi-threshold boundary behavior:

```bash
python backend/scripts/test_pipeline.py
```

### Refresh Historical Records from Open-Meteo API
To re-query the Open-Meteo Archive and NWP Forecast APIs for live Mumbai data:

```bash
python backend/scripts/run_pipeline.py --fetch-api
```
*Note: Strict cache validation ensures that only genuine Mumbai datasets with matching coordinates are utilized.*

### Generate Verified Project Deliverables & Exports
To regenerate all project export files independently:

```bash
python backend/scripts/generate_exports.py
```

---

## 5. Verified Project Exports

The export scripts and frontend download buttons generate the following files:

| Deliverable | Location | Description |
|---|---|---|
| **Cleaned Historical Data (CSV)** | `backend/output/heatsense_cleaned_historical_temperatures.csv` | 28,042 daily Mumbai records (1950–2026) with full provenance metadata header, units (°C), and seasonal tags. |
| **Statistical Summary (JSON)** | `backend/output/heatsense_statistical_summary.json` | Machine-readable structured dictionary of sample metrics, quartiles, CIs, complete-years trend, and diagnostics. |
| **Statistical Summary (CSV)** | `backend/output/heatsense_statistical_summary.csv` | Tabular key-value statistical table with 95% confidence intervals and notes. |
| **Comprehensive Report (HTML)** | `backend/output/heatsense_project_report.html` & `frontend/report.html` | Publication-grade, printable HTML statistical report documenting Mumbai coastal methodology, formulas, results, and limitations. |

---

## 6. Project Architecture

```
HeatSense/
├── backend/
│   ├── data/
│   │   ├── dataset.csv                  # 28,042 validated daily Mumbai records (1950-01-01 to 2026-10-10)
│   │   └── dataset_metadata.json        # Provenance, coordinates, variables, and API cache status
│   ├── scripts/
│   │   ├── config.py                    # Centralized canonical location & path configuration
│   │   ├── common.py                    # Shared I/O utilities, statistics contracts, and paths
│   │   ├── 00_fetch_weather_data.py     # Open-Meteo Archive & Forecast API ingestion (with cache security)
│   │   ├── 01_core_stats.py             # Sample statistics, bootstrap CIs, Kelvin CV, seasonal breakdown
│   │   ├── 02_distribution_fit.py       # MLE candidate fitting (Lognorm, Gamma, Normal, Gumbel), KS tests
│   │   ├── 03_simulation.py             # Monte Carlo simulation, bootstrap resampling, sensitivity
│   │   ├── 04_trend.py                  # Complete calendar years (1950-2025) & daily secular trends
│   │   ├── 05_dependence.py             # Autocorrelation, heatwave run length, Markov transitions
│   │   ├── 06_synthesis.py              # Exploratory Heat Risk Index audit
│   │   ├── 07_visualizations.py         # Static diagnostic charts generator
│   │   ├── generate_exports.py          # CSV, JSON, and publication HTML report generator
│   │   ├── run_pipeline.py              # End-to-end pipeline runner and frontend snapshot sync
│   │   └── test_pipeline.py             # Comprehensive automated verification suite (14 tests)
│   └── output/
│       ├── results.json                 # Unified statistical state
│       ├── figures/                     # Generated PNG figures (histogram, Q-Q, sensitivity, etc.)
│       └── heatsense_*                  # Exported CSV, JSON, and HTML deliverables
├── frontend/
│   ├── index.html                       # Dark-themed responsive dashboard with live slider controls
│   ├── style.css                        # Design system, glassmorphic cards, arc gauge, animations
│   ├── app.js                           # Live slider state recalculation, chart updates, export triggers
│   ├── results.snapshot.json            # Synchronized results mirror
│   └── report.html                      # Standalone printable statistical report
├── report/
│   ├── report.md                        # Formal written investigation report (Mumbai)
│   ├── limitations.md                   # Methodological and climatological limitations
│   └── demo_script.md                   # 2-minute live presentation script
└── ARCHITECTURE.md                      # Technical design and integration contracts
```

---

## 7. Key Statistical Findings at a Glance (Mumbai)

- **Study Location:** Mumbai, Maharashtra, India ($19.0760^\circ\text{N}, 72.8777^\circ\text{E}$; ERA5 grid: $19.0861^\circ\text{N}, 72.8529^\circ\text{E}$, elevation $6.0\text{ m}$).
- **Sample Size ($N$):** $28,042$ consecutive days ($0$ missing, $0$ duplicates).
- **Mean Temperature:** $30.24^\circ\text{C}$ ($30.237^\circ\text{C}$, $95\%\text{ CI: } [30.21, 30.27]^\circ\text{C}$).
- **Median / IQR:** Median $= 30.20^\circ\text{C}$, $\text{IQR} = 3.70^\circ\text{C}$ ($Q_1 = 28.30^\circ\text{C}, Q_3 = 32.00^\circ\text{C}$).
- **Historical Extremes:** Min $= 22.10^\circ\text{C}$, Max $= 41.30^\circ\text{C}$ (Range $= 19.20^\circ\text{C}$).
- **Sample Standard Deviation:** $2.387^\circ\text{C}$ ($95\%\text{ CI: } [2.37, 2.405]^\circ\text{C}$, Variance: $5.699$).
- **Kelvin Relative Dispersion:** $0.79\%$ on absolute thermodynamic scale ($\bar{x}_{\text{Kelvin}} = 303.39\text{ K}$; Celsius CV $7.89\%$ with interval-scale warning).
- **Default Analytical Threshold ($T > 36.0^\circ\text{C}$):** Exactly **265 days** ($0.95\%$ / $0.00945$ empirical probability; average spacing $105.8$ days).
- **Seasonal Distribution:** Winter: $5$ / $6,918$ ($0.07\%$), Summer/Pre-Monsoon: $253$ / $7,084$ ($3.57\%$), Monsoon: $0$ / $9,394$ ($0.00\%$), Post-Monsoon: $7$ / $4,646$ ($0.15\%$). Denominators sum to $28,042$ without gaps or overlaps.
- **Distribution Modeling:** Log-Normal distribution yields lowest AIC ($128,123.52$, runner-up Gamma $128,163.53$); all unimodal candidates are formally rejected by Kolmogorov-Smirnov tests ($p < 0.0001$) due to coastal monsoon suppression and bimodal post-monsoon heating. Theoretical tail $P(T > 36.0^\circ\text{C}) = 1.21\%$.
- **Secular Trend (Complete Years 1950–2025, $N=76$):** $+0.1128^\circ\text{C}/\text{decade}$ ($95\%\text{ CI: } [+0.0725, +0.1532]^\circ\text{C}/\text{decade}$, $p < 0.0001$, $R^2 = 0.289$). Daily continuous series drift: $+0.1192^\circ\text{C}/\text{decade}$ (total drift $+0.92^\circ\text{C}$, $R^2 = 0.0122$).
- **Heatwave Persistence:** $\rho_1 = 0.9039$, weekly persistence $\rho_7 = 0.6484$, 163 distinct heatwave clusters, mean run length above $36^\circ\text{C} = 1.63$ days (max run $= 5$ days), Markov transition $P(\text{Hot}\mid\text{Hot}) = 38.6\%$ vs $P(\text{Hot}\mid\text{Cool}) = 0.6\%$.
- **Exploratory Heat Risk Index:** $\mathbf{1.05 / 100}$ (Low Band; uncalibrated operational decision indicator).
- **Forecast Validation & Verification Discipline:** Strict out-of-sample discipline ($0$ validated pairs claimed prior to date conclusion, current-day diagnostic excluded from out-of-sample validation, ERA5 reanalysis proxy limitations disclosed, uncalibrated confidence intervals removed).
- **Verification Status:** 16 automated unit, regression, and integration tests passing (`python backend/scripts/test_pipeline.py`).

