/* ============================================================
   HeatSense — app.js
   Reads ./results.snapshot.json only. Never hardcode a stat that
   exists in the snapshot — read it from `data`.
   ============================================================ */

'use strict';

let DATA = null;
let currentModel = null;
let currentThreshold = 36;
let sensitivityChart = null;

/* ── Fetch snapshot ─────────────────────────────────────────── */
fetch('./results.snapshot.json')
  .then(r => r.json())
  .then(data => { DATA = data; init(data); })
  .catch(err => {
    document.getElementById('metaLine').textContent =
      'Could not load results.snapshot.json — run backend/scripts/run_pipeline.py and copy the file (see ARCHITECTURE.md §4).';
    console.error(err);
  });

/* ── CDF implementations ────────────────────────────────────── */

function erf(x) {
  const sign = x < 0 ? -1 : 1;
  x = Math.abs(x);
  const a1=0.254829592, a2=-0.284496736, a3=1.421413741, a4=-1.453152027, a5=1.061405429, p=0.3275911;
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
    let sum = 1 / a, term = sum, n = a;
    for (let i = 0; i < 200; i++) {
      n += 1; term *= x / n; sum += term;
      if (Math.abs(term) < Math.abs(sum) * 1e-12) break;
    }
    return sum * Math.exp(-x + a * Math.log(x) - gammaln(a));
  } else {
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
    return 1 - Math.exp(-x + a * Math.log(x) - gammaln(a)) * h;
  }
}

function gammaCDF(x, a, loc, scale) {
  if (x - loc <= 0) return 0;
  return lowerIncompleteGammaRegularized(a, (x - loc) / scale);
}

function cdfFor(name, params, x) {
  switch (name) {
    case 'normal':  return normalCDF(x, params.loc, params.scale);
    case 'gumbel_r': return gumbelCDF(x, params.loc, params.scale);
    case 'lognorm': return lognormCDF(x, params.s, params.loc, params.scale);
    case 'gamma':   return gammaCDF(x, params.a, params.loc, params.scale);
    default: return null;
  }
}

function probExceeds(name, params, threshold) {
  const p = cdfFor(name, params, threshold);
  return p === null ? null : 1 - p;
}

function modelLabel(name) {
  return ({ normal: 'Normal', lognorm: 'Log-normal', gamma: 'Gamma', gumbel_r: 'Gumbel' })[name] || name;
}

/* ── Risk band helpers ──────────────────────────────────────── */

function bandFor(prob) {
  const synth = DATA && DATA.synthesis;
  const bands = synth && synth.risk_bands_reference;
  if (!bands) {
    if (prob <= 0.05) return 'low';
    if (prob <= 0.15) return 'moderate';
    return 'high';
  }
  for (const b of bands) {
    if (b.max === null || prob <= b.max) return b.label;
  }
  return bands[bands.length - 1].label;
}

function updateGauge(prob) {
  const fill = document.getElementById('gaugeFill');
  if (prob === null) { fill.style.width = '100%'; return; }
  const synth = DATA && DATA.synthesis;
  const bands = synth && synth.risk_bands_reference;
  const maxDomain = (bands && bands[bands.length - 2] && bands[bands.length - 2].max)
    ? bands[bands.length - 2].max * 2 : 0.3;
  const pct = Math.max(0, Math.min(100, (1 - Math.min(prob, maxDomain) / maxDomain) * 100));
  fill.style.width = pct + '%';
}

/* ── Slider gradient update ─────────────────────────────────── */
function updateSliderGradient() {
  const slider = document.getElementById('thresholdSlider');
  const min = parseFloat(slider.min);
  const max = parseFloat(slider.max);
  const val = parseFloat(slider.value);
  const pct = ((val - min) / (max - min)) * 100;
  slider.style.background = `linear-gradient(90deg, var(--red) ${pct}%, var(--border) ${pct}%)`;
}

/* ── Init ───────────────────────────────────────────────────── */

