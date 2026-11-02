# 5. Data acquisition

## 5.1 Principles

- **One acquisition package and one manifest.** Every dataset is described once in `config/sources.yaml`: provider, version or release, URL or API query, licence, expected checksum or size, download date and local path. Downloads are idempotent (skipped when the recorded size and SHA-256 match), resumable and logged; a failed file does not stop the batch. A file is verified against the provider's checksum where one is published, otherwise against the advertised size, and its local SHA-256 is recorded.
- **Raw files are never edited.** A separate conversion step writes Parquet in EPSG:3035 with grid cell ids; every later step reads only these converted tables.
- **Discovery through APIs where they exist** (data.gouv.fr, transport.data.gouv.fr, IGN Géoplateforme, GISCO, Eurostat, INSEE catalogue); direct versioned URLs otherwise (INSEE files, Geofabrik, Overture).
- **Restricted data stay local.** The Fichiers fonciers come through a Cerema convention and have no API; the manifest records their local path and millésime, and the files are registered, never downloaded or modified by script.
- **National coverage from the start.** All sources are acquired for metropolitan France and the destination area abroad, not for the pilot only; the pilot (the Gironde with a 50 km halo) is a processing area.
- **Archive what cannot be fetched again.** Overture keeps each release online for 60 days only, and transit feeds change constantly: every extract used is stored under `data/raw` with its manifest entry.
- **One geography for all years.** Communes and EPCI in their 2026 versions, NUTS in its 2024 version; data of 2021 and 2023 are recoded with INSEE's table de passage.

## 5.2 Reference years and vintages

The baseline is 2021, the year of Filosofi 2021 and of the census and employment files of the same year. The second state is 2023, the latest year for which census, employment and commuting files exist. One dating rule applies: **physical stocks (buildings, networks, services) are taken at 1 January of the following year, the "end of year"; statistics on people and jobs are taken for the state year.**

| Layer | Baseline 2021 | Second state 2023 | Notes |
|---|---|---|---|
| Population, households | Filosofi 2021, natural level; Eurostat 2021 1 km grid (population, residential change 2020–2021); census 2021 commune data | Census 2023 commune data; Filosofi-like 2023 generated from the Fichiers fonciers 2024 (section 6.3) | Census results for year N pool the collections of N−2 to N+2 |
| Buildings | Fichiers fonciers 2022 (stock at 1 January 2022) | Fichiers fonciers 2024 (stock at 1 January 2024) | Cerema convention, no API |
| Job totals | INSEE EMP 2021, employment at place of work | INSEE EMP 2023 | The same source validates the allocation at commune level |
| Job keys | Fichiers fonciers 2022 premises; OSM of 1 January 2022 (public-sector surfaces); Overture (archived extract) for comparison | Fichiers fonciers 2024; OSM of 1 January 2024; Overture | Overture starts in July 2023, so for 2021 it serves only as a comparison of shares |
| Services | BPE 2021, used for 1 January 2022 | BPE 2025 | BPE 2024 cannot be found on INSEE's site, so BPE 2025 stands for the 2023 state; codes changed in 2023 (section 7.3) |
| Roads, bike infrastructure, nature, land use, PT stops | OSM extracts of 1 January 2022 | OSM extracts of 1 January 2024 | Geofabrik dated extracts |
| PT timetables | 2026 GTFS, rebuilt for the network of 1 January 2022 (section 5.6) | 2026 GTFS, rebuilt for 1 January 2024 | No archived feeds found; frequencies are those of 2026 |
| Commuting flows and modes | MOBPRO 2021 | MOBPRO 2023 | Validation of mode choice and of commune-to-commune work flows |
| Daily travel time budget (and energy) | EMP 2019; EMC² surveys of 14 EPCIs (Cerema, published 2019–2022) | Same | EMP 2019 is pre-COVID; EMC² surveys were carried out from 2018 to 2022, some during the COVID period but never during lockdowns |
| Foreign regions | NUTS3 employment 2021 (Eurostat `nama_10r_3empers`) | NUTS3 employment 2023 | Jobs only, allocated with Overture (section 7.2) |
| Boundaries | Communes and EPCI 2026; NUTS 2024 | Same | Recoding with the table de passage |

## 5.3 Sources

Long addresses are broken over several lines; they read as one URL.

