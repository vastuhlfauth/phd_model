# Fast, scenario-ready multimodal O-D costs for metropolitan France

_This folder is the Markdown version of proposal v8. File index: [README.md](README.md)._

_Literature review and methodological proposal_

_Working document · version 8 · 9 October 2026_

> **Changes in version 8.** BPE 2025 stands for the 2023 state; NUTS boundaries are those of 2024; the 14 EMC² surveys are listed (section 5). Known network changes in the test EPCIs are set out for the GTFS rebuilding (section 5.6). Car ownership becomes a commune-level model of accessibility and income (section 6.4). The Géovélo cycle-infrastructure dataset is used for validation and possibly as the base network (section 8.1). The vehicle factor is replaced by the Compendium's riding rate and the crowding term (section 9.5). The monetary cost is simplified to fixed and per-km costs from the official mileage scale (section 9.10). The existing Google Maps validation scripts are reviewed and integrated (sections 12, 13 and 14.4).

> **Placeholders.** Text written [TO CONFIRM: …] marks a choice to make or a fact to confirm before implementation. All of them are listed in `docs/progress.md`.

# Summary

The goal is to produce, for metropolitan France, travel time, distance and bodily energy by walk, bike, car and public transport (PT) between cells, together with the population at origins and the opportunities at destinations (jobs, services, nature, people), and accessibility indicators derived from them. These feed a distribution model (the O-D flow matrix), a mode-share model and a daily energy budget per cell. Infrastructure and macro-economic scenarios, small or very large, must be easy to specify and as quick as possible to recompute at national scale.

The proposal rests on ten decisions:

- **Two modules.** `landgrid` builds origins and opportunities per cell, year and scenario; `mobgrid` builds networks, O-D costs and accessibility. They share the grid and configuration, and can run independently.
- **Two states: 2021 and 2023.** Physical stocks (buildings, networks, services) are taken at 1 January of the following year; statistics on people and jobs are taken for the state year. The 2023 state serves to back-test the scenario engine against observed change.
- **Origins at 200 m.** Filosofi 2021 (natural level) is redistributed to 200 m cells with dwellings from the Fichiers fonciers located at building points, preserving INSEE totals; a model trained on 2021 generates a Filosofi-like 2023.
- **Opportunities as control totals times allocation keys,** in one destination grid with a flag per type. Jobs: INSEE totals by EPCI, Fichiers fonciers premises as keys, compared with Overture. Services (BPE) and nature: first ones in reach. Jobs and social: radiative accessibility. Abroad, only jobs and nature.
- **Resolutions by mode.** Walk and PT from 200 m to 200 m (access to stops is computed on foot at 200 m); bike and car from 1 km to 1 km. Motorways and PT keep their nodes; all other layers are gridded or point-based.
- **Trips as chains of legs.** Every trip is built from legs (walking, waiting, riding, transfers, driving, parking, cycling) with standard formulas for time and energy; body mass is explicit; congestion and crowding act on identified legs.
- **One search, three products.** Each search fills the O-D table (time, distance, energy, and from them the monetary cost), cumulative opportunity curves and the nearest destinations of each type, at full resolution. Accessibility never depends on how the O-D table is aggregated for storage.
- **A daily energy budget per cell.** The Kölbl & Helbing (2003) value of about 615 kJ per person and day is the starting point; it is re-estimated with this project's energy model on the French travel survey EMP 2019.
- **Scenarios at any scale.** Land-use changes need no routing; network changes are grouped into dated epochs; each edit is triaged automatically between table updates, local searches and full runs, with error bounds for gradual changes.
- **Data fetched by script from versioned sources and APIs,** recorded in a manifest; DuckDB for all table work, numba for graph searches.
