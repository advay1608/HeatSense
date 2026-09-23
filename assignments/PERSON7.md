# PERSON 7 — Dependence & Clustering Analysis
**Role:** Test whether extreme-heat days occur independently or cluster
together (heatwaves), and explain what that means for how the risk
estimate should actually be interpreted.
**Script you own:** `backend/scripts/05_dependence.py`
**Section you write to `results.json`:** `dependence`
**Depends on:** only the raw dataset — can start immediately, in parallel
with Persons 1, 5, and 6.

---

## 1. What you're actually answering

Every probability number in this project (theoretical, Monte Carlo,
bootstrap) is a statement about a **single, independent day**: "any given
day has roughly a 7% chance of being extreme." But real heat doesn't
arrive as isolated random days — it arrives in waves. If extreme days
cluster, a 7% daily probability actually translates into a much more
concentrated, more disruptive real-world risk (e.g. a 3-day heatwave) than
the same 7% spread evenly and independently across the calendar would
suggest. Your job is to measure whether this clustering is actually
happening in the data, and how strongly.

## 2. Concepts you must understand before writing this

- **Autocorrelation**: measures whether today's value is correlated with
  a previous day's value. **Lag-1 autocorrelation** specifically checks
  correlation between each day and the day immediately before it. A value
  near 0 means no relationship (today tells you nothing about tomorrow); a
  positive value means hot days tend to follow hot days.
  `pandas.Series.autocorr(lag=1)` computes this directly, or
  `statsmodels.tsa.stattools.acf` if you want the full autocorrelation
  function across multiple lags (useful for the plot in script 7).
- **Statistical significance of autocorrelation**: for a series of length
  `n`, a common rough significance threshold is `±1.96/sqrt(n)` — if the
  lag-1 autocorrelation exceeds this in absolute value, it's reasonably
  considered statistically significant, not just noise. Use this or a
  proper Ljung-Box test if you want to be more rigorous.
- **Run-length analysis**: define "extreme" as any day exceeding the
  canonical threshold (`results["distribution_fit"]["threshold_c"]`, set
  by Person 1). Then walk through the time-ordered data and find
  consecutive runs of extreme days (a single extreme day surrounded by
  non-extreme days is a "run" of length 1; three extreme days in a row is
  a run of length 3). This directly answers "when extreme weather hits,
  how long does it tend to last?" — a genuinely different and more useful
  question than a single-day probability.

## 3. What to compute

1. Load the raw dataset AND read `results["distribution_fit"]["threshold_c"]`
   — do not hardcode your own threshold, use the canonical one
2. Compute lag-1 autocorrelation on the raw `max_temp_c` series
3. Determine `is_significant` using the `±1.96/sqrt(n)` rule (or document
   your chosen method if different)
4. Create a boolean "is extreme" series (`max_temp_c > threshold_c`), then
   walk through it to find all consecutive runs of `True` values — record
   `max_run_length_above_threshold`, `mean_run_length_above_threshold`
   (average length across all runs found), and `n_exceedance_runs` (how
   many separate runs occurred at all)
5. Write a plain-English `interpretation` string summarizing what this
   means practically (e.g., whether the team should describe risk as
   "isolated random days" or "clustered multi-day events" in the report
   and dashboard)

## 4. Output schema

```jsonc
"dependence": {
  "lag1_autocorrelation": 0.41,
  "is_significant": true,
  "max_run_length_above_threshold": 3,
  "mean_run_length_above_threshold": 1.6,
  "n_exceedance_runs": 5,
  "interpretation": "Extreme days show mild clustering; per-day probability underestimates the risk of a multi-day heat event."
}
```

## 5. Depends on

`results["distribution_fit"]["threshold_c"]` (Person 1) for defining what
counts as "extreme" in the run-length analysis — but the autocorrelation
calculation itself only needs the raw dataset, so you can start that part
immediately, and add the run-length part once Person 1's section exists.

## 6. Definition of done

- [ ] Script runs standalone, writes a valid `dependence` section
- [ ] Uses the canonical threshold from `distribution_fit`, not a hardcoded one
- [ ] Run-length logic correctly identifies consecutive-day clusters (test
      it by hand against a small toy example before trusting it on the
      real data)
- [ ] **Rerun against the REAL dataset once Person 3 delivers it.** Same
      caveat as Person 6: placeholder data is random noise, so "no
      clustering detected" right now proves nothing about real heatwave
      behavior — it only proves the script runs
- [ ] You can explain, unscripted, why a 7% daily probability with strong
      clustering is a materially different real-world risk than the same
      7% with no clustering
