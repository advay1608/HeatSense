# Limitations of the Analysis
**Statistical & Operational Boundaries of the HeatSense Pipeline**

---

## 1. Independence Assumption
- **Empirical Finding:** The lag-1 autocorrelation is $\rho_1 = 0.9745$, vastly exceeding the $95\%$ significance bound ($\pm 1.96/\sqrt{n} = \pm 0.0117$).
- **Methodological Impact:** Classical statistical probability models assume independent and identically distributed (i.i.d.) observations. Because atmospheric synoptic systems move slowly, high-temperature days strongly cluster into extended heatwave runs (mean cluster length: $10.42$ days, maximum run: $95$ consecutive days above $36.0^\circ\text{C}$).
- **Mitigation:** The composite Heat Risk Index applies a maximum clustering penalty multiplier ($\beta_{\text{cluster}} = +30\%$) to explicitly account for serial persistence in operational planning.

---

## 2. Stationarity & Secular Drift
- **Empirical Finding:** Linear regression over the 76-year record yields a slope of $-0.00002^\circ\text{C}/\text{day}$ ($-0.085^\circ\text{C}/\text{decade}$, $p < 0.001$, $R^2 = 0.00076$). Total linear drift across the entire window is $-0.65^\circ\text{C}$.
- **Methodological Impact:** While statistically significant due to the immense sample size ($N = 28,039$), the practical effect size is modest compared to the seasonal variance ($s = 6.80^\circ\text{C}$). The climate process exhibits pronounced multi-decadal oscillation and aerosol dimming effects common to the Indo-Gangetic Plain, rather than monotonic linear warming.
- **Mitigation:** Recent decades should be weighted more heavily when projecting near-future seasonal risks.

---

## 3. Representativeness of Historical Record
- **Empirical Finding:** Spanning $28,039$ continuous daily observations from January 1950 to October 2026, the dataset captures major historical climate anomalies, including severe El Niño episodes, monsoon failures, and intense heat domes.
- **Limitation:** Historical reanalysis averages past climate dynamics; it cannot directly predict unprecedented tipping points or physical atmospheric regime shifts outside historical bounds.

---

## 4. Model Adequacy & Goodness-of-Fit
- **Empirical Finding:** The Normal distribution achieved the lowest AIC ($187,042.02$) and BIC ($187,058.50$), closely matched by the Log-Normal model ($187,044.02$). On holdout cross-validation ($N_{\text{test}} = 5,608$), test-set log-likelihood was identical ($-18,702.75$).
- **Limitation:** Both Shapiro-Wilk ($W = 0.985, p < 0.001$) and D'Agostino-Pearson ($K^2 = 1427.28, p < 0.001$) formally reject strict normality due to annual seasonal bimodal cycles (cold winters vs. hot summers). The fitted bell curve models the aggregate annual distribution well, but seasonal stratification (summer-only modeling) would yield even tighter tail characterization.

---

## 5. Measurement Quality & Reanalysis Reification
- **Data Source:** ECMWF ERA5 Reanalysis via Open-Meteo API.
- **Limitation:** ERA5 assimilates satellite, radiosonde, and surface weather station measurements onto a $0.25^\circ$ ($~31\text{ km}$) numerical grid. While state-of-the-art for global climate modeling, micro-scale urban street-canyon effects (micro-UHI variations between dense concrete centers and green parks) are smoothed across the grid cell.

---

## 6. What This Analysis Is Not
**This pipeline is not a physical meteorological weather forecast.** It does not simulate fluid Navier-Stokes atmospheric dynamics or satellite Doppler radar feeds for tomorrow's weather. It is a defensible, empirical statistical risk quantification engine designed to help engineers, municipal planners, and energy grid operators measure real-world thermal exceedance likelihood and heatwave persistence.
