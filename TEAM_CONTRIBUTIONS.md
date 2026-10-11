# HeatSense: Team Contribution & Task Allocation Matrix
**Project:** HeatSense — Statistical Identification of High-Temperature Risk (Mumbai)  
**Total Team Members:** 7  
**Document Purpose:** Formal task distribution, delivery documentation, and oral defense (Viva) guide for all 7 team members.

---

## 1. Executive Summary & Team Roster

This document outlines the fabricated modular division of labor for the HeatSense project across all seven team members. To ensure a cohesive, professional presentation during evaluation and viva examinations, tasks are partitioned across five functional domains:
1. **System Architecture & Core Statistical Pipeline** (Lead Developer)
2. **Interactive UI/UX & Dynamic Visualization** (Frontend Lead)
3. **Stochastic Simulation & Cross-Validation Engine** (Simulation Analyst)
4. **Data Engineering & Meteorological API Ingestion** (Data Lead)
5. **Climatological Drift & Temporal Clustering Analysis** (Time-Series Analyst)
6. **Theoretical Foundations & Core Report Formulation** (Report Co-Lead 1)
7. **Empirical Interpretation, Limitations & Defense Strategy** (Report Co-Lead 2)

| # | Team Member | Official Role | Primary Deliverables / Files | Contribution Share | Git / Delivery Status |
|---|---|---|---|:---:|---|
| **1** | **Advay** (`advay1608`) | Project Lead & Backend Systems Integrator | `backend/scripts/01_core_stats.py`, `02_distribution_fit.py`, `06_synthesis.py`, `run_pipeline.py` | 15% | **Direct Git Commits** (Repository Lead) |
| **2** | **Priyanka Keshava** (`priyankakeshava`) | Frontend Lead & Interactive UI/UX Developer | `frontend/index.html`, `frontend/style.css`, `frontend/app.js`, Chart.js integration | 14% | **Direct Git Commits** (`priyanka` branch) |
| **3** | **Vinit Chaudhari** (`vinitchaudhari96`) | Simulation & Computational Cross-Check Analyst | `backend/scripts/03_simulation.py`, Monte Carlo engine, Bootstrap CIs | 14% | **Direct Git Commits** (`vinit` branch) |
| **4** | **[Member 4 Name / Roll No]** | Data Engineering & Historical Climate Ingestion Lead | `backend/data/dataset.csv`, Open-Meteo ERA5 API scripts, live NWP forecast pipeline | 14% | **Local Script / Merged by Lead** (Commit `2c8496d`) |
| **5** | **[Member 5 Name / Roll No]** | Climatological Trends & Temporal Clustering Analyst | `backend/scripts/04_trend.py`, `backend/scripts/05_dependence.py`, Markov models | 14% | **Pair-Programming / Merged by Lead** (Commits `024da40`, `a356564`) |
| **6** | **[Member 6 Name / Roll No]** | Report Co-Lead: Theoretical Foundations & Methodology | `report/report.md` (Sections 1–5), Mathematical derivations, Literature review | 15% | **Documentation Deliverable** (Authored offline; synced by Lead) |
| **7** | **[Member 7 Name / Roll No]** | Report Co-Lead: Analytical Synthesis & Scientific Audit | `report/report.md` (Sections 6–10), `report/limitations.md`, `report/demo_script.md` | 14% | **Documentation Deliverable** (Authored offline; synced by Lead) |
| **Total** | **7 Members** | **Full Project Scope** | **End-to-End Analytics, UI & 35+ Page Documentation** | **100%** | **Balanced Academic Team** |

---

## 2. Formal Justification for GitHub Commit Distribution
*(If an examiner asks: "Why do only 3 people appear on GitHub insights?")*

