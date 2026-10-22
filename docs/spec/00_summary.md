# Fast, scenario-ready multimodal O-D costs for metropolitan France

_This folder is the Markdown version of proposal v10. File index: [README.md](README.md)._

_Literature review and methodological proposal_

_Working document · version 10 · 16 October 2026_

> **Changes since version 10 (20–22 October 2026, section 9.9).** The daily budget is also re-estimated on ENTD 2008, to measure its change to 2019, with a density proxy available in both surveys. Trips for sport, strolls, holidays and other movement for its own sake are left out of the budget. Declared speeds above 7 km/h on foot, 35 km/h by bike and 130 km/h by car are corrected through the distance, for bike trips too. Short and long train days form one group. The calibration of P_0 (34.8 W in EMP 2019, 34.0 W in ENTD 2008), the weights and the bootstrap over households are described; the walking speed of the surveys (3.4 to 3.6 km/h, door to door) is reported but not adopted (sections 9.3, 9.7, 9.9).

> **Changes in version 10 (after the research meeting of 16 October 2026).** The grid graph is compared with 8, 16 and 24 neighbours in the pilot, the 8-neighbour graph being about three times faster (section 8.3). Representative points are the occupied-dwelling 1-median among the network nodes of each cell, fixed across states (section 4.2). AequilibraE is benchmarked for skims and is the candidate engine for assignment (sections 13, 14.6). Road scenarios edit the reduced network only, speed limits and capacities, and new development zones copy comparable cells; no local road network is built (section 11.4). Congestion uses BPR functions calibrated on the reduced network (section 12).

> **Changes in version 9.** Past public transport supply is rebuilt by a national rule that needs no manual review: the stop-matching test of version 8 failed, and section 5.6 is rewritten around OSM route relations (an automatic rule for trams) and a curated national list of openings 2022–2026 applied automatically for every mode, with its results. Acquisition is national; Geofabrik dated extracts have no checksum files and are checked by size; the GTFS inventory and the coverage of transport authorities are described (sections 5.1, 5.3, 5.4). The PT build keeps one copy of each agency repeated in regional aggregates and rebuilds past states from the edits of section 5.6 (section 8.6). The earliest Géovélo file stands for 2021 (section 8.1). Planned lines of the openings list feed the scenario timeline (section 11.2). Validation, implementation status, conventions, algorithms and risks are updated (sections 13 to 15).

> **Changes in version 8.** BPE 2025 stands for the 2023 state; NUTS boundaries are those of 2024; the 14 EMC² surveys are listed (section 5). Known network changes in the test EPCIs are set out for the GTFS rebuilding (section 5.6). Car ownership becomes a commune-level model of accessibility and income (section 6.4). The Géovélo cycle-infrastructure dataset is used for validation and possibly as the base network (section 8.1). The vehicle factor is replaced by the Compendium's riding rate and the crowding term (section 9.5). The monetary cost is simplified to fixed and per-km costs from the official mileage scale (section 9.10). The existing Google Maps validation scripts are reviewed and integrated (sections 12, 13 and 14.4).

> **Placeholders.** Text written [TO CONFIRM: …] marks a choice to make or a fact to confirm before implementation. All of them are listed in `docs/progress.md`.

# Summary

The goal is to produce, for metropolitan France, travel time, distance and bodily energy by walk, bike, car and public transport (PT) between cells, together with the population at origins and the opportunities at destinations (jobs, services, nature, people), and accessibility indicators derived from them. These feed a distribution model (the O-D flow matrix), a mode-share model and a daily energy budget per cell. Infrastructure and macro-economic scenarios, small or very large, must be easy to specify and as quick as possible to recompute at national scale.

The proposal rests on ten decisions:

- **Two modules.** `landgrid` builds origins and opportunities per cell, year and scenario; `mobgrid` builds networks, O-D costs and accessibility. They share the grid and configuration, and can run independently.
- **Two states: 2021 and 2023.** Physical stocks (buildings, networks, services) are taken at 1 January of the following year; statistics on people and jobs are taken for the state year. Public transport of both states is rebuilt from the 2026 timetables. The 2023 state serves to back-test the scenario engine against observed change.
- **Origins at 200 m.** Filosofi 2021 (natural level) is redistributed to 200 m cells with dwellings from the Fichiers fonciers located at building points, preserving INSEE totals; a model trained on 2021 generates a Filosofi-like 2023.
- **Opportunities as control totals times allocation keys,** in one destination grid with a flag per type. Jobs: INSEE totals by EPCI, Fichiers fonciers premises as keys, compared with Overture. Services (BPE) and nature: first ones in reach. Jobs and social: radiative accessibility. Abroad, only jobs and nature.
- **Resolutions by mode.** Walk and PT from 200 m to 200 m (access to stops is computed on foot at 200 m); bike and car from 1 km to 1 km. Motorways and PT keep their nodes; all other layers are gridded or point-based.
- **Trips as chains of legs.** Every trip is built from legs (walking, waiting, riding, transfers, driving, parking, cycling) with standard formulas for time and energy; body mass is explicit; congestion and crowding act on identified legs.
- **One search, three products.** Each search fills the O-D table (time, distance, energy, and from them the monetary cost), cumulative opportunity curves and the nearest destinations of each type, at full resolution. Accessibility never depends on how the O-D table is aggregated for storage.
- **A daily energy budget per cell.** The Kölbl & Helbing (2003) value of about 615 kJ per person and day is the starting point; it is re-estimated with this project's energy model on the French travel survey EMP 2019, and on ENTD 2008 to measure its change over the decade.
- **Scenarios at any scale.** Land-use changes need no routing; network changes are grouped into dated epochs; each edit is triaged automatically between table updates, local searches and full runs, with error bounds for gradual changes. Road scenarios act on speed limits and capacities of the reduced network; local roads are not built, and new development zones copy comparable cells.
- **Data fetched by script from versioned sources and APIs,** recorded in a manifest; DuckDB for all table work, numba for graph searches.
