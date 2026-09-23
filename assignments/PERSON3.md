# PERSON 3 — Data Lead
**Role:** Source, clean, and document the real temperature dataset.
**Deliverable:** `backend/data/dataset.csv` (replacing the placeholder)
**You do not write to `results.json`** — your output is the dataset itself,
plus a short written documentation section for the report.
**Everyone else is blocked on you.** This is a lead role because of that,
not because the individual task is the hardest — it's because nothing else
can be validated against real numbers until this lands.

---

## 1. What you're actually delivering

Not just "a CSV file" — a **documented, defensible data source**. The
report requires "description of the dataset" and "source of data" as
explicit sections, and if the professor asks "where did this come from and
can I check it," you need a real, citable answer.

## 2. Required schema (non-negotiable)

`backend/data/dataset.csv` must be exactly:
```
date,max_temp_c
2026-08-06,33.4
2026-08-07,32.3
...
```

- `date`: ISO format `YYYY-MM-DD`, sorted ascending, no duplicate dates
- `max_temp_c`: numeric, one decimal place is fine, no missing values
- **Minimum 20 rows** (assignment hard minimum). **Target 30+ rows** — more
  days means tighter confidence intervals for Person 1 and more stable
  Monte Carlo/bootstrap results for Person 5.
- No header variations — the column names must be exactly `date` and
  `max_temp_c` (lowercase), because `backend/scripts/common.py` reads them
  literally.

## 3. Where to actually get real data

Recommended, in order of ease:

1. **Open-Meteo Historical Weather API** — free, no API key required,
   returns daily max temperature directly. Search "Open-Meteo historical
   weather API" for the current endpoint format; as of this project it
   accepts a latitude/longitude and date range and returns JSON with a
   `daily.temperature_2m_max` array you can convert straight into the
   required CSV shape.
2. **timeanddate.com** historical weather pages for your city — manually
   readable, useful if the API route has issues, but more tedious to
   collect 30 days from by hand.
3. **India Meteorological Department (IMD)** public data, if accessible for
   your city/station — the most "official" source, good if you want the
   documentation section to cite a national meteorological authority.

Pick ONE primary source. Don't mix sources within the same dataset (a
station change or measurement methodology change mid-dataset can introduce
an artificial jump that Person 6's trend analysis would misread as a real
warming signal).

## 4. Cleaning checklist

- [ ] No duplicate dates
- [ ] No missing days — if a day genuinely has no reading, either exclude
      it and shrink your date range to stay contiguous, or document the gap
      explicitly in your write-up (do NOT silently interpolate — that
      would corrupt Person 7's autocorrelation/run-length analysis and
      Person 6's trend, which assume a real observed sequence)
- [ ] Consistent units — confirm the source you used actually reports
      Celsius, not Fahrenheit, before you commit the file
- [ ] Sanity-check the range — daily max temps for your city/season should
      look plausible; a stray 4°C or 65°C entry means a units or parsing
      bug, not a real observation

## 5. Required documentation (for the report)

Write a short section (a few paragraphs, hand off to Person 4) covering:

- **Source**: exact name of the API/site/agency, and the date you accessed
  it (data sources update; recording access date makes your work
  reproducible/citable)
- **Location**: exact city/station used, and its coordinates if from an API
- **Date range**: start and end date, and why you chose that particular window
- **Collection method**: API call / manual transcription / other — briefly,
  so a reader understands how the numbers were obtained, not just where
  from
- **Any cleaning decisions**: anything you excluded, adjusted, or flagged,
  and why

## 6. How to hand this off

1. Replace `backend/data/dataset.csv` with your real, cleaned file (same
   filename, same schema — nothing else needs to change).
2. Run `python3 backend/scripts/common.py` — confirm it loads without
   errors or warnings.
3. Tell the team the real dataset has landed — this unblocks Persons 1, 5,
   6, and 7, all of whom have likely been developing against placeholder
   data until now, and now need to rerun everything.
4. Update `results.json["_meta"]["dataset_source"]` — actually this field
   gets set by whichever script runs first after your data lands (commonly
   `01_core_stats.py`); confirm with Person 1 that it correctly reflects
   your real source name, not `"placeholder"`.

## 7. Definition of done

- [ ] `backend/data/dataset.csv` contains real, sourced, cleaned data —
      30+ rows if possible, 20 minimum
- [ ] Loads cleanly via `common.load_dataset()` with no errors or warnings
- [ ] Written source/description documentation handed to Person 4
- [ ] You can state, out loud, exactly where every number in the dataset
      came from and defend why the date range and location were chosen
