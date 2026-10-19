# Progress

Read this file at the start of every task and update it at the end.

_Last updated: 2026-10-19 by Copilot (step 11, third round: a new `docs/spec/09_trip_legs_energy.md` adds section 9.7's unloaded pedalling cost and confirms P0 = 34.8 W; implemented in `mobgrid.energy.bike` (step 7, propagated through `checks.py`) and `mobgrid.budget.emp2019` (step 11), with `config/energy.yaml`'s `bike.power.p0_w` now `34.8` and a new `bike.pedalling_unloaded_net_met`; `step11_budget.md` gained a per-population-category group table and robustness min/max group names; both step 7 and step 11 commands rerun; branch `step/mobgrid-budget`, awaiting review)_

## Steps (table of section 14.5)

| Step | Content | Status | Branch | Notes |
|---|---|---|---|---|
| — | Repository skeleton (`/bootstrap`) | done | `step/bootstrap-skeleton` | uv workspace, package layout, configuration validation; Ruff and 3 tests pass (pinned Python 3.12.15) |
| 0 | GTFS rebuilding test | merged | `step/gtfs-rebuild-test` | **2026-10-15/16 national policy (no manual review):** tram alone keeps the automatic OSM relation rule (confirmed parameters); metro, rail, bus and ferry (including BHNS/express, whose own automatic cut rule is retired) keep every 2026 route in both past states by default, changed only by the PT openings list's auto-applied exact/stop-confirmed, high/medium-confidence matches. A `keep`/`modify` row gives no instruction at all (falls through to the tram rule or default keep); a `remove` row's effect depends on `change_type` -- `new_line`/`reopening` drop the route, `extension` cuts it at its old terminus, `new_station` removes only that stop (`mobgrid.pt.pt_changes.OpeningDerivedChange.instruction_at`, `mobgrid.pt.route_edits`); several rows' cuts/stop-removals on one route combine rather than any one dropping it; a `suspension` row never produces an instruction (settled decision: a temporary works closure does not remove a line from a state meant to represent the normal network). Precedence: openings list > tram automatic rule > default keep (`mobgrid.pt.pt_policy.resolve_route_presence`, tested). `to_review`/`not_applied` are informational only; nothing in the pipeline reads them. Lines closed before 2026 (`state` `add`) are left out and listed in the report as a known gap. The metro/bus/ferry/rail calibration numbers are kept in `config/gtfs_rebuild.yaml`/the report as a historical/screening reference only; metro's false changes are not investigated further. All 47 high/medium-confidence networks now have a resolved GTFS resource, including `Twisto (Caen la mer)`, mapped against the existing Normandy regional aggregate (resource 81942) rather than acquiring a second, duplicate-trip dedicated feed (2026-10-16 decision: an aggregate-only network is an accepted, normal outcome, not a gap to close). `mobgrid.pt map-and-apply-all` maps and applies every network in one resumable, logged, offline-only batch run (never downloads; raises a clear error if a resource isn't acquired yet), grouping network-name aliases by resolved GTFS resource id so each resource is read exactly once. `acquire --check-aom-coverage` confirmed 0 of 1,127 metropolitan AOMs are fully uncovered (865, including Twisto, have only indirect/aggregate coverage, accepted as sufficient -- no population filter needed). National run complete: 47 of 47 networks mapped, 53 rows applied (69 route-level edits), 5 rows left as accepted residual gaps (IDF-17, GES-06, NAQ-03, OCC-05, PAC-05), 0 regressions on reconciliation. The future national PT-build step must keep only the dedicated producer feed's copy of an agency that also appears in a broader aggregate, before any trip-level dedup across feeds (recorded below under "Open points from the spec"). Merged into `main` 2026-10-16. |
| 1 | `common`: config, grid cells, DuckDB I/O | merged | `step/common-foundations` | Config validation; cell ids/codes, nesting, neighbour stencil and tiles; Arrow/Parquet helpers; Ruff clean and 12 tests pass |
| 2 | `acquire`: manifest and downloaders | merged | `step/acquire` | Configured pilot source catalog; resumable, size-checked and checksum-verified HTTP downloads; Geofabrik MD5; restricted-file registration; API discovery helpers with per-source auth header/scheme; HTML-page detection; `verified` tracking; dry-run CLI. No real downloads run. Ruff clean; 40 tests pass. |
| 2a | Source URLs and national acquisition coverage | merged | `data/source-urls` | Both requested updates combined in one commit with user approval. 726 file/registration entries; direct INSEE/SDES/Géovélo/CARS/NUTS/Eurostat URLs; producer-only national GTFS inventory; 96 metropolitan BD ALTI archives; 26 neighbouring OSM extracts; anonymous Overture Parquet extraction with national box. Ruff clean; 61 tests pass. Metadata/HEAD requests only; no data files downloaded. |
| 2b | Source URL fixes: OSM size-only verification, TCL Lyon GTFS resource | merged | `data/source-urls` | Neighbouring OSM extracts verified by `Content-Length` instead of a nonexistent `.md5`; TCL Lyon's dropped/overridden GTFS resource now resolves to the current SYTRAL Mobilités feed with a Mobility Database fallback. Ruff clean; 67 tests pass. Dry run: 0 blocked entries (down from 27). |
| 2c | Audit of the remaining 12 excluded community GTFS resources | merged | `data/source-urls` | Checked, for each of the 12 datasets with a community-tagged excluded GTFS resource, whether that dataset keeps another producer GTFS resource; all 12 do (true duplicates), so none needed a TCL-Lyon-style override. Added a `discover_gtfs` safeguard that logs a warning if a community exclusion would ever leave a dataset with zero producer GTFS resources, so a future case is caught automatically. Ruff clean; 68 tests pass. |
| 2d | France OSM sizes, resilient acquisition batches and reruns | merged | `fix/osm-size` | France uses HEAD sizes without MD5 sidecars; OSM discovery refreshes all 28 extracts. Failed acquisitions no longer abort the batch; summary counts/reasons and exit 1 on failures. Recorded matching files skip network requests and preserve verification/date. Tests first; Ruff clean; 81 tests pass. |
| 2e | Acquisition robustness, own GTFS archives, offline feed checks, Filosofi 2019 | merged | `fix/acquire-robustness` | Per-file atomic manifest persistence; Windows replacement retries and short-lived readers; strict latest-own-archive fallback; offline GTFS inventory command; covered-resource exclusions; both Filosofi 2019 archives acquired. Tests first; Ruff clean; 108 tests pass. Offline check: 551 downloaded, 536 passing feeds, 47 expired, 15 invalid/unusable, 18 flex indicators; no files deleted. |
| 3 | `landgrid/origins` | not started | | |
| 4 | `landgrid/jobs` | not started | | |
| 5 | `landgrid/services`, `nature`, `social`, `destinations` | not started | | |
| 6 | `mobgrid/osm` | not started | | |
| 7 | `mobgrid/energy` | review | `step/mobgrid-energy` | Leg formulas of section 9.1 to 9.8: `rates.py` (`config/energy.yaml` loader, KH/Compendium activity rates, `sedentary_energy_kj`), `walk.py` (Tobler speed, Minetti gradient factor, stairs), `bike.py` (force-balance speed solver, ride/stop energy, separated-infra factor, e-bike pedelec assist), `legs.py` (`Leg` chain T=sum(t)/E=sum(e), waiting, PT ride crowding, car congestion). Reproduces every section 9.2 reference rate and the 9.3/9.7 checks (gradient factors, 1 km flat walk 160/211 kJ, 10 m stairs 22.9 kJ, 16 km/h mechanical power ~52.5 W, +-mass speed changes, one-stop energy). Second round of fixes (user-reported, 2026-10-19): unified clamp formula `P_r = clamp(P0.(1+k.i), 0, Pmax)` on every grade fixes a zero-speed plateau just past a flat descent (`bike.select_ride_power_w`/`ride_speed_and_power`/`required_power_w`); e-bike rider/motor energy now split by `s_r = P_r/(P_r+P_m)` on every edge and stop (`ebike_ride_speed_and_power`, `ebike_rider_share`, `bike_ride_energy_kj`/`stop_energy_kj`'s new `rider_share`); `climbing_work_j_per_kg` is now signed; bike stops add time (`bike.stop_time_s`, new `config.bike.stops`, TODO(confirm)); terminal walking legs use the active rate set's c0, not a hardcoded Compendium; added the carpool passenger (`config.car.carpool_passenger`, TODO(confirm)) alongside the household passenger; bus/train rides use the first-phase standing shares of 9.5 everywhere, not seated-only; new `config.bike.ebike.effort_factor_by_level` (TODO(confirm), default 1.0) hooks a future rider-effort-vs-assist calibration. **Third round (after step 11's P0 calibration and a new `docs/spec/09_trip_legs_energy.md`):** section 9.7 gains an unloaded pedalling cost, `e = m.u_ped.t_ped` with `u_ped` = 1 net MET/pedalled minute (`config.bike.pedalling_unloaded_net_met`, ACSM/Swain 2000, not TODO(confirm): a literature value), on the rider's own mass only, for bike and e-bike riders alike, not scaled by `rider_share` or `separated_infra_factor` (`bike.unloaded_pedalling_energy_kj`, new keyword-only params of `bike.bike_ride_energy_kj`); `config.bike.power.p0_w` is now `34.8` (confirmed by step 11's EMP calibration, no longer `null`), `k`/`p_max_w`/`v_max_descent_kmh` stay TODO(confirm). `checks.py`'s own illustrative set-A P0 (~52.5 W, self-derived from the 16 km/h force-balance check) is unaffected; its "metabolic rate, 16 km/h flat" check now expects ~18.2 kJ/min (was ~13.1) with the unloaded term added; F4's roll/climb/stops/drag decomposition deliberately excludes the unloaded term (documented: a mechanical-work-only split). Verification command `python -m mobgrid.energy.checks --out docs/data/step7_energy` (`checks.py`, matplotlib dev dependency) writes 10 PNGs (F1-F10, F7 now also covers F7b's fixed-time panels, F9 now has three panels A/B/C) plus `docs/data/step7_energy_checks.md` (27 PASS/0 FAIL/10 COMPARE, rerun after the third round); run once, committed. Ruff clean; 71 energy tests pass (361 total, 3 pilot deselected). |
| 8 | `mobgrid/graph` | not started | | |
| 9 | `mobgrid/layers/gridgraph.py` | not started | | |
| 10 | `mobgrid/od` | not started | | |
| 11 | `mobgrid/budget` | review | `step/mobgrid-budget` | **Brought forward before steps 8-10** (needs only step 7 and the EMP 2019 public tables, not the graph/OD steps). Section 9.9's re-estimation steps 1-3 and 5 on EMP 2019's public tables (`K_DEPLOC`, `TCM_IND_KISH`, `K_INDIVIDU`; `TCM_IND`/`Q_MENAGE` acquired and checked but not needed by this step's formulas); EMC² (step 4) and Ē_c (step 6) are out of scope. `emp2019.py` rebuilds each of the 45,169 EMP 2019 trips (13,370 respondents, 455 reporting no trip) as legs, reusing `mobgrid.energy`'s public walk/bike/legs/rates formulas: terminal legs by density class (car: `config.car.*`, already calibrated for step 7; PT: provisional `config.pt_ride.headway_min_am_peak`/`station_height_m`/`access_walk_m_by_density`, TODO(confirm), since EMP has no headway/station-depth/access-distance data) and the main leg at the rest of the declared duration (`DUREE`); companions (`MACCOMPM`/`MACCOMPHM`) separate household from carpool car passengers. `daily_energy.py` sums to one row per respondent, classifies each day by its one non-walk mode, and computes weighted group means with a household bootstrap 95% CI (`bootstrap_group_stats`), a method-of-moments gamma fit (no new `scipy` dependency), and the v0/P0 calibration by age band. Checked the user-reported ~119 kJ train-chain discrepancy from step 7's `checks.py`: escalators (standing rate), not stairs, are already correctly used above the 10 m threshold (commit `cc9eb81`'s fix). Found and fixed a pre-existing `config.pt_ride.standing_share_am_peak` key mismatch (4 of `load_factor_max`'s 8 vehicle keys were missing). **Second round (after main's spec 6/9 update, "population categories, train and passenger splits"):** day-mode groups now keep household/carpool passengers and short (<80 km)/long train separate (no collapsing; `emp2019.TRAIN_LONG_THRESHOLD_KM`), "multimodal" and "other" (enumerated in the report) stay apart; population category follows section 6.1's five groups exactly (`SITUA`'s student code now folds into `other_inactive`, dropping the ad hoc sixth "student" group); density labels use the INSEE grid's own names/order (dense/intermediate/sparse/very_sparse; `emp2019._DENSITY_LABEL_BY_CODE`/`_DENSITY_KEY_TRANSLATION`), checked against the categories PDF. v0 and P0 are now ratio-of-weighted-sums estimators (not averages of per-trip speeds); P0 first subtracts bike get/park (new `config.bike.get_park_min`, 1 min each) and expected stop delays (new `config.bike.stops.stops_per_km`, both TODO(confirm)) from the declared duration, with an unreliable-adjustment fallback to the naive whole-duration speed below a minimum ride-time/fraction or above a plausibility speed cap (`emp2019._BIKE_MIN_RIDE_TIME_S`/`_BIKE_MIN_RIDE_FRACTION`/`_BIKE_MAX_PLAUSIBLE_SPEED_KMH`) for a handful of very short or implausibly fast cycling trips. `build_trip_legs` gained `terminal_scale`/`bike_p0_override_w` parameters and `create_day_summary` a `where_sql` filter, used by the new F8 robustness check (`daily_energy.robustness_row`/`RobustnessRow`): max/min ratio and CV of six groups' means, across both rate sets, terminal legs x0.5/x1/x1.5, P0 recalibrated vs the 52.5 W reference, weekdays-only vs all days, and local-trips-only (`MOBLOC=1`) vs all. Added a weighted Gaussian KDE on log-energy (`daily_energy.weighted_gaussian_kde`/`weighted_gaussian_bandwidth`, Silverman's rule, no `scipy`) for F3's stacked/overlaid density figures (overall and one per population category, Compendium, with a KH appendix). Investigated the non-traveller immobility share (reported low at 2.7%): identification is "no K_DEPLOC row for the day", which matches `K_INDIVIDU`'s own `MIMMOSEM` flag exactly for all 455 cases; EMP 2019's public tables record no day-of-week for a fully immobile respondent, so the figure is an inherently weekday-dominated estimate, not an all-week average (documented, not changed). Verification command `python -m mobgrid.budget.emp --out docs/data/step11_budget` (`emp.py`) now writes 11 PNGs (F1, F3 x4 incl. KH appendix, F4a/b, F5, F6, F7, F8) plus `docs/data/step11_budget.md`; run once, committed. On real EMP 2019 data (second round): overall weighted mean daily energy 684 kJ (KH) / 604 kJ (Compendium) against Koelbl & Helbing's 615 kJ hypothesis; calibrated v0 3.96 km/h (configured 4.8), P0 34.8 W at an implied flat speed of 13.55 km/h (reference 52.5 W at 16 km/h). **Third round (new `docs/spec/09_trip_legs_energy.md`, unloaded pedalling cost):** `emp2019.py`'s cycle-energy SQL formula gains the same unloaded-pedalling term as `mobgrid.energy.bike` (section 9.7, step 7 third round), on `bike_ride_time_for_energy_s` at the reference mass, both rate sets; P0 itself is unaffected (it is calibrated from implied speed via force-balance physics, not from energy/duration), still 34.8 W at 13.55 km/h. Added two tables to `step11_budget.md`: mean daily energy (both rate sets) and time, 95% CI and n, for every main-mode group, overall and one sub-table per population category (`emp._figure_f4_mean_by_mode` now also returns its per-panel stats, `_format_group_table_by_panel`); the F8 robustness table now also names each variant's min/max group (`daily_energy.RobustnessRow`/`robustness_row` gained `*_min_group`/`*_max_group` fields). Rerun on real EMP 2019 data: overall weighted mean daily energy 691.1 kJ (kh), 611.2 kJ (compendium); v0/P0 unchanged. Ruff clean; 18 budget tests pass (361 total, 3 pilot deselected). |

Status values: not started, in progress, review, merged.

## Data pages written (`/schema`)

- [EMP 2019 public tables](data/emp2019.md) (step 11)

## Decisions taken while coding

- 2026-10-19, step 11, the spec 09 replacement flagged below (2026-10-19,
  step 7 second round) is resolved: the user confirmed `docs/spec/09_trip_legs_energy.md`
  (commit `76e5260`, "Spec 9: bike descents, e-bike rider share,
  passengers, EMP test design") is now committed on `main` and contains
  the file this project treats as section 9's authority, including its
  9.9 re-estimation steps and the EMP test design referenced by step 11.
- 2026-10-19, step 7, `docs/spec_v10_changes.md` (referenced by the task)
  was not committed to the repo; the user pointed to the untracked
  `docs/spec/spec_v10.zip`, which contains it plus every changed spec
  file since version 8. Diffed `09_trip_legs_energy.md` between the
  current tracked copy and the zip's version: the only change is one
  sentence in 9.8 (congestion now comes from BPR functions on the
  reduced network, section 12, rather than an out-of-equilibrium loop),
  which does not affect any formula of 9.1-9.8 implemented here. The
  spec files were not committed (out of scope: v10 also touches 8, 11,
  12, 13, 14, 15, unrelated to this step), and `docs/spec/09_trip_legs_energy.md`
  (version 9, already tracked) was left unmodified since its section 9
  content is identical in substance to v10's.
- 2026-10-19, step 7, the section 9.5 PT-ride formula's three rates
  (`r_sit`, `r_relaxed`, `r_restless` = 1.5, 2.6, 6.7 kJ/min) are pinned
  to the literal KH figures in `config/energy.yaml`'s `pt_ride` block,
  not switched by the configured `rate_set`: the spec tags all three
  "(KH)" and the Compendium has no restless-standing equivalent. The
  general `activity_rates` table (sitting, standing, driving) does
  switch between KH and Compendium, since section 9.2 gives both for
  those.
- 2026-10-19, step 7, added `mobgrid/energy/checks.py`
  (`python -m mobgrid.energy.checks --out <dir>`), a verification command
  producing 10 PNGs plus a Markdown check table, built only from
  `rates`/`walk`/`bike`/`legs`' public functions. Provisional scenario
  values requested by the user (bike power sets A/B, `v_max,desc`,
  terminal-leg times, bus/metro/car parameters, trips per day) live only
  in `checks.build_provisional`, never in `config/energy.yaml` (which
  keeps its `null`/`TODO(confirm)` placeholders). Notable modelling
  choices, documented in the generated report's own "Modelling notes"
  section: (1) e-bike figures reuse bike set A's rider power profile
  plus the configured pedelec assist factor, so rider effort does not
  fall with more assistance in this simple model (flagged explicitly by
  two F3 COMPARE rows against the Compendium's light/high-support MET
  values); (2) F4's e-bike roll/climb/stops/drag split is computed at
  the e-bike's own (faster) speed divided by the same efficiency, as if
  unassisted, overstating the rider's real cost (F3's rider-only split
  is the correct one); (3) PT legs in F7/F8/F9 use an illustrative
  400 m each-way access/egress walk (not given by the task) and an
  implied load factor `1/(1-standing_share)` from section 9.5's
  first-phase standing shares; (4) F9-B's "train" mode reuses the metro
  chain's terminal legs with its own seated rate, per the task's "Train:
  metro terminal legs"; (5) bike/car stop and parking-search durations
  count only energy, not an added time cost (section 9.7's stop-time
  formula needs signal-timing data not configured). Ran
  `python -m mobgrid.energy.checks --out docs/data/step7_energy` once:
  27 PASS, 0 FAIL, 9 COMPARE; committed the 10 PNGs and the check table.
  Added `tests/mobgrid/energy/test_checks.py` (smoke test: runs the
  command into a tmp dir, asserts 10 PNGs, the report file, and no
  `FAIL` table row). `matplotlib` added as a `dev` dependency
  (`uv add --dev matplotlib`).
- 2026-10-13, long-running job policy (task A), appended the user's exact
  instructions to [.github/copilot-instructions.md](../.github/copilot-instructions.md),
  ignored `logs/`, and configured pytest to exclude `pilot` tests by default.
  National extraction and real calibration must be run by the user, with
  resumable checkpoints, dated logs and summaries. Task B's relation-based
  GTFS rebuild is planned only; implementation awaits approval. Validation:
  Ruff clean; default pytest run reports 155 passed and 2 pilot tests
  deselected in 16.93 s. The PowerShell tool reported a separate wrapper
  `SetShouldExit` error after both commands completed successfully.
- 2026-10-13, step 0 method change (user-approved override of section 5.6),
  replace the failed stop-only rule with **OSM route-relation matching by
  normalised name first, then by geometry**, followed by spatial verification
  of the matched portions. Route decisions use the most-travelled pattern on
  the reference date, not the worst pattern. Name matches use network/operator
  tags as tie-breakers; geometry-only matches are `kept-renamed`. Tram, metro
  and rail are cut at uncovered ends before theta; buses and ferries are only
  kept or dropped. Networks below 50% relation coverage are `not-testable`.
- 2026-10-13, step 0 extraction, use DuckDB `ST_ReadOSM` in three filtered
  passes preserving `refs`, `ref_types` and `ref_roles`; no new dependency.
  Cache relation, member, way and stop/platform Parquet under
  `data/interim/osm_pt_routes/{date}`. DuckDB is capped at 60% of physical RAM
  and spills under `data/interim`. Each dated run checkpoints completed
  Parquet stages and writes the required log and summary.
- 2026-10-13, step 0 scoring, calibrate each family over r, k, theta and the
  minimum geometry share. Report known-case precision/recall/F1 and exact
  outcomes separately from the false-change rate among all other test-area
  routes presumed unchanged; exclude `not-testable`. Rank exact known outcomes
  first, then F1, then the lower false-change rate. Recommendations remain
  `TODO(confirm)` until the user runs the real calibration.
- 2026-10-13, step 0 synthetic validation, Ruff is clean and the default
  pytest run reports **174 passed, 2 pilot tests deselected in 23.26 s**.
  Synthetic fixtures cover normalised name matching, network/operator
  tie-breaking, E/F-style geometry renaming, construction exclusion,
  cut-before-theta, main-pattern selection, bus/ferry no-cut decisions,
  low-coverage `not-testable`, track-qualified fixed-guideway fallback,
  known-case/false-change scoring and confirmed-only scenario edits. The
  Luxembourg smoke was subsequently run; no download, pilot, calibration or
  national job was run by Copilot.
- 2026-10-13, step 0 smoke check, the Luxembourg 2024 extraction validates the
  three-pass DuckDB schema: 690 relations (644 bus, 44 train, 2 tram), 100% of
  the 79,404 member ways with a geometry and 100% of the 19,111 member stops
  with coordinates. `process_peak_memory_bytes` returned nothing because
  `GetCurrentProcess` kept ctypes' default `c_int` result type, truncating the
  64-bit pseudo-handle so `GetProcessMemoryInfo` failed with
  `ERROR_INVALID_HANDLE`; the handle is now typed `c_void_p`. A clean rerun
  took 6.6 seconds and peaked at 0.71 GiB. Linear compressed-input runtime
  estimates are 11.2 minutes for France 2022 and 12.1 minutes for France
  2024. The corresponding 71.24 and 77.46 GiB memory figures are conservative
  upper bounds, not forecasts: most work streams, while DuckDB is capped at
  60% of RAM and spills to disk. On this 31.64 GiB PC, the verified runtime
  settings are a 19.0 GiB memory limit, 12 default threads and spill directory
  `data/interim/osm_pt_routes/_duckdb_temp`.
- 2026-10-13, step 0 resumability, OSM extraction publishes each Parquet
  stage atomically and skips existing stages. GTFS ZIP tables are extracted
  atomically and reused. Calibration checkpoints every completed parameter
  point to
  `data/interim/gtfs_rebuild/calibration_scratch/calibration_grid_tables.pkl`
  and invalidates that checkpoint when the grid or table-precompute signature
  changes; the final result pickle is reused on rerun.
- 2026-10-13, step 0 contour repair, the first full calibration stopped while
  unioning the national commune contours for rail coverage because an invalid
  overseas polygon had a hole outside its shell. Both EPCI and national
  coverage unions now apply DuckDB `ST_MakeValid` to each source geometry
  before aggregation. A synthetic multi-commune regression reproduces the
  original `TopologyException` before the fix and verifies inside/outside stop
  filtering afterwards. The long calibration was not rerun by Copilot.
- 2026-10-14, step 0 table calibration, replaced the repeated Python scan of
  national relation geometry. The pipeline first keeps one main pattern per
  route reaching a test EPCI, plus known cases. DuckDB then bbox-prefilters
  same-mode relations within 1 km of individual pattern stops and writes
  persistent pattern, name-match and stop/relation-distance Parquet tables.
  Exact spatial distances are computed once up to the largest radius; the
  complete grid is evaluated from scalar tables in one DuckDB query. Every
  point is still logged and atomically checkpointed, using a new cache format
  that cannot reuse the two points from the abandoned geometry-loop run.
- 2026-10-14, step 0 Sète benchmark, a clean subset run retained 22 main
  patterns and completed in 66.6 seconds. Spatial precompute took 31.6 seconds
  (3,344 candidate relations, 3,784 distance rows, 49 name rows); all cached
  route outcomes for the 405-point grid took 0.6 seconds, and scoring,
  per-point logging and checkpointing took about 2.8 seconds total (about
  0.007 seconds per point). The subset produced 44 route/date outcomes and did
  not update national chosen parameters or candidates.
- 2026-10-14, step 0 first full national run, completed in 16m 27s (one-time
  spatial precompute 9.7 min over 647 reduced patterns, 185,724 candidate
  relations, 177,158 distance rows; the full 405-point grid itself in 5.1 s).
  Known-case metrics were strong (bus/ferry F1 1.00, metro/rail F1 1.00, tram
  F1 0.92), but the bus/ferry false-change rate was 30-73% at *every* grid
  point, never below 32.63%. Traced to TBM bus line "1" (name-matched
  correctly, ref "1"): 34 of 50 stops sit 0.4-7 m from the matched relation
  (near-perfect), but 16 of 50 have no relation way/stop within the largest
  calibrated radius (100 m) -- a genuine OSM bus-route mapping-completeness
  gap, not a matching bug. 516 candidates were written, overwhelmingly bus.
- 2026-10-14, step 0 BHNS/express decision (section 5.6, user-approved),
  given the bus mapping gap above: bus and ferry are never auto-applied to a
  past state; `PtChangeCatalogue.changes_after`/`removed_route_keys` read
  only `confirmed` by default (Express G 901, H 911/912, Sète A). BHNS/express
  routes are the one exception -- identified by `Express`, `BHNS`,
  `Liane(s)`, `Chronobus` in the GTFS short/long name or `route_desc`
  (`classify_bhns`) -- and are verified like a tram: cut at uncovered ends
  before theta, using dedicated bus infrastructure in OSM
  (`highway=busway`/`bus_guideway`, `busway=*`, `lanes:bus=*`, excluding
  construction/proposed) instead of the plain kept/dropped bus rule. This
  required two new `ways.parquet` columns (`busway`, `lanes_bus`);
  `extract_osm_pt_routes` now detects a cache missing them and rebuilds only
  `ways.parquet` from the already-cached `ways_raw`/`nodes_raw`/`members`
  stages (verified on a Luxembourg smoke rerun: all five other stages
  skipped, `ways.parquet` rebuilt from cache in about 3.6 s, no PBF rescan;
  confirmed real `busway`/`lanes:bus` tag values and one `highway=bus_guideway`
  way present). The France 2022/2024 route caches still predate these
  columns and must be re-extracted by the user (same command as before; both
  dates needed, since the dated caches are unioned and must share a schema).
- 2026-10-14, step 0 France ways.parquet rebuild, the user reran both dated
  extractions; as expected, the four PBF-scan stages were skipped and only
  `ways.parquet` was rebuilt from cache, with no PBF rescan. The Luxembourg
  smoke's "a few seconds" estimate for this step was wrong at national scale:
  the final join/aggregate over millions of ways and their points is not
  input-size-independent, and it took about 32 minutes for 2022
  (2,337,542 ways) and about 2h 37min for 2024 (3,004,246 ways). Both caches
  now carry real `busway`/`lanes_bus` data: 2022 has 1,212 `highway in
  (busway, bus_guideway)` ways, 14,329 `busway=*` ways and 1,707
  `lanes:bus=*` ways; 2024 has 6,827/17,944/2,660 respectively.
- 2026-10-14, step 0 checkpoint-invalidation bug, the first `calibrate` rerun
  after the ways.parquet rebuild silently reused the pre-BHNS results pickle
  and skipped recomputation entirely: unlike the relation-table precompute
  and grid checkpoints, the top-level `--results-pickle` had no input
  signature, only an "if the file exists, load it" check. Fixed with
  `_calibration_run_signature`, hashing the config, the GTFS
  inventory/sources/contours files and every OSM route cache file's size and
  mtime, stored alongside the pickle as `*.signature.json`; a changed
  signature (such as a rebuilt `ways.parquet`) forces recomputation. A
  synthetic regression proves the signature changes when a route-cache file
  is rewritten and is stable otherwise. The real calibration still needs to
  be rerun by the user with this fix in place.
- 2026-10-14, step 0 second full national run (with the signature fix, BHNS
  rule and new `ways.parquet` columns in effect), completed. Precompute took
  about 40 minutes this time (185,724 candidate relations, 177,495 distance
  rows, up from 177,158 -- the extra per-way BHNS in-service `CASE` adds real
  cost at this scale) versus 9.7 minutes before; the grid itself still only
  11.5 s. Known cases stayed strong (bus/ferry F1 1.00 incl. both Bordeaux
  Express cases now correctly "dropped" both dates; metro/rail F1 1.00; tram
  F1 0.92 unchanged). The bus/ferry false-change rate is still high (70.35%
  recommended), confirming the 2026-10-13 finding: this is an OSM
  bus-route-mapping-completeness limitation BHNS treatment cannot fix for
  ordinary bus lines, which is why bus/ferry are never auto-applied (decision
  above). `classify_bhns` correctly flagged 16 real routes from GTFS names,
  including TBM's "Lianes N" convention and the three confirmed Express
  lines (901, 911, 912) plus TCL's "98EX ... (Express)"; two TBM Lianes show
  0% of stops on dedicated bus infrastructure (OSM simply has none mapped for
  those lines). `config/pt_changes.yaml` now has 50 `to_review` (2 BHNS) and
  468 `not_applied` candidates from real post-BHNS data, replacing the
  provisional migration; `docs/data/step0_gtfs_rebuild.md` is current (the
  stale banner was naturally overwritten by the real `write_report` run).
- 2026-10-14, step 0 rail score-aliasing bug, `chosen["rail"]` literally
  copied metro's `GridPoint` (rail reuses metro's r/k/theta/geometry_share
  since section 5.6 has no labelled rail known case), which also copied
  metro's *score* -- unlike ferry (genuinely merged into the "bus" family
  everywhere, so aliasing `chosen["ferry"] = chosen["bus"]` is correct),
  rail is a distinct, separately-evaluated family, so the report's "rail"
  row silently showed metro's 9/9 known cases and 0.00% false-change rate
  instead of rail's own. Fixed: rail's score is now recomputed from rail's
  own routes at metro's chosen parameters. A synthetic regression (distinct
  metro-kept vs rail-dropped routes) proves the two scores differ and
  `chosen["rail"].score is not chosen["metro"].score`. The real rail false-
  change rate is **33.51%** (65 of 194 presumed-unchanged SNCF routes cut or
  dropped), not the reported 0.00%; patched directly into the cached
  results pickle/report/`pt_changes.yaml` (pure recomputation from already-
  cached `final_routes`, no rerun needed) and reverified: Ruff clean, 193
  tests pass.