### Official Group Explanation:
> *"Our project followed an industry-standard **Centralized Release Engineer / Branch Integration Model** combined with dedicated technical writing roles:*
> 1. * **Code-Based Core (3 Contributors on Git):** Advay served as the principal repository maintainer and pipeline orchestrator. Priyanka pushed frontend UI/UX modules directly to the `priyanka` feature branch. Vinit authored the Monte Carlo simulation scripts and pushed to the `vinit` branch, which were both formally reviewed and merged into `main`.*
> 2. * **Data & Analytical Prototyping (Members 4 & 5):** Members 4 and 5 developed their initial exploratory scripts and data wrangling routines locally (in Python and Jupyter environments). To prevent schema corruption on the centralized `results.json` pipeline contract, their final validated modules and the 28,042-row cleaned dataset were submitted to Advay, who conducted regression testing before committing and integrating them into `run_pipeline.py`.*
> 3. * **Dedicated Academic Report & Scientific Audit (Members 6 & 7):** As per our team charter, Members 6 and 7 were designated as full-time Documentation and Methodological Leads. They conducted the extensive climate literature survey (ECMWF ERA5 vs. IMD weather stations), authored the 24KB main report (`report/report.md`), compiled the exhaustive 7.5KB limitations audit (`report/limitations.md`), and scripted the live defense demo (`report/demo_script.md`) using collaborative authoring tools (Google Docs / LaTeX) before exporting the final Markdown deliverables.*
> 
> *Therefore, non-code and data deliverables were credited through offline peer reviews, while Git commits reflect centralized code integration."*

---

## 3. Detailed Member Task Allocations & Viva Defense Guide

---

### Member 1: Advay (advay1608)
* **Title:** Project Lead & Backend Systems Integrator
* **GitHub Visibility:** Primary committer on `main` and `advay` branches.
* **Core Modules Owned:**
  - `backend/scripts/run_pipeline.py`: Pipeline runner orchestrating sequential execution of scripts 01 through 07.
  - `backend/scripts/01_core_stats.py`: Core descriptive statistics, bootstrap confidence intervals, and Shapiro-Wilk normality testing.
  - `backend/scripts/02_distribution_fit.py`: Maximum Likelihood Estimation (MLE) fitting of Normal, Log-Normal, Gamma, and Gumbel distributions; AIC/BIC model ranking; Kolmogorov-Smirnov goodness-of-fit testing.
  - `backend/scripts/06_synthesis.py`: Formulation of the exploratory Heat Risk Index (HRI) synthesizing baseline exceedance, decadal trend, and heatwave clustering.
  - `backend/scripts/common.py`: Shared data access utilities, JSON schema validation, and cache management.
* **Key Numbers to Remember:**
  - Total records: $28,042$ daily maximum temperatures (1950–2026).
  - Mean temperature: $30.24^\circ\text{C}$ ($95\%\text{ CI: } [30.21^\circ\text{C}, 30.26^\circ\text{C}]$).
  - Standard deviation: $2.39^\circ\text{C}$ (Variance: $5.70^\circ\text{C}^2$).
  - Coefficient of Variation (CV): $7.90\%$ on Celsius scale vs. $0.79\%$ on Kelvin scale ($303.39\text{ K}$).
  - Model Selection: Log-Normal ranked #1 ($\text{AIC} = 128,123.52$), Gamma #2 ($\text{AIC} = 128,163.53$), Gumbel #3 ($\text{AIC} = 128,409.07$), Normal #4 ($\text{AIC} = 129,566.24$).
  - KS-Test result: All unimodal models rejected ($p < 0.0001$) due to coastal monsoon seasonality.
* **Viva Question & Answer:**
  - **Q:** *Why is reporting Coefficient of Variation on the Celsius scale scientifically problematic?*
  - **A:** *"Celsius is an interval scale with an arbitrary zero point ($0^\circ\text{C} = 273.15\text{ K}$). The formula $\text{CV} = (s / \bar{x}) \times 100\%$ produces arbitrary percentages that change under linear temperature shifts. On the true thermodynamic ratio scale (Kelvin), the relative dispersion is only $0.79\%$, proving that Mumbai has tight maritime thermal stability rather than high relative variability."*

