# 1. Purpose and requirements

The table translates the project requirements into design constraints.

| Requirement | Design implication |
|---|---|
| Time and distance per mode, per O-D pair, at cell scale; feeds a distribution model then a mode-share model | Store time and distance for every mode. For PT, also store components (access, wait, in-vehicle, transfers, egress, boardings) and the lines used. |
| Bodily energy per mode, to explain mode choice | Energy built leg by leg along each path, slope-dependent for walking and cycling, body mass explicit; stored in kJ above rest (section 9). |
| A daily energy budget per cell, from which mode choice is derived | Daily energy of all trips of a day; budget re-estimated on EMP 2019 with the same formulas (section 9.9). |
| Accessibility to jobs, services, nature and people within time, distance or energy limits; nearest service by type | Computed inside the routing pass at full resolution, never from aggregated O-D data (sections 4.5 and 10.2). |
| Walk and PT at 200 m; bike and car at 1 km | 200 m origins and destinations for walk and PT, 1 km for bike and car; storage can aggregate, accessibility does not. |
| Origins: individuals, households, buildings at 200 m | Filosofi 2021 natural level redistributed with Fichiers fonciers dwellings at building points; Filosofi-like 2023 (section 6). |
| Opportunities: jobs, services, nature, social, varying with macro-economic dynamics | Control totals times allocation keys, per year and scenario, in one flagged destination grid (section 7). |
| Car times free-flow now; congestion later, calibrated on Google Maps data | Capacity and class on every car edge; congestion as an out-of-equilibrium loop (section 12). |
| Origins in metropolitan France; destinations include nearby foreign NUTS3 (later NUTS2) | Networks, jobs and nature extend beyond the border (no population or services abroad), plus a routing halo so French-to-French trips can transit abroad when faster. |
| Dynamic scenarios, including very large ones (station reopenings across France, redistribution of jobs and buildings) | Event timeline, automatic triage of edits, error bounds, full runs parallel by tile when needed (section 11). |
| Data searched online through available APIs | One acquisition package driven by a manifest of versioned sources (section 5). |
| Coherent reference years | Baseline 2021, second state 2023, one dating rule (section 5.2). |
| Python, as fast as possible; implemented with Claude Code and GitHub agents | DuckDB and Arrow for tables, numba for searches; repository, conventions and first files specified in section 14. |
