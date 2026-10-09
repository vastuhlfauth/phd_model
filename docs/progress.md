# Progress

Read this file at the start of every task and update it at the end.

_Last updated: 2026-10-09 by Copilot_

## Steps (table of section 14.5)

| Step | Content | Status | Branch | Notes |
|---|---|---|---|---|
| — | Repository skeleton (`/bootstrap`) | done | `step/bootstrap-skeleton` | uv workspace, package layout, configuration validation; Ruff and 3 tests pass (pinned Python 3.12.15) |
| 0 | GTFS rebuilding test | not started | | |
| 1 | `common`: config, grid cells, DuckDB I/O | review | `step/common-foundations` | Config validation; cell ids/codes, nesting, neighbour stencil and tiles; Arrow/Parquet helpers; Ruff clean and 12 tests pass |
| 2 | `acquire`: manifest and downloaders | not started | | |
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

## Assumptions to check

- 2026-10-09, bootstrap, the initial base configuration contains the EPSG:3035 coordinate system and 200 m/1 km resolutions; `config/base.yaml`.

## Open points from the spec

Each item stays open until a value is decided; the value goes into `config/`.

- [ ] Inhabited 200 m cells: about 2.3 million (section 4.5)
- [ ] EMC² surveys: access conditions (section 5.3)
- [ ] EMC² surveys: zoning and leg detail (section 5.4)
- [ ] Géovélo cycle infrastructure: a version for 2021 (sections 5.3 and 8.1)
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
