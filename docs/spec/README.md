# Specification index

This folder is the Markdown version of the proposal (version 8, 9 October 2026), one file per section. "Section 9.3" in the text refers to subsection 9.3 of `09_trip_legs_energy.md`. Figures are in `figures/`.

## Files

| File | Section | Content |
|---|---|---|
| `00_summary.md` | Summary | Goal and the ten main decisions |
| `01_requirements.md` | 1 | Requirements and their design consequences |
| `02_literature.md` | 2 | Literature: grids, routing, accessibility, energy, downscaling |
| `03_architecture.md` | 3 | Two modules, network layers, resolutions |
| `04_spatial_frame.md` | 4 | Grids, cell ids, representative points, study area, tiles, storage |
| `05_data_acquisition.md` | 5 | Sources, vintages for 2021 and 2023, access, GTFS rebuilding (5.6) |
| `06_origins.md` | 6 | Population and households at 200 m, car ownership |
| `07_opportunities.md` | 7 | Jobs, services (BPE groups), nature, social, destination flags |
| `08_networks.md` | 8 | OSM edge table, bike infrastructure, walk, bike, car, trunk, PT |
| `09_trip_legs_energy.md` | 9 | Time and energy of every trip leg, reference rates, monetary cost, daily budget |
| `10_od_accessibility.md` | 10 | Searches by mode, the three products, storage, performance |
| `11_scenario_engine.md` | 11 | Timeline, triage, edit catalogue, bounds, checks |
| `12_congestion.md` | 12 | Congestion loop and Google data |
| `13_validation.md` | 13 | Validation plan |
| `14_implementation.md` | 14 | Stack, repository, conventions, script review, steps, packages, algorithms, roadmap |
| `15_risks.md` | 15 | Risks and open points |
| `16_references.md` | — | References |

## Spec files to read for each step

Steps are those of the table in section 14.5. Give the agent only these files.

| Step | Package | Spec files |
|---|---|---|
| 0 | GTFS rebuilding test | `05_data_acquisition.md` (5.6), `08_networks.md` (8.6) |
| 1 | `common` | `04_spatial_frame.md` (4.1, 4.2, 4.4), `14_implementation.md` (14.2, 14.3) |
| 2 | `acquire` | `05_data_acquisition.md`, `../data/download_checklist.md` |
| 3 | `landgrid/origins` | `06_origins.md` (6.1 to 6.3, 6.5, 6.6), `04_spatial_frame.md` (4.1) |
| 4 | `landgrid/jobs` | `07_opportunities.md` (7.1, 7.2) |
| 5 | `landgrid/services`, `nature`, `social`, `destinations` | `07_opportunities.md` (7.1, 7.3 to 7.6), `04_spatial_frame.md` (4.5) |
| 6 | `mobgrid/osm` | `08_networks.md` (8.1, 8.4, 8.5), `09_trip_legs_energy.md` (9.7, surface table) |
| 7 | `mobgrid/energy` | `09_trip_legs_energy.md` (9.1 to 9.8) |
| 8 | `mobgrid/graph` | `10_od_accessibility.md` (10.2, 10.3), `14_implementation.md` (14.7) |
| 9 | `mobgrid/layers/gridgraph.py` | `08_networks.md` (8.3, 8.4), `04_spatial_frame.md` (4.2) |
| 10 | `mobgrid/od` | `10_od_accessibility.md`, `04_spatial_frame.md` (4.5), `13_validation.md` |
| 11 | `mobgrid/budget` | `09_trip_legs_energy.md` (9.9), `05_data_acquisition.md` (5.4) |

## Later steps

| Step | Spec files |
|---|---|
| Walk layer and access tables | `08_networks.md` (8.2) |
| Car trunk layer | `08_networks.md` (8.5) |
| PT engine, fast variant, r5py benchmark | `08_networks.md` (8.6), `10_od_accessibility.md` |
| Car ownership (needs accessibility) | `06_origins.md` (6.4) |
| Monetary cost | `09_trip_legs_energy.md` (9.10) |
| Scenario engine | `11_scenario_engine.md` |
| Google validation (rework of the legacy scripts) | `12_congestion.md`, `13_validation.md`, `14_implementation.md` (14.4) |
| Congestion | `12_congestion.md` |