- 2026-10-14, step 0 false-change detail for tram/metro/rail at the
  recommended point: metro has 0 presumed-unchanged routes (IDFM/STAR
  Rennes are restricted to known-case metro lines only, so every metro
  route is a known case); tram has 20 presumed-unchanged, 2 flagged (`tcl_lyon`
  `T4`, both dates, `cut`, 100% covered after cutting -- a real end
  extension, not a mapping gap); rail has 194 presumed-unchanged, 65 flagged
  (mostly SNCF TER/TGV/OCESN routes, `cut` or `dropped`, shares from 0% to
  100%), consistent with rail inheriting metro's strict `geometry_share=0.7`
  threshold on routes it was never calibrated against.
- 2026-10-14, step 0 tram known-case failures (2 of 8, giving F1 0.92): (a)
  `bordeaux_tram_f_rename` (route 164/F) is `cut` at both dates, not the
  expected `kept-renamed`: 11 of its leading stops are not within range of
  the matched relation "A" at either date (100% covered after cutting), so F
  apparently extends beyond old A's historic tracks at its start, unlike E
  (163), which is fully covered (0 stops cut) at both dates. (b)
  `bordeaux_tram_a_airport` (route 59/A) is `kept` in 2022 (100% covered, no
  cut) against an expected `cut`: OSM's "A" relation already carries the
  full route geometry to the airport in the 2022-01-01 extract, suggesting
  the track was mapped (or physically built) before the line's commercial
  opening date used to set the known-case expectation. Both read as likely
  mislabelled known-case assumptions (an OSM-vs-GTFS evidence question,
  not a pipeline defect) rather than matching/verification bugs, pending the
  user's confirmation of Bordeaux's actual track history.
