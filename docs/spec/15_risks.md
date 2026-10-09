# 15. Risks and open points

- **Rebuilt PT supply.** Both states use 2026 timetables: lines closed before 2026 are missing, frequencies are those of 2026, and the stop-matching rule can keep lines whose stops are shared or still mapped; the calibration measures this.
- **BPE.** The retained groups are defined in two nomenclatures (2021 and 2023), and BPE 2025 stands for the 2023 state, two years later.
- **Fichiers fonciers.** Restricted access; public premises poorly described (hence OSM for the public sector); `cconac` of medium quality; variables that change between millésimes.
- **Origins imputation.** Large natural-level cells in rural areas leave most of the location to the keys; the validation by cell size measures this, and the 2023 Filosofi-like data rest on a model.
- **Energy.** Two rate sets differ by about a third for walking; MET-to-kJ conversions carry about ±20%; the constancy of the daily budget is a hypothesis to test on EMP 2019, a pre-COVID survey, and on the 14 EMC² surveys.
- **Congestion and crowding coefficients.** Physiological evidence for stress-related energy is thin; these coefficients are parameters with sensitivity ranges.
- **Storage.** Opportunity curves at 200 m and full car tables are large; the pilot sets bins, bands and what is kept.
- **PT computing time** from 2.3 million origins; the fast variant must be validated before national runs.
- **Overture schema changes and retention.** POI queries need versioned mappings and tests; releases disappear after 60 days.
- **Census pooling.** Census years pool five collections, so changes between 2021 and 2023 are smoothed.
- **OSM change between snapshots** mixes real infrastructure changes and mapping improvements; infrastructure edits for the back-test must be curated.
- **Foreign regions.** Only jobs and nature are covered abroad; jobs rest on Overture.
- **Approximations of the engine.** Level 1 updates, bounds and the decomposition by new elements are checked against full runs on samples and in the back-test.
