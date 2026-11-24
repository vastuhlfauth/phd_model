# Progress log: networks (steps 6, 8, 9, 10)

OSM extraction, directed edges, elevation, speeds and costs, graphs, O-D.
Newest entry first. Add yours at the top.

### Step 8: compact graph storage (2026-11-24)

- Graph archives version 2 store compact class and bucket ids, reverse arc
  references, and ordered original Parquet edge-row membership.
- Contraction retains class and bucket transitions; SCC filtering and archive
  round trips preserve the member paths and weight sums.
- Synthetic graph tests: 11 passed; Ruff clean. No pilot build was run.
- Report estimates the old format on the new topology alongside actual memory;
  the previously reported pilot car graph used 248 MiB for 976k arcs.
- Next: implement bounded searches and destination products.

### Step 8: CSR and degree-2 graph build (2026-11-24)

- Added per-mode CSR arrays from the validated one-to-one edge/cost join,
  including time, distance, reference-mass energy, climb and bike/car
  components; every graph also stores its transpose.
- Largest-SCC filtering reuses the OSM Kosaraju routine. Degree-2 chains
  stop at kept nodes and sum every float32 weight; unanchored cycles remain
  intact. Kept nodes include signals, junctions and mixed road classes.
- Added `python -m mobgrid.graph.build --state 2021 --area pilot`; it writes
  three `.npz` graphs and reports node/edge counts, array memory and stage
  timings to the terminal and step 6 report.
- Synthetic graph tests: 10 passed; Ruff clean. No pilot or national build
  was run. Dijkstra and search products remain for the rest of step 8.
- Command for the user: `python -m mobgrid.graph.build --state 2021 --area pilot`.

### Step 6b: standalone Géovélo comparison (2026-11-24)

- Removed the Géovélo comparison from edge builds; it now has a standalone
  `python -m mobgrid.osm.geovelo_report` command.
- Replaced buffer unions with Shapely STRtree nearest-line matching of
  length-weighted samples at 5 m spacing, within the configured 15 m.
- Generic OSM `cycleway=lane` and `cycleway:both=lane` count both sides.
  `highway=cycleway`, designated paths/footways and `cycleway:*=track` are
  counted as cycle facilities; other car-free paths open to bikes appear in
  a separate table. Routing's `bike_infra` is unchanged.
- Mapped `DOUBLE SENS CYCLABLE NON MATERIALISE` to low speed. Report reruns
  preserve later sections, and elevation rewrites preserve smoothing
  sensitivity. The report notes Géovélo is itself based on OSM.
- Synthetic validation: 46 focused OSM tests passed; Ruff clean. No pilot or
  national build was run. Next, run the standalone command and confirm the
  requested under-60-second pilot timing.
- Command: `python -m mobgrid.osm.geovelo_report --state 2021 --config
  config/network.yaml --manifest config/sources.yaml --pilot-config
  config/pilot.yaml --report docs/data/step06_osm_pilot.md`.

### Step 6b: Géovélo department comparison (2026-11-24)

- Added configured `ame_d`/`ame_g` family mappings, including marked and
  unmarked contraflow, plus explicit exclusions and a 15 m matching threshold.
- The step 6 report lists distinct values, excluded counts/lengths, family
  lengths by commune, and Géovélo same-family matched shares.
- Both sources are clipped to the configured department; OSM uses way tags
  and ordered way geometry, not directed-edge lengths. Two-sided facilities
  count twice; separated paths count once.
- Synthetic report test covers two-sided OSM/Géovélo lanes, a two-way path,
  distinct values, exclusions and matching; report settings leave the edge
  cache signature unchanged. Focused OSM tests: 21 passed; Ruff clean.
- No pilot or national build was run. Run the step 6 report to inspect the
  real department values and matching results.

### Step 6b: elevation climb sensitivity (2026-11-24)

- Added report-only `--smoothing-windows`; alternative windows are computed
  from saved raw way elevations and do not rewrite stored profiles.
