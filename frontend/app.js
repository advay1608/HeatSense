'use strict';

/* ── Global state ─────────────────────────────────────────── */
let DATA              = null;
let currentModel      = null;
let currentThreshold  = 36.0;
let prevBand          = null;
let sensitivityChart  = null;
let aicChart           = null;
let timelineChart     = null;
let liveForecastData  = null;

/* ── Arc gauge math constants ─────────────────────────────── */
const ARC_R     = 100;
const ARC_CX    = 130;
const ARC_CY    = 130;
const ARC_LEN   = Math.PI * ARC_R;
const ARC_MAX_P = 0.50;

fetch('./results.snapshot.json')
  .then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  })
  .then(data => {
    DATA = data;
    init(data);
  })
  .catch(err => {
    document.getElementById('metaLine').textContent =
      'Could not load results.snapshot.json - please run: python backend/scripts/run_pipeline.py';
    document.body.classList.remove('loading');
    console.error('Snapshot load error:', err);
  });

/* ── Distribution CDF implementations ─────────────────────── */
function erf(x) {
  const sign = x < 0 ? -1 : 1;
  x = Math.abs(x);
  const a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741, a4 = -1.453152027, a5 = 1.061405429, p = 0.3275911;
  const t = 1 / (1 + p * x);
  return sign * (1 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x));
}

function normalCDF(x, loc, scale) {
  return 0.5 * (1 + erf((x - loc) / (scale * Math.SQRT2)));
}

function lognormCDF(x, s, loc, scale) {
  if (x - loc <= 0) return 0;
  if (!s || s <= 0) return x >= scale + loc ? 1 : 0;
  return normalCDF(Math.log(x - loc), Math.log(scale), s);
}

function gumbelCDF(x, loc, scale) {
  return Math.exp(-Math.exp(-(x - loc) / scale));
}

function gammaln(x) {
  const g = 7;
  const c = [
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
      n++;
      term *= x / n;
      sum += term;
      if (Math.abs(term) < Math.abs(sum) * 1e-12) break;
    }
    return sum * Math.exp(-x + a * Math.log(x) - gammaln(a));
  }
  let b = x + 1 - a, c = 1e308, d = 1 / b, h = d;
  for (let i = 1; i < 200; i++) {
    const an = -i * (i - a);
    b += 2;
    d = an * d + b;
    if (Math.abs(d) < 1e-30) d = 1e-30;
    c = b + an / c;
    if (Math.abs(c) < 1e-30) c = 1e-30;
    d = 1 / d;
    const del = d * c;
    h *= del;
    if (Math.abs(del - 1) < 1e-12) break;
  }
  return 1 - Math.exp(-x + a * Math.log(x) - gammaln(a)) * h;
}

function gammaCDF(x, a, loc, scale) {
  return x - loc <= 0 ? 0 : lowerIncompleteGammaRegularized(a, (x - loc) / scale);
}

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
  return p === null ? null : Math.max(0, Math.min(1, 1 - p));
}

function modelLabel(name) {
  return ({ normal: 'Normal', lognorm: 'Log-normal', gamma: 'Gamma', gumbel_r: 'Gumbel' })[name] || name;
}

function bandFor(prob) {
  if (prob <= 0.05) return 'low';
  if (prob <= 0.20) return 'moderate';
  return 'high';
}