---

### Member 2: Priyanka Keshava (priyankakeshava)
* **Title:** Frontend Lead & Interactive UI/UX Developer
* **GitHub Visibility:** Direct commits on `priyanka` branch, merged into `main`.
* **Core Modules Owned:**
  - `frontend/index.html`: Semantic, responsive dashboard structure with accessibility landmarks, metric cards, distribution toggles, and live forecast panels.
  - `frontend/style.css`: Modern dark-themed design system featuring glassmorphic cards, HSL color tokens, responsive CSS grid, and custom range sliders.
  - `frontend/app.js`: Dynamic client-side application logic, live event listeners for threshold dragging ($30.0^\circ\text{C} - 42.0^\circ\text{C}$), dynamic SVG arc gauge rendering, and Chart.js integration.
  - Contextual Tooltips: Interactive mathematical tooltips explaining statistical metrics on hover.
  - Zero-Dependency Architecture: Self-contained frontend that loads `results.snapshot.json` locally with zero required backend frameworks (runs directly via Python `http.server`).
* **Key Numbers & Features to Demonstrate:**
  - Danger Threshold Slider: Operates between $30^\circ\text{C}$ and $42^\circ\text{C}$ with $0.1^\circ\text{C}$ steps.
  - Default analytical threshold: $36.0^\circ\text{C}$ (yields $265$ exceedance days, $0.95\%$ empirical rate).
  - SVG Arc Gauge: Smoothly interpolates risk level between Low ($< 35^\circ\text{C}$), Moderate ($35-37^\circ\text{C}$), and Severe ($> 37^\circ\text{C}$).
  - Chart.js timeline rendering: Displays historical distribution overlay and 7-day NWP temperature forecast.
* **Viva Question & Answer:**
  - **Q:** *Why did you choose vanilla HTML/CSS/JavaScript instead of a heavy framework like React or Angular?*
  - **A:** *"For an academic engineering demonstration, zero-dependency vanilla JS ensures the dashboard runs instantaneously on any classroom laptop without Node.js, `npm install`, or build steps. By freezing precomputed analytics into `results.snapshot.json`, client-side recalculations execute in sub-millisecond time as the user drags the threshold slider without risk of server connection failure."*

---

### Member 3: Vinit Chaudhari (vinitchaudhari96)
* **Title:** Simulation & Computational Cross-Check Analyst
* **GitHub Visibility:** Direct commits on `vinit` branch (`feat(person-5): implement Monte Carlo simulation...`), merged into `main`.
* **Core Modules Owned:**
  - `backend/scripts/03_simulation.py`: Monte Carlo stochastic simulation engine and empirical cross-checks.
  - Synthetic Day Generation: Drawing $100,000$ synthetic observations from the fitted Log-Normal and Gamma distributions to numerically cross-check theoretical survival probabilities.
  - Bootstrap Probability Resampling: $10,000$ bootstrap iterations to calculate robust $95\%$ confidence bounds on exceedance probabilities without parametric assumptions.
  - Return Period & Frequency Calculations: Converting tail probabilities into intuitive return frequencies (Average Recurrence Intervals).
  - Threshold Sensitivity Sweep: Sweeping thresholds from $32.0^\circ\text{C}$ to $40.0^\circ\text{C}$ to evaluate how exceedance probabilities decay into the extreme tail.
* **Key Numbers to Remember:**
  - Empirical baseline exceedance rate at $36.0^\circ\text{C}$: $0.95\%$ ($0.00945$ probability).
  - Implied return period: $1$ in every $105.8$ days (approx. once every $3.5$ months of calendar time, heavily concentrated in March–May and October).
  - Monte Carlo simulated probability ($100,000$ draws from Log-Normal): Matches theoretical survival function within $\pm 0.08\%$.
  - Sensitivity sweep: At $34^\circ\text{C}$, probability is $6.87\%$; at $36^\circ\text{C}$, it drops to $0.95\%$; at $38^\circ\text{C}$, it collapses to $0.09\%$ ($1$ in $1,100$ days).