- Report whole-pilot and 10 km tile car climb per directed kilometre, the
  50 m PNG map and 10 flattest/hilliest tile lists.
- Tile IDs use 10 km EPSG:3035 squares; an edge is assigned by the midpoint
  of its endpoint coordinates. `--flat-tiles` and `--hilly-tiles` aggregate
  selected tile lists as the two reference zones.
- Synthetic flat-noise/slope and report-only CLI tests pass: 16 tests;
  Ruff clean. Pilot not run; choose reference tiles from the output.

### Step 6b: vectorized active costs (2026-11-24)

- Load sorted node ids, coordinates, raw elevations and endpoint tags once.
  Map edge nodes with `numpy.searchsorted`; flatten Arrow lists and gather
  segment endpoints without SQL windows or per-batch node-file reads.
- Preserve the loading, walk, speed-table, bike-riding, stops and writing
  timing logs; invalidate active/joined cost checkpoints, not car costs.
- Legacy-query comparisons on synthetic edges and the Monaco fixtures match
  walk/bike times and energies at 1e-6 relative tolerance.
- Focused validation: 25 tests passed and Ruff clean. Pilot not run; rerun to
  verify the requested walk/bike target of under 60 s and inspect timings.

### Step 6b: pilot active-cost corrections (2026-11-24)

- Use the approved surface-adjusted effective grade for bike rider power;
  physical grade still determines forces and paved outputs remain unchanged.
- Use raw node samples for stairs; floor stair time at flat walking time,
  and treat bike steps as pushing, without riding or stop components.
- Report any remaining zero-speed segments as errors; aggregate and print
  loading, walking, table, riding, stop and writing times across batches.
- Version active and joined cost checkpoints separately from the unchanged
  car checkpoint; matching edge, elevation and car outputs can be reused.
- Synthetic regressions cover the speed grid, stairs, checkpoint invalidation
  and timing logs: 88 passed, Ruff clean. No pilot rerun; inspect timings and
  reports after rerunning.

### Step 6b: pilot cost failure (2026-11-24)

- Added surface defaults for every known highway and bike class, including
  platform, corridor and steps.
- Masked bike divisions; positive-length zero-speed segments invalidate their
  edge costs and are counted with class, surface, grade and cap diagnostics.
- Synthetic grass/sand at -2.8% yields zero: configured power and coasting
  are both zero. No unsupported speed floor was introduced; the failed pilot
  log did not record its actual combinations.
- Both elevation commands use the existing pilot report name and migrate an
  identical old-name checkpoint without redoing elevation. The old duplicate
  is retained until that migration has run.
- The edge change adds only forced-rebuild/cache handling and does not change
  segment assignment SQL. Pilot assign-segments timing regression is unexplained.
- Validation: 19 touched-module tests passed; Ruff clean. No pilot rerun.

### Step 6b: resumable edge costs (2026-11-24)

- Added the cost CLI: checkpointed elevation, car and B1 active costs,
  one-to-one float32 cost output, and per-stage terminal/file timings.
- Cost parameters invalidate costs without rebuilding edge topology; explicit
  `--force` rebuilds edges. The step 6 report includes elevation coverage,
  class speed and urban-length diagnostics.
- Synthetic tests cover speed changes, reuse after interrupted joins, key
  validation, report values and interrupted forced builds: 26 passed;
  Ruff clean. Pilot performance remains unverified.

### Step 6b: elevation profiles, car density and timing (2026-11-24)

- Compute profiles and candidate clipped grades once per undirected
  `(way_id, segment_index)`; derive each direction from the shared result.
- Materialize only needed node columns for profile work and replace the
  smoothing update with a table join. Bump the completion checkpoint version.
- Monaco regression uses deterministic synthetic elevations and the original
  directed implementation as its baseline: 14,149 profiles and 314 clipped
  segments match, with a 1 mm elevation tolerance; raw and smoothed
  directed-climb totals also match to 1 mm.
