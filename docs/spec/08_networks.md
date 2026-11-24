# 8. Network layer specifications

## 8.1 Base data: one edge table as the single source of truth

All road-based layers derive from one OSM edge table (Parquet), built once per state; scenarios edit the reduced network built from it, never the table (section 11.4). Columns include way and node identifiers, length, `highway` class, `maxspeed`, lanes, direction, access per mode (car, bike, foot), bike infrastructure class, surface, bus lanes, elevation at both ends and grade per direction (from IGN elevation data), urban flag, tile and geometry. A node table holds traffic signals and junction types. Time, distance and energy per mode are computed per directed edge from these attributes and the formulas of section 9.

**Bike infrastructure is included from the start.** A bike scenario needs a baseline that already distinguishes infrastructure; it changes time (cruising speed, fewer stops) and energy (stops, surface); route and mode choices value it (Broach, Dill & Gliebe 2012); and the 2022 and 2024 OSM extracts capture the growth of cycling networks since 2020 for the back-test.

| Class | OSM tags (examples) | Effect in the model |
|---|---|---|
| Separated track or path | `highway=cycleway`; `cycleway=track`; `cycleway:left` or `:right=track`; `highway=path` with `bicycle=designated` | Cruising speed; lower stop probability at junctions; calmer riding, hence lower energy (section 9.7); counts in the share of separated distance |
| Painted lane | `cycleway=lane`, `cycleway:both=lane` | Cruising speed in traffic |
| Bus lane open to bikes | `cycleway=share_busway`; bus lanes with bike access | As painted lane |
| Low-speed street | `highway=living_street`; `maxspeed` up to 30; `bicycle_road=yes` | Mixed traffic at low speed |
| Mixed traffic | Other roads with bike access, by class and speed limit | Speed caps; stop probability |
| Surface | `surface`, `smoothness` | Rolling resistance (section 9.7) |

**Géovélo dataset.** The national cycle-infrastructure dataset on transport.data.gouv.fr (Géovélo, built from OSM in the national schema, monthly files since mid-2022) is first used to validate the OSM tagging: length by class and commune, and share of segments matched. It could later become the base of the bike network, since it fixes the classification of each facility. Its dated files serve both states: the earliest file (18 July 2022) stands for 2021 and the January 2024 file for 2023; a methodology change in October 2026 shifts some classes, so files from before and after that date are not compared directly. In the 2021 pilot (Gironde, OSM 2021 against the July 2022 file), 98.5% of the separated and painted-lane length and 89% of the bus-lane length lie within 15 m of an OSM way of the same class, and the lengths agree within 4% (separated 1,651 km in OSM against 1,670 km, painted lanes 654 against 628 km). For this check only, separated facilities count designated ones (`highway=cycleway`, `bicycle=designated`, `cycleway:*=track`); the other car-free paths open to bikes stay in the separated class for speed and energy. Since Géovélo is built from OSM, the check tests the classification, not the completeness of OSM (`docs/data/step06_osm_pilot.md`).

**Free-flow car speed model.** Speed comes from `maxspeed`, or from French defaults by class and context, times a calibrated realism factor:

- **Context:** the OSM tags where present (`maxspeed=FR:urban`, `FR:rural`, `FR:zone30`, `zone:traffic` and their variants); elsewhere a road-density rule: urban when the undirected car-road length within 500 m, counted on a 50 m grid, exceeds a threshold fitted on the tagged edges (5.0 km in the 2021 pilot, agreeing with the tags on 88% of their length).
- **Defaults:** 50 km/h urban; 80 rural, the rule since 2018 (roads signed 90 carry `maxspeed`); 110 on rural dual carriageways (trunk and primary roads mapped as one-way ways); 130 on motorways and 80 on their links, whatever the context. When `maxspeed` is missing, living streets, service roads, tracks and car access on paths are capped at 20 km/h, and residential streets at 50.
- **Delays,** per control on the edge in its direction: 15 s at a signal (a signalled pedestrian crossing counts as one), 5 s at a stop sign, 2 s at a give-way, 3 s at a mini-roundabout, none at an unsignalled pedestrian crossing, and 2 s at a junction of three or more branches.