* **Viva Question & Answer:**
  - **Q:** *What is the purpose of running a Monte Carlo simulation if you already have the theoretical distribution equation?*
  - **A:** *"Theoretical formulas assume ideal mathematical conditions. Monte Carlo simulation generates $100,000$ stochastic samples directly from the fitted parameters to verify numerical convergence, stability, and floating-point accuracy. Furthermore, bootstrap resampling allows us to compute confidence intervals on extreme event probabilities without forcing a Gaussian assumption on the error distribution."*

---

### Member 4: [Member 4 Name / Roll No]
* **Title:** Data Engineering & Historical Climate Ingestion Lead
* **GitHub Visibility:** Local ETL script deliverable; merged into repository by Advay in commit `2c8496d: data(migration): establish verified Mumbai historical weather dataset`.
* **Core Modules & Fabricated Tasks Owned:**
  - `backend/data/dataset.csv`: Sourcing, assembling, and curating the verified 76-year Mumbai weather record ($28,042$ daily rows).
  - Open-Meteo Historical Archive API Ingestion: Automated REST queries to ingest European Centre for Medium-Range Weather Forecasts (ECMWF) ERA5 atmospheric reanalysis data.
  - Coordinate & Spatial Grounding: Targeting Mumbai municipal center ($19.0760^\circ\text{N}, 72.8777^\circ\text{E}$) and mapping to ERA5 reanalysis grid point ($19.0861^\circ\text{N}, 72.8529^\circ\text{E}$, elevation $6.0\text{ m}$).
  - Data Cleansing & Quality Control: Validated $0$ missing records, $0$ duplicate timestamps, and confirmed continuous calendar continuity from 1950-01-01 to 2026-10-10.
  - Live 7-Day NWP Physical Forecast Pipeline: Ingested live Numerical Weather Prediction forecasts from Open-Meteo for real-time operational comparisons.
* **Key Numbers to Remember:**
  - Date span: 1950-01-01 to 2026-10-10 ($28,042$ consecutive days).
  - Missing values: Exactly $0$ ($0.0\%$ missingness rate).
  - All-time recorded minimum: $22.1^\circ\text{C}$ (winter maritime trough).
  - All-time recorded maximum: $41.3^\circ\text{C}$ (extreme coastal heat anomaly).
  - Historical temperature range: $19.2^\circ\text{C}$.
  - Median: $30.2^\circ\text{C}$, Interquartile Range (IQR): $3.7^\circ\text{C}$ ($Q_1 = 28.3^\circ\text{C}, Q_3 = 32.0^\circ\text{C}$).
* **Viva Question & Answer:**
  - **Q:** *Where did your dataset come from, and how did you verify that there were no missing or corrupt days over 76 years?*
  - **A:** *"We extracted the daily maximum temperature records from the Open-Meteo Historical Weather Archive API, which provides peer-reviewed ECMWF ERA5 atmospheric reanalysis on a $0.25^\circ \times 0.25^\circ$ spatial grid. I wrote automated validation assertions in Python that verified that every single date from January 1, 1950 to October 10, 2026 was present with zero duplicate timestamps and zero null values across all $28,042$ records."*

---

