# Statistical Identification of High-Temperature Risk
**HeatSense: An Uncertainty-Aware Urban Thermal Risk Assessment Framework**

**Authors:** HeatSense Engineering & Analytics Group  
**Dataset Location:** New Delhi, India ($28.6139^\circ\text{ N}, 77.2090^\circ\text{ E}$, Elevation: $214\text{ m}$)  
**Temporal Coverage:** 1950-01-01 to 2026-10-07 ($28,039$ consecutive daily observations)  
**Data Provenance:** Open-Meteo Historical Weather Archive API / ECMWF ERA5 Reanalysis  
**Canonical Danger Threshold ($T_{\text{thresh}}$):** $36.0^\circ\text{C}$  

---

## 1. Problem Statement
Urban Heat Island (UHI) effects and intensifying summer heatwaves pose acute risks to public health, urban electrical grid stability, and outdoor workforce safety. Conventional heat hazard assessments frequently rely on naive historical means or single-point determinism, omitting observational uncertainty, non-Gaussian distributional tails, and serial persistence (heatwave clustering).

The objective of this investigation is to construct a rigorous, data-driven statistical engine that converts decades of empirical daily maximum temperature records into actionable, uncertainty-quantified risk projections. Specifically, this framework answers three operational questions:
1. What is the defensible probability that daily maximum temperatures will cross dangerous thresholds ($T > 36.0^\circ\text{C}$)?
2. Does the empirical temperature distribution conform to classical Gaussian assumptions, or do heavy-tailed/skewed models provide superior empirical fidelity?
3. How do multi-decadal trends and multi-day temporal clustering amplify the real-world operational risk beyond an isolated single-day probability?

---

## 2. Description of the Dataset
The dataset comprises $28,039$ consecutive daily maximum temperature ($T_{\max}$) observations spanning over $76$ years (January 1, 1950 through October 7, 2026). 

### Key Dataset Characteristics:
- **Observation Count ($n$):** $28,039$ days (zero missing records, continuous temporal sequence).
- **Recorded Minimum:** $12.3^\circ\text{C}$ (winter cold-snap troughs).
- **Recorded Maximum:** $47.5^\circ\text{C}$ (extreme pre-monsoon heatwaves).
- **Median Temperature:** $31.4^\circ\text{C}$ ($\text{IQR} = 9.7^\circ\text{C}$, from $25.8^\circ\text{C}$ to $35.5^\circ\text{C}$).
- **Exceedance Prevalence:** $6,350$ days ($22.65\%$ of the total historical record) exceeded the $36.0^\circ\text{C}$ danger threshold.

---

## 3. Source of Data & Data Provenance
Data was programmatically ingested via the **Open-Meteo Historical Weather Archive API**, which serves peer-reviewed **ECMWF (European Centre for Medium-Range Weather Forecasts) ERA5 Reanalysis** atmospheric data at $0.25^\circ \times 0.25^\circ$ spatial resolution ($~31\text{ km}$ grid).

### Citable Reference:
> Open-Meteo Historical Weather API (2026). *ECMWF ERA5 Atmospheric Reanalysis for New Delhi ($28.6139^\circ\text{ N}, 77.2090^\circ\text{ E}$)*. Open-Meteo GmbH. Available at: `https://archive-api.open-meteo.com/v1/archive`. Data retrieved under Creative Commons Attribution 4.0 International (CC BY 4.0).

---

## 4. Statistical Concepts Used
1. **Unbiased Sample Moments:** Calculating sample variance and standard deviation with Bessel's correction ($n-1$ degrees of freedom) to ensure unbiased estimation.
2. **Relative Dispersion:** Coefficient of Variation ($\text{CV} = \frac{s}{\bar{x}} \times 100\%$) for scale-independent variability quantification.
3. **Non-Parametric Bootstrap Confidence Intervals:** Evaluating $95\%$ confidence bounds via $10,000$ empirical resamplings with replacement, eliminating parametric distribution assumptions.
4. **Formal Normality Hypothesis Testing:** Shapiro-Wilk test (subsampled at $N=5,000$) and D'Agostino-Pearson $K^2$ omnibus test.
5. **Parametric Distribution Fitting via MLE:** Fitting Normal, Log-Normal, Gamma, and Extreme Value Type I (Gumbel) distributions.
6. **Model Selection Criteria:** Penalized likelihood comparison using Akaike Information Criterion (AIC) and Bayesian Information Criterion (BIC), reinforced by an $80/20$ train/test holdout validation.
7. **Stochastic Cross-Checks:** Monte Carlo convergence simulations ($1,000$, $10,000$, and $100,000$ iterations) and empirical bootstrap probability validation.
8. **Temporal Dependency & Clustering Analysis:** Lag-1 autocorrelation ($\rho_1$) and Bernoulli run-length extraction to quantify consecutive heatwave persistence.
9. **Synthesis:** Composite Heat Risk Index (HRI) integrating exceedance likelihood, trend drift, and clustering multipliers.