/* ── UI utilities ─────────────────────────────────────────── */
function initDarkMode() {
  const urlParams   = new URLSearchParams(window.location.search);
  const themeParam  = urlParams.get('theme');
  const saved       = themeParam || localStorage.getItem('heatsense-theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const isDark      = saved ? saved === 'dark' : prefersDark;
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

function initArcGaugeTicks() {
  const tickLow = document.getElementById('tickLow');
  const tickMod = document.getElementById('tickMod');
  const pLow = 0.05;
  const pMod = 0.20;

  function setTick(el, p) {
    if (!el) return;
    const frac = Math.min(Math.max(p / ARC_MAX_P, 0), 1);
    const angle = Math.PI - frac * Math.PI;
    const r1 = ARC_R - 8;
    const r2 = ARC_R + 8;
    el.setAttribute('x1', (ARC_CX + r1 * Math.cos(angle)).toFixed(1));
    el.setAttribute('y1', (ARC_CY - r1 * Math.sin(angle)).toFixed(1));
    el.setAttribute('x2', (ARC_CX + r2 * Math.cos(angle)).toFixed(1));
    el.setAttribute('y2', (ARC_CY - r2 * Math.sin(angle)).toFixed(1));
  }
  setTick(tickLow, pLow);
  setTick(tickMod, pMod);
}

function updateArcGauge(prob) {
  const arcFill   = document.getElementById('arcFill');
  const arcNeedle = document.getElementById('arcNeedle');
  const arcBand   = document.getElementById('arcBandText');
  if (!arcFill) return;

  const fillFrac   = prob !== null ? Math.max(0, Math.min(prob / ARC_MAX_P, 1)) : 0;
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
    arcBand.textContent = band.charAt(0).toUpperCase() + band.slice(1) + ' historical frequency';
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

function getRecordedTemps() {
  if (DATA._recordedTemps) return DATA._recordedTemps;
  if (DATA.trend?.daily_temperatures && Array.isArray(DATA.trend.daily_temperatures)) {
    DATA._recordedTemps = DATA.trend.daily_temperatures;
    return DATA._recordedTemps;
  }
  const trend = DATA.trend;
  const residuals = trend?.residuals || [];
  DATA._recordedTemps = residuals.map((r, i) => {
    return (trend?.intercept_c !== undefined && trend?.slope_c_per_day !== undefined)
      ? (trend.intercept_c + trend.slope_c_per_day * i + r)
      : (DATA.core_stats.mean + r);
  });
  return DATA._recordedTemps;
}

function computeLiveExceedance(threshold) {
  const temps = getRecordedTemps();
  let count = 0;
  for (let i = 0; i < temps.length; i++) {
    if (temps[i] > threshold) count++;
  }
  const prob = temps.length > 0 ? count / temps.length : 0;
  return { count, total: temps.length, prob };
}

function updateLiveComparison() {
  const grid    = document.getElementById('liveCompGrid');
  const thrSpan = document.getElementById('liveCompThreshold');
  const diagBox = document.getElementById('gofDiagnosticNote');
  if (!grid || !DATA) return;
  if (thrSpan) thrSpan.textContent = currentThreshold.toFixed(1);

  const dfit = DATA.distribution_fit;
  const emp = computeLiveExceedance(currentThreshold);
  grid.innerHTML = '';

  // 1. Empirical Ground Truth item
  const empDiv = document.createElement('div');
  empDiv.className = 'live-comp-item best-model';
  empDiv.style.borderLeft = '3px solid var(--green)';
  empDiv.innerHTML = `
    <div class="live-comp-name" style="color:var(--green)">Empirical Baseline ★</div>
    <div class="live-comp-prob">${(emp.prob * 100).toFixed(2)}%</div>
    <div class="live-comp-bar-track"><div class="live-comp-bar" style="width:${Math.min(emp.prob * 100, 100).toFixed(1)}%; background:var(--green)"></div></div>
    <div class="live-comp-aic">${emp.count.toLocaleString()} / ${emp.total.toLocaleString()} valid days <span class="help-icon" data-tip="Directly observed historical proportion exceeding threshold. Primary verifiable ground truth."><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17h.01"/></svg></span></div>
  `;
  grid.appendChild(empDiv);

  // 2. Candidate distribution models
  dfit.candidates.forEach(c => {
    const prob = probExceeds(c.name, c.params, currentThreshold);
    const pct  = prob !== null ? prob * 100 : null;
    const fillW = prob !== null ? Math.min(prob * 100, 100) : 0;
    const isSelected = c.name === currentModel;

    const div = document.createElement('div');
    div.className = `live-comp-item${isSelected ? ' best-model' : ''}`;
    div.innerHTML = `
      <div class="live-comp-name">${modelLabel(c.name)}${c.name === dfit.best_model ? ' (Lowest AIC)' : ''}</div>
      <div class="live-comp-prob">${pct !== null ? pct.toFixed(2) + '%' : '—'}</div>
      <div class="live-comp-bar-track"><div class="live-comp-bar" style="width:${fillW.toFixed(1)}%"></div></div>
      <div class="live-comp-aic">AIC ${c.aic.toLocaleString()} | KS p ${c.goodness_of_fit?.ks_p_value_formatted || '< 0.0001'}</div>
    `;
    grid.appendChild(div);
  });

  if (diagBox) {
    diagBox.innerHTML = `
      <strong>Statistical Goodness-of-Fit Diagnostic:</strong> While <em>${modelLabel(dfit.best_model)}</em> has the lowest AIC penalty among candidates,
      formal Kolmogorov-Smirnov tests reject all four single annual distributions (p &lt; 0.0001) due to strong annual seasonal oscillations (winter cold vs. summer heatwaves).
      <strong>The empirical exceedance rate (${(emp.prob * 100).toFixed(2)}%) is the primary, directly verifiable baseline.</strong>
    `;
  }
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
    tick: isDark ? '#506980' : '#7a8fa0',
    grid: isDark ? 'rgba(255,255,255,.04)' : 'rgba(0,0,0,.05)',
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
  const empProbs = (sens.empirical_probabilities || sens.probabilities).map(p => +(p * 100).toFixed(2));
  const paramProbs = sens.probabilities.map(p => +(p * 100).toFixed(2));

  if (sensitivityChart) sensitivityChart.destroy();
  sensitivityChart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Empirical Historical Rate (%)',
          data: empProbs,
          backgroundColor: 'rgba(39, 174, 96, 0.75)',
          borderColor: 'rgb(39, 174, 96)',
          borderWidth: 1.5,
          borderRadius: 6,
        },
        {
          label: `Parametric Model (${modelLabel(data.distribution_fit?.best_model)}) (%)`,
          data: paramProbs,
          backgroundColor: 'rgba(41, 128, 185, 0.65)',
          borderColor: 'rgb(41, 128, 185)',
          borderWidth: 1.5,
          borderRadius: 6,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true, position: 'top', labels: { color: tick, font: { size: 11, family: 'Inter, sans-serif' } } },
        tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)}% exceedance` } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: tick, font: { size: 12, family: 'Inter, sans-serif' } } },
        y: {
          grid: { color: grid },
          ticks: { color: tick, font: { size: 11, family: 'Inter, sans-serif' }, callback: v => v + '%' },
          title: { display: true, text: 'Exceedance rate (%)', color: tick, font: { size: 11, family: 'Inter, sans-serif' } }
        }
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
  const deltaAics = aics.map(a => +(a - minAic).toFixed(2));

  const colors = dfit.candidates.map(c =>
    c.name === dfit.best_model ? 'rgba(41,128,185,.85)' : 'rgba(122,143,160,.55)'
  );
  const borders = dfit.candidates.map(c =>
    c.name === dfit.best_model ? 'rgb(41,128,185)' : 'rgb(122,143,160)'
  );

  if (aicChart) aicChart.destroy();
  aicChart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'ΔAIC Penalty (0 = Best Fit)',
        data: deltaAics,
        backgroundColor: colors,
        borderColor: borders,
        borderWidth: 2,
        borderRadius: 6,
        borderSkipped: false
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              const raw = aics[ctx.dataIndex];
              const delta = ctx.parsed.y;
              return delta === 0
                ? ` ΔAIC: 0.00 (Best relative fit! Raw AIC: ${raw.toLocaleString()})`
                : ` ΔAIC: +${delta.toFixed(2)} penalty (Raw AIC: ${raw.toLocaleString()})`;
            }
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: tick, font: { size: 12, family: 'Inter, sans-serif' } } },
        y: {
          grid: { color: grid },
          beginAtZero: true,
          ticks: { color: tick, font: { size: 11, family: 'Inter, sans-serif' }, callback: v => '+' + v },
          title: { display: true, text: 'ΔAIC relative penalty (lower = better relative parsimony)', color: tick, font: { size: 11, family: 'Inter, sans-serif' } }
        }
      }
    }
  });
}

function fetchLiveForecastClient() {
  const lat = DATA?.dataset_info?.latitude || 19.0760;
  const lon = DATA?.dataset_info?.longitude || 72.8777;
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&daily=temperature_2m_max&timezone=Asia%2FKolkata&forecast_days=7`;

  fetch(url)
    .then(r => r.json())
    .then(apiData => {
      const daily = apiData.daily;
      if (daily && daily.time && daily.temperature_2m_max) {
        const pi_1 = 0.00945;
        const lambda_markov = 0.3805;
        const nowIst = new Date();
        const todayStr = nowIst.toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' }); // YYYY-MM-DD
        const istTimeStr = nowIst.toLocaleString('en-GB', {
          timeZone: 'Asia/Kolkata',
          day: 'numeric',
          month: 'short',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        }) + ' IST';

        const days = daily.time.map((d, i) => {
          const tVal = daily.temperature_2m_max[i];
          const isToday = (d === todayStr || i === 0);
          const isFuture = (d > todayStr);
          const leadDays = i;
          // Decouple Markov persistence scenario: Day 1 is conditioning state S_0 (no false 100% assignment)
          const markovP = isToday ? null : Math.round((pi_1 + Math.pow(lambda_markov, leadDays) * (1.0 - pi_1)) * 10000) / 10000;
          return {
            day_index: i + 1,
            lead_days: leadDays,
            date: d,
            forecast_max_temp_c: tVal !== null ? parseFloat(tVal) : null,
            is_today: isToday,
            is_future: isFuture,
            phase: isToday ? 'today_current_cycle' : 'future_nwp_projection',
            historical_markov_scenario: {
              is_conditioning_state: isToday,
              conditional_exceedance_probability: markovP,
              disclaimer: isToday
                ? 'Observed conditioning state S_0, not a forward transition probability.'
                : 'Exploratory historical persistence scenario; NOT a calibrated future weather probability from Open-Meteo.'
            },
            validation: {
              is_validated: false,
              observed_proxy_max_temp_c: isToday ? tVal : null,
              difference_c: isToday ? 0.0 : null,
              verification_target: 'ERA5 Reanalysis Grid Proxy (19.0861°N, 72.8529°E)',
              status: isToday ? 'same_day_diagnostic_excluded' : 'pending_future_observation',
              note: isToday
                ? 'Current-Day Diagnostic — Excluded from Out-of-Sample Validation.'
                : 'Awaiting conclusion of target date observation cycle.'
            }
          };
        });

        liveForecastData = {
          status: 'live',
          source: 'Open-Meteo Numerical Weather Prediction (NWP) Forecast API',
          retrieval_timestamp_utc: new Date().toISOString(),
          retrieval_timestamp_ist: istTimeStr,
          retrieved_at: new Date().toISOString(),
          timing_disclosure: 'Timestamp reflects client data retrieval time from API, not NWP model run cycle initialization.',
          days: days,
          validation_summary: DATA?.forecast?.validation_summary || {
            total_target_days: days.length,
            n_validated_pairs: 0,
            n_out_of_sample_validated: 0,
            n_same_day_diagnostic_excluded: 1,
            n_pending_future_days: days.length - 1,
            mae_c: null,
            bias_c: null,
            verification_target_nature: 'ECMWF ERA5 Reanalysis Grid Proxy (Area-averaged cell). Notice: Reanalysis estimates share numerical parameterization errors with NWP models and do not constitute independent physical station verification.',
            status_statement: '0 out-of-sample forecast dates validated. 1 current-day diagnostic excluded from out-of-sample validation. 6 future forecast dates await observation.'
          }
        };
        buildForecast(DATA);
        buildTimelineChart(DATA);
      }
    })
    .catch(err => {
      console.warn('Client forecast fetch unavailable; using snapshot forecast:', err);
    });
}