function init(data) {
  const dfit = data.distribution_fit;
  currentModel = dfit.best_model;
  currentThreshold = dfit.threshold_c;

  // Topbar/sidebar metadata
  const generatedAt = data._meta && data._meta.generated_at
    ? new Date(data._meta.generated_at).toLocaleDateString('en-GB', { day:'numeric', month:'short', year:'numeric' })
    : 'snapshot';
  const metaText = `${data.core_stats.n_days} days · best fit: ${modelLabel(dfit.best_model)} · ${generatedAt}`;
  document.getElementById('metaLine').textContent = metaText;
  const topbarStatus = document.getElementById('topbarStatus');
  if (topbarStatus) topbarStatus.textContent = generatedAt;

  // Threshold slider
  const slider = document.getElementById('thresholdSlider');
  slider.value = currentThreshold;
  updateSliderGradient();
  slider.addEventListener('input', e => {
    currentThreshold = parseFloat(e.target.value);
    updateSliderGradient();
    render();
  });

  // Mobile menu toggle
  const menuBtn = document.getElementById('menuBtn');
  const sidebar = document.getElementById('sidebar');
  if (menuBtn && sidebar) {
    menuBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
    // Close sidebar when clicking outside
    document.addEventListener('click', e => {
      if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== menuBtn) {
        sidebar.classList.remove('open');
      }
    });
  }

  buildModelToggle(dfit);
  buildForecast(data);
  buildComparisonTable(data);
  buildStatsTable(data);
  buildAssumptions(data);
  buildSynthesis(data);
  buildSensitivityChart(data);
  setupNavHighlighting();

  const panSlider = document.getElementById('panSlider');
  panSlider.addEventListener('input', drawTimeline);
  window.addEventListener('resize', drawTimeline);

  render();
}

/* ── Render (called on every threshold/model change) ────────── */

function render() {
  document.getElementById('thresholdVal').textContent = currentThreshold.toFixed(1);

  const dfit = DATA.distribution_fit;
  const cand = dfit.candidates.find(c => c.name === currentModel);
  let prob;
  if (cand) prob = probExceeds(currentModel, cand.params, currentThreshold);
  if (prob === null || prob === undefined || Number.isNaN(prob)) {
    prob = currentModel === dfit.best_model ? dfit.theoretical_probability : null;
  }

  const probPct = prob !== null ? prob * 100 : null;
  document.getElementById('probBig').textContent =
    probPct !== null ? probPct.toFixed(2) + '%' : 'n/a';
  document.getElementById('returnPeriod').textContent =
    prob && prob > 0 ? `≈ 1-in-${(1 / prob).toFixed(1)}-day event` : '';

  const band = prob !== null ? bandFor(prob) : 'unavailable';
  const bandEl = document.getElementById('riskBand');
  bandEl.textContent = band.charAt(0).toUpperCase() + band.slice(1);
  bandEl.className = `risk-band-pill band-${band}`;

  document.getElementById('modelNote').textContent =
    currentModel === dfit.best_model
      ? `${modelLabel(currentModel)} · live probability recompute from fitted parameters`
      : `${modelLabel(currentModel)} · showing fitted probability from snapshot`;

  updateTakeaway(prob);
  buildForecast(DATA);
  updateGauge(prob);
  drawTimeline();
}

/* ── 7-day forecast ─────────────────────────────────────────── */

