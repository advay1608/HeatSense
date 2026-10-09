# ARCHITECTURE.md

This is the technical contract that makes seven people's independent work
integrate without anyone touching anyone else's code. Read this before
writing any script. Your `assignments/PERSON<N>.md` tells you *what* to
compute; this file tells you *how it plugs into everything else*.

---

## 1. The core idea: one pipeline, one shared results file

```
backend/data/dataset.csv
        │
        ▼
backend/scripts/01 ... 06   (each script: reads dataset + results.json,
        │                    computes its section, calls write_result())
        ▼
backend/output/results.json   ◄── THE single source of truth
        │
        ├──────────────► frontend/  (Person 2 reads this file, renders dashboard)
        └──────────────► report/    (Person 4 reads this file, writes the report)
```

Every script:
1. Reads `backend/data/dataset.csv` (via `common.load_dataset()`)
2. Optionally reads other sections it depends on from `results.json` (via
   `common.read_results()`)
3. Computes its own section
4. Writes it back with `common.write_result("section_name", {...})`

No script imports another script's Python code directly. The **only**
interface between scripts is `results.json`. This is deliberate: it means
any script can be rewritten, rerun, or debugged by one person without
needing to understand or import anyone else's code.

---

## 2. Directory structure

```
heat-risk-project/
├── README.md
├── ARCHITECTURE.md          <- this file
├── SYSTEM.md
├── REQUIREMENTS.md
├── CLAUDE.md
├── assignments/
│   ├── PERSON1.md ... PERSON2.md
├── backend/
│   ├── data/
│   │   └── dataset.csv       <- Person 3's deliverable
│   ├── scripts/
│   │   ├── common.py         <- shared contract, DO NOT FORK
│   │   ├── 00_generate_sample_data.py
│   │   ├── 01_core_stats.py          <- Person 1
│   │   ├── 02_distribution_fit.py    <- Person 1
│   │   ├── 03_simulation.py          <- Person 5
│   │   ├── 04_trend.py               <- Person 6
│   │   ├── 05_dependence.py          <- Person 7
│   │   ├── 06_synthesis.py           <- Person 1 (runs LAST, needs everyone else's section)
│   │   ├── 07_visualizations.py      <- Person 4 (report figures) / shared
│   │   └── run_pipeline.py           <- runs 01-07 in the correct order
│   └── output/
│       ├── results.json      <- THE shared contract file (generated, git-ignored or committed — see SYSTEM.md)
│       └── figures/          <- PNGs from 07_visualizations.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── results.snapshot.json <- a COPY of backend/output/results.json, frozen for the demo (see §4)
└── report/
    ├── report.md
    └── limitations.md
```

---

## 3. `results.json` — the full schema

This is the single most important reference in the repo. Every key here is
**owned by exactly one person**. If your assignment doc says you own
`"core_stats"`, you write exactly this shape and nothing else touches it.