function init(data) {
  const dfit = data.distribution_fit;
  const urlParams = new URLSearchParams(window.location.search);
  const qModel    = urlParams.get('model');
  const qThresh   = parseFloat(urlParams.get('threshold'));

  currentModel    = (qModel && dfit.candidates.some(c => c.name === qModel)) ? qModel : dfit.best_model;
  currentThreshold = (!isNaN(qThresh) && qThresh >= 10 && qThresh <= 60) ? qThresh : dfit.threshold_c;

  const locName = data.dataset_info?.location_name || 'Mumbai, Maharashtra, India';
  const startYear = data.dataset_info?.start_date ? data.dataset_info.start_date.slice(0, 4) : '1950';
  const endYear = data.dataset_info?.end_date ? data.dataset_info.end_date.slice(0, 4) : '2026';
  const spanStr = ` (${startYear}–${endYear})`;

  document.title = `${locName} — HeatSense Risk Dashboard`;

  const heroLabel = document.getElementById('heroLabel');
  if (heroLabel) heroLabel.textContent = `Historical Climate Baseline · ${locName}`;

  const heroDesc = document.getElementById('heroDesc');
  if (heroDesc) {
    heroDesc.textContent = `Long-run empirical proportion of daily maximum temperatures exceeding your selected threshold across ${data.core_stats.n_days.toLocaleString()} daily records from ${startYear} to ${endYear} in ${locName} (ECMWF ERA5 reanalysis). This reflects historical baseline frequency, strictly distinct from today's numerical weather forecast.`;
  }

  document.getElementById('metaLine').textContent =
    `${locName} · ${data.core_stats.n_days.toLocaleString()} days${spanStr} · best fit: ${modelLabel(dfit.best_model)}`;
  const tStatus = document.getElementById('topbarStatus');
  if (tStatus) tStatus.textContent = `${locName} · ERA5 & NWP`;

  const footerMeta = document.getElementById('footerMeta');
  if (footerMeta && data.dataset_info) {
    footerMeta.innerHTML = `Data: <strong>${data.dataset_info.location_name}</strong> · ${data.dataset_info.source} (${data.dataset_info.start_date} to ${data.dataset_info.end_date}) · ${data.core_stats.n_days.toLocaleString()} valid observations`;
  }

  initArcGaugeTicks();

  const slider = document.getElementById('thresholdSlider');
  if (slider && data.core_stats) {
    const minVal = Math.floor(data.core_stats.min_temp !== undefined ? data.core_stats.min_temp : 20);
    const maxVal = Math.ceil(data.core_stats.max_temp !== undefined ? data.core_stats.max_temp : 50);
    slider.min = Math.max(15, minVal);
    slider.max = Math.min(55, maxVal);
    slider.value = currentThreshold;

    const bounds = document.querySelectorAll('.slider-bounds span');
    if (bounds.length >= 2) {
      bounds[0].textContent = slider.min + '°C';
      bounds[1].textContent = slider.max + '°C';
    }

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
  buildSeasonalTable(data);
  buildStatsTable(data);
  buildAssumptions(data);
  buildSynthesis(data);
  buildSensitivityChart(data);
  buildAicChart(data);
  updateLiveComparison();
  setupNavHighlighting();
  initHelpTooltips();
  initExports(data);

  document.getElementById('panSlider')?.addEventListener('input', () => {
    if (timelineChart) timelineChart.options.animation = false;
    buildTimelineChart(DATA);
  });

  document.body.classList.remove('loading');
  render(true);

  // Attempt live client forecast fetch in background
  fetchLiveForecastClient();
}

function render(firstLoad = false) {
  document.getElementById('thresholdVal').textContent = currentThreshold.toFixed(1);

  // 1. Empirical Ground Truth Calculation
  const emp = computeLiveExceedance(currentThreshold);
  const empiricalProb = emp.prob;
  const empiricalPct  = (empiricalProb * 100).toFixed(2);

  // 2. Active Model Parametric Exceedance Probability
  const dfit = DATA.distribution_fit;
  const cand = dfit.candidates.find(c => c.name === currentModel);
  let modelProb = null;
  if (cand) modelProb = probExceeds(currentModel, cand.params, currentThreshold);
  if (modelProb === null || modelProb === undefined || Number.isNaN(modelProb)) {
    modelProb = currentModel === dfit.best_model ? dfit.theoretical_probability : null;
  }
  const modelPct = modelProb !== null ? (modelProb * 100).toFixed(2) : 'n/a';

  // 3. Update Hero Arc Gauge to display empirical ground truth baseline
  const arcProbEl = document.getElementById('arcProbText');
  if (arcProbEl) arcProbEl.textContent = empiricalPct + '%';

  updateArcGauge(empiricalProb);

  const retPeriodEl = document.getElementById('returnPeriod');
  if (retPeriodEl) {
    retPeriodEl.textContent = empiricalProb > 0
      ? `≈ 1 in ${(1 / empiricalProb).toFixed(1)} days historical spacing (${emp.count.toLocaleString()} of ${emp.total.toLocaleString()} days; extremes cluster in multi-day events)`
      : `0 recorded historical crossings at ${currentThreshold.toFixed(1)}°C`;
  }

  const crosscheckEl = document.getElementById('heroCrosscheck');
  if (crosscheckEl) {
    crosscheckEl.innerHTML = `Fitted <strong>${modelLabel(currentModel)}</strong>: ${modelPct}% | Empirical Rate: <strong>${empiricalPct}%</strong>`;
  }

  const band   = bandFor(empiricalProb);
  const bandEl = document.getElementById('riskBand');
  bandEl.textContent = band.charAt(0).toUpperCase() + band.slice(1) + ' (Historical)';
  bandEl.className = `risk-band-pill band-${band}`;

  updateHeroColor(band);

  if (!firstLoad && prevBand !== null && prevBand !== band) {
    showToast(`Historical exceedance level changed to ${band.toUpperCase()}`, band);
  }
  prevBand = band;

  document.getElementById('modelNote').textContent =
    `${modelLabel(currentModel)} · AIC: ${cand ? cand.aic.toLocaleString() : '—'} · (Rule: temp > ${currentThreshold.toFixed(1)}°C)`;

  updateTakeaway(empiricalProb, modelProb, emp);
  buildForecast(DATA);
  updateLiveComparison();
  buildComparisonTable(DATA);
  buildSeasonalTable(DATA);
  buildSynthesis(DATA);
  buildTimelineChart(DATA);
  updateExportsUI();
}

function buildForecast(data) {
  const grid = document.getElementById('forecastGrid');
  const note = document.getElementById('forecastNote');
  if (!grid) return;

  const fcSource = liveForecastData || data.forecast;
  const days = fcSource?.days || [];

  if (!days.length) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; padding: 1.5rem; text-align: center; color: var(--ink-3); background: var(--surface); border: 1px dashed var(--border); border-radius: var(--radius-sm);">
        7-Day Numerical Weather Forecast temporarily unavailable. Predictions are never artificially generated from historical distributions.
      </div>
    `;
    if (note) note.textContent = 'Forecast offline';
    return;
  }

  // Format retrieval timestamp in IST (labeled as data retrieval time, not upstream model issue time)
  let retrievedDisplay = 'Recent';
  const now = new Date();
  if (fcSource.retrieved_at || fcSource.retrieval_timestamp_utc || fcSource.retrieval_timestamp_ist) {
    try {
      const rawIso = fcSource.retrieved_at || fcSource.retrieval_timestamp_utc;
      let d = rawIso ? new Date(rawIso) : null;
      if (d && !isNaN(d.getTime())) {
        // Prevent displaying a retrieval time in the future relative to the client clock
        if (d.getTime() > now.getTime()) {
          d = now;
        }
        retrievedDisplay = d.toLocaleString('en-GB', {
          timeZone: 'Asia/Kolkata',
          day: 'numeric',
          month: 'short',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        }) + ' IST';
      } else if (fcSource.retrieval_timestamp_ist) {
        retrievedDisplay = fcSource.retrieval_timestamp_ist;
      }
    } catch (_) {
      retrievedDisplay = fcSource.retrieval_timestamp_ist || 'Recent';
    }
  }

  if (note) {
    note.textContent = `Data Retrieval Time: ${retrievedDisplay} · Open-Meteo NWP Grid`;
    note.title = 'Client data retrieval query time from Open-Meteo API (Asia/Kolkata). Model initialization cycle maintained by upstream numerical weather provider.';
  }

  // Render cards
  const cards = days.map((dItem, idx) => {
    const temp = dItem.forecast_max_temp_c;
    const isExceed = temp !== null && temp > currentThreshold;
    const diff = temp !== null ? (temp - currentThreshold).toFixed(1) : 0;
    const isToday = dItem.is_today || (idx === 0);

    let weekdayStr = '';
    let dayMonthStr = '';
    if (dItem.date) {
      const parts = dItem.date.split('-');
      if (parts.length === 3) {
        const d = new Date(Date.UTC(+parts[0], +parts[1] - 1, +parts[2]));
        weekdayStr = d.toLocaleDateString('en-GB', { weekday: 'short' });
        dayMonthStr = d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
      }
    }

    let dateTitle = '';
    let phaseBadge = '';
    let statProbHtml = '';
    let ciHtml = '';
    let valHtml = '';

    if (isToday) {
      dateTitle = `Today · ${weekdayStr}, ${dayMonthStr}`;
      phaseBadge = `<span class="forecast-phase-badge today">Today · Active Day</span>`;
      statProbHtml = `<span class="forecast-prob-badge" title="Observed conditioning state S_0">Conditioning State S₀</span>`;
      ciHtml = ``; // No uncalibrated prediction intervals
      valHtml = `<span class="forecast-val-badge val-excluded" title="Current-day diagnostic comparison against ERA5 grid proxy. Retrieved during active daytime cycle prior to local day conclusion; strictly excluded from out-of-sample validation.">Current-Day Diagnostic — Excluded from Out-of-Sample Validation</span>`;
    } else {
      const leadK = dItem.lead_days || idx;
      dateTitle = `${weekdayStr}, ${dayMonthStr} (+${leadK}d)`;
      phaseBadge = `<span class="forecast-phase-badge future">Future NWP Projection</span>`;

      const markovP = dItem.historical_markov_scenario?.conditional_exceedance_probability ?? dItem.statistical_prediction?.markov_conditional_prob;
      if (markovP !== undefined && markovP !== null) {
        statProbHtml = `<span class="forecast-prob-badge" title="Exploratory historical Markov persistence scenario (not an NWP forecast probability; subject to strong seasonal limits)">Markov Scenario: ${(markovP * 100).toFixed(1)}% (Exploratory)</span>`;
      } else {
        statProbHtml = `<span class="forecast-prob-badge" title="Baseline empirical rate">Baseline P: 0.95%</span>`;
      }

      ciHtml = ``; // Raw NWP temperatures without uncalibrated 95% intervals
      valHtml = `<span class="forecast-val-badge val-pending" title="Target date has not concluded. Forecast snapshot logged prior to target date.">⏳ Pending Verification</span>`;
    }

    const statusHtml = isExceed
      ? `<span class="forecast-day-status status-above">⚠️ Exceeds threshold (+${diff}°C)</span>`
      : `<span class="forecast-day-status status-below">✓ ${Math.abs(diff).toFixed(1)}°C below threshold</span>`;

    return `
      <div class="forecast-day${isToday ? ' today' : ''}${isExceed ? ' hot' : ''}">
        ${phaseBadge}
        <span class="forecast-day-label" style="margin-top: 0.2rem;">${dateTitle}</span>
        <strong class="forecast-day-temp">${temp !== null ? temp.toFixed(1) + '°C' : '—'}</strong>
        ${statProbHtml}
        ${ciHtml}
        ${statusHtml}
        ${valHtml}
      </div>
    `;
  });

  grid.innerHTML = cards.join('');

  // Update validation ledger summary in UI if elements exist
  const valPairsEl = document.getElementById('valPairsCount');
  const valExcludedEl = document.getElementById('valExcludedCount');
  const valPendingEl = document.getElementById('valPendingCount');
  const valMaeBiasEl = document.getElementById('valMaeBias');
  const vs = fcSource.validation_summary;
  if (vs) {
    if (valPairsEl) {
      valPairsEl.textContent = `${vs.n_out_of_sample_validated ?? vs.n_validated_pairs ?? 0} dates (Strict out-of-sample rule)`;
      valPairsEl.style.color = 'var(--ink-2)';
    }
    if (valExcludedEl) {
      const exDates = vs.same_day_diagnostic_dates || [];
      let exDateStr = '11 Oct 2026';
      if (exDates.length > 0) {
        exDateStr = exDates.map(d => {
          const parts = d.split('-');
          if (parts.length === 3) {
            const dt = new Date(Date.UTC(+parts[0], +parts[1] - 1, +parts[2]));
            return dt.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
          }
          return d;
        }).join(', ');
      }
      const nEx = vs.n_same_day_diagnostic_excluded ?? exDates.length ?? 1;
      valExcludedEl.textContent = `${nEx} date (${exDateStr})`;
    }
    if (valPendingEl) {
      const pDates = vs.pending_dates || days.slice(1).map(d => d.date).filter(Boolean);
      let pRangeStr = '';
      if (pDates.length > 0) {
        const fmtDate = (dStr) => {
          const parts = dStr.split('-');
          if (parts.length === 3) {
            const dt = new Date(Date.UTC(+parts[0], +parts[1] - 1, +parts[2]));
            return dt.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
          }
          return dStr;
        };
        const yearStr = pDates[0].length >= 4 ? ` ${pDates[0].slice(0, 4)}` : '';
        pRangeStr = pDates.length === 1
          ? `${fmtDate(pDates[0])}${yearStr}`
          : `${fmtDate(pDates[0])}–${fmtDate(pDates[pDates.length - 1])}${yearStr}`;
      } else {
        pRangeStr = 'awaiting observation';
      }
      const nPend = vs.n_pending_future_days ?? pDates.length ?? 6;
      valPendingEl.textContent = `${nPend} dates (${pRangeStr})`;
    }
    if (valMaeBiasEl) {
      if (vs.mae_c !== null && vs.mae_c !== undefined) {
        valMaeBiasEl.textContent = `MAE: ${vs.mae_c.toFixed(1)}°C · Bias: ${vs.bias_c.toFixed(1)}°C`;
      } else {
        valMaeBiasEl.textContent = `MAE: N/A · Bias: N/A (Awaiting observation)`;
      }
    }
  }
}

function updateTakeaway(empiricalProb, modelProb, emp) {
  const cs = DATA.core_stats;
  const count = emp ? emp.count : 0;
  const total = emp ? emp.total : cs.n_days;

  const percent = `${(empiricalProb * 100).toFixed(2)}%`;
  const cadence = empiricalProb > 0
    ? `an average historical spacing of 1 in ${(1 / empiricalProb).toFixed(1)} days (inverse empirical rate; not a regular schedule because extremes cluster in multi-day events)`
    : '0 days in the historical record';

  document.getElementById('takeawayTitle').textContent =
    `${percent} empirical exceedance rate at ${currentThreshold.toFixed(1)}°C`;
  document.getElementById('takeawayText').textContent =
    `This represents ${cadence}. In the historical record of ${total.toLocaleString()} valid days, exactly ${count.toLocaleString()} days crossed this threshold (rule: temp > ${currentThreshold.toFixed(1)}°C). Under the fitted ${modelLabel(currentModel)} model, the parametric estimate is ${(modelProb * 100).toFixed(2)}%.`;

  const crossEl = document.getElementById('observedCrossings');
  const peakEl  = document.getElementById('observedPeak');

  if (crossEl) crossEl.textContent = `${count.toLocaleString()} / ${total.toLocaleString()}`;
  if (peakEl)  peakEl.textContent  = `${cs.max_temp.toFixed(1)}°C`;
}

function buildModelToggle(dfit) {
  const wrap = document.getElementById('modelToggle');
  wrap.innerHTML = '';
  dfit.candidates.forEach(c => {
    const btn = document.createElement('button');
    btn.className = `model-btn${c.name === currentModel ? ' active' : ''}${c.name === dfit.best_model ? ' best' : ''}`;
    btn.textContent = modelLabel(c.name);
    btn.title = `AIC: ${c.aic} | BIC: ${c.bic} | Log-likelihood: ${c.log_likelihood}`;
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
  const td2 = document.createElement('td');
  td2.textContent = value;
  tr.append(td1, td2);
  table.appendChild(tr);
}

function buildComparisonTable(data) {
  const t = document.getElementById('comparisonTable');
  if (!t) return;
  const emp = computeLiveExceedance(currentThreshold);
  const cand = data.distribution_fit?.candidates?.find(c => c.name === currentModel);
  const mProb = cand ? probExceeds(currentModel, cand.params, currentThreshold) : null;
  const sim = data.simulation;

  t.innerHTML = '';
  row(t, 'Empirical Baseline (Ground Truth)', `${(emp.prob * 100).toFixed(2)}% (${emp.count.toLocaleString()} / ${emp.total.toLocaleString()} days)`, `Observed proportion of historical days strictly exceeding ${currentThreshold.toFixed(1)}°C across ${data.core_stats.n_days.toLocaleString()} observations. Primary directly verifiable baseline.`);
  row(t, `Parametric Theoretical Model (${modelLabel(currentModel)})`, mProb !== null ? `${(mProb * 100).toFixed(2)}%` : '—', `Theoretical survival function under fitted ${modelLabel(currentModel)} distribution at ${currentThreshold.toFixed(1)}°C. Candidate comparison only.`);
  row(t, 'Log-Normal Monte Carlo (10k draws)', `${(sim.comparison.monte_carlo_10k * 100).toFixed(2)}%`, `Parametric random draws strictly sampled from the fitted best-fit Log-Normal model at canonical ${sim.threshold_c}°C. Confirms numerical convergence of theoretical survival function; does not validate whether the model is empirically true.`);
  row(t, 'Empirical Bootstrap Resampling (10k draws)', `${(sim.comparison.bootstrap * 100).toFixed(2)}%`, `Non-parametric resampling with replacement directly from ${data.core_stats.n_days.toLocaleString()} empirical observations at canonical ${sim.threshold_c}°C. Completely distribution-free and separate from both parametric estimates.`);
  row(t, 'Empirical Average Spacing (1/P)', emp.prob > 0 ? `1 in ${(1 / emp.prob).toFixed(1)} days` : 'rare event', `Inverse of long-run empirical exceedance rate. Extreme temperatures cluster in multi-day runs, so this is not a regular recurring schedule.`);
  row(t, 'Goodness-of-Fit Diagnostic', 'Rejected (KS p < 0.0001)', 'Strong annual seasonality violates unimodality, formally rejecting all single candidate distributions. Lowest AIC indicates relative ranking, not adequate absolute fit.');
}

function buildSeasonalTable(data) {
  const t = document.getElementById('seasonalTable');
  if (!t || !data.core_stats?.seasonal_summary) return;
  t.innerHTML = '';

  const header = document.createElement('tr');
  header.innerHTML = `
    <th style="text-align:left; padding:0.4rem 0; font-size:0.75rem; color:var(--ink-3);">Season</th>
    <th style="text-align:right; padding:0.4rem 0; font-size:0.75rem; color:var(--ink-3);">Mean Max</th>
    <th style="text-align:right; padding:0.4rem 0; font-size:0.75rem; color:var(--ink-3);">Peak Max</th>
    <th style="text-align:right; padding:0.4rem 0; font-size:0.75rem; color:var(--ink-3);">Days &gt; 36°C</th>
    <th style="text-align:right; padding:0.4rem 0; font-size:0.75rem; color:var(--ink-3);">Exceedance Rate</th>
  `;
  t.appendChild(header);

  data.core_stats.seasonal_summary.forEach(s => {
    const rateFrac = s.n_days > 0 ? (s.exceedance_count / s.n_days) : 0;
    const ratePct = (rateFrac * 100).toFixed(2);
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="padding:0.45rem 0; font-weight:600; color:var(--ink);">${s.season_name}</td>
      <td style="text-align:right; padding:0.45rem 0; color:var(--ink-2);">${s.mean_c.toFixed(1)}°C</td>
      <td style="text-align:right; padding:0.45rem 0; color:var(--red); font-weight:600;">${s.max_c.toFixed(1)}°C</td>
      <td style="text-align:right; padding:0.45rem 0; color:var(--ink-2);">${s.exceedance_count.toLocaleString()} / ${s.n_days.toLocaleString()}</td>
      <td style="text-align:right; padding:0.45rem 0; font-weight:700; color:${rateFrac > 0.3 ? 'var(--red)' : rateFrac > 0.05 ? 'var(--amber)' : 'var(--green-dark)'};">${ratePct}%</td>
    `;
    t.appendChild(tr);
  });
}

