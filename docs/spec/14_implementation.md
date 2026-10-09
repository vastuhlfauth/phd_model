# 14. Implementation

## 14.1 Performance principles

- **DuckDB is the backbone for all table work:** reading OSM (`ST_ReadOSM` in the spatial extension, or QuackOSM on top of it), reading Overture directly from S3, GTFS cleaning, rebuilding and edits in SQL, Fichiers fonciers and Filosofi processing, 200 m to 1 km aggregations, accessibility from opportunity curves, scenario differences, and the partitioned Parquet outputs. It is columnar, multi-threaded and works out of core.
- **Graph searches are not SQL.** Millions of bounded Dijkstra and RAPTOR runs go to numba-compiled code on flat CSR arrays; DuckDB hands data over through Arrow without copying.
- **No pandas or geopandas in hot paths;** they stay for one-off I/O and quality-control maps. Vectorised shapely 2 for geometry when needed.
- **EPSG:3035 and integer cell ids everywhere,** instead of Lambert-93 and WGS84 GeoPackages; GeoPackage only for maps.
- **Integer and float32 types, preallocated arrays, one worker process per tile;** all parameters in configuration files, never in code.

## 14.2 Repository organisation

One repository with four packages, so that land use and networks can evolve and run separately while sharing the grid, configuration and I/O:

```text
mobility-france/
├── README.md
├── .github/                 copilot-instructions.md, instructions/, prompts/ (14.3)
├── pyproject.toml           one workspace, four packages
├── config/                  base, modes, energy, landuse, sources (.yaml)
├── scenarios/               infrastructure/ and macro/ scenario files
├── data/                    not versioned: raw/ interim/ base/ derived/ results/
├── packages/
│   ├── common/              grid cells, configuration, DuckDB I/O, logging
│   ├── acquire/             manifest, downloaders, API clients, checksums
│   ├── landgrid/
│   │   ├── origins/         filosofi, fichiers_fonciers, households, filosofi_like
│   │   ├── jobs/            ff_premises, osm_public, overture_poi, allocate
│   │   ├── services/        bpe, code_list, presence_model
│   │   ├── nature/          polygons, access_points
│   │   ├── social/          population destinations
│   │   ├── destinations.py  flags per cell and type
│   │   └── scenarios.py     macro and land-use edits
│   └── mobgrid/
│       ├── osm/             extract, edges, bike_infra, elevation, speeds
│       ├── graph/           csr, dijkstra, simplify
│       ├── layers/          gridgraph, walk, trunk
│       ├── pt/              gtfs_clean, gtfs_rebuild, raptor, stop_tables, r5py
│       ├── energy/          rates, walk, bike, legs
│       ├── od/              compute, products, aggregate, store
│       ├── budget/          emp2019 days, daily energy
│       ├── scenario/        schema, timeline, triage, bounds, affected, run
│       └── validation/      compare
├── legacy/                  current scripts, kept for comparison until replaced
└── tests/                   one test module per source module, pilot fixtures
```

## 14.3 Conventions for the coding agents (.github/copilot-instructions.md)

