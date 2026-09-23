# PERSON 6 — Trend Analysis
**Role:** Test whether the temperature record shows a warming (or cooling)
trend over the observation window, and whether that trend is both
statistically and practically meaningful.
**Script you own:** `backend/scripts/04_trend.py`
**Section you write to `results.json`:** `trend`
**Depends on:** only the raw dataset — can start immediately, in parallel
with Persons 1, 5, and 7.

---

## 1. What you're actually answering

Every probability calculation in this project quietly assumes the process
generating the data is **stationary** — that "hot" today means the same
thing as "hot" three weeks ago. If temperatures are actually drifting
upward across your observation window, that assumption is shaky, and it
changes how the whole risk estimate should be interpreted (a rising trend
means recent probability estimates are the more relevant ones, not the
whole-window average). Your job is to test this directly, honestly, and
explain what it means either way.

## 2. Concepts you must understand before writing this

- **Linear regression**: fit a straight line, `temperature = slope * day_index + intercept`,
  through your data using ordinary least squares
  (`scipy.stats.linregress` is the simplest tool for this — it directly
  gives you slope, intercept, r-value, p-value, and standard error in one call).
- **Statistical significance vs. practical significance** — this is the
  most important conceptual point of your whole section. A p-value tells
  you whether the slope is likely non-zero. It does NOT tell you whether
  the slope is large enough to matter. A trend of +0.003°C/day could be
  "statistically significant" with enough data points while amounting to
  a fraction of a degree over your entire window — genuinely a footnote,
  not a headline. You must report BOTH: is it significant, AND is it
  meaningfully large in absolute terms.
- **R-squared**: how much of the day-to-day variation in temperature is
  "explained" by the trend line versus just noise. A low R² alongside a
  significant p-value is completely normal and expected here — temperature
  is noisy day to day, but a trend can still be real underneath the noise.
  Don't let a low R² make you think the analysis "failed."
- **Residual diagnostics**: after fitting the line, look at `actual - predicted`
  for every point. If residuals look roughly random and scattered around
  zero, the straight-line trend model is a reasonable description. If
  residuals show a clear pattern (e.g. a curve, or increasing spread over
  time), that's a sign a simple linear trend isn't the full story — this
  becomes a genuine, defensible limitation to name, not something to hide.

## 3. What to compute

1. Convert `date` to a numeric day-index (e.g. days since the first
   observation) — regression needs a numeric x-axis, not date strings
2. Run `scipy.stats.linregress(day_index, max_temp_c)` — get slope,
   intercept, r-value, p-value
3. Compute `r_squared = r_value ** 2`
4. Decide `is_statistically_significant` using the standard `p < 0.05` cutoff
5. Compute the *total* drift implied over your full window
   (`slope * n_days`) and write a one-line `practical_note` stating whether
   that total drift is actually large relative to normal day-to-day
   variability (compare it informally to `core_stats.std_dev` from Person
   1's output if available — a trend smaller than natural daily variation
   is a weak signal, however "significant" the p-value)
6. Compute residuals (`actual - predicted` for every point) and do a basic
   sanity check — plot-worthy data for script 7, and a boolean
   `residuals_pattern_ok` (true if residuals look reasonably random; use
   your judgement, or a simple runs test if you want to be rigorous —
   document whichever you use)

## 4. Output schema

```jsonc
"trend": {
  "slope_c_per_day": 0.021,
  "slope_p_value": 0.03,
  "r_squared": 0.11,
  "is_statistically_significant": true,
  "practical_note": "Slope significant but total drift over the window is < 1C; practically small.",
  "residuals_pattern_ok": true
}
```

## 5. Depends on

Only `backend/data/dataset.csv`. No dependency on any other section — you
can build and test this from day one against placeholder data.

## 6. Definition of done

- [ ] Script runs standalone, writes a valid `trend` section
- [ ] Both statistical significance (p-value) AND practical magnitude
      (actual °C drift) are reported — not just one
- [ ] Residuals are computed and exported for script 7's diagnostic plot
- [ ] **Rerun against the REAL dataset once Person 3 delivers it.** On
      45 days of randomly-generated placeholder noise, "no significant
      trend" is a trivial, meaningless result — it tells you nothing about
      whether your CODE is correct. Only real data with real seasonal/
      weather structure is a genuine test of this analysis
- [ ] You can explain, unscripted, why a statistically significant trend
      can still be practically unimportant, and vice versa