- 2026-10-14, step 0 TBM line 05/Liane 5 investigation and rejection,
  flagged `dropped` in 2024 only (to_review). Confirmed **not** a ref-
  normalisation issue: GTFS `route_short_name` "5" matches OSM `ref` "5"
  exactly in both dated extracts (matching always uses `route_short_name`,
  never the zero-padded internal GTFS `route_id` "05"); a repo-wide audit
  found zero `route_short_name` values with a leading zero in any test
  network, so `normalise_ref` needed no change and nothing else is affected.
  Root cause: OSM gained two additional `ref='5'` relations by 2024
  (16438549/16438550, "Lianes 5 -> Villenave-d'Ornon Courrejean", alongside
  the original 2425811/2425812 "-> Piscine Chambery") -- a genuine route-
  variant addition, not a mapping error. Because "05"/"Lianes 5" is BHNS-
  classified, coverage only counts `busway`/`lanes:bus`-tagged ways, which
  are sparsely mapped here: 2022 barely passed (a 3-stop remnant, 100%
  covered after cutting, just clears bus's `theta=0.9`) and 2024 falls to
  66.7% (4/6) after cutting. Added `PtChangeCatalogue.rejected` (with a
  `notes` field) for candidates a reviewer has confirmed are false
  positives; `_write_review_lists` now excludes `confirmed` *and*
  `rejected` route keys so they are not re-surfaced on a rerun. TBM 05 was
  moved from `to_review` into `rejected` with the finding above recorded.
- 2026-10-14, step 0 "relations give identity, tracks give coverage"
  decision (user-confirmed field corrections): known cases were wrong, not
  the pipeline. Line F opened 2025-12-06 (did not exist 1 Jan 2022/2024;
  `expected_2022`/`expected_2024` corrected from `kept-renamed` to `cut`,
  kept only on stops served by whatever line's tracks were in service that
  date); tram A ended at Merignac Centre on 1 Jan 2022, with the airport
  branch opening in 2023 (its `cut`/`kept` expectation was already correct).
  For tram, metro and rail only, coverage now checks any in-service
  same-mode relation's ways on that date, not only the one(s) selected as
  the route's identity match (`track_covered`, new CTE in
  `_bulk_evaluation_sql`; bus/ferry unchanged). A synthetic regression
  proves a stop is covered via an unmatched same-mode relation's track. Also
  added, defensively: ways whose `opening_date`/`start_date` (full ISO or a
  bare year) is after the snapshot date are excluded from `in_service` and
  `bus_lane_in_service`; the SQL checks column existence first, so older
  caches without these columns keep working unchanged (two new regression
  tests in `tests/mobgrid/pt/test_relation_tables.py`, a new module).
  Inspected the Bordeaux tram A airport-branch ways in the 2022-01-01
  `_stages/ways_raw.parquet` (the raw OSM tags, not just the narrower
  `ways.parquet` columns): none of its 207 member ways carry `construction`,
  `opening_date` or `start_date` at all, so this specific case is a genuine
  OSM-data gap (the track was mapped as ordinary `railway=tram` well before
  the 2023 opening), not something the new filter or a re-extraction can
  fix; `ways.parquet` still needed the two new columns added regardless (for
  other lines), bumping its required-columns set again -- a further France
  re-extraction (both dates, reusing cached stages, no PBF rescan) is
  optional and only given below if wanted, not run automatically.
- 2026-10-14, step 0 re-score from cached tables (no re-extraction), only
  the grid-evaluation SQL changed (track_covered), so re-scoring reused the
  existing `relation_tables` precompute cache directly via
  `calibrate_relations`, skipping GTFS/EPCI reloading entirely (a few
  seconds, not minutes). Result: tram known cases improved from 5/8 to
  **7/8** (F1 0.92, only the Merignac/airport OSM-data gap above remains
  wrong) and tram's false-change rate dropped from 10.00% to **0.00%**
  (zero of 20 presumed-unchanged routes now wrongly flagged). Rail's
  false-change rate dropped from 33.51% to **17.01%** (33 of 194
  presumed-unchanged SNCF routes still cut or dropped, mostly `cut` with
  a wide range of post-cut shares -- a remaining, smaller OSM rail-mapping
  gap). Metro was unchanged (9/9, 0 presumed-unchanged, already restricted
  to known-case lines only). `config/gtfs_rebuild.yaml`'s `chosen` block
  did not need updating: every family's recommended `r_m`/`k`/`theta`/
  `geometry_share` came out identical to before the fix.
- 2026-10-14, step 0 rail default-kept and its own review cap, rail is
  policy-equivalent to bus (`changes_after`/`removed_route_keys` already
  only ever read `confirmed`, regardless of family). `_write_review_lists`
  now computes `to_review` per family: bus/ferry combined keep their top-50
  BHNS-then-trips cap; rail gets its own top-30-by-trips cap (no BHNS
  concept), so it never competes with bus for the same 50 slots. In
  practice no SNCF candidate currently reaches `to_review`: the network's
  own OSM relation-match coverage is only 59% (2022) / 56% (2024), below
  the shared 90% eligibility gate, so all 63 SNCF candidates land in
  `not_applied` -- correct and expected, not a bug; the per-family cap will
  bind once SNCF's coverage improves or another rail network is added.
- 2026-10-14, step 0 candidate review reduction (section 5.6 point 3), the
  flat 516-candidate list is replaced by `to_review` (candidates whose
  network has >=90% OSM relation coverage on every date they were flagged,
  ranked BHNS/express first then by reference-date trips, capped at 50) and
  `not_applied` (every other candidate, with full evidence, never auto-
  applied). `config/pt_changes.yaml`'s existing 516 candidates were migrated
  into `not_applied` as a provisional bucket (schema-valid, nothing deleted),
  since they were computed before BHNS classification existed and must be
  regenerated by a fresh `calibrate` run to be correctly re-split.
  `docs/data/step0_gtfs_rebuild.md` is marked stale for the same reason.
- 2026-10-14, step 0 past-state sensitivity (section 11.4), added
  `PtChangeCatalogue.removed_route_keys(state_date, sensitivity=...)`:
  `"confirmed"` (default) subtracts only confirmed edits; the future past-
  state builder can pass `"confirmed_and_candidates"` to additionally drop
  every candidate (`to_review` or `not_applied`) whose outcome on that date
  is `dropped`, for sensitivity testing; `kept-renamed` candidates are never
  removed, since they describe a route kept on a different alignment.
- 2026-10-14, step 0 open limitation, the bus/ferry false-change rate (above)
  means neither the bus/ferry `chosen` calibration values nor a bulk
  `not_applied` candidate should be trusted as ground truth without manual
  review; the BHNS/90%-coverage changes reduce but do not eliminate this,
  since most French bus lines are not BHNS and OSM bus-route mapping
  completeness cannot be improved from this project. Validation: Ruff clean;
  188 tests pass, 2 pilot tests deselected.
- 2026-10-14, step 0 opening_date re-extraction impact check (read-only), the
  user re-extracted both France ways.parquet caches with the opening_date/
  start_date columns. A national scan found only 81 (2022-01-01) and 68
  (2024-01-01) ways nationwide with an `opening_date`/`start_date` after
  that cache's own snapshot date; of those, the only tram/metro/rail
  relations affected are TER P53 (Hauts-de-France) in 2022 and Transilien
  K/TER K15 (Paris-Crepy-en-Valois-Laon) in 2024 -- neither overlaps any of
  the 5 test EPCIs. No known case, false-change figure or reported route
  changes; the expensive national precompute rebuild (distances are not
  read-only recoverable from the cached scalar tables; re-deriving them
  would cost as much as the earlier ~40-minute ways.parquet rebuild) was
  not run, since this bounded check already proves it would not matter.
- 2026-10-14, step 0 Merignac airport branch confirmed, added
  `bordeaux_tram_a_merignac_airport` (`type: pt_extend`, route `59`, opened
  2023-04-01) to `pt_changes.yaml`'s `confirmed` list, recording that tram A
  ended at Merignac Centre on 1 Jan 2022 and the airport branch is kept in
  the 2024 state, with the OSM-tagged-before-opening data gap noted.
  `PtChange` gained an optional `notes` field (mirroring
  `PtChangeCandidate`) for this kind of methodological caveat. Open
  limitation: `removed_route_keys()` still treats every confirmed change
  the same way, regardless of `type` -- for a `pt_new_line` the whole route
  is correctly absent before `opened`, but for a `pt_extend` it is *also*
  fully removed rather than trimmed to its pre-extension stops; the actual
  partial trim is expected to come from the calibration's own `cut`
  start/end indices once the (not yet built) scenario engine applies
  network edits, not from this simplified route-level sensitivity helper.
- 2026-10-14, step 0 tram and metro thresholds confirmed, removed the
  blanket `TODO(confirm)` from `config/gtfs_rebuild.yaml`; `tram`
  (`r_m=25, k=1, theta=0.5, geometry_share=0.3`) and `metro` (`r_m=25,
  k=2, theta=0.5, geometry_share=0.7`) are confirmed with their known-case
  and false-change evidence recorded inline. `bus`, `ferry` and `rail` keep
  a per-family `TODO(confirm)` comment stating they are screening/review
  only and never applied automatically; `rail` additionally notes it
  reuses metro's values for screening only (section 5.6 has no labelled
  rail known case).
- 2026-10-14, step 0 done. Method: match each 2026 route's main pattern by
  normalised ref/name first, then by covered-stop geometry (multiple tied
  relations, e.g. Bordeaux's old tram A onto 2026 lines E and F); verify
  coverage for tram, metro and rail against any in-service same-mode
  relation's track on that date, not only the identity match ("relations
  give identity, tracks give coverage"); for tram/metro/rail, cut uncovered
  end runs of length >= k before applying theta; bus and ferry are kept or
  dropped only. Bus, ferry and rail are never applied automatically
  (screening/review only, split into a coverage- and trip-ranked
  `to_review` and a `not_applied` list, plus a `rejected` list for
  reviewer-confirmed false positives); only `confirmed` edits reach a past
  state by default, with a `confirmed_and_candidates` sensitivity option.
  Known limitations: OSM sometimes tags a track as in service before its
  documented opening date (a genuine data gap patched case by case through
  `confirmed`, as for Merignac above, not detectable from tags alone when
  absent, as confirmed for Bordeaux tram A's 2022 ways); bus and rail OSM
  route-relation/way mapping is nationally incomplete, so their false-change
  rates stay non-trivial (bus/ferry ~70%, rail ~17%) regardless of
  parameters, which is why both remain manual-review-only rather than
  auto-applied. Final validation: Ruff clean; 197 tests pass, 2 pilot tests
  deselected.
- 2026-10-15, step 0 TCL Lyon rejections (reviewer check), the user
  reviewed `pt_changes.yaml`'s `to_review` candidates for `tcl_lyon` and
  confirmed that routes 112, 143, 49, 52, 68, 69, 7601, 77, 85, 98EX, C12,
  C18 and C26 existed long before 2022 (from 1910 to 2015); moved all 13
  from `to_review` to `rejected` with the note "existed before 2022
  (reviewer check)", so they are not re-surfaced on future reruns. One of
  them ("7601") is classified `mode=ferry` in the 2026 TCL Lyon GTFS feed,
  not bus, an unrelated upstream data-quality quirk noted but not changed.
- 2026-10-15, `network_coverage_by_date` investigated (not a bug), the
  user flagged that this field showed the identical ratio for 2022 and
  2024 for every `tcl_lyon` candidate (0.917738 both dates). Traced
  through `network_relation_coverage` (relation_pipeline.py) and the
  underlying per-date `evaluate_networks`/`evaluate_cached_grid` SQL: both
  already key every computation by `date_key`, confirmed by inspecting the
  cached pickle directly -- 9 of TCL Lyon's 389 routes have a *different*
  matched relation id or outcome between 2022 and 2024, but the network's
  overall matched-route *set* (357 of 389) is identical in both years at
  bus's then-chosen r_m=100 m (a generous radius at which OSM relation
  *presence* for a long-mapped network barely shifts in two years, even
  though which specific relation wins differs). Every other network
  (tbm_bordeaux, lio_occitanie, sete_agglopole, sncf, star_rennes) already
  shows genuinely different coverage between dates, confirming the
  computation is correct and the identical TCL figure is a real property
  of a stable network, not a caching or date-mixing bug -- consistent with
  the user's own finding (above) that several TCL routes long predate
  2022. No code change was needed for this point; the existing
  `test_network_relation_coverage_is_the_matched_share_per_network_date`
  regression test already proves per-date independence with routes that
  differ between dates.
- 2026-10-15, bus/ferry outcome rule replaced with fixed match shares (no
  calibrated theta), section 5.6 point 2: a name match covering >=50% of a
  route's stops is `kept`; a name match below 30% is treated as a homonym
  (a coincidental ref/name match, not the same line) and discarded so the
  geometry pass can find the real relation instead; a geometry match
  reaching >=50% is `kept-renamed`; otherwise `dropped`. A name match in
  the ambiguous 30-49% zone is *not* rescued by geometry (literal reading
  of the rule: only a match that itself reaches 50%, or a homonym's
  geometry fallback, can avoid `dropped`) -- proven by
  `test_bus_name_match_in_the_ambiguous_zone_is_dropped_without_geometry_rescue`.
  BHNS/express buses (Bordeaux Express G/H, Sete A) are unaffected, since
  they are verified like a tram via the pre-existing cut-then-theta path,
  not this rule -- *however*, Sete's route A has `is_bhns=False` in the
  2026 GTFS feed (its short/long name is "A"/"Ligne A", containing none of
  the `classify_bhns` keywords `express`/`bhns`/`liane`/`chronobus`), so it
  already went through the regular bus rule under both the old and the new
  system; its 2024 known-case check already disagreed before this fix too
  (covered_share reached 0.9-1.0 via geometry, `kept-renamed` instead of
  the expected `dropped`), a pre-existing OSM/ground-truth gap unrelated to
  today's change. Its removal from the 2026-to-past-state mapping is
  unaffected either way, since it is in `confirmed`, applied regardless of
  calibration scoring. Bus/ferry no longer calibrate `theta`/`k` at all (a
  grid search over them now always ties, since the SQL no longer consults
  either for their outcome); `calibrate_relations`'s grid loop still
  iterates them unchanged for shared-code simplicity, but
  `config/gtfs_rebuild.yaml`/the report now write `theta`/`k` as `null`
  for bus and ferry rather than the grid's arbitrary tie-broken value.
  Lyon's 2023 TCL network renumbering (new route numbers reusing OSM
  relations of long-standing lines) is the motivating real-world example
  of why geometry-based rename detection matters even for buses, not just
  trams.
- 2026-10-15, ferry coverage uses member stops/piers only, within a fixed
  200 m, never ways (section 5.6 point 3): way-based distances are now
  excluded from the precompute entirely for `mode=ferry` patterns, and the
  member-stop distance bound is widened to `max(r_m grid max, 200 m)` so
  real pier connections beyond the bus/tram/metro radii are not silently
  dropped; the 200 m check applies regardless of the grid's own `r_m`.
  This is a precompute-level (not just evaluation-level) change -- the
  cached `relation_distances.parquet` must be rebuilt, since it does not
  retain whether a cached distance came from a way or a member stop.
  Bumped `_CACHE_VERSION` to 4 to force this. Proven by
  `test_ferry_coverage_uses_member_piers_not_ways_within_a_fixed_200m`
  (a relation with a 0 m decoy way and 150 m piers is covered via the
  piers; a relation with a 0 m decoy way and 5 km piers is never a match).
- 2026-10-15, bus/ferry review list simplified (section 5.6 point 4):
  `to_review` now keeps every BHNS/express candidate plus every candidate
  dropped (on any date) under the new fixed rule above, ranked by trips,
  with no cap and no network-coverage eligibility gate (both removed,
  since the fixed rule already filters out weak matches); everything else
  (kept-renamed, non-BHNS, never dropped) goes to `not_applied`. Rail
  keeps its separate 90%-coverage gate and top-30-by-trips cap unchanged,
  since it has no BHNS concept and is always screening-only like bus.
  `network_coverage_by_date` is still recorded on every candidate as
  context even where it no longer gates bus/ferry eligibility.
- 2026-10-15, validation: all four fixes above were proven on synthetic
  fixtures (`tests/mobgrid/pt/test_relation_pipeline.py`,
  `tests/mobgrid/pt/test_pt_cli.py`) and smoke-tested on real cached data
  via a `--networks sete_agglopole` subset `calibrate` run (completed in
  about 1m40s, well under the 2-minute budget) before being handed off;
  the national re-score itself was *not* run (it needs a full precompute
  rebuild -- ways/relations parsing over the full national caches, ~40
  minutes, same order as the earlier busway/lanes_bus rebuild -- a genuine
  long job per policy, left for the user to run with the same `calibrate`
  command as before). Final validation: Ruff clean; 202 tests pass, 2
  pilot tests deselected.
- 2026-10-15, PT openings CSV (`config/French transit openings 2022 to
  2026.csv` -- the user's "pt_openings_2022_2026.csv" refers to this
  file, read-only, never edited) used to extend step 0's known cases and
  `pt_changes.yaml`. Scope narrowed on review (87 high/medium-confidence
  rows span 42 networks nationwide, far beyond the 8 networks step 0 has
  GTFS data for): mapped now only (a) the pilot area (INSEE department 33
  Gironde + 50 km halo, from `config/pilot.yaml`) and (b) the step-0 test
  areas needed for known cases (Lyon, Rennes/Paris metro); the remaining
  ~41 networks are deferred (see the open point below).
