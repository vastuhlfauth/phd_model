# Landgrid origins

## 2026-11-27 — Step 3 year-aware origins inputs

- Configured the 2019/2021 Filosofi-to-FF pairings once; the default remains
  2021. FF, downscale and composition accept `--year`.
- The 2019 builders read the unpacked interim CSVs and reuse 2021 method
  choices; model fits use 2019 data without cross-validation.
- Synthetic touched-module tests: 55 passed; Ruff passed. No real data run.
- Not yet implemented: COG-mapped cell-commune output, census integration,
  temporal comparison and the 2023 grid. Do not treat the commands below
  as completing the temporal test.
- Prepare files with `python -m landgrid.origins.unpack_filosofi`.
- Build FF: `python -m landgrid.origins.fichiers_fonciers --vintage 2021 --year 2019`;
  `python -m landgrid.origins.fichiers_fonciers --vintage 2022`;
  `python -m landgrid.origins.fichiers_fonciers --vintage 2024`.
- Run `python -m landgrid.origins.downscale --year 2019`, then
  `python -m landgrid.origins.composition --year 2019`. The latter requires
  the 2021 method-choice JSON under interim.

## 2026-11-27 — Step 3 stable-unit census growth factors

- Census measures are summed within connected, year-specific COG units before
  growth ratios are calculated; per-variable factors use census measures or
  their denominator.
- Added individual-growth fallback support for unavailable census bases and
  fallback-to-individual handling for missing configured measures.
- Synthetic temporal tests: 16 passed; Ruff passed. No real data was accessed.
- The end-to-end 2019–2021 temporal test and 2023 grid remain open.

## 2026-11-27 — Step 3 temporal archive preparation

- Added resumable preparation of the two nested 2019 Filosofi archives using
  Windows `tar`, restricted to configured interim destinations.
- Synthetic extraction tests: 5 passed; Ruff and Pylance syntax checks passed.
  The real archives were not unpacked or validated in this session.
- The 2019 unpacker is not yet integrated with the FF or composition builders.
  Commune allocation, COG matching, growth and temporal outputs remain open.
- Run `python -m landgrid.origins.unpack_filosofi` to prepare the archives.

## 2026-11-27 — Step 3 chosen composition and within covariates

- Applied configured overrides, then cross-validation choices, then the
  configured default; missing choice files warn. The benchmark is unchanged.
- Within models train on eligible non-imputed 200 m observations in reached
  natural cells. Within-constant/dependent features are dropped and recorded;
  interim reports include dispersion-adjusted model diagnostics.
- Composition and cross-validation checkpoints invalidate on changed inputs
  or fitting rules. INSEE within results are in-sample; Eurostat is independent.
- The `dnbniv` bound of 80 stays as a plausibility check; `dniv` is not used.
  Section 6.3 wording will be fixed separately.
- Synthetic touched-module tests: 44 passed; Ruff passed. No real data or full
  jobs were run.

## 2026-11-27 — Step 3 verified separation and proportional guards

- Reproduced the actual fold-1 `ind_inc` failure: the missing-covariate
  indicator separates the unknown-age counts; its finite unpenalized fit
  does not exist. The earlier synthetic numerical fixes did not resolve it.
- At the user's direction, configured `ind_inc` proportional to individuals;
  excluded it from both fitting paths and method choice, retained its age-IPF
  margin. No boundary solution or regularization was applied.
- Added the configured absolute bound of 10 on non-intercept coefficients.
  Separation/non-convergence, singular fits and over-bound coefficients cause
  logged proportional fallbacks in composition and cross-validation.
- Cross-validation reports and JSON list fit/fold/reason; any failed variable
  is forced to proportional in final choices. Changed rules invalidate old
  checkpoints; the existing proportional benchmark is untouched.
- Synthetic changed-module tests: 54 passed. Ruff passed, excluding the
  unrelated pre-existing E501 in `fichiers_fonciers.py`.
- With explicit approval, checked all five actual folds in separate hard-capped
  runs: fitting, scoring and all three methods' control totals passed.
  Actual composition fitting/IPF and pooled JSON/report generation also passed.
  `men_5ind` used the configured guard (over-bound/singular fits).
- Each check stayed below two minutes; retained only aggregate diagnostics
  under `data/interim/landgrid/guarded_crossval_checks/`.
- Run `python -m landgrid.origins.crossval`; rebuild composition if needed with
  `python -m landgrid.origins.composition`. Neither full command was run.

## 2026-11-27 — Step 3 stable within-cell line search

- The user's retry completed fold 0 and failed fitting `ind_inc` in fold 1.
- Reproduced the same error synthetically with correlated covariates:
  subtracting large log-likelihood totals rejected a positive Newton update.
- Compare the conditional likelihood increment directly using `expm1` and
  `log1p`; keep the model, convergence tolerance and full-step stopping rule
  unchanged. Failed line searches now report aggregate step diagnostics.
- Synthetic composition tests: 14 passed; Ruff passed. The prior weak-variation
  repair and explicit separated-fit failure remain covered.
