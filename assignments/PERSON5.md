# PERSON 5 — Simulation & Probability Cross-Checks
**Role:** Monte Carlo simulation, bootstrap probability estimation, return
period framing, threshold sensitivity.
**Script you own:** `backend/scripts/03_simulation.py`
**Section you write to `results.json`:** `simulation`
**Depends on:** `distribution_fit` (Person 1) must exist first.

---

## 1. What you're actually answering

Person 1 gives you one number: "here's the theoretical probability of an
extreme day, according to our best-fit model." Your entire job is to
**stress-test that number two independent ways** and reframe it in language
a non-statistician (and an engineer) actually uses.

## 2. Concepts you must understand before writing this

- **Monte Carlo simulation**: generate thousands of synthetic "days" by
  drawing random samples from the FITTED distribution (not the raw data —
  Person 1's `distribution_fit.best_model` and its `params`). Count what
  fraction exceed the threshold. This tests: "does the math actually behave
  the way the formula claims, if I brute-force simulate it?" It should
  closely match the theoretical probability — if it doesn't, something is
  wrong in either your simulation or Person 1's fit, and that's worth
  flagging immediately.
- **Convergence / sensitivity analysis**: run the Monte Carlo simulation at
  1,000, 10,000, and 100,000 trials. The estimate should stabilize
  (converge) toward the theoretical value as trial count increases. This
  demonstrates the simulation is behaving correctly, not just producing a
  lucky number once.
- **Bootstrap probability estimate**: unlike Monte Carlo, this uses ONLY the
  real recorded data, resampled with replacement, with **no distribution
  assumption at all**. For each of ~10,000 resamples (same size as the
  original dataset), compute what fraction exceeds the threshold, then
  average across all resamples. This is your distribution-free cross-check
  — if it disagrees noticeably with the theoretical/Monte Carlo numbers,
  that's real evidence the fitted distribution doesn't perfectly capture
  reality (which ties directly to Person 1's Shapiro-Wilk / holdout results).
- **Return period**: `1 / probability`, in days. Turns "7.45% per day" into
  "roughly a 1-in-13-day event" — the way engineering/safety standards
  actually communicate risk. Simple division, but state it explicitly; it's
  one of the most legible outputs in the whole project for a general audience.
- **Threshold sensitivity**: instead of reporting probability at ONE
  threshold, compute it across a small range (e.g. every 1°C from 33 to
  38°C) using the same fitted model. This shows how risk changes as the
  definition of "extreme" changes, and produces a proper curve for the
  dashboard's slider to trace.

## 3. What to compute

1. Load `results.json["distribution_fit"]` — get `best_model`, its
   `params`, and `threshold_c`. **Never re-fit your own distribution or
   hardcode a different threshold** — always read Person 1's canonical
   values.
2. Monte Carlo: simulate at `n_trials` = 1,000 / 10,000 / 100,000 using
   `scipy.stats.<best_model>.rvs(*params, size=n_trials, random_state=<fixed seed>)`,
   count fraction exceeding threshold at each trial count.
3. Bootstrap: resample the real dataset (`common.load_temps()`) 10,000
   times with replacement, compute exceedance fraction per resample, average.
4. Build the `comparison` object: theoretical (from Person 1) vs.
   Monte Carlo (10k) vs. bootstrap — all three, side by side.
5. Return period = `1 / theoretical_probability` (or use the 10k Monte
   Carlo figure if you prefer — document which you used).
6. Threshold sensitivity: loop the theoretical model's `sf()` across a
   small range of thresholds around the main one.

## 4. Output schema

```jsonc
"simulation": {
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
}
```

## 5. Depends on

`results.json["distribution_fit"]` (Person 1). If that section doesn't
exist yet, your script should fail with a clear message telling the user to
run `02_distribution_fit.py` first — see `common.py`'s error style and
match it.

## 6. Definition of done

- [ ] Script reads `distribution_fit`, never hardcodes threshold or refits
      its own distribution
- [ ] All three probability estimates (theoretical, Monte Carlo, bootstrap)
      are present and computed independently
- [ ] Convergence trend across 1k/10k/100k is printed clearly to terminal
- [ ] Fixed random seed used everywhere (numbers must be reproducible)
- [ ] **Rerun against the REAL dataset once Person 3 delivers it.** The
      return period and threshold sensitivity range in the starter code
      are placeholder values computed on fake data — re-check the
      sensitivity range still makes sense (e.g. don't leave thresholds
      that are absurdly high/low for your city's real climate)
- [ ] You can explain the difference between what Monte Carlo tests and
      what bootstrap tests, unscripted, without looking at notes