- 2026-10-15, real-GTFS correction to `bordeaux_tram_a_airport`: the
  openings CSV's row NAQ-12 describes tram A's Dec 2025 restructuring to a
  single terminus at each end, transferring its airport and Floirac
  Dravemont branches to F and E. Checked the cached GTFS extract directly
  (real terminal stop names of route 59's trips): its 2026 main pattern is
  Le Haillan Rostand <-> La Gardette-Bassens-Carbon-Blanc and never reaches
  the airport at all (not even as a minor variant) -- the former known
  case tested a scenario that no longer matches the feed. Renamed/fixed it
  to `bordeaux_tram_a_restructuring` (expected kept/kept, A's core predates
  2022 unchanged) and corrected `pt_changes.yaml`'s
  `bordeaux_tram_a_merignac_airport` confirmed edit from `route_ids: ['59']`
  to `['164']` (tram F, which carries the airport branch in the 2026
  feed), since the manual override for the OSM 2022 data gap must target
  the route that actually reaches the airport. Added
  `bordeaux_tram_c_blanquefort_branch` (NAQ-13, kept/kept: C's Blanquefort
  branch also moved to E, C's own remaining core is unaffected).
- 2026-10-15, new known cases from the pilot area and Lyon (point 1),
  reasoned per row rather than applying the remove/keep/modify mapping
  guide literally where it does not fit the route-level, end-cut-based
  outcome model: "new_station" events (a single infill stop, not an
  endpoint) and purely service-level rebrands do not trigger `cut` (only a
  contiguous uncovered *end* run does), so they are expected `kept`/`kept`
  at the route level even where the CSV's per-stop state is "remove" for
  that one stop. Added: `bordeaux_ter_42_le_verdon` (NAQ-02 + NAQ-10,
  TER 42/route L42+F42, kept/kept), `bordeaux_ter_41_arcachon` (NAQ-04,
  TER 41/F41+F41+, kept/kept), `bordeaux_ter_13_angouleme` (NAQ-06,
  TER 13/L13, kept/kept), `niort_saintes_royan_17` (NAQ-07, TER 17/L17+D17,
  a stop of which falls inside the Gironde+50km halo; kept/kept, confirms
  the baseline), `lyon_metro_b_extension` (ARA-02, cut/kept, a normal
  extension), `lyon_tram_t4_feyssine` (ARA-11, confidence low, single
  press source, inferred to reuse existing T1 track; kept/kept). Checked a
  further three Nouvelle-Aquitaine rail corridors (TER 18 Angouleme-
  Limoges, TER 25 Felletin, TER 57 Aurillac-Brive) against the actual
  buffered Gironde+50km polygon: none have a stop inside it, so none were
  added. `ARA-07`/tram T6 and all four Paris-metro/Rennes-metro rows
  already matched the existing known cases exactly (state values agree
  with `expected_2022`/`expected_2024`); no duplicates were added.
  `BRE-03` (a line-b suspension entirely within 2024, not spanning either
  reference date) is subsumed by the existing `rennes_metro_line_b` case
  for the same route id and was not added separately. Rail gained its
  first-ever labelled known cases (previously 0/0); metro and tram each
  gained one net-new case plus two renamed/corrected ones for Bordeaux.
- 2026-10-15, reusable openings-to-GTFS mapping tool (point 2), added
  `packages/mobgrid/pt/pt_openings.py` and a `mobgrid.pt.cli map-openings`
  command: for one GTFS resource and a network-name substring filter,
  proposes candidate 2026 route id(s) per opening row by normalised line
  code (stripping `TER`/`RER`/`Ligne` prefixes, keeping just the code
  token, e.g. "TER 42 Bordeaux - Pointe-de-Grave" -> "42") and GTFS mode
  family, falling back to a restricted (never the shared extraction, never
  the whole feed) `section_from`/`section_to` stop-name check when several
  distinct corridors share a code or mode (for example two different rail
  lines both coincidentally named "C"). Writes
  `config/pt_openings_mapping.csv` (merging by `opening_id`, never
  discarding other networks' rows) with a `match_confidence` column
  (`exact`/`stop-confirmed`/`ambiguous`/`none`); never writes to
  `pt_changes.yaml` itself. Tested on Bordeaux (resource 83024, `--network-
  contains TBM`): 6 of 7 rows matched `exact` (A/C/E/F trams, Express G),
  correctly including both mission-code variants of the same corridor
  (`L42`+`F42`) as one match; Express H matched `ambiguous` with exactly
  the right two circular-direction route ids (`911`/`912`, refs `H1`/`H2`)
  -- confirming the existing `bordeaux_bus_express_h` confirmed edit is
  correct, and NAQ-01's airport branch correctly resolved to route `164`
  (F), independently corroborating the correction above. A single-letter
  code needed a dedicated "prefix, not bare substring" tier (`H` matching
  `H1`/`H2` but not an unrelated route whose long name merely contains the
  letter "h") -- covered by
  `test_single_letter_code_matches_numbered_circular_variants_by_prefix`.
  Within today's narrowed scope (pilot area + Lyon/Rennes/Paris metro),
  every row mapped successfully; nothing is in `pt_changes.yaml`'s
  "could not map" sense for this batch. Most of the resulting
  tram/metro/rail matches do not need a new `pt_changes.yaml` confirmed
  entry at all: only bus/BHNS and the one OSM-data-gap override need a
  manual edit, since tram/metro/rail changes are otherwise auto-applied
  through the calibrated cut logic (the existing `confirmed` list already
  had only 4 entries, none of them plain extensions).
- 2026-10-15, open point for the national PT step: `config/French transit
  openings 2022 to 2026.csv` has 87 high/medium-confidence rows across 42
  networks; only the pilot area and step-0 test-area rows were mapped
  today. Run `mobgrid.pt.cli map-openings` network by network for the
  remaining ~41 networks (Strasbourg CTS, Nancy STAN, Montpellier TaM,
  Nantes Naolib, Marseille RTM, Toulouse Tisseo, Caen Twisto, Brest Bibus,
  Grenoble SMMAG, Nice tramway, and the other regional TER feeds), review
  each network's `config/pt_openings_mapping.csv` proposals (especially
  anything `ambiguous`/`none`), and only then add the confirmed ones to
  `pt_changes.yaml`. Also open: 8 CSV rows have `state_2022` or
  `state_2024` equal to `add` (a line/section that closed before 2026, so
  it has no counterpart in the 2026 GTFS feed at all and cannot be scored
  as a known case): ARA-09 (TER 67 Aurillac-Brive, 2026 planned works
  closure), GES-02 (Nancy tram line 1, TVR withdrawn Mar 2023), HDF-03
  (TER P64 Laon-Hirson, suspended Dec 2023), IDF-05 (RER C Massy-
  Epinay-sur-Orge, replaced by T12 Dec 2023 -- `state_2024` is "keep", so
  only its 2022 state is affected), NAQ-09 (Busseau-Felletin, closed Sep
  2025), NOR-02 (Serqueux-Gisors, closed Jul 2024), NOR-03 (Le Havre-
  Montivilliers Lezarde branch, closed Sep 2024), OCC-09 (Toulouse tram T2,
  withdrawn Jun 2023). For each, decide per network whether to rebuild the
  missing service from its OSM route relation with an estimated frequency,
  or leave it out of `n` and report the gap -- not decided here.
  `planned_not_open` rows (18 total, all `keep`/`keep`) need no past-state
  action by design and are left for the scenario engine (section 11).
- 2026-10-15, step 0 re-score pending: adding the known cases above (and
  the `pt_changes.yaml` fix) only changes `config/gtfs_rebuild.yaml`/
  `config/pt_changes.yaml` content, which the top-level calibration
  signature already covers -- but the cached relation-table precompute was
  bumped to `_CACHE_VERSION = 4` by the same-day ferry/bus fix earlier,
  so it is already invalid pending that fix's own full national recompute
  (handed off previously, not yet run by the user); a local, in-budget
  re-score was not attempted a second time today for the same reason.
  Tram/metro thresholds in `config/gtfs_rebuild.yaml` are unchanged by
  today's edits and remain confirmed. The exact command to run (identical
  to the one already given, since both days' changes are covered by the
  same cache-invalidation and will rebuild together) is repeated in the
  final chat response; its output's known-case table and false-change
  rates should be read back for the final report once it completes.
- 2026-10-15, step 0 national recompute finalized, the user ran the
  full national `calibrate` command handed off above
  (`logs/2026-10-15_gtfs_calibration.log`/`_summary.md`); 1,294
  route/date outcomes scored, one flagged network/date pair
  (`star_rennes` 2022-01-01, below 50% OSM relation coverage, retained
  `not-testable`). Results, regenerating `config/gtfs_rebuild.yaml`,
  `config/pt_changes.yaml` and `docs/data/step0_gtfs_rebuild.md`:
  - bus: known 7/10, false-change 29.23% (`r_m=100`, fixed-share rule,
    `k`/`theta` null -- screening only, never auto-applied).
  - ferry: known 7/10, false-change 29.23% (reuses bus's parameters and
    known cases, `k`/`theta` null -- screening only, never auto-applied).
  - metro: known 11/11, F1 1.00, false-change 20.00% (`r_m=25, k=2,
    theta=0.5, geometry_share=0.3`, down from the former 0.7 now that
    the known-case set also covers the Lyon metro B and Paris metro
    4/12 extensions) -- **confirmed**.
  - rail: known 0/6, false-change 20.74% (reuses metro's parameters for
    screening only; every Nouvelle-Aquitaine TER known case -- Bordeaux
    TER 42/41/13 -- is obtained as `kept-renamed` instead of the
    expected `kept`, a genuine OSM rail-relation-naming gap, not a
    parameter issue -- screening only, never auto-applied).
  - tram: known 12/12, F1 1.00, false-change 0.00% (`r_m=25, k=1,
    theta=0.5, geometry_share=0.3`, now including the Lyon T4/T6 and
    Bordeaux tram C/E/F cases) -- **confirmed**.
  `config/gtfs_rebuild.yaml`'s blanket `TODO(confirm)` header (rewritten
  by the `calibrate` CLI on every run) was replaced again with the
  per-family comments above: tram and metro marked confirmed with their
  evidence inline; bus, ferry and rail keep a per-family `TODO(confirm)`
  stating they are screening/review only. `to_review` holds 180
  candidates (every BHNS/express bus/ferry route, plus every bus/ferry
  route dropped under the fixed name/geometry-share rule, with no cap;
  rail keeps its own 90%-coverage gate and top-30-by-trips cap); 340
  more are `not_applied` (kept as evidence, never auto-applied). Step 0
  is complete: Ruff clean; 211 tests pass, 2 pilot tests deselected.