function buildForecast(data) {
  const grid = document.getElementById('forecastGrid');
  const note = document.getElementById('forecastNote');
  const dfit = data.distribution_fit;
  const candidate = dfit.candidates.find(item => item.name === currentModel);
  if (!candidate) return;

  const cs = data.core_stats;
  const trend = data.trend;
  const cards = [];

  for (let day = 1; day <= 7; day++) {
    const index = cs.n_days + day - 1;
    const expected = cs.mean + trend.slope_c_per_day * (index - cs.n_days / 2);
    const spread = candidate.params.scale * (1 + (day - 1) * 0.15);
    const chance = probExceeds(currentModel, candidate.params, currentThreshold);
    const isHot = chance !== null && chance > 0.15;

    cards.push(`
      <div class="forecast-day${isHot ? ' hot' : ''}" style="animation-delay:${(day-1)*0.05}s">
        <span class="forecast-day-label">Day +${day}</span>
        <strong class="forecast-day-temp">${expected.toFixed(1)}°C</strong>
        <span class="forecast-day-range">${Math.max(0, expected - spread).toFixed(1)}–${(expected + spread).toFixed(1)}°C</span>
        <span class="forecast-day-prob">${chance !== null ? (chance * 100).toFixed(1) : '—'}% over threshold</span>
      </div>
    `);
  }

  grid.innerHTML = cards.join('');
  note.textContent = `${modelLabel(currentModel)} projection · uncertainty widens by day`;
}

/* ── Takeaway / insight card ────────────────────────────────── */

function updateTakeaway(prob) {
  const cs = DATA.core_stats;
  const trend = DATA.trend;

  const residuals = (trend && trend.residuals) ? trend.residuals : [];
  const recorded = residuals.map((residual, index) =>
    cs.mean + trend.slope_c_per_day * (index - cs.n_days / 2) + residual
  );

  const crossings = recorded.filter(v => v > currentThreshold).length;
  const peak = recorded.length > 0 ? Math.max(...recorded) : cs.mean;
  const percent = prob === null ? 'n/a' : `${(prob * 100).toFixed(1)}%`;
  const cadence = prob && prob > 0 ? `about once every ${(1 / prob).toFixed(1)} days` : 'very rarely';

  document.getElementById('takeawayTitle').textContent =
    `${percent} chance of crossing ${currentThreshold.toFixed(1)}°C on any given day`;
  document.getElementById('takeawayText').textContent =
    `That is ${cadence}. In the recorded sample, ${crossings} of ${cs.n_days} days crossed this threshold.`;
  document.getElementById('observedCrossings').textContent = `${crossings}/${cs.n_days}`;
  document.getElementById('observedPeak').textContent = `${peak.toFixed(1)}°C`;
}

/* ── Model toggle ────────────────────────────────────────────── */

function buildModelToggle(dfit) {
  const wrap = document.getElementById('modelToggle');
  wrap.innerHTML = '';
  dfit.candidates.forEach(c => {
    const btn = document.createElement('button');
    btn.className = `model-btn${c.name === currentModel ? ' active' : ''}${c.name === dfit.best_model ? ' best' : ''}`;
    btn.textContent = modelLabel(c.name);
    btn.setAttribute('aria-pressed', c.name === currentModel);
    btn.title = `AIC: ${c.aic}  |  BIC: ${c.bic}`;
    btn.addEventListener('click', () => {
      currentModel = c.name;
      [...wrap.children].forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-pressed', 'false');
      });
      btn.classList.add('active');
      btn.setAttribute('aria-pressed', 'true');
      render();
    });
    wrap.appendChild(btn);
  });
}

/* ── Comparison + stats tables ───────────────────────────────── */

function row(table, label, value) {
  const tr = document.createElement('tr');
  const td1 = document.createElement('td'); td1.textContent = label;
  const td2 = document.createElement('td'); td2.textContent = value;
  tr.append(td1, td2);
  table.appendChild(tr);
}

function buildComparisonTable(data) {
  const t = document.getElementById('comparisonTable');
  const sim = data.simulation;
  row(t, 'Theoretical (fitted model)', (sim.comparison.theoretical * 100).toFixed(2) + '%');
  row(t, 'Monte Carlo (10,000 trials)', (sim.comparison.monte_carlo_10k * 100).toFixed(2) + '%');
  row(t, 'Bootstrap (real data, no model)', (sim.comparison.bootstrap * 100).toFixed(2) + '%');
  row(t, 'Return period', `1-in-${sim.return_period_days}-day event`);
}

