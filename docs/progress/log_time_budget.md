# Progress log: time budget and variation (steps 11 and 12)

Survey reconstruction, time budget and time per mode, 2008-2019 variation, Zahavi reports, handoffs.
Newest entry first. Add yours at the top.

### Spec: time per mode and the mobility model (2026-11-20)

- Decision of 20 November 2026 (spec 9.9, new 10.4): the reference constant is
  f_m, the national distribution of minutes per user day of each mode (EMP
  2019, weekdays, reference scope), checked on ENTD 2008. It replaces the
  daily budget per population category b_k, which becomes a validation
  output. The constraint T(c) = B(c) is retired; total daily time is an
  output.
- New section 10.4, the mobility model: mode use as day patterns; required
  time per mode from the O-D products; allocation within f_m by national
  rank, with a correlation rho_m and a drift factor delta_m (default 1);
  destinations by the radiation model tilted to fill the allocated time.
  New package `mobgrid/mobility/`, a later step after the PT engine.
- No density classes in the model, neither for mode use nor for time
  (decision of 20 November 2026). They remain a test dimension: the INSEE
  density grid of EMP 2019 in cross-section, the proxy of spec 9.9 only for
  2008-2019 comparisons.
- Step 11 (`mobgrid/budget`) gains f_m and the inputs of the mode-use model
  (spec 9.9, re-estimation steps 5 and 6). Not started.
- Spec files changed: 00, 01, 02, 03, 04, 05, 06, 09, 10, 12, 13, 14, 15,
  16 and README. New placeholders are listed under "Open points from the
  spec".

### Mode-cell report: CLI and synthetic integration (2026-11-20)

- Added the all-scope CLI and Markdown report, with the six requested CSVs.
  Signed Z1 caches are read without modification; source trip legs and
  respondent attributes are rebuilt in temporary directories. The existing
  cache makes reruns possible, but report-stage checkpoints were not added.
- The report includes all-scope subgroup and reweighting tables, B2 variants
  and rounding bounds, reference-scope energy and collapse results, disclosure
  notes, fallback/support information and unsupported-energy coverage. Each
  stage logs elapsed time; the dated log and summary use the configured logs
  directory. Per-scope and rate-set intervals are in the CSVs.
- Synthetic end-to-end CLI uses temporary fixtures for both surveys and all
  eight scopes. Report writing took 0.12 s for four days, two modes and five
  draws; this is not a comparable 500-day benchmark. Scaling the earlier
  2.607 s calculation stages linearly by days, modes and draws gives about
  79 minutes for 26,000 days, seven modes and 200 draws. This is highly
  uncertain: pairwise KS, I/O, source extraction, reconstruction and report
  writing do not follow that scaling and were not measured at full size.
- CLI config-file defaults follow the existing Z3 CLI pattern, since the
  requested no-extra-flags command needs them and the shared config modules
  cannot be changed while Z3 runs. They can all be overridden via CLI flags.
- No real-data report or data write was run. Open point: compare synthetic
  estimate with the user's eventual full-run summary.

### Mode-cell report: reference energy calculations (2026-11-20)

- Added reference-scope KH and Compendium energy by overall population,
  population category, density, income, vehicles and day-mode group, with
  household-bootstrap intervals, ratios, verdicts and disclosure flags.
  Day-mode per-person values are explicitly undefined. Attributable mode
  energy uses the full roster, with non-users zero; open days and days with
  only unsupported energy are excluded from both numerator and denominator.
- Joined cached day energy and roster attributes to reconstructed mode energy
  with consistency checks. Known daily mode energies must sum to cached totals;
  synthetic tests also verify the per-person identity in bootstrap draws.
  The collapse test and both rate-set loaders remain separate calculations
  until the report orchestrator connects them.
- Synthetic grouped-energy timing: 0.047 s for both rates, 500 days, two modes
  and 20 draws, excluding reconstruction and all other stages. Together with
  earlier synthetic stages (2.56 s), this is 2.607 s; workload scaling is
  uncertain and excludes extraction, reconstruction and report I/O.
- Local energy draw-weight and cache-join helpers are kept in the new module
  to avoid changing shared functions during the running Z3 job; review for
  merging into shared helpers later.
- **Stage 5 remains:** connect all calculations and both rate sets to the
  CLI; six CSVs, Markdown report, logging and summary; synthetic end-to-end
  test and timing. No real-data report or data write was run.

### Mode-cell report: energy groundwork, superseded above (2026-11-20)

- Added a scoped trip-energy loader that joins the unchanged Z1 cache to
  reconstructed step-11 KH or Compendium trip energy, and a reference-scope
  collapse calculator. It computes pairwise and same-mode cross-year
  weighted KS distances, shared-household bootstrap intervals, and the
  median energy-versus-time contrast. Missing energy does not erase the
  corresponding time distribution; median comparisons use pairs with
  energy available for both modes.
- Synthetic collapse timing: 500 days, two modes and 20 household draws,
  both rate sets, took 0.016 s, excluding reconstruction, grouped energy,
  and every other stage. No reliable full-report runtime is available.
- **Stage 4 remains incomplete and uncommitted**: implement grouped daily
  energy per travel day and per person for category, density, income and
  vehicles; day-mode energy per travel day with per-person marked undefined;
  per-mode attributable energy per person with zero users and open days
  handled as agreed, and a sum-to-total test. Connect the collapse test to
  both reconstructed rate sets and add end-to-end synthetic tests.
- **Stage 5 remains:** safe, resumable source reconstruction and cache
  handling; CLI, per-stage logs and summary, six CSVs and Markdown report,
  and synthetic end-to-end checks. The module still exits with an explicit
  not-implemented message when invoked. No real-data report or data write.

### Mode-cell report: per-mode B2 and rounding (2026-11-20)

- Added per-mode user-day B2 decomposition with shared household-bootstrap
  95% intervals, keeping the distance-selection term separate. The published
  variant reads `distance_km_declared` from reconstructed step-11 trip legs,
  not the speed-corrected Z1 cache. The alternative uses 2008 crow-fly km and
  2019 crow-fly km rounded to whole kilometres.
- Added C4 row-a nearest/up duration-rounding extrema per mode-user day.
  Missing 2019 duration cells are flagged and their 2008 trip-weight share
  recorded; these bounds are incomplete. Day-table comparisons are suppressed.
- Synthetic timing: 500 days, two modes and 20 household draws across eight
  scopes took 0.328 s for decomposition and rounding, excluding source
  reconstruction and all other stages. Timing is logged per scope and stage.
- Clarification for the subgroup stage: its cached `distance_km` comes from
  step 11 and includes speed corrections; its output labels that source.
  The published-distance B2 variant above deliberately uses the reconstructed
  uncorrected producer value instead.
- Remaining: both-rate energy and collapse tests; build/reuse trip-leg
  reconstruction safely and connect all stages to resumable CLI/report,
  six CSVs and Markdown. No real-data report or data write was run.

### Mode-cell report: mode-user reweighting (2026-11-20)

- Added mode-specific 2019-to-2008 joint reweighting, with independently
  paired household-draw intervals for raw and reweighted ratios. Unknown
  population category or income is excluded and its weight share recorded.
  Sparse density neighbours may merge; population categories and income
  quintiles remain separate. Small retained joint cells still contribute.
- The configured Z2 maximum lost-target share applies to each draw and is
  strict: below it, rescale onto common support; at or above it, the
  reweighted estimate is unavailable. The 2008 fixed-cell diagnostic uses
  the population parent when a 2019 cell has no 2008 observations and
  reports the fallback share; a missing parent is explicitly unavailable.
  Day-table cross-year output is suppressed and labelled.
- Synthetic timing: 500 days, two modes and 20 household draws over all
  eight scopes took 0.078 s, excluding extraction and all other stages;
  timings are logged per scope. This is not a full-report runtime estimate.
- Remaining: connect both completed stages to the output, implement
  per-mode B2 and whole-km distance variant, duration-rounding bounds,
  both-rate energy and collapse tests, and the resumable CLI/report with
  six CSVs and Markdown. No real-data report or data write was run.

### Mode-cell report: subgroup statistics (2026-11-20)

- Added scoped mode-user-day loading and all six subgroup analyses, using the
  Z3 ordered-neighbour merge rules while preserving nominal categories.
  Household identifiers are text before bootstrap lookup. Mode national
  comparisons retain hidden and unknown-category days; unknown population
  categories are excluded from category cells with their weight share shown.
- Cell outputs include per-year minutes, known-distance km/day and aggregate
  speed, 95% household-bootstrap intervals, weighted KS against national mode
  users, and an additive distance/speed/selection split. Missing-distance
  km are a lower bound, with trip coverage and a separate selection term.
  Cells below 50 days are hidden, those below 100 flagged, and day-table
  cross-year results are blank and labelled. The caller supplies thresholds.
- Synthetic timing: 500 days, two modes and 20 household draws in all eight
  scopes took 2.141 s for cell calculations (0.22–0.38 s per scope); this
  excludes data loading and every later stage. It is not a report runtime.
  Stage timing is logged by `evaluate_mode_scope`.
- Still to do: integrate the cell stage into the report and verify its
  end-to-end output; reweighting, B2/crow-fly and rounding, energy/collapse,
  the resumable CLI and all six CSVs and Markdown. Parent fallback remains
  to be implemented where a 2008 comparison cell is absent. No real-data
  report or data write was run.

### Mode-cell report: isolated foundations (2026-11-20)

- The report is **not complete**. Added isolated mode-user-day aggregation
  and exact joint-target reweighting primitives. Aggregation retains
  distance-known counts and time for B2's selection term, preserves missing
  energy, and converts household identifiers to text. Reweighting does not
  merge nominal levels and explicitly rejects unsupported target cells.
- Synthetic checks cover aggregation at a constant energy rate, missing
  energy, inconsistent weights, exact joint-target reweighting and missing
  support, B2 decomposition, and weighted-KS symmetry. The module does not
  yet implement the CLI; running it explicitly reports that fact. Eight
  synthetic tests passed; Ruff and Pylance syntax checks passed.
- Decision: day-mode-group energy is per day with trips only; its per-person
  basis is undefined because zero-trip days have no mode group. Per-mode
  per-person energy is attributable, including non-users as zero, and must
  sum to total per-person energy. Category, density, income and vehicle
  groupings use both bases.
- Remaining: load and join mode-user days and survey attributes for all eight
  scopes; implement cell estimates and bootstrap intervals, subgroup versus
  national KS and distance/speed gap split, suppression and caution flags,
  day-table labels and cross-year suppression, and absent-2008 parent
  fallback. Integrate Z2's draw/support policy with the new target reweighting
  without merging nominal categories and report raw and reweighted ratios.
- Remaining: per-mode published/rounded-crow-fly B2 decomposition and C4
  rounding bounds; reconstruct trip energy with both rate sets without
  modifying the signed Z1 cache, implement grouped and attributable energy
  with the agreed bases and per-person sum check, and implement all pairwise
  and cross-year collapse tests with bootstrap intervals. Wire the six CSVs,
  Markdown report, resumable checkpoints, logging, summary and CLI; add
  synthetic end-to-end coverage. Runtime is unmeasured.
- No shared helper was changed; the new target reweighting function is local
  to the new module and should be considered for a later shared-helper merge.
  No real-data report or data write was run.

### Grouping report: CLI and output (2026-11-20)

- Completed `python -m mobgrid.budget.zahavi_groupings --out docs\data\step12_groupings`:
  eight scopes, four CSVs, Markdown report,
  timestamped log and run summary. It reads signed Z1/Z2 caches and shared
  household draws; it does not rebuild trip legs. Attribute and scope
  checkpoints resume only under a matching input, configuration and code
  signature. Stage elapsed times are logged.
- Day-table cross-year results are blank and labelled throughout; small-cell
  values are hidden without removing their contributions. Population
  exclusions and absent-2008 parent fallback shares are reported. Age-band
  code `0` is normalized to the documented `00` before grouping.
- Synthetic integration covers all eight scopes, output, CLI and checkpoint
  resume. Changed-module tests: 25 passed; Ruff passed. The fixed-mode
  distribution uses weighted mid-rank matching within each mode, not
  independent mode draws. No real-data report was run.
- Synthetic timing: 500 persons per year, 10 draws and 14 groupings in one
  scope took 0.360 s for cell statistics and 0.281 s for counterfactuals.
  A naive linear scaling to 15,500 persons and 200 draws across eight scopes
  suggests roughly 45 minutes including previously observed extraction time;
  30–120 minutes is a very uncertain planning range, not a measured runtime.
  Cell cardinality, bootstrap validity, disk I/O and mode calculations may
  change it substantially. The generated run summary reports actual timings.

### Grouping report: household type verified (2026-11-20)

- Both releases document the same `TYPMEN5` codes: 1 single person,
  2 single parent, 3 couple without children, 4 couple with children,
  5 other/complex. Added the source entries to both dataset notes and a
  tested mapping on the existing household views. The earlier label
  verification open point is resolved.
- Synthetic grouping tests: 23 passed; changed-file Ruff passed. The report
  and CLI are not yet wired; no real-data report ran.

### Grouping report: cross-scope summary rows (2026-11-20)

- Added one summary row per scope and grouping, sorted within scope by the
  counterfactual ratio's distance from one. The four day-table scopes retain
  within-year eta-squared but suppress all cross-year summary fields and
  display the coverage warning.
- Household-type label verification, report rendering, the resumable CLI,
  checkpointing and synthetic runtime timings remain open. No real-data
  report ran.

### Grouping report: per-mode person estimates (2026-11-20)

- Added cached mode-by-day loading and section 9.9's roster denominator,
  including zero days and subtraction of open-day weights. The paired
  household draws provide 95% intervals for the exact use-share and
  time-per-user decomposition.
- The fixed-mode distribution maps weighted mid-ranks of 2019 mode-user
  days to the 2008 weighted empirical mode-user distributions, preserving
  2019 mode-use combinations. Equal 2019 durations are ordered stably.
  The distribution's finite-sample mean need not equal the analytical
  fixed-mode mean. A negative residual zero-day weight is an explicit error.
- Day-table cross-year results are suppressed. These functions are not yet
  wired to the report; no real-data report ran. Household-type labels and
  the cross-scope summaries, CLI, checkpointing and report remain open.

### Grouping report: fixed-cell statistics (2026-11-20)

- Added fixed-cell predictions, observed/predicted mean ratios with paired
  household-bootstrap 90% intervals, mix terms, weighted KS with 95%
  intervals and both distributions' deciles. Full-sample absent cells use
  their parent distribution; their 2019 weight share is recorded. Empty
  bootstrap support invalidates that replicate instead of changing the
  fixed partition or silently selecting a new parent.
- Day-table cross-year results are suppressed. These calculations are not
  yet connected to a report or CLI; no real-data report ran. Household-type
  labels, per-mode statistics, cross-scope summaries and output remain open.

### Grouping report: cell statistics groundwork (2026-11-20)

- Added cached weekday travel-day loading, the requested partition catalogue,
  fixed ordered-secondary merges, unknown-category exclusion shares, cell
  levels and pooled stability, and household-bootstrap eta-squared intervals.
  Day-table comparisons are suppressed and carry the agreed coverage warning.
- Household-type categories remain unresolved: both survey household tables
  have a `TYPMEN5` field, but its code labels have not yet been verified.
  The loader accepts a verified mapping, but no mapping is inferred.
- Cell calculations are not yet wired to CSV or report output. The fixed-cell
  statistics, per-mode model, cross-scope summary, resumable CLI and report
  remain incomplete. No real-data report ran.