- Coordinates in EPSG:3035 metres; cell ids = (N // res) × 100,000 + (E // res), with the resolution stored alongside; INSPIRE text codes `CRS3035RES{res}mN{N}E{E}` for joins with INSEE files.
- Units: time in seconds (outputs in 10 s units), distance in metres (outputs in 10 m), energy in kJ above rest for the reference mass set in `config/energy.yaml` (outputs in 0.1 kJ), with net MET-minutes derived; counts of people, jobs and services as floats until the final rounding step.
- States are named by year (2021, 2023); physical stocks are dated 1 January of the following year; all zones in the 2026 geography.
- Every external file comes through `acquire` and the manifest; no hard-coded paths or URLs in other packages.
- Graphs are CSR arrays; searches always take a cutoff, support several sources with initial offsets, and fill the three products of section 10.2.
- DuckDB for tables, numba for searches, no pandas in loops; parameters only in `config/`; every module tested on a pilot fixture (one département with its halo); outputs are deterministic.
- Any change to output schemas or units updates this document and the tests.

## 14.4 Review of the existing scripts

The current scripts contain useful logic to keep; most changes concern formats, coordinate systems, speed and a few method points.

| Script | What it does | Keep | Change |
|---|---|---|---|
| `00_download_neighbor_pbf.py` | Downloads Geofabrik extracts dated 2022-01-01 for neighbouring countries and border sub-regions | The country and sub-region list; pinning a snapshot date | Move into `acquire` with the manifest; add the 2024-01-01 extracts and France; verify .md5 checksums; derive the list from the destination NUTS3 and halo |
| `00_data_import_preparation.py` | Imports BPE 2021 with a curated list of equipment types; turns Filosofi 2019 200 m cells into centroids; builds NUTS3 boundaries; extracts OSM beaches and ski areas | The NUTS3 neighbour logic; the principle of a curated list | Review the code list against the official labels and the 2023 code changes (section 7.3); BPE 2021 and 2025; Filosofi 2021 through section 6; Parquet in EPSG:3035 with cell ids; NUTS from GISCO; DuckDB reading |
| `00_extract_parks_coast.py` | Extracts parks, protected areas and sea beaches as centroids (pyosmium, WSL only) | Tag selection; the sea-beach filter by distance to the coastline | Access points every 50 m on contours; parks of at least 2,500 m²; rivers; first in reach (section 7.4); DuckDB or QuackOSM instead of pyosmium, so it also runs on Windows; EPSG:3035 |
| `00_prepare_public_transport.py` | Validates GTFS feeds, makes ids unique, filters calendars, snaps stops to grid points, groups stops, generates transfers | Validation checks, id prefixes, route_type repair, feed discovery | Rebuilding rule of section 5.6; the four points below the table |
| `00_employment_comparison/` (18,000 lines) | Overture and OSM POIs to NACE; weights from Eurostat business statistics; population scaling law; rules for agriculture, industry and construction; NUTS3 downscaling; validation against census jobs by NA5; Monte Carlo of 40 configurations on Gironde | The method as comparison in France and as main method abroad; NACE mappings; calibration and validation framework | EPCI totals from INSEE EMP; Fichiers fonciers keys as main method in France; no population-in-reach scaling; migrate Overture queries to schema v2.0.0; merge the successive versions into one configurable module; Parquet |
| `07_evaluation_pipeline.py` (+ `_no_api` wrapper) | Samples model O-D pairs per mode (DuckDB reservoir sampling, stratified by duration bins), queries the Google Routes API at fixed departure times with retries, rate limit and resume, writes request and result tables | Sampling, request table, resume logic, rate limiting | Add `staticDuration`, `polyline` and traffic on the polyline to the field mask; stratify also by density class and region; store raw responses with their date; compare car driving time without terminal legs; read the API key through `acquire` |
| `07_evaluation_pipeline_google_subset_pt.py` | Recomputes PT at the exact departure times of the Google requests (RAPTOR from the access stops, walk access and egress) | Exact-time comparison, which removes the effect of the departure window | Call the PT engine of `mobgrid/pt` instead of importing the old Phase 4 script dynamically; same access rules as section 8.6 (20 min) |
| `08_evaluation_visuals.py` and `_google_subset_pt` variant | Comparison table, metrics by mode, hour, duration and distance bins, scatter plots and residual histograms | Metrics and plots | Merge the two near-identical versions into `mobgrid/validation/google`; add shares within ±2 and ±5 min and distance errors |

Points to fix in the PT preparation, in addition to the move to DuckDB SQL:

- **Stops are moved to grid-cell coordinates** when within 250 m of a grid point. Stop areas are network elements and access is computed from 200 m cells (section 3); stops should keep their own coordinates.
- **Service selection.** The code keeps every service running on any weekday whose date range overlaps the reference date, and ignores removals in `calendar_dates.txt`. It should keep the services active on the exact reference date: day-of-week flag, date range, additions and removals.
- **Time window.** Cutting `stop_times` to 07:00–09:30 truncates trips that start before or end after the window. Whole trips running in the 08:00–09:00 window (plus a margin) should be kept.
- **Transfers and duplicates.** Transfers are straight-line pairs built in Python loops; they should come from the walking network. Trips duplicated across feeds (TER in national and regional feeds) are not removed yet.

## 14.5 First files to build

In this order, on one pilot département with its halo and for the 2021 baseline; each step has a test that must pass before the next. Step 0 can start immediately.

| # | Package / files | Purpose | Acceptance test |
|---|---|---|---|
| 0 | GTFS rebuilding test (DuckDB only) | Stop matching between 2026 GTFS and OSM of 1 January 2022 and 2024 on the five test EPCIs and the metro cases; share thresholds by mode family; cutting of extensions | Score table; parameters r, θ and k chosen |
| 1 | `common`: config, grid cells, DuckDB I/O | Parameters, cell ids and INSPIRE codes, nesting, 24-neighbour stencil, tiles; Parquet and Arrow helpers | Round trip with INSEE 200 m and 1 km codes; 25 children per 1 km cell; configuration rejects invalid values |
| 2 | `acquire`: manifest and downloaders | INSEE files, data.gouv.fr, transport.data.gouv.fr, Géoplateforme, GISCO, Eurostat, Geofabrik, Overture S3; 2021 and 2023 vintages | Pilot inputs downloaded twice give identical checksums; manifest records every vintage; Overture extract archived |
| 3 | `landgrid/origins` | Fichiers fonciers 2022 at building points, households, the two variants for individuals, Filosofi 2021 totals | Natural-level totals preserved exactly; comparison with INSEE 200 m and the Eurostat grid reported |
| 4 | `landgrid/jobs` | Fichiers fonciers premises keys, OSM public-sector surfaces, EMP totals; Overture comparison | EPCI totals exact; commune validation by sector for both methods |
| 5 | `landgrid/services`, `nature`, `social`, `destinations` | BPE groups in both nomenclatures; nature access points; social cells; flags | Counts match BPE; access points on polygon boundaries; flags consistent with counts |
| 6 | `mobgrid/osm` | Nodes and ways from PBF; directed edges with access per mode; bike infrastructure classes; gradients; free-flow times | Connectivity checks; car times on sample paths within tolerance of OSRM; bike infrastructure compared with the national dataset |
| 7 | `mobgrid/energy` | Leg formulas of section 9 per mode and direction | Reproduces the reference rates of section 9.2 and the checks of sections 9.3 and 9.7 |
| 8 | `mobgrid/graph` | CSR graph; bounded multi-source Dijkstra with secondary weights, predecessors and the three products | Same distances as scipy's Dijkstra on random graphs; products equal brute-force sums and minima |
| 9 | `mobgrid/layers/gridgraph.py` | 1 km grid edges to 24 neighbours, stray check, time per road class | Edge times equal OSRM between neighbouring cells within tolerance |
| 10 | `mobgrid/od` | Car and bike O-D and products for the pilot, Parquet output | Validation metrics of section 13 against OSRM |
| 11 | `mobgrid/budget` | EMP 2019 survey days rebuilt as legs; daily energy per person | Constancy tests of section 9.9 reported |

Then: walk layer, trunk layer, PT engine and fast variant, scenario engine (timeline, triage, bounds), national tiling.

## 14.6 Candidate packages

| Task | Packages | Notes |
|---|---|---|
| Tables, OSM, Overture, GTFS, outputs | duckdb (+ spatial, httpfs), quackosm, pyarrow | Backbone of all data work |
| API clients and downloads | httpx or requests; eurostat; pynsee for INSEE files in its catalogue (`get_file_list`, `download_file`), local data, BDM series and Sirene; direct calls to the Melodi API, which pynsee does not cover; overturemaps (optional) | All calls go through `acquire`; pynsee's file catalogue is maintained by volunteers, so each recent dataset (Filosofi 2021, EMP and MOBPRO 2021 and 2023, census 2023, BPE) is checked in step 2 |
| Arrays and compiled searches | numpy, numba | CSR graphs, Dijkstra, RAPTOR, products |
| Geometry | shapely 2 (vectorised), pyproj; exactextract | exactextract gives the exact share of each cell covered by a polygon, where rasterio.features only marks cells as in or out; contour access points with shapely |
| Snapping and matching | scipy.spatial (cKDTree) | Nearest node per point; GTFS stops to OSM stops |
| Elevation | rasterio | Sampling IGN elevation at nodes |
| Statistics | statsmodels or scikit-learn | Household size model; Filosofi-like 2023; daily energy budget |
| Configuration and scenarios | pydantic, PyYAML | Typed validation of every parameter and edit |
| Tile caching | xxhash | Content hash of each tile's inputs |
| Parallelism | joblib or multiprocessing | One process per tile |
| PT engine to benchmark | r5py | Against the numba RAPTOR |
| Reference and validation | OSRM (existing), OTP | Not used in production |
| Command line, tests, maps | typer, pytest; geopandas and pyogrio for maps only |  |

## 14.7 Algorithms to implement

| Algorithm | Used for | Notes |
|---|---|---|
| Redistribution preserving zone totals (dasymetric) | Origins at 200 m; jobs within EPCI | Key per variable; totals checked exactly |
| Regression of household size on dwelling characteristics | Keys for individuals; Filosofi-like 2023 | Estimated across natural-level cells |
| Iterative proportional fitting | Consistency of variables within cells | Age groups, household types |
| Nearest-neighbour matching (KD-tree) | GTFS stops to OSM stops | Per mode family, with distance r |
| Exact polygon-grid intersection; boundary crossings | Nature access points, land-use areas | Plus OSM entrances and points every 50 m |
| Bounded multi-source Dijkstra with secondary weights | All road and walk searches, grid edges, access tables | Binary heap with stale-entry skipping; reusable workspace; Dial's bucket queue as a faster variant with integer times |
| Binned accumulation and k-nearest labels during the search | Opportunity curves; nearest of each type | A few array updates per settled flagged cell |
| Speed from a force balance | Bike and e-bike edge speeds | Cubic in v solved per edge and direction |
| Reverse search, pruned by stored values | New destinations; nearest-of-type updates; affected origins | Same code on the transposed graph |
| Min-plus combination of tables | PT fast variant; land-use updates for PT | Stop-to-stop times with access and egress tables |
| Path-fixed update and bounds | Gradual levers; interpolation between epochs | From stored time components |
| Decomposition by first new element | Few added links or stops | Forward and backward searches per element |
| Path tracing from predecessor edges | Stray check of grid edges, assignment later | Only for the 24 neighbour targets per cell |
| Degree-2 contraction, largest component | Shrinking the OSM graph | Keeps exact times, distances and energy |
| RAPTOR and range RAPTOR (Delling et al. 2015) | PT over the departure window | Range RAPTOR reuses labels across departures |
| ULTRA transfer shortcuts (Baum et al. 2023) | Unrestricted walking between stops | Later, if transfer limits matter |
| Content hashing per tile | Rebuilding only changed tiles | Hash of inputs, parameters and code version |
| Speed-flow models and regressions | Congestion (later) | Out-of-equilibrium loop |

## 14.8 Roadmap

| Phase | Content | Deliverable |
|---|---|---|
| 0. Data and origins | GTFS rebuilding test; acquisition package and manifest with 2021 and 2023 vintages; origins at 200 m on the pilot; BPE list review | Thresholds; versioned base tables; origins validation |
| 1. Pilot | Opportunities and destination flags; all network layers with leg formulas; products; validation; r5py vs RAPTOR benchmark and fast variant; speed calibration against OSRM; storage decisions; EMP 2019 budget re-estimation | Validation report; engine, storage, allocation and energy choices |
| 2. National baseline | Origins and opportunities nationally; tiled national run, all modes, for 2021 | Baseline 2021 tables and products |
| 3. Second state and scenarios | 2023 build; scenario engine (timeline, triage, bounds, caching); back-test 2021 to 2023 | 2023 tables; back-test report; scenario runs with logs |
| 4. Congestion and crowding | Speed-flow models on Google Maps data; out-of-equilibrium loop; PT loads and crowding | Congested car costs; crowding-dependent PT energy |