- Elevation and car-speed stages now log elapsed times to terminal and dated
  files; car speeds also write a dated run summary.
- Car density rasterizes undirected segments to configured 50 m cells and
  uses tiled focal-disc convolution. A checkpoint reuses completed densities;
  the unused single-option fitting-strategy setting was removed.
- Synthetic and Monaco tests cover density splitting, disc and tile boundaries,
  configuration and checkpoint invalidation: 37 passed; Ruff clean. No pilot
  run. Monaco has no rural car labels, so fitted agreement and pilot timing
  remain unverified.

### Step 6b: way elevation and active costs (2026-11-23)

- Extract bridge, tunnel and layer tags; interpolate complete bridge/tunnel
  ways between endpoints by distance and store per-way and directed profiles.
- Report treated bridge/tunnel length once per way; preserve raw node samples.
- Smooth complete way-profile runs with a distance-weighted 50 m window;
  report directed mode climb before/after and incomplete counts.
- Separate read and write cursors prevent Arrow batch readers being truncated
  during smoothing and active-cost processing.
- Active costs clip walking and bike grades to their respective configured
  ranges; a grade report counts affected directed segments by mode/highway
  and ranks the 20 longest affected edges, retaining their original grades.
- The elevation report also provides these clipping diagnostics before the
  cost stage; synthetic tests compare both reports' counts.
- The elevation CLI checkpoints sampling and completed outputs in interim
  storage and writes dated logs and run summaries.
- Count only the additional braking and acceleration time beyond the
  cruising time already included in the edge ride, plus the signal wait.
- Stop energy is unchanged. The user confirmed this reading of section 9.7;
  the spec wording will be aligned separately.
- Synthetic tests: 27 passed, 1 pilot deselected; Ruff clean. No pilot ran.

### Step 6b: active-mode edge costs (2026-11-23)

- Added directed walk and bike costs from ordered node elevations, summing
  segment-by-segment grades; steps use the configured stair formula.
- The bike cost function reuses the grade speed table, applies provisional
  control probabilities and signal wait, and resolves surface/tracktype
  fallbacks. Unknown surface values fall back by highway and are counted.
- Elevation enrichment now stores nullable `elevation_m` on nodes for this
  later cost function. Incomplete profiles stay null and are counted.
- Bike energy stores its per-kg and drag parts separately, plus unloaded
  pedalling energy; separated length and positive climb are retained.
- Provisional caps, stop probabilities and surface maps are
  `TODO(confirm)` in `config/network.yaml`; signal timing remains in
  `config/energy.yaml`.
- Synthetic active-cost and elevation tests: 10 passed; Ruff and Pylance clean.
  No pilot, national build, download or raw-data modification was run.
- B2 stage orchestration and the Géovélo check remain.

### Step 6: edge-build performance (2026-11-23)

- Bumped edge-build cache version to 7; narrowed point and segment rows,
  materialized per-way attributes, sparse controls, directions and allowed edges,
  and computed degrees from allowed edges.
- Compute centroids, cells and tiles once per segment; reverse geometry only
  for output. Added elapsed logs for the new stages and disabled DuckDB
  insertion-order preservation for the CLI.
- Version 6 regression baselines match every edge column on synthetic cases
  and 14,149 Monaco directed edges; lengths match within 1 mm.
- Monaco local builds: 1.65 s old and 0.36 s new; these are not pilot timings.
  Replicated Monaco segment test: ordered-line length 0.381 s, pairwise lag
  0.466 s, so the existing ordered-line calculation was retained.
- CLI uses the existing extraction connection setup and configured interim
  path; memory limit and threads are not exposed by the loaded configs.
- Validation: 19 edge tests passed; Ruff and Pylance clean. No pilot run.
- Pilot timing and the under-five-minute target remain to be verified by user.

### Step 6b: bike speed-table groundwork (2026-11-23)