- Synthetic grouping tests: 13 passed; changed-file Ruff passed.

### Grouping report: incomplete synthetic groundwork (2026-11-20)

- Added ordered-neighbour configuration and a full-sample merge helper that
  leaves nominal dimensions untouched. Added weighted eta-squared and a
  fixed-cell distribution helper with a parent fallback for cells absent in
  2008; an empty bootstrap cell does not trigger a new fallback.
- The report, survey joins, all-scope calculations, confidence intervals,
  per-mode model, CSVs, checkpointing and CLI remain unimplemented. The
  module exits with an error if run as a report. No real-data report ran.
- User decision: include all eight scopes; for the four day-table scopes show
  within-year results only, suppressing cross-year comparisons because ENTD
  coverage beyond 80 km is not established. Exclude unknown population
  category from category partitions and report its weight share. Never merge
  nominal levels; retain unresolved small cells in calculations, hide their
  published levels, and disclose parent fallback shares.
- Synthetic grouping tests and changed-file Ruff were run; see the task
  report for their results. Runtime for the unimplemented report is unknown.

### Zahavi income correction: zero vehicles, joint cells and income shares

- EMP households with `JNBVEH = 0` are classified as zero even when the
  follow-up `JNBVHS` and all out-of-use counts are blank.
- Joint reweighting starts from observed cells only and pools sparse cells
  individually within quintile. The report and reweighting CSV show the
  full-sample pooled target share in merged cells, by estimation basis.
- The report shows each quintile's individual-weighted roster share, omits
  an empty ENTD unknown-income group, and quotes all three vehicle questions.
  The ENTD release is complete; its dictionary does not establish upstream
  imputation.
- Validation: 41 synthetic income tests passed and Ruff passed; the
  real-data report was not rerun.

### Zahavi income correction: harmonised household vehicles (2026-11-20)

- ENTD `q_menage.csv` contains `V1_JNBCCVUL`; classes use
  `V1_JNBVEH + V1_JNBCCVUL`. EMP `Q_MENAGE_public` contains all three
  out-of-use counts, so the in-use total subtracts them from `JNBVEH`.
  Missing out-of-use counts become zero only for `JNBVHS = 2`; otherwise
  the class is unknown. A fallback uses `JNBVEH` and reports the weighted
  `JNBVHS = 1` household share if the counts are absent.
- Dataset notes now quote the questionnaire prompts and document the
  harmonised definition. The income report generator adds household-weighted
  shares for 0, 1, 2+ and unknown classes with unweighted household n.
- Synthetic checks: 40 income tests passed; changed-file Ruff passed.
  No real-data report was run; regenerate with
  `python -m mobgrid.budget.zahavi_income --out docs\data\step12_income`.

### Zahavi income correction: grouped warnings (2026-11-19)

- Insufficient bootstrap intervals are reported once per estimate group,
  with counts by valid/total draw count; regression summaries also count
  rank-deficient draws and nonfinite effects. Individual coefficients
  retain their own 95%-valid-draw requirement.
- The final support audit also emits zero-respondent, zero-household rows
  for original reweighting cells absent from one year, with all that year's
  draws marked empty.
- Synthetic income tests: 38 passed; Ruff passed. The real report was not
  rerun.

### Zahavi income correction: earlier vehicle definitions (2026-11-19)

- This preliminary cars-only interpretation was superseded by the
  2026-11-20 harmonisation above, after verifying `V1_JNBCCVUL` and the
  EMP public out-of-use count fields.

### Zahavi income correction: reweighting (2026-11-19)

- Joint cells below the configured respondent minimum are pooled within
  quintile: cars 1 and 2+ first, then sparse and very sparse density.
  The existing fallback pools all density and car categories within a
  quintile if a cell still has no common support. A remaining small cell
  is reported explicitly and that quintile's reweighted estimates are
  unavailable; no additional unrequested merge is invented.
- Each draw records its lost pooled-target share in `reweighted.csv`.
  The target is rescaled onto common cells only below the configured 1%
  limit; the strict boundary and retained estimates have synthetic checks.
  `support.csv` includes both original and collapsed cells.
- Synthetic-only validation; no real-data report ran. Car wording and
  warning aggregation remain outstanding.

### Zahavi income correction: regression (2026-11-19)

- Sparse observed predictor levels are pooled with configured adjacent
  levels using respondent counts in both full samples, before drawing.
  The report lists each merge and `support.csv` includes original levels
  as well as fitted columns. Missing income remains a separate 2008
  category rather than being assigned to a known quintile.
- Bootstrap WLS drops empty columns only for that draw and retains
  coefficients identifiable despite other rank deficiencies; each effect
  keeps its own valid-draw interval. The pooled design never constructs
  a 2019 interaction for 2008-only unknown income.
- Synthetic checks: 32 passed; Ruff passed. Reweighting, car definition and
  warning aggregation are not yet corrected. No real-data report ran.

### Zahavi income correction: support audit (2026-11-19)

- Added per-scope `support.csv` with respondents, households and empty
  household draws for each regression column and reweighting cell, per
  year; structural pooled-model zeros are flagged. The report includes a
  compact group/year summary. Per-person empty cells use the net
  denominator after open-day removal.
- Synthetic-only validation; no real-data report or data write. Remaining
  corrections: sparse-level merging, per-coefficient rank handling, joint
  cell collapse and partial-support draws, vehicle wording, and warnings.

### Zahavi income supplement: bootstrap warning investigation (2026-11-19)

- The completed run summary records 23 or 40 travel-day reweighting draws
  and 11 per-person reweighting draws without common support, depending on
  scope. It also records 79 rank-deficient draws in three regression fits
  per scope. The summary does not identify their cells, predictors or years.
- Z2 discards a whole reweighting draw if any joint cell lacks support.
  A synthetic two-quintile check confirmed that this also discards a Q5
  result when only Q1 has lost support and Q5 remains estimable.
- Z2 also discards every coefficient in a rank-deficient WLS draw. A
  synthetic check confirmed that a missing nuisance-indicator column can
  make the full design singular even when the Q5 coefficient is identifiable
  from the remaining columns.
- The inherited interval rule requires 190 of 200 valid draws, so these
  wholesale exclusions suppress intervals. The missing real-data cells and
  regression columns remain unverified; sparse household categories are a
  hypothesis, not a confirmed cause. Do not infer the affected predictor
  or accept the report as a complete set of intervals from this summary.
- Follow-up: add cell/term-specific diagnostics and assess estimability
  separately, retaining the shared household draws and paired intervals.
  No code, real-data outputs or checkpoints were changed or rerun during
  this investigation.

### Zahavi income supplement: report and CLI (2026-11-19)

- Completed income levels, paired gaps and 90% ratio intervals, pooled
  joint-distribution reweighting, M0–M2 and pooled weighted regressions,
  quintile-by-density tables, conclusion grids, five CSVs and Markdown.
  The ENTD unknown-income group is separate; the imputed EMP income has
  no equivalent group. Both years use the step 11 density proxy and
  household cars grouped 0, 1, 2+.
- Per-person cell support accounts for excluded open-day weights before
  collapsing empty cells. Estimates require at least 95% valid bootstrap
  draws for an interval, including the 90% cross-year ratio interval.
  The ratio-validity guard is local to Z2 because the existing shared
  ratio helper filters invalid draws without that guard; consider merging
  this rule into shared code later.
- Reuse Z1's signed caches and household draws; completed scopes checkpoint
  under `data/interim/budget/zahavi_income` and resume when input signatures,
  report code and configuration match. No report was run on real data;
  both existing Z1 cache signatures were verified read-only.
- Open point: exact ENTD/EMP household vehicle coverage still needs
  questionnaire verification. The M2 gap is a conditional geometric
  ratio, not the reweighted arithmetic-mean gap.
- Run: `python -m mobgrid.budget.zahavi_income --out docs/data/step12_income`.
  Runtime is unmeasured; an eight-fit synthetic WLS benchmark extrapolated
  to about 3 minutes for 11,200 fits alone, excluding I/O, extraction,
  reweighting and other work. Allow roughly 15–60 minutes; actual time
  may differ substantially.
- Synthetic income tests: 28 passed; changed Python files pass Ruff.
  No full suite, real-data report or download was run.

### Zahavi income supplement: controls groundwork (2026-11-19)

- Added cache-roster joins for income, residence proxy, car bands and
  weekday; both survey car-count inputs retain missing values explicitly.
- Added pooled-weight estimates with shared paired draws and a documented
  common-support collapse: pool cars within density, then pool density and
  cars within a quintile if a density is absent in one year. Added
  weighted log-regression design, bootstrap and percentage-effect helpers,
  plus the quintile-by-density table with suppression and warning flags.
- Synthetic checks: 21 passed; changed-file Ruff passed. Remaining:
  survey attribute extraction and joins, invoking the complete models,
  real-data edge cases for empty person-denominator cells, the CLI, report,
  CSVs and conclusion grid. No real-data report ran. Runtime is unmeasured.

### Zahavi income supplement: level and gap calculations (2026-11-19)

- Added weekday travel-day and per-person estimators using the Z1 shared
  household multipliers, including zero-trip people and subtracting open
  days. Level and ratio rows suppress small cells and keep the 2008
  unknown-income group separate; gap rows calculate 95% intervals from
  paired household draws.
- Synthetic checks: 11 passed; Ruff passed. Cache joins and report/CLI
  integration remain outstanding; no real-data report ran.

### Zahavi income supplement: ENTD car input (2026-11-19)

- Added a standalone CP1252 household-car loader using `V1_JNBVEH` and
  household IDs, retaining the existing signed mode caches. Counts are
  grouped 0, 1 and 2+; blanks remain unknown, and malformed counts and
  duplicate IDs fail explicitly.
- The supplied 20,178-household file has no blank counts. All 18,632 Kish
  respondents match a household with a nonblank count. Exact vehicle
  coverage against EMP 2019 still needs questionnaire verification.
- Synthetic loader and income tests: 8 passed; changed-file Ruff passed.
  The loader is not yet wired into a report. No real-data report ran and
  no files under `data/` were written.

### Zahavi income supplement: partial groundwork (2026-11-19)

- Added independent helpers in `zahavi_income.py` for the existing survey
  income quintiles, unknown-income shares, paired Q5-minus-Q1 gap changes,
  pooled joint-cell weights on common support, and numpy weighted least
  squares. No shared function or cache signature was modified.
- Synthetic checks: 6 passed; changed Python files pass Ruff. Pylance
  reports no syntax errors in the new module. The real-data income report
  was not run and no files under `data/` or the mode outputs were written.
- Incomplete: report/CLI, per-person and day levels, ratio and gap tables,
  collapse of empty cells, bootstrap regression models, density tables,
  conclusion grid, and item-by-item commits. No runtime estimate for the
  unimplemented CLI is available.
- The public ENTD release lists household-vehicle and vehicle-description
  files, but neither is locally available. Identify and validate the
  household car-count variable before implementing the 2008 car control;
  do not infer that the variable is absent. See `docs/data/entd2008.md`.
- The existing cache stores income and density for trip days but not the
  full roster's income or both surveys' requested density proxy; join
  validated respondent attributes without rebuilding or modifying Z1's
  signed caches. Use temporary files for any extraction.

### Zahavi B3 cached household-ID correction (2026-11-19)

- Reproduced the reported B3 interval crash with numeric Parquet household
  IDs: the draw roster used text IDs but the B3 sample retained integers.
  The B3 cache reader now uses the same text-normalisation helper as the
  roster and other cached samples. Existing caches remain valid.
- The user's run measured cache construction at 22.1 min (ENTD) and
  9.4 min (EMP); the reference-scope analysis reached B3 after about
  1.8 min. All-scope completion time remains unmeasured.
- Rerun the same report command; no cache rebuild is required. No real-data
  report was run by the assistant.
- Validation: numeric-ID regression failed before the fix; all 15 tests
  in the touched mode-report module now pass, and changed-file Ruff passes.

### Zahavi mode supplement CLI (2026-11-19)

- Completed the report CLI and six CSVs, using the signed survey caches,
  shared household draws and all eight scope switches. Missing or invalid
  caches are built automatically; report-only code edits do not invalidate
  trip-leg caches. Stages are timed and a dated log and summary are written.
- The reference-scope stability table checks the rounded 52.0/57.0
  minutes/person against the scope cube and warns on a discrepancy; this
  comparison remains unverified on real data. B3 point terms are quoted
  from the existing report; missing mode-level intervals use its estimator
  and the shared draws only when source and cached trip counts agree.
  Km/trip and speed shares are approximate because the source terms are
  rounded; mismatched counts leave new intervals unavailable with a warning.
- Synthetic cache builds took 14.05 s and 13.49 s; the subsequent tiny
  one-scope report took roughly 1-2 s. These timings do not support a
  reliable estimate for national data or all scopes. No real-data report
  was run; the earlier pending notes below are historical.
- Final validation: 18 synthetic tests passed across the two touched
  modules; Ruff passed on the changed Python files.
- Run `python -m mobgrid.budget.zahavi_modes --out docs\data\step12_modes`.
  The existing reference-scope B3 report must be present at the configured
  source path. No separate cache command is needed.

### Zahavi B3 quotation (2026-11-19)

- Added direct quotation of the existing reference-scope B3 tables, with
  suppression and signed km/trip and speed shares of the within-mode term.
  Shares are approximate because the source publishes rounded mode terms.
- B3 provides aggregate intervals but not per-mode intervals; these remain
  unavailable rather than silently recomputing the decomposition. Ten
  synthetic tests passed; Ruff passed. CLI wiring remains outstanding.

### Zahavi mode stability calculations (2026-11-19)

- Added mode-user, day-mode-group and per-person weighted means and shared
  household intervals, plus trip and minute shares. The per-person path
  calls the scope-cube's `daily_energy` estimator and removes open days.
- Nine synthetic tests passed, including mode totals and open/zero days.
  CLI output and the historical 52.0/57.0 minute check remain to be wired.

### Zahavi mode comparisons (2026-11-19)

- Added weighted interpolated and step deciles, trip-duration thresholds,
  weighted KS distances and paired household-bootstrap intervals. Crow-fly
  band comparisons preserve the same-commune flag when rounding EMP
  distances to whole kilometres.
- Seven synthetic tests passed; Ruff passed. Report/CSV wiring is pending;
  no real-data report was run.

### Zahavi mode distributions (2026-11-19)

- Added cached weekday trip, mode-user-day and step-11 day-mode-group
  samples, with weighted ECDFs and Gaussian densities on minute grids.
  Each group uses a pooled bandwidth with equal total weight per survey;
  zero-variance densities are explicitly unavailable. Small cells are blank.
- Three synthetic tests passed; Ruff passed. CLI/CSV wiring and the remaining
  comparison, stability and B3 tables are still outstanding.

### Zahavi mode-report cache (2026-11-19)

- Added a survey cache API for all eight weekday scopes: signed Parquet
  trip and day tables, the person-weekday roster and the full described-day
  base needed to remove open days from the per-person denominator.
  Signatures cover source data, the energy configuration, scope threshold
  and reconstruction code; a completed cache is reused without rebuilding
  trip legs. Each cache stage logs its elapsed time.
- Synthetic cache tests passed for both surveys (3 passed); Ruff passed.
  No real-data report or long-running computation was run.
- Open: the Zahavi mode-report CLI, outputs and the 52.0/57.0 minute
  reference checks are not yet implemented; the cache API is not yet wired
  into a report. Existing user files under `docs/article/figures/` were left
  untouched.