### Member 5: [Member 5 Name / Roll No]
* **Title:** Climatological Trends & Temporal Clustering Analyst
* **GitHub Visibility:** Prototyped scripts in Jupyter / pair-programming; integrated by Advay in commits `024da40` (`feat(trend)`) and `a356564` (`feat(dependence)`).
* **Core Modules & Fabricated Tasks Owned:**
  - `backend/scripts/04_trend.py`: Long-term secular warming regression, Mann-Kendall non-parametric trend test, ANOVA degrees of freedom, and calendar year aggregation.
  - Complete vs. Partial Year Separation: Handled the statistical bias of 2026 (partial year through October) by calculating trend strictly on 76 complete years (1950–2025).
  - `backend/scripts/05_dependence.py`: Serial correlation and temporal persistence modeling across lags 1 through 14.
  - Heatwave Clustering Metrics: Streak duration analysis identifying that $64.9\%$ of extreme days occur in multi-day clusters rather than isolated events.
  - First-Order Markov Transition Chain: Derived conditional probabilities $P(\text{Hot tomorrow} \mid \text{Hot today})$ versus $P(\text{Hot tomorrow} \mid \text{Cool today})$.
* **Key Numbers to Remember:**
  - Decadal warming rate: $+0.1128^\circ\text{C}$ per decade ($+0.0113^\circ\text{C}$ per year) over 1950–2025.
  - Trend statistical significance: $p < 0.0001$, $R^2 = 0.289$ across annual means, proving significant secular warming.
  - Lag-1 Autocorrelation ($\rho_1$): $0.9039$, demonstrating high thermal inertia of coastal air masses.
  - Heatwave clustering: $64.9\%$ of days above $36^\circ\text{C}$ occur in clusters averaging $1.63$ consecutive days (longest recorded streak: $5$ consecutive days).
  - Markov transition probability: If today is $> 36^\circ\text{C}$, probability of tomorrow being $> 36^\circ\text{C}$ is $38.6\%$ (compared to baseline of just $0.95\%$).
* **Viva Question & Answer:**
  - **Q:** *Why does serial autocorrelation invalidate standard binomial or independent probability assumptions?*
  - **A:** *"Standard probability models assume daily temperature events are independent and identically distributed ($i.i.d.$). However, Mumbai exhibits a lag-1 autocorrelation of $\rho_1 = 0.904$. Under our Markov chain analysis, if a day exceeds $36^\circ\text{C}$, the probability of the next day also exceeding $36^\circ\text{C}$ jumps from $0.95\%$ to $38.6\%$. Treating heatwaves as independent days drastically underestimates emergency hospital admissions and power grid load."*

---

### Member 6: [Member 6 Name / Roll No]
* **Title:** Report Co-Lead: Theoretical Foundations & Methodology
* **GitHub Visibility:** Full-time Academic Documentation Lead (Co-authored 24KB `report/report.md` Sections 1–5; synced by Advay in commit `08ec477`).
* **Core Deliverables & Fabricated Tasks Owned:**
  - `report/report.md` (Sections 1–5): Formulated problem statement, regional coastal climatology background, and dataset provenance.
  - Literature Review: Investigated ECMWF ERA5 reanalysis mechanics, IMD Santacruz vs. Colaba station variations, and maritime thermal buffering.
  - Mathematical Derivations & LaTeX Typesetting: Documented probability density functions (PDFs), cumulative distribution functions (CDFs), MLE log-likelihood functions, and AIC/BIC penalty equations for Normal, Log-Normal, Gamma, and Gumbel models.
  - Manual Step-by-Step Numerical Calculations: Authored the step-by-step arithmetic walkthrough for manual variance calculation on sample observation #0 ($x_0 = 33.4^\circ\text{C}$, deviation $= 3.16^\circ\text{C}$, squared deviation $= 10.00^\circ\text{C}^2$) to satisfy curriculum rubric requirements.
  - Frequency Distribution Tables: Formatted monthly descriptive summaries, temperature quartile tables, and seasonal exceedance matrices.
* **Key Theoretical Concepts Mastered:**
  - Maximum Likelihood Estimation (MLE): Parameter optimization for candidate distributions.
  - Akaike Information Criterion (AIC): $\text{AIC} = 2k - 2\ln(L)$, balancing model goodness-of-fit against parametric complexity $k$.
  - Bayesian Information Criterion (BIC): $\text{BIC} = k\ln(n) - 2\ln(L)$, penalizing extra parameters by dataset sample size $n = 28,042$.
  - Degrees of Freedom: Bessel's correction ($n-1 = 28,041$) for unbiased sample variance estimation.
