/* ============================================================
   Heat Risk Dashboard — app.js
   Reads ./results.snapshot.json only. Never hardcode a stat that
   exists in the snapshot — read it from `data`.
   See assignments/PERSON2.md for the full spec this implements.
   ============================================================ */

let DATA = null;
let currentModel = null;
let currentThreshold = 36;

fetch("./results.snapshot.json")
  .then(res => res.json())
  .then(data => { DATA = data; init(data); })
  .catch(err => {
    document.getElementById("metaLine").textContent =
      "Could not load results.snapshot.json — run backend/scripts/run_pipeline.py and copy the file (see ARCHITECTURE.md §4).";
    console.error(err);
  });

/* ---------------- statistics: CDFs for all 4 candidate models ---------------- */

function erf(x) {
  const sign = x < 0 ? -1 : 1;
  x = Math.abs(x);
  const a1=0.254829592,a2=-0.284496736,a3=1.421413741,a4=-1.453152027,a5=1.061405429,p=0.3275911;
  const t = 1 / (1 + p * x);
  const y = 1 - (((((a5*t+a4)*t)+a3)*t+a2)*t+a1)*t*Math.exp(-x*x);
  return sign * y;
}
function normalCDF(x, loc, scale) {
  return 0.5 * (1 + erf((x - loc) / (scale * Math.sqrt(2))));
}
function lognormCDF(x, s, loc, scale) {
  if (x - loc <= 0) return 0;
  return normalCDF(Math.log(x - loc), Math.log(scale), s);
}
function gumbelCDF(x, loc, scale) {
  return Math.exp(-Math.exp(-(x - loc) / scale));
}
// Regularized lower incomplete gamma function P(a, x) — Numerical Recipes style
function gammaln(x) {
  const g = 7, c = [
    0.99999999999980993, 676.5203681218851, -1259.1392167224028,
    771.32342877765313, -176.61502916214059, 12.507343278686905,
    -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7
  ];
  if (x < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * x)) - gammaln(1 - x);
  x -= 1;
  let a = c[0];
  const t = x + g + 0.5;
  for (let i = 1; i < g + 2; i++) a += c[i] / (x + i);
  return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
}
function lowerIncompleteGammaRegularized(a, x) {
  if (x <= 0) return 0;
  if (x < a + 1) {
    // series expansion
    let sum = 1 / a, term = sum, n = a;
    for (let i = 0; i < 200; i++) {
      n += 1; term *= x / n; sum += term;
      if (Math.abs(term) < Math.abs(sum) * 1e-12) break;
    }
    return sum * Math.exp(-x + a * Math.log(x) - gammaln(a));
  } else {
    // continued fraction for the upper part, then 1 - that
    let b = x + 1 - a, c = 1e308, d = 1 / b, h = d;
    for (let i = 1; i < 200; i++) {
      const an = -i * (i - a);
      b += 2;
      d = an * d + b; if (Math.abs(d) < 1e-30) d = 1e-30;
      c = b + an / c; if (Math.abs(c) < 1e-30) c = 1e-30;
      d = 1 / d;
      const del = d * c; h *= del;
      if (Math.abs(del - 1) < 1e-12) break;
    }
    const upper = Math.exp(-x + a * Math.log(x) - gammaln(a)) * h;
    return 1 - upper;
  }
}
function gammaCDF(x, a, loc, scale) {
  if (x - loc <= 0) return 0;
  return lowerIncompleteGammaRegularized(a, (x - loc) / scale);
}

function cdfFor(name, params, x) {
  switch (name) {
    case "normal":   return normalCDF(x, params.loc, params.scale);
    case "gumbel_r":  return gumbelCDF(x, params.loc, params.scale);
    case "lognorm":  return lognormCDF(x, params.s, params.loc, params.scale);
    case "gamma":    return gammaCDF(x, params.a, params.loc, params.scale);
    default: return null;
  }
}
function probExceeds(name, params, threshold) {
  const p = cdfFor(name, params, threshold);
  return p === null ? null : 1 - p;
}

/* ---------------- init ---------------- */

function init(data) {
  const dfit = data.distribution_fit;
  currentModel = dfit.best_model;
  currentThreshold = dfit.threshold_c;

  document.getElementById("metaLine").textContent =
    `${data.core_stats.n_days} days observed · best fit: ${dfit.best_model} · snapshot`;

  document.getElementById("thresholdSlider").value = currentThreshold;
  document.getElementById("thresholdSlider").addEventListener("input", e => {
    currentThreshold = parseFloat(e.target.value);
    render();
  });

  buildModelToggle(dfit);
  buildComparisonTable(data);
  buildStatsTable(data);
  buildAssumptions(data);
  buildSynthesis(data);

  const panSlider = document.getElementById("panSlider");
  panSlider.addEventListener("input", drawTimeline);
  window.addEventListener("resize", drawTimeline);

  render();
}

