# PERSON 1 — Backend Lead
**Role:** Core statistics, uncertainty quantification, multi-distribution
model selection, and final synthesis (Heat Risk Index).
**Scripts you own:** `backend/scripts/01_core_stats.py`,
`backend/scripts/02_distribution_fit.py`, `backend/scripts/06_synthesis.py`
**Sections you write to `results.json`:** `core_stats`, `distribution_fit`, `synthesis`
**You also coordinate:** integration of everyone else's sections; you are
the person who runs `run_pipeline.py` end-to-end and fixes breakage.

Read `ARCHITECTURE.md` in full before starting — this doc assumes you have.

---

## 1. What you're actually answering

Three separate questions, in order:

1. **What do our numbers actually say, and how sure are we?** (core_stats)
2. **What shape does temperature risk actually follow — and is "Normal"
   even the right assumption?** (distribution_fit)
3. **Combining everything the team produced, what's the single risk verdict?**
   (synthesis — this is your last job, after everyone else is done)

---

## 2. Script 1 — `01_core_stats.py`

### Concepts you must understand before writing this
- **Sample vs. population variance**: we divide by `n-1` (`ddof=1` in numpy),
  not `n`, because our ~30-45 days are a *sample* of all possible days, not
  the entire population. Using `n-1` corrects a known bias.
- **Coefficient of variation (CV)**: `(std_dev / mean) * 100`. Lets you
  compare variability independent of the units/scale.
- **Bootstrap confidence intervals**: resample the dataset (with
  replacement) thousands of times, recompute the statistic each time, take
  the 2.5th/97.5th percentile of the resulting distribution as your 95% CI.
  This makes no assumption about the data's shape — important, since your
  own Shapiro-Wilk test may show the data *isn't* perfectly Normal, which
  would make classical formula-based CIs unreliable.
- **Shapiro-Wilk test**: a formal statistical test for normality.
  `p < 0.05` → statistically significant evidence the data is NOT Normal.
  This result feeds directly into `distribution_fit` (script 2) and the
  report's limitations section.

### What to compute
1. `n_days`, `mean`, `variance`, `std_dev`, `cv_percent` — direct from `common.load_temps()`
2. Bootstrap 95% CIs for `mean`, `std_dev`, `cv_percent` (≥10,000 resamples,
   fixed seed)
3. Shapiro-Wilk test statistic and p-value
4. A manual step-by-step calculation for ONE data point (index 0 is fine) —
   this satisfies the assignment's explicit "step-by-step numerical
   calculations" requirement. Print it clearly; it goes directly into the report.

### Output schema (write exactly this shape)
```jsonc
"core_stats": {
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
}
```

