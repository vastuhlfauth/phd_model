# Changelog

Notable changes to the `mobgrid.budget` step 11 re-estimation (section
9.9). Not an exhaustive history; see `docs/progress.md` for the full
decision log.

## Unreleased (branch `step/mobgrid-budget-entd2008`)

### Fixed

- **Bike distance correction for implausible speeds.** Reversed a round-5
  decision that flagged-but-implausible cycling trips were reported, not
  distance-corrected (unlike walk and car), on the premise that cycling
  energy is purely time-based. That premise missed that the energy
  formula's "stops" sub-term still multiplies by the trip's distance and
  by the (distance-derived) ride speed squared, so an uncorrected
  implausible distance still inflated total energy through it. Found via
  3 ENTD 2008 cycling trips declared at ~247-347 km/h; the worst, at
  376 km/65 min, produced ~1.3M kJ for a single day and, through its
  section 9.9 population weight (~20,400 person-days), dominated every
  2008 "overall" energy figure/table in the EMP 2019 vs ENTD 2008
  comparison. Bike's flagged distance is now corrected exactly like
  walk's and car's (`trip_legs.build_trip_legs`).

  | Metric | Before | After |
  |---|---|---|
  | ENTD 2008 multimodal group mean energy (KH) | 1,642.6 kJ | 687.7 kJ |
  | ENTD 2008 multimodal group 95% CI (KH) | [664.7, 3724.7] | [660.6, 714.9] |
  | ENTD 2008 overall mean energy (KH / CP, all groups) | 625.0 / 572.8 kJ | 533.3 / 481.1 kJ |
  | ENTD 2008 calibrated P0 | 47.5 W | 34.0 W (2019: 34.8 W) |

  EMP 2019 is unaffected: 0 of its 1,023 cycle trips were ever flagged by
  the speed check. Regression test:
  `tests/mobgrid/budget/test_emp2019.py::test_implausibly_fast_cycle_trip_has_its_distance_corrected`.

- F8's `_run_robustness` did not restore `trip_legs` to the base case
  after its last variant, so every later computation (F3-F5, F9, the
  cycle decomposition) silently reused the mutated state; this had made
  F4's "overall" panel disagree with the main group table. Fixed by
  rebuilding the base case as `_run_robustness`'s last step.

### Added

- ENTD 2008 support: `mobgrid.budget.entd2008` (mode/purpose conversion,
  the sequence-purpose rule, `POIDS_JOUR > 0` filtering,
  `V2_MOBILREF`-based non-travellers, `distcor`/`v2_mduree` fill-rate
  reporting), and the CLI's `--survey {emp2019,entd2008}`, `--density
  {grid,proxy}` and `--compare` options.
- `--compare`'s `compare_energy_time.png` figure: a third panel for KH
  energy alongside compendium, and each year's overall (all groups
  combined) mean daily energy and mean daily *time* as labelled
  reference lines; the report gets the same two overall-mean values in
  text.

### Changed

- `emp2019.build_trip_legs` split into a survey-specific `trips_norm`
  view and the shared, survey-agnostic
  `mobgrid.budget.trip_legs.build_trip_legs`; `day_summary` now groups
  by `trip_legs.day_id` (one day per person for EMP 2019, up to three
  per person for ENTD 2008), not `ident_ind`.

### Known issues (not introduced by this branch)

- `tests/mobgrid/pt/test_calibration_pilot.py::test_chosen_parameters_resolve_the_clear_cut_known_cases`
  fails with `AttributeError: 'dict' object has no attribute 'r_m'`.
  Confirmed pre-existing on `main` (same failure with the same local
  `calibration_run.pkl`/`osm_pt_stops` cache, verified via a scratch
  worktree). Root cause: commit `b7be54e` ("Step 0: route relation
  extraction, memory settings", 2026-10-13) changed
  `GtfsRebuildConfig.chosen` to `dict[ModeFamily, ChosenFamilyParameters]`
  without updating this test, which still reads it as a single object.
  Likely fix: index the per-family dict in the test, not regenerate the
  pickle. See `docs/progress.md`'s decision log for the full
  investigation; out of scope for this branch.
