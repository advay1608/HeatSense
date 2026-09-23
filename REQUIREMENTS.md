# REQUIREMENTS.md

Source of truth for **what this project must deliver**, mapped directly to
the internal assignment sheet, plus the extra requirements the team has
voluntarily taken on to raise the quality bar. If in doubt about whether
something is "required" or "nice to have," this file is the tiebreaker.

---

## 1. Assignment-mandated requirements

Taken directly from the module handout ("Activity Requirements" and
"Interactive Demonstration" sections).

### 1.1 Statistical investigation must include

| # | Requirement | Where it is satisfied |
|---|---|---|
| 1 | Problem statement | `report/` — Person 4 |
| 2 | Description of the dataset | `assignments/PERSON3.md` deliverable, written into `report/` |
| 3 | Source of data | Same — must be a named, citable public source |
| 4 | Statistical concepts used | Variance, SD, CV, distribution fitting, probability, simulation, resampling — implemented across `backend/scripts/` |
| 5 | Relevant formulae | Documented inline in each script's docstring + restated in `report/` |
| 6 | Step-by-step numerical calculations | `backend/scripts/01_core_stats.py` includes an explicit manual walkthrough for one data point |
| 7 | Appropriate tables / frequency distributions | Histogram bin data, generated in `backend/scripts/07_visualizations.py` |
| 8 | Graphical representation | 6 required charts — see §1.3 |
| 9 | Interpretation of results | `report/` — Person 4, sourced from every backend section |
| 10 | AI / engineering decision | The composite Heat Risk Index (§2.4) is the explicit engineering decision output |
| 11 | Limitations of the analysis | `report/limitations.md` — every assumption in §3 below must be addressed |

**Minimum dataset size: 20 observations.** Project target: 30+ (see
`assignments/PERSON3.md`).

### 1.2 Interactive demonstration

The assignment requires "a small working model, simulation, dashboard, game,
or interactive demonstration." This project satisfies it with the dashboard
in `frontend/` (owned by Person 2), built directly on top of `backend/output/results.json`.

The demonstration must clearly show (per the handout, continued on the next
slide the team has — confirm final bullet list before submission, but the
project currently targets):
- Live recalculation of probability as a threshold changes
- A visible representation of uncertainty (confidence intervals / bands)
- The engineering decision (risk classification) responding to user input

### 1.3 Required graphs

| Graph | Script | Purpose |
|---|---|---|
| Histogram + fitted distribution overlay | `07_visualizations.py` | Shows raw frequency distribution against the fitted model |
| Boxplot | `07_visualizations.py` | Spread, median, outliers |
| Q-Q plot | `07_visualizations.py` | Normality check, visual |
| Monte Carlo convergence plot | `07_visualizations.py` | Sensitivity analysis (§2.2) |
| Threshold sensitivity curve | `07_visualizations.py` | Probability across a range of thresholds, not just one point |
| Autocorrelation plot | `07_visualizations.py` | Clustering / independence check |

---

## 2. Team-added requirements (scope beyond the handout)

These were adopted deliberately to raise the ceiling of the project. They
are not optional extras that can be silently dropped — once assigned in
`assignments/PERSON<N>.md`, they are part of the deliverable for that role.
See `ARCHITECTURE.md` for exactly what output each of these must produce.

### 2.1 Multi-distribution model selection
Fit Normal, Log-Normal, Gamma, and Gumbel distributions. Select the best fit
using AIC and BIC (not eyeballing). Validate the winner with a holdout
train/test split. Owner: Person 1.

### 2.2 Simulation and resampling cross-checks
Monte Carlo simulation at 1,000 / 10,000 / 100,000 trials (convergence
check). Bootstrap resampling of the real dataset (distribution-free
probability estimate). Bootstrap confidence intervals for mean, SD, CV.
Owners: Person 1 (CIs), Person 5 (Monte Carlo + bootstrap probability).

### 2.3 Assumption testing
- **Independence**: autocorrelation test + run-length (heatwave clustering)
  analysis. Owner: Person 7.
- **Stationarity / trend**: linear regression of temperature vs. time,
  with residual diagnostics, and a clear statement of statistical vs.
  practical significance. Owner: Person 6.

### 2.4 Composite Heat Risk Index
A single synthesized decision number/classification combining exceedance
probability, trend adjustment, and clustering adjustment. This is the
project's answer to the assignment's "AI/engineering decision" requirement.
Owner: Person 1, using outputs from Persons 5, 6, and 7.

### 2.5 Return period framing
Probability re-expressed as "1-in-N-day event," matching how real
engineering/safety standards communicate risk. Owner: Person 5.

---

## 3. Assumptions that MUST be explicitly addressed in the report

Every one of these is a real statistical assumption this project's methods
depend on. None may be silently ignored — each needs at least one sentence
in `report/limitations.md` stating whether it holds, and how the team tested
it (cite the specific script/output that tested it).

1. **Independence** — daily temperatures are treated as independent
   observations by the core probability/distribution work. Tested by Person 7.
2. **Stationarity** — the climate/process generating the data is assumed not
   to be shifting during the observation window. Tested by Person 6.
3. **Representativeness** — the observation window is assumed typical, not
   an unusual stretch. Cannot be fully tested with a short record; must be
   stated as an acknowledged limitation.
4. **Model adequacy** — one of the four candidate distributions is assumed
   to adequately describe the data. Tested by Person 1 (AIC/BIC + holdout).
5. **Measurement quality** — the source archive is assumed accurate and
   consistently recorded. Documented (source named, access date recorded)
   but not independently verified. Person 3's responsibility to document.

---

## 4. Non-requirements (explicitly out of scope)

To protect the timeline, the following were considered and deliberately
**not** included. If someone wants to add one, it needs the whole team's
sign-off first, since it changes downstream integration:

- Extreme Value Theory (block maxima / Peak-Over-Threshold modelling) beyond
  including Gumbel as a candidate distribution
- Multi-city / comparative analysis
- A live backend server for the dashboard (see `ARCHITECTURE.md` §4 for why)
- Any authentication, user accounts, or persistence beyond the static
  `results.json` snapshot

---

## 5. Definition of done (per role)

A role is complete when:
1. Its script runs standalone with `python3 backend/scripts/<script>.py`
   with no errors, using either the placeholder or real dataset.
2. It calls `write_result()` (see `backend/scripts/common.py`) with exactly
   the section name and keys specified in its `assignments/PERSON<N>.md`.
3. Running `backend/scripts/run_pipeline.py` end-to-end includes that
   script without modification.
4. The person can explain, out loud, without notes, what every number their
   section produces means and how it was calculated. (This is the actual
   bar — "the code runs" is necessary but not sufficient.)
