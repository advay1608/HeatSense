# PERSON 4 — Report Lead
**Role:** Written investigation, interpretation, limitations, demo script.
**Script you own:** `backend/scripts/07_visualizations.py` (shared —
generates the figures your report needs)
**Deliverable:** `report/report.md` (+ export to PDF/Word at the end),
`report/limitations.md`
**You do not write to `results.json`** — you consume the whole file and
produce prose.

---

## 1. What you're actually delivering

Not a summary of what everyone did — an **argument**. The report needs to
read as one coherent investigation with a beginning, middle, and end, not
seven pasted-together sections. You are the only person whose job is to
make the whole thing make sense to a reader who wasn't in any of the team's
planning conversations.

## 2. Required report structure (maps directly to `REQUIREMENTS.md` §1.1)

1. **Problem statement** — what question is this investigation answering,
   and why does it matter (engineering/safety framing, not just "for class")
2. **Description of the dataset** — from Person 3's documentation
3. **Source of data** — from Person 3's documentation
4. **Statistical concepts used** — variance, SD, CV, distribution fitting,
   probability, simulation, resampling — briefly define each, don't just
   name-drop them
5. **Relevant formulae** — pull directly from each script's docstring in
   `backend/scripts/`; they're already written precisely for this purpose
6. **Step-by-step numerical calculation** — use Person 1's
   `results["core_stats"]["manual_walkthrough"]` directly, don't re-derive it
7. **Tables / frequency distributions** — histogram bin data from script 7
8. **Graphical representation** — all 6 required graphs (see §3 below),
   each with a caption explaining what it shows and why it's there
9. **Interpretation of results** — the actual analysis: what do the numbers
   mean, do the three probability estimates agree, what does the winning
   distribution tell us, is there a trend, do extreme days cluster
10. **Engineering decision** — `results["synthesis"]["heat_risk_index"]`
    and `risk_band`, explained plainly: what would an engineer/planner
    actually do with this number
11. **Limitations of the analysis** — see §4 below, this is its own file

## 3. Figures you need (`07_visualizations.py`)

This script reads `results.json` (and the raw dataset) and generates PNGs
into `backend/output/figures/`:

1. Histogram + fitted distribution curve overlay (use the winning model
   from `distribution_fit`, not necessarily Normal)
2. Boxplot
3. Q-Q plot (against Normal, using `distribution_fit.qq_plot_r_value` data)
4. Monte Carlo convergence plot (`simulation.monte_carlo`)
5. Threshold sensitivity curve (`simulation.threshold_sensitivity`)
6. Autocorrelation plot (`dependence` — Person 7's output)

Each function should save one named PNG and print its save path. Reuse
matplotlib patterns already established in the project rather than
inventing a new visual style per figure — the report should look like it
came from one team, not seven.

## 4. `report/limitations.md` — required content

This is not an afterthought section — it's a direct requirement (see
`REQUIREMENTS.md` §3). For EACH of these five assumptions, write at least a
paragraph stating whether it holds for our data, which teammate's output
tested it, and what it would mean if it didn't:

1. **Independence** — tested by Person 7 (`dependence.lag1_autocorrelation`, run lengths)
2. **Stationarity** — tested by Person 6 (`trend.slope_p_value`, residuals)
3. **Representativeness** — cannot be fully tested with a short record;
   state this honestly rather than glossing over it
4. **Model adequacy** — tested by Person 1 (AIC/BIC comparison, holdout
   validation, Shapiro-Wilk)
5. **Measurement quality** — from Person 3's documented source and any
   cleaning decisions

Also state explicitly (this is your single most important sentence for
avoiding an awkward question in the demo): **this is not a weather
forecast** — it's a statistical characterization of risk from a limited
historical record, not a physical atmospheric model.

## 5. Demo script

A short (~2 minute) spoken walkthrough for whoever presents:
1. State the problem in one sentence
2. Show the dashboard: move the threshold slider, show the probability and
   risk gauge updating live
3. Toggle the distribution model, point out the probability shifts —
   explicitly say "we tested multiple models instead of assuming one"
4. State the headline risk number and what it means in plain language
5. One sentence on the honest limitation (see §4) — raising it yourself,
   unprompted, reads as far stronger than getting asked and improvising

## 6. Working method

You will be finishing last, but you should be **drafting throughout**, not
starting once everyone else is "done." Concretely:
- Start the problem statement and dataset/source sections as soon as Person
  3 delivers
- Draft the concepts/formulae sections early — they don't depend on final
  numbers, only on the scripts' docstrings, which are stable from early on
- Fill in interpretation and the engineering decision only once
  `results.json` is fully populated (after Person 1's `synthesis` step)
- Write limitations in parallel with whoever is testing each assumption —
  don't wait until the very end to start that conversation with Persons 1, 6, and 7

## 7. Definition of done

- [ ] `07_visualizations.py` produces all 6 required figures without errors,
      **regenerated against the real dataset** (delete and rerun once
      Person 3 delivers — the current figures in the repo are placeholders)
- [ ] `report/report.md` — **currently a bare skeleton with section headers
      only, zero prose written.** All 11 sections from §2 actually written,
      in your own words, not copy-pasted script docstrings
- [ ] `report/limitations.md` — **also currently a bare skeleton.** All 5
      assumptions genuinely discussed with real numbers, not placeholders
- [ ] Demo script written and reviewed by whoever is presenting
- [ ] You can walk through the entire report's logic out loud without
      reading it verbatim