- Added the provisional grade grid, tolerances, class and highway speed caps.
- Coarse linear interpolation alone misses the requested 0.1 km/h tolerance
  near coasting and speed-cap transitions. Vectorised bracketed force balance
  refines the interpolated result; no scalar solver is called per segment.
- Tested speed and per-km energy against the energy package over all eight
  surfaces and the four requested caps, including grades beyond the grid.
- Speed-table and car-speed tuning no longer invalidate extraction or edge
  signatures. Existing extraction signatures change once on the next run.
- This is groundwork, not a cost stage: walk/bike edge aggregation, stops,
  surface fallbacks, cache orchestration and the Géovélo report remain.
- Validation: 54 changed-module tests passed, 1 pilot deselected; Ruff and
  Pylance clean.
- No pilot, national build, downloads or raw-data modification was run.

### Step 6b: car defaults and controls (2026-11-23)

- Added provisional default-only class speed caps, rural trunk/primary
  `oneway=yes` dual-carriageway defaults, and typed control delays.
- Edge-build version 6 retains raw `oneway`, separates stop and give-way,
  and classifies signalised crossings as signals without double-counting.
- Bike costs, the unified resumable cost stage and the Géovélo report remain:
  the spec and configuration do not set class caps, stop probabilities,
  surface fallbacks, interpolation tolerance or Géovélo family mappings.
- Validation: 29 changed-module tests passed; Ruff and Pylance clean.
- No pilot, national build, downloads or raw-data modification was run.

### Step 6b: Windows flat BD ALTI unpack (2026-11-23)

- Fixed Windows path-length failures by extracting only listed `.asc` tiles
  into short staging folders and flattening to `bdalti/D###/<tile>.asc`;
  department outputs no longer include the manifest source id.
- Checked native `tar --help` and option parsing: `-s` is unsupported;
  `--strip-components` with tile-only `-T` lists works, including mixed depths.
- Reject duplicate basenames case-insensitively and verify every tile before
  promotion/reuse. Failed staging trees use `\\?\` cleanup on Windows.
- The sampler already finds flat tiles with recursive discovery; unchanged.
- Regression fixtures use names listed from the real D016 archive. A tiny
  synthetic archive exercises native tar; flat final paths are under 160
  characters at the project root. No real archive extraction was run.
- Validation: 10 unpack tests passed; Ruff clean; no Pylance errors.
- Retry: `python -m mobgrid.osm.unpack_bdalti --area pilot`
  Move aside old nested/stale department outputs first; they are preserved.

### Step 6b: car free-flow costs (2026-11-21)

- Added configured car free-flow speeds with `maxspeed` precedence, class/context
  defaults, per-class realism factors, and speed-limit buckets; directional
  control counts and qualifying to-node degrees add configured delays.
- Untagged contexts use clipped car-edge length within a centroid radius.
  The threshold maximizes length-weighted agreement on tagged urban/rural
  edges; the report records agreement and urban directed-length shares by
  class, including zero-share classes.
- Defaults, class overrides, realism factors, density settings, delays and
  bucket bounds are provisional `TODO(confirm)` values in
  `config/network.yaml`; see `docs/progress.md`.
- Speed-only config changes no longer invalidate enriched edges, preserving
  BD ALTI results when tuning car parameters.
- Validation: 28 focused edge/elevation/unpack/speed tests passed; Ruff and
  Pylance diagnostics passed. No archive extraction, pilot or national build
  was run. Bike costs remain for step 6b.

### Step 6b: BD ALTI and edge elevation (2026-11-21)

- Added `mobgrid.osm.unpack_bdalti`: it intersects the configured pilot buffer
  with 2021 department contours, selects the corresponding `bdalti` manifest
  archives, and atomically unpacks them under `data/interim/bdalti/D###/`.
- Added the edge-elevation stage: node coordinates transform from EPSG:3035 to
  the BD ALTI EPSG:2154 grid; ordered OSM segments produce directional endpoint
  elevations, climb, descent and mean grade on `edges.parquet`.
