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
`construction`, lifecycle-tag presence, the ordered EPSG:3035 point list,
and WKB linestring geometry. A way appearing in two relations appears twice.

### `stops.parquet`

One row per member stop/platform node, with member order and role, selected
OSM tags, EPSG:3035 `x`/`y`, and WKB point geometry.

`_stages/` contains resumable intermediate Parquet files. `_SUCCESS.json` is
written only after all final tables have been published.
