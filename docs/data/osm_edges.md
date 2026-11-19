# OSM network edges

- **Sources:** `osm-2022` for state 2021 and `osm-2024` for state 2023;
  source paths are resolved through `config/sources.yaml`.
- **Pilot area:** communes whose 2021 contour `departement` is `33`, dissolved
  and buffered by the configured `halo_km` in EPSG:3035.
- **National area:** metropolitan communes, excluding Corsica and overseas
  departments, dissolved and buffered with the same configured halo.
- **Read bounds:** the buffered geometry is transformed to WGS84 and its
  bounding box is retained with the area cache. PBF ways are then clipped by
  node-in-polygon, not by the rectangular read bounds.
- **Intermediate cache:** `data/interim/osm/{state}/{area}/`; it stores
  candidate ways, their nodes, control nodes, area WKB, and filtered raw
  `ways.parquet` and `nodes.parquet`. Each completed stage is reused only when
  its input signature and required schema are current.
- **Base outputs:** `data/base/network/{state}/{area}/edges.parquet` and
  `nodes.parquet`. Coordinates and lengths use EPSG:3035 metres; edge geometry
  is WKB. No elevation or travel times are populated in this step.

## Edge columns

| Column | Type | Meaning |
|---|---|---|
| `way_id` | int64 | OSM way id |
| `from_node_id`, `to_node_id` | int64 | Directed edge endpoints |
| `is_forward` | bool | True follows the stored way reference order |
| `mode` | string | One row for each permitted direction and mode: car, bike or foot |
| `node_ids` | list[int64] | Ordered OSM node ids along the segment |
| `length_m` | float64 | EPSG:3035 geometry length in metres |
| `highway` | string, nullable | OSM road class |
| `maxspeed_kmh` | float64, nullable | Parsed maxspeed in km/h |
| `motorroad` | bool | `motorroad=yes` (also accepts `true` and `1`) |
| `lanes` | string, nullable | Raw `lanes` value |
| `car_access`, `bike_access`, `foot_access` | bool | Effective access flags before one-way filtering |
| `bike_infra` | string, nullable | Direction-specific class from the table below |
| `surface`, `smoothness` | string, nullable | Raw OSM values |
| `busway`, `lanes_bus`, `lanes_psv` | string, nullable | Raw bus-lane values |
| `signal_count`, `junction_count` | int8 | Control-node indicators at `to_node_id` |
| `cell_1km_id` | int64 | 1 km cell id of the edge-geometry centroid |
| `tile_id` | int64 | Configured tile id of the edge-geometry centroid |
| `geometry_wkb` | binary | Directed EPSG:3035 line geometry |

`nodes.parquet` has `node_id` (int64), `x` and `y` (float64 metres in
EPSG:3035), `tags` (OSM tag map), and `graph_node` (bool). Graph nodes are way
ends and nodes shared by at least two kept ways. Other retained way nodes and
area traffic-control nodes are also present with `graph_node=false`.

## Access and direction rules

All rule values are configured in `config/network.yaml`. A mode-specific tag
has precedence over generic `access`; an explicit `no` or `private` denies
access unless a higher-precedence mode tag explicitly permits it.

| Mode | Access-tag precedence | Default/exclusion rules | Direction rules |
|---|---|---|---|
| Car | `motorcar`, `motor_vehicle`, `access` | Excludes footway, path, steps, pedestrian, cycleway and bridleway unless a more-specific access tag allows the way | `oneway=yes/1/true` forward only; `-1` reverse only; no/unknown permits both. Roundabouts and motorways imply forward one-way |
| Bike | `bicycle`, `access` | Excludes motorways, motorway links, footways, steps and pedestrian ways unless `bicycle` explicitly allows them; motorways, motorway links and `trunk` + `motorroad=yes` are unconditional exclusions | `oneway:bicycle` overrides; `cycleway=opposite*` permits both directions; otherwise inherits `oneway`, with `cycleway:*:oneway=no` allowing both and `-1` allowing reverse travel |
| Foot | `foot`, `access` | Sidewalks and footway, path, steps, pedestrian and living-street classes permit walking; motorways, motorway links, and trunk + `motorroad=yes` are excluded | Both directions |

Traffic-control tags are read for `highway=traffic_signals`, `stop`,
`give_way`, `crossing` and `mini_roundabout`. `signal_count` is one for a
traffic-signal endpoint; `junction_count` is one for a stop, give-way,
crossing or mini-roundabout endpoint.

## Bike infrastructure classes

For `cycleway:left` and `cycleway:right`, the left/right suffix is relative to
the OSM way's stored direction: right applies to forward edges and left to
reverse edges. Classification priority is separated, painted, bus lane,
low-speed, then mixed traffic.

| Class | OSM tags and conditions |
|---|---|
| `separated_track_path` | `highway=cycleway`; `cycleway[(:both|:left|:right)]=track`; or `highway=path` with `bicycle=designated` |
| `painted_lane` | `cycleway[(:both|:left|:right)]=lane` |
| `bus_lane` | `cycleway[(:left|:right)]=share_busway`; `cycleway=share_busway`; or a configured busway lane with bike access |
| `low_speed` | `highway=living_street`; parsed `maxspeed` at or below 30 km/h; or `bicycle_road=yes` |
| `mixed_traffic` | Any other bike-accessible way |

## Maxspeed parsing

The configured French symbolic values are `FR:urban` = 50, `FR:rural` = 80,
`FR:zone30` = 30 and `FR:motorway` = 130 km/h. Numeric km/h values and mph
values are converted; `walk` is provisionally 5 km/h (`TODO(confirm)`), while
`none` and unrecognized values are null.
