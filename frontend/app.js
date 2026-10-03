/* ============================================================
   HeatSense — app.js  (v2 — full feature set)
   Reads ./results.snapshot.json only.
   Features: arc gauge, countUp, dark mode, slider tooltip,
             hero colour shift, canvas hover tooltip, AIC chart,
             live comparison, skeletons, toast, scroll progress.
   ============================================================ */

'use strict';

/* ── Global state ─────────────────────────────────────────── */
let DATA            = null;
let currentModel    = null;
let currentThreshold = 36;
let prevBand        = null;   // for toast on band change
let sensitivityChart = null;
let aicChart         = null;

/* ── Arc gauge math constants ─────────────────────────────── */
const ARC_R      = 100;                         // radius of arc
const ARC_CX     = 130;                         // center-x in viewBox
const ARC_CY     = 130;                         // center-y in viewBox
const ARC_LEN    = Math.PI * ARC_R;             // ≈ 314.16
const ARC_MAX_P  = 0.25;                        // gauge "full" at 25% prob

/* ─────────────────────────────────────────────────────────── */
/* 1. FETCH                                                    */
/* ─────────────────────────────────────────────────────────── */

fetch('./results.snapshot.json')
  .then(r => r.json())
  .then(data => { DATA = data; init(data); })
  .catch(err => {
    document.getElementById('metaLine').textContent =
      'Could not load results.snapshot.json — run backend/scripts/run_pipeline.py first.';
    document.body.classList.remove('loading');
    console.error(err);
  });

/* ─────────────────────────────────────────────────────────── */
/* 2. CDF IMPLEMENTATIONS (unchanged)                          */
/* ─────────────────────────────────────────────────────────── */

function erf(x) {
  const sign = x < 0 ? -1 : 1;
  x = Math.abs(x);
  const a1=0.254829592,a2=-0.284496736,a3=1.421413741,a4=-1.453152027,a5=1.061405429,p=0.3275911;
  const t = 1 / (1 + p * x);
  return sign * (1 - (((((a5*t+a4)*t)+a3)*t+a2)*t+a1)*t*Math.exp(-x*x));
}
function normalCDF(x, loc, scale) { return 0.5 * (1 + erf((x - loc) / (scale * Math.SQRT2))); }
function lognormCDF(x, s, loc, scale) { return x - loc <= 0 ? 0 : normalCDF(Math.log(x - loc), Math.log(scale), s); }
function gumbelCDF(x, loc, scale) { return Math.exp(-Math.exp(-(x - loc) / scale)); }

function gammaln(x) {
  const g = 7, c = [0.99999999999980993,676.5203681218851,-1259.1392167224028,771.32342877765313,-176.61502916214059,12.507343278686905,-0.13857109526572012,9.9843695780195716e-6,1.5056327351493116e-7];
  if (x < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * x)) - gammaln(1 - x);
  x -= 1; let a = c[0]; const t = x + g + 0.5;
  for (let i = 1; i < g + 2; i++) a += c[i] / (x + i);
  return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
}
function lowerIncompleteGammaRegularized(a, x) {
  if (x <= 0) return 0;
  if (x < a + 1) {
    let sum = 1/a, term = sum, n = a;
    for (let i = 0; i < 200; i++) { n++; term *= x/n; sum += term; if (Math.abs(term) < Math.abs(sum)*1e-12) break; }
    return sum * Math.exp(-x + a * Math.log(x) - gammaln(a));
  }
  let b = x+1-a, c = 1e308, d = 1/b, h = d;
  for (let i = 1; i < 200; i++) {
    const an = -i*(i-a); b+=2;
    d = an*d+b; if (Math.abs(d)<1e-30) d=1e-30;
    c = b+an/c; if (Math.abs(c)<1e-30) c=1e-30;
    d=1/d; const del=d*c; h*=del;
    if (Math.abs(del-1)<1e-12) break;
  }
  return 1 - Math.exp(-x + a*Math.log(x) - gammaln(a))*h;
}
function gammaCDF(x, a, loc, scale) { return x-loc<=0 ? 0 : lowerIncompleteGammaRegularized(a, (x-loc)/scale); }

function cdfFor(name, params, x) {
  switch (name) {
    case 'normal':   return normalCDF(x, params.loc, params.scale);
    case 'gumbel_r': return gumbelCDF(x, params.loc, params.scale);
    case 'lognorm':  return lognormCDF(x, params.s, params.loc, params.scale);
    case 'gamma':    return gammaCDF(x, params.a, params.loc, params.scale);
    default: return null;
  }
}
function probExceeds(name, params, threshold) {
  const p = cdfFor(name, params, threshold);
  return p === null ? null : 1 - p;
}
function modelLabel(name) {
  return ({normal:'Normal', lognorm:'Log-normal', gamma:'Gamma', gumbel_r:'Gumbel'})[name] || name;
}

/* ─────────────────────────────────────────────────────────── */
/* 3. RISK BAND HELPERS                                        */
/* ─────────────────────────────────────────────────────────── */

