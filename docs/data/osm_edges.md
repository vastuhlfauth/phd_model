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
  GRS80 at sub-millimetre precision for road-edge lengths. The edge-build step
  itself does not populate elevation or travel times; the elevation stage adds
  sampled elevations to nodes, per-way profiles to `way_elevations.parquet`,
  and directional profiles to `edges.parquet`.
  Car costs are stored in the one-to-one `car_costs.parquet` keyed by
  `edge_key`.

## Resumable edge-cost stage

After the edge build, `python -m mobgrid.osm.costs --state 2021 --area pilot`
reuses the elevation and car-density checkpoints, then builds B1 walk and bike
costs and joins all modes to `edge_costs.parquet`. Elevation also requires
the extracted `ways.parquet` and unpacked BD ALTI grids; it enriches the edge
and node tables in place. The cost and substage checkpoints under
`data/interim/osm/{state}/{area}/costs/` include a build-logic version,
input/output fingerprints and relevant parameters. Changes to cost parameters
invalidate costs, not the edge build. `python -m mobgrid.osm.edges --state 2021
--area pilot --force` explicitly rebuilds the edges and step 6 report.

The cost command updates the report with incomplete-elevation edge counts,
length/time mean speeds by highway class, and the urban share of directed car
length by class. It prints substage times and writes dated logs and summaries.
Intermediate car and active cost files remain available as described below.
The 2021 pilot edge report also compares `geovelo-2022` to OSM inside the
configured department: it lists distinct `ame_d`/`ame_g` values, excluded
lengths, family lengths by commune, and same-family matches within the
configured tolerance. Run the command below to write the report; matching
edge-build outputs are reused:

`python -m mobgrid.osm.edges --state 2021 --area pilot`
For the 2021 pilot, both elevation entry points use
`docs/data/step06_elevation_pilot.md`. An existing checkpoint using the old
year-suffixed name is reused only when both report contents and all other
checkpoint signatures match.

`edge_costs.parquet` has exactly one row per directed `edge_key`. Its numeric
columns are nullable float32: `length_m`, `climb_m` and `separated_length_m`
are metres; `car_time_s`, `walk_time_s` and `bike_time_s` are seconds;
`walk_energy_kj`, `bike_energy_kj`, `bike_energy_drag_kj` and
`bike_pedalling_energy_kj` are kJ; `bike_energy_per_kg_kj_per_kg` is kJ/kg.
The `is_urban` boolean and `speed_limit_bucket` string apply to car edges.
`bike_zero_speed_segments` is a nullable int32 count for bike edges.
Mode-inapplicable values and costs with incomplete elevation profiles are null.
For bike steps, the three riding-energy component columns are null; total
energy is the walking stair energy.

The version 2 per-mode graph archives store each contracted arc's ordered
zero-based row positions in this exact `edges.parquet`, using int64 offsets
and member rows. Rebuild the graph after replacing or reordering that file.
Road classes and speed-limit buckets use uint8 ids with archive dictionaries;
contraction stops at changes of either. The transpose points to forward arc
indices rather than duplicating costs. Graph reports compare actual array
memory with an estimate of version 1 for the same contracted topology.

Bounded graph searches use reusable workspaces, support forward and reverse
arcs, and can fill the three section 10.2 products at settlement. Road-class
and speed-bucket times are optional post-search path splits. Search resolution
and product bin widths are configured in `config/search.yaml`. Dial rounds
edge and source times to the configured resolution; the heap retains float
times. The configured queue is Dial, faster for all three pilot modes; heap
remains selectable. Low-level callers must pass the configured queue and Dial
resolution explicitly.
The benchmark needs all three mode cutoffs filled in that configuration; it
checkpoints under the pilot interim directory and writes a dated log and
summary under the configured log directory.

## Edge columns