```jsonc
{
  "core_stats": {                     // OWNER: Person 1
    "n_days": 45,
    "mean": 32.97,
    "mean_ci95": [32.31, 33.62],
    "variance": 4.51,
    "std_dev": 2.10,
    "std_dev_ci95": [1.78, 2.39],
    "cv_percent": 6.44,
    "cv_percent_ci95": [5.50, 7.31],
    "shapiro_wilk": { "statistic": 0.932, "p_value": 0.011, "is_normal_at_5pct": false },
    "manual_walkthrough": {
      "sample_index": 0, "x_i": 33.4, "mean": 32.97,
      "deviation": 0.43, "squared_deviation": 0.18
    }
  },

  "distribution_fit": {               // OWNER: Person 1
    "threshold_c": 36.0,
    "candidates": [
      { "name": "normal",     "params": {"loc": 32.97, "scale": 2.10}, "aic": 187.3, "bic": 189.1, "log_likelihood": -91.6 },
      { "name": "lognorm",    "params": {"s": 0.06, "loc": 0, "scale": 32.5}, "aic": 182.9, "bic": 184.7, "log_likelihood": -89.4 },
      { "name": "gamma",      "params": {"a": 245.0, "loc": 0, "scale": 0.134}, "aic": 185.1, "bic": 186.9, "log_likelihood": -90.5 },
      { "name": "gumbel_r",   "params": {"loc": 32.0, "scale": 1.9}, "aic": 184.0, "bic": 185.8, "log_likelihood": -90.0 }
    ],
    "best_model": "lognorm",
    "holdout_validation": {
      "train_size": 36, "test_size": 9,
      "best_model_test_log_likelihood": -18.2,
      "runner_up_test_log_likelihood": -19.7
    },
    "qq_plot_r_value": 0.9623,
    "theoretical_probability": 0.0745
  },

  "simulation": {                     // OWNER: Person 5
    "threshold_c": 36.0,
    "monte_carlo": {
      "trials": [1000, 10000, 100000],
      "probabilities": [0.0730, 0.0756, 0.0749]
    },
    "bootstrap_probability": 0.0669,
    "bootstrap_resamples": 10000,
    "comparison": {
      "theoretical": 0.0745, "monte_carlo_10k": 0.0756, "bootstrap": 0.0669
    },
    "return_period_days": 13.4,
    "threshold_sensitivity": {
      "thresholds_c": [33, 34, 35, 36, 37, 38],
      "probabilities":  [0.44, 0.28, 0.16, 0.0745, 0.03, 0.01]
    }
  },

  "trend": {                          // OWNER: Person 6
    "slope_c_per_day": 0.021,
    "slope_p_value": 0.03,
    "r_squared": 0.11,
    "is_statistically_significant": true,
    "practical_note": "Slope significant but total drift over the window is < 1C; practically small.",
    "residuals_pattern_ok": true
  },

  "dependence": {                     // OWNER: Person 7
    "lag1_autocorrelation": 0.41,
    "is_significant": true,
    "max_run_length_above_threshold": 3,
    "mean_run_length_above_threshold": 1.6,
    "n_exceedance_runs": 5,
    "interpretation": "Extreme days show mild clustering; per-day probability underestimates the risk of a multi-day heat event."
  },

  "synthesis": {                      // OWNER: Person 1  (must run LAST)
    "heat_risk_index": 0.62,
    "risk_band": "moderate",
    "formula_note": "index = exceedance_probability * (1 + trend_adjustment) * (1 + clustering_adjustment)",
    "components_used": {
      "base_probability": 0.0745,
      "trend_adjustment": 0.05,
      "clustering_adjustment": 0.12
    }
  },

  "_meta": {
    "generated_at": "2026-09-22T10:00:00",
    "dataset_source": "placeholder | <real source name once Person 3 delivers>",
    "dataset_n_days": 45,
    "last_updated_section": "synthesis"
  }
}
```

**Rules:**
- Keys inside your section can be added to if your analysis needs more, but
  never remove or rename a key another script/the frontend/the report
  already depends on without updating this file and telling the team.
- All probabilities are plain floats in `[0, 1]`, not percentages (multiply
  by 100 only at display time, in the frontend/report, never in the JSON).
- All temperatures are in Celsius.
- Confidence intervals are always `[lower, upper]` 2-element arrays, 95% CI
  unless a key explicitly says otherwise.

---

## 4. Frontend integration model: static snapshot, not a live server

**Decision:** the dashboard does NOT call a running Python backend during
the demo. Instead:

1. Run the full pipeline (`run_pipeline.py`) ahead of time.
2. Copy the resulting `backend/output/results.json` into
   `frontend/results.snapshot.json`.
3. `frontend/app.js` loads that snapshot with `fetch('./results.snapshot.json')`
   on page load and does all "live" recalculation (e.g. probability at a
   new threshold from the fitted distribution parameters) **in JavaScript**,
   using the distribution parameters already present in the snapshot.

**Why:** a live Python server is one more thing that can fail in front of
the class (server not running, port conflict, laptop sleeps, wifi drops).
A static snapshot recomputes instantly in-browser and cannot crash mid-demo.
The audience cannot tell the difference.