function bandFor(prob) {
  const bands = DATA?.synthesis?.risk_bands_reference;
  if (!bands) { return prob <= 0.05 ? 'low' : prob <= 0.15 ? 'moderate' : 'high'; }
  for (const b of bands) if (b.max === null || prob <= b.max) return b.label;
  return bands[bands.length-1].label;
}

/* ─────────────────────────────────────────────────────────── */
/* 4. COUNT-UP ANIMATION                                       */
/* ─────────────────────────────────────────────────────────── */

function countUp(el, target, suffix = '', decimals = 2, duration = 900) {
  if (!el) return;
  const start = performance.now();
  function step(now) {
    const t = Math.min((now - start) / duration, 1);
    // Ease out cubic
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = (target * eased).toFixed(decimals) + suffix;
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

/* ─────────────────────────────────────────────────────────── */
/* 5. DARK MODE                                                */
/* ─────────────────────────────────────────────────────────── */

function initDarkMode() {
  const saved      = localStorage.getItem('heatsense-theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const isDark     = saved ? saved === 'dark' : prefersDark;
  applyDarkMode(isDark, false);

  document.getElementById('darkToggle').addEventListener('click', () => {
    const currently = document.documentElement.getAttribute('data-theme') === 'dark';
    applyDarkMode(!currently, true);
  });
}

function applyDarkMode(isDark, save) {
  document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
  document.getElementById('darkToggle').setAttribute('aria-pressed', isDark);
  if (save) localStorage.setItem('heatsense-theme', isDark ? 'dark' : 'light');
  // Update Chart.js themes
  updateChartsTheme(isDark);
}

function updateChartsTheme(isDark) {
  const tickColor = isDark ? '#506980' : '#7a8fa0';
  const gridColor = isDark ? 'rgba(255,255,255,.04)' : 'rgba(0,0,0,.05)';
  const titleColor = tickColor;
  [sensitivityChart, aicChart].forEach(chart => {
    if (!chart) return;
    Object.values(chart.options.scales).forEach(scale => {
      if (scale.ticks)  scale.ticks.color = tickColor;
      if (scale.grid)   scale.grid.color = gridColor;
      if (scale.title)  scale.title.color = titleColor;
    });
    chart.update('none');
  });
}

/* ─────────────────────────────────────────────────────────── */
/* 6. SCROLL PROGRESS BAR                                      */
/* ─────────────────────────────────────────────────────────── */

function initScrollProgress() {
  const bar = document.getElementById('scrollProgress');
  if (!bar) return;
  window.addEventListener('scroll', () => {
    const docH = document.documentElement.scrollHeight - window.innerHeight;
    const pct  = docH > 0 ? (window.scrollY / docH) * 100 : 0;
    bar.style.width = pct + '%';
  }, { passive: true });
}

/* ─────────────────────────────────────────────────────────── */
/* 7. SLIDER TOOLTIP                                           */
/* ─────────────────────────────────────────────────────────── */

function updateSliderTooltip() {
  const slider  = document.getElementById('thresholdSlider');
  const tooltip = document.getElementById('sliderTooltip');
  if (!slider || !tooltip) return;
  const min = parseFloat(slider.min);
  const max = parseFloat(slider.max);
  const val = parseFloat(slider.value);
  const pct = (val - min) / (max - min);
  // Account for thumb width (~10px each side)
  const thumbW = 10;
  const trackW = slider.offsetWidth - thumbW * 2;
  const leftPx = thumbW + pct * trackW;
  tooltip.style.left = leftPx + 'px';
  tooltip.textContent = val.toFixed(1) + '°C';
  tooltip.classList.add('visible');
}

function hideSliderTooltip() {
  document.getElementById('sliderTooltip')?.classList.remove('visible');
}

/* ─────────────────────────────────────────────────────────── */
/* 8. SLIDER GRADIENT                                          */
/* ─────────────────────────────────────────────────────────── */

function updateSliderGradient() {
  const slider = document.getElementById('thresholdSlider');
  if (!slider) return;
  const min = parseFloat(slider.min);
  const max = parseFloat(slider.max);
  const val = parseFloat(slider.value);
  const pct = ((val - min) / (max - min)) * 100;
  slider.style.background = `linear-gradient(90deg, var(--red) ${pct}%, var(--border) ${pct}%)`;
}

/* ─────────────────────────────────────────────────────────── */
/* 9. ARC GAUGE                                                */
/* ─────────────────────────────────────────────────────────── */

function updateArcGauge(prob) {
  const arcFill   = document.getElementById('arcFill');
  const arcNeedle = document.getElementById('arcNeedle');
  const arcProb   = document.getElementById('arcProbText');
  const arcBand   = document.getElementById('arcBandText');
  if (!arcFill) return;

  const fillFrac   = prob !== null ? Math.min(prob / ARC_MAX_P, 1) : 0;
  const dashOffset = ARC_LEN * (1 - fillFrac);

  arcFill.style.strokeDasharray  = ARC_LEN;
  arcFill.style.strokeDashoffset = dashOffset;

  // Move needle dot to tip of fill arc
  if (arcNeedle && prob !== null) {
    // Angle: starts at π (left) ends at 0 (right), fill goes left-to-right
    const angle = Math.PI - fillFrac * Math.PI; // radians from center
    const nx = ARC_CX + ARC_R * Math.cos(Math.PI - fillFrac * Math.PI);
    const ny = ARC_CY - ARC_R * Math.sin(fillFrac * Math.PI);
    arcNeedle.setAttribute('cx', nx);
    arcNeedle.setAttribute('cy', ny);
    arcNeedle.style.opacity = '1';
  } else if (arcNeedle) {
    arcNeedle.style.opacity = '0';
  }

  if (arcBand && prob !== null) {
    const band = bandFor(prob);
    arcBand.textContent = band.charAt(0).toUpperCase() + band.slice(1) + ' risk';
  }
}

/* ─────────────────────────────────────────────────────────── */
/* 10. HERO COLOUR SHIFT                                       */
/* ─────────────────────────────────────────────────────────── */

function updateHeroColor(band) {
  const hero = document.getElementById('heroBand');
  if (!hero) return;
  hero.className = 'hero-band' + (band ? ` band-${band}` : '');
}

/* ─────────────────────────────────────────────────────────── */
/* 11. TOAST NOTIFICATIONS                                     */
/* ─────────────────────────────────────────────────────────── */

function showToast(message, band) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast toast-${band}`;
  toast.innerHTML = `<div class="toast-icon"></div><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'toast-out 0.3s ease forwards';
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
  }, 3000);
}

