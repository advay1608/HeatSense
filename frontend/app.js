'use strict';

/* ── Global state ─────────────────────────────────────────── */
let DATA            = null;
let currentModel    = null;
let currentThreshold = 36;
let prevBand        = null;   // for toast on band change
let sensitivityChart = null;
let aicChart         = null;
let timelineChart    = null;

/* ── Arc gauge math constants ─────────────────────────────── */
const ARC_R      = 100;
const ARC_CX     = 130;
const ARC_CY     = 130;
const ARC_LEN    = Math.PI * ARC_R;
const ARC_MAX_P  = 0.25;

fetch('./results.snapshot.json')
  .then(r => r.json())
  .then(data => { DATA = data; init(data); })
  .catch(err => {
    document.getElementById('metaLine').textContent =
      'Could not load results.snapshot.json — run backend/scripts/run_pipeline.py first.';
    document.body.classList.remove('loading');
    console.error(err);
  });

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

function bandFor(prob) {
  const bands = DATA?.synthesis?.risk_bands_reference;
  if (!bands) { return prob <= 0.05 ? 'low' : prob <= 0.15 ? 'moderate' : 'high'; }
  for (const b of bands) if (b.max === null || prob <= b.max) return b.label;
  return bands[bands.length-1].label;
}

function countUp(el, target, suffix = '', decimals = 2, duration = 900) {
  if (!el) return;
  const start = performance.now();
  function step(now) {
    const t = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = (target * eased).toFixed(decimals) + suffix;
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

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
  updateChartsTheme(isDark);
}

function updateChartsTheme(isDark) {
  const tickColor = isDark ? '#506980' : '#7a8fa0';
  const gridColor = isDark ? 'rgba(255,255,255,.04)' : 'rgba(0,0,0,.05)';
  const titleColor = tickColor;
  [sensitivityChart, aicChart, timelineChart].forEach(chart => {
    if (!chart) return;
    if (chart.options.scales) {
      Object.values(chart.options.scales).forEach(scale => {
        if (scale.ticks)  scale.ticks.color = tickColor;
        if (scale.grid)   scale.grid.color = gridColor;
        if (scale.title)  scale.title.color = titleColor;
      });
    }
    if (chart.options.plugins?.legend?.labels) {
      chart.options.plugins.legend.labels.color = tickColor;
    }
    chart.update('none');
  });
}

function initScrollProgress() {
  const bar = document.getElementById('scrollProgress');
  if (!bar) return;
  window.addEventListener('scroll', () => {
    const docH = document.documentElement.scrollHeight - window.innerHeight;
    const pct  = docH > 0 ? (window.scrollY / docH) * 100 : 0;
    bar.style.width = pct + '%';
  }, { passive: true });
}

function updateSliderTooltip() {
  const slider  = document.getElementById('thresholdSlider');
  const tooltip = document.getElementById('sliderTooltip');
  if (!slider || !tooltip) return;
  const min = parseFloat(slider.min);
  const max = parseFloat(slider.max);
  const val = parseFloat(slider.value);
  const pct = (val - min) / (max - min);
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

function updateSliderGradient() {
  const slider = document.getElementById('thresholdSlider');
  if (!slider) return;
  const min = parseFloat(slider.min);
  const max = parseFloat(slider.max);
  const val = parseFloat(slider.value);
  const pct = ((val - min) / (max - min)) * 100;
  slider.style.background = `linear-gradient(90deg, var(--red) ${pct}%, var(--border) ${pct}%)`;
}

function updateArcGauge(prob) {
  const arcFill   = document.getElementById('arcFill');
  const arcNeedle = document.getElementById('arcNeedle');
  const arcBand   = document.getElementById('arcBandText');
  if (!arcFill) return;

  const fillFrac   = prob !== null ? Math.min(prob / ARC_MAX_P, 1) : 0;
  const dashOffset = ARC_LEN * (1 - fillFrac);

  arcFill.style.strokeDasharray  = ARC_LEN;
  arcFill.style.strokeDashoffset = dashOffset;

  if (arcNeedle && prob !== null) {
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

function updateHeroColor(band) {
  const hero = document.getElementById('heroBand');
  if (!hero) return;
  hero.className = 'hero-band' + (band ? ` band-${band}` : '');
}

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

function initHelpTooltips() {
  const tooltip = document.getElementById('helpTooltip');
  if (!tooltip) return;

  document.addEventListener('mouseover', e => {
    const icon = e.target.closest('.help-icon');
    if (!icon) return;
    const text = icon.getAttribute('data-tip');
    if (!text) return;

    tooltip.textContent = text;
    tooltip.classList.add('visible');

    const rect = icon.getBoundingClientRect();
    tooltip.style.left = (rect.left + rect.width / 2) + 'px';
    tooltip.style.top  = (rect.top - 8) + 'px';
  });

  document.addEventListener('mouseout', e => {
    if (e.target.closest('.help-icon')) {
      tooltip.classList.remove('visible');
    }
  });
}

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
      <div class="live-comp-aic">AIC ${c.aic} <span class="help-icon" data-tip="Akaike Information Criterion. Lower is better."><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17h.01"/></svg></span></div>
    `;
    grid.appendChild(div);
  });
}

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

function init(data) {
  const dfit = data.distribution_fit;
  currentModel    = dfit.best_model;
  currentThreshold = dfit.threshold_c;

  const locName = data.dataset_info?.location_name || 'Urban Station';
  const startYear = data.dataset_info?.start_date ? data.dataset_info.start_date.slice(0, 4) : '';
  const endYear = data.dataset_info?.end_date ? data.dataset_info.end_date.slice(0, 4) : '';
  const spanStr = startYear && endYear ? ` (${startYear}–${endYear})` : '';

  document.getElementById('metaLine').textContent =
    `${locName} · ${data.core_stats.n_days.toLocaleString()} days${spanStr} · best fit: ${modelLabel(dfit.best_model)}`;
  const tStatus = document.getElementById('topbarStatus');
  if (tStatus) tStatus.textContent = `${locName} · Live API`;

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

  const menuBtn = document.getElementById('menuBtn');
  const sidebar = document.getElementById('sidebar');
  if (menuBtn && sidebar) {
    menuBtn.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', e => {
      if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== menuBtn)
        sidebar.classList.remove('open');
    });
  }

  initDarkMode();
  initScrollProgress();

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
  initHelpTooltips();

  document.getElementById('panSlider')?.addEventListener('input', () => {
    // We can use animation: false to make sliding feel instant like before
    if (timelineChart) timelineChart.options.animation = false;
    buildTimelineChart(DATA);
  });

  document.body.classList.remove('loading');
  render(true);
}

function render(firstLoad = false) {
  document.getElementById('thresholdVal').textContent = currentThreshold.toFixed(1);

  const dfit = DATA.distribution_fit;
  const cand = dfit.candidates.find(c => c.name === currentModel);
  let prob;
  if (cand) prob = probExceeds(currentModel, cand.params, currentThreshold);
  if (prob === null || prob === undefined || Number.isNaN(prob))
    prob = currentModel === dfit.best_model ? dfit.theoretical_probability : null;

  const probPct = prob !== null ? prob * 100 : null;

  const arcProbEl = document.getElementById('arcProbText');
  if (firstLoad && probPct !== null) {
    countUp(arcProbEl, probPct, '%', 2, 1000);
  } else if (arcProbEl) {
    arcProbEl.textContent = probPct !== null ? probPct.toFixed(2) + '%' : 'n/a';
  }

  updateArcGauge(prob);

  document.getElementById('returnPeriod').textContent =
    prob && prob > 0 ? `≈ 1-in-${(1 / prob).toFixed(1)}-day event` : '';

  const band   = prob !== null ? bandFor(prob) : 'unavailable';
  const bandEl = document.getElementById('riskBand');
  bandEl.textContent = band.charAt(0).toUpperCase() + band.slice(1);
  bandEl.className = `risk-band-pill band-${band}`;

  updateHeroColor(band);

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
  buildTimelineChart(DATA);
}

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

function updateTakeaway(prob, firstLoad = false) {
  const cs        = DATA.core_stats;
  const trend     = DATA.trend;
  const residuals = trend?.residuals || [];
  const recorded  = residuals.map((r, i) => cs.mean + trend.slope_c_per_day * (i - cs.n_days / 2) + r);
  
  // Safe aggregation that handles large datasets without call-stack overflow
  let crossings = 0;
  let peak = cs.max_temp !== undefined ? cs.max_temp : -Infinity;
  for (let i = 0; i < recorded.length; i++) {
    const val = recorded[i];
    if (val > currentThreshold) crossings++;
    if (cs.max_temp === undefined && val > peak) peak = val;
  }
  if (peak === -Infinity) peak = cs.mean;

  const percent = prob === null ? 'n/a' : `${(prob * 100).toFixed(1)}%`;
  const cadence = prob && prob > 0 ? `about once every ${(1 / prob).toFixed(1)} days` : 'very rarely';

  document.getElementById('takeawayTitle').textContent =
    `${percent} chance of crossing ${currentThreshold.toFixed(1)}°C on any given day`;
  document.getElementById('takeawayText').textContent =
    `That is ${cadence}. In the recorded sample of ${cs.n_days.toLocaleString()} days, ${crossings.toLocaleString()} days crossed this threshold.`;

  const crossEl = document.getElementById('observedCrossings');
  const peakEl  = document.getElementById('observedPeak');

  if (firstLoad) {
    countUp(crossEl, crossings, `/${cs.n_days.toLocaleString()}`, 0, 600);
    countUp(peakEl,  peak, '°C', 1, 700);
  } else {
    if (crossEl) crossEl.textContent = `${crossings.toLocaleString()}/${cs.n_days.toLocaleString()}`;
    if (peakEl)  peakEl.textContent  = `${peak.toFixed(1)}°C`;
  }
}

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

function row(table, label, value, tooltip = null) {
  const tr = document.createElement('tr');
  const td1 = document.createElement('td');
  if (tooltip) {
    td1.innerHTML = `${label} <span class="help-icon" data-tip="${tooltip}"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17h.01"/></svg></span>`;
  } else {
    td1.textContent = label;
  }
  const td2 = document.createElement('td'); td2.textContent = value;
  tr.append(td1, td2); table.appendChild(tr);
}

function buildComparisonTable(data) {
  const t = document.getElementById('comparisonTable');
  const sim = data.simulation;
  t.innerHTML = '';
  row(t, 'Theoretical (fitted model)',     (sim.comparison.theoretical   * 100).toFixed(2) + '%', "Probability calculated purely from the mathematical curve of the model.");
  row(t, 'Monte Carlo (10,000 trials)',    (sim.comparison.monte_carlo_10k * 100).toFixed(2) + '%', "Probability generated by simulating 10,000 random futures.");
  row(t, 'Bootstrap (real data)',          (sim.comparison.bootstrap      * 100).toFixed(2) + '%', "Probability found by resampling the actual recorded historical data.");
  row(t, 'Return period',                 `1-in-${sim.return_period_days}-day event`, "The estimated average time between dangerous heat events.");
}

function buildStatsTable(data) {
  const t = document.getElementById('statsTable');
  const cs = data.core_stats;
  const info = data.dataset_info;
  t.innerHTML = '';
  if (info) {
    row(t, 'Location & Source', `${info.location_name} (Open-Meteo ERA5 API)`);
    row(t, 'Observation Period', `${info.start_date} to ${info.end_date}`);
  }
  row(t, 'Sample size', `${cs.n_days.toLocaleString()} consecutive days`);
  row(t, 'Historical Mean', `${cs.mean}°C  (95% CI ${cs.mean_ci95[0]}–${cs.mean_ci95[1]})`);
  if (cs.min_temp !== undefined && cs.max_temp !== undefined) {
    row(t, 'Recorded Range', `${cs.min_temp}°C (min) to ${cs.max_temp}°C (all-time peak)`);
  }
  row(t, 'Std. deviation', `${cs.std_dev}°C  (95% CI ${cs.std_dev_ci95[0]}–${cs.std_dev_ci95[1]})`, "Average amount temperatures vary from the mean. Higher means more volatile.");
  row(t, 'Coeff. of variation', `${cs.cv_percent}%  (95% CI ${cs.cv_percent_ci95[0]}–${cs.cv_percent_ci95[1]})`, "Ratio of the standard deviation to the mean. Measures overall relative volatility.");
  row(t, 'Normality check', `${cs.shapiro_wilk.is_normal_at_5pct ? 'Normal' : 'Non-Normal'} (p=${cs.shapiro_wilk.p_value})`, "Statistical tests show non-normality due to distinct seasonal patterns.");
}

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

function buildTimelineChart(data) {
  const canvas = document.getElementById('timelineCanvas');
  if (!canvas || typeof Chart === 'undefined') return;

  const cs = data.core_stats;
  const trend = data.trend;
  const residuals = trend?.residuals || [];
  const nDays = cs.n_days;
  const projDays = 7;
  const totalDays = nDays + projDays;

  // Windowing logic for the pan slider
  const panSlider = document.getElementById('panSlider');
  const panFrac = (panSlider ? parseFloat(panSlider.value) : 100) / 100;
  const visibleSpan = Math.min(totalDays, 45); // show 45 days window
  const maxStart = totalDays - visibleSpan;
  const start = Math.max(0, Math.round(maxStart * panFrac));
  const end = Math.min(totalDays, start + visibleSpan);

  const datesList = trend?.dates || [];
  const labels = [];
  for (let i = start; i < end; i++) {
    if (i < nDays && datesList[i]) {
      const d = new Date(datesList[i]);
      labels.push(d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: '2-digit' }));
    } else if (i < nDays) {
      labels.push(`Day ${i + 1}`);
    } else {
      labels.push(`+${i - nDays + 1}d Proj`);
    }
  }

  const recorded = [];
  const projected = [];
  const threshold = [];

  for (let i = 0; i < totalDays; i++) {
    const expected = cs.mean + trend.slope_c_per_day * (i - nDays / 2);
    threshold.push(currentThreshold);

    if (i < nDays) {
      recorded.push(expected + (residuals[i] || 0));
      projected.push(null);
    } else {
      if (i === nDays) {
        const lastRec = expected - trend.slope_c_per_day + (residuals[nDays - 1] || 0);
        recorded.push(null);
        projected[nDays - 1] = lastRec;
      }
      projected.push(expected);
    }
  }

  const slicedRecorded = recorded.slice(start, end);
  const slicedProjected = projected.slice(start, end);
  const slicedThreshold = threshold.slice(start, end);

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const { tick, grid } = getChartColors(isDark);

  if (timelineChart) timelineChart.destroy();

  const ctx = canvas.getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, isDark ? 'rgba(41,128,185,0.6)' : 'rgba(41,128,185,0.3)');
  gradient.addColorStop(1, 'rgba(41,128,185,0)');

  timelineChart = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Recorded Temp',
          data: slicedRecorded,
          borderColor: '#2980b9',
          backgroundColor: gradient,
          borderWidth: 2.5,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: ctx => ctx.raw > currentThreshold ? '#e05a3a' : '#2980b9',
          pointBorderColor: isDark ? '#1a2e3b' : '#fff',
          pointBorderWidth: 1.5,
          pointRadius: ctx => (ctx.raw > currentThreshold || ctx.dataIndex === slicedRecorded.length - 1) ? 5 : 0,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: ctx => ctx.raw > currentThreshold ? '#e05a3a' : '#2980b9'
        },
        {
          label: 'Projected Mean',
          data: slicedProjected,
          borderColor: '#27ae60',
          borderWidth: 2.5,
          borderDash: [5, 5],
          fill: false,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 5
        },
        {
          label: 'Danger Threshold',
          data: slicedThreshold,
          borderColor: '#e05a3a',
          borderWidth: 2,
          borderDash: [6, 4],
          fill: false,
          pointRadius: 0,
          pointHoverRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: { color: tick, usePointStyle: true, boxWidth: 8, font: {family: 'Inter, sans-serif'} }
        },
        tooltip: {
          backgroundColor: isDark ? '#fff' : '#1a2e3b',
          titleColor: isDark ? '#1a2e3b' : '#fff',
          bodyColor: isDark ? '#1a2e3b' : '#fff',
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: ctx => {
              if (ctx.dataset.label === 'Danger Threshold') return null;
              return ` ${ctx.dataset.label}: ${ctx.raw.toFixed(1)}°C`;
            }
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: tick, maxTicksLimit: 12, font: {family: 'Inter, sans-serif'} } },
        y: { grid: { color: grid }, ticks: { color: tick, font: {family: 'Inter, sans-serif'}, callback: v => v + '°C' } }
      }
    }
  });
}