function buildStatsTable(data) {
  const t = document.getElementById('statsTable');
  const cs = data.core_stats;
  const info = data.dataset_info;
  const trend = data.trend;
  const dep = data.dependence;
  t.innerHTML = '';

  if (info) {
    row(t, 'Location & ERA5 Grid Point', `${info.location_name} (Grid: ${info.latitude}°N, ${info.longitude}°E, alt. ${info.elevation_m || 214}m)`, 'ECMWF ERA5 reanalysis grid-point estimate delivered via Open-Meteo API. Reflects atmospheric reanalysis assimilation, not direct readings from a single physical weather station.');
    row(t, 'Data Source & Variable', `${info.source} · ECMWF ERA5 (daily max near-surface temperature_2m_max, °C)`);
    row(t, 'Observation Period', `${info.start_date} to ${info.end_date} (${cs.n_days.toLocaleString()} valid days, ${cs.n_missing || 0} missing)`);
  } else {
    row(t, 'Sample Size', `${cs.n_days.toLocaleString()} consecutive days (${cs.n_missing || 0} missing)`);
  }
  row(t, 'Historical Mean', `${cs.mean}°C (95% CI ${cs.mean_ci95[0]}–${cs.mean_ci95[1]}°C)`);
  row(t, 'Median & IQR', `${cs.median_temp}°C (IQR: ${cs.iqr}°C, Q1: ${cs.q1}°C, Q3: ${cs.q3}°C)`);
  row(t, 'All-Time Record Range', `${cs.min_temp}°C (min) to ${cs.max_temp}°C (peak) — Range: ${cs.range_c}°C`);
  row(t, 'Sample Variance & SD', `Variance: ${cs.variance} | SD: ${cs.std_dev}°C (95% CI ${cs.std_dev_ci95[0]}–${cs.std_dev_ci95[1]}°C)`);
  const kelvinMeanVal = (cs.kelvin_mean !== undefined ? cs.kelvin_mean : (cs.mean + 273.15)).toFixed(2);
  row(t, 'Thermodynamic Relative Dispersion', `${cs.cv_kelvin_percent}% (Kelvin scale CV = s / ${kelvinMeanVal} K)`, 'Evaluated strictly on ratio Kelvin scale. Celsius CV is omitted because interval scales with arbitrary zeros yield physically meaningless CV percentages.');
  row(t, 'Canonical Exceedance (> 36°C)', `${cs.exceedance_count.toLocaleString()} days (${(cs.exceedance_proportion * 100).toFixed(2)}% of historical record)`);

  if (trend) {
    if (trend.complete_years_trend) {
      const cyt = trend.complete_years_trend;
      const r2Val = cyt.r_squared !== undefined ? cyt.r_squared.toFixed(3) : '0.289';
      row(t, 'Secular Trend (1950–2025 Complete Years)', `${cyt.slope_c_per_decade > 0 ? '+' : ''}${cyt.slope_c_per_decade}°C / decade (95% CI [${cyt.slope_ci95_per_decade[0]}, ${cyt.slope_ci95_per_decade[1]}], p = ${cyt.p_value_formatted}, R² = ${r2Val})`, 'Canonical annual trend across 76 complete calendar years (OLS on annual means). 2026 excluded as partial year (283 days) to avoid seasonal bias. Note: Inter-annual climatic memory requires cautious interpretation.');
    }
    const autoCorrVal = dep?.lag1_autocorrelation || 0.904;
    row(t, 'Continuous Daily Series Drift (1950–2026)', `${trend.slope_c_per_decade > 0 ? '+' : ''}${trend.slope_c_per_decade}°C / decade (total drift: ${trend.total_drift_c}°C across 28,042 days)`, `Linear regression on raw daily series. Caveat: Daily serial autocorrelation (ρ₁ = ${autoCorrVal}) violates OLS independence, making daily p-values overly optimistic.`);
  }
  if (dep) {
    row(t, 'Serial Dependence (Lag-1)', `ρ₁ = ${dep.lag1_autocorrelation} (Weekly ρ₇ = ${dep.multilag_autocorrelations?.lag_7 || '—'})`, 'Lag-1 autocorrelation. High persistence proves heat arrives in clusters.');
    row(t, 'Heatwave Cluster Share', `${dep.pct_extreme_days_in_multiday_clusters}% in multi-day runs (mean: ${dep.mean_run_length_above_threshold} days)`, 'Percentage of extreme days occurring in runs of 2+ days.');
    if (dep.transition_probabilities) {
      row(t, 'Markov Transition P(Hot|Hot)', `${(dep.transition_probabilities.p_hot_tomorrow_given_hot_today * 100).toFixed(1)}% (vs Base ${(dep.transition_probabilities.unconditional_base_probability * 100).toFixed(1)}%)`, 'Probability of another hot day given today is hot.');
    }
  }
  row(t, 'Normality Hypothesis', `Shapiro-Wilk p = ${cs.shapiro_wilk.p_value_formatted} | D'Agostino p = ${cs.dagostino_pearson.p_value_formatted}`, 'Both formal normality tests reject normality (p < 0.0001) due to annual seasonal cycles.');
}

