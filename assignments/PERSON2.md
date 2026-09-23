# PERSON 2 — Frontend Lead
**Role:** Build the interactive dashboard — the project's live demonstration.
**Files you own:** `frontend/index.html`, `frontend/style.css`, `frontend/app.js`
**You read (never write) `frontend/results.snapshot.json`** — a frozen copy
of `backend/output/results.json` (see `ARCHITECTURE.md` §4 for why it's a
snapshot, not a live server call).

Read `ARCHITECTURE.md` §3–§5 in full before starting — this doc assumes you
have.

---

## 1. What you're actually building

Not a static report — an instrument. Someone with zero statistics
background should be able to drag one slider and immediately understand
"how likely is a dangerously hot day," while someone who DOES know
statistics can toggle between distribution models and see the team tested
its assumptions instead of trusting one blindly.

## 2. Tech stack for this piece

Plain HTML + CSS + vanilla JavaScript. No build step, no npm install, no
React. See `ARCHITECTURE.md` §5 for the full reasoning — in short: this
needs to open and work instantly on a random classroom laptop with zero
setup, and it cannot depend on a running server that might fail mid-demo.
You may load Chart.js from a CDN if you want easier charting, but the core
interactivity (slider math, gauge color) should be plain JS you understand
line by line, since you may be asked to explain it live.

## 3. Layout

1. **Header** — title + location/date range (pull from `_meta` in the snapshot)
2. **Main timeline graph** — solid line = actual recorded temps, dashed
   line + shaded uncertainty band = projected days beyond the record,
   horizontal threshold line, red-shaded region wherever the projection
   band crosses above threshold
3. **Scroll/range control** below the graph — drag to pan the visible window
4. **Threshold slider** — dragging it updates: the horizontal line on the
   graph, the shaded risk region, and the live probability number
5. **Risk gauge** — simple green/yellow/red bar or dial reflecting current probability
6. **Distribution model toggle** — buttons/dropdown: Normal / Log-Normal /
   Gamma / Gumbel. Switching model reshapes the projection band and updates
   the probability using that model's parameters from the snapshot
7. **Probability comparison panel** — theoretical vs. Monte Carlo vs.
   bootstrap, read directly from `simulation.comparison` in the snapshot
   (these three numbers do NOT change when you move the slider — they're
   fixed at the canonical threshold; only the "theoretical" curve output
   recomputes live as the slider moves, since Monte Carlo/bootstrap were
   pre-computed at build time, not something JS can regenerate live)
8. **Stats footer** — mean/SD/CV from `core_stats`, each shown with its CI:
   e.g. `Mean: 32.97°C (95% CI: 32.31–33.62)`

## 4. Data source

On page load:
```js
fetch('./results.snapshot.json')
  .then(res => res.json())
  .then(data => initDashboard(data));
```
Everything the page displays comes from this one object. Never hardcode a
number that exists in the snapshot — if you catch yourself typing `32.97`
directly into your JS, that value should be read from `data.core_stats.mean` instead.

**Refreshing the snapshot** (do this whenever backend numbers change):
```bash
python3 backend/scripts/run_pipeline.py
cp backend/output/results.json frontend/results.snapshot.json
```

## 5. Reference JS: recomputing probability live from a fitted model

The slider needs to recompute `P(X > threshold)` in-browser as the user
drags it, using whichever distribution is currently toggled. You do not
need to derive these formulas — here is a standard, correct reference
implementation for the Normal CDF (the most common case; Log-Normal reuses
this by transforming with `Math.log`, Gamma and Gumbel have their own
closed forms you can look up if you support toggling to them for live
recompute — at minimum, support live recompute for the model marked
`best_model` in the snapshot, and it's fine for the other toggle options to
just display their pre-computed `theoretical_probability` from
`distribution_fit.candidates` without live slider recompute if time is short):

```js
// Standard normal CDF via Abramowitz-Stegun approximation (accurate to ~1e-7)
function normalCDF(x, mean, stdDev) {
  const z = (x - mean) / (stdDev * Math.sqrt(2));
  return 0.5 * (1 + erf(z));
}

function erf(x) {
  // Abramowitz-Stegun formula 7.1.26
  const sign = x < 0 ? -1 : 1;
  x = Math.abs(x);
  const a1 =  0.254829592, a2 = -0.284496736, a3 = 1.421413741;
  const a4 = -1.453152027, a5 =  1.061405429, p  = 0.3275911;
  const t = 1 / (1 + p * x);
  const y = 1 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1) * t * Math.exp(-x*x);
  return sign * y;
}

// P(X > threshold) for a Normal distribution:
function probabilityExceeds(threshold, mean, stdDev) {
  return 1 - normalCDF(threshold, mean, stdDev);
}

// Usage, reading params from the snapshot's distribution_fit.candidates
// (find the entry whose name matches the currently toggled model):
const normalParams = data.distribution_fit.candidates.find(c => c.name === "normal").params;
const liveProbability = probabilityExceeds(sliderValue, normalParams.loc, normalParams.scale);
```

Do not need to reimplement Log-Normal/Gamma/Gumbel CDFs from scratch under
time pressure — it's acceptable for the MVP to support live recompute only
for whichever model is `distribution_fit.best_model`, with other toggle
options shown as static pre-computed values. State clearly in your PR
description which models support live slider recompute vs. static display
only, so Person 4 describes the demo accurately in the demo script.

## 6. Risk gauge color logic

Reuse the same risk bands Person 1 defines in `synthesis.risk_band` — don't
invent your own thresholds independently. Read the band cutoffs from
wherever Person 1 documents them (check `results.json["synthesis"]` and
`assignments/PERSON1.md` §4 for the band definitions) so the gauge always
agrees with the "official" engineering decision, rather than showing a
different color than what the report claims.

## 7. Definition of done

- [ ] Loads `results.snapshot.json` on open, zero hardcoded statistics
- [ ] Threshold slider live-updates probability, shaded region, and gauge
      for at least the `best_model` distribution
- [ ] Distribution toggle switches between all 4 candidates (live recompute
      for best_model, static display acceptable for the rest — documented)
- [ ] Probability comparison panel shows theoretical/Monte Carlo/bootstrap
      from the snapshot
- [ ] Works opened directly as a local file (`file://`) with no server running
- [ ] **Refresh `results.snapshot.json` from the REAL pipeline output before
      the actual demo** — the current snapshot is built on placeholder
      data; see `ARCHITECTURE.md` §4 for the exact refresh command. Also
      give the layout an actual design pass once real numbers are in —
      the current build is a functional first draft, not a polished result
- [ ] You can explain what every number on screen means and where in
      `results.json` it came from, unscripted