### Report runtime observation (2026-11-18)

- The first EMP report was still running after about 57 minutes; its CPU
  counter increased between observations. The later queued commands had
  not started, and report/figure timestamps were unchanged.
- The EMP CLI prints its completion message only after `run` and report
  writing finish; there is no intermediate stage output. CPU activity does
  not establish useful progress or identify the current function.
  No running process was interrupted and no report was launched.

### Step 12: subset speed intervals (2026-11-18)

- Common standardisation cells are fixed on the full samples; a draw
  missing any of them is invalid, even if its 2008 mix gives it zero weight.
- Purpose/departure rows report paired valid draw counts in Markdown and
  CSV. Their 90% CIs use valid draws when at least 95% survive (190/200).
  Other speed-table CI gates remain unchanged. Boundary regressions cover
  190, 189 and zero valid draws, retaining the point ratio in every case.
- Final focused selection: 46 passed, 0 failed. Changed-file Ruff and
  source syntax checks passed; modified signatures have compatible callers.
  No full suite, real-data reports, figures or downloads were run.
- Regenerate the four reference-scope reports and the eight-scope cube:
  `python -m mobgrid.budget.emp --out docs\data\step11_budget`
  `python -m mobgrid.budget.emp --survey entd2008 --out docs\data\step11_budget_entd2008`
  `python -m mobgrid.budget.emp --compare --out docs\data\step11_compare`
  `python -m mobgrid.budget.variation_report --out docs\data\step12_variation --entd2008-zoning-data-path data\raw\entd2008\ENTD2008_avec_zonages_EMP`
  `python -m mobgrid.budget.scope_cube --out docs\data\scope_cube`
  Add `--scope all` to the first four commands for all scope variants.

### Step 12: professional-round ledger and preserved audit (2026-11-18)

- The variation loader retains a pre-round-exclusion sample, keeping the
  selected day/distance rules and other destination exclusions unchanged.
  The car-driver rounds table uses this sample and raw destination codes.
- Ledger row h gives the kept-minus-excluded effect on the 2019-minus-2008
  change in minutes/day and trips/day, plus speed ratios with/without
  rounds and the source section. This is a point sensitivity, excluded
  from the existing non-additive residual envelope.
- Cube output explains the new shared destination rule; synthetic totals
  verify the round is removed and its return remains. Focused validation:
  15 passed, Ruff passed. No real-data report run.

### Step 12: professional-round diagnostics (2026-11-18)

- Sequential scope removals now show professional rounds after group 8,
  with weighted trips/minutes/km and household-bootstrap intervals.
  Open-day removals no longer double-count excluded rounds.
- Focused diagnostic regression passed; Ruff passed. No real-data run.

### Step 12: professional-round destination rule (2026-11-18)

- Section 9.9 now excludes recorded EMP 9.4 / ENTD 9.95 destinations
  under `dest`; the following trip remains eligible even with motive 9.4.
- Synthetic acceptance tests cover both codes and retain 9.2, 9.3 and 9.5.
  Scope tests: 10 passed; Ruff passed. No real-data report run.

### Step 12: commuting, peak hours and professional rounds (2026-11-18)

- Added the supplied questionnaire wording, plus weekday speed comparisons
  by harmonised purpose and departure period, a counterfactual excluding
  recorded professional rounds, and commute distance and duration tables.
  Each new table has a CSV sidecar and suppresses estimates based on fewer
  than 50 trips. Speed comparisons use each subset's 2008 mix on common support.
- Six focused synthetic cases and Ruff passed. No figures or real-data
  report were run; whether the slowdown is concentrated in commuting or
  peak hours remains to be checked on the regenerated report.

### Step 12: clock-speed bootstrap safeguard (2026-11-17)

- Sparse mode × distance × density cells can disappear in a household
  draw. The standardised estimator discards that draw, and the previous
  ratio code silently calculated an interval from however few paired draws
  survived, or suppressed the point ratio when none survived. A synthetic
  11-cell example retained only 16 of 200 paired draws.
- Clock-speed and the new tour-speed tables now retain the point ratio,
  show the valid draw count, and explicitly mark the CI unavailable unless
  every draw is valid. CSVs likewise leave unavailable bounds blank. This
  is a conservative reporting safeguard, not a way to recover the
  requested CIs; a justified sparse-cell estimation method remains open.
- Survey questionnaires were located, but the local environment has no PDF
  text reader and the online questionnaire fetch did not expose readable
  pages. Questionnaire/guide page references and stop rules remain open.
- Final changed-module selection: 13 passed, 0 failed; Ruff passed. Neither
  the full suite nor a real-data report or any figures were run.

### Step 12: simple versus chained tour speeds (2026-11-17)

- Added the C6 standardised car-driver speed comparison and weighted trip
  shares for two-trip and 3+-trip complete in-scope tours, with a matching
  CSV. Shares use all selected car-driver trips as denominator; incomplete
  or partially filtered tours therefore remain outside both groups.
- Each ratio reports the number of valid paired household-bootstrap draws,
  since sparse standardisation cells can invalidate draws. Nine focused
  tests passed; Ruff passed. No figures or real-data report were run.

### Step 12: trips per tour (2026-11-17)

- Added tour counts and trip-count distributions with a matching CSV. Tours
  are split at residence arrivals on the original day chain; only complete
  tours with every trip in the selected scope count. The tours/day
  denominator includes all selected days with trips, including those with
  no complete in-scope tour. This avoids inventing tours across filtered
  stops, but excludes partial-scope tours.
- Six targeted tests passed; Ruff passed. No figures or real-data report
  were run.

### Step 12: stays between trips (2026-11-17)

- Added weighted stay distributions by survey and arriving-trip mode, and
  under-five-minute stays per day with trips, with a matching CSV and
  suppression below 50 trips. Consecutive trips are identified in the full
  described-day chain before selecting the arriving trip's scope; missing
  times do not enter the stay distribution.
- Five targeted tests passed; Ruff passed. No figures or real-data report
  were run.

### Step 12: trip-delimitation purposes (2026-11-17)

- Added weighted weekday trips per day with trips and minutes per trip by
  main mode and harmonised escort, shopping, work, study, leisure and
  personal-business purposes. Returns retain the section 9.9 origin-purpose
  assignment; visits count as leisure and medical/administrative errands as
  personal business. Each measure is suppressed below 50 eligible trips and
  the report writes a matching CSV. No real-data report or figures were run.
- The remaining trip-delimitation checks and the clock-speed interval need
  separate follow-up; this entry records only the purpose table.

### Step 12: scope cube (2026-11-10)

- New `mobgrid/budget/scope_cube.py` writes the spec's cross-scope
  comparison to `docs/data/scope_cube.md` and
  `docs/data/scope_cube/estimates.csv`: core indicators for the 8 scopes
  × 2 surveys × population categories (and All) on weekdays — n
  respondents/trips, share of person-days kept, trips per day, minutes
  and km per trip (producer and crow-fly, ratios of weighted totals),
  minutes per day on the described-day, travel-day and per-person bases —
  with means/95% CIs, medians and quartiles for per-day quantities, the
  2019/2008 ratio with its 90% CI and verdicts at ±15%/±10%. Flipping one
  switch at a time from the reference gives the change in each indicator
  (2008/2019 levels and the ratio) with paired-bootstrap CIs: one shared
  set of 200 household draws per survey across every scope.
- It reuses, without duplication: the scope chain (`scope.py`), the
  step-11 survey loaders and `trip_legs`, step 12's Kish person-weekday
  roster, `variation.household_multipliers`, `daily_energy`'s weighted
  quantiles and `bootstrap_replicate_ratio_ci`, and the step-12
  suppression/formatting helpers (cells under 50 respondents keep their
  true n and hide values, in the report and in the CSV). No figures.
- Assumptions: the person-weekday universe is 5 × the individual weight
  (as the step-12 roster); `round` drops non-round described trip-days
  from the universe (open-day rule) while trip switches keep the day at
  zero; trips per day uses the days-with-trips basis; ratio columns sit
  on the EMP 2019 CSV rows; switch effects are computed for All only
  (per-category levels for every scope are in item 1). ENTD `daytable`
  cells carry the observed-coverage caveat in the report intro.
- Tests (11) cover hand-computed weighted totals, shared draws across
  scopes (identical scopes give exactly [0, 0] paired intervals), the
  shared ratio function, suppression, an end-to-end run on synthetic
  72-respondent surveys, and CSV rows equalling the report's table cells.
  Repo-wide Ruff passes; the changed module plus `test_scope.py` and
  `test_variation.py` pass (24 tests, 36.5 s). The full suite was stopped
  after more than an hour (the pre-existing step-11/12 figure tests run
  90+ s each; no existing source file was modified) — rerun
  `uv run pytest -q` offline if wanted. No real-data report was run.
  Generate with
  `uv run python -m mobgrid.budget.scope_cube --out docs\data\scope_cube`.

### Step 11/12: report consistency fixes (2026-11-10)

- Step 11 selects Monday-Friday trips before building either survey's
  normalized trips, so SQL diagnostics, robustness rebuilds, tables, overall
  estimates and figures use the same days. EMP retains one separately
  labelled Monday-Sunday per-person sensitivity; ENTD has no weekend
  estimates. The full described-day no-trip audit is preserved so weekend
  travellers are not misclassified as immobile respondents.
- Comparison time-by-category panel A is removed; weekday traveller and
  per-person panels B/C remain. Step 11/12 figure subtitles and CSV day
  metadata explicitly say Monday-Friday. C7 verdicts now put 15% before 10%.
- Scope coverage counts Kish respondents, blanks estimates below 50 and
  omits small unknown categories from scope diagnostics. Step-11 tables and
  shift-share tables likewise omit unsupported unknown rows.
- B7a's title is wrapped and checked against both figure edges. The shared
  saver translates category tick labels (major/minor), legends and category
  titles, without resetting numeric tick locators or restyling the plots.
- Each requested item has its own commit; a test-formatting follow-up is
  separate. The comparison CLI smoke test uses synthetic survey results
  but writes both real figures/CSVs and the report, with a 10-second limit;
  its final call took 1.11 s. Production defaults are unchanged.
- Final changed-test selection: 21 passed, 0 failed (7.36 s); changed-file
  Ruff passed and all three source files passed syntax checks. No full
  suite or real-data report ran, and no generated data documentation was
  edited. Regeneration commands remain the four reference-scope commands
  documented below, invoked as `python -m ...`.

### Step 11: comparison axis scaling correction (2026-11-09)

- `compare_energy_time.png` no longer applies fixed quantity ranges:
  the synthetic energy maximum of 411.5 kJ previously produced a 1500 kJ
  axis. Each panel now retains its data-driven limits, including reference
  lines, confidence intervals and quartiles. Numeric tick locators remain
  automatic instead of being replaced with fixed ticks.
- Four focused comparison/style tests passed (3.86 s); changed-file Ruff
  passed. The regression checks exact preservation of pre-save limits and
  tick locators. The session preview gallery's comparison was refreshed and
  visually inspected; no real-data report or estimate was changed.

### Step 11: complete figure-rendering restoration (2026-11-09)

- The previous readability correction was incomplete: only four plots were
  exempted from the shared resizing and annotations. The default saver now
  preserves every producer's original dimensions, fonts, series colours,
  axes/ticks, heatmap text and colourbars. Automatic value labels and the
  generic bootstrap/quartile footer no longer crowd the survey plots.
  Scope subtitles are small and positioned below the measured title.
- F01/F01b/F01c no longer display redundant sample labels; F01 heatmap
  cells again show just their values. Sample metadata remain in CSVs.
  F04 retains mean/median/quartile markers and overall mean/median
  references in both energy and time panels.
- The approved `compare_energy_time.png` rendering explicitly retains its
  existing styling. `compare_time_by_category.png` now has each survey's
  own weighted overall mean (dashed) and median (dotted) in A/B. As
  confirmed by the user, C shows the existing roster-based overall mean
  only, without an invented median. CSV reference rows distinguish means
  from medians. No estimator or production default changed.
- Eleven focused regressions passed (92.69 s); changed-file Ruff passed.
  The strengthened production-title/all-category rendering rerun passed
  (3 tests, 96.54 s); final comparison/reference/call-wiring checks passed
  (4 tests, 5.62 s), including legend clearance above plotted values.
  Rendering checks cover all 18 survey figures for each survey on populated
  synthetic data, preserving artist styles and checking title bounds,
  title/subtitle separation and absence of layout warnings. Comparison
  checks verify visible reference lines and exact CSV values.
- Synthetic full-size previews and a local HTML gallery are saved in the
  session's `files/figure-restoration-preview/` directory. No real-data
  report or full suite was run; existing generated reports are untouched.

### Step 11 figure readability correction (2026-11-07)

- The F04 and comparison figures preserve their designed multi-panel size.
  F04 uses the same mode categories and y-scale in its energy and time panels;
  redundant automatic values and comparison annotations no longer crowd the
  plots, while figure CSV values remain available.
- The focused figure regressions passed (5); changed-file Ruff passed. No
  real-data report or full test suite was run.

### Step 11/12 figure finishing (2026-11-07)

- The hand-written ENTD 2008 data page now states the observed cross-survey
  coverage comparison and the `daytable` caveat requested for its tables.
- Weighted day p25, median and p75 now come from the same functions as the
  means; tables, figure quartile bars, and figure CSV sidecars use those
  shared values. Focused statistics, comparison figure/export and report
  tests: 31 passed; changed-file Ruff passed.

### Step 11 figure finishing: gamma-fit handling (2026-11-07)

- A zero weighted variance now skips the method-of-moments gamma fit with a
  `RuntimeWarning`; the report labels the fit as skipped instead of failing.
- The ENTD CLI fixture varies durations and adds round-trip legs for both a
  car-passenger day and a cycling day, so the reference-scope energy fit has
  realistic spread and calibration inputs.
- Gamma unit tests passed (2); the ENTD 2008 CLI reached its figures and
  passed (1, 93.54 s). The full comparison CLI exceeded the 120-second test
  limit and was stopped; its CLI argument-routing test and existing focused
  comparison-figure tests remain the bounded checks. No report command or
  full test suite was run.

### Step 12 test runtime (2026-11-07)

- The step-12 CLI test now isolates argument forwarding and report-output
  orchestration; report rendering and figure/CSV exports remain covered by
  their focused tests. One bootstrap replicate is used in the CLI smoke test;
  production defaults are unchanged.
- The new CLI smoke test and scope CLI test passed in 2.00 s; changed-file
  Ruff passed. The former data-pipeline CLI test did not meet the 10-second
  target even with a one-replicate sample, so it was replaced rather than
  run as a long integration test. No full test suite or real-data report ran.

### Step 11/12: report fixes, 4 of 4 (2026-11-07)

- Scope words now appear in the report title and scope line, not every
  heading or figure caption. Figures retain their own scope subtitles.
  C5 and C7 headings continue naming their different/multiple scopes.
- What each rule removes now starts with one all-mode/all-category share
  table per survey, followed by one population-category table with all
  modes combined. These use the existing aggregate bootstrap cells, not
  averages of subgroup shares.
- Complete mode/category rule detail and `activity_5/15/30` rows go to
  `<report>_scope_rules_<scope-id>.csv` beside the step-12 Markdown report,
  with full-precision values and separate confidence-limit columns.
- Walking/cycling diagnostics retain walk, cycle and all-modes rows.
  A return-leg count column attributes every mode's dropped return to the
  preceding walk/cycle activity, instead of printing other-mode zero rows.