/* ─────────────────────────────────────────────────────────── */
/* 12. CANVAS HOVER TOOLTIP                                    */
/* ─────────────────────────────────────────────────────────── */

function initCanvasTooltip() {
  const canvas  = document.getElementById('timelineCanvas');
  const tooltip = document.getElementById('canvasTooltip');
  if (!canvas || !tooltip) return;

  canvas.addEventListener('mousemove', e => {
    if (!DATA) return;
    const rect  = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;

    const cs     = DATA.core_stats;
    const trend  = DATA.trend;
    const nDays  = cs.n_days;
    const residuals = trend?.residuals || [];
    const projDays  = 7;
    const total     = nDays + projDays;

    const panFrac     = document.getElementById('panSlider').value / 100;
    const visibleSpan = Math.min(total, 30);
    const maxStart    = total - visibleSpan;
    const start       = Math.round(maxStart * panFrac);

    const padL = 50, padR = 20;
    const dpr  = window.devicePixelRatio || 1;
    const cssWidth = parseFloat(canvas.style.width) || (canvas.parentElement.clientWidth - 40);
    const plotW = cssWidth - padL - padR;

    // Find nearest day index
    const dayFloat = start + ((mouseX - padL) / plotW) * (visibleSpan - 1);
    const dayIdx   = Math.round(dayFloat);

    if (dayIdx < start || dayIdx >= start + visibleSpan) {
      tooltip.classList.remove('visible');
      return;
    }

    const meanLine  = i => cs.mean + trend.slope_c_per_day * (i - nDays / 2);
    const isRecorded = dayIdx < nDays;
    const temp = isRecorded
      ? meanLine(dayIdx) + (residuals[dayIdx] || 0)
      : meanLine(dayIdx);

    const above = temp > currentThreshold;
    tooltip.innerHTML = `
      <strong>${temp.toFixed(2)}°C${above ? ' 🔴' : ''}</strong>
      Day ${dayIdx + 1} · ${isRecorded ? 'Recorded' : 'Projected'}
      ${above ? '<br><span style="color:#f48080">Above threshold</span>' : ''}
    `;
    tooltip.classList.add('visible');
    // Position tooltip
    const tx = e.clientX + 14;
    const ty = e.clientY - 10;
    tooltip.style.left = tx + 'px';
    tooltip.style.top  = ty + 'px';
    // Keep in viewport
    const tipW = tooltip.offsetWidth;
    if (tx + tipW > window.innerWidth - 16) {
      tooltip.style.left = (e.clientX - tipW - 14) + 'px';
    }
  });

  canvas.addEventListener('mouseleave', () => tooltip.classList.remove('visible'));
}

/* ─────────────────────────────────────────────────────────── */
/* 13. LIVE MODEL COMPARISON                                   */
/* ─────────────────────────────────────────────────────────── */

function updateLiveComparison() {
  const grid    = document.getElementById('liveCompGrid');
  const thrSpan = document.getElementById('liveCompThreshold');
  if (!grid || !DATA) return;
  if (thrSpan) thrSpan.textContent = currentThreshold.toFixed(1);

  const dfit = DATA.distribution_fit;
  grid.innerHTML = '';

  dfit.candidates.forEach(c => {
    const prob = probExceeds(c.name, c.params, currentThreshold);
    const pct  = prob !== null ? prob * 100 : null;
    const fillW = prob !== null ? Math.min(prob / ARC_MAX_P, 1) * 100 : 0;
    const isBest = c.name === dfit.best_model;

    const div = document.createElement('div');
    div.className = `live-comp-item${isBest ? ' best-model' : ''}`;
    div.innerHTML = `
      <div class="live-comp-name">${modelLabel(c.name)}${isBest ? ' ★' : ''}</div>
      <div class="live-comp-prob">${pct !== null ? pct.toFixed(2) + '%' : '—'}</div>
      <div class="live-comp-bar-track"><div class="live-comp-bar" style="width:${fillW}%"></div></div>
      <div class="live-comp-aic">AIC ${c.aic}</div>
    `;
    grid.appendChild(div);
  });
}