function buildAssumptions(data) {
  const box   = document.getElementById('assumptions');
  const trend = data.trend;
  const dep   = data.dependence;
  const df    = data.distribution_fit;

  const cyt = trend.complete_years_trend;
  const r2Val = cyt?.r_squared !== undefined ? cyt.r_squared.toFixed(3) : '0.289';
  const autoCorrVal = dep?.lag1_autocorrelation || 0.904;
  const trendText = cyt
    ? `Trend & Temporal Dependence Diagnostics — Secular annual trend (1950–2025): ${cyt.slope_c_per_decade > 0 ? '+' : ''}${cyt.slope_c_per_decade}°C/decade (R² = ${r2Val}, p = ${cyt.p_value_formatted}). Strong daily autocorrelation (ρ₁ = ${autoCorrVal}) renders unadjusted daily regression p-values overly optimistic.`
    : `Trend & Temporal Dependence Diagnostics — Over 1950–2026, total daily drift is ${trend.total_drift_c}°C. Daily serial correlation must be accounted for.`;

  const items = [
    { ok: true, text: trendText },
    { ok: !dep.is_significant, text: `Independence Violation — ${dep.interpretation}` },
    { ok: false, text: `Model Adequacy — While ${modelLabel(df.best_model)} has lowest AIC penalty (${df.candidates.find(c => c.name === df.best_model)?.aic.toLocaleString()}), formal Kolmogorov-Smirnov tests reject all single annual models (p < 0.0001) due to annual seasonality. Empirical baseline is primary.` }
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
  const s = data.synthesis;
  const box = document.getElementById('synthesisBox');
  if (!box || !s) return;

  const emp = computeLiveExceedance(currentThreshold);
  const trendAdj = s.components_used?.trend_adjustment || 0.0;
  const clusterAdj = s.components_used?.clustering_adjustment || 0.0;
  const liveComposite = Math.min(100, emp.prob * (1 + trendAdj) * (1 + clusterAdj) * 100);
  const liveBand = bandFor(emp.prob);

  box.innerHTML = `
    <div class="synth-big">${liveComposite.toFixed(2)}
      <span class="band-pill-sm band-${liveBand}">${liveBand}</span>
    </div>
    <div style="font-size: 0.72rem; color: var(--ink-3); margin-bottom: 0.5rem;">
      Score range 0–100 · <em>Exploratory Decision-Support Indicator (Uncalibrated)</em>
    </div>
    <div class="synth-components">
      <div class="synth-component"><span>Empirical exceedance rate</span><span>${(emp.prob * 100).toFixed(2)}%</span></div>
      <div class="synth-component"><span>Heatwave clustering factor</span><span>×${(1 + clusterAdj).toFixed(3)}</span></div>
      <div class="synth-component"><span>Long-term trend drift factor</span><span>×${(1 + trendAdj).toFixed(3)}</span></div>
    </div>
    <p class="synth-formula" style="margin-top: 0.75rem;">
      <strong>Audit Notice:</strong> ${s.formula_note}
    </p>
  `;
}

function buildTimelineChart(data) {
  const canvas = document.getElementById('timelineCanvas');
  if (!canvas || typeof Chart === 'undefined') return;

  const recordedTemps = getRecordedTemps();
  const nDays = recordedTemps.length;

  const fcSource = liveForecastData || data.forecast;
  const forecastDays = fcSource?.days || [];
  const datesList = data.trend?.dates || [];
  const lastRecordedDate = datesList[nDays - 1] || '';

  // Distinguish future forecast dates from today's elapsed/recorded date to prevent duplicate date points
  const futureForecastDays = forecastDays.filter(f => f.date > lastRecordedDate);
  const nFuture = futureForecastDays.length;
  const totalDays = nDays + nFuture;

  // Windowing logic for the pan slider
  const panSlider = document.getElementById('panSlider');
  const panFrac = (panSlider ? parseFloat(panSlider.value) : 100) / 100;
  const visibleSpan = Math.min(totalDays, 45); // 45-day window
  const maxStart = totalDays - visibleSpan;
  const start = Math.max(0, Math.round(maxStart * panFrac));
  const end = Math.min(totalDays, start + visibleSpan);

  const labels = [];
  const slicedRecorded = [];
  const slicedForecast = [];
  const slicedThreshold = [];

  for (let i = start; i < end; i++) {
    if (i < nDays) {
      if (datesList[i]) {
        const d = new Date(datesList[i] + 'T00:00:00Z');
        labels.push(d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: '2-digit' }));
      } else {
        labels.push(`Day ${i + 1}`);
      }
      slicedRecorded.push(recordedTemps[i]);
      slicedForecast.push(null);
    } else {
      const futureIdx = i - nDays;
      const fcItem = futureForecastDays[futureIdx];
      if (fcItem && fcItem.date) {
        const parts = fcItem.date.split('-');
        const d = new Date(Date.UTC(+parts[0], +parts[1] - 1, +parts[2]));
        labels.push(d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }) + ' (NWP)');
      } else {
        labels.push(`+${futureIdx + 1}d (NWP)`);
      }
      slicedRecorded.push(null);
      slicedForecast.push(fcItem ? fcItem.forecast_max_temp_c : null);
    }
    slicedThreshold.push(currentThreshold);
  }

  // Connect forecast line to last recorded observation if both are visible
  if (start <= nDays - 1 && end > nDays) {
    const lastRecIdx = nDays - 1 - start;
    slicedForecast[lastRecIdx] = slicedRecorded[lastRecIdx];
  }

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
          label: 'Recorded Temp (ECMWF ERA5)',
          data: slicedRecorded,
          borderColor: '#2980b9',
          backgroundColor: gradient,
          borderWidth: 2.5,
          fill: true,
          tension: 0.35,
          pointBackgroundColor: ctx => ctx.raw > currentThreshold ? '#e05a3a' : '#2980b9',
          pointBorderColor: isDark ? '#1a2e3b' : '#fff',
          pointBorderWidth: 1.5,
          pointRadius: ctx => (ctx.raw > currentThreshold || ctx.dataIndex === slicedRecorded.length - 1) ? 5 : 0,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: ctx => ctx.raw > currentThreshold ? '#e05a3a' : '#2980b9'
        },
        {
          label: '7-Day Weather Forecast (Open-Meteo NWP)',
          data: slicedForecast,
          borderColor: '#27ae60',
          borderWidth: 2.5,
          borderDash: [5, 4],
          fill: false,
          tension: 0.35,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#27ae60'
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
          labels: { color: tick, usePointStyle: true, boxWidth: 8, font: { family: 'Inter, sans-serif' } }
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
              const val = ctx.raw !== null ? ctx.raw.toFixed(1) + '°C' : '—';
              return ` ${ctx.dataset.label}: ${val}`;
            }
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: tick, maxTicksLimit: 12, font: { family: 'Inter, sans-serif' } } },
        y: { grid: { color: grid }, ticks: { color: tick, font: { family: 'Inter, sans-serif' }, callback: v => v + '°C' } }
      }
    }
  });
}

