# Limitations of the Analysis
**Statistical & Operational Boundaries of the HeatSense Pipeline (Mumbai)**

---

## 1. Independence Assumption & Temporal Persistence
- **Empirical Finding:** The lag-1 autocorrelation in Mumbai is $\rho_1 = 0.9039$, vastly exceeding the $95\%$ significance bound ($\pm 1.96/\sqrt{n} = \pm 0.0117$), with weekly persistence of $\rho_7 = 0.6484$.
- **Methodological Impact:** Classical statistical probability models assume independent and identically distributed (i.i.d.) observations. Because atmospheric synoptic systems and coastal sea-breeze regimes persist across multiple days, high-temperature events cluster into heatwave runs (163 distinct clusters above $36.0^\circ\text{C}$, mean run length: $1.63$ days, maximum run: $5$ consecutive days strictly above $36.0^\circ\text{C}$).
- **Mitigation:** The composite Heat Risk Index incorporates an explicit clustering amplification factor ($\beta_{\text{cluster}} = +1.9\%$) to account for serial persistence in operational planning, and the Markov transition matrix proves $P(\text{Hot tomorrow} \mid \text{Hot today}) = 38.6\%$ vs $0.6\%$ if today is cool. Over $64.9\%$ of extreme days occur as part of multi-day runs.

---

## 2. Trend Diagnostics & Temporal Drift
- **Secular Complete Calendar Years Trend (1950–2025, N=76):** Annual mean regression across complete calendar years yields $+0.1128^\circ\text{C}/\text{decade}$ ($95\%\text{ CI: } [+0.0725, +0.1532]^\circ\text{C}/\text{decade}$, $p < 0.0001$, $R^2 = 0.289$). Incomplete year 2026 (283 days) is excluded from the trend model to avoid seasonal truncation bias. Inter-annual climate cycles (such as ENSO and Indian Ocean Dipole) affect annual temperatures.
- **Continuous Daily Series Linear Drift (1950–2026, N=28,042):** Linear regression over all 28,042 consecutive days yields a slope of $+0.1192^\circ\text{C}/\text{decade}$ (total warming drift: $+0.92^\circ\text{C}$). 
- **Methodological Impact:** High serial autocorrelation ($\rho_1 = 0.9039$) violates OLS independence, making naive daily standard errors and p-values optimistic. However, the secular warming in Mumbai is robustly confirmed on complete calendar-year means ($p < 0.0001$).
- **Mitigation:** The dashboard and reports present both the canonical complete-years annual trend and the continuous daily series, explicitly disclaiming stationarity and highlighting autocorrelation caveats.

---

## 3. Representativeness of Historical Record
- **Empirical Finding:** Spanning $28,042$ continuous daily observations from January 1, 1950 to October 10, 2026, the dataset captures major historical climate anomalies, including intense Arabian Sea cyclonic events, severe El Niño anomalies, and coastal "October heat" episodes.
- **Limitation:** Historical reanalysis averages past climate dynamics; it cannot directly predict unprecedented tipping points or physical atmospheric regime shifts outside historical bounds.

---

## 4. Model Adequacy & Goodness-of-Fit
- **Empirical Finding:** The Log-Normal distribution achieved the lowest relative AIC ($128,123.52$) and BIC ($128,140.00$), followed by Gamma ($128,163.53$, $\Delta\text{AIC} = +40.01$) and Normal ($128,385.18$, $\Delta\text{AIC} = +261.66$). On holdout cross-validation ($N_{\text{test}} = 5,608$), Log-Normal test-set log-likelihood was $-12,846.16$.
- **Critical Limitation:** All candidate single annual distributions are formally rejected by Kolmogorov-Smirnov goodness-of-fit testing ($p < 0.0001$). Daily temperatures contain intense annual coastal seasonal variation: monsoon months (June–September) feature heavy cloud cover and ocean rain suppression that cap temperatures below $36.0^\circ\text{C}$ ($0$ exceedances recorded in monsoon season), whereas pre-monsoon (March–May) and post-monsoon "October heat" produce hot spikes. A single unimodal distribution over the entire calendar year cannot adequately fit this multi-modal coastal cycle.
- **Mitigation:** The empirical exceedance rate ($0.95\%$, 265 days) is established as the primary, directly verifiable ground truth baseline, supplemented by seasonal stratification in the dashboard and reports.

---

## 5. Measurement Quality & Reanalysis Grid Point
- **Data Source:** ECMWF ERA5 Reanalysis via Open-Meteo Historical Weather Archive API.
- **Grid Point Details:** Selected grid point for Mumbai is located at $19.086115^\circ\text{N}, 72.85291^\circ\text{E}$ (elevation: $6.0\text{ m}$).
- **Limitation:** ERA5 assimilates satellite, radiosonde, and surface meteorological observations onto a $0.25^\circ$ ($~31\text{ km}$) numerical grid. It represents a spatial grid cell rather than a single physical airport weather station (e.g. Santacruz or Colaba), smoothing extreme localized microclimates such as urban heat islands or dense coastal sea-front breezes.

---

## 6. What This Analysis Is Not
**This historical statistical pipeline is not a physical fluid-dynamics forecast.** It models historical empirical risk, extreme value persistence, and statistical tail probabilities. For operational 7-day weather forecasting, HeatSense integrates the actual Open-Meteo Numerical Weather Prediction (NWP) Forecast API directly for Mumbai ($19.0760^\circ\text{N}, 72.8777^\circ\text{E}$), displaying real atmospheric model forecasts with transparent retrieval timestamps and clearly distinguishing them from historical statistical estimates.

---

## 7. Numerical Forecast Validation & Verification Target Limitations
- **Strict Out-of-Sample Discipline:** A valid out-of-sample forecast requires a pre-target snapshot logged before the target date's heating window commences, verified only after that date's diurnal cycle concludes. Our API retrieval on October 10 occurred at 16:51:17 IST—after Mumbai's diurnal maximum had already occurred. A same-day match with an archive endpoint does not establish forecast skill; it is labeled strictly as a same-day diagnostic comparison and excluded from MAE and bias metrics ($N_{\text{out-of-sample}} = 0$). Future dates (October 11–16) remain pending until their respective observation cycles conclude.
- **Verification Target Nature (Reanalysis vs. Physical Station):** The Open-Meteo Historical Archive serves ECMWF ERA5 reanalysis grid estimates ($19.0861^\circ\text{N}, 72.8529^\circ\text{E}$), not an independent ground thermometer shelter. Operational NWP and ERA5 share numerical parameterizations and assimilation frameworks; error metrics therefore quantify forecast-versus-reanalysis proxy agreement, not independent ground station accuracy. Physical thermometer stations (such as IMD Santacruz and IMD Colaba) reflect localized microclimates and sea-breeze thermal gradients.
- **Absence of Calibrated Prediction Intervals:** Historical temperature standard deviation ($\pm 3.5^\circ\text{C}$) reflects seasonal climatological variability, not calibrated NWP forecast error. Until a sufficiently large sample of verified out-of-sample forecast-error pairs is collected, raw NWP temperatures are presented without uncalibrated prediction intervals.
- **Decoupling Markov Scenarios from NWP Projections:** Markov transition probabilities ($38.64\%, 15.28\%, \dots$) are generated by an empirical 2-state persistence model conditioned on historical 1950–2026 data. They are not physical probabilities produced by Open-Meteo and are not calibrated future weather probabilities. They represent exploratory stationary scenarios subject to seasonal concentration limitations.
