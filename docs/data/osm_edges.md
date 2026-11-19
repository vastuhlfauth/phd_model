# OSM network edges

- **Sources:** `osm-2022` for state 2021 and `osm-2024` for state 2023;
  source paths are resolved through `config/sources.yaml`.
- **Pilot area:** communes whose 2021 contour `departement` is `33`, dissolved
  and buffered by the configured `halo_km` in EPSG:3035.
- **National area:** metropolitan communes, excluding Corsica and overseas
  departments, dissolved and buffered with the same configured halo.
- **Read passes:** read all tagged nodes in the buffered geometry's WGS84
  bounding box, then join unnested way references to nodes covered by the
  topology-preserving simplified area polygon, then read only the out-of-box
  nodes of those ways. The simplification tolerance is configured in
  `config/network.yaml`; the national bounding box covers the national extract.
- **Intermediate cache:** `data/interim/osm/{state}/{area}/`; it stores
  in-box nodes, kept way candidates, out-of-box nodes of kept ways, area WKB,
  and filtered raw `ways.parquet` and `nodes.parquet`. Control nodes are taken
  from the in-box node pass. Each completed stage is reused only when its
  input signature and required schema are current.
- **Base outputs:** `data/base/network/{state}/{area}/edges.parquet` and
  `nodes.parquet`. Node coordinates and edge geometry use EPSG:3035; edge
  lengths are ellipsoidal metres summed from the ordered OSM node coordinates.
  DuckDB's spheroid function uses WGS84 parameters, numerically equivalent to
  GRS80 at sub-millimetre precision for road-edge lengths. No elevation or
  travel times are populated in this step.

## Edge columns

| Column | Type | Meaning |
|---|---|---|
| `way_id` | int64 | OSM way id |
| `from_node_id`, `to_node_id` | int64 | Directed edge endpoints |
| `is_forward` | bool | True follows the stored way reference order |
| `mode` | string | One row for each permitted direction and mode: car, bike or foot |
| `node_ids` | list[int64] | Ordered OSM node ids along the segment |
| `length_m` | float64 | Ellipsoidal length in metres from the ordered node latitude/longitude coordinates |
| `highway` | string, nullable | OSM road class |
| `maxspeed_kmh` | float64, nullable | Parsed maxspeed in km/h |
| `speed_context` | string, nullable | Context parsed from `zone:traffic`, `source:maxspeed`, `maxspeed:type` or `zone:maxspeed` (`urban`, `rural`, `zone30`, `motorway`); retained independently of numeric maxspeed |
| `motorroad` | bool | `motorroad=yes` (also accepts `true` and `1`) |
| `lanes` | string, nullable | Raw `lanes` value |
| `car_access`, `bike_access`, `foot_access` | bool | Effective access flags before one-way filtering |
| `bike_infra` | string, nullable | Direction-specific class from the table below |
| `surface`, `smoothness` | string, nullable | Raw OSM values |
| `busway`, `lanes_bus`, `lanes_psv` | string, nullable | Raw bus-lane values |
| `signal_count`, `stop_count`, `crossing_count`, `mini_roundabout_count` | int8 | Direction-filtered control-node counts along the edge, excluding its first node |
| `to_degree` | int64 | Distinct neighbouring graph nodes of `to_node_id` for this mode, considering incoming and outgoing edges |
| `cell_1km_id` | int64 | 1 km cell id of the edge-geometry centroid |
| `tile_id` | int64 | Configured tile id of the edge-geometry centroid |
| `geometry_wkb` | binary | Directed EPSG:3035 line geometry |

`nodes.parquet` has `node_id` (int64), `x` and `y` (float64 metres in
EPSG:3035), `tags` (OSM tag map), and `graph_node` (bool). Graph nodes are way
ends and nodes shared by at least two kept ways. Other retained way nodes and
area traffic-control nodes are also present with `graph_node=false`.
The extracted way tag maps also retain `zone:traffic`, `source:maxspeed`,
`maxspeed:type`, `zone:maxspeed`, `tracktype`, `service` and `area` for
downstream speed and surface processing.

## Access and direction rules

All rule values are configured in `config/network.yaml`. A mode-specific tag
has precedence over generic `access`. Values are split on `;`; access is denied
only when every listed value is one of `no`, `private`, `agricultural`,
`forestry`, `delivery`, `emergency` or `use_sidepath`. Car access on footway,
path, pedestrian, cycleway and bridleway requires an explicit `motorcar` or
`motor_vehicle` value of `yes`, `destination`, `permissive`, `designated` or
`customers`; generic `access` does not open these classes. Steps, corridors,
bus stops, platforms and elevators never allow cars. Bike access on footway
and steps requires an explicit `bicycle` tag; pedestrian ways remain open to
bikes. The highway classes
`construction`, `proposed`, `abandoned`, `razed`, `disused`, `raceway`,
`bus_guideway`, `escape` and `elevator` are unconditionally excluded.

| Mode | Access-tag precedence | Default/exclusion rules | Direction rules |
|---|---|---|---|
| Car | `motorcar`, `motor_vehicle`, `access` | `platform`, `busway`, steps, corridors, bus stops and elevators are unconditionally excluded; generic `access` cannot open footway, path, pedestrian, cycleway or bridleway | `oneway=yes/1/true` forward only; `-1` reverse only; no/unknown permits both. Roundabouts, circular junctions and motorways imply forward one-way |
| Bike | `bicycle`, `access` | Motorways, motorway links and `trunk` + `motorroad=yes` are unconditional exclusions; footway and steps require explicit `bicycle`; pedestrian ways are allowed at walking pace | `oneway:bicycle` overrides; `cycleway=opposite*` permits both directions; otherwise inherits `oneway`, with `cycleway:*:oneway=no` allowing both and `-1` allowing reverse travel |
| Foot | `foot`, `access` | Sidewalks and footway, path, steps, pedestrian and living-street classes permit walking; motorways, motorway links, and trunk + `motorroad=yes` are excluded | Both directions |

Traffic-control tags are read for `highway=traffic_signals`, `stop`,
`give_way`, `crossing` and `mini_roundabout`. Each directed edge counts its
ordered OSM nodes except its first: signals contribute to `signal_count`,
stops and give-ways to `stop_count`, crossings to `crossing_count`, and
mini-roundabouts to `mini_roundabout_count`. `traffic_signals:direction`
overrides `direction` for signals; other controls use `direction`. Values
`forward` and `backward` are relative to the stored way order and are compared
with the edge's `is_forward` flag. `to_degree` counts distinct neighboring
graph nodes among edges permitted for the same mode, in either direction.

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