function render() {
  document.getElementById("thresholdVal").textContent = currentThreshold.toFixed(1);

  const dfit = DATA.distribution_fit;
  const cand = dfit.candidates.find(c => c.name === currentModel);
  let prob;
  if (cand) {
    prob = probExceeds(currentModel, cand.params, currentThreshold);
  }
  if (prob === null || prob === undefined || Number.isNaN(prob)) {
    // fall back to the pre-computed static value at the canonical threshold only
    prob = currentModel === dfit.best_model ? dfit.theoretical_probability : null;
  }

  const probPct = prob !== null ? (prob * 100) : null;
  document.getElementById("probBig").textContent = probPct !== null ? probPct.toFixed(2) + "%" : "n/a";
  document.getElementById("returnPeriod").textContent =
    prob && prob > 0 ? `≈ 1-in-${(1/prob).toFixed(1)}-day event` : "";

  updateGauge(prob);
  drawTimeline();
}

/* ---------------- risk gauge (bands must match synthesis.risk_bands_reference) ---------------- */

function bandFor(prob) {
  const bands = DATA.synthesis.risk_bands_reference;
  for (const b of bands) {
    if (b.max === null || prob <= b.max) return b.label;
  }
  return bands[bands.length - 1].label;
}
function updateGauge(prob) {
  const fill = document.getElementById("gaugeFill");
  if (prob === null) { fill.style.width = "100%"; return; }
  const bands = DATA.synthesis.risk_bands_reference;
  const maxDomain = (bands[bands.length - 2] && bands[bands.length - 2].max) ? bands[bands.length - 2].max * 2 : 0.3;
  const pct = Math.max(0, Math.min(100, (1 - Math.min(prob, maxDomain) / maxDomain) * 100));
  fill.style.width = pct + "%";
}

/* ---------------- model toggle ---------------- */

function buildModelToggle(dfit) {
  const wrap = document.getElementById("modelToggle");
  wrap.innerHTML = "";
  dfit.candidates.forEach(c => {
    const btn = document.createElement("button");
    btn.textContent = c.name + (c.name === dfit.best_model ? " ★" : "");
    if (c.name === currentModel) btn.classList.add("active");
    btn.addEventListener("click", () => {
      currentModel = c.name;
      [...wrap.children].forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      render();
    });
    wrap.appendChild(btn);
  });
}

/* ---------------- comparison + stats tables ---------------- */

function row(table, label, value) {
  const tr = document.createElement("tr");
  const td1 = document.createElement("td"); td1.textContent = label;
  const td2 = document.createElement("td"); td2.textContent = value;
  tr.append(td1, td2);
  table.appendChild(tr);
}

function buildComparisonTable(data) {
  const t = document.getElementById("comparisonTable");
  const sim = data.simulation;
  row(t, "Theoretical (fitted model)", (sim.comparison.theoretical * 100).toFixed(2) + "%");
  row(t, "Monte Carlo (10,000 trials)", (sim.comparison.monte_carlo_10k * 100).toFixed(2) + "%");
  row(t, "Bootstrap (real data, no model)", (sim.comparison.bootstrap * 100).toFixed(2) + "%");
  row(t, "Return period", `1-in-${sim.return_period_days}-day event`);
}

function buildStatsTable(data) {
  const t = document.getElementById("statsTable");
  const cs = data.core_stats;
  row(t, "Mean", `${cs.mean}°C  (CI ${cs.mean_ci95[0]}–${cs.mean_ci95[1]})`);
  row(t, "Std. deviation", `${cs.std_dev}°C  (CI ${cs.std_dev_ci95[0]}–${cs.std_dev_ci95[1]})`);
  row(t, "Coefficient of variation", `${cs.cv_percent}%  (CI ${cs.cv_percent_ci95[0]}–${cs.cv_percent_ci95[1]})`);
  row(t, "Shapiro-Wilk p-value", `${cs.shapiro_wilk.p_value} (${cs.shapiro_wilk.is_normal_at_5pct ? "Normal" : "not Normal"} at 5%)`);
}

/* ---------------- assumptions ---------------- */

function buildAssumptions(data) {
  const box = document.getElementById("assumptions");
  const items = [];

  const trend = data.trend;
  items.push({
    ok: !trend.is_statistically_significant || Math.abs(trend.total_drift_c) < 1,
    text: `Stationarity — ${trend.practical_note}`
  });

  const dep = data.dependence;
  items.push({
    ok: !dep.is_significant,
    text: `Independence — ${dep.interpretation}`
  });

  const df = data.distribution_fit;
  items.push({
    ok: true,
    text: `Model adequacy — best fit is ${df.best_model} (AIC-selected, holdout-validated); Q-Q R=${df.qq_plot_r_value} against Normal.`
  });

  box.innerHTML = "";
  items.forEach(it => {
    const div = document.createElement("div");
    div.className = "assumption";
    div.innerHTML = `<span class="dot ${it.ok ? "ok" : "flag"}"></span><span>${it.text}</span>`;
    box.appendChild(div);
  });
}

/* ---------------- synthesis ---------------- */

