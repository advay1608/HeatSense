# 2-Minute Interactive Demo & Presentation Script
**Project:** HeatSense — Statistical Identification of High-Temperature Risk  
**Target Time:** 120 seconds  

---

### [0:00 – 0:25] 1. Problem Statement & Motivation
> "Good morning, everyone. In urban centers like New Delhi, extreme heat is not just uncomfortable—it is a critical engineering and public health hazard that triggers power grid collapse and severe health emergencies. 
> 
> Most conventional analyses make a dangerous mistake: they either calculate a basic average and standard deviation assuming a simple bell curve, or they treat extreme days as isolated random events. 
> 
> With HeatSense, we built an uncertainty-quantified statistical engine running on over **76 years of empirical daily maximum temperature data (28,039 records)** to rigorously measure when, how often, and for how long extreme thermal thresholds are breached."

---

### [0:25 – 0:50] 2. The Interactive Dashboard (Live Demonstration)
*(Action: Open `frontend/index.html` on the projector. Point to the Arc Gauge and Danger Threshold slider.)*

> "This is our interactive demonstration. Right here on the primary arc gauge, we see the baseline exceedance risk. 
> 
> Watch what happens when I drag the **Danger Threshold slider** from $36.0^\circ\text{C}$ to $38.0^\circ\text{C}$..."  
*(Action: Drag the slider. Point to the live recalculation.)*  
> "...the dashboard recomputes the exceedance probability and implied return period in real time directly from our fitted mathematical survival functions. At $36.0^\circ\text{C}$, the daily crossing probability is approximately **22.3%**, or a 1-in-4.5-day event."

---

### [0:50 – 1:15] 3. Multi-Distribution Model Selection (Testing Assumptions)
*(Action: Scroll to the Model Selection buttons: Normal, Log-Normal, Gamma, Gumbel.)*

> "Crucially, **we tested our assumptions instead of blindly trusting one model**. 
> 
> We fitted four distinct parametric probability distributions via Maximum Likelihood Estimation: Gaussian, Log-Normal, Gamma, and the Gumbel distribution for extreme values. 
> 
> When we toggle between these models, notice how the tail probabilities shift. We evaluated each model using **Akaike Information Criterion (AIC)** and an **80/20 train/test holdout validation on over 5,600 unseen days**. Both the Normal and Log-Normal models achieved the lowest AIC scores (~187,042), validating that our risk projections generalize accurately to unobserved periods."

---

### [1:15 – 1:40] 4. Synthesis & The Composite Heat Risk Index
*(Action: Scroll to the Heat Risk Index card and Timeline.)*

> "Now, for our core engineering decision: a single day's 22% probability only tells part of the story, because **heat arrives in waves**. 
> 
> Our serial dependence analysis revealed an extreme lag-1 autocorrelation of **0.975**. In our 76-year record, extreme days cluster into heatwaves averaging **10.4 consecutive days**. 
> 
> We synthesized this into our composite **Heat Risk Index (HRI)**, which combines base probability with an empirical clustering multiplier (+30%). That elevates our composite risk index to **28.96%**, placing the region firmly in the **HIGH RISK** operational category. For municipal dispatchers, this proves emergency cooling protocols must be deployed across multi-week windows, not isolated days."

---

### [1:40 – 2:00] 5. Proactive Methodological Limitation
> "To conclude with an honest, critical limitation: **HeatSense is a statistical characterization of empirical risk, not a physical fluid-dynamics weather forecast**. 
> 
> While our 76-year ERA5 reanalysis dataset provides exceptional statistical power with a 95% bootstrap confidence interval of just $\pm 0.08^\circ\text{C}$, localized street-canyon microclimates vary across city blocks. 
> 
> Thank you, and we welcome your questions!"