| Dataset | Vintages | Access | Use |
|---|---|---|---|
| Filosofi gridded data, natural level | 2021 | https://www.insee.fr/fr/statistiques/fichier/8735108/Filosofi2021_carreaux_nivNaturel_csv.zip | Origins (section 6) |
| Filosofi gridded data, natural level and 200 m | 2019 | INSEE, same series | Temporal test of the origins model (section 6.5) |
| Eurostat census grid (GISCO population grids) | 2021, 1 km (already downloaded) | https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids | Validation of origins; residential change 2020–2021 |
| Census commune data (RP) | 2021 and 2023, same source | https://www.insee.fr/fr/statistiques/5359146 | Commune control totals; 2023 origins |
| Census home-to-work file (MOBPRO) | 2021, 2023 | 2021: https://www.insee.fr/fr/statistiques/8205896?sommaire=8205966; 2023: https://www.insee.fr/fr/statistiques/9004795?sommaire=9004842 | Validation of mode choice and of commune-to-commune work flows |
| Employment at place of work (EMP), replacing Flores | 2021, 2023 | 2021: https://www.insee.fr/fr/statistiques/8202930?sommaire=8205947; 2023: https://www.insee.fr/fr/statistiques/9004561 | Job totals by EPCI and sector; commune validation |
| BPE (permanent equipment base) | 2021 (downloaded); 2025 | INSEE; nomenclatures: INSEE lists of equipment types for BPE 2021 and BPE 2025; latest vintage: https://www.insee.fr/fr/statistiques/8217525?sommaire=8217537 | Services |
| Fichiers fonciers | 2022, 2024 (2021 also available) | Cerema convention, local files | Dwellings, premises, sectors of premises |
| OpenStreetMap | 1 January 2022 and 2024 | https://download.geofabrik.de/ (dated extracts of France and 13 neighbouring regions; no checksum file is published for dated extracts, so files are checked by size) | Networks, bike infrastructure, nature, public-sector surfaces, PT stops and route relations (section 5.6) |
| Overture places | Release 2026-09-23.1, archived | Public S3 GeoParquet, read with DuckDB | Comparison of job keys; foreign jobs |
| GTFS | 2026 feeds, snapshot of October 2026 | transport.data.gouv.fr API, producer resources (section 5.4); foreign portals | Public transport, rebuilt per state (section 5.6) |
| Openings and closures of public transport lines | 1 January 2022 to October 2026, plus planned lines | Compiled for this project from public sources, with sources per entry: `config/French transit openings 2022 to 2026.csv` | Past PT states (section 5.6); dated events for scenarios (section 11.2) |
| National travel survey (EMP 2019) | 2018–2019 | SDES public tables, open licence (also on data.gouv.fr) | Daily travel time budget; trip rates by purpose |
| National travel survey (ENTD 2008) | 2007–2008 | SDES public tables, open licence | Change of the daily travel time budget between 2008 and 2019 (section 9.9) |
| Households by number of cars (census, via the Tableau de bord des mobilités durables) | 2011, 2016, 2022; communes | https://www.data.gouv.fr/datasets/part-des-menages-selon-le-nombre-de-voiture-a-disposition | Car ownership grid (section 6.4) |
| Territorial travel surveys (EMC², Cerema) | 14 territories, surveys 2018–2022 (section 5.4) | Cerema [TO CONFIRM: access conditions] | Daily travel time budget at local scale; trip rates by purpose; validation |
| Cycle infrastructure (Géovélo, national schema) | Monthly files since mid-2022; the earliest (18 July 2022) stands for the 2021 state, the January 2024 file for the 2023 state | https://transport.data.gouv.fr/datasets/amenagements-cyclables-france-metropolitaine | Validation of OSM bike infrastructure; possibly the base bike network (section 8.1) |
| NUTS boundaries | NUTS 2024 | https://ec.europa.eu/eurostat/web/gisco/geodata/statistical-units/territorial-units-statistics | Study area |
| Communes to EPCI table | 2026 | https://www.insee.fr/fr/information/7671844 | Aggregation zones |
| Communes table de passage | Since 2003 | https://www.insee.fr/fr/information/7671867 | Recoding 2021 and 2023 data to 2026 |
| Commune contours | 2021, 2023, 2026 | https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/2021/geojson/; https://etalab-datasets.geo.data.gouv.fr/2023/geojson/; https://etalab-datasets.geo.data.gouv.fr/2026/geojson/ | Maps; point-in-commune joins |
| Elevation (BD ALTI, IGN) | 25 m resolution | https://www.data.gouv.fr/datasets/bd-alti-r-1 | Gradients for walk and bike |
| Eurostat national employment | 2021, 2023 | `lfsi_emp_a`: https://ec.europa.eu/eurostat/databrowser/view/lfsi_emp_a/default/table?lang=en | National control (country level only) |
| Eurostat NUTS3 employment | 2021, 2023 | `nama_10r_3empers`: https://ec.europa.eu/eurostat/databrowser/view/nama_10r_3empers/default/table?lang=en | Foreign job totals (place of work) |