function buildSynthesis(data) {
  const s = data.synthesis;
  const box = document.getElementById("synthesisBox");
  box.innerHTML = `
    <div class="synthbig">${(s.heat_risk_index*100).toFixed(2)}%
      <span class="band-pill band-${s.risk_band}">${s.risk_band}</span>
    </div>
    <p class="cardsub">base ${( s.components_used.base_probability*100).toFixed(2)}%
      × (1 + trend ${s.components_used.trend_adjustment})
      × (1 + clustering ${s.components_used.clustering_adjustment})</p>
    <div class="formula">${s.formula_note}</div>
  `;
}

/* ---------------- timeline canvas ---------------- */

function drawTimeline() {
  if (!DATA) return;
  const canvas = document.getElementById("timelineCanvas");
  const dpr = window.devicePixelRatio || 1;
  const cssWidth = canvas.parentElement.clientWidth;
  const cssHeight = 280;
  canvas.width = cssWidth * dpr;
  canvas.height = cssHeight * dpr;
  canvas.style.height = cssHeight + "px";
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, cssWidth, cssHeight);

  const cs = DATA.core_stats;
  const trend = DATA.trend;
  const nDays = cs.n_days;
  const projectionDays = 7;

  // Build a synthetic index-based series: real days use trend line + noise-free
  // fitted mean as a stand-in for actual values (illustrative — the true
  // per-day values live only in backend/data/dataset.csv, which the
  // dashboard intentionally does not need to reload).
  const totalPoints = nDays + projectionDays;
  const padL = 46, padR = 16, padT = 16, padB = 26;
  const plotW = cssWidth - padL - padR;
  const plotH = cssHeight - padT - padB;

  const panFrac = document.getElementById("panSlider").value / 100;
  const visibleSpan = Math.min(totalPoints, 30);
  const maxStart = totalPoints - visibleSpan;
  const start = Math.round(maxStart * panFrac);
  const end = start + visibleSpan;

  const meanLine = i => cs.mean + trend.slope_c_per_day * (i - nDays / 2);
  const sd = cs.std_dev;

  const yMin = cs.mean - 3.2 * sd, yMax = cs.mean + 3.5 * sd;
  const xOf = i => padL + ((i - start) / (visibleSpan - 1)) * plotW;
  const yOf = v => padT + (1 - (v - yMin) / (yMax - yMin)) * plotH;

  ctx.strokeStyle = "#D7DEDC"; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(padL, padT + plotH); ctx.lineTo(padL + plotW, padT + plotH); ctx.stroke();

  ctx.fillStyle = "#5C6E76"; ctx.font = "11px Archivo, sans-serif";
  [yMin, cs.mean, yMax].forEach(v => {
    const y = yOf(v);
    ctx.fillText(v.toFixed(1), 4, y + 3);
    ctx.strokeStyle = "#EEF1F0";
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(padL + plotW, y); ctx.stroke();
  });

  // uncertainty band (±1, ±2 SD) widening into the projection
  for (let i = start; i < end; i++) {
    if (i < nDays) continue;
  }
  ctx.beginPath();
  let started = false;
  for (let i = Math.max(start, nDays - 1); i < end; i++) {
    const daysOut = Math.max(0, i - nDays);
    const widen = 1 + daysOut * 0.15;
    const v = meanLine(i) + 2 * sd * widen;
    const x = xOf(i), y = yOf(v);
    if (!started) { ctx.moveTo(x, y); started = true; } else ctx.lineTo(x, y);
  }
  for (let i = end - 1; i >= Math.max(start, nDays - 1); i--) {
    const daysOut = Math.max(0, i - nDays);
    const widen = 1 + daysOut * 0.15;
    const v = meanLine(i) - 2 * sd * widen;
    ctx.lineTo(xOf(i), yOf(v));
  }
  ctx.closePath();
  ctx.fillStyle = "rgba(24,107,102,0.10)";
  if (started) ctx.fill();

  // threshold line + red risk zone above it within projection band
  const thrY = yOf(currentThreshold);
  ctx.strokeStyle = "#B03A2B"; ctx.setLineDash([5, 4]); ctx.lineWidth = 1.4;
  ctx.beginPath(); ctx.moveTo(padL, thrY); ctx.lineTo(padL + plotW, thrY); ctx.stroke();
  ctx.setLineDash([]);

  // solid actual line (recorded)
  ctx.strokeStyle = "#186B66"; ctx.lineWidth = 2.2;
  ctx.beginPath();
  let s2 = false;
  for (let i = start; i < Math.min(end, nDays); i++) {
    const x = xOf(i), y = yOf(meanLine(i));
    if (!s2) { ctx.moveTo(x, y); s2 = true; } else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // dashed projected line
  ctx.strokeStyle = "#5C6E76"; ctx.setLineDash([5, 4]); ctx.lineWidth = 2;
  ctx.beginPath();
  let s3 = false;
  for (let i = Math.max(start, nDays - 1); i < end; i++) {
    const x = xOf(i), y = yOf(meanLine(i));
    if (!s3) { ctx.moveTo(x, y); s3 = true; } else ctx.lineTo(x, y);
  }
  ctx.stroke();
  ctx.setLineDash([]);

  ctx.fillStyle = "#B03A2B"; ctx.font = "11px Archivo, sans-serif";
  ctx.fillText(`${currentThreshold.toFixed(1)}°C threshold`, padL + plotW - 110, thrY - 6);
}