- The elevation report separates nodes outside every tile from nodes with no
  valid interpolation sample. Added data pages for BD ALTI and commune contours.
- Synthetic elevation/unpack tests: 9 passed; Ruff and Pylance diagnostics
  passed. The native Windows `tar` listed the Gironde archive; no extraction,
  pilot, or national build was run.
- Unpack command: `python -m mobgrid.osm.unpack_bdalti --area pilot`
- Car free-flow speed and delay costs remain for step 6b.

### Step 6b: edge-cost groundwork (2026-11-21)

- Added a deterministic directed mode edge key and retained `tracktype` on
  edges for the requested one-to-one cost join and surface fallback. The edge
  cache version is 5. Segment identity also prevents repeated endpoint pairs
  on one way from duplicating control counts.
- Validation: 14 synthetic edge tests passed; Ruff and Pylance diagnostics
  passed.
- This is groundwork only: the BD ALTI unpack CLI, elevation integration,
  car and active-mode costs, resumable cost stage and Géovélo report remain.
  The BD ALTI and Géovélo dataset pages are still absent; document their
  verified schemas before using those datasets. No unpacking, pilot or
  national build was run.

### Step 6b: road classes (2026-11-21)

- Added the configured highway allowlist, filtering unknown ways before graph
  segmentation, and ensured ways without a highway remain foot-only.
  The edge-build cache version is 4.
- The edge report counts dropped ways by highway value and tabulates car
  non-road edges by their effective access tag and value; access rules for
  known classes are unchanged.
- Synthetic edge tests: 13 passed; Ruff and Pylance syntax checks passed.
  No pilot or national build was run. Elevation, costs and the Géovélo
  comparison remain to be implemented.
- Set section 9.7's provisional bike parameters k=37, P_max=200 W and
  descent cap=30 km/h in `config/energy.yaml` (`TODO(confirm)`: calibrate
  against observed commuter speeds). The energy-rate tests: 13 passed;
  Ruff passed.
- The bike solver now applies `v_max,desc` only on negative gradients,
  as confirmed by the user; class caps still apply on every gradient.
  At the configured P_0 the descent cap does not bind on level ground.
  The focused bike tests: 30 passed; Ruff passed.
- Elevation groundwork only: an ESRI ASCII grid sampler interpolates across
  aligned tile boundaries and propagates missing cells; a directional profile
  helper computes climb, descent and mean grade. Three synthetic tests passed;
  Ruff passed. Neither helper is connected to network outputs yet.
- There are no dataset pages for BD ALTI or Géovélo in `docs/data/`; their
  schemas and the remaining elevation, car and bike costs, cost-stage CLI,
  Géovélo check and unpack CLI remain to be completed. Windows `tar`
  successfully listed the Gironde `.7z`, so `py7zr` is not needed here.

### Step 6: OSM network pilot pipeline

- OSM extraction reads all nodes in the WGS84 area bounds, joins unnested way
  references to nodes covered by the once-simplified area, then reads only
  out-of-bounds nodes needed by retained ways. The stages are resumable and
  the extraction signature is version 3.
- Directed edges apply configured access exclusions, count direction-filtered
  controls along each edge, and record same-mode `to_degree`. Lengths use
  DuckDB's ellipsoidal spheroid function on ordered node coordinates (WGS84
  parameters, numerically GRS80-equivalent at sub-millimetre edge precision);
  geometry remains EPSG:3035.
- Edge fields and rules are documented in
  [docs/data/osm_edges.md](docs/data/osm_edges.md). The user generated the
  connectivity report at `docs/data/step06_osm_pilot.md`.
- Open points: area simplification tolerance is provisionally 10 m and
  `maxspeed=walk` is provisionally 5 km/h; both are marked `TODO(confirm)` in
  `config/network.yaml`.
- Final focused validation: 13 synthetic tests passed, 1 pilot test deselected,
  and Ruff passed. No PBF/pilot or national run was performed during validation.