function buildStatsTable(data) {
  const t = document.getElementById('statsTable');
  const cs = data.core_stats;
  row(t, 'Mean', `${cs.mean}°C  (CI ${cs.mean_ci95[0]}–${cs.mean_ci95[1]})`);
  row(t, 'Std. deviation', `${cs.std_dev}°C  (CI ${cs.std_dev_ci95[0]}–${cs.std_dev_ci95[1]})`);
  row(t, 'Coefficient of variation', `${cs.cv_percent}%  (CI ${cs.cv_percent_ci95[0]}–${cs.cv_percent_ci95[1]})`);
  row(t, 'Shapiro-Wilk p-value', `${cs.shapiro_wilk.p_value} (${cs.shapiro_wilk.is_normal_at_5pct ? 'Normal' : 'Not normal'} at 5%)`);
  row(t, 'Sample size', `${cs.n_days} days`);
}

/* ── Assumption checks ───────────────────────────────────────── */

function buildAssumptions(data) {
  const box = document.getElementById('assumptions');
  const items = [];

  const trend = data.trend;
  items.push({
    ok: !trend.is_statistically_significant || Math.abs(trend.total_drift_c || 0) < 1,
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
    text: `Model adequacy — best fit is ${modelLabel(df.best_model)} (AIC-selected, holdout-validated); Q-Q R=${df.qq_plot_r_value}.`
  });

  box.innerHTML = '';
  items.forEach(it => {
    const div = document.createElement('div');
    div.className = 'assumption';
    div.innerHTML = `<span class="dot ${it.ok ? 'ok' : 'flag'}"></span><span>${it.text}</span>`;
    box.appendChild(div);
  });
}

/* ── Synthesis / composite score ─────────────────────────────── */

function buildSynthesis(data) {
  const s = data.synthesis;
  const box = document.getElementById('synthesisBox');
  box.innerHTML = `
    <div class="synth-big">${(s.heat_risk_index * 100).toFixed(2)}%
      <span class="band-pill-sm band-${s.risk_band}">${s.risk_band}</span>
    </div>
    <div class="synth-components">
      <div class="synth-component">
        <span>Base probability</span>
        <span>${(s.components_used.base_probability * 100).toFixed(2)}%</span>
      </div>
      <div class="synth-component">
        <span>Trend adjustment</span>
        <span>×(1 + ${s.components_used.trend_adjustment})</span>
      </div>
      <div class="synth-component">
        <span>Clustering adjustment</span>
        <span>×(1 + ${s.components_used.clustering_adjustment})</span>
      </div>
    </div>
    <p class="synth-formula">${s.formula_note}</p>
  `;
}

/* ── Sensitivity chart (Chart.js) ────────────────────────────── */

