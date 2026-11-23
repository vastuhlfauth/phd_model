# Progress

Read this file at the start of every task and update it at the end.

## Where the history is

This file holds the current state only. Search the history for your step; don't read it whole.

- `docs/progress/log_networks.md`: steps 6, 8, 9 and 10. Latest entries:
  - Step 6b: Windows flat BD ALTI unpack (2026-11-23)
  - Step 6b: edge-cost groundwork (2026-11-21)
  - Step 6b: road classes (2026-11-21)
  - Step 6: OSM network pilot pipeline
- `docs/progress/log_time_budget.md`: steps 11 and 12, the Zahavi reports and the spec of the time model. Latest entries:
  - Spec: time per mode and the mobility model (2026-11-20)
  - Mode-cell report: CLI and synthetic integration (2026-11-20)
  - Mode-cell report: reference energy calculations (2026-11-20)
- `docs/progress/decisions.md`: decisions taken while coding, all steps.

At the end of a task: one dated entry of at most 25 lines at the top of your area's log,
decisions in `decisions.md`, and the step row, assumptions and open points below.

## Steps (table of section 14.5)

| Step | Content | Status | Branch | Notes |
|---|---|---|---|---|
| — | Repository skeleton (`/bootstrap`) | done | `step/bootstrap-skeleton` | uv workspace, package layout, configuration validation; Ruff and 3 tests pass (pinned Python 3.12.15) |
| 0 | GTFS rebuilding test | merged | `step/gtfs-rebuild-test` | Notes moved to `docs/progress/log_networks.md` (Step 0: notes from the steps table) |
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
| 6 | `mobgrid/osm` | in progress | `step/mobgrid-osm` | Edge build optimized; active-mode costs include corrected bike stop delay; pilot timing, unified stage and Géovélo check remain |
| 7 | `mobgrid/energy` | review | `step/mobgrid-energy` | Notes moved to `docs/progress/log_networks.md` (Step 7: notes from the steps table) |
| 8 | `mobgrid/graph` | not started | | |
| 9 | `mobgrid/layers/gridgraph.py` | not started | | |
| 10 | `mobgrid/od` | not started | | |
| 11 | `mobgrid/budget` | review | `step/mobgrid-budget-entd2008` | Notes moved to `docs/progress/log_time_budget.md` (Step 11: notes from the steps table) |

Status values: not started, in progress, review, merged.

## Data pages written (`/schema`)