- User ran the 2021 pilot extraction on 2026-11-19: cached stages were reused,
  yielding 438,593 ways and 3,688,154 nodes in 20.9 seconds, with no warnings.
  This timing is for the cached run, not a fresh extraction.
- User ran the 2021 pilot edge build: 4,464,264 directed mode edges and
  3,688,154 nodes in 1,487.6 seconds, with no warnings. The connectivity report
  was written; its acceptance results have not been assessed here.
- Run the pilot with:
  `python -m mobgrid.osm.extract --state 2021 --area pilot`
  `python -m mobgrid.osm.edges --state 2021 --area pilot --report docs/data/step06_osm_pilot.md`
- Follow-up fixes (2026-11-19): generic `access` no longer opens car-restricted
  non-road classes; bicycle-only access on footway and steps is enforced.
  Extraction retains the seven R2 hint tags, and edge rows now include nullable
  `speed_context`. Segment assignment uses cumulative graph-node counts and
  logs the elapsed time for every build stage, including connectivity/report.
- Monaco edge benchmark (2,503 ways, 10,909 nodes; same 14,203 edges): the
  prior range join took 2.180 s overall (0.097 s assigning segments); the
  linear assignment took 2.934 s (0.153 s assigning segments). This is one
  small sequential sample, not evidence of a pilot speedup. The requested
  under-5-minute pilot target remains unverified; no 2021 pilot or national run
  was performed.
- Current focused validation: 17 OSM tests passed, 1 pilot test deselected;
  Ruff passed. The report header now describes ellipsoidal lengths from the
  ordered node latitude/longitude coordinates.

### Notes moved from the steps table (2026-11-21)