/* ─────────────────────────────────────────────────────────── */
/* 14. SIDEBAR NAV HIGHLIGHTING                                */
/* ─────────────────────────────────────────────────────────── */

function setupNavHighlighting() {
  const sections = document.querySelectorAll('.section[id]');
  const navLinks  = document.querySelectorAll('.nav-item[data-section]');
  if (!sections.length || !navLinks.length) return;

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navLinks.forEach(link =>
          link.classList.toggle('active', link.dataset.section === entry.target.id)
        );
      }
    });
  }, { threshold: 0.3 });

  sections.forEach(s => observer.observe(s));
}

/* ─────────────────────────────────────────────────────────── */
/* 15. CHARTS (sensitivity + AIC)                              */
/* ─────────────────────────────────────────────────────────── */

function getChartColors(isDark) {
  return {
    tick:  isDark ? '#506980' : '#7a8fa0',
    grid:  isDark ? 'rgba(255,255,255,.04)' : 'rgba(0,0,0,.05)',
  };
}

function buildSensitivityChart(data) {
  const canvas = document.getElementById('sensitivityChart');
  if (!canvas || typeof Chart === 'undefined') return;
  const sens = data.simulation?.threshold_sensitivity;
  if (!sens) return;

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const { tick, grid } = getChartColors(isDark);

  const labels = sens.thresholds_c.map(t => `${t}°C`);
  const probs  = sens.probabilities.map(p => +(p * 100).toFixed(2));
  const colors = probs.map(p => p <= 5 ? 'rgba(39,174,96,.75)' : p <= 15 ? 'rgba(230,126,34,.75)' : 'rgba(224,90,58,.75)');
  const border = probs.map(p => p <= 5 ? 'rgb(39,174,96)'      : p <= 15 ? 'rgb(230,126,34)'      : 'rgb(224,90,58)');

  if (sensitivityChart) sensitivityChart.destroy();
  sensitivityChart = new Chart(canvas, {
    type: 'bar',
    data: { labels, datasets: [{ label: 'Exceedance probability (%)', data: probs, backgroundColor: colors, borderColor: border, borderWidth: 2, borderRadius: 6, borderSkipped: false }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y.toFixed(2)}% chance of exceeding ${ctx.label}` } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: tick, font: { size: 12, family: 'Inter, sans-serif' } } },
        y: { grid: { color: grid }, ticks: { color: tick, font: { size: 11, family: 'Inter, sans-serif' }, callback: v => v + '%' }, title: { display: true, text: 'Exceedance probability (%)', color: tick, font: { size: 11, family: 'Inter, sans-serif' } } }
      }
    }
  });
}

function buildAicChart(data) {
  const canvas = document.getElementById('aicChart');
  if (!canvas || typeof Chart === 'undefined') return;

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const { tick, grid } = getChartColors(isDark);

  const dfit   = data.distribution_fit;
  const labels = dfit.candidates.map(c => modelLabel(c.name));
  const aics   = dfit.candidates.map(c => c.aic);
  const minAic = Math.min(...aics);

  const colors = dfit.candidates.map(c =>
    c.name === dfit.best_model ? 'rgba(41,128,185,.85)' : 'rgba(122,143,160,.45)'
  );
  const borders = dfit.candidates.map(c =>
    c.name === dfit.best_model ? 'rgb(41,128,185)' : 'rgb(122,143,160)'
  );

  if (aicChart) aicChart.destroy();
  aicChart = new Chart(canvas, {
    type: 'bar',
    data: { labels, datasets: [{ label: 'AIC score', data: aics, backgroundColor: colors, borderColor: borders, borderWidth: 2, borderRadius: 6, borderSkipped: false }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` AIC: ${ctx.parsed.y.toFixed(2)}${ctx.parsed.y === minAic ? ' ← best fit' : ''}` } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: tick, font: { size: 12, family: 'Inter, sans-serif' } } },
        y: { grid: { color: grid }, min: Math.floor(minAic - 10), ticks: { color: tick, font: { size: 11, family: 'Inter, sans-serif' } }, title: { display: true, text: 'AIC (lower = better fit)', color: tick, font: { size: 11, family: 'Inter, sans-serif' } } }
      }
    }
  });
}

/* ─────────────────────────────────────────────────────────── */
/* 16. INIT                                                    */
/* ─────────────────────────────────────────────────────────── */

function init(data) {
  const dfit = data.distribution_fit;
  currentModel    = dfit.best_model;
  currentThreshold = dfit.threshold_c;

  // Meta line
  const generatedAt = data._meta?.generated_at
    ? new Date(data._meta.generated_at).toLocaleDateString('en-GB', { day:'numeric', month:'short', year:'numeric' })
    : 'snapshot';
  document.getElementById('metaLine').textContent =
    `${data.core_stats.n_days} days · best fit: ${modelLabel(dfit.best_model)} · ${generatedAt}`;
  const tStatus = document.getElementById('topbarStatus');
  if (tStatus) tStatus.textContent = generatedAt;

  // Threshold slider
  const slider = document.getElementById('thresholdSlider');
  if (slider) {
    slider.value = currentThreshold;
    updateSliderGradient();

    slider.addEventListener('input', e => {
      currentThreshold = parseFloat(e.target.value);
      updateSliderGradient();
      updateSliderTooltip();
      render();
    });
    slider.addEventListener('mouseenter', updateSliderTooltip);
    slider.addEventListener('focus',      updateSliderTooltip);
    slider.addEventListener('mouseleave', hideSliderTooltip);
    slider.addEventListener('blur',       hideSliderTooltip);
  }

  // Mobile sidebar toggle
  const menuBtn = document.getElementById('menuBtn');
  const sidebar = document.getElementById('sidebar');
  if (menuBtn && sidebar) {
    menuBtn.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', e => {
      if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== menuBtn)
        sidebar.classList.remove('open');
    });
  }

  // Dark mode
  initDarkMode();

  // Scroll progress
  initScrollProgress();

  // Build everything
  buildModelToggle(dfit);
  buildForecast(data);
  buildComparisonTable(data);
  buildStatsTable(data);
  buildAssumptions(data);
  buildSynthesis(data);
  buildSensitivityChart(data);
  buildAicChart(data);
  updateLiveComparison();
  setupNavHighlighting();
  initCanvasTooltip();

  // Pan slider + resize
  document.getElementById('panSlider').addEventListener('input', drawTimeline);
  window.addEventListener('resize', drawTimeline);

  // Remove skeleton class
  document.body.classList.remove('loading');

  // Render & animate
  render(true /* firstLoad */);
}

/* ─────────────────────────────────────────────────────────── */
/* 17. RENDER (called on every threshold/model change)         */
/* ─────────────────────────────────────────────────────────── */

function render(firstLoad = false) {
  document.getElementById('thresholdVal').textContent = currentThreshold.toFixed(1);

  const dfit = DATA.distribution_fit;
  const cand = dfit.candidates.find(c => c.name === currentModel);
  let prob;
  if (cand) prob = probExceeds(currentModel, cand.params, currentThreshold);
  if (prob === null || prob === undefined || Number.isNaN(prob))
    prob = currentModel === dfit.best_model ? dfit.theoretical_probability : null;

  const probPct = prob !== null ? prob * 100 : null;

  // Arc gauge + count-up on first load, instant update after
  const arcProbEl = document.getElementById('arcProbText');
  if (firstLoad && probPct !== null) {
    countUp(arcProbEl, probPct, '%', 2, 1000);
  } else if (arcProbEl) {
    arcProbEl.textContent = probPct !== null ? probPct.toFixed(2) + '%' : 'n/a';
  }

  // Also count up the big probability display in risk card (if re-used as arc text)
  updateArcGauge(prob);

  document.getElementById('returnPeriod').textContent =
    prob && prob > 0 ? `≈ 1-in-${(1 / prob).toFixed(1)}-day event` : '';

  const band   = prob !== null ? bandFor(prob) : 'unavailable';
  const bandEl = document.getElementById('riskBand');
  bandEl.textContent = band.charAt(0).toUpperCase() + band.slice(1);
  bandEl.className = `risk-band-pill band-${band}`;

  // Hero color shift
  updateHeroColor(band);

  // Toast on band change (not on first load)
  if (!firstLoad && prevBand !== null && prevBand !== band && prob !== null) {
    showToast(`Risk level changed to ${band.toUpperCase()}`, band);
  }
  prevBand = band;

  document.getElementById('modelNote').textContent =
    currentModel === dfit.best_model
      ? `${modelLabel(currentModel)} · live probability recomputed from fitted parameters`
      : `${modelLabel(currentModel)} · probability from snapshot`;

  updateTakeaway(prob, firstLoad);
  buildForecast(DATA);
  updateLiveComparison();
  drawTimeline();
}

/* ─────────────────────────────────────────────────────────── */
/* 18. 7-DAY FORECAST                                          */
/* ─────────────────────────────────────────────────────────── */

function buildForecast(data) {
  const grid  = document.getElementById('forecastGrid');
  const note  = document.getElementById('forecastNote');
  const dfit  = data.distribution_fit;
  const cand  = dfit.candidates.find(c => c.name === currentModel);
  if (!cand) return;

  const cs    = data.core_stats;
  const trend = data.trend;
  const cards = [];

  for (let day = 1; day <= 7; day++) {
    const idx      = cs.n_days + day - 1;
    const expected = cs.mean + trend.slope_c_per_day * (idx - cs.n_days / 2);
    const spread   = cand.params.scale * (1 + (day - 1) * 0.15);
    const chance   = probExceeds(currentModel, cand.params, currentThreshold);
    const isHot    = chance !== null && chance > 0.15;

    cards.push(`
      <div class="forecast-day${isHot ? ' hot' : ''}">
        <span class="forecast-day-label">Day +${day}</span>
        <strong class="forecast-day-temp">${expected.toFixed(1)}°C</strong>
        <span class="forecast-day-range">${Math.max(0, expected - spread).toFixed(1)}–${(expected + spread).toFixed(1)}°C</span>
        <span class="forecast-day-prob">${chance !== null ? (chance * 100).toFixed(1) : '—'}% over threshold</span>
      </div>
    `);
  }

  grid.innerHTML = cards.join('');
  if (note) note.textContent = `${modelLabel(currentModel)} projection · uncertainty widens by day`;
}

/* ─────────────────────────────────────────────────────────── */
/* 19. TAKEAWAY                                                */
/* ─────────────────────────────────────────────────────────── */

function updateTakeaway(prob, firstLoad = false) {
  const cs        = DATA.core_stats;
  const trend     = DATA.trend;
  const residuals = trend?.residuals || [];
  const recorded  = residuals.map((r, i) => cs.mean + trend.slope_c_per_day * (i - cs.n_days / 2) + r);
  const crossings = recorded.filter(v => v > currentThreshold).length;
  const peak      = recorded.length > 0 ? Math.max(...recorded) : cs.mean;
  const percent   = prob === null ? 'n/a' : `${(prob * 100).toFixed(1)}%`;
  const cadence   = prob && prob > 0 ? `about once every ${(1 / prob).toFixed(1)} days` : 'very rarely';

  document.getElementById('takeawayTitle').textContent =
    `${percent} chance of crossing ${currentThreshold.toFixed(1)}°C on any given day`;
  document.getElementById('takeawayText').textContent =
    `That is ${cadence}. In the recorded sample, ${crossings} of ${cs.n_days} days crossed this threshold.`;

  const crossEl = document.getElementById('observedCrossings');
  const peakEl  = document.getElementById('observedPeak');

  if (firstLoad) {
    countUp(crossEl, crossings, `/${cs.n_days}`, 0, 600);
    countUp(peakEl,  peak, '°C', 1, 700);
  } else {
    if (crossEl) crossEl.textContent = `${crossings}/${cs.n_days}`;
    if (peakEl)  peakEl.textContent  = `${peak.toFixed(1)}°C`;
  }
}

/* ─────────────────────────────────────────────────────────── */
/* 20. MODEL TOGGLE                                            */
/* ─────────────────────────────────────────────────────────── */

function buildModelToggle(dfit) {
  const wrap = document.getElementById('modelToggle');
  wrap.innerHTML = '';
  dfit.candidates.forEach(c => {
    const btn = document.createElement('button');
    btn.className = `model-btn${c.name === currentModel ? ' active' : ''}${c.name === dfit.best_model ? ' best' : ''}`;
    btn.textContent = modelLabel(c.name);
    btn.title = `AIC: ${c.aic}  |  BIC: ${c.bic}  |  Log-likelihood: ${c.log_likelihood}`;
    btn.setAttribute('aria-pressed', c.name === currentModel);
    btn.addEventListener('click', () => {
      currentModel = c.name;
      [...wrap.children].forEach(b => { b.classList.remove('active'); b.setAttribute('aria-pressed', 'false'); });
      btn.classList.add('active');
      btn.setAttribute('aria-pressed', 'true');
      render();
    });
    wrap.appendChild(btn);
  });
}

/* ─────────────────────────────────────────────────────────── */
/* 21. TABLES                                                  */
/* ─────────────────────────────────────────────────────────── */

function row(table, label, value) {
  const tr = document.createElement('tr');
  const td1 = document.createElement('td'); td1.textContent = label;
  const td2 = document.createElement('td'); td2.textContent = value;
  tr.append(td1, td2); table.appendChild(tr);
}

function buildComparisonTable(data) {
  const t = document.getElementById('comparisonTable');
  const sim = data.simulation;
  row(t, 'Theoretical (fitted model)',     (sim.comparison.theoretical   * 100).toFixed(2) + '%');
  row(t, 'Monte Carlo (10,000 trials)',    (sim.comparison.monte_carlo_10k * 100).toFixed(2) + '%');
  row(t, 'Bootstrap (real data)',          (sim.comparison.bootstrap      * 100).toFixed(2) + '%');
  row(t, 'Return period',                 `1-in-${sim.return_period_days}-day event`);
}

function buildStatsTable(data) {
  const t = document.getElementById('statsTable');
  const cs = data.core_stats;
  row(t, 'Mean',                   `${cs.mean}°C  (CI ${cs.mean_ci95[0]}–${cs.mean_ci95[1]})`);
  row(t, 'Std. deviation',         `${cs.std_dev}°C  (CI ${cs.std_dev_ci95[0]}–${cs.std_dev_ci95[1]})`);
  row(t, 'Coeff. of variation',    `${cs.cv_percent}%  (CI ${cs.cv_percent_ci95[0]}–${cs.cv_percent_ci95[1]})`);
  row(t, 'Shapiro-Wilk p-value',   `${cs.shapiro_wilk.p_value} (${cs.shapiro_wilk.is_normal_at_5pct ? 'Normal' : 'Not normal'} at 5%)`);
  row(t, 'Sample size',            `${cs.n_days} days`);
}

/* ─────────────────────────────────────────────────────────── */
/* 22. ASSUMPTIONS + SYNTHESIS                                 */
/* ─────────────────────────────────────────────────────────── */

function buildAssumptions(data) {
  const box   = document.getElementById('assumptions');
  const trend = data.trend;
  const dep   = data.dependence;
  const df    = data.distribution_fit;

  const items = [
    { ok: !trend.is_statistically_significant || Math.abs(trend.total_drift_c || 0) < 1, text: `Stationarity — ${trend.practical_note}` },
    { ok: !dep.is_significant, text: `Independence — ${dep.interpretation}` },
    { ok: true, text: `Model adequacy — best fit is ${modelLabel(df.best_model)} (AIC-selected, holdout-validated); Q-Q R=${df.qq_plot_r_value}.` }
  ];

  box.innerHTML = '';
  items.forEach(it => {
    const div = document.createElement('div');
    div.className = 'assumption';
    div.innerHTML = `<span class="dot ${it.ok ? 'ok' : 'flag'}"></span><span>${it.text}</span>`;
    box.appendChild(div);
  });
}

function buildSynthesis(data) {
  const s   = data.synthesis;
  const box = document.getElementById('synthesisBox');
  box.innerHTML = `
    <div class="synth-big">${(s.heat_risk_index * 100).toFixed(2)}%
      <span class="band-pill-sm band-${s.risk_band}">${s.risk_band}</span>
    </div>
    <div class="synth-components">
      <div class="synth-component"><span>Base probability</span><span>${(s.components_used.base_probability * 100).toFixed(2)}%</span></div>
      <div class="synth-component"><span>Trend adjustment</span><span>×(1 + ${s.components_used.trend_adjustment})</span></div>
      <div class="synth-component"><span>Clustering adjustment</span><span>×(1 + ${s.components_used.clustering_adjustment})</span></div>
    </div>
    <p class="synth-formula">${s.formula_note}</p>
  `;
}

/* ─────────────────────────────────────────────────────────── */
/* 23. TIMELINE CANVAS                                         */
/* ─────────────────────────────────────────────────────────── */

function drawTimeline() {
  if (!DATA) return;
  const canvas = document.getElementById('timelineCanvas');
  const dpr    = window.devicePixelRatio || 1;
  const cssWidth  = Math.max(100, canvas.parentElement.clientWidth - 40);
  const cssHeight = 280;
  canvas.width  = cssWidth * dpr;
  canvas.height = cssHeight * dpr;
  canvas.style.width  = cssWidth + 'px';
  canvas.style.height = cssHeight + 'px';
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, cssWidth, cssHeight);

  const cs       = DATA.core_stats;
  const trend    = DATA.trend;
  const nDays    = cs.n_days;
  const projDays = 7;
  const total    = nDays + projDays;
  const padL = 52, padR = 20, padT = 22, padB = 32;
  const plotW = cssWidth - padL - padR;
  const plotH = cssHeight - padT - padB;

  const panFrac     = document.getElementById('panSlider').value / 100;
  const visibleSpan = Math.min(total, 30);
  const maxStart    = total - visibleSpan;
  const start       = Math.round(maxStart * panFrac);
  const end         = start + visibleSpan;

  const residuals  = trend?.residuals || [];
  const meanLine   = i => cs.mean + trend.slope_c_per_day * (i - nDays / 2);
  const actualVal  = i => meanLine(i) + (residuals[i] || 0);
  const sd         = cs.std_dev;

  const yMin = cs.mean - 3.5 * sd;
  const yMax = cs.mean + 4.2 * sd;
  const xOf  = i => padL + ((i - start) / (visibleSpan - 1)) * plotW;
  const yOf  = v => padT + (1 - (v - yMin) / (yMax - yMin)) * plotH;

  // Theme-aware colours
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const gridCol  = isDark ? '#243547' : '#e3e8ed';
  const textCol  = isDark ? '#506980' : '#7a8fa0';
  const surfCol  = isDark ? '#182533' : '#ffffff';

  // Horizontal grid lines + y-axis labels
  [yMin, cs.mean - sd, cs.mean, cs.mean + sd, yMax].forEach(v => {
    const y = yOf(v);
    ctx.strokeStyle = gridCol; ctx.lineWidth = 1; ctx.setLineDash([]);
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(padL + plotW, y); ctx.stroke();
    ctx.fillStyle = textCol; ctx.font = '11px Inter, Segoe UI, sans-serif';
    ctx.textAlign = 'right'; ctx.fillText(v.toFixed(1), padL - 6, y + 4);
  });

  // Day tick marks + labels
  const every = Math.ceil(visibleSpan / 7);
  for (let i = start; i < end; i++) {
    if ((i - start) % every !== 0) continue;
    const x = xOf(i);
    ctx.strokeStyle = isDark ? '#1a2e3d' : '#f2f4f6'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(x, padT); ctx.lineTo(x, padT + plotH); ctx.stroke();
    ctx.fillStyle = textCol; ctx.font = '10px Inter, Segoe UI, sans-serif';
    ctx.textAlign = 'center'; ctx.fillText(`d${i + 1}`, x, padT + plotH + 20);
  }

  // Divider between recorded and projected
  if (nDays >= start && nDays <= end) {
    const divX = xOf(nDays - 1);
    ctx.strokeStyle = isDark ? '#2a4560' : '#d0d8e0'; ctx.lineWidth = 1;
    ctx.setLineDash([3, 4]);
    ctx.beginPath(); ctx.moveTo(divX, padT); ctx.lineTo(divX, padT + plotH); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = textCol; ctx.font = '9px Inter, Segoe UI, sans-serif';
    ctx.textAlign = 'center'; ctx.fillText('forecast →', divX + 28, padT + 14);
  }

  // ±2 SD uncertainty band (projection)
  ctx.beginPath(); let started = false;
  for (let i = Math.max(start, nDays - 1); i < end; i++) {
    const dout = Math.max(0, i - nDays); const widen = 1 + dout * 0.15;
    const v = Math.min(meanLine(i) + 2 * sd * widen, yMax);
    if (!started) { ctx.moveTo(xOf(i), yOf(v)); started = true; } else ctx.lineTo(xOf(i), yOf(v));
  }
  for (let i = end - 1; i >= Math.max(start, nDays - 1); i--) {
    const dout = Math.max(0, i - nDays); const widen = 1 + dout * 0.15;
    ctx.lineTo(xOf(i), yOf(Math.max(meanLine(i) - 2 * sd * widen, yMin)));
  }
  ctx.closePath(); ctx.fillStyle = 'rgba(41,128,185,0.09)';
  if (started) ctx.fill();

  // Risk zone above threshold in projection
  ctx.beginPath(); let rStarted = false;
  for (let i = Math.max(start, nDays - 1); i < end; i++) {
    const dout = Math.max(0, i - nDays); const widen = 1 + dout * 0.15;
    const upper = meanLine(i) + 2 * sd * widen;
    const x = xOf(i), y = yOf(Math.max(currentThreshold, Math.min(upper, yMax)));
    if (!rStarted) { ctx.moveTo(x, y); rStarted = true; } else ctx.lineTo(x, y);
  }
  for (let i = end - 1; i >= Math.max(start, nDays - 1); i--) {
    const dout = Math.max(0, i - nDays); const widen = 1 + dout * 0.15;
    const upper = meanLine(i) + 2 * sd * widen;
    ctx.lineTo(xOf(i), yOf(Math.min(upper, currentThreshold)));
  }
  ctx.closePath(); ctx.fillStyle = 'rgba(224,90,58,0.12)';
  if (rStarted) ctx.fill();

  // Threshold line
  const thrY = yOf(currentThreshold);
  ctx.strokeStyle = '#e05a3a'; ctx.setLineDash([6, 4]); ctx.lineWidth = 1.8;
  ctx.beginPath(); ctx.moveTo(padL, thrY); ctx.lineTo(padL + plotW, thrY); ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = '#e05a3a'; ctx.font = 'bold 11px Inter, Segoe UI, sans-serif';
  ctx.textAlign = 'right'; ctx.fillText(`${currentThreshold.toFixed(1)}°C`, padL + plotW, thrY - 7);

  // Recorded data line
  ctx.strokeStyle = '#2980b9'; ctx.lineWidth = 2.5; ctx.lineJoin = 'round';
  ctx.beginPath(); let s2 = false;
  for (let i = start; i < Math.min(end, nDays); i++) {
    const x = xOf(i), y = yOf(actualVal(i));
    if (!s2) { ctx.moveTo(x, y); s2 = true; } else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // Data point dots
  for (let i = start; i < Math.min(end, nDays); i++) {
    const val = actualVal(i); const hot = val > currentThreshold;
    ctx.beginPath();
    ctx.fillStyle   = hot ? '#e05a3a' : surfCol;
    ctx.strokeStyle = hot ? '#e05a3a' : '#2980b9';
    ctx.lineWidth = 2;
    ctx.arc(xOf(i), yOf(val), hot ? 5 : 3, 0, Math.PI * 2);
    ctx.fill(); ctx.stroke();
  }

  // Projected mean line
  ctx.strokeStyle = '#27ae60'; ctx.setLineDash([6, 4]); ctx.lineWidth = 2;
  ctx.beginPath(); let s3 = false;
  for (let i = Math.max(start, nDays - 1); i < end; i++) {
    const x = xOf(i), y = yOf(meanLine(i));
    if (!s3) { ctx.moveTo(x, y); s3 = true; } else ctx.lineTo(x, y);
  }
  ctx.stroke(); ctx.setLineDash([]);
}