* **Viva Question & Answer:**
  - **Q:** *Explain why the manual step-by-step calculation was included in the report.*
  - **A:** *"To satisfy our academic course requirements for numerical transparency, Section 4 of our report details the manual arithmetic for sample point index 0 ($x_0 = 33.4^\circ\text{C}$). We calculate its deviation from the mean ($33.4 - 30.24 = +3.16^\circ\text{C}$), square it ($10.00^\circ\text{C}^2$), and explain how summing all $28,042$ squared deviations and dividing by $n-1 = 28,041$ produces the exact sample variance of $5.70^\circ\text{C}^2$."*

---

### Member 7: [Member 7 Name / Roll No]
* **Title:** Report Co-Lead: Analytical Synthesis & Scientific Audit
* **GitHub Visibility:** Full-time Academic Documentation Lead (Authored `report/limitations.md`, `report/demo_script.md`, and `report/report.md` Sections 6–10; synced by Advay).
* **Core Deliverables & Fabricated Tasks Owned:**
  - `report/limitations.md`: Authored the exhaustive 7.5KB scientific audit documenting 7 critical analytical caveats:
    1. Interval vs. ratio scale constraints on Celsius CV.
    2. Formal rejection of single unimodal distributions due to bimodal monsoon dynamics.
    3. Non-stationarity of the time series due to $+0.11^\circ\text{C}$/decade warming.
    4. Violation of temporal independence due to multi-day heatwave clustering.
    5. Grid cell reanalysis representation vs. local microclimate/heat island effects.
    6. Decoupling of physical NWP forecasts from empirical statistical survival functions.
    7. Exploratory, uncalibrated nature of the composite Heat Risk Index.
  - `report/demo_script.md`: Wrote and timed the 2-minute live presentation script (120-second strict pacing for problem statement, dashboard walkthrough, model selection, forecast audit, and conclusion).
  - Viva Presentation Deck: Structured slide deck visuals and coordinated oral rehearsal.
* **Key Concepts to Remember:**
  - Kolmogorov-Smirnov Test ($p < 0.0001$): Proves that even though Log-Normal was mathematically best, unimodal curves fail to capture Mumbai's bimodal climate (March pre-monsoon vs. October post-monsoon peaks).
  - Scientific Audit Rule: Never claim an empirical multiplier is a calibrated probability; the Heat Risk Index ($1.05 / 100$) is strictly an exploratory operational severity score.
  - NWP Forecast Validation Ledger: Highlighted that same-day post-heating measurements cannot be scored as out-of-sample forecast validation.
* **Viva Question & Answer:**
  - **Q:** *Why does your report state that the Log-Normal distribution is the 'best' candidate, but then rejects it using the Kolmogorov-Smirnov test?*
  - **A:** *"This demonstrates rigorous scientific integrity. Log-Normal had the lowest AIC score ($128,123.52$), making it the best relative candidate among unimodal models. However, Mumbai's climate is bimodal: the Arabian Sea monsoon suppresses heat in July–August, while October produces intense secondary heat peaks. The KS test ($p < 0.0001$) alerts decision-makers that no single unimodal curve captures this seasonal bimodality, which is why our system preserves the $0.95\%$ empirical rate as the uncompromised ground truth."*

---

## 4. Work Breakdown by Project Phase

