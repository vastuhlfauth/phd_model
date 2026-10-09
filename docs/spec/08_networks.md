# 8. Network layer specifications

## 8.1 Base data: one edge table as the single source of truth

All road-based layers derive from one OSM edge table (Parquet), which level 2 scenarios edit. Columns include way and node identifiers, length, `highway` class, `maxspeed`, lanes, direction, access per mode (car, bike, foot), bike infrastructure class, surface, bus lanes, elevation at both ends and grade per direction (from IGN elevation data), urban flag, tile and geometry. A node table holds traffic signals and junction types. Time, distance and energy per mode are computed per directed edge from these attributes and the formulas of section 9.

**Bike infrastructure is included from the start.** A bike scenario needs a baseline that already distinguishes infrastructure; it changes time (cruising speed, fewer stops) and energy (stops, surface); route and mode choices value it (Broach, Dill & Gliebe 2012); and the 2022 and 2024 OSM extracts capture the growth of cycling networks since 2020 for the back-test.

| Class | OSM tags (examples) | Effect in the model |
|---|---|---|
| Separated track or path | `highway=cycleway`; `cycleway=track`; `cycleway:left` or `:right=track`; `highway=path` with `bicycle=designated` | Cruising speed; lower stop probability at junctions; calmer riding, hence lower energy (section 9.7); counts in the share of separated distance |
| Painted lane | `cycleway=lane`, `cycleway:both=lane` | Cruising speed in traffic |
| Bus lane open to bikes | `cycleway=share_busway`; bus lanes with bike access | As painted lane |
| Low-speed street | `highway=living_street`; `maxspeed` up to 30; `bicycle_road=yes` | Mixed traffic at low speed |
| Mixed traffic | Other roads with bike access, by class and speed limit | Speed caps; stop probability |
| Surface | `surface`, `smoothness` | Rolling resistance (section 9.7) |

**Géovélo dataset.** The national cycle-infrastructure dataset on transport.data.gouv.fr (Géovélo, built from OSM in the national schema, monthly files since mid-2022) is first used to validate the OSM tagging: length by class and commune, and share of segments matched. It could later become the base of the bike network, since it fixes the classification of each facility. Its dated files serve both states [TO CONFIRM: a version for 2021]; a methodology change in October 2026 shifts some classes, so files from before and after that date are not compared directly.

**Free-flow car speed model.** Speed comes from `maxspeed`, or from French defaults by class and context (50, 80–90, 110, 130 km/h), times a calibrated realism factor. Fixed delays apply at signals and junctions. OSRM includes turn and signal penalties, so this model is calibrated against OSRM in the pilot, then against Google Maps when congestion is added. Bus lanes (`busway`, `lanes:bus`, `lanes:psv`) are kept for buses in the congestion phase.

## 8.2 Walk (200 m)

- Points: inhabited 200 m cells and all 200 m cells flagged as destinations.
- Exact routing on the foot graph with a **30-minute cutoff**, rather than a grid graph. Pedestrian barriers (motorways, rail lines, rivers, footbridges) are where grids fail most, and walking is local, so exact routing stays cheap.
- Outputs: (a) walk costs from 200 m cells to 200 m cells, stored in full; (b) an access and egress table from 200 m cells to stop areas within **20 minutes**, including the walk inside stations (section 9.3); (c) transfer footpaths between stop areas from the foot network, up to 400 m.
- Energy uses the walking formulas of section 9.3, with body mass explicit.

## 8.3 Bike (1 km grid)

- Edge speeds come from the force balance of section 9.7 (rider power, body and bike mass, slope, surface), by infrastructure class and direction; stops at signals and junctions add time and energy.
- Grid edges: exact local bike times, distances and energy between each cell's representative point and its **24 neighbours**, directed: the 8 adjacent cells and the 16 cells of the second ring, i.e. the whole 5 × 5 block around the cell.
- **Why the second ring.** With the 8 adjacent cells only, paths move in 8 directions, every 45°, and a straight trip at an intermediate angle is overstated by up to about 8%. Eight cells of the second ring (one step across and two along, the "knight moves") add 8 directions, at about 26.6° and 63.4° from the axes, which cuts the maximum overstatement to about 2.7% (van Bemmelen et al. 1993). The 8 other cells of the ring (two steps straight or diagonal) add no direction, but their edges carry the exact network time over 2 km instead of a path through the representative point of the cell in between, which removes part of the detour error. The full ring costs 50% more edges than 16 neighbours: about 13 million directed edges nationally instead of 8.7 million.
- **Stray check.** An edge is flagged or dropped if its path runs mostly outside the cells crossed by the straight segment between its two points, which catches missing bridges and barriers.
- Each grid edge also stores its climb (sum of positive height differences) and its length on separated infrastructure, accumulated along searches.
- Fastest path by time. A perceived-cost path that values infrastructure and avoids climbs (Broach, Dill & Gliebe 2012) can be added later for route choice.

## 8.4 Car: local roads (1 km grid)

- Same construction as bike, with 24 neighbours, on car-accessible edges, excluding the trunk layer.
- Each grid edge also stores its time split by road class (and speed-limit bucket). This is what makes level 1 scenarios exact when paths do not change: a speed-limit change rescales one component without rerunning any search on OSM.
- The split between local and trunk is by **access control, not by speed**. A 50 km/h threshold would move every 80–90 km/h départementale into the node-based layer; those roads can be joined at every intersection, so nodes would be needed everywhere. They are exactly what a grid represents well.

## 8.5 Car: trunk

- Selection: OSM `motorway`, `motorway_link`, and `trunk` with `motorroad=yes` (voies express) and their links, which roughly corresponds to the 110–130 km/h network.
- Contraction to interchange nodes; directed links carry time, distance, energy and lanes.
- Connectors: each ramp attaches to the 1 km cell containing it, with the exact local time from that cell's representative point.
- The **combined car graph** (local grid, trunk, connectors) is searched as one graph.

## 8.6 Public transport

- **Feeds:** 2026 GTFS for France (transport.data.gouv.fr) plus feeds covering border regions, rebuilt for each state (section 5.6).
- **Cleaning:** keep the services active on the exact reference date (day-of-week flags, date range, additions and removals); keep whole trips running in the window plus a margin; remove trips duplicated across feeds (TER often appears in national and regional feeds).
- **Time window: 08:00–09:00.** Range RAPTOR evaluates every departure minute in the window for about the cost of a few single runs and reports the median (and percentiles if needed). With plain RAPTOR, departures every 15 minutes (Stępniak et al. 2019) [TO CONFIRM after the benchmark].
- **Access and egress:** from 200 m cells to stop areas on foot within 20 minutes (table 8.2 b). Origins and destinations are 200 m cells.
- **Fast variant to test:** compute median stop-to-stop times once per stop area over the window, then combine them with the 200 m access and egress tables by min-plus products. Taking the minimum of medians instead of the median of minima can overstate times when different stops are best at different departure times, so the variant is validated against per-origin range RAPTOR on a sample.
- **Storage:** O-D table aggregated to 1 km pairs; accessibility products at 200 m origins (section 10.2); for each pair, up to three route groups used (for scenario triage and, later, line loads); stop-to-stop times and the access and egress tables, so that land-use changes need no new timetable routing (section 11.1).
- **Two tiers:** the national rail layer (TGV, Intercités, TER) stays national; urban and interurban networks are handled per tile with halo.
- **Engine:** RAPTOR compiled with numba, or r5py, behind one interface. The benchmark on one département compares runtime per origin, memory, agreement of median times, turnaround after a GTFS edit, and access to journey components.