| Step | Content | Status | Branch | Notes |
|---|---|---|---|---|
| 0 | GTFS rebuilding test | merged | `step/gtfs-rebuild-test` | **2026-10-15/16 national policy (no manual review):** tram alone keeps the automatic OSM relation rule (confirmed parameters); metro, rail, bus and ferry (including BHNS/express, whose own automatic cut rule is retired) keep every 2026 route in both past states by default, changed only by the PT openings list's auto-applied exact/stop-confirmed, high/medium-confidence matches. A `keep`/`modify` row gives no instruction at all (falls through to the tram rule or default keep); a `remove` row's effect depends on `change_type` -- `new_line`/`reopening` drop the route, `extension` cuts it at its old terminus, `new_station` removes only that stop (`mobgrid.pt.pt_changes.OpeningDerivedChange.instruction_at`, `mobgrid.pt.route_edits`); several rows' cuts/stop-removals on one route combine rather than any one dropping it; a `suspension` row never produces an instruction (settled decision: a temporary works closure does not remove a line from a state meant to represent the normal network). Precedence: openings list > tram automatic rule > default keep (`mobgrid.pt.pt_policy.resolve_route_presence`, tested). `to_review`/`not_applied` are informational only; nothing in the pipeline reads them. Lines closed before 2026 (`state` `add`) are left out and listed in the report as a known gap. The metro/bus/ferry/rail calibration numbers are kept in `config/gtfs_rebuild.yaml`/the report as a historical/screening reference only; metro's false changes are not investigated further. All 47 high/medium-confidence networks now have a resolved GTFS resource, including `Twisto (Caen la mer)`, mapped against the existing Normandy regional aggregate (resource 81942) rather than acquiring a second, duplicate-trip dedicated feed (2026-10-16 decision: an aggregate-only network is an accepted, normal outcome, not a gap to close). `mobgrid.pt map-and-apply-all` maps and applies every network in one resumable, logged, offline-only batch run (never downloads; raises a clear error if a resource isn't acquired yet), grouping network-name aliases by resolved GTFS resource id so each resource is read exactly once. `acquire --check-aom-coverage` confirmed 0 of 1,127 metropolitan AOMs are fully uncovered (865, including Twisto, have only indirect/aggregate coverage, accepted as sufficient -- no population filter needed). National run complete: 47 of 47 networks mapped, 53 rows applied (69 route-level edits), 5 rows left as accepted residual gaps (IDF-17, GES-06, NAQ-03, OCC-05, PAC-05), 0 regressions on reconciliation. The future national PT-build step must keep only the dedicated producer feed's copy of an agency that also appears in a broader aggregate, before any trip-level dedup across feeds (recorded below under "Open points from the spec"). Merged into `main` 2026-10-16. |
| 7 | `mobgrid/energy` | review | `step/mobgrid-energy` | Leg formulas of section 9.1 to 9.8: `rates.py` (`config/energy.yaml` loader, KH/Compendium activity rates, `sedentary_energy_kj`), `walk.py` (Tobler speed, Minetti gradient factor, stairs), `bike.py` (force-balance speed solver, ride/stop energy, separated-infra factor, e-bike pedelec assist), `legs.py` (`Leg` chain T=sum(t)/E=sum(e), waiting, PT ride crowding, car congestion). Reproduces every section 9.2 reference rate and the 9.3/9.7 checks (gradient factors, 1 km flat walk 160/211 kJ, 10 m stairs 22.9 kJ, 16 km/h mechanical power ~52.5 W, +-mass speed changes, one-stop energy). Second round of fixes (user-reported, 2026-10-19): unified clamp formula `P_r = clamp(P0.(1+k.i), 0, Pmax)` on every grade fixes a zero-speed plateau just past a flat descent (`bike.select_ride_power_w`/`ride_speed_and_power`/`required_power_w`); e-bike rider/motor energy now split by `s_r = P_r/(P_r+P_m)` on every edge and stop (`ebike_ride_speed_and_power`, `ebike_rider_share`, `bike_ride_energy_kj`/`stop_energy_kj`'s new `rider_share`); `climbing_work_j_per_kg` is now signed; bike stops add time (`bike.stop_time_s`, new `config.bike.stops`, TODO(confirm)); terminal walking legs use the active rate set's c0, not a hardcoded Compendium; added the carpool passenger (`config.car.carpool_passenger`, TODO(confirm)) alongside the household passenger; bus/train rides use the first-phase standing shares of 9.5 everywhere, not seated-only; new `config.bike.ebike.effort_factor_by_level` (TODO(confirm), default 1.0) hooks a future rider-effort-vs-assist calibration. **Third round (after step 11's P0 calibration and a new `docs/spec/09_trip_legs_energy.md`):** section 9.7 gains an unloaded pedalling cost, `e = m.u_ped.t_ped` with `u_ped` = 1 net MET/pedalled minute (`config.bike.pedalling_unloaded_net_met`, ACSM/Swain 2000, not TODO(confirm): a literature value), on the rider's own mass only, for bike and e-bike riders alike, not scaled by `rider_share` or `separated_infra_factor` (`bike.unloaded_pedalling_energy_kj`, new keyword-only params of `bike.bike_ride_energy_kj`); `config.bike.power.p0_w` is now `34.8` (confirmed by step 11's EMP calibration, no longer `null`), `k`/`p_max_w`/`v_max_descent_kmh` stay TODO(confirm). `checks.py`'s own illustrative set-A P0 (~52.5 W, self-derived from the 16 km/h force-balance check) is unaffected; its "metabolic rate, 16 km/h flat" check now expects ~18.2 kJ/min (was ~13.1) with the unloaded term added; F4's roll/climb/stops/drag decomposition deliberately excludes the unloaded term (documented: a mechanical-work-only split). Verification command `python -m mobgrid.energy.checks --out docs/data/step7_energy` (`checks.py`, matplotlib dev dependency) writes 10 PNGs (F1-F10, F7 now also covers F7b's fixed-time panels, F9 now has three panels A/B/C) plus `docs/data/step7_energy_checks.md` (27 PASS/0 FAIL/10 COMPARE, rerun after the third round); run once, committed. Ruff clean; 71 energy tests pass (361 total, 3 pilot deselected). |