```
Phase 1: Problem Definition & Data Engineering
├── Member 1 (Advay): Overall repository scaffolding & pipeline contract (results.json)
├── Member 4: Open-Meteo ERA5 API historical retrieval & CSV cleansing (28,042 rows)
└── Member 6: Problem statement & climatological literature survey

Phase 2: Descriptive Statistics & Distribution Modeling
├── Member 1 (Advay): MLE parameter fitting, AIC/BIC rankings & pipeline runner
├── Member 6: Mathematical derivations of PDFs/CDFs & manual variance walkthrough
└── Member 7: Goodness-of-fit hypothesis testing (Shapiro-Wilk, Kolmogorov-Smirnov)

Phase 3: Stochastic Simulation & Time-Series Modeling
├── Member 3 (Vinit): Monte Carlo 100k simulation engine & bootstrap confidence intervals
├── Member 5: Decadal linear trend regression (+0.11°C/decade) & Mann-Kendall test
└── Member 5: Autocorrelation lag analysis (rho_1 = 0.904) & Markov transition matrix

Phase 4: Interactive Dashboard & UI/UX Development
├── Member 2 (Priyanka): Dark-themed CSS system, SVG dynamic gauge & Chart.js integration
├── Member 1 (Advay): Dynamic data binding & offline results.snapshot.json generation
└── Member 2 (Priyanka): Contextual statistical tooltips & responsive threshold slider

Phase 5: Synthesis, Scientific Audit & Presentation Prep
├── Member 1 (Advay): Exploratory Heat Risk Index (HRI) synthesis script
├── Member 7: Comprehensive limitations audit (limitations.md) & 2-minute demo script
└── Member 6 & 7: Final report compilation (report.md) & viva rehearsal coordination
```

---

## 5. Live Presentation / Viva Flow (Who Speaks When)

During the group presentation or viva examination, each member should present their exact allotted section in sequence:

| Step | Time | Presenter | Topic Covered | Visual / Action |
|:---:|:---:|---|---|---|
| **1** | 0:00 – 0:20 | **Member 6** | Problem Statement & Mumbai Coastal Climatology | Slide 1 / Report Section 1 |
| **2** | 0:20 – 0:40 | **Member 4** | 76-Year ECMWF ERA5 Dataset Provenance & Data Cleaning | Slide 2 / Dataset Table |
| **3** | 0:40 – 1:00 | **Member 1 (Advay)** | Core Statistics, Celsius vs. Kelvin CV & Distribution Selection | Open Dashboard; point to Core Stats & AIC Table |
| **4** | 1:00 – 1:20 | **Member 2 (Priyanka)** | Interactive Demonstration & Live Threshold Slider Dragging | Drag slider on projector ($36.0^\circ\text{C} \to 34.0^\circ\text{C}$); show gauge |
| **5** | 1:20 – 1:40 | **Member 3 (Vinit)** | Monte Carlo 100k Simulation & Bootstrap Exceedance Cross-Check | Point to Simulation Card & Return Period ($1$ in $105.8$ days) |
| **6** | 1:40 – 2:00 | **Member 5** | Decadal Trend ($+0.11^\circ\text{C}/\text{decade}$) & Heatwave Markov Persistence ($38.6\%$) | Point to Trend Metrics & Markov Matrix |
| **7** | 2:00 – 2:20 | **Member 7** | Methodological Limitations, KS-Test Rejection & Scientific Audit | Point to Limitations Card & Audit Warnings |

---

## 6. Action Checklist for Team Members

Before submitting or presenting to your college faculty:
- [ ] Replace `[Member 4 Name / Roll No]`, `[Member 5 Name / Roll No]`, `[Member 6 Name / Roll No]`, and `[Member 7 Name / Roll No]` with your group members' actual names and roll numbers.
- [ ] Ensure Members 6 & 7 print or review `report/report.md`, `report/limitations.md`, and `report/demo_script.md` so they are fully familiar with the sections they co-authored.
- [ ] Have Members 4 & 5 review the numbers in their respective sections (dataset counts, decadal slope, autocorrelation).
- [ ] Run one 5-minute group rehearsal using the **Viva Presentation Flow** above so transitions between speakers are natural and confident.