The national building reference (RNB) is not used.

## 5.4 Access notes

- **transport.data.gouv.fr:** `/api/datasets` returns all datasets and their resources in one call, `/api/datasets/{id}` the details; no authentication or quota; documentation at `/swaggerui`.
- **GTFS inventory.** Only producer resources are kept: community copies are excluded unless they are the producer's own feed under a community tag (TCL Lyon, resource 81943, forced in by configuration). Each resource is downloaded from the producer's URL; if that fails, from its own latest archive on transport.data.gouv.fr when it is less than 60 days old, never from older archives or other mirrors. The October 2026 snapshot has 552 producer resources in 486 datasets; 551 were downloaded, 536 pass the offline checks (valid archive, required files, service dates), 47 have expired calendars and 15 are unusable; all are listed with their errors in `config/gtfs_inventory.csv`, and none is repaired or deleted automatically. Regional and departmental aggregates overlap local feeds: of the 1,127 transport authorities (AOM) of metropolitan France, 262 have a feed of their own, 865 are covered only through an aggregate, and none is uncovered. Some networks publish only on data.gouv.fr and not on the national access point (Caen's Twisto); they are covered by their regional aggregate (Normandy). The PT build keeps one copy of each agency (section 8.6).
- **GTFS history.** A 2026 feed cannot be filtered back to 2021 or 2023: its calendars only cover its own validity period. No archive goes further back than 2026 (transport.data.gouv.fr resource history, Mobility Database, Transitland), so past supply is rebuilt (section 5.6).
- **Geofabrik:** dated extracts (`-220101`, `-240101`) are published without `.md5` files, unlike the current extracts; the advertised size is recorded at discovery and checked at download (4.14 GB for France on 1 January 2022, 4.50 GB on 1 January 2024).
- **IGN Géoplateforme download:** `https://data.geopf.fr/telechargement/capabilities` lists resources, then `/resource/{name}`, `/resource/{name}/{sub}` and `/download/{name}/{sub}/{file}`; limited to 10 requests per second per IP address.
- **Overture:** `s3://overturemaps-us-west-2/release/{release}/theme=places/type=place/*`, queried with DuckDB and a bounding-box filter on the national box (west, south, east, north: −5.5, 40.4, 10.0, 51.6); the release in use is 2026-09-23.1. Release 2026-09-23.0 (schema v2.0.0) removed the `categories` field: queries must use `taxonomy.primary`, `taxonomy.hierarchy`, `taxonomy.alternates` or `basic_category`, and can filter on `operating_status`. The current scripts use `categories.primary` and will fail on newer releases. Releases stay online for 60 days, so the extract used must be archived locally.
- **INSEE:** BPE 2023 and 2024 (situation at 1 January) are described in INSEE's metadata but cannot be downloaded, so BPE 2025 is used for the 2023 state; its two-year lead is a limitation of the back-test for services. The API catalogue also offers Sirene, BDM, Données locales and Métadonnées. Large files (Filosofi, MOBPRO, EMP) are downloaded as versioned zip or Parquet files.
- **EMP 2019:** the SDES public tables include households, individuals and daily trips (`K_DEPLOC`, with modes and distances), with residence and trip ends coded by density grid, urban unit, attraction area and region, not by commune.
- **ENTD 2008:** the SDES public tables have the same structure as EMP 2019 (`K_DEPLOC` with `V2_` prefixes, `K_INDIVIDU`, `Q_TCM_INDIVIDU`, `Q_TCM_MENAGE`), with two-decimal codes for modes and purposes. Each respondent describes the weekday before the visit and one or both weekend days, each with its own day weight (`POIDS_JOUR`, zero for trips outside the reference weekday). Trip ends are coded by urban-unit status (centre, suburb, isolated town, rural) and the residence by urban-unit size, not by density grid. The mapping to EMP 2019's variables and codes is in `docs/data/entd2008.md`.
- **EMC² surveys (Cerema):** household surveys in which each member describes all trips of the previous day; they were not carried out during COVID lockdowns, so they reflect ordinary mobility. They cover an EPCI or a département, with a finer zoning inside [TO CONFIRM: zoning and leg detail]. The 14 territories:

| Territory | Year | Territory | Year |
|---|---|---|---|
| Aix-Marseille-Provence | 2020 | Indre-et-Loire | 2019 |
| Bassin de vie des Sables d'Olonne | 2021 | Lannion-Trégor Communauté | 2022 |
| Gironde | 2021 | Loire Sud – Pilat | 2021 |
| Grand Reims | 2021 | Métropole Savoie et Avant-Pays Savoyard | 2022 |
| Grande Région Angevine | 2022 | Nord Est Thionvillois | 2019 |
| Grande région grenobloise | 2020 | Valenciennois | 2019 |
| Île-de-France (IDFM) | 2018–2020 | Vendée | 2020 |

- **Eurostat:** `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset}` (JSON-stat) or the SDMX 2.1 endpoint. **GISCO:** `https://gisco-services.ec.europa.eu/distribution/v2/nuts/` lists NUTS files per year and projection.

## 5.5 Two states and a back-test

Building the whole pipeline for 2021 and for 2023 gives a test of the model on real changes:

1. **Engine consistency.** The changes observed between the two states that scenarios can represent (new trunk sections, speed limits, PT lines, bike infrastructure shares, newly developed cells, buildings, services, jobs) are written as scenario edits and applied to the 2021 baseline with the incremental engine. The resulting O-D costs, opportunities and accessibility must match a direct build of 2023. This measures the error of the engine itself (section 11.8).
2. **Behavioural back-test.** The economic model, run on the 2021 baseline plus those edits, predicts changes in flows and mode shares that are compared with observed changes between MOBPRO 2021 and MOBPRO 2023.
- **Caveats:** OSM differences between snapshots mix real infrastructure changes and mapping improvements, so the infrastructure edits must be curated (known projects, major road classes, PT lines). Census results pool five annual collections, so observed changes in commuting are smoothed. PT supply in both states is rebuilt from 2026 timetables (section 5.6), so the PT back-test is limited to line openings and extensions.

## 5.6 Rebuilding past public transport supply from current GTFS

No archived national timetables exist for the two state dates (section 5.4), so both states start from the 2026 feeds: services active on the reference day, Tuesday 13 October 2026 (a school-term weekday), each route being judged on its most-travelled stop pattern that day. For each 2026 route and each state date (1 January 2022 and 1 January 2024), the rebuild decides one of four outcomes: **keep** the route, **cut** it back to its former terminus (extension opened since), **skip** a stop (station opened since) or **drop** it (line opened since). Trips keep their 2026 times on what remains.

The method must run nationally without manual review. It combines two sources of evidence, in this order of precedence:

1. **The national openings list** (section 5.6.1), for every mode;
2. **The automatic OSM rule** (section 5.6.2), for trams only;
3. otherwise the route is **kept** as in 2026.

The first version of this section (proposal v8) matched GTFS stops to OSM stops mapped at each date. It was tested first and failed: 3 of 11 known cases right and a best F1 of 0.02 for buses over 1,574 routes. Stops are shared by several lines and stay mapped after a line changes, new stations are often mapped before they open, and bus stops are unevenly mapped. A line has to be tested as a line, which OSM route relations allow.

### 5.6.1 The national openings list

**Content.** A list compiled for this project from public sources (operators, transport authorities, press, Wikipedia), with its sources for each entry, of the changes to public transport lines in metropolitan France between 1 January 2022 and October 2026, plus planned openings (`config/French transit openings 2022 to 2026.csv`). Each row gives the network, mode, line, type of change (new line, extension, new station, reopening, restructuring, renaming, relocation, suspension, closure), the section concerned (from, to), the dates, the state of the line on 1 January 2022 and on 1 January 2024 (`keep`, `remove`, `modify` or `add`) and a confidence level (high, medium, low). It has 120 entries: 102 changes that took effect in 47 networks, and 18 planned lines or extensions, which give dated events for scenarios (section 11.2).

**Mapping.** Each network of the list is resolved to a GTFS resource of the national inventory (section 5.4); a network that has no feed of its own is resolved to the regional aggregate that carries it (Caen's Twisto network in the Normandy aggregate), and a network whose modes are published in different feeds is resolved per mode (TER Occitanie: rail in the SNCF feed, coaches in the liO feed). Each row is then matched to the 2026 routes of its mode by normalised line code (prefixes such as `TER`, `RER` or `Ligne` removed). When several lines share a code, the names of the stops in `section_from` and `section_to` decide; when no line code matches, a fallback looks for those stop names among the routes of the same mode. Each match is rated `exact`, `stop-confirmed`, `ambiguous` or `none`.

**Application.** Only rows of high or medium confidence with an `exact` or `stop-confirmed` match are applied. Only a `remove` state is an instruction; its effect depends on the type of change:

| Type of change | Effect where the state is `remove` |
|---|---|
| New line, reopening | The route is dropped |
| Extension | The route is cut at `section_from` (its former terminus); the stops up to it are kept |
| New station | That stop is removed from the route's patterns |
| Restructuring, renaming, relocation (`modify`) | No instruction: the service existed in another form (Bordeaux trams E and F run on the former tracks of A and C) |
| Suspension | No instruction: a temporary works closure on 1 January does not remove a line from a state meant to represent the normal network |
| Closure (`add`) | Known gap: the line is absent from the 2026 feeds and cannot be rebuilt; it is left out of the state and reported |

Several rows acting on one route combine: metro 14, extended at both ends in 2024, is cut at both ends, and several new stations are all skipped. Only a new line or a reopening drops a route. An extension or a new station applies to every route of the line where its anchor stop is found (the several missions of a TER line); if the anchor is not found, the edit is logged and the route is kept whole.

**National run (16 October 2026).** All 47 networks were mapped. Every row of the list falls in exactly one category, which is checked at each run:

| Category | Rows |
|---|---:|
| Applied (69 route-level edits) | 53 |
| `remove` instruction not matched: accepted residuals (Tzen 4, Mettis A extension, Périgueux BHNS, Lebus+ Aubagne – Gémenos, Pont-Saint-Esprit – Avignon) | 5 |
| Low confidence, not applied | 19 |
| No `remove` state at either date (planned lines and extensions) | 13 |
| Type of change that gives no instruction | 22 |
| Absent from the 2026 feeds (closed or suspended): known gap (Nancy TVR, Toulouse tram T2 to the airport, RER C between Massy and Épinay-sur-Orge, and five regional rail lines or sections) | 8 |
| **Total** | **120** |

A full run reads each GTFS resource once, so entries can be added to the list and applied again at any time.

### 5.6.2 The automatic OSM rule, for trams

**Evidence.** OSM public-transport route relations at each date, with their member ways and stops, extracted from the dated France extracts with DuckDB `ST_ReadOSM` in three filtered passes and cached as Parquet: 19,030 relations and 2.3 million member ways on 1 January 2022, 23,376 relations and 3.0 million member ways on 1 January 2024.

**Identity: which relation is the line.** A name pass looks for relations of the same mode with the same normalised `ref` or name, the `network` and `operator` tags breaking ties; a name match covering under 30% of the route's stops is a homonym and is discarded. Without a name match, a geometry pass takes the same-mode relation covering the largest share of the route's stops within a distance r; if that share reaches a minimum, the line existed under another name (`kept-renamed`), as for Bordeaux trams E and F.

**Coverage: which stops were served.** Relations give identity, tracks give coverage. A stop is covered at a date if it lies within r of an in-service way of **any** relation of the same mode at that date, not only of the matched one, since lines share trunk sections. Ways tagged with a lifecycle prefix (`construction:`, `proposed:`, `disused:`, `abandoned:`), `railway=construction`, or an `opening_date` or `start_date` after the snapshot are not in service.

**Decision.** A run of at least k uncovered stops at either end of the pattern is cut first; the route is then dropped if its covered share is below θ. Isolated uncovered stops inside a pattern are kept, being more often gaps in OSM than new stations; a long uncovered run inside a pattern is reported. A network whose lines are less than half covered by relations at a date is not testable at that date, and its routes are kept.

**Calibration.** The parameters were chosen on known cases in five test EPCIs (Bordeaux Métropole, Métropole de Lyon, CA Sète Agglopôle Méditerranée, CC Couserans-Pyrénées and CC Marche Occitane – Val d'Anglin) and on metro extensions in Paris, Lyon and Rennes, over r ∈ {25, 50, 100} m, θ ∈ {0.5, …, 0.9}, k ∈ {1, 2, 3} and a minimum geometry share ∈ {0.3, 0.5, 0.7}. Parameter sets were ranked by exact known outcomes, then F1, then the false-change rate, the share of the other routes of the test areas, presumed unchanged, that a rule wrongly cuts or drops. The known cases:

| Case | Expected on 1 Jan 2022 / 1 Jan 2024 |
|---|---|
| Bordeaux trams A and C (branches transferred to E and F in December 2025) | Kept / kept |
| Bordeaux tram E (December 2025, on the tracks of A and C) | Kept-renamed / kept-renamed |
| Bordeaux tram F (December 2025; airport branch opened in April 2023 as a branch of A) | Cut / cut |
| Lyon tram T4 (school-week service extended over existing track, 2026) | Kept / kept |
| Lyon tram T6 (extended north to La Doua, February 2026) | Cut / cut |
| Lyon metro B (extended to Saint-Genis-Laval, October 2023) | Cut / kept |
| Paris metro 14 (Saint-Denis Pleyel and Orly, June 2024) and 11 (Rosny-Bois-Perrier, June 2024) | Cut / cut |
| Paris metro 4 (Bagneux, January 2022) and 12 (Mairie d'Aubervilliers, May 2022) | Cut / kept |
| Rennes metro b (September 2022) | Dropped / kept |
| TER 41, 42 and 13 around Bordeaux (new halts or a service rebrand only) | Kept / kept |
| Bordeaux Express bus G (June 2024) and H (2025); Sète express bus A (January 2026) | Dropped / dropped |

Results of the national recompute (15 October 2026):

| Family | Retained parameters | Known outcomes right | False changes | Use |
|---|---|---:|---:|---|
| Tram | r = 25 m, k = 1, θ = 0.5, geometry share ≥ 0.3 | 12 / 12 | 0% | Applied automatically |
| Metro | r = 25 m, k = 2, θ = 0.5, geometry share ≥ 0.3 | 11 / 11 | 20% | Not applied: metro changes come from the list |
| Rail | As metro | 0 / 6 (lines found, but by geometry only) | 21% | Not applied |
| Bus, ferry | r = 100 m; fixed match shares | 7 / 10 | 29% | Not applied |

Only the tram rule is reliable enough to run unattended. OSM relations of bus and rail lines are incomplete nationally: on Bordeaux bus line 1, 16 of 50 stops have no relation way within 100 m. Metro changes are few and all in the list, which makes the metro rule unnecessary. The calibration values of the other families are kept in `config/gtfs_rebuild.yaml` as a reference only.

**A known OSM data gap.** Track is sometimes mapped as in service before it opens, without any date tag: the airport branch of Bordeaux tram A, opened in April 2023, was mapped as ordinary tram track before 2022. The openings list, which takes precedence, corrects such cases.

### 5.6.3 Edits file and use in the state builder

`config/pt_changes.yaml` holds the edits applied to past states: confirmed manual edits and the edits written automatically from the openings list. Candidate changes detected by the screening rules of the other families (180 to review, 340 not applied) are kept in the same file as information only; nothing in the pipeline waits for them or reads them. Routes are identified everywhere by the pair (GTFS resource id, `route_id`).

When the public transport network of a state is built (section 8.6), the presence of each route follows the precedence above, the cuts and skipped stops of each route are combined, and the remaining trips keep their 2026 times.

### 5.6.4 Limits

- Lines closed or suspended before the 2026 reference day are absent from the feeds; the 8 known cases are reported but not rebuilt. They could be rebuilt from their OSM relations with an estimated frequency [TO CONFIRM: whether to do so].
- Frequencies and timetables are those of 2026, so reorganisations of existing networks (Sète in January 2026, Lyon's renumbering in 2023) are not captured.
- Changes to ordinary bus routes that are not in the list are ignored: past bus networks are those of 2026, apart from the BHNS and major lines of the list.
- The list is the main assumption of the method: its completeness decides what is rebuilt. Entries can be added and applied again at any time.
- The back-test of 2021 to 2023 (section 5.5) therefore sees PT openings and extensions, not changes in frequency.
