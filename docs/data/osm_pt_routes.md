# OpenStreetMap public-transport route relations

- **Source:** dated Geofabrik OSM PBF extracts configured in
  `config/sources.yaml`.
- **Vintages:** 1 January 2022 and 1 January 2024.
- **Local cache:** `data/interim/osm_pt_routes/{date}/`.
- **CRS:** geometry and coordinate columns are EPSG:3035 metres.
- **Method:** three filtered `ST_ReadOSM` passes: selected route relations,
  their member ways, then the nodes needed by those members. DuckDB uses 60%
  of physical RAM and spills under `data/interim/osm_pt_routes/_duckdb_temp/`.

Only relations tagged `type=route` and one of `bus`, `trolleybus`, `coach`,
`tram`, `subway`, `light_rail`, `train`, `monorail`, or `ferry` are retained.
Relation-member order, type and role come from the `refs`, `ref_types` and
`ref_roles` arrays returned by `ST_ReadOSM`.

## Parquet tables

### `relations.parquet`

| Column | Type | Meaning |
|---|---|---|
| `relation_id` | int64 | OSM relation id |
| `ref` | string | Line reference |
| `name` | string | Relation name |
| `network` | string | OSM network tag |
| `operator` | string | OSM operator tag |
| `route` | string | Exact OSM route mode |

### `members.parquet`

| Column | Type | Meaning |
|---|---|---|
| `relation_id` | int64 | Parent relation |
| `sequence` | int64 | One-based member order |
| `member_id` | int64 | OSM member id |
| `member_type` | string | `node`, `way`, or `relation` |
| `role` | string | OSM member role |

### `ways.parquet`

One row per relation-member way. It preserves `railway`, `highway`,
`busway` and `lanes:bus` (stored as `lanes_bus`), `construction`,
lifecycle-tag presence, the ordered EPSG:3035 point list, and WKB
linestring geometry. A way appearing in two relations appears twice.

`busway`/`lanes_bus` support the 2026-10-14 BHNS/express bus decision
(docs/progress.md): a way is dedicated bus infrastructure if
`highway = 'busway'`, or `busway` or `lanes:bus` is present, and it is not
under construction or proposed. Adding these columns bumped the required
`ways.parquet` schema; `extract_osm_pt_routes` detects a cache missing them
and rebuilds only `ways.parquet` from the already-cached
`ways_raw.parquet`/`nodes_raw.parquet`/`members.parquet` stages, without
re-scanning the PBF.

### `stops.parquet`

One row per member stop/platform node, with member order and role, selected
OSM tags, EPSG:3035 `x`/`y`, and WKB point geometry.

`_stages/` contains resumable intermediate Parquet files. `_SUCCESS.json` is
written only after all final tables have been published.

## GTFS calibration tables

Calibration performs spatial work once and caches scalar Parquet tables under
`data/interim/gtfs_rebuild/calibration_scratch/relation_tables/`:

- `patterns.parquet`: the main reference-date pattern of each retained route,
  limited to routes reaching a test EPCI plus configured known cases;
- `relation_distances.parquet`: `(date, network, pattern, stop sequence,
  relation)` pairs within the largest calibrated radius, with distance in
  metres, relation ref, in-service status and a fallback-stop marker;
- `name_matches.parquet`: normalised ref/name matches among same-mode relations
  whose bounding box comes within 1 km of a pattern stop, including the
  network/operator affiliation tie-break score;
- `precompute.json`: cache version, input signature, dates, maximum radius and
  row counts.

DuckDB applies bounding-box filters before every exact `ST_Distance`. Grid
evaluation reads only these scalar tables; it performs no geometry operation
and never loads national relation geometry into Python.