**Implication for Person 2:** you need a small JavaScript reimplementation
of the Normal/Log-Normal/Gamma/Gumbel CDF (or at minimum, the winning
model's CDF) to make the threshold slider recompute probability live. This
is a solved, well-documented problem — do not derive it from scratch; use a
standard JS stats formula (see `assignments/PERSON2.md` for a reference
implementation of the Normal CDF you can copy).

**Refresh procedure** (do this every time backend numbers change):
```bash
python3 backend/scripts/run_pipeline.py
cp backend/output/results.json frontend/results.snapshot.json
```

---

## 5. Tech stack decision: plain HTML/CSS/JS, not React

For this project, plain HTML + CSS + vanilla JS (or at most a single
charting library loaded via CDN, e.g. Chart.js) is the right choice over
React:

- No build step, no `npm install`, no bundler — open `index.html` and it
  works. Zero risk of a broken build on demo day.
- The dashboard's actual complexity (a slider, a chart redraw, a gauge, a
  toggle) does not need component architecture or state management.
- It is trivially deployable/shareable — literally one folder, works from
  any file server or even `file://`.

If Person 2 is already confident with React and wants component structure
for their own sanity, that's fine — but the output must still be a static
build with no server dependency at runtime, consuming
`results.snapshot.json` the same way.

---

## 6. Execution order (`run_pipeline.py`)

```
00_generate_sample_data.py   (only if backend/data/dataset.csv doesn't exist yet)
01_core_stats.py             (Person 1)
02_distribution_fit.py       (Person 1 — needs core_stats' mean/SD as a starting point)
03_simulation.py             (Person 5 — needs distribution_fit's best_model + params)
04_trend.py                  (Person 6 — independent, only needs raw dataset)
05_dependence.py             (Person 7 — independent, only needs raw dataset)
06_synthesis.py              (Person 1 — needs simulation, trend, dependence sections; MUST run last)
07_visualizations.py         (figures for the report; needs everything above)
```

`run_pipeline.py` simply calls each script's `main()` in this order and
stops with a clear error if a required upstream section is missing from
`results.json`.

---

## 7. What "readily integrable" means in practice

If you follow this document and your assignment doc:
- You never need to ask a teammate for their raw code.
- You never need to agree on file formats in a group chat mid-project.
- Person 2 (frontend) and Person 4 (report) can start building their
  consumers against the **example JSON in §3** on day one, before anyone's
  real script even exists — because the schema is fixed in advance.
- Re-running any single script after a bug fix automatically updates only
  that section of `results.json`, without needing anyone to re-run their own
  script.

---

## 8. Short-term AR(1) persistence forecasting

While macro climate regression (`04_trend.py`) tracks decadal temperature drift (e.g. -0.085°C/decade over 76 years), daily operational heat management requires high-resolution short-term projections.

In `06_synthesis.py`, an autoregressive persistence model is computed using Person 7's verified serial lag-1 autocorrelation ($\rho_1 = 0.9745$) anchored at the latest recorded day's temperature ($T_t$) and 14-day seasonal momentum ($m_{\text{recent}}$):

$$\mathbb{E}[T_{t+k}] = \mu + \rho_1^k (T_t - \mu) + k \cdot m_{\text{recent}} \cdot e^{-k / 5}$$

Uncertainty widens naturally over time as autoregressive memory decays:

$$\sigma_k = \sigma \sqrt{\max\left(0.05, 1 - \rho_1^{2k}\right)} + 0.20 \cdot k$$

This projection is exported under `results.json["forecast"]` and consumed by both the 7-day forecast cards and the timeline chart, providing seamless continuity between historical observations and near-term projections.

---

## 9. Physical support bounds for skewed distributions

When fitting positive continuous physical quantities (such as daily temperatures above absolute zero in Kelvin or Celsius above regional base levels), unbounded SciPy location optimization can cause numerical degeneracy on symmetric datasets (e.g. driving $\text{loc} \to -\infty$ and $s \to 0$ in log-normal fits).

In `02_distribution_fit.py`, distributions with positive support (`lognorm` and `gamma`) are constrained using `floc=0`. This ensures stable parameter estimates, non-zero scale parameters, and well-behaved analytical CDFs in both Python and client-side JavaScript.

---

## 10. Dashboard query parameter controls

The frontend supports direct URL parameters for automated evaluation, headless testing, and deep-linking:

- `?theme=dark` or `?theme=light`: overrides stored preference and system color-scheme.
- `?model=normal`, `?model=lognorm`, `?model=gamma`, or `?model=gumbel_r`: selects the active statistical distribution.
- `?threshold=40`: sets the active danger threshold in °C (valid range: 10–60°C).
