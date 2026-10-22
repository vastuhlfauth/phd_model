# 15. Risks and open points

- **Rebuilt PT supply.** Both states use 2026 timetables: lines closed before 2026 are missing (8 known), frequencies are those of 2026, and changes outside trams depend on the completeness of the openings list; ordinary bus routes are those of 2026. OSM route relations are too incomplete for buses and rail to support an automatic rule (section 5.6).
- **BPE.** The retained groups are defined in two nomenclatures (2021 and 2023), and BPE 2025 stands for the 2023 state, two years later.
- **Fichiers fonciers.** Restricted access; public premises poorly described (hence OSM for the public sector); `cconac` of medium quality; variables that change between millésimes.
- **Origins imputation.** Large natural-level cells in rural areas leave most of the location to the keys; the validation by cell size measures this, and the 2023 Filosofi-like data rest on a model.
- **Energy.** Two rate sets differ by about a third for walking; MET-to-kJ conversions carry about ±20%; the constancy of the daily budget is a hypothesis to test on EMP 2019, a pre-COVID survey, on ENTD 2008 and on the 14 EMC² surveys.
- **Declared trips.** Survey distances and durations contain implausible values, and a single trip with a large weight can move a group mean: one ENTD 2008 bike day reached 1.3 million kJ before correction. Speeds are checked for walking, cycling and car trips, not yet for public transport and train, and no mode has a duration check (section 9.9). The share of persons without trips differs strongly between ENTD 2008 and EMP 2019 (15.5% and 2.7% on weekdays), so the two surveys are compared on days with trips.
- **Congestion and crowding coefficients.** Physiological evidence for stress-related energy is thin; these coefficients are parameters with sensitivity ranges.
- **Congestion on a reduced network.** A grid edge stands for several roads, so its capacity is not physical; the BPR calibration absorbs the difference, but capacity and the α parameter are hard to separate without traffic counts.
- **Coarser grid.** With 8 neighbours the directional bias reaches 8.2% for straight trips; the pilot measures whether a correction factor is enough.
- **Storage.** Opportunity curves at 200 m and full car tables are large; the pilot sets bins, bands and what is kept.
- **PT computing time** from 2.3 million origins; the fast variant must be validated before national runs.
- **Overture schema changes and retention.** POI queries need versioned mappings and tests; releases disappear after 60 days.
- **Census pooling.** Census years pool five collections, so changes between 2021 and 2023 are smoothed.
- **OSM change between snapshots** mixes real infrastructure changes and mapping improvements; infrastructure edits for the back-test must be curated.
- **Foreign regions.** Only jobs and nature are covered abroad; jobs rest on Overture.
- **Approximations of the engine.** Level 1 updates, bounds and the decomposition by new elements are checked against full runs on samples and in the back-test.