### Depends on
Nothing but `backend/data/dataset.csv`. This can be the very first script
anyone writes (after Person 3's dataset, or against placeholder data).

---

## 3. Script 2 — `02_distribution_fit.py`

### Concepts you must understand before writing this
- **Maximum Likelihood Estimation (MLE)**: `scipy.stats.<dist>.fit(data)`
  finds the parameters of a given distribution shape that make your
  observed data "most probable." This is how you fit each candidate.
- **The four candidates and why each is here:**
  - `scipy.stats.norm` — the standard bell curve; the "default" assumption
    most people make without checking.
  - `scipy.stats.lognorm` — right-skewed; realistic for quantities that
    can't go negative and have a longer tail on the high side.
  - `scipy.stats.gamma` — also right-skewed, flexible, common for physical
    measurements.
  - `scipy.stats.gumbel_r` — specifically designed for modelling *maxima*.
    Daily peak temperature is literally a daily maximum, so this is the
    most theoretically appropriate candidate, not just an add-on.
- **AIC / BIC (Akaike / Bayesian Information Criterion)**: both measure fit
  quality penalized for model complexity, so you can't just pick whichever
  model has the most parameters. **Lower is better** for both.
  `AIC = 2k - 2*log_likelihood`, `BIC = k*ln(n) - 2*log_likelihood`, where
  `k` = number of parameters, `n` = number of data points.
  `scipy.stats.<dist>.logpdf(data, *params).sum()` gives you log-likelihood.
- **Holdout validation**: split your data (e.g. 80/20, train/test). Fit
  each candidate ONLY on the train set. Then check which candidate assigns
  the highest log-likelihood to the *test* set it never saw. This is the
  step that proves your winning model isn't just overfit to your specific
  45 days — it's the single most important thing standing between "we
  picked whichever fit our own data best" and a genuinely validated result.
- **Q-Q plot data**: `scipy.stats.probplot(data, dist="norm")` gives you the
  points needed to visually check Normal-fit quality (script 7 turns this
  into an actual image; you just need to export the R-value here).
- **Theoretical probability**: once you've picked the winning distribution,
  `<dist>.sf(threshold, *params)` gives `P(X > threshold)` directly — the
  "survival function" (1 - CDF).

### What to compute
1. Fit all four candidates via MLE on the FULL dataset (report their params, AIC, BIC)
2. Also run the 80/20 holdout split, fit on train only, compare test-set
   log-likelihood for at least the top 2 candidates by full-data AIC
3. Pick `best_model` = lowest AIC on full data, cross-checked against
   holdout performance — if they disagree, use your judgement and document why
4. Decide `threshold_c` (default 36.0°C, or whatever your team agrees is
   "extreme heat" for your city — this is the ONE canonical place this
   value is set; everyone else reads it from here)
5. Compute `theoretical_probability` = `P(X > threshold_c)` using the winning model
6. Q-Q plot R-value against Normal (for the report's normality discussion,
   independent of which model you actually pick)

### Output schema
```jsonc
"distribution_fit": {
  "threshold_c": 36.0,
  "candidates": [
    { "name": "normal",   "params": {"loc": 32.97, "scale": 2.10}, "aic": 187.3, "bic": 189.1, "log_likelihood": -91.6 },
    { "name": "lognorm",  "params": {"s": 0.06, "loc": 0, "scale": 32.5}, "aic": 182.9, "bic": 184.7, "log_likelihood": -89.4 },
    { "name": "gamma",    "params": {"a": 245.0, "loc": 0, "scale": 0.134}, "aic": 185.1, "bic": 186.9, "log_likelihood": -90.5 },
    { "name": "gumbel_r", "params": {"loc": 32.0, "scale": 1.9}, "aic": 184.0, "bic": 185.8, "log_likelihood": -90.0 }
  ],
  "best_model": "lognorm",
  "holdout_validation": {
    "train_size": 36, "test_size": 9,
    "best_model_test_log_likelihood": -18.2,
    "runner_up_test_log_likelihood": -19.7
  },
  "qq_plot_r_value": 0.9623,
  "theoretical_probability": 0.0745
}
```

### Depends on
`core_stats` (reads `results.json["core_stats"]["mean"]`/`std_dev` as a
sanity check / initial guess, though `scipy`'s `.fit()` doesn't strictly
need it). Uses the raw dataset directly for fitting.

---

## 4. Script 3 — `06_synthesis.py` (write this LAST)

### What this does
Combines everyone's work into ONE decision output — this is the project's
answer to the assignment's "AI/engineering decision" requirement, and the
headline number for the demo.

### Formula (documented, not black-box)
```
heat_risk_index = base_probability * (1 + trend_adjustment) * (1 + clustering_adjustment)
```
- `base_probability` = `results["distribution_fit"]["theoretical_probability"]`
- `trend_adjustment` = a small positive number derived from
  `results["trend"]["slope_c_per_day"]` (Person 6's output) — e.g., scale
  the slope to reflect how much extra risk a continuing trend implies over
  the next N days. Document your exact formula choice in the script's
  docstring; keep it simple and explainable over your line, not "sound
  sophisticated" — you must be able to justify every multiplier out loud.
- `clustering_adjustment` = derived from
  `results["dependence"]["lag1_autocorrelation"]` and
  `mean_run_length_above_threshold` (Person 7's output) — clustered extreme
  days are operationally worse than isolated ones even at the same average
  probability, so this bumps the index up when clustering is present.

Classify into a `risk_band` (e.g. `"low"` < 0.05, `"moderate"` 0.05–0.15,
`"high"` > 0.15 — pick real thresholds and justify them, don't just copy
these).

### Output schema
```jsonc
"synthesis": {
  "heat_risk_index": 0.62,
  "risk_band": "moderate",
  "formula_note": "index = exceedance_probability * (1 + trend_adjustment) * (1 + clustering_adjustment)",
  "components_used": {
    "base_probability": 0.0745,
    "trend_adjustment": 0.05,
    "clustering_adjustment": 0.12
  }
}
```

### Depends on
`distribution_fit`, `simulation` (Person 5), `trend` (Person 6),
`dependence` (Person 7). **This script must be the last one you write and
run** — it is a hard blocker for Persons 5, 6, and 7 finishing first.

---

## 5. Your coordination responsibilities

Beyond your own three sections, you own making `run_pipeline.py` work
end-to-end. Concretely:
- When a teammate says their script is "done," pull their branch and run
  the full pipeline yourself before merging to `main`.
- If someone's output doesn't match the schema in `ARCHITECTURE.md` §3,
  that's a bug in their script, not something you silently patch around in
  yours — send it back with the specific mismatch.
- You're the tiebreaker if two people's work implies conflicting values for
  something that should be shared (e.g. the threshold) — the canonical
  value always comes from `distribution_fit.threshold_c`, which you own.

---

## 6. Definition of done

- [ ] `01_core_stats.py` runs standalone, writes valid `core_stats` section
- [ ] `02_distribution_fit.py` runs standalone, writes valid `distribution_fit` section
- [ ] `06_synthesis.py` runs after Persons 5/6/7 have delivered, writes valid `synthesis` section
- [ ] `python3 backend/scripts/run_pipeline.py` completes with no errors
- [ ] **Rerun against the REAL dataset once Person 3 delivers it, and
      re-check every output** — the numbers you see against placeholder
      data (including which distribution "wins") are meaningless and WILL
      change. In particular: re-verify the winning model still makes
      sense, re-check the holdout gap isn't suspiciously large, and
      re-sanity-check the Heat Risk Index and risk-band cutoffs actually
      produce a sensible verdict on real numbers — the cutoffs in
      `06_synthesis.py` are a starting judgement call, not a validated one
- [ ] You can explain, unscripted, why AIC/BIC penalize complexity, why
      holdout validation matters, and what the Heat Risk Index formula means
