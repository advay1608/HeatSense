# 2-Minute Interactive Demo & Presentation Script
**Project:** HeatSense — Statistical Identification of High-Temperature Risk (Mumbai)  
**Target Time:** 120 seconds  

---

### [0:00 – 0:25] 1. Problem Statement & Motivation
> "Good morning, everyone. In tropical coastal megacities like Mumbai, extreme heat combined with high ambient humidity poses a severe engineering, public health, and workforce hazard. 
> 
> Most conventional analyses make a dangerous mistake: they either calculate a basic average assuming a symmetric bell curve, or they treat extreme hot days as independent, isolated events. 
> 
> With HeatSense, we built an uncertainty-quantified statistical engine running on over **76 years of empirical daily maximum temperature data for Mumbai (28,042 validated records from 1950 to 2026)** to rigorously measure when, how often, and for how long extreme thermal thresholds are breached."

---

### [0:25 – 0:50] 2. The Interactive Dashboard (Live Demonstration)
*(Action: Open `frontend/index.html` on the projector. Point to the Arc Gauge and Danger Threshold slider.)*

> "This is our interactive demonstration. Right here on the primary arc gauge, we display the **Historical heat exceedance risk** as our primary, directly verifiable baseline.
> 
> Watch what happens when I drag the **Danger Threshold slider** from $36.0^\circ\text{C}$ down to $34.0^\circ\text{C}$ or up to $38.0^\circ\text{C}$..."  
*(Action: Drag the slider. Point to the live recalculation.)*  
> "...the dashboard recomputes the exact empirical exceedance count, empirical probability, fitted model survival functions, and implied average spacing in real time across all 28,042 observations. At our project's default $36.0^\circ\text{C}$ analytical threshold ($T > 36.0^\circ\text{C}$), Mumbai has experienced **265 days** above threshold—an empirical baseline of **0.95%**, or an average historical spacing of 1 in 105.8 days."

---

### [0:50 – 1:15] 3. Multi-Distribution Model Selection (Statistical Honesty)
*(Action: Scroll to the Model Selection buttons: Log-Normal, Gamma, Normal, Gumbel, and the Diagnostics Table.)*

> "Crucially, **we tested our assumptions instead of blindly trusting one model**. 
> 
> We fitted four candidate parametric distributions via Maximum Likelihood Estimation: Log-Normal, Gamma, Gaussian, and Gumbel. 
> 
> In Mumbai's coastal climate, the **Log-Normal distribution** achieved the lowest AIC score ($128,123.52$), followed closely by Gamma ($128,163.53$). But here is our critical statistical safeguard: **a model being the best among candidates does not mean it is a statistically adequate fit**.
> 
> Because Mumbai experiences distinct monsoon seasonality—where heavy cloud cover and rainfall completely suppress maximum temperatures below 36°C during June to September, followed by a sharp 'October heat' surge—rigorous Kolmogorov-Smirnov tests formally reject all four single unimodal distributions ($p < 0.0001$). Our dashboard openly communicates this diagnostic limitation and keeps the empirical record as the primary ground truth."

---

### [1:15 – 1:40] 4. NWP Forecast Integration & Operational Heat Risk Index
*(Action: Scroll to the 7-Day NWP Forecast and the Exploratory Heat Risk Index card.)*

> "Next, look at our forecast panel: rather than fabricating a synthetic 7-day projection, we integrated the **live Open-Meteo Numerical Weather Prediction (NWP) API for Mumbai**.
> 
> Notice how we strictly audit this forecast: we present **Today (10 Oct: 37.6°C)** as an elapsed diurnal heating peak. Because our data was retrieved at 16:52 IST—after the day's maximum—matching the reanalysis proxy is a diagnostic check, not out-of-sample forecast validation. Under strict scientific discipline, we exclude it from forecast MAE and bias calculations, leaving **0 verified out-of-sample dates** and **6 pending future dates (11–16 Oct)** that await finalized observations.
> 
> We also show raw NWP temperatures without artificial confidence intervals, because historical variance does not calibrate an NWP prediction interval. Beside the forecast, we provide our **exploratory Markov persistence scenario** (38.6% tomorrow given today's heat spike), but we clearly label it as an empirical persistence baseline subject to strong seasonal limits, strictly decoupled from the physical NWP model.
> 
> To synthesize this for municipal decision-makers, we computed an **Exploratory Heat Risk Index (score 1.05 / 100, Low Risk at 36°C)**. Rather than falsely presenting arbitrary multipliers as a calibrated probability, we transparently explain it as an operational severity index combining the 0.95% empirical baseline, heatwave clustering, and secular decadal warming (+0.11°C/decade, R² = 0.289, p < 0.0001)."

---

### [1:40 – 2:00] 5. Proactive Methodological Limitation & Anticipated Defense
> "To conclude with an honest methodological limitation: HeatSense rigorously separates empirical climate baselines, parametric approximations, and physical NWP forecasts. 
> 
> While our 76-year ERA5 reanalysis dataset provides exceptional statistical power with a 95% bootstrap confidence interval of just $\pm 0.03^\circ\text{C}$ on the mean, ERA5 reflects a reanalysis grid cell ($19.086^\circ\text{N}, 72.8529^\circ\text{E}$, elevation 6.0 m) rather than an independent physical weather station thermometer. Reanalysis and NWP share atmospheric modeling physics, meaning verification errors reflect model-versus-reanalysis proxy agreement rather than independent ground truth.
> 
> If asked why October NWP predictions reach 36.8–37.6°C: this reflects authentic **'October Heat'** in Mumbai, where continental easterly land breezes delay the cooling sea breeze, matching inland **IMD Santacruz** observations (which frequently reach 36–38°C in October) while coastal Colaba remains marine-moderated at 32–34°C. Furthermore, we maintain a strict validation ledger: we never score future dates (11–16 Oct) or same-day post-peak retrievals as verified forecast accuracy.
> 
> Thank you, and we welcome your questions!"
