> ⚠️ **PROJECT STATUS: scaffold only, running on FAKE data.** Every script
> runs end-to-end and every number in `backend/output/results.json` is
> currently computed from `00_generate_sample_data.py`'s randomly generated
> placeholder dataset — not real temperatures. Nothing here is a finished
> result. The pipeline proves the *plumbing* works; it does not mean
> anyone's actual analysis, writing, or design work is done. See each
> `assignments/PERSON<N>.md`'s "Definition of done" — every one of them
> requires rerunning against real data before that role is actually complete.

# Statistical Identification of High-Temperature Risk

Internal assignment project — Statistics & Probability, Module 2.
A Python analysis engine + interactive dashboard that turns a real record
of past temperatures into a defensible, uncertainty-aware probability of
extreme heat.

> We don't just calculate the mean and standard deviation and call it a day.
> We fit and compare multiple probability models, quantify how confident we
> are in every number, cross-check our probability estimate three
> independent ways, and test the assumptions (independence, stability) that
> the whole analysis depends on — then wrap all of it in a live interactive
> dashboard. Full reasoning in `ARCHITECTURE.md` and the pitch document
> linked below.

---

## Start here

| I want to... | Go to |
|---|---|
| Understand what we're building and why | This README, then the pitch doc (link below) |
| Know exactly what the assignment requires | `REQUIREMENTS.md` |
| Understand how all the pieces connect | `ARCHITECTURE.md` |
| Set up my environment and run something | `SYSTEM.md` |
| Know what *I* specifically need to build | `assignments/PERSON<N>.md` (find your number below) |
| An AI assistant reading this repo | `CLAUDE.md` |

**Full team pitch / project brief:** see the published brief the team
already reviewed (link it here once finalized), or `report/` once written.

---

## Team

| # | Role | Assignment doc |
|---|---|---|
| Person 1 | Backend lead — statistics, uncertainty, distribution fitting, synthesis | `assignments/PERSON1.md` |
| Person 5 | Simulation — Monte Carlo, bootstrap, return period | `assignments/PERSON5.md` |
| Person 3 | Data lead — sourcing, cleaning, documenting the dataset | `assignments/PERSON3.md` |
| Person 4 | Report lead — written investigation, interpretation, limitations | `assignments/PERSON4.md` |
| Person 6 | Trend analysis — regression, stationarity check | `assignments/PERSON6.md` |
| Person 7 | Dependence analysis — autocorrelation, heatwave clustering | `assignments/PERSON7.md` |
| Person 2 | Frontend lead — interactive dashboard | `assignments/PERSON2.md` |

---

## Quickstart

```bash
git clone <repo-url>
cd heat-risk-project
pip install numpy pandas scipy matplotlib --break-system-packages
python3 backend/scripts/00_generate_sample_data.py   # placeholder data
python3 backend/scripts/run_pipeline.py               # runs full analysis
open frontend/index.html                              # view the dashboard
```

Full setup and conventions: `SYSTEM.md`.

---

## Project structure

```
heat-risk-project/
├── README.md              you are here
├── ARCHITECTURE.md         the technical contract — read before coding
├── SYSTEM.md               environment setup, conventions, git workflow
├── REQUIREMENTS.md         what the assignment (and we) require, mapped to deliverables
├── CLAUDE.md               instructions for AI assistants working in this repo
├── assignments/            one detailed brief per person (PERSON1.md ... PERSON2.md)
├── backend/                Python analysis pipeline
│   ├── data/dataset.csv
│   ├── scripts/
│   └── output/results.json, figures/
├── frontend/                interactive dashboard (HTML/CSS/JS)
└── report/                  the written investigation
```

---

## Status

- [ ] Real dataset sourced and cleaned (Person 3)
- [ ] Core stats + uncertainty (Person 1)
- [ ] Distribution fitting + model selection (Person 1)
- [x] Simulation + bootstrap probability (Person 5)
- [ ] Trend analysis (Person 6)
- [ ] Dependence/clustering analysis (Person 7)
- [ ] Synthesis / Heat Risk Index (Person 1)
- [ ] Dashboard (Person 2)
- [ ] Report (Person 4)

Update this checklist as pieces land — it's the fastest way for anyone to
see where the project actually stands.
