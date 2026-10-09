# Progress

Read this file at the start of every task and update it at the end.

_Last updated: 2026-10-09 by Copilot_

## Steps (table of section 14.5)

| Step | Content | Status | Branch | Notes |
|---|---|---|---|---|
| — | Repository skeleton (`/bootstrap`) | done | `step/bootstrap-skeleton` | uv workspace, package layout, configuration validation; Ruff and 3 tests pass (pinned Python 3.12.15) |
| 0 | GTFS rebuilding test | not started | | |
| 1 | `common`: config, grid cells, DuckDB I/O | review | `step/common-foundations` | Config validation; cell ids/codes, nesting, neighbour stencil and tiles; Arrow/Parquet helpers; Ruff clean and 12 tests pass |
| 2 | `acquire`: manifest and downloaders | review | `step/acquire` | Configured pilot source catalog; resumable, size-checked and checksum-verified HTTP downloads; Geofabrik MD5; restricted-file registration; API discovery helpers with per-source auth header/scheme; HTML-page detection; `verified` tracking; dry-run CLI. No real downloads run. Ruff clean; 40 tests pass. |
| 2a | Source URLs and national acquisition coverage | review | `data/source-urls` | Both requested updates combined in one commit with user approval. 726 file/registration entries; direct INSEE/SDES/Géovélo/CARS/NUTS/Eurostat URLs; producer-only national GTFS inventory; 96 metropolitan BD ALTI archives; 26 neighbouring OSM extracts; anonymous Overture Parquet extraction with national box. Ruff clean; 61 tests pass. Metadata/HEAD requests only; no data files downloaded. |
| 2b | Source URL fixes: OSM size-only verification, TCL Lyon GTFS resource | review | `data/source-urls` | Neighbouring OSM extracts verified by `Content-Length` instead of a nonexistent `.md5`; TCL Lyon's dropped/overridden GTFS resource now resolves to the current SYTRAL Mobilités feed with a Mobility Database fallback. Ruff clean; 67 tests pass. Dry run: 0 blocked entries (down from 27). |
| 2c | Audit of the remaining 12 excluded community GTFS resources | review | `data/source-urls` | Checked, for each of the 12 datasets with a community-tagged excluded GTFS resource, whether that dataset keeps another producer GTFS resource; all 12 do (true duplicates), so none needed a TCL-Lyon-style override. Added a `discover_gtfs` safeguard that logs a warning if a community exclusion would ever leave a dataset with zero producer GTFS resources, so a future case is caught automatically. Ruff clean; 68 tests pass. |
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

## Assumptions to check

- 2026-10-09, bootstrap, the initial base configuration contains the EPSG:3035 coordinate system and 200 m/1 km resolutions; `config/base.yaml`.

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
- [ ] Step 0: verify liO/Rémi stops inside the 2026 Couserans-Pyrénées and Marche Occitane – Val d'Anglin EPCI polygons
- [x] Neighbouring OSM extracts: Geofabrik publishes no `.md5` sidecar for dated regional files; verified by `Content-Length`-based size instead
- [ ] Acquisition API resources: direct file URLs, source-specific licenses, and expected checksums where providers publish them
- [ ] Lyon BHNS Part-Dieu – Sept-Chemins: opening date (section 5.6)
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