---

## 5. Relevant Formulae

### Sample Mean, Unbiased Variance & Standard Deviation:
$$\bar{x} = \frac{1}{n} \sum_{i=1}^n x_i, \quad s^2 = \frac{1}{n-1} \sum_{i=1}^n (x_i - \bar{x})^2, \quad s = \sqrt{s^2}$$

### Coefficient of Variation (CV):
$$\text{CV} = \left(\frac{s}{\bar{x}}\right) \times 100\%$$

### Information Criteria (AIC & BIC):
$$\text{AIC} = 2k - 2\ln(\hat{L}), \quad \text{BIC} = k\ln(n) - 2\ln(\hat{L})$$
*(where $k$ is the number of estimated parameters, $n$ is sample size, and $\hat{L}$ is maximized likelihood)*.

### Gumbel (Type I Extreme Value) Survival Function:
$$S(x) = P(X > x) = 1 - \exp\left(-\exp\left(-\frac{x - \mu}{\beta}\right)\right)$$

### Lag-1 Autocorrelation ($\rho_1$):
$$\rho_1 = \frac{\sum_{t=1}^{n-1} (x_t - \bar{x})(x_{t+1} - \bar{x})}{\sum_{t=1}^n (x_t - \bar{x})^2}$$

### Return Period ($R$):
$$R = \frac{1}{P(T > T_{\text{thresh}})} \quad \text{[days]}$$

### Composite Heat Risk Index (HRI):
$$\text{HRI} = P_{\text{base}} \times (1 + \alpha_{\text{trend}}) \times (1 + \beta_{\text{cluster}})$$

---

## 6. Step-by-Step Numerical Calculation (First Historical Data Point)
To verify computation pipeline transparency, the first recorded data point ($i = 0$, Date: 1950-01-01) is manually walked through:
- Observed value: $x_0 = 25.8^\circ\text{C}$
- Sample mean over all $28,039$ days: $\bar{x} = 30.8154^\circ\text{C}$
- Deviation:
  $$x_0 - \bar{x} = 25.8 - 30.8154 = -5.0154^\circ\text{C}$$
- Squared deviation:
  $$(x_0 - \bar{x})^2 = (-5.0154)^2 = 25.1547^\circ\text{C}^2$$
- Contribution to sample variance:
  $$\frac{(x_0 - \bar{x})^2}{n-1} = \frac{25.1547}{28038} = 8.9716 \times 10^{-4}$$

---

## 7. Statistical Summary & Model Comparison Tables

### Table 1: Core Sample Statistics & 95% Bootstrap Confidence Bounds
| Metric | Point Estimate | 95% Bootstrap CI [Lower, Upper] | Interpretation |
| :--- | :--- | :--- | :--- |
| **Sample Size ($n$)** | $28,039$ days | — | 76+ continuous years |
| **Mean ($\bar{x}$)** | $30.815^\circ\text{C}$ | $[30.736^\circ\text{C}, 30.896^\circ\text{C}]$ | Extremely tight confidence band ($\pm 0.08^\circ\text{C}$) |
| **Sample Std. Dev. ($s$)** | $6.796^\circ\text{C}$ | $[6.750^\circ\text{C}, 6.842^\circ\text{C}]$ | High seasonal volatility |
| **Sample Variance ($s^2$)**| $46.192^\circ\text{C}^2$ | $[45.563, 46.813]$ | Unbiased ($ddof=1$) |
| **Coeff. of Variation (CV)**| $22.06\%$ | $[21.890\%, 22.219\%]$ | Substantial seasonal dispersion |
| **Shapiro-Wilk Test** | $W = 0.985$ | $p = 0.000$ | Reject Normality ($p < 0.05$) |
| **D'Agostino Omnibus** | $K^2 = 1427.28$ | $p = 0.000$ | Significant multi-modal/skewed departure |

### Table 2: Candidate Model Fitting & Information Criteria
| Model | Parameters | Log-Likelihood ($\ln \hat{L}$) | AIC | BIC | Rank |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Normal** | $\mu=30.815, \sigma=6.796$ | $-93,519.01$ | **187,042.02** | **187,058.50** | **#1 (Best)** |
| **Log-Normal** | $s=0.000, \text{loc}=-2.1\times 10^6, \text{scale}=2.1\times 10^6$ | $-93,519.01$ | $187,044.02$ | $187,068.75$ | #2 |
| **Gamma** | $a=914.08, \text{loc}=-175.48, \text{scale}=0.226$ | $-93,550.76$ | $187,107.51$ | $187,132.24$ | #3 |
| **Gumbel** | $\mu=27.394, \beta=6.525$ | $-95,331.98$ | $190,667.96$ | $190,684.44$ | #4 |

*Holdout Validation ($80\%$ Train / $20\%$ Test, $N_{\text{test}} = 5,608$):*  
- Best Model (Normal) Test Log-Likelihood: $-18,702.75$  
- Runner-up (Log-Normal) Test Log-Likelihood: $-18,702.75$

