# Changelog

Notable changes to the `mobgrid.budget` step 11 re-estimation (section
9.9). Not an exhaustive history; see `docs/progress.md` for the full
decision log.

## 2026-10-22 — step 11 fixes

### Fixed

- **Bike stop energy** now costed at the single flat speed the rider
  holds at the calibrated P0 (the inverse of the same force-balance
  solve `daily_energy.calibrate_p0` uses forward), not at each trip's
  own declared-distance/ride-time speed: that speed is noisy and the
  stop term is quadratic, so a small share of fast-declared trips
  dominated it (6% of EMP 2019 bike trips above 25 km/h gave 37% of the
  stop energy; the term carried 11.5%/10.2% of cycling-day energy in
  EMP 2019/ENTD 2008). Regression test:
  `tests/mobgrid/budget/test_emp2019.py::test_stop_energy_per_stop_is_the_same_regardless_of_declared_speed`.

  | Metric | Before | After |
  |---|---|---|
  | EMP 2019 (grid) `cycle` mean energy (KH / CP) | 631.0 / 613.6 kJ | 595.9 / 578.6 kJ |
  | EMP 2019 (grid) `multimodal` mean energy (KH / CP) | 754.6 / 658.8 kJ | 749.4 / 653.6 kJ |
  | ENTD 2008 `cycle` mean energy (KH / CP) | 588.0 / 570.0 kJ | 564.3 / 546.3 kJ |
  | ENTD 2008 `multimodal` mean energy (KH / CP) | 687.7 / 605.9 kJ | 686.5 / 604.7 kJ |
  | Compare report overall mean energy, 2019 (proxy, KH / CP) | 544.4 / 495.7 kJ | 543.4 / 494.7 kJ |
  | Compare report overall mean energy, 2008 (KH / CP) | 533.3 / 481.1 kJ | 532.7 / 480.4 kJ |
  | Cycle-day stop-term share of total energy, 2019 (2008) | 11.5% (10.2%) | 6.3% (6.4%) |

  Every other group's mean energy is unchanged (the term only enters
  the `cycle` energy formula).

- **`declared_vs_modelled_walk_wait`** (the declared-vs-modelled walk/wait
  check table) summed car's walk-to/from-car *and* PT's access-walk
  legs for every mode, including car ones (`access_walk_ori/des_min` is
  computed for every row regardless of mode): car's modelled walk was
  silently doubled, 17.6-19.2 min against a 9/10-minute default cap.
  Now mode-specific, matching the energy formula: car modes use only
  walk_to_car + walk_from_car; urban_pt/train use only access_walk_ori
  + access_walk_des. EMP 2019 `car_driver`'s modelled walk: 17.6 -> 6.3 min.

- **Sample-flow accounting**: the `**Sample:**` line's
  `n_days + non_traveler_n` reconstruction of "respondents" silently
  dropped respondents who had a trip but whose day fell out of scope or
  ended with null energy; replaced with an explicit sample-flow table
  (respondents -> days with trips -> days with energy -> days within
  scope -> days within scope with energy), in consistent units (persons
  and days kept apart). True respondent counts: EMP 2019 13,825 (the
  old line implied 12,429); ENTD 2008 18,632, `k_individu` (the old line
  implied 35,957, conflating a day-record count with `q_tcm_individu`'s
  49,283-row full household roster). Non-traveller share is now reported
  both unweighted and weighted, over the full roster.

- **Day-type mix**: `traveler_day_type_share` printed a raw
  `sum(pond_jour)` straight into a `.1%` format (e.g.
  "TYPEJOUR=1: 25002074313.3%"); now an actual share of the total.

- **Children-as-car-drivers**: the prose's day count (56 EMP 2019 / 148
  ENTD 2008) was read off a `day_summary` already silently rebuilt to
  the full, pre-exclusion motive scope by a later diagnostic block,
  while the table's count (50/140) used the needs-only scope. Both
  numbers are now computed together, in the needs-only scope: EMP 2019
  56 -> 50, ENTD 2008 148 -> 140.

- **"Six groups" comment/prose**: `F8_ROBUSTNESS_GROUPS` has always held
  7 groups; the comment above it and the matching report prose said six.

- **`config/energy.yaml`'s P0 comment** cited the total raw cycle-trip
  count (1,023) as the "reliable" one; the re-estimation's own reliable
  subset (passing the get/park + stop-delay reliability checks) is 727.

## 2026-10-20 — step 11, ENTD 2008

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