function buildSensitivityChart(data) {
  const canvas = document.getElementById('sensitivityChart');
  if (!canvas || typeof Chart === 'undefined') return;

  const sens = data.simulation && data.simulation.threshold_sensitivity;
  if (!sens) return;

  const labels = sens.thresholds_c.map(t => `${t}°C`);
  const probs  = sens.probabilities.map(p => +(p * 100).toFixed(2));
  const colors = probs.map(p =>
    p <= 5  ? 'rgba(39,174,96,0.7)'  :
    p <= 15 ? 'rgba(230,126,34,0.7)' :
              'rgba(224,90,58,0.7)'
  );
  const borderColors = probs.map(p =>
    p <= 5  ? 'rgb(39,174,96)'  :
    p <= 15 ? 'rgb(230,126,34)' :
              'rgb(224,90,58)'
  );

  if (sensitivityChart) sensitivityChart.destroy();

  sensitivityChart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Exceedance probability (%)',
        data: probs,
        backgroundColor: colors,
        borderColor: borderColors,
        borderWidth: 2,
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.parsed.y.toFixed(2)}% chance of exceeding ${ctx.label}`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 12, family: 'Inter, sans-serif' }, color: '#7a8fa0' }
        },
        y: {
          grid: { color: 'rgba(0,0,0,.05)' },
          ticks: {
            font: { size: 11, family: 'Inter, sans-serif' },
            color: '#7a8fa0',
            callback: v => v + '%'
          },
          title: {
            display: true,
            text: 'Exceedance probability (%)',
            color: '#7a8fa0',
            font: { size: 11, family: 'Inter, sans-serif' }
          }
        }
      }
    }
  });
}

/* ── Sidebar nav scroll highlighting ─────────────────────────── */

function setupNavHighlighting() {
  const sections = document.querySelectorAll('.section[id]');
  const navLinks  = document.querySelectorAll('.nav-item[data-section]');
  if (!sections.length || !navLinks.length) return;

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navLinks.forEach(link => {
          link.classList.toggle('active', link.dataset.section === entry.target.id);
        });
      }
    });
  }, { threshold: 0.35 });

  sections.forEach(s => observer.observe(s));
}

/* ── Timeline canvas ─────────────────────────────────────────── */

function drawTimeline() {
  if (!DATA) return;
  const canvas = document.getElementById('timelineCanvas');
  const dpr = window.devicePixelRatio || 1;
  const cssWidth  = canvas.parentElement.clientWidth - 40; // account for padding
  const cssHeight = 280;
  canvas.width  = cssWidth * dpr;
  canvas.height = cssHeight * dpr;
  canvas.style.width  = cssWidth + 'px';
  canvas.style.height = cssHeight + 'px';
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, cssWidth, cssHeight);

  const cs    = DATA.core_stats;
  const trend = DATA.trend;
  const nDays = cs.n_days;
  const projectionDays = 7;
  const totalPoints    = nDays + projectionDays;
  const padL = 50, padR = 20, padT = 20, padB = 30;
  const plotW = cssWidth - padL - padR;
  const plotH = cssHeight - padT - padB;

  const panFrac     = document.getElementById('panSlider').value / 100;
  const visibleSpan = Math.min(totalPoints, 30);
  const maxStart    = totalPoints - visibleSpan;
  const start       = Math.round(maxStart * panFrac);
  const end         = start + visibleSpan;

  const meanLine  = i => cs.mean + trend.slope_c_per_day * (i - nDays / 2);
  const residuals = trend.residuals || [];
  const actualValue = i => meanLine(i) + (residuals[i] || 0);
  const sd = cs.std_dev;

  const yMin = cs.mean - 3.5 * sd;
  const yMax = cs.mean + 4.0 * sd;
  const xOf  = i => padL + ((i - start) / (visibleSpan - 1)) * plotW;
  const yOf  = v => padT + (1 - (v - yMin) / (yMax - yMin)) * plotH;

  // Background grid
  const gridVals = [yMin, cs.mean - sd, cs.mean, cs.mean + sd, yMax];
  gridVals.forEach(v => {
    const y = yOf(v);
    ctx.strokeStyle = '#e3e8ed';
    ctx.lineWidth = 1;
    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(padL + plotW, y);
    ctx.stroke();

    ctx.fillStyle = '#7a8fa0';
    ctx.font = '11px Inter, Segoe UI, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(v.toFixed(1), padL - 6, y + 4);
  });

  // Vertical grid lines (day markers)
  for (let i = start; i < end; i += Math.ceil(visibleSpan / 6)) {
    const x = xOf(i);
    ctx.strokeStyle = '#f0f2f4';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, padT);
    ctx.lineTo(x, padT + plotH);
    ctx.stroke();
    ctx.fillStyle = '#7a8fa0';
    ctx.font = '10px Inter, Segoe UI, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`d${i + 1}`, x, padT + plotH + 18);
  }

  // Uncertainty band (projection)
  ctx.beginPath();
  let started = false;
  for (let i = Math.max(start, nDays - 1); i < end; i++) {
    const daysOut = Math.max(0, i - nDays);
    const widen   = 1 + daysOut * 0.15;
    const v = meanLine(i) + 2 * sd * widen;
    const x = xOf(i), y = yOf(Math.min(v, yMax));
    if (!started) { ctx.moveTo(x, y); started = true; } else ctx.lineTo(x, y);
  }
  for (let i = end - 1; i >= Math.max(start, nDays - 1); i--) {
    const daysOut = Math.max(0, i - nDays);
    const widen   = 1 + daysOut * 0.15;
    const v = meanLine(i) - 2 * sd * widen;
    ctx.lineTo(xOf(i), yOf(Math.max(v, yMin)));
  }
  ctx.closePath();
  ctx.fillStyle = 'rgba(41,128,185,0.08)';
  if (started) ctx.fill();

  // Risk band above threshold in projection
  ctx.beginPath();
  let riskStarted = false;
  for (let i = Math.max(start, nDays - 1); i < end; i++) {
    const daysOut = Math.max(0, i - nDays);
    const widen   = 1 + daysOut * 0.15;
    const upper   = meanLine(i) + 2 * sd * widen;
    const x = xOf(i), y = yOf(Math.max(currentThreshold, Math.min(upper, yMax)));
    if (!riskStarted) { ctx.moveTo(x, y); riskStarted = true; } else ctx.lineTo(x, y);
  }
  for (let i = end - 1; i >= Math.max(start, nDays - 1); i--) {
    const daysOut = Math.max(0, i - nDays);
    const widen   = 1 + daysOut * 0.15;
    const upper   = meanLine(i) + 2 * sd * widen;
    ctx.lineTo(xOf(i), yOf(Math.min(upper, currentThreshold)));
  }
  ctx.closePath();
  ctx.fillStyle = 'rgba(224,90,58,0.12)';
  if (riskStarted) ctx.fill();

  // Threshold line
  const thrY = yOf(currentThreshold);
  ctx.strokeStyle = '#e05a3a';
  ctx.setLineDash([6, 4]);
  ctx.lineWidth = 1.8;
  ctx.beginPath();
  ctx.moveTo(padL, thrY);
  ctx.lineTo(padL + plotW, thrY);
  ctx.stroke();
  ctx.setLineDash([]);

  // Label threshold
  ctx.fillStyle = '#e05a3a';
  ctx.font = 'bold 11px Inter, Segoe UI, sans-serif';
  ctx.textAlign = 'right';
  ctx.fillText(`${currentThreshold.toFixed(1)}°C`, padL + plotW, thrY - 6);

  // Recorded line (solid blue)
  ctx.strokeStyle = '#2980b9';
  ctx.lineWidth = 2.5;
  ctx.lineJoin = 'round';
  ctx.beginPath();
  let s2 = false;
  for (let i = start; i < Math.min(end, nDays); i++) {
    const x = xOf(i), y = yOf(actualValue(i));
    if (!s2) { ctx.moveTo(x, y); s2 = true; } else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // Data points on recorded line
  for (let i = start; i < Math.min(end, nDays); i++) {
    const value  = actualValue(i);
    const isHot  = value > currentThreshold;
    const radius = isHot ? 5 : 3;
    ctx.beginPath();
    ctx.fillStyle = isHot ? '#e05a3a' : '#fff';
    ctx.strokeStyle = isHot ? '#e05a3a' : '#2980b9';
    ctx.lineWidth = 2;
    ctx.arc(xOf(i), yOf(value), radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }

  // Projected line (dashed green)
  ctx.strokeStyle = '#27ae60';
  ctx.setLineDash([6, 4]);
  ctx.lineWidth = 2;
  ctx.beginPath();
  let s3 = false;
  for (let i = Math.max(start, nDays - 1); i < end; i++) {
    const x = xOf(i), y = yOf(meanLine(i));
    if (!s3) { ctx.moveTo(x, y); s3 = true; } else ctx.lineTo(x, y);
  }
  ctx.stroke();
  ctx.setLineDash([]);
}