- Nineteen focused synthetic tests passed, including the full synthetic
  step-12 CLI and SQL scope diagnostics (101.94 seconds for the selected
  run); changed-file Ruff and signature compatibility checks passed.
  The final repository-wide Ruff check reports four pre-existing findings
  in `docs/article/figures/fig_long_run.py` (I001 and three E501); that
  unrelated article figure was left unchanged.
  Pylance found no errors in the changed scope/report helpers. Full
  real-data report runs were not performed.
- A coupled energy-sample regression also confirms that DuckDB NULL masks
  are excluded, rather than treating their underlying array values as
  energy-known observations in comparison figure ratios.
- Four code fixes are committed separately. The generated ENTD data-page line
  remains the one blocked sub-item described under fix 3. No generated
  outputs were edited, and no long job or download was started.
- Regenerate the four reference-scope reports in the user's terminal:
  `uv run python -m mobgrid.budget.emp --out docs\data\step11_budget`
  `uv run python -m mobgrid.budget.emp --survey entd2008 --out docs\data\step11_budget_entd2008`
  `uv run python -m mobgrid.budget.emp --compare --out docs\data\step11_compare`
  `uv run python -m mobgrid.budget.variation_report --out docs\data\step12_variation --entd2008-zoning-data-path data\raw\entd2008\ENTD2008_avec_zonages_EMP`
  Add `--scope all` to each command to regenerate all eight scope variants.

### Step 11/12: report fixes, 3 of 4 (2026-11-07)

- Day-table scopes now print 2019/2008 ratios in the comparison, B2,
  C6 and C7 instead of suppressing them based on documentation wording.
  The shared note follows the temporal/C7 tables and the coverage table:
  "The ENTD 2008 documentation does not guarantee coverage beyond 80 km;
  observed coverage is similar (Scope section)."
- This follows section 9.9's empirical coverage check, supplied in the
  request: non-local rows on 3.6%/3.2% of person-weekdays (ENTD/EMP),
  0.079/0.073 trips/day and 7.1/8.0 minutes/day.
- Thirteen focused synthetic tests and changed-file Ruff passed. No
  generated reports or real-data report computations were run.
- Blocked sub-item: no producer/template for `docs/data/entd2008.md` was
  found in the repository; it is an existing data-description page, not
  emitted by the report CLIs. Following the code-only instruction, that
  generated-output line was not edited and no output-text patcher added.
- Next: fix 4, heading placement and compact scope diagnostic tables.

### Step 11/12: report fixes, 2 of 4 (2026-11-07)

- Survey registration now applies the same residents-aged-6+ universe to
  both surveys' respondent and trip views, before every scope switch.
  This also covers diagnostic, per-person and C7 rosters, without an
  SDES-only age branch. Unfiltered views remain available for age audits.
- Both survey reports, the comparison and step 12 now print age-exclusion
  counts under Choices made, separating under-6 and missing-age respondents.
- A read-only count of the cached respondent CSVs (not a report run)
  confirms ENTD: 18,632 before, 18,542 after; all 90 exclusions are ages
  under 6, zero missing ages. EMP: 13,825 before and after, zero under-6
  or missing-age exclusions. There is no unexplained remainder.
- Two synthetic SQL acceptance tests cover both age tables, age exactly
  six, children below six, missing ages and unmatched demographics.
  Eleven focused synthetic tests passed; changed-file Ruff and scope
  Pylance diagnostics passed. No generated data pages edited or real-data
  reports run.
- Next: fix 3, report day-table ratios with the coverage caveat.

### Step 11/12: report fixes, 1 of 4 (2026-11-07)

- B2, C7, the comparison tables and figure annotations use the shared
  `daily_energy.bootstrap_ratio_ci`: independent household draws within
  each survey, one report seed, 200 replicates by default, 90% percentile
  intervals. Per-person and minutes/trip denominators use the same helper;
  the duplicate C7 and figure-bootstrap implementations were removed.
- Time and trip summaries include all in-scope days with trips, including
  those without an energy estimate. Energy tables retain energy-known
  days and their sample counts. Figure CSV ratios retain full precision
  rather than being reconstructed from rounded annotation text.
- Synthetic regression tests compare identical point estimates and
  intervals across B2, C7, comparison and a figure CSV, and across
  per-person comparison/C7/figure inputs. No generated data pages edited.
- Validation uses the existing `.venv` Python because `uv` is not on PATH.
  Nine focused synthetic tests passed; changed-file Ruff and signature
  compatibility checks passed.
  An initial dictionary-registered DuckDB test fixture required optional
  pandas; native SQL fixtures avoid that unnecessary dependency. No
  packages were downloaded, and no real-data reports or full test suite
  run. Next: fix 2, apply and audit ages 6+ in every scope.

### Step 11/12: report figure styling and exports (2026-11-06)

- Added a shared figure style/export helper and routed step-11 survey,
  comparison, and step-12 figures through it for fixed-width 200-dpi PNGs
  and same-stem CSV sidecars. Comparison mode charts now include all table
  mode groups, table-derived overall reference lines, time confidence
  intervals, and bootstrap ratio annotations.
- Focused figure/export tests: 3 passed; targeted Ruff passed. The synthetic
  step-12 CLI sidecar test passed (1 test; 55.8 s). No real-data reports or
  full test suite were run. ENTD/compare synthetic CLIs remain blocked before
  plotting by the existing zero-variance gamma fit.
- Remaining:
  - Add per-day quartile bars and `p25`/`p75` CSV values.
  - Synthetic ENTD and comparison CLI tests stop before plotting on the
    zero-variance gamma fit.
  - The synthetic step-12 CLI test takes 55.8 s.

### Step 11/12: scope module (2026-11-06)

- Added the three-switch scope ids and labels and full-day trip/day flags;
  destination activity flags use the supplied stay threshold and propagate
  to the next return home. The A3 person estimator now subtracts open-day
  weights in point estimates and household-bootstrap replicates.
- Synthetic scope and estimator tests: 33 passed; targeted Ruff and Pylance
  signature compatibility checks passed. No real-data reports were run.
- Step b is complete: the EMP 2019, ENTD 2008, comparison and step-12 CLIs
  accept `--scope` (reference by default) and `--scope all`; the eight runs
  are isolated under `scopes/<id>/`. General trip/day analyses use the
  selected scope; C5 remains on the SDES scope, and C7 compares the reference,
  SDES and day-table scopes. The retired needs scope and its dedicated
  filters were removed. Focused synthetic scope/report tests: 40 passed;
  targeted Ruff passed. No real-data reports or full test suite were run.
- Step c is complete: Markdown table headings and figure captions carry the
  selected scope words; step 12's Choices made names the selected scope,
  C5's fixed SDES scope, and the three C7 scopes. The report pipelines emit
  Markdown and PNGs, not CSVs, so there were no report CSVs to add a scope
  column to. Focused synthetic report tests: 5 passed; targeted Ruff passed.
- Step d is complete: the step-12 report begins with weekday Scope
  diagnostics for open days, walking/cycling activity and stay durations,
  sequential rule drops, and day-table coverage, split by survey and
  population category. Household-bootstrap 95% intervals are reported;
  negative point cells remain non-estimable and invalid draws are counted.
  ENTD 2008 day-table results are marked partial coverage and cross-year
  ratios are suppressed; unavailable away-from-home flags are reported as
  not recorded. Four focused synthetic tests and targeted Ruff checks
  passed. No real-data reports or full test suite were run.
- Follow-up: fixed a comparison-report variable-shadowing bug that caused
  `--compare` to fail when formatting the temporal section. Added a synthetic
  regression test around `run_compare`; two focused tests and targeted Ruff
  checks passed.
- Follow-up: scope diagnostics now normalise category-map person ids to
  text before looking up the text roster ids. Numeric ids previously
  misclassified the roster as unknown and caused bootstrap category
  `KeyError`s. Regression tests cover numeric and text ids in both surveys;
  six focused tests and targeted Ruff checks passed. No real-data run.
- Neither survey's documented immobility reasons identify a comparable
  away-from-home category. Count days without trips as zero in both surveys;
  do not use voyage dates. Verify and report any survey-specific away
  reason separately in the coverage diagnostic.

### Step 11/12: three-switch scope frame (2026-11-06)

- The described-day chain is every `K_DEPLOC` row for the person and day,
  including non-local rows; the voyage module is not joined to that chain.
  The all-distance setting is renamed `daytable` and does not mean total
  mobility. The later decision rules out using voyage dates.
- Section 9.9 was subsequently updated. EMP's public voyage table has
  weekday and month rather than complete voyage dates; ENTD's voyage
  dictionary lists start and end days, but its `K_VOYAGE` input is absent.
  ENTD's documentation defines a local-mobility field and does not establish
  systematic coverage beyond 80 km. Details are in the survey data pages.
- Both dictionaries identify departure and arrival times: EMP `MORIHDEP` /
  `MDESHARR`, ENTD `V2_MORIHDEP` / `V2_MDESHARR`.
- At this point implementation had not yet begun; see the scope module
  entry above for the current status.

_Last updated: 2026-11-06 by Copilot (three-switch scope data-coverage open point)_

### Step 12: C7 budgets and C8 compensation (2026-11-04, branch `step/variation`)

- C7 adds weekday, Saturday, Sunday and 7-day EMP estimates per person and
  per traveller for SDES, needs and all-trips sensitivity scopes, with
  household-bootstrap 2019/2008 ratios, 90% intervals and ±10%/±15% verdicts.
  ENTD 2008 is weekday-only: weekend selector and weight checks failed.
- C8b relates complete EMP weekday-out flags to local needs-scope intensity
  and compares category × density CVs. C8a is deferred because ENTD weekend
  weights are not validated; C8c is unavailable because EMP records no
  teleworking/working-from-home variable.
- Validation: 58 tests passed in `test_variation_report.py`; targeted Ruff
  check and format passed. No national report or data job was run. The local
  scope trip/minute reductions still need values from report regeneration.
- Regenerate the step-11 reports, comparison and step-12 report:
  `uv run python -m mobgrid.budget.emp --out docs\data\step11_budget`
  `uv run python -m mobgrid.budget.emp --survey entd2008 --out docs\data\step11_budget_entd2008`
  `uv run python -m mobgrid.budget.emp --compare --out docs\data\step11_compare`
  `uv run python -m mobgrid.budget.variation_report --out docs\data\step12_variation --entd2008-zoning-data-path data\raw\entd2008\ENTD2008_avec_zonages_EMP`

### B0: step-11/12 estimate corrections

- ENTD 2008's weekday per-person estimator now uses its full Kish-roster
  weight without an extra divisor of five, matching the temporal-ratio
  estimator. The step-11 per-person comparison now reports the corrected
  values, and equivalence verdicts distinguish equivalent, different and
  inconclusive intervals.
- C5 reports EMP's 7-day trip count as a weekly total and compares it with
  SDES's weekly reference. The checked-in row was rescaled from the prior
  rounded daily value and interval; regenerate the report for full-precision
  values and confidence limits.
- Validation: 2 focused `test_emp.py` tests, the synthetic step-11 report
  test and the focused C5 test passed (4 total); targeted Ruff passed.
  The synthetic report test emitted existing empty-legend warnings. No
  national-data jobs were run.
- Regenerate exact report values in the user's terminal:
  `uv run python -m mobgrid.budget.emp --compare --out docs\data\step11_compare`
  `uv run python -m mobgrid.budget.variation_report --out docs\data\step12_variation --entd2008-zoning-data-path data\raw\entd2008\ENTD2008_avec_zonages_EMP`

### Step 11/12: producer per-person estimators (A3)

- Step 11 weekday and 7-day per-person time budgets now use direct
  producer-weighted sums of local, needs-scope day totals over the full
  respondent roster; EMP uses divisors 5/7, ENTD uses full-roster
  `POIDS_JOUR`. Household-bootstrap CIs cover weekday and 7-day values.
- Both step-11 reports describe the weighted share of weekday out-days with
  zero local trips. Step 12 C5 now checks each supplied SDES trip/person,
  minutes/trip and km/trip reference and reports percentage gaps, including
  EMP's weekday and 7-day values; its diagnostic is age 6+.
- Validation: 23 `test_daily_energy.py`, 2 focused `test_emp.py`, 15
  `test_emp2019.py`, 21 `test_entd2008.py`, and 51
  `test_variation_report.py` tests passed; targeted Ruff passed. The full
  `test_emp.py` module exceeded the 2-minute job limit and was stopped.
- No real-data report or generated output was changed. Regenerate in the
  user's terminal:
  `uv run python -m mobgrid.budget.emp --out docs\data\step11_budget`
  `uv run python -m mobgrid.budget.emp --survey entd2008 --out docs\data\step11_budget_entd2008`
  `uv run python -m mobgrid.budget.emp --compare --out docs\data\step11_compare`
  `uv run python -m mobgrid.budget.variation_report --out docs\data\step12_variation --entd2008-zoning-data-path data\raw\entd2008\ENTD2008_avec_zonages_EMP`

### Step 12: final-prompt follow-up (2026-11-03)

- Fixed B2 ratio-table column alignment and changed equivalence results to
  equivalent/different/inconclusive; B7a now uses unscaled crow-fly B2 terms
  and a non-additive residual.
- Added C5 official-scope indicators from weekday local trips, age 6+, all
  motives, using the existing person-budget household bootstrap.
- Validation: 39 tests passed in `test_variation_report.py`; Ruff passed.
- Outstanding: C4 measurement ledger and the ten article CSV exports are
  not implemented. No real-data report or generated outputs were changed.

### Step 12: final 2008 -> 2019 comparison (2026-11-03)

- B2 and the B7a waterfall now use raw crow-fly distances for both surveys.
  The B2 sensitivity table keeps step-11 corrected distances and identifies
  the ENTD and EMP measures separately; within-EMP comparisons retain their
  step-11 corrected distances.
- C2 now compares only crow-fly distances. The Choices made section notes
  EMP 2019 declared-distance unit/coding errors. C3 warns that the unemployed
  and other-inactive professional/home-study shifts reflect motive coding.
- Added 2019/2008 daily-time ratios, 90% household-bootstrap CIs, and the
  configured ±15%/±10% equivalence verdicts to cross-year B2 rows and B6.5.
- Validation: 36 passed in `test_variation_report.py`; Ruff check and format
  checks passed. No other tests or real-data report runs were performed.
- Regenerate the report in the user's terminal with:
  `uv run python -m mobgrid.budget.variation_report --out docs\data\step12_variation --entd2008-zoning-data-path data\raw\entd2008\ENTD2008_avec_zonages_EMP`
- Existing generated report/figure changes remain uncommitted and untouched.

### Step 12: motive and density-grid consistency (2026-11-03)

- The main comparison now applies ENTD 2008's raw return-home reassignment
  (`MMOTIFDES`/`MOTPREC`) to EMP 2019 too. It drives both needs scope and
  motive groups; EMP's `MOT_SEQ_COMPL` remains a separate C3 sensitivity table.
- Added the SDES 2020-zoning joins for ENTD 2008. The zoning-variable
  inventory is in `docs/data/entd2008.md`; the supplement has no commune-code
  columns, so existing crow-fly distances are unchanged.
- Residence density grids join for every household. Of 132,880 trip keys,
  624 origin and 583 destination density codes are missing/invalid; the
  shared trip-leg grid fallback remains `intermediate`.
- Added B6.5: 2008 -> 2019 trips/day and minutes/day by residence density-grid
  class and population category.
- Validation: 71 passed in the three touched budget test modules; Ruff
  check/format clean. No full test suite or real-data report run.