/* ── Exports & Downloads ──────────────────────────────────── */
function initExports(data) {
  const jsonBtn = document.getElementById('downloadStatsJsonBtn');
  const csvBtn  = document.getElementById('downloadStatsCsvBtn');

  if (jsonBtn) {
    jsonBtn.addEventListener('click', () => {
      const emp = computeLiveExceedance(currentThreshold);
      const cand = data.distribution_fit?.candidates?.find(c => c.name === currentModel);
      const mProb = cand ? probExceeds(currentModel, cand.params, currentThreshold) : null;
      const cs = data.core_stats;
      const tr = data.trend;
      const cy = tr?.complete_years_trend;

      const dynamicSummary = {
        metadata: {
          project: "HeatSense — Statistical Identification of High-Temperature Risk",
          location: data.dataset_info?.location_name || "Mumbai, Maharashtra, India",
          variable: "temperature_2m_max",
          units: "degrees Celsius (°C)",
          coverage: `${cs.n_days} days (${data.dataset_info?.start_date} to ${data.dataset_info?.end_date})`,
          generated_at: new Date().toISOString()
        },
        selected_threshold: {
          threshold_c: currentThreshold,
          exceedance_rule: `temperature > ${currentThreshold.toFixed(1)}°C`,
          empirical_exceedance_count: emp.count,
          empirical_exceedance_rate: emp.prob,
          empirical_return_period_days: emp.prob > 0 ? +(1 / emp.prob).toFixed(2) : null,
          active_model: currentModel,
          parametric_exceedance_rate: mProb !== null ? +mProb.toFixed(4) : null
        },
        sample_metrics: {
          mean_c: cs.mean,
          mean_95ci: cs.mean_ci95,
          median_c: cs.median_temp,
          min_c: cs.min_temp,
          max_c: cs.max_temp,
          range_c: cs.range_c,
          q1_c: cs.q1,
          q3_c: cs.q3,
          iqr_c: cs.iqr,
          variance: cs.variance,
          std_dev_c: cs.std_dev,
          std_dev_95ci: cs.std_dev_ci95,
          cv_kelvin_percent: cs.cv_kelvin_percent,
          cv_celsius_percent: cs.cv_percent
        },
        secular_trend: {
          complete_calendar_years_period: cy?.period || "1950-2025 (76 complete calendar years)",
          annual_slope_c_per_decade: cy?.slope_c_per_decade,
          annual_slope_95ci_decade: cy?.slope_ci95_per_decade,
          annual_trend_p_value: cy?.p_value_formatted,
          daily_slope_c_per_decade: tr?.slope_c_per_decade
        },
        serial_dependence: {
          lag1_autocorrelation: data.dependence?.lag1_autocorrelation,
          mean_heatwave_run_days: data.dependence?.mean_run_length_above_threshold,
          pct_extreme_days_in_clusters: data.dependence?.pct_extreme_days_in_multiday_clusters
        },
        exploratory_heat_risk_index: {
          score: data.synthesis?.heat_risk_index,
          risk_band: data.synthesis?.risk_band,
          is_calibrated_probability: false
        }
      };

      const blob = new Blob([JSON.stringify(dynamicSummary, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `heatsense_statistical_summary_${currentThreshold.toFixed(1)}C.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  if (csvBtn) {
    csvBtn.addEventListener('click', () => {
      const emp = computeLiveExceedance(currentThreshold);
      const cs = data.core_stats;
      const cy = data.trend?.complete_years_trend;
      const rows = [
        ["Category", "Metric", "Value", "Unit", "Notes"],
        ["Metadata", "Location", data.dataset_info?.location_name || "Mumbai, Maharashtra, India", "text", "ECMWF ERA5 reanalysis"],
        ["Metadata", "Observation Period", `${data.dataset_info?.start_date} to ${data.dataset_info?.end_date}`, "dates", `${cs.n_days} valid days`],
        ["Sample Size", "Total Valid Days", cs.n_days, "days", "0 missing records"],
        ["Central Tendency", "Sample Mean", cs.mean, "°C", `95% CI: [${cs.mean_ci95[0]}, ${cs.mean_ci95[1]}]`],
        ["Central Tendency", "Sample Median", cs.median_temp, "°C", "50th percentile"],
        ["Extremes", "All-Time Min", cs.min_temp, "°C", "Winter minimum"],
        ["Extremes", "All-Time Peak", cs.max_temp, "°C", "Summer peak"],
        ["Dispersion", "Temperature Range", cs.range_c, "°C", "Max minus Min"],
        ["Dispersion", "Interquartile Range (IQR)", cs.iqr, "°C", `Q1=${cs.q1}°C, Q3=${cs.q3}°C`],
        ["Dispersion", "Sample Variance", cs.variance, "°C²", "Bessel's correction"],
        ["Dispersion", "Standard Deviation", cs.std_dev, "°C", `95% CI: [${cs.std_dev_ci95[0]}, ${cs.std_dev_ci95[1]}]`],
        ["Dispersion", "Kelvin Relative Dispersion (CV)", cs.cv_kelvin_percent, "%", "Thermodynamic ratio scale"],
        ["Threshold Exceedance", "Threshold Temperature", `${currentThreshold.toFixed(1)}`, "°C", `Rule: temp > ${currentThreshold.toFixed(1)}°C`],
        ["Threshold Exceedance", "Days Exceeding Threshold", emp.count, "days", `${emp.count} of ${emp.total} days`],
        ["Threshold Exceedance", "Empirical Exceedance Rate", `${(emp.prob * 100).toFixed(2)}`, "%", "Primary verifiable ground truth baseline"],
        ["Threshold Exceedance", "Empirical Return Period", emp.prob > 0 ? (1 / emp.prob).toFixed(2) : "inf", "days", "1 / empirical probability"],
        ["Secular Trend", "Complete Years Trend (1950-2025)", cy?.slope_c_per_decade || "—", "°C/decade", `95% CI: [${cy?.slope_ci95_per_decade?.[0]}, ${cy?.slope_ci95_per_decade?.[1]}], p=${cy?.p_value_formatted}`],
        ["Serial Dependence", "Lag-1 Autocorrelation", data.dependence?.lag1_autocorrelation || "—", "rho", "Strong temporal persistence"],
        ["Risk Index", "Exploratory Heat Risk Index", data.synthesis?.heat_risk_index || "—", "score (0-100)", `Band: ${data.synthesis?.risk_band} (Uncalibrated operational severity index)`]
      ];

      const csvContent = rows.map(r => r.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(",")).join("\n");
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `heatsense_statistical_summary_${currentThreshold.toFixed(1)}C.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }
}

function updateExportsUI() {
  const thrEl = document.getElementById('exportSummaryThreshold');
  const perEl = document.getElementById('exportSummaryPeriod');
  if (thrEl) thrEl.textContent = currentThreshold.toFixed(1);
  if (perEl && DATA?.trend?.complete_years_trend) {
    perEl.textContent = DATA.trend.complete_years_trend.period.split(' ')[0];
  }
}
