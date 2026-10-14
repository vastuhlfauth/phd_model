# Progress

Read this file at the start of every task and update it at the end.

_Last updated: 2026-10-14 by Copilot_

## Steps (table of section 14.5)

| Step | Content | Status | Branch | Notes |
|---|---|---|---|---|
| — | Repository skeleton (`/bootstrap`) | done | `step/bootstrap-skeleton` | uv workspace, package layout, configuration validation; Ruff and 3 tests pass (pinned Python 3.12.15) |
| 0 | GTFS rebuilding test | done | `step/gtfs-rebuild-test` | Relation-based rebuild (name match, then geometry; in-service tracks of any same-mode relation give coverage, not only the matched one; cut-then-theta for tram/metro/rail) replaces the failed stop-only calibration. Bus, ferry and rail are never auto-applied (screening/review only); tram and metro thresholds are confirmed. Known limitations: OSM sometimes tags tracks in service before their documented opening (a data gap, patched case by case in `pt_changes.yaml`'s `confirmed` list); bus and rail OSM relation/way mapping is incomplete nationally, kept to manual review via `to_review`/`not_applied`. |
| 1 | `common`: config, grid cells, DuckDB I/O | review | `step/common-foundations` | Config validation; cell ids/codes, nesting, neighbour stencil and tiles; Arrow/Parquet helpers; Ruff clean and 12 tests pass |
| 2 | `acquire`: manifest and downloaders | review | `step/acquire` | Configured pilot source catalog; resumable, size-checked and checksum-verified HTTP downloads; Geofabrik MD5; restricted-file registration; API discovery helpers with per-source auth header/scheme; HTML-page detection; `verified` tracking; dry-run CLI. No real downloads run. Ruff clean; 40 tests pass. |
| 2a | Source URLs and national acquisition coverage | review | `data/source-urls` | Both requested updates combined in one commit with user approval. 726 file/registration entries; direct INSEE/SDES/Géovélo/CARS/NUTS/Eurostat URLs; producer-only national GTFS inventory; 96 metropolitan BD ALTI archives; 26 neighbouring OSM extracts; anonymous Overture Parquet extraction with national box. Ruff clean; 61 tests pass. Metadata/HEAD requests only; no data files downloaded. |
| 2b | Source URL fixes: OSM size-only verification, TCL Lyon GTFS resource | review | `data/source-urls` | Neighbouring OSM extracts verified by `Content-Length` instead of a nonexistent `.md5`; TCL Lyon's dropped/overridden GTFS resource now resolves to the current SYTRAL Mobilités feed with a Mobility Database fallback. Ruff clean; 67 tests pass. Dry run: 0 blocked entries (down from 27). |
| 2c | Audit of the remaining 12 excluded community GTFS resources | review | `data/source-urls` | Checked, for each of the 12 datasets with a community-tagged excluded GTFS resource, whether that dataset keeps another producer GTFS resource; all 12 do (true duplicates), so none needed a TCL-Lyon-style override. Added a `discover_gtfs` safeguard that logs a warning if a community exclusion would ever leave a dataset with zero producer GTFS resources, so a future case is caught automatically. Ruff clean; 68 tests pass. |
| 2d | France OSM sizes, resilient acquisition batches and reruns | review | `fix/osm-size` | France uses HEAD sizes without MD5 sidecars; OSM discovery refreshes all 28 extracts. Failed acquisitions no longer abort the batch; summary counts/reasons and exit 1 on failures. Recorded matching files skip network requests and preserve verification/date. Tests first; Ruff clean; 81 tests pass. |
| 2e | Acquisition robustness, own GTFS archives, offline feed checks, Filosofi 2019 | review | `fix/acquire-robustness` | Per-file atomic manifest persistence; Windows replacement retries and short-lived readers; strict latest-own-archive fallback; offline GTFS inventory command; covered-resource exclusions; both Filosofi 2019 archives acquired. Tests first; Ruff clean; 108 tests pass. Offline check: 551 downloaded, 536 passing feeds, 47 expired, 15 invalid/unusable, 18 flex indicators; no files deleted. |
| 3 | `landgrid/origins` | not started | | |
| 4 | `landgrid/jobs` | not started | | |
| 5 | `landgrid/services`, `nature`, `social`, `destinations` | not started | | |
| 6 | `mobgrid/osm` | not started | | |
| 7 | `mobgrid/energy` | not started | | |
| 8 | `mobgrid/graph` | not started | | |
| 9 | `mobgrid/layers/gridgraph.py` | not started | | |
| 10 | `mobgrid/od` | not started | | |
| 11 | `mobgrid/budget` | not started | | |

Status values: not started, in progress, review, merged.

## Data pages written (`/schema`)

- (none yet)

## Decisions taken while coding

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

## Assumptions to check

- 2026-10-09, bootstrap, the initial base configuration contains the EPSG:3035 coordinate system and 200 m/1 km resolutions; `config/base.yaml`.
- 2026-10-12, step 0, a pattern's expected outcome defaults to "kept" at
  both state dates unless it is one of section 5.6's listed known
  changes; this lets the calibration score every bus/tram/metro route of
  the test networks, not just the handful of explicitly named cases.
- 2026-10-13, step 0, routes not listed as labelled known cases in each test
  area are presumed unchanged for false-change scoring. This is not ground
  truth and is reported separately from known-case precision/recall/F1.

## Open points from the spec

Each item stays open until a value is decided; the value goes into `config/`.

- [ ] Inhabited 200 m cells: about 2.3 million (section 4.5)
- [ ] EMC² surveys: access conditions (section 5.3)
- [ ] EMC² surveys: zoning and leg detail (section 5.4)
- [ ] Géovélo cycle infrastructure: a version for 2021 (sections 5.3 and 8.1)
- [x] Exact earliest Géovélo 2022 monthly vintage and direct resource URL: 2022-07-18, proxy for 2021
- [x] Filosofi 2021 imputed 200 m benchmark: published file URL configured
- [x] Overture places: release 2026-09-23.1 and national Parquet extraction configured
- [ ] Archive Overture before approximately 2026-11-22; no data acquisition has been run
- [x] Step 0: TCL Lyon GTFS now resolves to the current SYTRAL Mobilités resource 81943 (producer URL + Mobility Database fallback); the deprecated 65812 resource is dropped
- [x] Step 0: verify liO/Rémi stops inside the 2026 Couserans-Pyrénées and Marche Occitane – Val d'Anglin EPCI polygons: Couserans-Pyrénées is covered (30 liO patterns); Marche Occitane has no liO/Rémi/SNCF stop inside its polygon
- [x] Neighbouring OSM extracts: Geofabrik publishes no `.md5` sidecar for dated regional files; verified by `Content-Length`-based size instead
- [x] France OSM extracts: same size-only verification for both vintages; section 5.3's dated-extract `.md5` claim is incorrect (user-approved override, specification left unchanged)
- [ ] Acquisition API resources: direct file URLs, source-specific licenses, and expected checksums where providers publish them
- [ ] Lyon BHNS Part-Dieu – Sept-Chemins: opening date (section 5.6)
- [ ] Step 0 relation parameters: run the approved Luxembourg smoke, national
  relation extractions and calibration; review `kept-renamed`/`dropped`
  candidates and confirm recommended r, k, theta and geometry shares
- [ ] PT: rule for a regular service whose `calendar`/`calendar_dates` window has already expired by the state/reference date — shift it to its last valid week (e.g. same weekday pattern one week back) or drop it entirely (section 8.6/14.4)
- [ ] Car ownership model: functional form, e.g. ordered or multinomial logit (section 6.4)
- [ ] Public-sector jobs: default surface by amenity type when there is no building footprint (section 7.2)
- [ ] PT engine: departure sampling if plain RAPTOR is kept, after the benchmark (section 8.6)
- [ ] Crush loads per seat (LF_max): check against operators' vehicle data (section 9.5)
- [ ] EMP 2019: leg detail and durations in the public tables (section 9.9)
- [ ] PT fares and passes by network (section 9.10)
- [ ] Bike and e-bike prices and lifetimes (section 9.10)
- [ ] Fiscal power of the car fleet by cell, 5 CV by default (section 9.10)
- [ ] Opportunity-curve storage: number of job sectors counted, 6 by default (section 10.2)
- [ ] Google Routes API: pricing tier of `staticDuration`, `polyline` and traffic on polylines (section 12)
- [ ] Traffic counts: national and departmental sources (section 12)