These values are provisional (`config/network.yaml`). In the 2021 pilot, mean free-flow speeds including delays are 121 km/h on motorways, 99 on trunk roads, 56–60 on primary, secondary and tertiary roads, 37 on residential streets and 18 on service roads. OSRM includes turn and signal penalties, so this model is calibrated against OSRM in the pilot, then against Google Maps when congestion is added. Bus lanes (`busway`, `lanes:bus`, `lanes:psv`) are kept for buses in the congestion phase.

**Elevation.** BD ALTI 25 m (IGN) is sampled bilinearly at every node, in Lambert-93. Ways tagged `bridge` or `tunnel` take a straight profile between their end nodes, since the terrain model gives the river under a bridge and the hill above a tunnel (238 km of bridges and 27 km of tunnels in the 2021 pilot). Each way's profile is then smoothed along its length with a 50 m window weighted by distance, and grades are computed per segment and direction; stairs keep the unsmoothed elevation (section 9.3). In the pilot, car edges climb 10.8 m per km unsmoothed, 10.1 with the 50 m window and 9.1 with a 200 m window. The ten flattest 10 km tiles (Landes, Médoc) climb 0.7 to 1.0 m per km and the ten hilliest 19 to 23, so the terrain model adds little noise and wider windows start removing real slopes. Grades beyond the walking range (±45%) or the bike speed table (±20%) are clipped and counted (`docs/data/step06_elevation_pilot.md`).

## 8.2 Walk (200 m)

- Points: inhabited 200 m cells and all 200 m cells flagged as destinations.
- Exact routing on the foot graph with a **30-minute cutoff**, rather than a grid graph. Pedestrian barriers (motorways, rail lines, rivers, footbridges) are where grids fail most, and walking is local, so exact routing stays cheap.
- Outputs: (a) walk costs from 200 m cells to 200 m cells, stored in full; (b) an access and egress table from 200 m cells to stop areas within **20 minutes**, including the walk inside stations (section 9.3); (c) transfer footpaths between stop areas from the foot network, up to 400 m.
- Energy uses the walking formulas of section 9.3, with body mass explicit.

## 8.3 Bike (1 km grid)

- Edge speeds come from the force balance of section 9.7 (rider power, body and bike mass, slope, surface), by infrastructure class and direction; stops at signals and junctions add time and energy.
- Grid edges: exact local bike times, distances and energy between each cell's representative point (section 4.2) and its neighbours, directed.
- **Neighbourhood: three variants compared in the pilot.**

| Neighbours | Cells | Directed edges nationally | Overstatement of a straight trip, mean / maximum |
|---|---|---:|---|
| 8 | The adjacent cells | about 4.4 million | 5.5% / 8.2% |
| 16 | Plus the 8 "knight moves" (one step across, two along) | about 8.7 million | 1.4% / 2.7% |
| 24 | The whole 5 × 5 block | about 13 million | 1.4% / 2.7%, with exact 2 km edges |

  With 8 neighbours paths move every 45°; the knight moves add directions at about 26.6° and 63.4° from the axes (van Bemmelen et al. 1993). The 8 other cells of the second ring add no direction, but their edges carry the exact network time over 2 km instead of a path through the point of the cell in between, which removes part of the detour error. The overstatements are those of straight trips in uniformly spread directions; on real networks the errors are measured against OSRM (section 13). Search time grows with the number of edges, so 8 neighbours divide it by about three compared with 24; their bias is mostly systematic (+5.5% on average) and can be partly corrected by a calibrated factor. The 8-neighbour graph is also the simplest reduced network for congestion: each orthogonal edge crosses one cell boundary (section 12). The choice follows the pilot comparison of runtime and error.