| Column | Type | Meaning |
|---|---|---|
| `edge_key` | string | Deterministic `way_id:segment_index:mode:direction` key, with direction `f` or `r`; unique per directed mode edge within one build |
| `way_id` | int64 | OSM way id |
| `from_node_id`, `to_node_id` | int64 | Directed edge endpoints |
| `is_forward` | bool | True follows the stored way reference order |
| `mode` | string | One row for each permitted direction and mode: car, bike or foot |
| `node_ids` | list[int64] | Ordered OSM node ids along the segment |
| `length_m` | float64 | Ellipsoidal length in metres from the ordered node latitude/longitude coordinates |
| `highway` | string, nullable | OSM road class |
| `maxspeed_kmh` | float64, nullable | Parsed maxspeed in km/h |
| `oneway` | string, nullable | Raw OSM oneway tag, used to identify explicitly one-way carriageways |
| `speed_context` | string, nullable | Context parsed from `zone:traffic`, `source:maxspeed`, `maxspeed:type` or `zone:maxspeed` (`urban`, `rural`, `zone30`, `motorway`); retained independently of numeric maxspeed |
| `elevation_from_m`, `elevation_to_m` | float64, nullable | Elevation at the directed endpoints, sampled from BD ALTI |
| `node_elevations_m` | list[float64] | Way-specific elevations in directed `node_ids` order, nullable per node |
| `climb_m`, `descent_m` | float64, nullable | Sum of positive and negative height changes along ordered OSM nodes |
| `mean_grade` | float64, nullable | Endpoint elevation change divided by horizontal edge length; dimensionless |
| `motorroad` | bool | `motorroad=yes` (also accepts `true` and `1`) |
| `lanes` | string, nullable | Raw `lanes` value |
| `car_access`, `bike_access`, `foot_access` | bool | Effective access flags before one-way filtering |
| `bike_infra` | string, nullable | Direction-specific class from the table below |
| `surface`, `tracktype`, `smoothness` | string, nullable | Raw OSM values |
| `busway`, `lanes_bus`, `lanes_psv` | string, nullable | Raw bus-lane values |
| `signal_count`, `stop_count`, `give_way_count`, `crossing_count`, `mini_roundabout_count` | int8 | Direction-filtered control-node counts along the edge, excluding its first node; signalised crossings count only as signals |
| `to_degree` | int64 | Distinct neighbouring graph nodes of `to_node_id` for this mode, considering incoming and outgoing edges |
| `cell_1km_id` | int64 | 1 km cell id of the edge-geometry centroid |
| `tile_id` | int64 | Configured tile id of the edge-geometry centroid |
| `geometry_wkb` | binary | Directed EPSG:3035 line geometry |

`nodes.parquet` has `node_id` (int64), `x` and `y` (float64 metres in
EPSG:3035), `tags` (OSM tag map), `graph_node` (bool), and nullable
`elevation_m` (float64) after elevation enrichment. Graph nodes are way ends
and nodes shared by at least two kept ways. Other retained way nodes and area
traffic-control nodes are also present with `graph_node=false`.
The extracted way tag maps also retain `zone:traffic`, `source:maxspeed`,
`maxspeed:type`, `zone:maxspeed`, `tracktype`, `service` and `area` for
downstream speed and surface processing. The edge-build report joins those
extracted ways to car edges to identify the access tag and value for each
car-accessible non-road class.
Extracted tags also retain `bridge`, `tunnel` and `layer`. Bridge and tunnel
ways whose tag is present and not `no` use a linear profile by distance between
their first and last nodes; the sampled terrain remains unchanged in the node
table. If an endpoint lacks elevation, interpolated interior values are null.
The elevation report gives the length of complete treated ways by structure
type, counted once per way, not once per directed mode edge.
Each way profile is then averaged over the configured 50 m window by
integrating the piecewise-linear profile over distance. At the ends of each
complete run, the endpoint slope is extended to fill the window; missing
samples remain missing. `way_elevations.parquet` stores both the interpolated
pre-smoothing and smoothed values. The elevation report gives total directed
climb before and after smoothing by mode, with incomplete edges counted
separately. The window is a provisional `TODO(confirm)` value.
Segments are assigned an index by the cumulative graph-node count along each way;
interior graph nodes also serve as the preceding segment's endpoint. This
avoids joining every way point against sequence ranges.
The key is stable for unchanged way segmentation; splitting a way at a new
graph node can change subsequent segment indexes and keys.

## Active-mode edge costs

The step 6b active-cost function writes `active_costs.parquet`, one row per
directed foot or bike `edge_key`. Inapplicable mode-specific cost columns are
null. It uses way-specific smoothed edge elevations for segment grades,
except for steps, which use raw `nodes.parquet` elevation samples. Incomplete
profiles have null costs and are counted in its summary.
Non-stair walking grades are clipped to the configured Minetti range and
non-stair bike grades to the configured speed-table grid for both time and energy.
Physical climb remains based on the original elevation changes. The adjacent
`.grades.md` report counts clipped directed segments and their lengths by
mode and OSM highway class and lists the configured 20 longest affected
edges with their most extreme original signed grade.
The elevation-stage report is computed before active costs, using smoothed
profiles and configured grade ranges, including bike steps; its clipping
counts can therefore differ from the active report.
For rider power, the approved effective grade is physical grade plus the
surface Crr minus the configured paved Crr; force balance retains physical
grade. Paved results are unchanged. Any remaining zero-speed segments with
positive length are errors counted by highway,
bike infrastructure, resolved surface, original grade range and speed cap in
`active_costs.grades.md`. Their containing bike edges have null time and energy,
not infinite or partial costs. The step 6 report gives the total error count.
Stair time is at least flat walking time over the full edge; bike steps use
the walking stair time and energy without riding or stop costs.
Active-cost loading, walking, speed-table construction, riding, stops and
writing times are printed and logged as batch-aggregated durations.

The elevation CLI checkpoints sampled nodes and completed output signatures
under `data/interim/osm/{state}/{area}/elevation/`. Matching reruns reuse
completed outputs; changed inputs or settings trigger recomputation. Its
dated log and run summary are written under `logs/`.

