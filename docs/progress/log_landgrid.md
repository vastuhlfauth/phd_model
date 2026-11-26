# Landgrid origins

## 2026-11-26 — Step 3: adopting the 2021/2022 hybrid

- Adopted `hybrid_2024` as the configured 2021 and 2022 rule under section 6.3;
  2024 remains `own`, and own comparisons require a separate output directory.
- Extended the `idlocal` join to 2021 and kept the default hybrid output at
  `data/interim/landgrid/`.
- Updated comparison wording and removed the obsolete build warning; the five
  pilot départements took 2–4 seconds each.
- Focused synthetic hybrid tests pass (3 cases); Ruff passes. No real-data
  build was run.
- Recorded the broader second-home/occasional-dwelling commune and
  natural-cell comparisons, including both null-`ccthp` variants; synthetic
  report tests pass. No broader-category report was run on restricted data.

## 2026-11-26 — Step 3: experimental 2022 hybrid comparison

- Added opt-in `hybrid_2024`; the default remains `own` and hybrid builds
  require a separate output directory. 2022 vacancy remains unchanged.
- Added SQL/Python synthetic branch tests, duplicate-key rejection and
  suppressed CLI counts; settled 2024 RS transfers are not main residences.
- Added a side-by-side census comparison, hybrid branch counts and natural-cell
  household-ratio deciles using complete geometric department containment.
- Synthetic origins tests: 26 passed; Ruff passed. No real data was read.
- Real-data commands are documented in `docs/data/step03_origins_pilot.md`,
  but interrupted builds lack checkpoints and automatic logs/summaries.
- Hybrid adoption and the real-data comparison remain open.

## 2026-11-25 — Step 3d: census selectors and commune report

- Verified 2023 commune housing selectors in the public long-form census file:
  `LOG_T1` / `DS_RP_SERIE_HISTORIQUE` and four housing `TAB_MEASURE` values.
- Added the dimension-value row-count inventory and documented the selected
  periods, selectors, and department-33 comparison. Three measures are within
  3.4% of 2021; second homes differ by +6.35%.
- Added `ff_communes_{vintage}.parquet` beside the cell aggregate, including
  owner-occupied inputs for the recent-transfer sensitivity cases.
- Added the `report` subcommand with matched-commune ratios/deciles, three
  transfer interpretations, top second-home gaps, Filosofi `log_soc`, and
  suppressed small counts.
- Synthetic origins tests and Ruff pass. No real FF build or report was run.

## 2026-11-25 — Step 3c: SQL pipeline and census schemas

- Moved Fichiers fonciers classification, cell assignment, cleaning
  diagnostics and aggregation into DuckDB; synthetic results match the
  Python reference.
- Derived the default department set from the pilot commune list and natural
  cells; `--department` remains an override.
- Added the census dossier-complet schema page with the 2021 and 2023 row
  counts. The 2023 Parquet has no `P23_*` fields and stores measures in
  `OBS_VALUE` with dimension selectors.
- Kept the 2023 commune comparison pending verified housing selectors; no
  census observations or guessed selectors were added to documentation.
- Targeted origins tests: 13 passed; Ruff passed. No real FF build or report
  was run.

## 2026-11-25 — Step 3 origins: config, natural helpers and FF cells

- Added `config/origins.yaml` for 2021, 2022 and 2024 FF vintages and section
  6.3 cleaning codes. Only the second-home rescaling coefficient is unconfirmed.
- Added `filosofi.py` natural-cell decoding, 200 m containment and derived
  département lists from `lcog_geo`.
- Added `fichiers_fonciers.py` 200 m classification, cleaning, aggregation,
  cache signatures and restricted-data diagnostics. House/flat flags use
  `loghmais` / `loghappt`.
- Synthetic tests pass; real FF builds and commune ratios remain deferred to
  the commands in `docs/data/step03_origins_pilot.md`.

## 2026-11-25 — Step 3b aggregate checks

- Added restricted-data aggregate checks to `docs/data/fichiers_fonciers.md`;
  counts below 50 are suppressed and no row-level values are included.
- In the 2022 département-33 partition, `X`/`Y` match EPSG:3035 ranges and
  98.54% of dwellings match a Filosofi 200 m row. `ban_geom` EWKB records
  SRID 2154; 35.93% of paired points fall in different 200 m cells.
- Exact share outside the département-33 bounding box remains open; the full
  local commune-geometry scan exceeded the one-minute limit.
- No local Cerema documentation was found for `source_geo`, `vecteur`,
  `ccthp` or `proba_rprs`; no code meanings or field substitutions inferred.
- `loghvac = 't'` and `ccthp = 'V'` select exactly the same 74,847 dwellings.
  The two candidate main-residence rules each count 782,301.
- 774,603 candidates lie in a Filosofi 200 m row intersecting 33, against
  735,421.1 Filosofi households. Fewer than 50 located candidates fall outside
  every natural-level cell (0.0056%); 1,190 candidates lack `X` or `Y`.
- Strict / combined `catpro2` containing `F1`: 111,881 / 118,658, versus
  99,906.6 Filosofi `log_soc` in the 33 200 m rows.
- Neighboring departments required: 17, 24, 40 and 47; all four 2022
  `pb0010_local` partitions exist. No package code or specification changed.

## 2026-11-25 — Step 3 data pages (in progress)

- Added Fichiers fonciers, Filosofi and Eurostat grid pages; indexed all three.
- Fichiers fonciers 2022 department-33 Parquet reads directly in DuckDB:
  1,766,607 rows; `idlocal` is unique.
- The 2022 schema has no `geomloc` or `rppo_rs`; no aliases were inferred.
  Section 6.3's four occupancy/residence groups cannot be computed.
- Filosofi 2021 totals: 2,324,577 200 m rows and 146,641 natural-level rows
  across metropolitan France, Martinique and La Réunion.
- The department-33 Filosofi subset uses official `lcog_geo` commune
  intersections. 200 m sums reconcile to natural-level values in every
  metropolitan natural cell (maximum household gap about 1.5e-9).
- Natural-level cells with linked populated 200 m records in both department
  33 and another department: at least 157; 19,450.2 whole-cell households.
- Eurostat grid IDs round-trip for all 4,595,919 grid-coded rows. 6,992
  linked 1 km cells total 1,656,946 population; this is not a clipped or
  independently boundary-validated total.
- A direct DuckDB read of the full 2021 commune geometry exceeded 60 seconds
  and was stopped. No raw data changed and no package code was added.
- Before implementation, resolve the missing Fichiers fonciers fields and
  obtain exact geometric straddler / Eurostat boundary counts if needed.
