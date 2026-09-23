# CLAUDE.md

Instructions for any AI assistant (Claude Code, or Claude via chat/artifacts)
working in this repository. If you are a human, this file is still useful —
it's a concise summary of the whole project's rules in one place.

---

## What this repo is

A 7-person student statistics project: "Variability and Extreme Temperature
Analysis — Statistical Identification of High-Temperature Risk." A Python
backend computes real statistics on temperature data; a static HTML/CSS/JS
dashboard visualizes it interactively; a written report explains it. Full
detail in `REQUIREMENTS.md`, `ARCHITECTURE.md`, `SYSTEM.md`.

## Read these first, in this order

1. `REQUIREMENTS.md` — what must be delivered and why
2. `ARCHITECTURE.md` — the exact `results.json` schema and how pieces connect
3. `SYSTEM.md` — how to run things, conventions
4. The specific `assignments/PERSON<N>.md` for whichever piece you're helping with

## Non-negotiable rules when writing or editing code here

1. **Never duplicate `load_dataset()`, `write_result()`, or `read_results()`.**
   They live in `backend/scripts/common.py` — import from it. If you think
   you need to change `common.py` itself, that's a whole-team decision, not
   a unilateral edit — flag it instead of just doing it.

2. **Never write outside your assigned section of `results.json`.** Check
   `ARCHITECTURE.md` §3 for the exact schema. If a script for "Person 6"
   writes into the `"dependence"` key (which belongs to Person 7), that's a
   bug, not a style choice — fix it.

3. **Never hardcode a value that already exists in `results.json`.** E.g.
   the extreme-heat threshold (`36.0°C`) is set once in
   `02_distribution_fit.py` and read from there everywhere else. If you spot
   a hardcoded duplicate of a shared value, that's worth fixing, flagged in
   the PR description.

4. **Every backend script must be runnable standalone** with
   `python3 backend/scripts/<name>.py` and produce a clear, human-readable
   terminal summary — not just silently write JSON. This is both a debugging
   aid and part of `REQUIREMENTS.md`'s "definition of done."

5. **The frontend never calls a live Python process.** It reads
   `frontend/results.snapshot.json` only. Do not add a Flask/FastAPI server
   as a "quick fix" for the dashboard — see `ARCHITECTURE.md` §4 for why
   this was deliberately rejected.

6. **Do not silently drop a required deliverable from `REQUIREMENTS.md`**
   (e.g. skipping the holdout validation, or skipping a required graph)
   even if it would make a task faster. If scope needs to shrink, that's
   flagged to the team, not decided unilaterally by whoever's coding.

7. **Preserve reproducibility.** Any simulation (Monte Carlo, bootstrap)
   must use a fixed random seed so numbers don't change between runs — the
   report and dashboard need stable, citable figures.

8. **Match the tone of existing docstrings/comments** when adding code —
   they explain *why*, not just *what*, because a teammate (or their
   professor, if asked) needs to be able to understand and defend every
   line, not just run it.

## When asked to "build Person N's script"

1. Open `assignments/PERSON<N>.md` and follow its schema exactly.
2. Open `ARCHITECTURE.md` §3 and confirm the exact keys expected in that
   person's `results.json` section.
3. Write the script into `backend/scripts/` at the filename `ARCHITECTURE.md`
   §2/§6 specifies for that role — do not invent a different filename.
4. Test it runs standalone against the placeholder dataset
   (`backend/scripts/00_generate_sample_data.py` output) before assuming
   it's done.
5. Confirm `python3 backend/scripts/run_pipeline.py` still runs end-to-end
   after adding the script.

## When asked to "update the dashboard" or "update the report"

Both consume `results.json` (dashboard via the frozen
`frontend/results.snapshot.json`, per `ARCHITECTURE.md` §4). Read the
current schema from that file directly rather than assuming — sections get
extended over the project's life, and the file on disk is more current than
this document's example in `ARCHITECTURE.md` §3 might be by the time you're
reading it.

## Things AI assistants should flag rather than silently fix

- A `results.json` section that doesn't match its documented schema
- A script that hardcodes the threshold, dataset path, or another script's
  output instead of reading it from `results.json`
- Any addition of a build step, server dependency, or new major library not
  already listed in `SYSTEM.md` §1 — the stack is intentionally minimal
- Placeholder data (`00_generate_sample_data.py`'s output) still being used
  in a script that's about to be treated as "final"