| Column | Type | Unit | Meaning |
|---|---|---|---|
| `edge_key` | string | none | Directed foot or bike edge key |
| `walk_time_s`, `walk_energy_kj` | float64, nullable | seconds, kJ | Summed segment walk cost; steps use the stair formula |
| `bike_time_s`, `bike_energy_kj` | float64, nullable | seconds, kJ | Ride plus expected stop time and riding energy; walking cost on steps |
| `bike_energy_per_kg_kj_per_kg` | float64, nullable | kJ/kg | Rolling, signed climb, and stop energy per total bike+rider kg; null on steps |
| `bike_energy_drag_kj` | float64, nullable | kJ | Drag energy; null on steps |
| `bike_pedalling_energy_kj` | float64, nullable | kJ | Unloaded pedalling energy, based on reference body mass; null on steps |
| `climb_m` | float64, nullable | metres | Sum of positive segment elevation changes |
| `separated_length_m` | float64 | metres | Bike-edge length on separated infrastructure, otherwise zero |

For riding, bike total energy equals the per-kg component times configured rider-plus-bike
mass, plus drag and unloaded-pedalling energy. Unknown non-empty `surface`
values use the highway-class default and are reported by value in the function
summary. All known highway classes have defaults; missing or unknown highway
classes use the configured bike-infrastructure class default. Stop time adds
only the deceleration and acceleration delay beyond
the cruising time already counted, plus expected signal wait; stop energy is
unchanged. Provisional stop probabilities and surface defaults are
`TODO(confirm)` values in `config/network.yaml`; signal timing is configured in
`config/energy.yaml`.

## Car free-flow costs

`car_costs.parquet` has one row per car `edge_key` (therefore one row per
direction). It contains `time_s`, `is_urban`, `road_class`, and
`speed_limit_bucket`. The speed limit uses `maxspeed_kmh` when present;
otherwise a configured class/context default applies. The urban-density rule
splits undirected car-road geometry into configured grid cells, sums their
projected length over a cell-centred disc, and samples the centroid cell of
each directed edge. It fits a length-weighted threshold against edges tagged
urban or rural and uses the configured fallback only when both labels are not
available. The report records the fitted agreement and urban directed-length
share by road class. The CLI checkpoints the density result under interim
storage and invalidates it when the edges or density settings change.
All defaults, realism factors, density parameters, delays, and bucket bounds
are in `config/network.yaml` with `TODO(confirm)` markers.
Default speeds are capped by class; rural trunk and primary roads use the
configured dual-carriageway default only when explicitly tagged `oneway=yes`.
Controls have separate configured delays by type.

| Column | Type | Unit | Meaning |
|---|---|---|---|
| `edge_key` | string | none | One-to-one directed edge key from `edges.parquet` |
| `time_s` | float64 | seconds | Free-flow time including configured control and to-node delays |
| `is_urban` | bool | none | Explicit urban/rural context or fitted road-density classification |
| `road_class` | string, nullable | none | OSM `highway` class |
| `speed_limit_bucket` | string | none | Configured bucket of the numeric/default limit before realism factor |

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
bikes. Only the highway classes listed in `known_highways` are retained.
Other highway values are dropped before graph-node detection and reported as
counts of extracted ways by value. Ways without a highway are retained only
for foot access to platforms.

| Mode | Access-tag precedence | Default/exclusion rules | Direction rules |
|---|---|---|---|
| Car | `motorcar`, `motor_vehicle`, `access` | `platform`, `busway`, steps, corridors, bus stops and elevators are unconditionally excluded; generic `access` cannot open footway, path, pedestrian, cycleway or bridleway | `oneway=yes/1/true` forward only; `-1` reverse only; no/unknown permits both. Roundabouts, circular junctions and motorways imply forward one-way |
| Bike | `bicycle`, `access` | Motorways, motorway links and `trunk` + `motorroad=yes` are unconditional exclusions; footway and steps require explicit `bicycle`; pedestrian ways are allowed at walking pace | `oneway:bicycle` overrides; `cycleway=opposite*` permits both directions; otherwise inherits `oneway`, with `cycleway:*:oneway=no` allowing both and `-1` allowing reverse travel |
| Foot | `foot`, `access` | Sidewalks and footway, path, steps, pedestrian and living-street classes permit walking; motorways, motorway links, and trunk + `motorroad=yes` are excluded | Both directions |

Traffic-control tags are read for `highway=traffic_signals`, `stop`,
`give_way`, `crossing` and `mini_roundabout`. Each directed edge counts its
ordered OSM nodes except its first: signals contribute to `signal_count`,
stops to `stop_count`, give-ways to `give_way_count`, unsignalled crossings to
`crossing_count`, and mini-roundabouts to `mini_roundabout_count`. A crossing
tagged `crossing=traffic_signals` contributes to `signal_count` instead.
`traffic_signals:direction`
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