- Regenerate the report with:
  `uv run python -m mobgrid.budget.variation_report --out docs\data\step12_variation --entd2008-zoning-data-path data\raw\entd2008\ENTD2008_avec_zonages_EMP`
- The pre-existing uncommitted report and figure changes are preserved.

### Step 12: C. Measurement checks (2026-11-03, branch `step/variation`)

- Added section C to `mobgrid.budget.variation_report`, configured by
  `config/variation.yaml` (pydantic-validated). A/B calculations and
  step-11 outputs are unchanged.
- C1 transfers EMP 2019's day-weighted cumulative rounding shares to
  ENTD 2008 within mode x original duration class. Levels are 1, 5, 15
  and 30 min, with sequential gap/eligible-share coarsening probabilities.
  Twenty seeded draws of nearest, up and nearest-with-5-min-minimum
  report mean/range of changes in minutes per day with trips, overall
  and by category, plus achieved cell shares alongside 2019 targets.
  Choices: nearest ties upward; cells never change after rounding;
  no refinement or pooling of empty target cells; the minimum applies
  to newly rounded values only. Zero, if produced, is a multiple of 30.
  Existing shares above target cannot be reduced and are left as-is;
  achieved shares expose overshoots and stochastic sampling variation.
- C2 reruns B2 (the existing `decompose()` household bootstrap), B4b's
  distance-band shift-share and duration distributions for raw declared
  distances (`V2_MDISTTOT`, never `distcor`; `MDISTTOT_decl`) and computed
  crow-fly distances (`V2_DVO_LOC`; `dVO_ORIDES`), without speed correction.
  Added known km per person-day, overall/by category with 95% CIs.
  All days/trips stay in N/T and the denominator; unknown distances
  remain unknown, with coverage/selection and an unknown-distance band.
  Known-km totals are explicitly lower bounds when distances are missing.
- C3 reports motive-group x category trip rates (zero-motive days kept),
  plus trips strictly under 5 min and under 1 km crow-fly per day, in
  each year and their difference, all with independent household-bootstrap
  95% CIs. Missing crow-fly distances never count as short; no imputation.
  This uses the existing needs scope and return-home motive reassignment.
- Validation: 43 passed, 0 failed in the two touched test modules only;
  Ruff check/format clean for the four changed Python files; Pylance
  syntax/diagnostics clean and all six `_format_b2` callers compatible.
  The synthetic CLI test checks that section C and the existing B7
  figures are generated. Additional tests cover fixed cells, class
  boundaries, weighted rounding probabilities, all variants, 20-draw
  ranges/target convergence/reproducibility, exact raw-field provenance,
  missing-distance aggregation and zero-inclusive household-bootstrap CIs.
  Used `.venv\Scripts\python.exe` because `uv` is unavailable.
- No other reports were opened; no real-data job was run. The existing
  uncommitted `docs/data/step12_variation.md` and figure directory are
  preserved and excluded from this task's commit. Regeneration is still
  needed to populate section C with real-data results:
  `uv run python -m mobgrid.budget.variation_report --out docs\data\step12_variation`.

### Step 12: report corrections (2026-11-03, branch `step/variation`)

- Fixed B2/B6 and B3/B4 km/speed calculations: N and T retain all
  trips; L and v use only finite-distance trips, with weighted coverage
  per comparison group. Person-day aggregation carries known-distance
  counts and minutes through the household bootstrap, including days
  with no known distance. An explicit selection residual preserves
  additive decompositions without mislabelling selection as speed.
  Unavailable B2 decompositions now include their reason.
- Missing distances have their own band instead of contaminating
  >=80 km. Distance-band plots use numeric order. B4b adds weighted
  median minutes per trip for each band and weighted duration quartiles
  by mode within >=80 km, for both years; suppression is unchanged.
- A1 now controls for the described day's weekday in both regressions
  and bootstrap fits; unknown weekdays are excluded from regression only.
- A4 names the exact loader fields: EMP `DUREE`; ENTD numeric
  `v2_mduree`, falling back to `V2_DUREE`; neither loader recomputes
  arrival minus departure. **Open point:** the checked producer variable
  labels do not establish independently declared duration versus a
  producer-side clock difference. The report explicitly marks this
  unverified instead of inferring it from rounding or a few raw rows.
- B7a is generated again with valid B2 data; its caption explains the
  proportional allocation and the explicit allocation residual needed
  when the net change is zero.
- Validation: 33 passed, 0 failed in the two touched test modules;
  Ruff check/format clean for the four changed Python files. Used the
  existing `.venv` Python because `uv` is unavailable. The synthetic CLI
  test verified report generation and all three B7 figures. No other
  tests or real-data jobs ran; existing reports and step-11 outputs
  were not opened or changed;
  step-11 source inspection was limited to duration-field references.
- Regenerate in the user's terminal:
  `uv run python -m mobgrid.budget.variation_report --out docs\data\step12_variation`.
  Existing uncommitted report/figure changes are left untouched.

### Step 12: variation of daily travel time (2026-11-02, branch `step/variation`)

- **Part D done.** The 13 EMC² surveys and the Île-de-France EGT
  2018-2020 under `data/raw/emc2/` are inventoried in
  `docs/data/emc2_inventory.md`: files/formats, counts, fieldwork dates
  by COVID period (no described day under any lockdown/curfew),
  sector-sequencing summary (sectors run in parallel), survey design,
  variable availability, EGT/Cerema differences, step-11 mapping and
  blockers (no income in EMC²; the V16 standard dictionary `.xls` is
  unreadable with the current toolchain; EGT has crow-fly distances
  only). `data/raw/` stays git-ignored; counts only, no processing.
- **Parts A and B done** in `packages/mobgrid/budget/variation_report.py`
  (new CLI `python -m mobgrid.budget.variation_report`) plus pure
  primitives in `variation.py` (shift-share, composition reweighting
  with 30-respondent age-band merging, tails, household-bootstrap
  helpers). A1 recall lag (EMP `MDATE_delai`; ENTD lag =
  `MDATENQ2V` − `V2_DATESEMREF`, mostly 1, 3 over weekends), A2 motive
  crosswalk + needs-scope removal shares, A3 distance provenance and
  bands + 80-km check, A4 duration rounding, A5 calendar; B1 V1-V3
  (V3 falls back to V2 for 2008→2019: no car count in ENTD's four
  public tables), B2 trips×km×speed by category, B3 mode shift-share
  (within split into km/speed), B4 motive and distance-band
  shift-shares, B5 tails, B6 pairs 1-4 (lag-1 variant; EMP dense vs
  intermediate and q1 vs q5 within category; density×income and
  IdF×income tables), B7 figures (waterfall, shift-share bars, recall
  lag). Choices are listed in the report under "Choices made".
- **Not run on real data** (step-12 rule): `docs/data/step12_variation.md`
  is a placeholder with the generation command; a 2% household smoke run
  (`--sample-households 2`) validated the whole pipeline (~1.5 min).