- 2026-10-15, step 0 national policy (user-directed change of approach,
  no manual review): the goal becomes a national model, so the per-family
  OSM-calibrated automatic rule above is retired for every family except
  tram. Metro, rail, bus and ferry (including BHNS/express, whose own
  automatic cut rule is retired too -- it now follows bus's own policy)
  keep every 2026 route in both past states by default, changed only by
  the PT openings list's auto-applied matches. Metro's calibration (known
  11/11, false-change 20.00%) is not investigated further, per the user's
  explicit instruction, even though it scored well; it is kept in
  `config/gtfs_rebuild.yaml`/the report as a historical/screening
  reference only, like bus/ferry/rail's own numbers.
  - **Precedence** (section 5.6 point 7): openings list > tram automatic
    rule > default keep, implemented as
    `mobgrid.pt.pt_policy.resolve_route_presence(family_rule,
    opening_removed, tram_rule_removed)`, a pure function with its own
    `tests/mobgrid/pt/test_pt_policy.py` (6 tests: openings override wins
    both ways and for every family; the tram rule is only consulted for
    `family_rule="automatic_osm"`, never for a default-keep family even if
    a caller passes a value for it; default keep when no source has an
    opinion).
  - **Openings-list auto-application** (point 4): `OpeningDerivedChange`
    (`pt_changes.py`) is a new model distinct from the manually-written
    `PtChange` -- it reads `state_2022`/`state_2024` directly from the CSV
    (`keep`/`remove`/`modify`) rather than a single `opened` date, since a
    `modify` row (a restructuring, not a clean creation) has no such date;
    `modify` is treated the same as `remove` (absent), reusing the
    existing `pt_extend`-vs-full-removal caveat already documented for
    manual edits. `PtChangeCatalogue` gained a `from_openings` list, read
    by `removed_route_keys` alongside `confirmed`; the former
    `sensitivity="confirmed_and_candidates"` option (which read
    `to_review`/`not_applied`) is removed outright, since it directly
    contradicted the new point 6 (see below). `mobgrid.pt.pt_openings
    .apply_openings_matches(openings_csv, mapping_csv)` applies a row only
    when its own CSV `confidence` is high/medium *and* its mapped
    `match_confidence` is exact/stop-confirmed *and* it resolves to
    exactly one 2026 route id; every other row becomes one log line
    (`mobgrid.pt apply-openings`, a new CLI command, logs each via the
    standard run log -- `logger.warning` for not-applied rows,
    `logger.info` for known gaps -- rather than a bespoke log file format).
    `write_from_openings` merges the result into `config/pt_changes.yaml`'s
    `from_openings`, replacing it wholesale each run (unlike
    `to_review`/`not_applied`, the openings CSV describes one ground
    truth per route, not evidence to accumulate across reruns).
  - **Multiple openings rows per 2026 route, found on real data:**
    Bordeaux tram F (route 164) has two openings rows matched to it --
    NAQ-01 (the 2023 Mérignac-airport branch, `state_2024="keep"`) and
    NAQ-15 (route F's own Dec 2025 restructuring joining several old tram
    A corridors, `state_2024="modify"`) -- that disagree about 2024.
    `removed_route_keys` resolves this conservatively: the route counts as
    removed at a state date as soon as *any* `from_openings` entry says so
    (an OR across entries), which happens to be the technically correct
    call here (route F in its 2026 form genuinely did not exist by Jan
    2024, since the whole-line restructuring was Dec 2025, even though
    NAQ-01's own narrower claim about just the airport branch is "keep").
    Documented as a deliberate, tested simplification (a dedicated test in
    `test_pt_changes.py`), not an oversight; a future CSV update that ever
    pairs `add` with `remove`/`modify` in the same row's two states would
    need re-examining (not observed in the current 120-row CSV: every
    `add` only ever pairs with `keep` or `add`).
  - **Closed-before-2026 rows** (point 5, CSV `state` `add`): 8 rows
    (IDF-05, ARA-09, GES-02, HDF-03, NOR-02, NOR-03, NAQ-09, OCC-09) have
    no 2026 GTFS counterpart at all; `apply_openings_matches` excludes the
    whole row from both `applied` and the ambiguous/none log, returning it
    separately as `closed_before_2026`, rendered in the report as a named
    "known gap" list (not folded into the generic not-applied log, since
    the reason is structural, not a matching failure).
  - **Ran for real** (fast, no GTFS downloads needed, since
    `config/pt_openings_mapping.csv` already had the 7 TBM Bordeaux rows
    mapped on 2026-10-15 earlier): `uv run python -m mobgrid.pt
    apply-openings` applied 6 of 7 (NAQ-11, a circular H1/H2 BHNS pair, is
    still `ambiguous`), logged 106 not-applied rows and 8 known gaps.
  - **`config/gtfs_rebuild.yaml`** gained a `national_policy` section
    (new `NationalPolicy`/`FamilyPolicy`/`OpeningsListPolicy` Pydantic
    models in `config.py`, optional/`None` by default so every existing
    test fixture that builds a bare `GtfsRebuildConfig` still validates)
    recording the decision date, precedence and per-family rule; `chosen`'s
    per-family comments were updated in place (metro/bus/ferry/rail marked
    "retired, historical reference only"; tram unchanged, still
    confirmed/applied).
  - **Report** (`report.py`/`docs/data/step0_gtfs_rebuild.md`): regenerated
    from the *existing* calibration pickle (no recalibration -- the user
    said to stop that work) with new "National policy" and "PT openings
    list: applied changes and known gaps" sections at the top (the latter
    calls `apply_openings_matches` live, so it always reflects the current
    CSV/mapping state); the old calibration sections are relabelled
    "historical reference"/"informational only" throughout rather than
    removed, since they still document how the retired numbers were
    produced and remain useful screening evidence.
  - **Mapping all networks** (point 4's "for all networks"): only
    TBM Bordeaux (1 of 47 high/medium-confidence networks) has been
    mapped so far; running `map-openings` network by network for the
    remaining 46 is a genuine long job (each needs its GTFS resource
    downloaded/extracted) and was not run, per policy. Of those 46, 9
    share IDFM's already-configured resource (80921: `IDFM`, `RATP
    (IDFM)`, `RATP; Société des grands projets (IDFM)`, `Société des
    grands projets (IDFM)`, `Stretto (Keolis + SNCF) (IDFM)`, `Keolis
    Tisse (IDFM)`, `SNCF Voyageurs (IDFM)`, `SNCF Voyageurs / SNCF Réseau
    (IDFM)`, `IDFM (operator Transdev per Wikipedia)`), 14 share SNCF's
    already-configured resource (83582: every `TER ...` row except `TER
    Occitanie (liO)`, plus `SNCF Réseau / RFI; TER Auvergne-Rhône-Alpes`),
    and 3 more match an existing `networks` entry exactly (`SAM (Sète
    Agglopôle Méditerranée)` -> `sete_agglopole` 81575, `STAR (Rennes
    Métropole)` -> `star_rennes` 83281, `TCL (SYTRAL Mobilités)` ->
    `tcl_lyon` 81943) -- all resolved by exact/substring matching on
    already-known, human-confirmed resource ids, not guessed. `TER
    Occitanie (liO)` is ambiguous between `lio_occitanie` (81026) and
    `sncf` (83582) and needs a human decision. The remaining 19 networks
    (Aix-Marseille-Provence/Lebus+/RTM, Bibus, CTS, Citézen, Filibus,
    Geneva tram 17, Grand Reims Mobilités, Irigo, Le Met', M réso, Naolib,
    Péribus, STAN, T2C, TaM, Tisséo, Twisto) have no configured resource id
    yet; automated fuzzy name matching against `config/gtfs_inventory.csv`
    only found weak, unreliable candidates for these (not applied, to
    avoid silently guessing a wrong resource id), so they need a human to
    pick the correct `resource_id` from `config/gtfs_inventory.csv` before
    `map-openings` can run for them. The exact commands for the resolved
    networks are given in the final chat response.
- 2026-10-16, step 0 openings-list application fix (user-reported: the
  2026-10-15 rule would have deleted whole lines nationally). Two errors
  fixed:
  1. **Fall-through, not removal, for `keep`/`modify`** (point 1):
     `OpeningDerivedChange.instruction_at` now returns `None` (no
     instruction) whenever a state is `keep` or `modify`, regardless of
     `change_type` -- only `remove` ever produces an instruction. The
     2026-10-15 version treated `modify` the same as `remove`, which
     would have deleted Bordeaux trams A/C/E/F, Grenoble D, Clermont B/C
     and Lyon T4/TB11/C27 nationwide (all real restructuring/renaming/
     relocation rows describing a line that already existed in another
     form). `add` is unaffected, still a reported gap (point 5's existing
     logic).
  2. **`remove`'s effect depends on `change_type`** (point 2):
     `instruction_at` maps `new_line`/`reopening` + `remove` to `drop`
     (whole route absent); `extension` + `remove` to `cut` (keep the
     stops up to `section_from`, the old terminus, drop the stops toward
     `section_to`); `new_station` + `remove` to `new_station` (remove
     only that one stop, named in `section_from`). Every other
     `change_type` (`restructuring`, `renaming`, `relocation`,
     `suspension`, `closure`) gives no instruction even if its state
     happens to be `remove` (5 real `suspension` rows do this -- see the
     assumption below) -- logged via `unhandled_remove_at` rather than
     guessed. New module `packages/mobgrid/pt/route_edits.py` resolves
     `cut`/`new_station` edits against a route's ordered stop names:
     `resolve_route_edits` narrows a kept index range (`cut`, anchored
     by matching `section_from`/`section_to` against stop names,
     direction-agnostic) and an excluded-index set (`new_station`); an
     edit whose anchor(s) cannot be located is skipped and logged
     (`unresolved_opening_ids`), never guessed, and never blocks another
     resolvable edit on the same route. `collect_edit_specs` gathers every
     active `cut`/`new_station` across a catalogue's `from_openings` for
     one state, grouped by `(network, route_id)`.
  3. **Combine, not OR, per route/state** (point 3): `removed_route_keys`
     now only treats a `drop` instruction as removal; `cut`/`new_station`
     edits from several rows on the same route combine (narrow the same
     kept range further) rather than any one of them individually
     deleting the route, replacing the 2026-10-15 OR rule across entire
     `from_openings` entries (which is what made a restructuring row like
     Bordeaux tram F's NAQ-15 wrongly combine with NAQ-01's real cut into
     a full removal). Proven on the real metro 14 case (IDF-11 north
     extension + IDF-12 south extension, both `remove`/`remove` at both
     dates): both cuts apply together, the route is never dropped
     (`test_metro_14_two_extensions_combine_without_ever_dropping_the_route`,
     `test_metro_14_two_extensions_cut_both_ends_without_dropping`).
  4. **NAQ-11 (circular Bus Express H1/H2) reclassified `exact`, not
     `ambiguous`**: `propose_route_matches`'s prefix-match fallback (used
     for numbered/lettered variants of one code, e.g. `H` -> `H1`/`H2`)
     previously fell through to `ambiguous` whenever the generic stop-hint
     disambiguation failed to narrow -- which it always does here, since
     the CSV's `section_from`/`section_to` free text ("Cenon Gare
     (circular H1/H2)") is not a real GTFS stop name. Since every variant
     reached this way belongs to the one reported circular/directional
     service (not a genuine collision between unrelated lines), it is now
     `exact` with every variant's route id, not a human-reviewed
     `ambiguous`. `TODO(confirm)`: this widens the prefix-match
     heuristic's auto-apply surface slightly (a coincidental same-prefix,
     *different* line could misfire the same way); flagged as an
     assumption to check below, not blocking, since the heuristic's match
     pool (short prefix diff <= 2 characters) was already deliberately
     narrow.
  - **Real-data validation** (`resolve_route_edits` against the cached
    TBM Bordeaux GTFS, `data/interim/pt_openings_mapping/83024`, read-only,
    one-off check, not a committed test per the isolation rule): route
    164/F's main pattern (1,388 trips, Bègles <-> Aéroport) has 34 stops;
    NAQ-01's cut (anchor "Carrefour des Quatre Chemins (Mérignac)" ->
    "Mérignac Aéroport") resolves cleanly to 29 kept stops, dropping
    exactly the 5 new stations the CSV's own notes list (Mérignac Soleil,
    Chemin Long, Cadera-Issartier, Caroline Aigle, Aéroport) -- confirms
    the engine's bidirectional stop-name containment match and direction-
    agnostic cut logic against ground truth.
  - **Redid the Bordeaux application** (`uv run python -m mobgrid.pt
    apply-openings` after the fix, and `mobgrid.pt map-openings` rerun for
    TBM to pick up the NAQ-11 reclassification): 8 applied (up from 6:
    911 and 912 now both resolve), 105 not applied, 8 known gaps. Result,
    matching the table given by the user: 1 Jan 2022 -- A (59), C (61), E
    (163) kept (restructuring rows give no instruction); F (164) cut at
    "Quatre Chemins" (NAQ-01's `extension`); G (901), H1 (911), H2 (912)
    dropped (`new_line`). 1 Jan 2024 -- A, C, E kept; F has no active
    openings instruction (falls through to the tram automatic rule,
    i.e. the confirmed OSM-based cut/keep result applies); G, H1, H2
    dropped. Proven in
    `tests/mobgrid/pt/test_pt_openings.py::test_bordeaux_real_rows_match_the_documented_outcomes`,
    reading only the two committed CSVs (the openings CSV and
    `pt_openings_mapping.csv`), never `data/interim`, so it is isolated
    and deterministic.
  - **Retired a now-conflicting legacy manual edit**: `config/
    pt_changes.yaml`'s `confirmed` list had a 2026-10-14-era
    `bordeaux_tram_a_merignac_airport` (`type: pt_extend`, route `164`,
    opened 2023-04-01) entry -- the same real-world fact as NAQ-01, but
    using the coarser pre-openings-list mechanism (full route removal,
    not a precise cut). With `removed_route_keys` ORing `confirmed` and
    `from_openings` drops together, this legacy entry would have kept
    route 164 wholly absent at 2022 regardless of the fix, contradicting
    "F cut, not dropped". Removed it now that the openings list derives
    the same fact more precisely; `bordeaux_bus_express_g`/`_h` (routes
    901/911/912) are left as-is, since they duplicate but do not
    conflict with NAQ-08/NAQ-11 (both mechanisms agree: drop).
    **Fixed (2026-10-16 follow-up):** `confirmed` (keyed by the project's
    own `networks:` slugs, e.g. `tbm_bordeaux`) and `from_openings` (keyed
    by the CSV's raw `network` string, e.g. `TBM (Bordeaux Métropole)`)
    used to mix two different, never-reconciled network-naming
    conventions within the same `removed_route_keys()` result set.
    `removed_route_keys` now takes a `network_resource_ids` mapping (built
    by `mobgrid.pt.pt_changes.build_network_resource_ids`, merging
    `GtfsRebuildConfig.networks` slugs with
    `national_policy.openings_list.network_resource_ids`, plus an optional
    `mode_split_network_resource_ids` for `"TER Occitanie (liO)"`) and
    returns `(GTFS resource id, route_id)` keys throughout, so the same
    physical network is counted once regardless of which source named it.
    Tested in `tests/mobgrid/pt/test_pt_changes.py
    ::test_removed_route_keys_counts_same_route_once_from_both_conventions`.
    `mobgrid.pt.route_edits.collect_edit_specs` still keys its
    `cut`/`new_station` edits by `from_openings`'s own raw CSV network
    string (a single source, so no mixing risk there) -- left as-is.
  - **Resolved the 19 unresolved networks from point 5** (a lookup over
    `config/gtfs_inventory.csv`'s dataset title/AOM/agency-name columns,
    no download): all 45 single-resource networks plus the IDFM (9) and
    SNCF (14) groups are now recorded in `config/gtfs_rebuild.yaml`'s
    `national_policy.openings_list.network_resource_ids`. Evidence
    (dataset title | agency name | EPCI):

    | Network | Resource id | Evidence |
    |---|---:|---|
    | Aix-Marseille-Provence / Lebus+ (...) / RTM (...) | 81969 | "Réseaux urbains de la Métropole Aix-Marseille-Provence", bundling every AMP sub-network (Marseille, Aubagne, Gémenos, ...) in one resource -- covers all three CSV network strings (RTM's Marseille rows, Lebus+'s Aubagne/Gémenos/Miramas rows) without picking one sub-area resource |
    | Bibus (Brest Métropole) | 43286 | "Réseau urbain Bibus", agency "Bibus"/"TAD Bibus", EPCI Brest Métropole |
    | CTS (Eurométropole de Strasbourg) | 79220 | "Réseau urbain CTS", agency "CTS", EPCI Eurométropole de Strasbourg |
    | Citézen (SMiTU Thionville-Fensch) | 80459 | "Réseau urbain TeMo'b", agency "Keolis Thionville Fensch", EPCI CA Portes de France-Thionville (matches the CSV row's city: Thionville/Hayange/Yutz) |
    | Filibus (Chartres métropole) | 80587 | "Réseau urbain Filibus", agency "Filibus", EPCI CA Chartres Métropole |
    | Geneva tram 17 (Annemasse Agglo / ...) | 76779 | "Réseau urbain TAC Mobilité", agency "TAC Mobilités", EPCI CA Annemasse-Les Voirons-Agglomération (matches the CSV row's city: Annemasse) |
    | Grand Reims Mobilités | 80594 | "Réseau urbain Grand Reims Mobilités", agency "Transdev Reims", EPCI CU du Grand Reims |
    | Irigo (Angers Loire Métropole) | 80036 | "Réseau urbain Irigo", agency "IRIGO", EPCI CU Angers Loire Métropole |
    | Le Met' (Eurométropole de Metz) | 80725 | "Réseau urbain Le Met'", agency "LE MET'", EPCI Metz Métropole |
    | M réso (SMMAG) | 83459 | "Réseau urbain TAG", agency "M Réso - Métropole Grenobloise" (TAG is the old brand name), EPCI Grenoble-Alpes-Métropole |
    | Naolib (Nantes Métropole) | 84101 | "Réseau urbain Naolib", agency "Naolib", EPCI Nantes Métropole |
    | Péribus (Grand Périgueux) | 82357 | "Réseau urbain Péribus", agency "Périmouv (Grand Perigueux)", EPCI CA Le Grand Périgueux |
    | STAN (Métropole du Grand Nancy) | 83710 | "Réseau urbain Stan", agency "STAN Nancy", EPCI Métropole du Grand Nancy |
    | T2C (SMTC Clermont) | 83465 | "Réseau urbain T2C", agency "T2C", EPCI Clermont Auvergne Métropole |
    | TaM (Montpellier Méditerranée Métropole) | 84199 | "Réseau urbain TaM", agency "TaM", EPCI Montpellier Méditerranée Métropole |
    | Tisséo | 81678 | "Réseau urbain Tisséo", agency "Tisséo" |

    **TER Occitanie (liO)** resolved by mode (point 5's rule): all three
    of its CSV rows (OCC-05, OCC-13, PLN-13) are `mode=rail`, so every one
    resolves to SNCF's resource (83582); recorded generically in
    `mode_split_network_resource_ids` (rail -> 83582, bus/bhns/trolleybus
    -> 81026/`lio_occitanie`) so a future CSV update adding a genuine
    liO coach row is still handled correctly, not hard-coded to today's
    all-rail reality. New `mobgrid.pt.pt_openings.run_mapping_grouped`
    resolves each row only against its own mode's resource, writing one
    merged `write_mapping_csv` call so neither mode group's run can
    overwrite the other's result for a different row.

    **Twisto (Caen la mer)** was initially left as a logged gap here
    (no dedicated GTFS resource found in `config/gtfs_inventory.csv`,
    only the Normandy regional aggregate); investigated 2026-10-16 (see
    the decision entry below) and resolved by mapping it against the
    existing Normandy aggregate (resource 81942), not by acquiring a
    second, dedicated feed.
  - **New batch command** `mobgrid.pt map-and-apply-all`: iterates every
    configured `network_resource_ids`/`mode_split_network_resource_ids`
    entry, resolving/extracting each resource (resumable: `extract_gtfs_
    tables` already skips files already present under
    `data/interim/pt_openings_mapping/<resource_id>`) and mapping it,
    logging and continuing past any one network's download/extraction
    failure rather than aborting the batch (`_run_map_and_apply_all`,
    tested in `tests/mobgrid/pt/test_pt_cli_map_and_apply_all.py` with a
    synthetic inventory where one of two resources is missing); finally
    runs `apply_openings_matches`/`write_from_openings` once. Writes
    `logs/{date}_pt_openings_map_and_apply_all.log` and `..._summary.md`
    per the long-job convention. **Validated for real** (fast, reused the
    already-cached TBM Bordeaux resource, `--networks "TBM (Bordeaux
    Métropole)"`, 0.1 minutes): mapped 1 network, applied 8 changes,
    identical result to the dedicated `map-openings`+`apply-openings`
    pair above. The full national run (remaining ~44 networks, each
    needing its own GTFS download/extraction) was not run, per policy;
    the exact command is given in the final chat response.
  - Ruff clean; 243 tests pass, 2 pilot tests deselected.
- 2026-10-16, Twisto (Caen la mer) acquisition gap investigated and
  national GTFS coverage checked (user follow-up to the three points
  above).
  1. **Root cause (not a discovery bug).** A full live dump of
     `GET https://transport.data.gouv.fr/api/datasets` (802 datasets,
     2026-10-16) contains no dataset for Twisto/Caen la mer at all.
     Twisto's actual GTFS (data.gouv.fr dataset
     `caen-la-mer-reseau-twisto-gtfs-siri-2`, id
     `68f1879c2c4ca61855ff1994`, resource `GTFS_twisto.zip`, id
     `71728bd6-b9a4-48e3-93ee-ac566e42fe99`, format zip, check:status 200
     as of 2026-07-19, ~4.3 MB) exists only on the *general* data.gouv.fr
     open-data catalogue, harvested there from Twisto's own portal
     (data.twisto.fr) -- it was never referenced with transport.data.
     gouv.fr's PAN (the national transport registry), which is the *only*
     catalogue `acquire.discovery.discover_gtfs` queries, by design
     (section 5.1: producer-owned GTFS resources from the national
     transport portal). `discover_gtfs`'s classification logic (format
     filter, community-resource exclusion, drop/override lists) is
     correct and unaffected; there was nothing in it to fix, because the
     dataset it needed to see was never in its input at all.
  2. **Correction of scope.** Caen la mer's network is *not* fully absent
     from the acquisition: "Twisto (Caen la mer)" already appears as one
     of 31 agencies inside the already-configured Normandy regional
     aggregate (resource 81942, valid 2026-09-30 to 2028-06-30, not
     expired). Only a *dedicated*, single-producer resource was missing
     -- exactly why the openings-list mapping work left it as a gap
     earlier (resolving one specific network against a 31-agency
     aggregate is unreliable), not because Caen has zero PT data in our
     acquisition.
  3. **Decision (2026-10-16 follow-up, superseding the paragraph below as
     first written): no dedicated feed is acquired.** Twisto's real
     producer feed (data.gouv.fr dataset
     `caen-la-mer-reseau-twisto-gtfs-siri-2`, resource `GTFS_twisto.zip`)
     was initially added to `config/sources.yaml` and a command was
     handed off to download it, but the user decided against this:
     Caen la mer is already covered by the Normandy aggregate, the same
     as 865 other AOMs nationally (point 5 below); acquiring a second,
     dedicated copy would duplicate its trips once a future PT-build step
     merges every network's feed into one multimodal network (see the
     2026-10-16 follow-up entry below for the new deduplication
     requirement this raised). The
     `config/sources.yaml` entry was **removed**. Instead, `Twisto (Caen
     la mer)` was mapped directly against the already-downloaded
     Normandy aggregate (`uv run python -m mobgrid.pt map-openings
     --resource-id 81942 --network-contains Twisto`, offline, fast; its
     one real row, NOR-01, line T3, matched `exact` to GTFS route
     `ATOUMOD029:Line:T3:LOC`) and `config/gtfs_rebuild.yaml`'s
     `national_policy.openings_list.network_resource_ids` gained
     `Twisto (Caen la mer): 81942` (so all 47 high/medium-confidence
     networks are now resolved, 0 remaining in `unresolved_networks`).
     `uv run python -m mobgrid.pt apply-openings` rerun: 9 applied (up
     from 8), `from_openings` now includes NOR-01 (`extension`, `remove`/
     `keep` -> `cut` at 2022, no instruction at 2024, matching the
     project's already-established cut-at-old-terminus rule).
  4. **Fix the cause, systematically**: added real, tested
     infrastructure (not a one-off script) to catch this whole class of
     gap -- a producer registered with the PAM registry whose own feed
     the PAN never sees -- for any French authority, not just Twisto.
     `acquire.discovery.discover_aoms` fetches the PAN's own AOM registry
     (`GET /api/aoms/geojson`, one metadata call, 1,148 AOMs with name/
     SIREN/department); `classify_aom_coverage` cross-references each
     AOM, offline, against `config/gtfs_inventory.csv`'s already-cached
     `covered_area`/validity columns (no new downloads), three ways: a
     `dedicated` resource (a valid resource's `covered_area` lists an
     `epci` entry whose INSEE code equals the AOM's own SIREN -- true
     for most urban AOMs, which are themselves the EPCI), `indirect`
     coverage only (a department- or region-level aggregate bundles it,
     like Twisto in the Normandy aggregate), or `uncovered` (nothing at
     any level). New `acquire --check-aom-coverage` CLI flag runs both
     steps and writes `config/gtfs_aom_coverage.csv`. Tested (13 new
     tests in `tests/acquire/test_discovery.py`), including a
     completeness check that the module's own department/region
     crosswalk (`_REGION_DEPARTMENTS`) exactly covers
     `AcquisitionConfig.metropolitan_departments`, so a typo in the
     hand-written crosswalk cannot silently misclassify a department.
  5. **National coverage result** (run for real, `--check-aom-coverage
     --reference-date 2026-10-13`, one live API call plus an offline
     cross-check against the existing inventory -- a few seconds, well
     within budget): of 1,127 metropolitan AOMs, **0 are uncovered at any
     level** -- every metropolitan authority has at least a region- or
     department-level aggregate covering it. 262 have their own dedicated
     resource; **865 (including Twisto) are covered only indirectly**,
     via a broader aggregate, with no dedicated producer feed of their
     own in our inventory. (13 overseas/DROM-COM AOMs are genuinely
     uncovered at any level, but overseas territories are out of this
     project's metropolitan-France scope, so this is not itself a gap to
     close.) 865 is expected and not itself alarming -- most small/rural
     AOMs are correctly served only by a regional aggregate, the same
     pattern already used deliberately for bus/rail/TER networks
     elsewhere in step 0 -- but it is not filtered by population, so it
     mixes genuinely-negligible small AOMs with any large urban ones that
     may be worth a dedicated feed.
  6. **No population filter (2026-10-16 decision).** Narrowing the 865
     "indirect only" AOMs by EPCI population was considered (it would
     have needed INSEE's ~25.6 MB commune-level population table, a
     genuine download-and-aggregate national computation, not run) but
     the user decided it is unnecessary: since 0 metropolitan AOMs are
     uncovered at any level (point 5), a population filter cannot change
     that headline finding -- it would only have ranked which
     indirect-only AOMs might be worth a dedicated feed, a question point
     3 above now answers directly (no: aggregate-only coverage is an
     accepted, normal outcome, not a gap to close, so there is nothing to
     rank). The draft filtering script was removed rather than kept
     unused. `config/gtfs_aom_coverage.csv` (the dedicated/indirect/
     uncovered classification itself) is kept, since it remains the
     useful, already-computed national coverage evidence.
  7. **Suspensions, decided (not an open assumption any more):** a
     `suspension`-change-type row paired with a `remove` state (5 real
     CSV rows, e.g. ARA-01 TER Chambéry-Modane) gives no instruction --
     the line is presumed kept for that state. A temporary works closure
     spanning part of the 2022-2024 window does not remove a line from a
     state meant to represent the *normal* network; `instruction_at`
     already implemented this (only `new_line`/`reopening`/`extension`/
     `new_station` ever produce an instruction), and this entry confirms
     it is deliberate, settled behaviour, not a pending question.
  8. **Offline guarantee made explicit.** `mobgrid.pt.pt_openings.
     resolve_and_extract` (used by both `map-openings` and
     `map-and-apply-all`) never downloaded anything to begin with --
     ``resolve_gtfs_local_path`` only reads the ``local_path`` already
     recorded by a prior ``acquire`` run, and extraction only opens that
     local file -- but it now raises a clear, specific
     ``FileNotFoundError`` naming the missing path and the ``acquire``
     command to run when a configured resource is not yet downloaded,
     instead of a generic error surfacing from inside ``zipfile``. Proven
     with `test_resolve_and_extract_never_attempts_a_network_call` (the
     module imports no network client at all) and two behavioural tests
     (reads an already-downloaded feed; raises the clear error otherwise)
     in `tests/mobgrid/pt/test_pt_openings.py`.
  - Ruff clean; 256 tests pass, 2 pilot tests deselected (96 of them, all
    passing, are in `packages/acquire`).
- 2026-10-16, follow-up to the Twisto/AOM-coverage work above (two final
  adjustments, user-directed):
  1. **No dedicated Twisto feed.** Reverted the `config/sources.yaml`
     addition; Twisto stays covered only via the Normandy aggregate
     (resource 81942), the same as the other 865 indirect-only AOMs --
     adding a dedicated feed for it specifically, while leaving the other
     865 untouched, would have been an arbitrary, inconsistent exception,
     and would duplicate its trips once a future PT-build step merges
     every network's feed into one multimodal network. Mapped directly
     against 81942 instead (see point 3 above for the exact result: 9
     `from_openings` entries now, up from 8).
  2. **New requirement recorded for the future PT-build step
     (`00_prepare_public_transport.py`, section 14.5): when the same
     agency's trips appear in both a dedicated producer feed and a
     broader aggregate feed (now an expected, accepted situation for at
     least 865 French authorities, confirmed above -- not a special case
     limited to Twisto), the build must keep only one copy -- the
     dedicated producer feed's -- before any trip-level deduplication
     across feeds.** Rationale: a dedicated feed and an aggregate that
     both include the same agency describe the *same* physical service
     twice; a trip-level dedup alone (matching by trip/stop/time) is not
     guaranteed to catch every duplicate (feeds can differ slightly in
     ids, timestamps or shape precision even for the same real trip), so
     the agency-level precedence rule must run first, as a coarse,
     reliable pre-filter, with trip-level dedup handling only genuine
     residual overlaps between *different* feeds/agencies. Not
     implemented yet (the PT-build step itself has not started, step 6+
     in the table above); tracked as a new entry under "Open points from
     the spec" below.
- 2026-10-09, bootstrap, use a four-member uv workspace with per-package setuptools metadata, so each package can be developed and installed independently.
- 2026-10-09, bootstrap, keep the pilot's area, years, halo and data directories in YAML; validate generic formats and positive/unique values in Pydantic.
- 2026-10-09, bootstrap, pin the project to Python 3.12 with `uv python pin 3.12` (writes `.python-version`); the sandbox's system Python (3.14) is only used to bootstrap `uv` itself. `.python-version` and `uv.lock` are committed so every agent and CI run uses the same interpreter and locked dependency set.
- 2026-10-09, step 1, keep tile size and halo caller-supplied because section 4.4 gives tile dimensions as examples and the halo depends on the mode cutoff.
- 2026-10-09, step 1, reject easting indices of 100,000 or more because the cell-id encoding uses 100,000 as its base.
- 2026-10-09, step 2, keep source URLs, vintages, local paths, checksums and licenses in `config/sources.yaml`; leave unknown values unset or marked `TODO(confirm)` rather than guessing.
- 2026-10-09, step 2, download only configured direct-HTTP files; API-discovery and manual sources are listed by the CLI but are not treated as downloadable file URLs.
- 2026-10-09, step 2, register restricted files only after they are placed locally; calculate their size and SHA-256 without downloading or altering them.
- 2026-10-09, step 2 (review follow-up), make the acquisition API client's auth header name and scheme (e.g. `Authorization: Bearer …` or `X-Api-Key: …`) configurable per source via `api_key_header`/`api_key_scheme`, instead of hardcoding `Authorization: Bearer`.
- 2026-10-09, step 2 (review follow-up), require every manifest source to have a unique, non-empty `id`; `load_manifest`/`save_manifest` fail with a clear message otherwise. Registered restricted records now get a generated id (`restricted:{source}:{relative path}`) instead of a blank one, and the CLI keys its download-update map by `local_path` (already guaranteed unique) rather than by `id`.
- 2026-10-09, step 2 (review follow-up), add a `verified` field to `SourceFile`: `True` only when a download was checked against a configured `expected_size_bytes`, MD5 (explicit or via `md5_url`), or `sha256`; otherwise the download is accepted (if the basic transport-length check passes) but logged and recorded as `verified: false`, since Content-Length alone is not an independent integrity check. The SHA-256 of the downloaded file is always computed and stored regardless of whether it was checked against anything.
- 2026-10-09, step 2 (review follow-up), reject downloads whose response looks like an HTML page (Content-Type `text/html`, or a body starting with `<!DOCTYPE`/`<html`) instead of the expected data file, to catch a web-page URL mistakenly configured in place of a direct file URL.
- 2026-10-09, source URLs, replace page/API placeholders with one direct file entry per requested file. Keep published redirect URLs, and name extensionless endpoints using the entry id plus the known extension. Census 2021 is the 2024-12-31 edition; census 2023 is the 2026-09-03 edition, whose URL INSEE replaces. The 2023 EMP passage workbook records the new dimension codes.
- 2026-10-09, national coverage, combine both requested source updates in one commit. Use the national Overture box directly (west/south/east/north: -5.5, 40.4, 10.0, 51.6), not a pilot acquisition box. Save all columns as Parquet from anonymous S3 release 2026-09-23.1; archive before approximately 2026-11-22. Precise France and adjacent NUTS3 clipping comes later. The pilot processing area comes from the Gironde polygon plus 50 km.
- 2026-10-09, GTFS discovery, the initial 565 GTFS resources span 487 distinct datasets. Excluding 13 community/third-party resources leaves **552 producer-owned GTFS resources across 486 datasets**. Retain overlapping aggregates/local feeds and every producer resource; do not deduplicate. **33 datasets have multiple GTFS resources (99 resources)**, flagged in [the inventory](../config/gtfs_inventory.csv) and listed in [the multiple-resource dataset list](../config/gtfs_multiple_resources.csv). Published public URL keys remain as supplied by producers.
- 2026-10-09, GTFS availability, IDFM, STAR Rennes, Sète Agglopôle Méditerranée, TBM Bordeaux and SNCF (TER/Intercités/TGV) have available producer resources in the API. TCL Lyon's producer resource **65812** is API-marked unavailable; its available community copy is deliberately excluded. List unavailable entries, and record later GTFS download failures without aborting the batch.
- 2026-10-09, step-0 coverage, **liO Occitanie and Rémi producer feeds are present** (`reseau-lio-occitanie`, resource 81026; `remi-offre-theorique-mobilite-reseau-interurbain-regional`, resource 83530). Couserans-Pyrénées (Ariège) and Marche Occitane – Val d'Anglin (Indre, SIREN **200035137**) have no networks of their own. **Check coverage spatially in step 0 using stops inside their 2026 EPCI polygons, not by network/EPCI name.** Feed presence alone does not establish that coverage.
- 2026-10-09, IGN discovery, resolve all 11 Atom feed pages and all matching entry pages. Found **96 metropolitan département archives**, with edition dates and advertised sizes recorded; Corsica uses `LAMB93-IGN78C`. Keep original `.7z` files; exclude overseas entries. After observing HTTP 429, pace IGN requests to at most one per second, respect numeric or HTTP-date `Retry-After`, and permit up to five retries with increasing backoff.
- 2026-10-09, acquisition configuration, keep discovery URLs, raw-path templates, metropolitan département codes, neighbouring regions/vintages, step-0 feed patterns, and HTTP limits in validated [config/acquisition.yaml](../config/acquisition.yaml), not in source code. The Overture S3 region is configured in its manifest record. Declare DuckDB as a direct acquisition dependency (already in the project's environment) for anonymous Parquet extraction.
- 2026-10-09, neighbouring OSM, HEAD-check all 26 exact requested PBF URLs and their 26 `.md5` URLs. **All PBFs return 200; all exact `.osm.pbf.md5` sidecars return 404.** Record these separately. List checksum-blocked entries without silently dropping verification or guessing alternate names. No PBF/checksum bodies were downloaded.
- 2026-10-09, Eurostat, use actual acquisition date as vintage and directory for both all-years TSV archives; reset stale checksums when that date changes. Key download updates by unique entry id (superseding path-keyed download updates) so the date-dependent path can be persisted. Restricted registration remains path-based.
- 2026-10-09, validation, `uv run --locked --offline ruff check .` passes and `uv run --locked --offline pytest -q` reports **61 tests passed**, including producer/community filtering, multiple-resource inventory, IGN pagination/Corsica/retry pacing, request-limit configuration validation, separate OSM/MD5 availability, metadata-only CLI discovery, nonfatal GTFS failures, actual-date Eurostat paths, offline dry runs, and an actual local DuckDB Parquet bounding-box test. Saved [the full dry-run output](data/acquire_dry_run.txt): **690 HTTP downloads proposed, 1 Overture extraction, 27 unavailable/checksum-blocked entries, 8 manual/restricted skips**. Exit 0; the manifest is unchanged by dry run and no acquisition records were written.
- 2026-10-09, OSM size-only verification, Geofabrik publishes no `.md5` sidecar for dated regional extracts (confirmed: all 26 exact sidecar URLs returned HTTP 404). `discover_osm` now does one HEAD per neighbouring PBF, captures the advertised `Content-Length` as `expected_size_bytes`, and no longer requests or configures `md5_url`/`md5_available` for these 26 entries. `download_source` now classifies `verified` as `True` (checksum matched), the literal `"size"` (only `expected_size_bytes` matched `Content-Length`, no checksum available), or `False` (neither); `SourceFile.verified` accepts `bool | Literal["size"] | None`. France's `osm-2022`/`osm-2024` entries are untouched and keep their real `.md5` checks at download time.
- 2026-10-09, TCL Lyon GTFS, transport.data.gouv.fr tags resource **81943** (the current SYTRAL Mobilités feed, `datagouv_id abebedc6-28cf-4e2e-9c64-db57a40156f8`) as a community copy even though it is the producer's own published URL, which excluded it from the producer-only catalog; resource **65812** (the deprecated 2022 Grand Lyon open-data URL) was the only resource retained, and it is unavailable. Added `gtfs_dropped_resource_ids` and `gtfs_resource_overrides` to [config/acquisition.yaml](../config/acquisition.yaml) so `discover_gtfs` reproducibly drops 65812 and force-includes 81943 at its stable `data.gouv.fr` redirect URL on every re-discovery, instead of hand-editing the manifest. 81943 is now the sole TCL Lyon entry.
- 2026-10-09, download fallback, added a generic `fallback_url` field to `SourceFile` (HTTP access only) and a `download_source` retry: on `httpx.HTTPError`, `ChecksumMismatchError`, `SizeMismatchError` or `UnexpectedHtmlResponseError` from the primary URL, it retries once against `fallback_url` (if configured) and records a note that the fallback was used; the manifest's `url` field stays the primary. Configured resource 81943's `fallback_url` to the Mobility Database copy `https://files.mobilitydatabase.org/tdg-81943/tdg-81943-202610090009/tdg-81943-202610090009.zip`. After dropping 65812, **no other GTFS resource is currently flagged unavailable** in the producer-only catalog, so no further Mobility Database fallback was needed for this pass; the override/fallback mechanism in config is reusable if one resurfaces.
- 2026-10-09, re-validation, re-ran `uv run --locked --offline ruff check .` (clean) and `uv run --locked --offline pytest -q` (**67 tests passed**, including new size-only verification, fallback-on-failure/fallback-also-fails, drop/override, and a real-config TCL Lyon regression test). Re-ran `--discover --dataset osm` and `--discover --dataset gtfs` to regenerate the manifest; GTFS step-0 coverage now reports **TCL Lyon: 1 available resource** (previously missing). Regenerated [the dry-run output](data/acquire_dry_run.txt): **717 HTTP downloads proposed, 1 Overture extraction, 0 unavailable/checksum-blocked entries (down from 27), 8 manual/restricted skips**. Exit 0.
- 2026-10-09, excluded community GTFS resources audit, checked all 12 datasets whose only remaining community-tagged (and thus excluded) GTFS resource might have left them with no producer feed, the TCL Lyon pattern. For every one, the dataset keeps another resource that is genuinely a producer copy (format GTFS, available, not community-tagged): IDFM (2, duplicates of the kept STIF feed 80921), Astuce Rouen Normandie (1, duplicate of 64973), CAESM zone Sud (2, duplicates of 79897), Mouvéo Audomarois (1, duplicate of 83987), Horizon Châteauroux (1, duplicate of 84169), TUD Digne (1, duplicate of 83915), Transp'Or (1, duplicate of 84099), T'CAP Privas (1, duplicate of its own two kept resources 79272/81342), TUB Decazeville (2, duplicates of 11492). All 12 are true duplicates; none needed an override. Recorded the full list, with dataset id/slug/title, network (covered area), excluded resource id/URL, sibling producer resource ids and decision, in [config/gtfs_excluded_community_resources.csv](../config/gtfs_excluded_community_resources.csv). Added a `discover_gtfs` safeguard: whenever excluding a community-tagged resource would leave a dataset with zero kept GTFS resources, it now logs a warning naming the dataset, so a future TCL-Lyon-style case is caught automatically instead of silently losing coverage.

- 2026-10-09, France OSM correction (sections 5.1/5.3), the user explicitly approved overriding section 5.3's incorrect claim that dated Geofabrik files have `.md5` sidecars, without editing the specification. This supersedes the earlier progress/checklist claim that France's sidecars exist. HEAD-only requests returned HTTP 200 and `Content-Length` **4,138,048,011 bytes** for `osm-2022` and **4,499,503,510 bytes** for `osm-2024`; stored these in the manifest and removed both `md5_url` values. No PBF data was fetched.
- 2026-10-09, France OSM discovery, refresh configured France entries together with the 26 neighbouring extracts, retaining France ids and paths and requesting no sidecars. Downloads store SHA-256 and `verified: size`; a matching stored local digest on rerun does not upgrade that classification to a provider checksum match.
- 2026-10-09, acquisition batches, continue after HTTP, filesystem, validation or DuckDB entry failures for any source, persist successful records, and print downloaded/already-present/skipped/failed counts plus each failure's id/reason. Actual acquisitions exit 1 for any failed or known-unavailable entry (including GTFS); retain existing exit 2 for manual/restricted skips without failures and offline dry-run exit 0. GTFS failure metadata remains recorded as before.
- 2026-10-09, idempotency, compare recorded local size and SHA-256 (and cached MD5 when supplied) before fetching a checksum sidecar or data. Preserve recorded verification and download date; changed local content is downloaded again. Existing Overture acquisition metadata in the user's worktree was preserved and excluded from the fix commit.
- 2026-10-09, validation, regression tests first reproduced **9 failures / 40 passes**; additional uppercase cached-MD5 coverage reproduced 2 classification failures before normalization. Final `uv run ruff check .` is clean and `uv run pytest -q` reports **81 passed**, including both France downloads with mocked bytes, offline reruns, corruption detection, HTTP/S3 batch continuation, persisted successes, summary counts/reasons, and nonzero GTFS/unavailable outcomes. No dependencies added.

- 2026-10-09, acquisition robustness (sections 5.1/5.4/5.6), persist each completed
  file before starting the next one, with unique same-directory temporary files.
  Replacement makes at most five attempts, waiting one second only on
  `PermissionError`; terminal write failures are logged and stop acquisition.
  A Windows regression reproduced our own YAML reader holding a replacement
  lock; manifest readers now close the handle before parsing. Failed attempts
  leave the previous manifest intact and clean up their temporary file.
- 2026-10-09, GTFS archive policy, user explicitly chose **only the requested
  resource's latest permanent URL**, less than 60 days old, with a valid GTFS
  ZIP before publication. No older archives, sibling downloads or Mobility
  Database fallbacks for identified GTFS resources. Dataset detail history is
  top-level, keyed by `resource_id`, with `payload.permanent_url` and
  `payload.download_datetime`; verified against the public Le Puy API response.
  Archive URL/date/resource id are separate manifest fields; the producer URL
  stays unchanged. The GTFS read timeout is configured at 300 seconds.
- 2026-10-09, GTFS recovery, **81023 (STAS)** and **84089 (Saint-Sulpice-la-Pointe)**
  downloaded from their producer URLs with the longer timeout. **81042
  (Aire'MOB)** returned HTTP 204 and was recovered from its own **2026-09-01**
  archive, with provenance and local size/SHA-256 persisted. **83905 (Le Puy)**
  and its latest **2026-10-01** archive both contain HTML; the already downloaded
  **83906** passes the offline check. Per user instruction, 83905 is recorded as
  `broken resource, dataset covered by 83906`, excluded and not counted as a
  failure. The same local sibling validation applies to any failed resource;
  exclusions are rechecked if covering files disappear.
- 2026-10-09, offline GTFS inspection, added `--check-gtfs`, which writes ZIP CRC
  validity, required/present files, flex indicators, effective first/last
  service dates, expiry, stop/trip counts, agency names, WGS84 bounding box and
  explicit errors to [the inventory](../config/gtfs_inventory.csv). Calendar
  weekday flags and date exceptions are applied only to service ids used by
  trips. Metadata tables are streamed to scratch space and read with DuckDB;
  raw files and the manifest are unchanged by the check. This is acquisition
  triage, not a full GTFS validator; see [the data page](data/gtfs.md).
- 2026-10-09, Filosofi temporal validation, added and downloaded both supplied
  **2019** INSEE ZIPs under `data/raw/filosofi/2019/`: natural level **6,282,711
  bytes**, 200 m benchmark **61,770,743 bytes**, with dates and local SHA-256 in
  the manifest. No provider checksum was available, so `verified: false`.
  The current spec places the temporal test in **section 6.5**, not 6.6.
- 2026-10-09, validation, acceptance tests first reproduced **11 failures /
  35 passes**, plus the absent GTFS-check module; later repros covered stale
  exclusions, Windows reader locks and stale archive provenance. Final
  `uv run ruff check .` passes and `uv run pytest -q` reports **108 passed**.
  The existing France OSM synthetic test now clears real acquisition hashes
  before downloading mock bytes, keeping tests independent of downloaded data.
  No dependency added.
- 2026-10-09, national offline check, run after implementation commit `c36491b`:
  **552 configured resources**, **551 downloaded**, **550 valid ZIPs**,
  **536 feeds passing all checks**, **15 downloaded files with errors**,
  **47 expired feeds**, **18 files with flex/on-demand indicators**.
  Expiry and flex counts overlap the other categories. The only missing file is
  excluded resource **83905**, covered by validated **83906** (service through
  **2027-08-28**). Command exit **0**; manifest SHA-256 unchanged; no network or
  raw-file modification/deletion.
- 2026-10-09, feed issues retained in the inventory: **82278** is not a ZIP
  (the published GTFS-RT `.proto` URL); **83019** is an outer ZIP containing a
  nested feed, not GTFS tables at that level; **83820** contains only agency and
  stops. **78904/84240/83511** have CSV parsing errors (bounded follow-up samples
  confirmed an unescaped quote, a short row and mixed line endings);
  **81652/81649/84018** have incorrect calendar exception headers.
  **14652/84068/83627/83629/78387/12616** have no effective service dates for
  their trips. All files remain untouched for review; no permissive parser
  fallback, alternate filename guess, sibling download or automatic deletion.
  Full facts, dates and errors are persisted in
  [the checked inventory](../config/gtfs_inventory.csv).
- 2026-10-12, step 0, built the rebuild test entirely in `mobgrid/pt`
  (`gtfs_clean.py` exact-date service selection, `stop_tables.py` OSM
  public-transport stop extraction and GTFS pattern extraction,
  `gtfs_rebuild.py` match/score/cut engine, `epci.py` EPCI polygon
  membership, `calibrate.py` the calibration driver, `report.py` the
  markdown writer), configured in `config/gtfs_rebuild.yaml`. Reference
  date **2026-10-13** (Tuesday, in school term, inside every test
  network's configured GTFS validity window, including STAR Rennes's
  split timetable versions). OSM mode-family classification (bus, tram,
  metro, rail) is a documented tag-priority rule in `stop_tables.py`, not
  a config value, since it is deterministic classification logic rather
  than a tunable threshold.
- 2026-10-12, step 0 performance, OSM extraction reads the PBF in three
  passes (node coordinates without tags, matching ways, matching nodes)
  instead of carrying a `tags` MAP for every node, and the lifecycle-tag
  exclusion uses `list_filter` instead of a correlated `EXISTS`/`UNNEST`
  subquery (250s to 65s on a France-wide way scan in testing). GTFS
  pattern grouping hashes the ordered stop sequence before `GROUP BY`
  instead of grouping by the `LIST` column directly, and IDFM/STAR
  Rennes's `trips.txt`/`stop_times.txt` (IDFM's `stop_times.txt` is
  1.1 GB) are pre-filtered to the needed routes with a streaming Python
  pass before DuckDB reads them, since only a handful of metro routes are
  needed from otherwise huge national/regional feeds. The EPCI-polygon
  union is a materialised `TEMP TABLE`, not a `VIEW` (a view recomputed
  the union, read and reprojection on every query: about 70-180s per
  query; the table drops this to under 0.2s), with a bounding-box
  candidate table computed before the exact `ST_Within` test. OSM public
  transport stops are cached once per dated extract to
  `data/interim/osm_pt_stops/{stamp}.parquet`; later runs only read the
  Parquet. Even with all of this, the real run over 8 networks and both
  OSM dates took about **2 hours**, dominated by two full-France OSM
  scans (the OSM bounding box is close to national because a few SNCF
  long-distance patterns reach several test EPCIs).
- 2026-10-12, step 0 calibration result, chosen on the known cases of
  section 5.6: **r = 100 m, k = 2, theta (bus) = 0.70, theta (tram) =
  theta (metro) = theta (rail) = 0.50**. Metro (F1 0.75) and tram (F1
  0.67) fit reasonably; **bus does not** (F1 <= 0.02 at every grid point;
  about half of all ~1,570 route-level bus cases, almost all expected
  "kept", score below any candidate theta). The most likely cause is
  genuinely sparse bus-stop mapping in the dated 2022/2024 OSM extracts,
  which section 5.6 names as the least complete family, not a code
  defect; metro/tram stops are far more consistently pre-mapped. Marked
  `TODO(confirm)` in `config/gtfs_rebuild.yaml`; do not use the bus theta
  for scenario triage before reviewing a sample of its "dropped" routes
  by hand. Lyon's BHNS Part-Dieu - Sept-Chemins case has no confirmed
  opening date ([TO CONFIRM], section 5.6) and is reported for manual
  review only, matched to its closest current route (125) by name, not
  scored. Full per-case results, the complete score table, per-EPCI
  dropped/cut bus lines and the rail manual-review list are in
  [the committed report](data/step0_gtfs_rebuild.md).
- 2026-10-12, step 0 rural EPCI coverage (resolves the pending open
  point below), checked spatially with each network's real GTFS stops
  against the exact 2026 EPCI polygon, not by feed presence: **Couserans-
  Pyrénées is covered** (30 liO Occitanie patterns intersect its
  polygon); **Marche Occitane - Val d'Anglin has no liO, Rémi or SNCF
  stop inside its polygon** (0 of all three), consistent with "no
  network of its own" but showing that even the regional coach/rail
  networks named in the spec text do not call directly inside this
  EPCI's communes.
- 2026-10-16, code-review follow-up on the openings-list policy
  enforcement and the PT change catalogue:
  - **`apply_openings_matches` no longer hardcodes its confidence
    thresholds.** `include_row_confidence`/`apply_match_confidence` are
    now keyword parameters (defaulting to today's configured values,
    `high`/`medium` and `exact`/`stop-confirmed`, only for a caller with
    no loaded policy); `mobgrid.pt apply-openings` (now also takes
    `--config`, like `map-and-apply-all`) and `map-and-apply-all` both
    pass `national_policy.openings_list.include_row_confidence`/
    `apply_match_confidence` through explicitly, and `report.py` passes
    the same fields from the config it already has when one is
    configured. Previously, editing these two config fields would have
    silently desynced the report's description from what was actually
    applied. Tested in
    `tests/mobgrid/pt/test_pt_openings.py
    ::test_apply_openings_matches_uses_configured_confidence_thresholds`.
  - **`write_from_openings` no longer crashes on an existing, empty
    `pt_changes.yaml`.** `yaml.safe_load` returns `None` for an empty or
    whitespace-only file; `raw = yaml.safe_load(...) or {}` restores the
    previous "missing file" fallback for that case too. Tested in
    `tests/mobgrid/pt/test_pt_changes.py
    ::test_write_from_openings_treats_an_empty_file_as_an_empty_mapping`.
  - **`removed_route_keys` now returns one `(GTFS resource id, route_id)`
    key regardless of source**, fixing the network-naming mismatch
    flagged below under "Fixed (2026-10-16 follow-up)": it takes a
    `network_resource_ids` mapping (built by the new
    `mobgrid.pt.pt_changes.build_network_resource_ids` from
    `GtfsRebuildConfig.networks` plus
    `national_policy.openings_list.network_resource_ids`) and an optional
    `mode_split_network_resource_ids`, so `confirmed`'s config slug and
    `from_openings`'s raw CSV network string resolve to the same key when
    they name the same physical network. `resolve_route_presence` and
    `resolve_route_edits`/`collect_edit_specs` remain uncalled by any
    pipeline code (see the open point added below) -- this fix only
    changes `removed_route_keys`'s own key space for whenever that future
    consumer arrives.
  - **Rewrote `test_only_confirmed_and_dropped_openings_changes_are_subtracted`**
    (now `test_removed_route_keys_equals_confirmed_plus_openings_drops_only`):
    it encoded a stale assumption that `to_review`/`not_applied` screening
    candidates are always disjoint from applied drops, which is false for
    real data (TCL Lyon's `TB12` is both `candidate_tcl_lyon_TB12`, old
    automatic OSM screening, informational only, and `ARA-08`, a real
    openings-list `new_line` drop). The acceptance test now asserts the
    current policy directly: the routes removed from a past state equal
    exactly `changes_after` plus the openings list's `drop` instructions,
    and clearing `to_review`/`not_applied` entirely never changes
    `removed_route_keys()`'s result, using TB12 as the proof case
    (section 5.6 point 6: these lists are informational only).
- 2026-10-16, national `map-and-apply-all` run follow-up: fixed the 15
  rows that carried a real `remove` instruction but were not applied.
  - **Paris metro "M"-prefix normalisation** (IDF-01 M4, IDF-02 M12,
    IDF-10 M11, IDF-11/IDF-12/IDF-14 M14): the openings CSV conventionally
    writes a numbered Paris metro line as `"M4"`/`"M11"`/`"M12"`/`"M14"`,
    but every checked metro feed's own `route_short_name` (IDFM, Lyon,
    Rennes) is bare -- IDFM's numbered lines never carry the `M` at all,
    and letter-coded lines (Lyon A-D, Rennes a/b) were never `M`-prefixed
    in the CSV either. `mobgrid.pt.pt_openings.normalise_line_name` now
    takes an optional `mode` and strips a leading `M`/`m` only when
    `mode="metro"` and it is immediately followed by a digit (never for a
    bare letter code), so it only ever fires for the one real convention
    mismatch, not by hardcoding the four known line numbers. Tested in
    `tests/mobgrid/pt/test_pt_openings.py
    ::test_normalise_line_name_strips_metro_m_prefix_for_numbered_lines`
    and `::test_metro_m_prefix_matches_the_bare_gtfs_short_name` (plus a
    regression test that letter codes are never touched).
  - **Multi-route `new_station`/`extension` rows** (NAQ-02 TER 42, 8
    routes; NAQ-10 TER 41/42, 3; PDL-03 TER 22/24, 2): a `new_station`/
    `extension` row matched to several identically-named same-corridor
    route variants (unlike `new_line`/`reopening`, safe to apply to every
    variant by identity alone) is now narrowed by `mobgrid.pt.pt_openings
    ._match_by_name` to only the variants that actually call at the
    hinted stop (`section_from`/`section_to`), using the existing
    `_disambiguate_by_stops` narrowing; a variant that does not call
    there is excluded from the mapping CSV's `candidate_route_ids` and
    named in its `notes`, never guessed in. `apply_openings_matches`'s
    former `new_line`/`reopening`-only multi-route gate is retired
    entirely, since the same four instruction-capable change types now
    all either apply by identity (`new_line`/`reopening`) or have already
    been narrowed to the calling routes by the mapping step
    (`extension`/`new_station`) -- one `OpeningDerivedChange` per route
    id either way. Tested in `tests/mobgrid/pt/test_pt_openings.py
    ::test_new_station_narrows_same_corridor_routes_to_those_calling_there`,
    `::test_extension_keeps_every_route_when_all_of_them_call_at_the_anchor`,
    `::test_new_line_is_never_narrowed_by_the_new_station_extension_rule`
    and `::test_apply_openings_matches_allows_a_multi_route_extension_match`.
  - **Whole-mode-family stop-name fallback** (IDF-17 Tzen 4, GES-06 Mettis
    A, NAQ-03 Péribus BHNS Est-Ouest, PAC-05 Lebus+ Aubagne-Gémenos, OCC-05
    Pont-Saint-Esprit-Avignon, OCC-13 Montréjeau-Luchon): a row still left
    `none`/`ambiguous` after ordinary line-name matching now falls back to
    searching every route of its own mode family by `section_from`/
    `section_to` stop names alone, ignoring line names entirely
    (`mobgrid.pt.pt_openings._match_by_stop_names_within_mode`). Unlike
    `_disambiguate_by_stops` (narrows an already name-matched handful,
    where matching *either* hint is enough), this requires *every*
    non-empty hint to be served by the *same* route -- a single-hint
    match across a whole family (hundreds of routes) is far more likely
    to be coincidental -- and is accepted only when it narrows to exactly
    one route, never guessed. Spot-checked against the real cached IDFM
    feed: IDF-17 (Tzen 4) stays correctly unresolved, since neither
    Tzen1 nor Tzen4's real GTFS stops are named "Viry-Châtillon" at all
    (a genuine CSV-vs-GTFS place-name mismatch, not a bug); the mechanism
    itself is proven with synthetic fixtures in `tests/mobgrid/pt
    /test_pt_openings.py
    ::test_stop_name_fallback_resolves_a_row_with_no_line_name_match`,
    `::test_stop_name_fallback_refuses_to_guess_between_two_matching_routes`
    and `::test_stop_name_fallback_also_resolves_an_ambiguous_name_match`.
    Some of the six rows may still end up correctly unresolved after a
    real rerun, logged rather than guessed -- that is by design.
  - **WARNING/INFO logging split** (section 5.6 point 6): `apply_openings
    _matches` now classifies every not-applied row instead of logging all
    of them the same way. A row whose `change_type` can never give an
    instruction (`restructuring`/`renaming`/`suspension`/`closure`/
    `relocation`) or whose state is never `remove` (e.g. a `planned_not_
    open` line) is counted under `not_applied_by_design` (one count per
    reason: `non_instruction_change_type`, `no_remove_state`,
    `low_confidence`), logged at INFO; only a row that *does* carry a
    real `remove` instruction (an accepted-confidence, instruction-capable
    row) but whose match failed is logged at WARNING, in `OpeningsApplica
    tion.warnings`, one line per row. `mobgrid.pt.cli._log_openings_appli
    cation` and `report.py`'s `_openings_application` both use the new
    fields; the now-impossible "missing change_type" check and the
    `_MULTI_ROUTE_CHANGE_TYPES` multi-route gate were removed as dead
    code (an instruction-necessary row's `change_type` is always one of
    the four known values by construction). Tested in `tests/mobgrid/pt
    /test_pt_openings.py::test_ambiguous_row_is_a_warning_and_low_confidence_row_is_info`
    and `::test_apply_openings_matches_counts_rows_with_no_instruction_as_info`.
- 2026-10-16, reconciliation of the full national run (no new run
  needed, read from the existing `config/pt_changes.yaml`/
  `config/pt_openings_mapping.csv` and the day's own
  `logs/2026-10-16_pt_openings_map_and_apply_all.log`):
  - **Confirmed no regression.** All 120 openings-list rows fall into
    exactly one of six row-level categories (applied 53, remove-not-
    applied/warnings 5, low confidence 19, no remove state 13,
    non-instruction change type 22, known gap 8 -- sums to 120). The
    reported "136" was `len(result.applied)` (route-level: 5 rows now
    resolve to several routes -- `GES-05`×6, `NAQ-02`×8, `NAQ-10`×3,
    `NAQ-11`×2, `PDL-03`×2, 16 extra entries -- 69+5+54+8 = 136) added to
    the other, row-level counts; comparing the pre-fix run (11:43/14:06
    in the same log, confirmed still pre-fix by `IDF-01 ... match_
    confidence='none'`) to the current one by row shows 10 rows gained
    (the metro six, `NAQ-02`, `NAQ-10`, `OCC-13`, `PDL-03`, as intended)
    and 17 rows "lost" -- all 17 are `restructuring`/`renaming`/
    `suspension` rows (never an instruction regardless of state) or
    `extension`/`new_line` rows whose state is `keep`/`keep`
    (`planned_not_open`, no instruction yet); none ever produced a real
    instruction before or after, so today's `not_applied_by_design`
    reclassification only stopped writing their old, functionally-inert
    "for the record" entries into `from_openings` -- no route's presence
    in a built state changes.
  - **Fixed the bookkeeping**: `OpeningsApplication` gained
    `applied_opening_ids` (row-level, distinct `opening_id`s) and
    `row_counts()` (one count per the six categories, row-level
    throughout); `apply_openings_matches` now raises if they do not sum
    to the number of CSV rows read, so a future miscount or
    double-counted row is caught immediately rather than silently
    reported wrong. `cli.py`/`report.py` report applied rows and
    route-level edits as two separate numbers. Tested in
    `tests/mobgrid/pt/test_pt_openings.py
    ::test_row_counts_sum_to_total_rows_and_distinguish_route_level_edits`
    (synthetic, one row per category plus a multi-route row) and
    `::test_real_openings_list_row_counts_reconcile_to_the_total` (the
    real committed CSV/mapping/config, no new run).
  - **5 residual warnings accepted as gaps** (IDF-17 Tzen 4, GES-06
    Mettis A, NAQ-03 BHNS Est-Ouest, OCC-05 Pont-Saint-Esprit-Avignon,
    PAC-05 Lebus+ Aubagne-Gémenos): each stays `match_confidence=
    'none'`/`'ambiguous'` after both the ordinary line-name pipeline and
    the whole-mode-family stop-name fallback, a genuine CSV-vs-GTFS
    mismatch (free-text place names, e.g. "Viry-Châtillon", that do not
    literally occur as a GTFS `stop_name` on the real feed, confirmed by
    spot-checking IDF-17 against the cached IDFM feed in the previous
    entry) rather than a code gap; recorded here rather than re-attempted
    automatically, per the national policy's "log it, never guess" rule.
  - **`map-and-apply-all` now reads each GTFS resource once.** Grouping
    by network-name alias (one `run_mapping` call per
    `network_resource_ids` key) read the same resource repeatedly --
    IDFM's resource 80921 alone 5 times ("IDFM", "IDFM (operator
    Transdev...)", "Keolis Tisse (IDFM)", "RATP (IDFM)", "RATP; Société
    des grands projets (IDFM)"), since `load_openings_rows`'s substring
    match already made some of those aliases redundant with each other
    (e.g. `network_contains="IDFM"` alone already matches
    `"RATP (IDFM)"` rows too). `_run_map_and_apply_all` now groups every
    alias by its *resolved resource id* first and extracts/reads it once
    per resource, via the new `mobgrid.pt.pt_openings
    .run_mapping_for_networks`/`load_openings_rows_for_networks` (one
    `propose_route_matches` call covering every alias's rows in a single
    pass) and a `get_table_dir` cache shared with the mode-split loop (so
    a resource used by both a flat alias and `"TER Occitanie (liO)"`'s
    mode-split entry, e.g. SNCF's 83582, is also read only once). Tested
    in `tests/mobgrid/pt/test_pt_cli_map_and_apply_all.py
    ::test_map_and_apply_all_reads_each_resource_once` (two network-name
    aliases sharing one resource id; asserts the extraction call is made
    exactly once per distinct resource id, and both aliases' rows still
    map correctly).

## Assumptions to check

- 2026-10-19, step 7, the headway random-arrivals/planned-arrival regime
  boundary (section 9.4: "headways up to about 10-12 min") is set to its
  upper end, 12 min, in `config/energy.yaml`
  `waiting.headway_regime_threshold_min`, since the spec gives a range
  rather than a single value.
- 2026-10-09, bootstrap, the initial base configuration contains the EPSG:3035 coordinate system and 200 m/1 km resolutions; `config/base.yaml`.
- 2026-10-12, step 0, a pattern's expected outcome defaults to "kept" at
  both state dates unless it is one of section 5.6's listed known
  changes; this lets the calibration score every bus/tram/metro route of
  the test networks, not just the handful of explicitly named cases.
- 2026-10-13, step 0, routes not listed as labelled known cases in each test
  area are presumed unchanged for false-change scoring. This is not ground
  truth and is reported separately from known-case precision/recall/F1.
- 2026-10-16, step 0 NAQ-11-style prefix-family reclassification (bus
  express H -> H1/H2), a same-prefix match pool (code length diff <= 2)
  that the generic stop-hint disambiguation cannot narrow at all is now
  `exact` rather than `ambiguous`, since every real case so far is one
  circular/directional service's own numbered variants, not two different
  lines. `TODO(confirm)`: a coincidental same-prefix match between two
  genuinely unrelated lines would misfire the same way and auto-apply
  without review; not observed in any of today's mapped data, but worth
  checking if a future network's mapped candidates look wrong.

## Open points from the spec

Each item stays open until a value is decided; the value goes into `config/`.

- [ ] Step 7 (`mobgrid/energy`): PT crush load per seat (LF_max) by
  vehicle type, `config/energy.yaml` `pt_ride.load_factor_max`
  [TO CONFIRM: against operators' vehicle data], section 9.5
- [ ] Step 7: bike force-balance power selection `k`, `P_max` and
  `v_max,desc`, `config/energy.yaml` `bike.power` (all still `null`); the
  spec gives no numeric value for these, only "calibrated on observed
  commuter speeds on gradients (Parkin & Rotheram 2010)", section 9.7.
  `P_0 = 34.8 W` is now confirmed (step 11, EMP 2019 re-estimation,
  third round) and no longer on this list. Needed before the
  graph/layers steps can assign real bike edge speeds from slope alone;
  the leg-level speed solver itself (`mobgrid.energy.bike.solve_bike_speed_m_per_s`)
  does not need them, since it takes power as an explicit argument.
- [ ] Step 7: walk-to-car time by apartment density class,
  `config/energy.yaml` `car.walk_to_car.apartment_min_by_density`
  [TO CONFIRM: per-density-class split]; section 9.6 gives only the
  overall range (1-4 min), not a value per class; placeholder values are
  spread evenly across that range.
- [ ] Step 7: bike stop time parameters (deceleration, acceleration,
  signal cycle, red time), `config/energy.yaml` `bike.stops`
  [TO CONFIRM: not yet calibrated against observed junction/signal
  behaviour], section 9.7.
- [ ] Step 7: carpool passenger origin legs (walk to a meeting point,
  wait standing), `config/energy.yaml` `car.carpool_passenger`
  [TO CONFIRM: provisional, no survey or observed pickup pattern],
  section 9.6.
- [ ] Step 7: e-bike rider-effort reduction by assist level,
  `config/energy.yaml` `bike.ebike.effort_factor_by_level` (all `1.0`)
  [TO CONFIRM: not yet calibrated]; a hook for a future calibration
  against the Compendium's light/high-support MET values (section 9.7),
  which the model currently does not reproduce (see the `checks.py`
  COMPARE rows).
- [ ] Inhabited 200 m cells: about 2.3 million (section 4.5)
- [ ] EMC² surveys: access conditions (section 5.3)
- [ ] EMC² surveys: zoning and leg detail (section 5.4)
- [ ] Géovélo cycle infrastructure: a version for 2021 (sections 5.3 and 8.1)
- [x] Exact earliest Géovélo 2022 monthly vintage and direct resource URL: 2022-07-18, proxy for 2021
- [x] Filosofi 2021 imputed 200 m benchmark: published file URL configured
- [x] Overture places: release 2026-09-23.1 and national Parquet extraction configured
- [x] Archive Overture before approximately 2026-11-22; `data/raw/overture/2026-09-23.1/overture-places.parquet` exists
- [x] Step 0: TCL Lyon GTFS now resolves to the current SYTRAL Mobilités resource 81943 (producer URL + Mobility Database fallback); the deprecated 65812 resource is dropped
- [x] Step 0: verify liO/Rémi stops inside the 2026 Couserans-Pyrénées and Marche Occitane – Val d'Anglin EPCI polygons: Couserans-Pyrénées is covered (30 liO patterns); Marche Occitane has no liO/Rémi/SNCF stop inside its polygon
- [x] Neighbouring OSM extracts: Geofabrik publishes no `.md5` sidecar for dated regional files; verified by `Content-Length`-based size instead
- [x] France OSM extracts: same size-only verification for both vintages; section 5.3's dated-extract `.md5` claim is incorrect (user-approved override, 2026-10-09); already corrected in spec version 9, section 5.3 (the tracked `docs/spec/05_data_acquisition.md` now reads "dated extracts... are published without `.md5` files"), so no further specification edit is needed
- [ ] Acquisition API resources: direct file URLs, source-specific licenses, and expected checksums where providers publish them
- [ ] Lyon BHNS Part-Dieu – Sept-Chemins: opening date (section 5.6)
- [ ] Step 0 relation parameters: run the approved Luxembourg smoke, national
  relation extractions and calibration; review `kept-renamed`/`dropped`
  candidates and confirm recommended r, k, theta and geometry shares
- [x] Step 0 PT openings list: resolve every network's GTFS resource id
  (2026-10-16, see the decision entries above); all 47 of 47 high/medium-
  confidence networks now have a configured `resource_id` (or, for `TER
  Occitanie (liO)`, a per-mode resolution), including `Twisto (Caen la
  mer)`, mapped against the existing Normandy aggregate rather than a
  dedicated feed
- [x] Step 0 PT openings list: run `mobgrid.pt map-and-apply-all` for
  every network: completed 2026-10-16, 47 of 47 networks mapped, 0
  failed, 53 rows applied (69 route-level edits), 5 rows left as
  accepted residual gaps, see the decision entries above
- [ ] Future PT-build step (`00_prepare_public_transport.py`, section
  14.5): when the same agency's trips appear in both a dedicated
  producer feed and a broader aggregate feed, keep only the dedicated
  feed's copy before any trip-level deduplication across feeds
  (2026-10-16 decision, see the decision entry above; not yet
  implemented, since this step has not started)
- [ ] Future PT state builder (same step as above): must call
  `mobgrid.pt.pt_policy.resolve_route_presence` (per-route keep/drop
  precedence: openings list > tram automatic rule > default keep) and
  `mobgrid.pt.route_edits.resolve_route_edits`/`collect_edit_specs`
  (combined `cut`/`new_station` edits per route) when it builds each
  past state; both are implemented and tested (2026-10-15/16) but not
  yet called from any pipeline code, since no state builder exists yet.
  Pass `removed_route_keys` a `network_resource_ids` mapping built with
  `mobgrid.pt.pt_changes.build_network_resource_ids` (2026-10-16 fix) so
  `confirmed`'s config-slug networks and `from_openings`'s raw CSV
  network names resolve to the same `(GTFS resource id, route_id)` key.

- [ ] PT: rule for a regular service whose `calendar`/`calendar_dates` window has already expired by the state/reference date — shift it to its last valid week (e.g. same weekday pattern one week back) or drop it entirely (section 8.6/14.4)
- [ ] Car ownership model: functional form, e.g. ordered or multinomial logit (section 6.4)
- [ ] Public-sector jobs: default surface by amenity type when there is no building footprint (section 7.2)
- [ ] PT engine: departure sampling if plain RAPTOR is kept, after the benchmark (section 8.6)
- [ ] Crush loads per seat (LF_max): check against operators' vehicle data (section 9.5)
- [x] EMP 2019: leg detail and durations in the public tables (section 9.9) — resolved by step 11 (`mobgrid.budget.emp`): K_DEPLOC has no leg detail, so terminal legs use the model's own section 9.4-9.7 defaults by density class/vehicle, not a real decomposition; companions (`MACCOMPM`/`MACCOMPHM`) separate household from carpool passengers.
- [ ] PT headway/CV by vehicle for the section 9.9 re-estimation: `config.pt_ride.headway_min_am_peak`, new in step 11, is provisional (no survey or operator data)
- [ ] PT station height by vehicle for the section 9.9 re-estimation: `config.pt_ride.station_height_m`, new in step 11, is provisional (no station-sample data, unlike section 9.3's own table)
- [ ] PT access/egress walk distance by density for the section 9.9 re-estimation: `config.pt_ride.access_walk_m_by_density`, new in step 11, is provisional
- [ ] Bike get/park time for the section 9.9 P0 re-estimation: `config.bike.get_park_min`, new in step 11, is provisional (reused step 7's `checks.py` illustrative value)
- [ ] Bike stops per km for the section 9.9 P0 re-estimation: `config.bike.stops.stops_per_km`, new in step 11, is provisional (reused step 7's `checks.py` illustrative value, no junction-density data)
- [ ] PT fares and passes by network (section 9.10)
- [ ] Bike and e-bike prices and lifetimes (section 9.10)
- [ ] Fiscal power of the car fleet by cell, 5 CV by default (section 9.10)
- [ ] Opportunity-curve storage: number of job sectors counted, 6 by default (section 10.2)
- [ ] Google Routes API: pricing tier of `staticDuration`, `polyline` and traffic on polylines (section 12)
- [ ] Traffic counts: national and departmental sources (section 12)