- **Stray check.** An edge is flagged or dropped if its path runs mostly outside the cells crossed by the straight segment between its two points, which catches missing bridges and barriers.
- Each grid edge also stores its climb (sum of positive height differences) and its length on separated infrastructure, accumulated along searches.
- Fastest path by time. A perceived-cost path that values infrastructure and avoids climbs (Broach, Dill & Gliebe 2012) can be added later for route choice.

## 8.4 Car: local roads (1 km grid)

- Same construction and neighbourhood as bike, on car-accessible edges, excluding the trunk layer.
- Each grid edge also stores its time split by road class (and speed-limit bucket) and a capacity (section 12). This is what makes scenarios exact when paths do not change: a speed-limit change rescales one component without rerunning any search on OSM, and a capacity change acts directly on the edge.
- The split between local and trunk is by **access control, not by speed**. A 50 km/h threshold would move every 80–90 km/h départementale into the node-based layer; those roads can be joined at every intersection, so nodes would be needed everywhere. They are exactly what a grid represents well.

## 8.5 Car: trunk

- Selection: OSM `motorway`, `motorway_link`, and `trunk` with `motorroad=yes` (voies express) and their links, which roughly corresponds to the 110–130 km/h network.
- Contraction to interchange nodes; directed links carry time, distance, energy and lanes.
- Connectors: each ramp attaches to the 1 km cell containing it, with the exact local time from that cell's representative point.
- The **combined car graph** (local grid, trunk, connectors) is searched as one graph.

## 8.6 Public transport

- **Feeds:** 2026 GTFS for France, producer resources of transport.data.gouv.fr (section 5.4), plus feeds covering border regions.
- **One copy per agency.** Regional and departmental aggregates repeat the trips of local networks. When an agency appears both in its own producer feed and in an aggregate, its copy in the aggregate is dropped, before the trip-level deduplication of the cleaning step. An agency published only in an aggregate (Caen's Twisto) is taken from the aggregate.
- **Past states:** each state's network is rebuilt from the 2026 feeds as in section 5.6. The presence of each route follows the precedence of section 5.6 (openings list, tram rule, default keep); the cuts and skipped stops of each route are combined and applied to its patterns; the remaining trips keep their 2026 times. Routes are identified by (GTFS resource id, `route_id`).
- **Cleaning:** keep the services active on the exact reference date, Tuesday 13 October 2026 (day-of-week flags, date range, additions and removals) [TO CONFIRM: rule for regular services whose calendar expired before the reference date, 47 feeds: shift to their last valid week or drop]; keep whole trips running in the window plus a margin; remove trips duplicated across feeds (TER often appears in national and regional feeds).
- **Time window: 08:00–09:00.** Range RAPTOR evaluates every departure minute in the window for about the cost of a few single runs and reports the median (and percentiles if needed). With plain RAPTOR, departures every 15 minutes (Stępniak et al. 2019) [TO CONFIRM after the benchmark].
- **Access and egress:** from 200 m cells to stop areas on foot within 20 minutes (table 8.2 b). Origins and destinations are 200 m cells.
- **Fast variant to test:** compute median stop-to-stop times once per stop area over the window, then combine them with the 200 m access and egress tables by min-plus products. Taking the minimum of medians instead of the median of minima can overstate times when different stops are best at different departure times, so the variant is validated against per-origin range RAPTOR on a sample.
- **Storage:** O-D table aggregated to 1 km pairs; accessibility products at 200 m origins (section 10.2); for each pair, up to three route groups used (for scenario triage and, later, line loads); stop-to-stop times and the access and egress tables, so that land-use changes need no new timetable routing (section 11.1).
- **Two tiers:** the national rail layer (TGV, Intercités, TER) stays national; urban and interurban networks are handled per tile with halo.
- **Engine:** RAPTOR compiled with numba, or r5py, behind one interface. The benchmark on one département compares runtime per origin, memory, agreement of median times, turnaround after a GTFS edit, and access to journey components.