- [EMP 2019 public tables](data/emp2019.md) (step 11)
- [ENTD 2008 public tables](data/entd2008.md) (step 11, section 9.9's 2008-2019 comparison)
- [Commune contours](data/commune_contours.md) (step 6)
- [BD ALTI 25 m elevation grids](data/bdalti.md) (step 6)
- [OSM directed edges, elevation and active costs](data/osm_edges.md) (step 6)

## Assumptions to check

- 2026-10-19, step 7, the headway random-arrivals/planned-arrival regime
  boundary (section 9.4: "headways up to about 10-12 min") is set to its
  upper end, 12 min, in `config/energy.yaml`
  `waiting.headway_regime_threshold_min`, since the spec gives a range
  rather than a single value.
- 2026-11-21, step 6b: provisional car-speed values in
  `config/network.yaml` (`TODO(confirm)`): context defaults are 50 km/h
  urban, 80 km/h rural, 30 km/h zone30 and 130 km/h motorway, with class
  overrides for trunk/primary roads; all realism factors are 1.0 until R4.
  Untagged context uses car-edge length within a 500 m centroid radius and
  a fitted length-weighted urban/rural separator (1 km fallback). Control
  delays are 15 s per signal, 5 s per stop, 2 s per give-way,
  3 s per mini-roundabout, 0 s per unsignalled crossing and 2 s at
  to-nodes of degree 3+, with
  30/50/80/110 km/h speed-limit bucket bounds. Confirm defaults, class
  overrides, factors, density rule, delays and buckets against the pilot/R4.
- 2026-11-23, step 6b: provisional bike infrastructure caps, stop
  probabilities, signal timing and surface fallbacks are configured with
  `TODO(confirm)` markers in `config/network.yaml` and `config/energy.yaml`.
  Confirm them against observed speeds, junctions and mapped surfaces before
  interpreting costs as calibrated.
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

- [ ] Step 6: verify the version 7 pilot edge-build time is under five minutes.
  DuckDB memory limit and threads are not exposed by the loaded base, pilot or
  network configs; the existing connection setup remains in use.
- [ ] Step 6b (section 8.4): validate car class/context defaults and
  overrides, realism factors, urban-density radius/fallback/fitting rule,
  control and junction delays, and speed-limit buckets; provisional values
  are marked `TODO(confirm)` in `config/network.yaml`.
- [ ] Step 6b (sections 8.3 and 9.7): confirm the provisional bike class
  and highway speed caps, grade grid and tolerances in `config/network.yaml`.
  Active-mode cost functions now use these plus the user-supplied provisional
  stop probabilities and surface fallbacks; all remain unconfirmed.
- [ ] Step 6b (section 8.1): configure and implement the user-supplied
  provisional Géovélo family mappings, side counts and 15 m matching rule;
  list distinct facility values before mapping.
- [ ] Step 6b: user rerun of BD ALTI unpack after the Windows path-length
  fix; move aside old nested/stale department outputs first. Real archive
  extraction was not run during validation; no new parameter assumptions.
- [x] Sections 9.9 and 10.4: Saturday and Sunday get their own f_m, in a
  later version (decision of 20 November 2026).
- [ ] Section 9.12: car passengers, train and bike are not shown stable;
  whether they keep a fixed f_m.
- [x] Section 10.4: multimodal patterns split by their main combinations,
  in a later version (decision of 20 November 2026).
- [ ] Section 10.4: driving licence, PT pass and bike per cell.
- [x] Section 10.4: household type per cell comes from the synthetic
  population (decision of 20 November 2026).
- [ ] Section 6.1: method of the synthetic population.
- [x] Section 10.4: accessibility variables: time to the 1st, 2nd and 3rd
  nearest opportunities, or opportunities within 15, 30 and 45 min, per
  mode and opportunity type (decision of 20 November 2026).
- [ ] Section 10.4: estimation sources of the accessibility terms (EMC²,
  MOBPRO, EMP 2019 through CASD), combined with the national person and
  household terms (to be tested).
- [x] Section 10.4: multinomial logit, nested only if the tests call for it
  (decision of 20 November 2026).
- [ ] Section 10.4: purposes out of a mode's reach in the required time
  (to be tested).
- [x] Section 10.4: time is the ranking key (decision of 20 November 2026).
- [ ] Section 10.4: calibration of rho_m (EMC², or categories in EMP 2019;
  to be tested).
- [x] Section 10.4: allocated time shorter than the nearest destinations:
  the nearest are kept and the excess reported (decision of 20 November 2026).
- [x] Section 10.4: the extended radiation parameter is calibrated on
  MOBPRO with the time tilt in place, iterating (decision of 20 November 2026).
- [ ] Section 10.4: delta_m as a yearly trend or only as a sensitivity
  (to be tested).
- [x] Section 10.4: travel outside the reference scope is added at its
  observed level per population category, unchanged across scenarios
  (decision of 20 November 2026).
- [x] Section 9.9: income variables settled by the step 12 income report
  (ENTD 2008 bracket midpoint per consumption unit; EMP 2019 imputed decile).
- [x] No microdata for the 1994 survey: the per-mode constant cannot be
  tested before 2008 (sections 10.4 and 15).

- [x] Step 11/12 (section 9.9): the described-day chain uses all `K_DEPLOC`
  rows, including non-local rows, without joining voyage trips (decision
  of 6 November 2026).
- [x] Step 11/12: voyage dates are not used to flag away days. The
  documented immobility reasons lack a comparable away-from-home category.
- [ ] Step 11/12: the ENTD local-mobility documentation does not establish
  systematic beyond-80-km coverage. Label `daytable` partial and suppress
  its cross-year ratio when wiring the reports.
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
- [ ] ENTD 2008 `STATUTCOM_UU_ORI`/`_DES` disclosure-masked codes '8'/'9' (and a blank status), seen in the real archive alongside the documented C/B/I/H: no meaning is given in `docs/data/entd2008.md` or EMP 2019's dictionary; `emp2019._UU_STATUS_BY_CODE` leaves them unmapped (`NULL`), falling back to the density proxy's 'intermediate' default like a stray grid code (step 11, eleventh round)
- [ ] PT fares and passes by network (section 9.10)
- [ ] Bike and e-bike prices and lifetimes (section 9.10)
- [ ] Fiscal power of the car fleet by cell, 5 CV by default (section 9.10)
- [ ] Opportunity-curve storage: number of job sectors counted, 6 by default (section 10.2)
- [ ] Google Routes API: pricing tier of `staticDuration`, `polyline` and traffic on polylines (section 12)
- [ ] Traffic counts: national and departmental sources (section 12)