- No real-data run; the original `ind_inc` cause remains unverified.
- Retry `python -m landgrid.origins.crossval`; fold 0 can be reused.

## 2026-11-27 — Step 3 within-cell convergence repair

- The user's cross-validation run failed in fold 0 during within-cell fitting.
- Reproduced false non-convergence synthetically with weak within-group
  covariate variation; absolute coefficient updates did not stabilize even
  though the conditional predictions had stabilized.
- Centered the fitting design within natural cells (conditional likelihood
  unchanged) and check the full Newton update of the conditional predictor.
  Damped steps cannot masquerade as convergence; divergent fits still fail.
- Fitting errors now identify the variable, iteration limit and predictor-step
  size, without including restricted observations.
- Synthetic solver and cross-validation tests: 17 passed; Ruff passed.
  No real-data run; the original failing variable remains unverified.
- Retry `python -m landgrid.origins.crossval`; completed folds are resumable.

## 2026-11-27 — Step 3 grouped cross-validation integration

- Added the standalone five-fold grouped cross-validation command, refitting
  natural-level and within-cell models outside each held-out natural cell.
- Applied the existing direct-weight and age-IPF steps to all three methods;
  scored the shared, non-imputed section-6.5 200 m holdouts by cell size and
  Eurostat density class.
- Added per-fold interim checkpoints, pooled method choices, within-model
  dispersion and suppressed zero-offset counts, plus the aggregate report.
- Synthetic acceptance and targeted validation/config tests passed. Ruff passed
  on changed code; an unrelated pre-existing E501 in `fichiers_fonciers.py`
  was excluded. No restricted inputs or real data were accessed.
- Run `python -m landgrid.origins.crossval` to perform the experiment.

## 2026-11-27 — Step 3 within-cell experiment groundwork

- Added a standalone within-cell Poisson fitting primitive with
  household-weighted preprocessing, zero-offset exclusion and
  Pearson-dispersion-adjusted standard errors.
- Added grouped-fold, pooled-median and tie-breaking validation helpers.
- Recorded the second-home decision and the experimental specification
  exception. The proportional benchmark remains unchanged.
- The new helpers are not connected to the composition or validation
  commands. Cross-validation, choice-file handling, model reporting and
  chosen-method output remain to be implemented; do not interpret the
  existing reports as cross-validated results.
- Only synthetic tests were run; no real data was accessed.

## 2026-11-26 — Step 3 validation checkpoint serialization

- Fixed positive-reference counts returned by DuckDB as decimals, which caused
  the aggregate JSON checkpoint to fail during the user's validation run.
- Synthetic tests cover JSON serialization for both validation paths; no
  real-data validation was rerun. Rerun `python -m landgrid.origins.validation`.

## 2026-11-26 — Step 3 experimental composition and age consistency

- Added dwelling-level natural and 200 m FF covariates and direct counterpart
  weights, with household fallbacks and the proportional benchmark retained.
- Added standardised household-weighted Poisson models, five-fold validation,
  individual-first age/income weights and natural-cell age IPF with `ind_inc`.
- Extended section-6.5 three-method validation and Eurostat age comparisons;
  under-11 and under-18 ratios to under-15 are informational only.
- Restricted products, model diagnostics and cell failures remain in interim.
  FF departments, models and validation metrics have resumable checkpoints;
  the three commands write dated logs and aggregate summaries.
- Synthetic touched-module tests and Ruff pass; no real data was run.
- Real-data performance, model convergence and age-margin compatibility remain
  open. Commands are in `docs/data/step03_origins_pilot.md`.
- Existing cleaning applies the floor-code threshold to `dnbniv`; section
  6.3 names `dniv`. The discrepancy remains open before model interpretation.

## 2026-11-26 — Step 3: Eurostat validation missing-data handling

- Count non-imputed 200 m validation cells by Eurostat match, unavailable
  population, and null, zero or negative land surface; counts may overlap.
- Fall back to the full 1 km² area for missing or non-positive land surface.
  Retain unmatched and unavailable-population cells in separate density classes.
- Exclude unavailable population from 1 km comparison totals; do not abort when
  no valid 1 km comparison remains.
- Synthetic validation tests and Ruff pass; no real-data validation was run.

## 2026-11-26 — Step 3: household downscaling and section 6.5 validation

- Added 2021 Filosofi natural-cell downscaling to 200 m using hybrid 2022
  Fichiers fonciers main residences, with dwelling and Filosofi-household
  fallbacks; 200 m natural cells are copied.
- Added the aggregate-only validation report against non-imputed INSEE 200 m
  cells and the Eurostat 1 km grid, including natural-cell/density strata and
  the equal-split baseline.
- Added synthetic coverage for zone-total preservation, fallback selection,
  error statistics, 1 km containment and suppression of counts below 50.
- Targeted origins tests: 32 passed; Ruff passed. No restricted-data build or
  report was run.
- Rebuild, commune-report, downscale and validation commands are documented
  in `docs/data/step03_origins_pilot.md`.

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