### Table 3: Multi-Method Probability Cross-Checks ($T > 36.0^\circ\text{C}$)
| Estimation Methodology | Probability $P(T > 36^\circ\text{C})$ | Implied Return Period ($1/P$) | Convergence Delta vs. Theory |
| :--- | :--- | :--- | :--- |
| **Theoretical (Fitted Model)** | **0.2228 (22.28%)** | **4.49 days** | *Baseline* |
| **Monte Carlo ($1,000$ trials)** | $0.2110$ ($21.10\%$) | $4.74$ days | $-0.0118$ |
| **Monte Carlo ($10,000$ trials)**| $0.2201$ ($22.01\%$) | $4.54$ days | $-0.0027$ |
| **Monte Carlo ($100,000$ trials)**| $0.2243$ ($22.43\%$) | $4.46$ days | $+0.0015$ |
| **Empirical Bootstrap ($10,000$)**| **0.2267 (22.67%)** | **4.41 days** | $+0.0039$ |

---

## 8. Graphical Representation
All 6 analytical and diagnostic figures generated by `07_visualizations.py` from the ingested data:

1. **Histogram & Fitted Distribution Overlay (`01_histogram.png`):** Shows the empirical frequency distribution of $28,039$ observations overlaid with the fitted candidate curve and the shaded extreme-heat tail region ($T > 36.0^\circ\text{C}$).
2. **Boxplot Diagnostics (`02_boxplot.png`):** Illustrates the median ($31.4^\circ\text{C}$), interquartile range ($25.8^\circ\text{C}$ to $35.5^\circ\text{C}$), and upper-tail outliers reaching $47.5^\circ\text{C}$.
3. **Normal Q-Q Plot (`03_qqplot.png`):** Quantile-quantile alignment plot confirming $R = 0.9930$, identifying slight heavy-tailed departures in the extreme summer maximum quantiles.
4. **Monte Carlo Convergence Curve (`04_convergence.png`):** Demonstrates rapid numerical convergence towards theoretical probability as trial sizes increase from $10^3$ to $10^5$.
5. **Threshold Sensitivity Matrix (`05_sensitivity.png`):** Plots exceedance probabilities across the operational threshold range ($33.0^\circ\text{C}$ to $38.0^\circ\text{C}$).
6. **Autocorrelation Profile (`06_autocorrelation.png`):** Plots sample autocorrelation through lag 15 against the $95\%$ Bartlett noise threshold ($\pm 0.0117$).

---

## 9. Interpretation of Results
1. **Uncertainty is Drastically Reduced by All-Time Ingestion:** Because the sample size encompasses $28,039$ days, the $95\%$ bootstrap confidence interval for mean temperature is exceptionally narrow ($[30.736^\circ\text{C}, 30.896^\circ\text{C}]$, a spread of only $0.16^\circ\text{C}$).
2. **Multi-Model Triangulation Agrees Closely:** The theoretical model ($22.28\%$), $100\text{k}$ Monte Carlo simulation ($22.43\%$), and $10\text{k}$ non-parametric bootstrap resampling ($22.67\%$) agree within $0.39\%$ of one another, validating the mathematical robustness of the probability engine.
3. **Severe Serial Persistence (Heatwaves):** The lag-1 autocorrelation is extraordinarily strong ($\rho_1 = 0.9745$, far exceeding the randomness bound of $\pm 0.0117$). Across the 76-year record, $610$ discrete multi-day heatwave clusters occurred above $36.0^\circ\text{C}$, with an average duration of $10.42$ consecutive days and a maximum run of $95$ days. This confirms that extreme thermal events do not occur independently; once initiated, atmospheric heat domes persist for weeks.

---

## 10. Engineering & Operational Decision

### Composite Heat Risk Index (HRI):
$$\text{HRI} = P_{\text{base}} \times (1 + \alpha_{\text{trend}}) \times (1 + \beta_{\text{cluster}}) = 0.2228 \times (1 + 0.0) \times (1 + 0.30) = \mathbf{0.2896} \quad (28.96\%)$$

### Risk Band Classification:
$$\text{HRI} = 0.2896 > 0.15 \implies \mathbf{HIGH\ RISK}$$

### Actionable Operational Guidance:
- **Urban Grid Dispatch:** Power grid operators must expect thermal overload strain approximately $1$ in every $3.5$ days during peak seasons, with contingency reserves sized for multi-week sustained demand.
- **Public Health Protocols:** Because heat occurs in consecutive spells of $10+$ days, emergency cooling centers cannot be staffed for single isolated days; protocols must remain active across extended synoptic clusters.

---

## 11. Limitations of the Analysis
Full treatment of methodological limitations, stationarity constraints, and physical model boundaries is detailed in [limitations.md](file:///c:/Projects/HeatSense/report/limitations.md).