- **Tests fast:** synthetic fixtures extended with the step-12 columns;
  all new tests use 3 bootstrap replicates and run in seconds; the
  synthetic `--compare` CLI test dropped from ~141 s to ~19 s
  (replicates 10→3, and `emp.run(make_figures=False)` for
  `run_compare`'s discarded sub-run figures — no output change).
- Validation: 29 tests in the touched modules passed (full budget
  package: 103 passed earlier in the session); Ruff check and format
  clean. The user runs the full suite and the real-data report.
- Next: run the real-data report, read the figures, then extend the
  same tests to the EMC²/EGT surveys using the Part D mapping.

### Step 12: travel-time variation handoff (2026-10-29, superseded)

- Implemented Part C equivalence summaries and true-n suppression fixes
  in the step-11 report path (committed 2026-11-02). The remaining
  parts were completed on 2026-11-02 (see above).

### Pause handoff (2026-10-29)

- **State:** branch `step/time-budget`, not merged. Last report commit: `93350305b36352af353248c953b0d4250cda88f5`; the subsequent handoff commit is the commit containing this note (`git log -1 -- docs/progress.md`), avoiding a self-referential hash. Not pushed: both push attempts failed because noninteractive GitHub authentication is unavailable. `uv` is unavailable in this session; checks used the existing `.venv` Python instead. Pytest: incomplete, stopped at the 110-second safety limit; final passed/failed counts unavailable (collection: 431 selected, 2 pilot tests deselected). Ruff: passed, 0 violations. The repository moved to `C:\work\phd_model` after the Windows account change; `C:\codes` is a read-only copy owned by the old account.
- **Decided:** the daily travel time budget per population category is the reference constant (27 October); terminal legs from declared walking and waiting times; energy computed in parallel; residence density from the household table; income quintiles of income per consumption unit, equal-sized within each survey.
- **To review before merging:** the regenerated reports (quintile sizes, the income gradient for retired and employed people, figure f10 and compare_time_by_category).
- **Decisions pending:** (a) income levels in the budget, for all categories or only employed and retired people; (b) the budget fixed at its 2019 level, or following the observed rise (about +6 min a day on weekdays between 2008 and 2019); (c) the tolerance for calling the budget constant (for example, a CV below 0.10 within a category).
- **Open points:** recalibrate the car walk defaults in config.car from the calibration table of spec 9.6; P_0 under declared legs against the 34.8 W in the config; a duration plausibility check for every mode; EMP 2019 short-walk distances (MDISTTOT_fin); ENTD 2008 weekend-day eligibility; the pre-existing calibration_pilot test failure; the matplotlib "no artists with labels" warnings in the test figures. The written report and the article must be revised: the main result changed from energy constant across modes to time constant within population categories.
- **Resume commands** (own terminal, from `C:\work\phd_model`): `uv run pytest -q -m "not pilot"`; `uv run ruff check .`; authenticate GitHub, then `git push origin step/time-budget`. Export: `C:\work\step11_bundle_v5.zip` (three reports, all their figure-directory files, and this progress file). No computation or report regeneration was started during this wrap-up.

### Step 11: regenerated report measurements (2026-10-29, section 9.9)

Sources: [EMP 2019 report](data/step11_budget.md), [ENTD 2008 report](data/step11_budget_entd2008.md), and [comparison](data/step11_compare.md). Reported shares are rounded to one decimal place, not claims of exact unrounded equality.

| Survey | q1 individual weight | q2 | q3 | q4 | q5 | Unknown income |
|---|---|---|---|---|---|---|
| EMP 2019 | 20.0% | 20.0% | 20.0% | 20.0% | 20.0% | 0 of 13,825 respondents; 0.0% individual weight; 0.0% day weight |
| ENTD 2008 | 20.0% | 20.0% | 20.0% | 20.0% | 20.0% | 0 of 18,632 respondents; 0.0% individual weight; 0.0% day weight |

ENTD 2008's missing-income audit reports zero missing household matches, zero blank income brackets, zero unparsed brackets and zero missing/zero consumption-unit counts. This resolves the earlier open question about the real release: the regenerated report finds no unknown-income respondents; no project-side imputation was added.

Income constancy of mean daily time **per day with trips**, within each population category (the reports' income constancy summary, not the separate weekday per-person budget). CV is across the included income classes; `-` means the report does not give a q5/q1 ratio, not a zero.

| Category | ENTD 2008 q5/q1 | ENTD 2008 CV | EMP 2019 q5/q1 | EMP 2019 CV |
|---|---|---|---|---|
| children_6_17 | 0.98 | 0.05 | 1.01 | 0.01 |
| employed | 1.28 | 0.09 | 1.20 | 0.07 |
| unemployed | 1.22 | 0.12 | - | 0.22 |
| retired | 1.40 | 0.11 | 1.27 | 0.09 |
| other_inactive | 1.09 | 0.04 | 0.92 | 0.11 |

P_0 calibrated with declared terminal legs (falling back to the spec defaults where missing): **ENTD 2008: 26.7 W**, implied flat speed 11.84 km/h, n=2,146; **EMP 2019: 28.4 W**, implied flat speed 12.23 km/h, n=727. Both are below the configured 34.8 W; configuration is unchanged. The comparison's weekday daily-time mean on days with trips rises from 68.6 to 74.7 minutes (+6.1 minutes, 95% CI [+3.5, +8.2]).

Wrap-up checks: all 38 Markdown figure references resolve; the three figure directories contain 42 files in total. No `spec_update_*.diff` files were present in this working repository's root, so none were deleted or committed. The initial worktree contained only the requested report/figure changes. Commits use the Copilot bot identity because this account has no configured Git author identity.

### Step 11: equal-sized income quintiles, missing-income audit, figure fixes (2026-10-28, branch `step/time-budget`, pushed, not merged)

- **Equal-sized income quintiles** (user-reported bug: EMP 2019's q1
  held 31M of day weight against q5's 87M; ENTD 2008's q1/q5 held 42M/
  63M). Root cause: `weighted_quintile_view_sql`'s deterministic
  `ORDER BY value_col` cumulative-weight cut moved a *whole* tied-value
  group across a cut point at once, whichever side its last row landed
  on -- lumpy, not 20% each, because both surveys' income value is
  highly discretized (EMP 2019's `decile_rev_uc`: only 10 distinct
  values; ENTD 2008's bracket-midpoint/`NBUC`: repeats whenever two
  households share a bracket and consumption-unit count). Fixed with
  `trip_legs.build_income_quintile_table` (replaces
  `weighted_quintile_view_sql`): a seeded `numpy` random tie-break
  (`np.random.default_rng(seed)`, default `seed=0`, reproducible across
  repeated calls on the same connection, e.g. the F8 sweep) orders rows
  *within* a tied value before the cumulative-weight cut, so a group
  straddling a cut point is split between the two quintiles in
  proportion to its weight, not moved as a block. Verified on a 2,000-
  row synthetic check with a 10-distinct-value income variable: quintile
  shares came out at 19.98-20.01% each (previously as lumpy as the
  user's real-data report). `respondent_income` is now a `TABLE` (built
  from a registered `pyarrow` table), not a `VIEW` (the cut is computed
  in Python, not pure SQL); `income_quintile_summary`/
  `income_quintile_cutpoints` are two small side tables
  (`trip_legs.income_quintile_summary` reads them back) giving the
  report its cut points (in `value_col`'s own unit: `decile_rev_uc`'s
  1-10 rank for EMP 2019, euros per consumption unit per month for ENTD
  2008) and each label's share of individual weight. New report section
  "Quintile shares and cut points" (both surveys): n, individual-weight
  share and day-weight share by label (`q1`-`q5`, `unknown`), plus the 4
  cut points.
- **Missing-income audit** (user-reported: `'unknown'` was empty in both
  surveys' real-data reports). Code-reviewed the full path from raw CSV
  to `income_quintile`: both surveys' `build_respondent_income` already
  use the full `K_INDIVIDU` respondent roster (EMP 2019: `k_individu`
  joined to `tcm_ind`/`tcm_men`, not restricted further; ENTD 2008:
  `k_individu` directly, the 18,632-respondent universe), and a `NULL`
  `value_col` is correctly labelled `'unknown'` (confirmed by this
  session's synthetic tests, which do exercise a blank bracket/decile).
  No code bug found that would silently drop a missing value. Two
  different explanations likely apply per survey, now stated explicitly
  in the report text rather than assumed: EMP 2019's `decile_rev_uc` is
  INSEE's own, *already fully imputed* decile (so an empty `'unknown'`
  row is the expected, correct consequence of that imputation, not
  evidence of a bug); ENTD 2008's `TrancheRevenuMensuel`/`NBUC` are read
  as published with no imputation on this project's side, so a non-zero
  `'unknown'` row there would be a genuine non-response, and a 0-n row
  would mean INSEE's own release already has none left -- *this specific
  question needs the user's real-data run to answer*, not assumed empty
  as a prior, uncommitted draft of this entry (28 October 2026,
  corrected above) had stated without having actually measured it.
- **F10 fixed**: the per-person cross markers (`PersonBudgetRow.budget_ci`)
  were plotted as a bare point (`ax.plot`, no error bars), even though
  the CI was already computed and shown in the report's own tables;
  switched to `ax.errorbar` with the same CI.
- **`compare_time_by_category.png` reworked** (user-reported: no CI, no
  median, one panel): three panels, mean with 95% CI and a median
  marker (panels A/B; no median for panel C, a per-person budget is a
  product, not a quantile of a raw distribution) -- (A) all days, day
  with trips (now with CI, via the new `population_time_stats`
  `ScalarGroupStats`, since `GroupStats` itself has no time CI); (B)
  weekday only, day with trips; (C) weekday only, per person (P(out) x
  T(out), `person_budget_weekday_population`, already computed for the
  text-only weekday comparison, now also plotted).

### Step 11: household income and time-parity figures (2026-10-27, branch `step/time-budget`, pushed, not merged)

Applied `spec_update_2026-10-27_income.diff` (`docs/spec/09_trip_legs_energy.md`
only), commit `dd363c2`: income per consumption unit alongside density
as a dimension tested for constancy; daily time split into trips/day x
minutes/trip; time given the same mean/median/CI treatment as energy.

**Income variables (section 9.9's "Income variables", `docs/data/
entd2008.md`):**

- EMP 2019 publishes no raw income bracket; `TCM_MEN.decile_rev_uc`
  (INSEE's own consolidated, fully-imputed decile of income per
  consumption unit, 0% missing in the real data) is used directly as
  the continuous rank.
- ENTD 2008's `Q_TCM_MENAGE.TrancheRevenuMensuel` (14 bracket labels)
  is parsed to its midpoint in euros (`entd2008.income_bracket_midpoint_eur`:
  interior brackets average their bounds, the bottom open bracket is
  half its upper bound, the top open bracket 1.5x its lower bound, spec
  9.9), divided by `NBUC` (already the modified-OECD consumption-unit
  count, verified identical formula to the spec's). Deliberately not
  the same as the table's own `REVUC`/`NIVIE`/`NIVIE10` ("simulated"
  income, checked to differ from bracket-midpoint/NBUC on 2,000 real
  households, only 11.9% match to within 1 EUR). Whether
  `TrancheRevenuMensuel`/`NBUC` are themselves ever missing in the real
  release was not independently verified in this session (28 October
  2026's audit added the report's own n/share-by-quintile table,
  `'unknown'` included, so the real run itself now answers this; see
  below).
- Quintiles (`'q1'` poorest to `'q5'` richest, `'unknown'` for missing)
  computed per survey with individual weights
  (`trip_legs.build_income_quintile_table`, a weighted-cumulative-share
  cut at 20/40/60/80% over the whole respondent roster, not per trip;
  28 October 2026: a seeded random tie-break now splits a value
  straddling a cut point between the two quintiles in proportion,
  replacing a deterministic `ORDER BY` cut that pushed whole blocks of
  weight into one quintile when `value_col` repeats, see below).
  New `trips_norm`/`trip_legs`/`day_summary` column `income_quintile`.

**New engines (`daily_energy.py`):**

- `ScalarGroupStats`/`bootstrap_scalar_group_stats`: mean+95% CI+median
  of one arbitrary scalar by group (time, trips/day, minutes/trip),
  giving time the same treatment `GroupStats` already gives energy,
  without changing `GroupStats` itself (used by every new time-with-CI
  table/figure).
- `PersonBudgetRow`/`person_budget_by_group`: the per-person budget
  (P(out) x T(out), days without trips included), weekday-only (both
  surveys) or all-week with `DAY_TYPE_WEIGHT` (EMP 2019 only, point
  estimate, no joint CI across day types) -- ported and generalised
  from the prior session's scratch script
  (`C:\codes\step11_bundle\time_budget_partA.py`), now a permanent,
  tested part of the pipeline (previously explicitly left out of Part
  B: "not yet done" above).
- `bootstrap_diff_ci`: 2008-2019 mean difference with its own bootstrap
  CI (independent resampling in each survey), used for the new
  weekday-only comparison.

**New `emp2019.py`/`entd2008.py` functions** (mirrors of the existing
`residence_density`/`non_traveler_summary` pattern, covering the *full*
respondent roster, not just those with a trip): `population_category_by_ident`,
`residence_density_by_ident`, `income_quintile_by_ident`,
`person_day_type_rows` (EMP 2019, ported from the scratch script) /
`person_weekday_rows` (ENTD 2008).

**Report additions (`emp.py`, both surveys):**

- Category x density time table gained a 95% CI column (`_format_category_key_table`,
  generalising the old `_format_category_density_table`); new,
  identically-formatted category x income quintile table and its own
  constancy summary (q5/q1, max/min, CV).
- Trips-per-day and minutes-per-trip by category x density, category x
  income, and density/income marginals, all with CI (section 9.9 point
  2's "daily time = trips/day x minutes/trip" split).
- Per-person budget (P0 2b): by category, and by category x density/
  income, weekday (both surveys) and all-week (EMP 2019 only).
- P0 under declared legs: already satisfied before this task (`run()`'s
  base case is always `terminal_legs='declared'`; the report text
  already names this explicitly) -- verified, no change needed.
- `--compare` gained a weekday-only 2008-2019 comparison (`_format_weekday_comparison`):
  daily time by category, per day with trips (with `bootstrap_diff_ci`)
  and per person (point difference, each side's own CI).

**New/reworked figures** (18 PNGs now, up from 14): F01b (trips/day by
category x density/income, CI), F01c (minutes/trip, same breakdowns);
F02 reworked into F02a (stacked by mode, overall, linear time axis) +
F02b (per-category panels, normalised) -- the same treatment F03a/F03b
give energy, replacing the old F02 (category-only KDE) and F02b
(category x density heatmap, folded into F05b below); F04b reworked to
F04a's layout (mean+95%CI+median by mode, one panel per category, not
just a plain n-labelled bar); F05b, a new 4-panel time heatmap (mode x
category, mode x density, category x density, category x income); F10,
one panel per category, mean time with CI by density/income quintile,
day-with-trips (circles) and per-person (crosses).

**Known scope reductions (documented, not oversights):** every new
income/density breakdown is needs-only scope (matching the existing
density tables, which were never duplicated for the "all trips"
variant either); the per-person budget's cross-survey comparison has no
joint bootstrap CI (point difference only, each side's own single-
survey CI shown) -- a joint CI would need both surveys' raw person/day
arrays available simultaneously, which `run()`'s per-survey return
value does not expose.

Full test suite: run after this entry (see below); `ruff check .`
clean. Real reports **not regenerated** (same policy as the previous
entry): exact commands given in the session's final report.

### Step 11: travel time budget as the reference (2026-10-27, branch `step/time-budget`, pushed, not merged)

Re-estimates section 9.9 with the daily travel time budget (one b_k per
population category) as the model's reference constant, replacing the
daily energy budget; energy is still computed, in parallel. Applied
`spec_update_2026-10-27_time_budget.diff` (10 files in `docs/spec/`,
commit `788da27`) first, not committed.

**Part A (code, both committed):**

- `trip_legs.build_trip_legs` gained `terminal_legs` (`'declared'`, the
  new default; `'declared_plus1'`; `'defaults'`, the former section
  9.4-9.7 model, the only variant `terminal_scale`'s x0.5/x1/x1.5 sweep
  still applies to): each trip's own declared walking
  (`MTEMPSMAP`/`V2_MTEMPSMAP`) and waiting (`MTPSATTENT`/
  `V2_MTPSATTENT`) minutes now replace the car/carpool/PT/bike
  terminal-leg defaults by default, falling back to them where missing
  (0.3-3% of trips, by mode); the bike P0/ride-time back-calculation
  uses the same selected value, not the fixed 2-min default. 7 new
  tests (`test_trip_legs.py`), 2 pre-existing tests re-pinned to the new
  default (intentional, documented). Commit `02d8dd2`.
- `home_density` (`daily_energy.create_day_summary`) now reads a new
  `trip_legs.residence_density` column, built from the household's own
  residence-commune density (EMP 2019: `TCM_MEN.DENSITECOM_RES` grid,
  `STATUTCOM_UU_RES` for the proxy; ENTD 2008: `Q_TCM_MENAGE.
  numcom_UUCat` mapped to the same C/B/I/R codes, crossed with `TU99`),
  not the density of the first trip departing from home -- defined for
  every respondent, including the ~2.6% of EMP 2019 respondents with no
  described day at all. Commit `3872c98`.
- Full test suite: 405 passed, 2 deselected (pilot); `ruff check .`
  clean, after each commit.

**Part A (scratch, not committed; `C:\codes\step11_bundle\`):**

- `time_budget_partA.py` / `time_budget_partA.md`: on the real EMP 2019
  (grid, proxy) and ENTD 2008 (proxy) data -- sample flows; daily time
  and trips/day by population category x density class, per day with
  trips and per person (days without trips included, EMP 2019 via
  `IMMODEP_A`-`G`'s weekday/Saturday/Sunday weighted budget, ENTD 2008
  via `V2_MOBILREF` on the reference weekday), both needs and all-trips
  scope; the constancy summary (dense/very_sparse, max/min, CV) for
  both the day-with-trips and per-person measures; the 2008-2019
  difference by category with a bootstrap interval (all day types
  combined, and weekdays only, both measures); the energy group table
  and F8 robustness over the terminal-legs variants; P0 calibrated
  under declared legs next to the configured 34.8 W (EMP 2019: 28.4 W;
  ENTD 2008: 26.7 W -- config unchanged); the section 9.6 calibration
  table (declared walk by density x `MSTATION` parking type, drivers
  and passengers, EMP 2019 grid); missing-declared-value shares.
- Headline: daily time is fairly flat by density within each category
  (max/min 1.06-1.26) and between years (overall 67.9 to 73.3 min); the
  across-main-mode-group energy ratio rises from 1.6-2.2 (former
  defaults) to 2.0-4.3 under declared legs -- energy is no longer
  stable the way Kolbl & Helbing's hypothesis held under the old,
  4x-too-long default car terminal legs.

**Part B (code, committed):**

- `daily_energy.POPULATION_CATEGORIES`: section 6.1's five categories,
  shared order.
- New figures F2 (daily time density by population category) and F2b
  (category x density heatmap of time, with n), the time-budget
  analogues of the former energy-only F3/F5; F3/F4/F5 (energy) kept, in
  parallel. New report sections: category x density time table and its
  constancy summary, in both the single-survey report and `--compare`
  (which also gains a time-by-category 2008-vs-2019 figure and table,
  and the constancy summary side by side).
- F8 robustness now explicitly sweeps `terminal_legs` (declared base
  case, declared_plus1, former defaults x0.5/x1/x1.5): fixed a latent
  bug this task's own Part A work exposed -- `terminal_scale` has no
  effect under the new `'declared'` default, so the pre-fix x0.5/x1.5
  rows had silently become duplicates of x1 the moment `terminal_legs`
  defaulted away from `'defaults'`.
- Updated stale report text referencing the old `home_density`/P0/
  declared-vs-modelled model. Full test suite: 405 passed (after Part
  A's commits) / tests/mobgrid/budget: 62 passed after Part B's commit;
  `ruff check .` clean. Commit `c0b8334`.

**Not yet done (by design, not an oversight):** the three real reports
(`docs/data/step11_budget.md`, `step11_budget_entd2008.md`,
`step11_compare.md`) are **not regenerated** in this session: that is a
multi-minute real-data run, which this project's own policy reserves
for the user's terminal, not the agent. Exact commands given in the
session's final report. The per-person budget's full `IMMODEP`
machinery (Part A's scratch script) was deliberately **not** ported
into the permanent `mobgrid.budget` report: the user's Part B figure/
table list does not ask for it, and the day-with-trips measure already
covers the explicitly requested figures; worth revisiting if the
per-person budget becomes a permanent deliverable.

### Step 11 reporting fixes (2026-10-22, branch `fix/step11-reporting`, pushed, not merged)

- Fixed, one commit each (full detail in `CHANGELOG.md`'s "2026-10-22 —
  step 11 fixes"): bike stop energy now costed at the P0 flat speed, not
  each trip's own ride speed (cycle-day mean energy -5.5% EMP 2019,
  -4.0% ENTD 2008); `declared_vs_modelled_walk_wait` no longer
  double-counts PT access walk onto car modes; the `**Sample:**` line
  replaced by an explicit, unit-consistent sample-flow table (true
  respondent counts: EMP 2019 13,825, ENTD 2008 18,632 via `k_individu`,
  not `q_tcm_individu`'s 49,283-row full household roster); the day-type
  mix now prints a share, not a raw weight; children-as-car-drivers'
  prose and table now use the same needs-only scope (50/140, not
  56/148); `F8_ROBUSTNESS_GROUPS`'s "six groups" comment/prose corrected
  to seven; `config/energy.yaml`'s P0 comment now cites the 727-trip
  reliable subset, not the 1,023-trip total.
- Applied `spec_update_2026-10-22_part5_stops.diff` (section 9.9/00
  summary: bike stops at the P0 flat speed; ENTD 2008 sample flow in
  consistent units) before the code changes.
- Regenerated all three reports and figures (EMP 2019 grid, ENTD 2008,
  the 2008-2019 comparison with the proxy); `pytest -q -m "not pilot"`:
  399 passed, 2 deselected; `ruff check .`: clean.
- New regression test:
  `test_emp2019.py::test_stop_energy_per_stop_is_the_same_regardless_of_declared_speed`.
- **Not yet done:** the ENTD 2008 Saturday/Sunday "days without trips"
  denominators (via `V2_MIMMOSAM`/`V2_MIMMODIM`) are plausible but
  unverified against an explicit per-respondent weekend-day-eligibility
  flag -- flagged, not asserted, in the sample-flow table (weekday-only
  figures are fully verified). The open points below (from the
  2026-10-20 merge) are unaffected and still open.

### Merge wrap-up (2026-10-22)

- **Merged into `main`:**
  - `step/mobgrid-budget-entd2008` (step 11, ENTD 2008 comparison and
    the bike-distance-correction fix): merge commit `faa7219`.
  - `docs/spec-9.9-update` (spec section 9's section 9.3/9.7/9.9 text
    updated to match the re-estimation's actual behaviour -- speed
    correction, P0 calibration and its 45 km/h guard, survey weights
    and the bootstrap CI, the merged train group, the EMP 2019 day
    selection and `IMMODEP` columns, and the "other" modes' missing
    energy formula; plus sections 00, 13, 15, 16): merge commit
    `8528a00`. Spec section 9 itself was updated across commits
    `571b034`, `53476df` and `7715d99` on that branch.
- Both branches, now fully contained in `main`, were deleted locally and
  on `origin`.
- Pre-merge checks (branch `step/mobgrid-budget-entd2008`): 398 passed,
  0 failed (`pytest -m "not pilot"`); of the repo's only 2 pilot-marked
  tests, 1 passed and 1 failed with the known pre-existing
  `tests/mobgrid/pt/test_calibration_pilot.py
  ::test_chosen_parameters_resolve_the_clear_cut_known_cases` failure
  (`AttributeError: 'dict' object has no attribute 'r_m'`, root cause
  commit `b7be54e`, unrelated to this work); `ruff check .` clean.
  Post-merge, `pytest -m "not pilot"` on `main` repeats the same 398
  passed / 0 failed.
- **Correction to the 2026-10-20 session handoff below:** its claim that
  "both pilot tests in `tests/mobgrid/budget/` pass on real data" was
  wrong -- there is no pilot-marked test in `tests/mobgrid/budget/` at
  all. Its one real-data check,
  `test_emp.py::test_real_emp_2019_mean_daily_energy_is_within_kh_order_of_magnitude`,
  is gated by `@pytest.mark.skipif(not _REAL_DATA_AVAILABLE, ...)`, not
  `@pytest.mark.pilot`; its module docstring wrongly claimed the
  latter and has been fixed. Since it is skipif-, not marker-gated, it
  already runs inside the default `-m "not pilot"` suite whenever the
  EMP 2019 archive is present, which is why it is already counted in
  the 398 passed above. The only `pilot`-marked tests in the whole repo
  are the 2 in `tests/mobgrid/pt/test_calibration_pilot.py`.
- **Open points from spec section 9.9, still open after this merge:**
  1. Walking v0: keep the configured 4.8 km/h, or adopt a survey-derived
     value (3.4-3.6 km/h door-to-door, both surveys) -- not decided
     (section 9.3).
  2. No mode has a duration plausibility check, and `urban_pt`/`train`
     have no speed check either (only walk, cycle and the three car
     groups are checked) -- section 9.9's own open-choices list now
     names this gap, not yet implemented.
  3. The EMP 2019 short-walk distances: 15.4% of walking trips are
     speed-flagged and distance-corrected (1,569 of 10,180), against
     1.7% in ENTD 2008 (467 of 27,429) -- a ninefold gap `[TO CONFIRM:
     how MDISTTOT_fin is computed for short walks]`, not investigated.
  4. EMP 2019 trips per person and day (and the share of days without
     trips) still need computing from `IMMODEP_A`-`IMMODEP_G` (plus the
     summary flag `IMMODEP_FLAG`) in `K_INDIVIDU`, crossed with the
     described day's trips -- not implemented yet (section 9.9, step 1).
  5. The pre-existing `test_calibration_pilot.py` failure (commit
     `b7be54e`, `GtfsRebuildConfig.chosen` now a per-mode-family dict,
     test still reads it as a single object) remains unfixed; out of
     scope for the budget/spec work merged here.

### Session handoff (2026-10-20, end of session; superseded above -- branch now merged into `main`, see "Merge wrap-up" above)

- **Branch:** `step/mobgrid-budget-entd2008`, pushed to `origin` with
  upstream tracking. Not merged.
- **PR:** not opened -- no issue/PR-creation tool or `gh` CLI was
  available in this environment (the GitHub MCP tools here are
  read-only for issues/PRs). GitHub's own compare link:
  https://github.com/vastuhlfauth/phd_model/pull/new/step/mobgrid-budget-entd2008
  -- the PR description (root cause, fix, before/after numbers, the new
  regression test, the regenerated reports, and the pre-existing
  `test_calibration_pilot.py` issue below) is ready, see the session's
  final chat summary or `CHANGELOG.md`.
- **Tests/lint:** 398 tests pass (`-m "not pilot"`). Correction (2026-10-22):
  there is no pilot-marked test in `tests/mobgrid/budget/` -- its one
  real-data check, `test_emp.py
  ::test_real_emp_2019_mean_daily_energy_is_within_kh_order_of_magnitude`,
  is gated by `@pytest.mark.skipif(not _REAL_DATA_AVAILABLE, ...)`, not
  `@pytest.mark.pilot` (its docstring wrongly claimed the latter; fixed
  in `tests/mobgrid/budget/test_emp.py`), so it already runs as part of
  the default (`-m "not pilot"`) suite above, not a separate pilot run.
  `ruff check .` is clean. `ruff format --check .` flags this branch's files, but also 46
  files repo-wide never touched this session -- the project's own
  validation command is `ruff check` (not `ruff format`), so this was
  not treated as a failure; not changed, to avoid an unrelated reformat
  of the whole repo.
- **Known pre-existing issue (not this branch, not fixed):**
  `tests/mobgrid/pt/test_calibration_pilot.py
  ::test_chosen_parameters_resolve_the_clear_cut_known_cases` fails with
  `AttributeError: 'dict' object has no attribute 'r_m'`; confirmed
  failing identically on `main` (scratch worktree, same local
  `calibration_run.pkl`/`osm_pt_stops` cache). Root cause: commit
  `b7be54e` changed `GtfsRebuildConfig.chosen` to a per-mode-family dict
  without updating this test. Full details in "Decisions taken while
  coding" below.
- **Open follow-ups for this step (not done this session):**
  1. The speed-plausibility check (`trip_legs.py`'s
     `speed_flagged_upper_sql`) has branches for `walk`, `cycle` and the
     three car groups only; `urban_pt`, `train` and `other` are **never
     flagged at all** (not just "flagged but uncorrected" like bike used
     to be -- there is no branch for them, so the check defaults to
     `FALSE`). PT/train's own energy formula has no distance term (it is
     duration x `ride_rate_kj_per_min`), so an implausible PT/train
     *distance* would not inflate energy the way bike's "stops" term
     did; but no mode has a *duration* plausibility check either, and an
     implausible duration would inflate `ride_rate_kj_per_min *
     duration_min` unchecked for PT/train. Worth checking both ENTD 2008
     and EMP 2019 for PT/train distance and duration outliers before
     deciding whether to extend the check.
  2. Find and update any downstream output that cites the pre-fix 2008
     numbers (1,642.6 kJ multimodal; 625.0/572.8 kJ overall; 47.5 W P0).
     None are known inside this repo as of this session (the three step
     11 reports and this progress file are already regenerated/updated);
     check anything external (drafts, slides, a thesis chapter) that may
     have copied the pre-fix `docs/data/step11_compare.md`/
     `step11_budget_entd2008.md` numbers before this session's fix.

### Notes moved from the steps table (2026-11-21)

| Step | Content | Status | Branch | Notes |
|---|---|---|---|---|
| 11 | `mobgrid/budget` | review | `step/mobgrid-budget-entd2008` | **Brought forward before steps 8-10** (needs only step 7 and the EMP 2019 public tables, not the graph/OD steps). Section 9.9's re-estimation steps 1-3 and 5 on EMP 2019's public tables (`K_DEPLOC`, `TCM_IND_KISH`, `K_INDIVIDU`; `TCM_IND`/`Q_MENAGE` acquired and checked but not needed by this step's formulas); EMC² (step 4) and Ē_c (step 6) are out of scope. `emp2019.py` rebuilds each of the 45,169 EMP 2019 trips (13,370 respondents, 455 reporting no trip) as legs, reusing `mobgrid.energy`'s public walk/bike/legs/rates formulas: terminal legs by density class (car: `config.car.*`, already calibrated for step 7; PT: provisional `config.pt_ride.headway_min_am_peak`/`station_height_m`/`access_walk_m_by_density`, TODO(confirm), since EMP has no headway/station-depth/access-distance data) and the main leg at the rest of the declared duration (`DUREE`); companions (`MACCOMPM`/`MACCOMPHM`) separate household from carpool car passengers. `daily_energy.py` sums to one row per respondent, classifies each day by its one non-walk mode, and computes weighted group means with a household bootstrap 95% CI (`bootstrap_group_stats`), a method-of-moments gamma fit (no new `scipy` dependency), and the v0/P0 calibration by age band. Checked the user-reported ~119 kJ train-chain discrepancy from step 7's `checks.py`: escalators (standing rate), not stairs, are already correctly used above the 10 m threshold (commit `cc9eb81`'s fix). Found and fixed a pre-existing `config.pt_ride.standing_share_am_peak` key mismatch (4 of `load_factor_max`'s 8 vehicle keys were missing). **Second round (after main's spec 6/9 update, "population categories, train and passenger splits"):** day-mode groups now keep household/carpool passengers and short (<80 km)/long train separate (no collapsing; `emp2019.TRAIN_LONG_THRESHOLD_KM`), "multimodal" and "other" (enumerated in the report) stay apart; population category follows section 6.1's five groups exactly (`SITUA`'s student code now folds into `other_inactive`, dropping the ad hoc sixth "student" group); density labels use the INSEE grid's own names/order (dense/intermediate/sparse/very_sparse; `emp2019._DENSITY_LABEL_BY_CODE`/`_DENSITY_KEY_TRANSLATION`), checked against the categories PDF. v0 and P0 are now ratio-of-weighted-sums estimators (not averages of per-trip speeds); P0 first subtracts bike get/park (new `config.bike.get_park_min`, 1 min each) and expected stop delays (new `config.bike.stops.stops_per_km`, both TODO(confirm)) from the declared duration, with an unreliable-adjustment fallback to the naive whole-duration speed below a minimum ride-time/fraction or above a plausibility speed cap (`emp2019._BIKE_MIN_RIDE_TIME_S`/`_BIKE_MIN_RIDE_FRACTION`/`_BIKE_MAX_PLAUSIBLE_SPEED_KMH`) for a handful of very short or implausibly fast cycling trips. `build_trip_legs` gained `terminal_scale`/`bike_p0_override_w` parameters and `create_day_summary` a `where_sql` filter, used by the new F8 robustness check (`daily_energy.robustness_row`/`RobustnessRow`): max/min ratio and CV of six groups' means, across both rate sets, terminal legs x0.5/x1/x1.5, P0 recalibrated vs the 52.5 W reference, weekdays-only vs all days, and local-trips-only (`MOBLOC=1`) vs all. Added a weighted Gaussian KDE on log-energy (`daily_energy.weighted_gaussian_kde`/`weighted_gaussian_bandwidth`, Silverman's rule, no `scipy`) for F3's stacked/overlaid density figures (overall and one per population category, Compendium, with a KH appendix). Investigated the non-traveller immobility share (reported low at 2.7%): identification is "no K_DEPLOC row for the day", which matches `K_INDIVIDU`'s own `MIMMOSEM` flag exactly for all 455 cases; EMP 2019's public tables record no day-of-week for a fully immobile respondent, so the figure is an inherently weekday-dominated estimate, not an all-week average (documented, not changed). Verification command `python -m mobgrid.budget.emp --out docs/data/step11_budget` (`emp.py`) now writes 11 PNGs (F1, F3 x4 incl. KH appendix, F4a/b, F5, F6, F7, F8) plus `docs/data/step11_budget.md`; run once, committed. On real EMP 2019 data (second round): overall weighted mean daily energy 684 kJ (KH) / 604 kJ (Compendium) against Koelbl & Helbing's 615 kJ hypothesis; calibrated v0 3.96 km/h (configured 4.8), P0 34.8 W at an implied flat speed of 13.55 km/h (reference 52.5 W at 16 km/h). **Third round (new `docs/spec/09_trip_legs_energy.md`, unloaded pedalling cost):** `emp2019.py`'s cycle-energy SQL formula gains the same unloaded-pedalling term as `mobgrid.energy.bike` (section 9.7, step 7 third round), on `bike_ride_time_for_energy_s` at the reference mass, both rate sets; P0 itself is unaffected (it is calibrated from implied speed via force-balance physics, not from energy/duration), still 34.8 W at 13.55 km/h. Added two tables to `step11_budget.md`: mean daily energy (both rate sets) and time, 95% CI and n, for every main-mode group, overall and one sub-table per population category (`emp._figure_f4_mean_by_mode` now also returns its per-panel stats, `_format_group_table_by_panel`); the F8 robustness table now also names each variant's min/max group (`daily_energy.RobustnessRow`/`robustness_row` gained `*_min_group`/`*_max_group` fields). Rerun on real EMP 2019 data: overall weighted mean daily energy 691.1 kJ (kh), 611.2 kJ (compendium); v0/P0 unchanged. Ruff clean; 18 budget tests pass (361 total, 3 pilot deselected). **Fourth round (bug fix and data-quality/robustness additions):** found and fixed the cycling-energy bug the user flagged (cycle-day energy at 1,295 kJ/69.6 min, ~18.6 kJ/min, above the population riding rate and with a tail to 10^4 kJ): `emp2019.py`'s energy formula derived each cycling trip's OWN power from its own (reliability-adjusted) implied speed -- correct for the aggregate v0/P0 calibration (a ratio of weighted sums), but wrong for per-trip energy, since power is convex in speed (drag's cubic term) and EMP's durations are rounded to 5/15/30/60 min, so averaging per-trip power over-estimates the population mean (the same Jensen's-inequality bias the ratio-of-sums estimator was built to avoid, reintroduced one level down). Fix: `build_trip_legs`'s cycling work term is now time-based at a single population-level power -- `bike_p0_override_w` if given, else `config.bike.power.p0_w` (34.8 W, EMP-confirmed) -- applied uniformly to every pedalled second (`bike_ride_time_for_energy_s`), matching how every other mode's rate is already a fixed, config-level constant, not a per-respondent recalibration; the per-trip `p0_calibrated_w` column is kept as a diagnostic only. Mean cycle-day energy dropped from 1,459 kJ to 1,020 kJ (median 735->706 kJ, max 21,761->6,747 kJ) on the unfiltered sample. Added a door-to-door speed-plausibility data-quality filter, all modes (walk 1.5-7 km/h, bike 5-35 km/h, car <=130 km/h; `emp2019.WALK_PLAUSIBLE_SPEED_KMH`/`CYCLE_PLAUSIBLE_SPEED_KMH`/`CAR_MAX_PLAUSIBLE_SPEED_KMH`, new `trip_legs.speed_plausible` column), with the main-mode group table reported both with and without flagged trips in `step11_budget.md` (25.8% of walk trips are flagged, mostly short, rounded-duration trips; 15.1% of cycle trips; 0% of car trips). Added weighted medians next to every mean in `GroupStats`/the group tables (`daily_energy._weighted_median`/`_weighted_group_medians`). Extended the F8 robustness table with a "core" scope (walk/driver/urban PT/train short) alongside the existing "full" six-group scope (`daily_energy.F8_CORE_ROBUSTNESS_GROUPS`, `RobustnessRow.scope`). Investigated "children as car drivers" (n=56 children_6_17 car_driver days): the raw `mtp` code is 3.1/3.3 ("Automobile" category, not a two-wheeler 2.x code), so no two-wheeler reclassification applies; most plausibly EMP's own household/accompanying-trip coding for the under-14 share, genuine voiturette/accompanied driving possible for the 14-17 share. F3's density figures now drop groups/panels with n < 50 trips and the 'unknown' population category (12 persons, also dropped from F1/F4/F5), and use a widened (x1.5) Silverman bandwidth; removed three stale first-round figure files (`f03_daily_energy_histogram.png`, `f04_mean_by_mode.png`, `f05_mean_by_age_density.png`). Rerun on real EMP 2019 data: overall weighted mean daily energy 682.1 kJ (kh), 602.3 kJ (compendium), closer to Koelbl & Helbing's 615 kJ than the buggy 691.1/611.2; v0/P0 calibration unaffected (still 34.8 W at 13.55 km/h, since it never used the per-trip power). Ruff clean; 19 budget tests pass (362 total, 3 pilot deselected). **Fifth round (leisure loops, correction instead of drop, decomposition, median robustness, every figure twice):** leisure-loop trips identified by EMP's own `MMOTIFDES` = 7.7 ("se promener sans destination precise"; no commune-level origin field exists in the public release for a geometric origin=destination check, so the purpose code is EMP's own operationalisation); `trip_legs.is_loop_trip`, reported as trip/day-energy shares by main-mode group and a loop-excluded group table (`create_day_summary`'s existing `where_sql`). The speed-quality filter is now upper-bound-only (walk > 7, bike > 35, car > 130 km/h; `emp2019.WALK_SPEED_UPPER_KMH`/`CYCLE_SPEED_UPPER_KMH`/`CAR_SPEED_UPPER_KMH`) and corrects flagged walk/car trips' declared distance to duration x the mode's own median speed (from its not-flagged trips, a window `median() FILTER` in `build_trip_legs`) instead of excluding them; bike is flagged but not corrected (its energy is already time-based). Added `emp._compute_cycle_decomposition` (ride work/unloaded/stops/get-park/same-day-walking, kJ and minutes, plus kJ/stop) to the report. `daily_energy.robustness_row`/`RobustnessRow` gained a `statistic` field (`"mean"`/`"median"`), so F8 now reports both for every variant and scope. F4a's bars now also show a diamond marker at each group's median. Every figure (F1-F8) is now produced twice per `emp._run_variant`, `"_all"`/`"_noloops"` (22 PNGs, replacing the single-pass set; `calibrate_v0_kmh`/`calibrate_p0` and `_run_robustness` gained a `where_sql`/`base_where_sql` filter for the `_noloops` pass). Ruff clean; 20 budget tests pass (363 total, 3 pilot deselected). **Sixth round (cycling energy by motive, user note "data for bike are still too large"):** decomposed cycling energy by `k_deploc.MOT_SEQ_COMPL` ("Motif corrige detaille de la sequence", EMP's own chain-level, corrected purpose -- unlike the raw, trip-level `MMOTIFDES` behind `is_loop_trip`, it excludes "return home" codes 1.1-1.3 since a return leg is recoded to its outward leg's purpose); new `trip_legs.motive` column (`emp2019.MOTIVE_LABEL_BY_CODE`, labels from the categories PDF's "Motif" table), `emp._compute_motive_decomposition`/`_format_motive_table` add a per-motive trip/energy-share table (sorted by weighted energy, largest first) plus a leisure-cycling rollup (`emp2019.LEISURE_CYCLING_MOTIVE_CODES` = 7.6 sport/7.7 loop/7.8 promenade-destination, per the user's own hunch) to `step11_budget.md`. Found: leisure cycling is 29.1% of weighted cycling trips but 46.9% of cycling's weighted energy (both rate sets, since cycling's own formula is almost entirely rate-set-invariant) -- the single largest identified driver of cycling's still-large mean energy, ahead of any remaining formula or data-quality issue. Ruff clean; 22 budget tests pass (365 total, 3 pilot deselected). **Seventh round (user confirmed the diagnosis; scope decision: "only interested in commuting and travelling for needs fulfilment"):** `emp2019.NEEDS_EXCLUDED_MOTIVE_CODES = (7.6, 7.7, 7.8)` and `NEEDS_ONLY_WHERE_SQL` (missing/refused motive kept, not excluded) are now the single base filter for every table and figure in the report -- not an optional variant; round 5's `_run_variant`/`_all`/`_noloops` figure-doubling mechanism is retired (back to one pass, one set of figures, per explicit user choice among three offered options). `_compute_cycle_decomposition` and the F8/v0/P0/passenger/carpool queries all now apply this same filter for consistency with `day_summary`'s own totals. A separate, final diagnostic pass on the full (unfiltered-by-motive) dataset keeps the motive-share evidence (now reported for every mode, not just cycling, via new `excluded_trip_shares`/`excluded_energy_shares`) and a few checks that must stay scope-independent (non-traveller share, data-quality corrections, children-as-car-drivers). New F9 figure: 100%-stacked bar of weighted KH energy by top-level motive (`emp2019.TOP_LEVEL_MOTIVE_LABEL_BY_CODE`), one bar per mode, full dataset -- confirms "leisure" is the largest or second-largest segment for cycle and walk. F4a gained two new per-panel "computed mean" reference lines (this panel's own weighted mean, kh and cp, alongside the fixed Koelbl & Helbing 615 kJ line), computed via new `emp._panel_overall_mean`. Investigated the user-reported "median below the CI interval, systematically": confirmed not a bug -- the bootstrap 95% CI is on the *mean*, which for samples in the hundreds/thousands is narrow, while every group's own distribution is right-skewed (a few long/expensive trips), so the median sits noticeably, and expectedly, below that narrow band; verified computationally (same underlying per-day values feed both estimators) rather than just asserted. Cycle group mean dropped 827 -> 632 kJ (median 607 -> 626, oddly close now); overall weighted mean dropped 587 kJ (kh) -- now *below* Koelbl & Helbing's 615 kJ, versus 682-691 kJ (overshooting) in earlier rounds. Figures: 12 total (F1, F3 x4 incl. KH appendix, F4a/b, F5, F6, F7, F8, F9), replacing round 5's 22 (`_all`/`_noloops` variants removed, F9 added); confirmed no stale files remain. Ruff clean; 22 budget tests pass (365 total, 3 pilot deselected). **Eighth round (final cleanup):** `train_short`/`train_long` (distance split at `TRAIN_LONG_THRESHOLD_KM` = 80 km) merged into a single `train` day-mode group across `emp2019.py` (classification CASE, both energy-formula CASE blocks), `daily_energy.DAY_MODE_GROUPS`/`F8_ROBUSTNESS_GROUPS`/`F8_CORE_ROBUSTNESS_GROUPS`, and every markdown string naming the split -- `train_long` had too few observations (n=39, vs train_short's 183) to be a meaningful separate group, and this removed a `TRAIN_LONG_THRESHOLD_KM` constant now dead. `emp2019.NEEDS_EXCLUDED_MOTIVE_CODES` extended from `(7.6, 7.7, 7.8)` to `(7.6, 7.7, 7.8, 8.1, 8.2, 8.3, 8.4)` (the whole of motive group 8 -- holidays, second/occasional residence, other private reasons -- none of them a needs-fulfilment destination), per explicit user confirmation; `_compute_motive_energy_matrix` gained a `where_sql` parameter so F9 can show both the full, pre-exclusion dataset (panel A, the evidence) and "the final decomposition" after the needs-only filter (panel B, confirms motive 8 disappears entirely and motive 7/leisure shrinks to its remaining 7.1-7.5 sub-codes, not to zero). F1 gained a 4th panel: a frequency heatmap of % of all weighted person-days by (population category x main-mode group), with "overall" marginal row/column (a genuine 2-way contingency table, not row-normalised), annotated with every cell's value. Cycle energy's needs-excluded share rose slightly to 47.8% (from 46.9%) once motive 8 was added; overall weighted mean daily energy is now 583.8 kJ (kh), 522.4 kJ (compendium). Ruff clean; 22 budget tests pass (365 total, 3 pilot deselected). **Ninth round (F1/F4a refinements):** F1's panel (D) now shows the weighted MEAN trips per day in each (population category x main-mode group) cell, not a % share of person-days -- the same quantity as panels (B)/(C), cross-tabulated (`_frequency_matrix` now computes `sum(weight * trips_per_day) / sum(weight)` per cell); the top-left "overall x overall" cell (3.3) matches panel (A)'s reported mean exactly, confirming consistency. F4a now prints each bar's mean value as rotated text above its CI whisker, and adds two more horizontal reference lines (dotted) for the "overall" median (kh/cp), each labelled with its numeric value, alongside the existing KH-615 and computed-mean lines. Confirmed (by code audit, no change needed) that every mean/median/CI/ratio computed in this module is weighted by `pond_jour` (the EMP day weight): `weighted_mean_variance`, `bootstrap_group_stats`, `bootstrap_mean_ci`, `_panel_overall_stats`, `_frequency_matrix`, the v0/P0 ratio-of-weighted-sums estimators, the robustness rows, and every SQL aggregate (`sum(pond_jour * ...)`); the one unweighted `.mean()`/`.std()` in `daily_energy.py` (robustness CV) operates on the array of already-weighted group means, not on raw trip/day data. Ruff clean; 22 budget tests pass. **Tenth round (F1 motive stacking, F4a line labels):** F1 panels (B)/(C) are now stacked bars, one segment per top-level motive (`_trips_by_group_and_motive`, same `NEEDS_ONLY_WHERE_SQL` scope as every other table/figure, a "not recorded" sentinel for the small share of trips with a missing/refused motive), each group's total bar height and 95% CI unchanged from before (segments sum to the previous single-colour bar). Investigated the user-flagged "employed x cycle (3.8) > overall x cycle (3.3), not possible": confirmed by a direct query this is a correct weighted average, not a bug -- employed is only 49.1% of weighted cycling person-days (children 21.4%, retired 16.8%, other_inactive 7.2%, unemployed 5.4%), and the other five categories' lower cycling rates (2.7-3.0 trips/day) pull the pooled "overall" below employed's own rate (0.491x3.764 + ... = 3.31, matching the reported 3.3); added a caption note to F1 panel (D) explaining this. F4a's mean-value bar labels moved from the CI-whisker tip to the bar top and lost their 90-degree rotation (horizontal, as asked); every reference line (Koelbl & Helbing 615 kJ, the panel's own computed mean, the overall median, both rate sets) now prints its value via the y-axis transform (x in axes fraction, y in data units), keeping every label inside the plot regardless of panel width. Ruff clean; 22 budget tests pass. **Eleventh round (ENTD 2008 comparison, `step/mobgrid-budget-entd2008`):** fix 0: `_run_robustness` rebuilt `trip_legs` for each F8 variant but never restored the base case (calibrated P0, `terminal_scale=1`) after its last variant (P0=52.5 W reference); every post-sweep computation (F3-F5, F9, the cycle decomposition) silently reused that mutated `trip_legs`, so F4's "overall" panel disagreed with the main group table for cycle (777.6 vs 631.0 kJ kh) and multimodal (767.1 vs 754.6) despite identical n — F4 was the wrong one; fixed by rebuilding the base-case `trip_legs` as `_run_robustness`'s last step. Refactor (point 1): `emp2019.build_trip_legs` split into a survey-specific `trips_norm` view (`emp2019.build_trips_norm`, EMP's own raw-table joins) and the shared energy SQL (new `mobgrid.budget.trip_legs.build_trip_legs`, reading `trips_norm` onward: mode/vehicle classification, density resolution, the speed-quality correction, section 9 formulas) — survey-agnostic, so ENTD 2008 reuses it unchanged; `day_summary` now groups by `trip_legs.day_id` (EMP 2019's `IDENT_IND`, one day per person; ENTD 2008's `IDENT_JOUR`, up to three days per person), not `ident_ind`, with every `ident_ind`-keyed join in `emp.py` updated to `day_id`. Added `TCM_MEN.TUU2017_RES` to EMP 2019 (comma-quoted dialect, unlike every other EMP table but `k_deploc`: a real-data surprise caught by the pilot test, not the synthetic fixture) and `STATUTCOM_UU_ORI`/`_DES` (`H`->`R`), `MTEMPSMAP`/`MTPSATTENT` to `trips_norm`, feeding section 9.9's density proxy (`trip_legs.density_proxy_case_sql`: trip-end urban-unit status x residence-size class, `--density grid|proxy`, ENTD 2008 always proxy) and a new "declared vs modelled walk/wait minutes by mode group" report table/section. Regression test (`test_refactor_preserves_emp2019_base_case_group_table`) pins the synthetic fixture's base-case group table before/after the split (also fixed a latent synthetic-fixture bug: the only walk/cycle trips were needs-excluded, crashing v0/P0 calibration — added two needs-only-scoped respondents). New `packages/mobgrid/budget/entd2008.py`: re-encodes the four public CSVs (cp1252->UTF-8, `data/interim/entd2008/csv`, code columns forced VARCHAR); `V2_MTP`/`V2_MMOTIFDES`/`V2_MMOTIFORI` conversion tables and the sequence-purpose rule (a return trip, raw purpose 1.1-1.3, takes its own `V2_MMOTIFORI`-converted purpose, since each `k_deploc` row already carries the previous trip's purpose); `POIDS_JOUR > 0` filter; `V2_MOBILREF = 0` non-traveller check (reference weekday only); `quirk_fill_rates` (on the real archive: `distcor` 0.23% filled, mean change +0.67 km where filled; `v2_mduree` 0.00% filled in this release, so `duration_min` always falls back to `V2_DUREE` — a real-data fact, not a bug, confirmed by direct inspection after a `try_cast` type-mismatch error). CLI gains `--survey {emp2019,entd2008}`, `--density {grid,proxy}`, `--data-path` (replaces `--data-zip`; also fixes a latent cache-collision bug: a custom `data_path` now gets a survey-named tmp-scoped extraction directory, not the shared, file-name-only `data/interim/<survey>/csv` cache) and `--compare` (`run_compare`/`docs/data/step11_compare.md`: group table 2008 vs 2019 both proxy, EMP 2019 grid vs proxy, F8 base-case robustness core/full means both years, declared vs modelled walk/wait minutes for car driver/urban PT/train both years, weekday non-traveller share both years, one energy/time-by-group comparison figure, 2008-calibrated v0/P0 for information only — same `config/energy.yaml` parameters in both years). On real data: ENTD 2008 33,012 described days (15.5% weekday non-travellers vs EMP 2019's 2.7%); overall multimodal-group mean energy is far higher in 2008 (1,642 kJ kh, wide CI) than 2019 (725 kJ), not further investigated this round. Ruff clean; 54 budget tests pass (full suite 397, 2 pilot deselected). **Twelfth round (user-flagged anomaly: per-group bars close and mostly higher in 2019, but the 2008 overall mean was far higher):** traced to 3 ENTD 2008 cycling trips with implausible declared distances (c. 360-376 km in 65-90 min, 245-347 km/h), flagged by the existing upper-speed-bound check but -- per the round-5/round-4 design ("cycling energy is time-based, so only walk's and car's corrected distances feed the energy formula; bike is flagged but not corrected") -- never distance-corrected; the cycling formula's "stops" sub-term still multiplies by the raw distance and by the (also distance-derived) ride speed squared, so one such trip alone produced ~1.3M kJ for its one day, and its section 9.9 population weight (c. 20,400 person-days, about a 3% pull on the whole multimodal group alone) explained most of the 2008-2019 gap in every "overall" figure/table. Fix (user-approved): bike's flagged distance is now corrected like walk's and car's (one new `cycle_median_speed_kmh` branch, `trip_legs.build_trip_legs`'s "corrected" CTE); EMP 2019 is unaffected (0 of 1,023 cycle trips ever flagged there). After the fix: ENTD 2008 multimodal drops from 1,642.6 to 687.7 kJ (kh), its CI from [664.7, 3724.7] to [660.6, 714.9]; cycle from 601.9 to 588.0 kJ (cp), now close to 2019's 613.6; the 2008 overall mean from 625.0/572.8 to 533.3/481.1 kJ (kh/cp), now close to 2019's 544.4/495.7; 2008's P0 from 47.5 W to 34.0 W, now close to 2019's 34.8 W. New regression test (`test_implausibly_fast_cycle_trip_has_its_distance_corrected`) pins the correction and that a flagged cycle trip's energy stays the same order of magnitude as a plausible one. `run()`/the compare report/figure also gained the overall mean daily *time* (not just energy) and a third panel for KH energy alongside compendium (`_figure_compare_energy_time`, both requested by the user); all three regenerated on real data. Ruff clean; 55 budget tests pass (full suite 398, 2 pilot deselected). |
