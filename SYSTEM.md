# SYSTEM.md

Environment setup, tech stack, conventions, and day-to-day workflow. Read
this to get your machine ready to actually run the project. For *what* to
build, see `REQUIREMENTS.md`. For *how the pieces fit together*, see
`ARCHITECTURE.md`.

---

## 1. Tech stack

| Layer | Technology | Notes |
|---|---|---|
| Backend / analysis | Python 3.10+ | `numpy`, `pandas`, `scipy`, `matplotlib` |
| Data interchange | JSON | one shared file, see `ARCHITECTURE.md` §3 |
| Frontend / dashboard | HTML + CSS + vanilla JS | optionally Chart.js via CDN; no build step (see `ARCHITECTURE.md` §5) |
| Report | Markdown, exported to PDF/Word at the end | `report/report.md` |
| Version control | Git + GitHub | see §5 below for branch/commit conventions |

No React, no Node.js build pipeline, no database, no backend server framework.
This is intentional — see `ARCHITECTURE.md` §5 for the reasoning.

---

## 2. One-time setup (everyone runs this once)

```bash
git clone <repo-url>
cd heat-risk-project

# Python dependencies
pip install numpy pandas scipy matplotlib --break-system-packages
# (drop --break-system-packages if you're using a virtualenv/conda env instead)

# Generate placeholder data so you can develop before real data lands
python3 backend/scripts/00_generate_sample_data.py

# Sanity check
python3 backend/scripts/common.py
```

You should see `Loaded dataset OK — 45 rows, ...` printed. If not, something
in your Python environment is missing — fix it before writing any analysis
code.

---

## 3. Running your own script

Every backend script is runnable standalone:

```bash
python3 backend/scripts/01_core_stats.py
```

This should:
1. Print a human-readable summary to the terminal (for your own sanity check)
2. Write/update `backend/output/results.json` with your section

If your script depends on another section (e.g. `03_simulation.py` needs
`distribution_fit`), and that section doesn't exist in `results.json` yet,
your script should fail with a clear message telling you which script to run
first — not a cryptic `KeyError`. See `assignments/PERSON<N>.md` for exactly
which upstream sections your script depends on.

---

## 4. Running the full pipeline

```bash
python3 backend/scripts/run_pipeline.py
```

Runs every backend script in the correct dependency order (see
`ARCHITECTURE.md` §6) and produces a complete `backend/output/results.json`.
Run this before generating figures, refreshing the dashboard, or updating
the report.

---

## 5. Git workflow

- **`main`** branch stays runnable at all times. Do not push code to `main`
  that breaks `run_pipeline.py`.
- Each person works on their own branch: `person1-backend`,
  `person7-frontend`, etc. — or feature branches like `distribution-fit`,
  `dashboard-slider`, whichever your team prefers, as long as it's clear.
- Open a pull request into `main` when your script runs cleanly end-to-end
  and satisfies the "definition of done" checklist in `REQUIREMENTS.md` §5.
- **Commit `backend/data/dataset.csv` once it's the real dataset** — don't
  leave the placeholder in the version everyone builds from.
- **`backend/output/results.json` and `frontend/results.snapshot.json`
  ARE committed to the repo** (not git-ignored), so that:
  - anyone can clone the repo and open the dashboard without running Python
  - the report always has a known-good snapshot to reference
  - you can `git diff` the JSON to see exactly what changed when someone
    updates their section

  Re-commit `results.json` (and refresh the frontend snapshot — see
  `ARCHITECTURE.md` §4) every time backend numbers change.

- `backend/output/figures/*.png` are also committed — Person 4 needs stable
  image paths to reference in the report.

---

## 6. File naming and code conventions

- Backend scripts are numbered by pipeline order (`01_`, `02_`, ...), not by
  person — see `ARCHITECTURE.md` §6 for exactly which script is whose.
- Every script has a module docstring at the top explaining: what it
  computes, what section of `results.json` it writes, and what upstream
  sections (if any) it reads. Copy the style already used in
  `common.py` and `00_generate_sample_data.py`.
- Import shared logic from `common.py`. Do not duplicate `load_dataset()`
  or the JSON-writing logic in your own script.
- Threshold value (currently `36.0°C`) is defined ONCE, and every script
  that needs it reads it from `results.json`'s `distribution_fit.threshold_c`
  (set by Person 1) rather than hardcoding it independently. If you need to
  change the threshold, change it in one place (`02_distribution_fit.py`)
  and rerun the pipeline.

---

## 7. Common pitfalls

- **"My script can't find results.json"** — you probably haven't run an
  upstream script yet. Check `ARCHITECTURE.md` §6 for the required order,
  or just run `run_pipeline.py` which handles ordering for you.
- **"The dashboard shows old numbers"** — you forgot to refresh
  `frontend/results.snapshot.json` after rerunning the pipeline. See
  `ARCHITECTURE.md` §4.
- **"I get different Monte Carlo numbers each time I run it"** — set a fixed
  random seed (see how `00_generate_sample_data.py` and the existing scripts
  do it) so results are reproducible for the report and demo.
- **"scipy.stats.lognorm.fit gives weird parameters"** — for temperature
  data (which isn't naturally zero-anchored), you may need to constrain or
  shift the fit. Flag this in the team chat rather than silently working
  around it — it affects the whole `distribution_fit` section's integrity.
