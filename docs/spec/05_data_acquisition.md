# 5. Data acquisition

## 5.1 Principles

- **One acquisition package and one manifest.** Every dataset is described once in `config/sources.yaml`: provider, version or release, URL or API query, licence, expected checksum, download date and local path. Downloads are idempotent (skipped when the checksum matches), resumable and logged.
- **Raw files are never edited.** A separate conversion step writes Parquet in EPSG:3035 with grid cell ids; every later step reads only these converted tables.
- **Discovery through APIs where they exist** (data.gouv.fr, transport.data.gouv.fr, IGN Géoplateforme, GISCO, Eurostat, INSEE catalogue); direct versioned URLs otherwise (INSEE files, Geofabrik, Overture).
- **Restricted data stay local.** The Fichiers fonciers come through a Cerema convention and have no API; the manifest records their local path and millésime.
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
| Daily travel and energy budget | EMP 2019; EMC² surveys of 14 EPCIs (Cerema, published 2019–2022) | Same | EMP 2019 is pre-COVID; EMC² surveys were carried out from 2018 to 2022, some during the COVID period but never during lockdowns |
| Foreign regions | NUTS3 employment 2021 (Eurostat `nama_10r_3empers`) | NUTS3 employment 2023 | Jobs only, allocated with Overture (section 7.2) |
| Boundaries | Communes and EPCI 2026; NUTS 2024 | Same | Recoding with the table de passage |

## 5.3 Sources

Long addresses are broken over several lines; they read as one URL.

| Dataset | Vintages | Access | Use |
|---|---|---|---|
| Filosofi gridded data, natural level | 2021 | https://www.insee.fr/fr/statistiques/fichier/8735108/Filosofi2021_carreaux_nivNaturel_csv.zip | Origins (section 6) |
| Eurostat census grid (GISCO population grids) | 2021, 1 km (already downloaded) | https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids | Validation of origins; residential change 2020–2021 |
| Census commune data (RP) | 2021 and 2023, same source | https://www.insee.fr/fr/statistiques/5359146 | Commune control totals; 2023 origins |
| Census home-to-work file (MOBPRO) | 2021, 2023 | 2021: https://www.insee.fr/fr/statistiques/8205896?sommaire=8205966; 2023: https://www.insee.fr/fr/statistiques/9004795?sommaire=9004842 | Validation of mode choice and of commune-to-commune work flows |
| Employment at place of work (EMP), replacing Flores | 2021, 2023 | 2021: https://www.insee.fr/fr/statistiques/8202930?sommaire=8205947; 2023: https://www.insee.fr/fr/statistiques/9004561 | Job totals by EPCI and sector; commune validation |
| BPE (permanent equipment base) | 2021 (downloaded); 2025 | INSEE; nomenclatures: INSEE lists of equipment types for BPE 2021 and BPE 2025; latest vintage: https://www.insee.fr/fr/statistiques/8217525?sommaire=8217537 | Services |
| Fichiers fonciers | 2022, 2024 (2021 also available) | Cerema convention, local files | Dwellings, premises, sectors of premises |
| OpenStreetMap | 1 January 2022 and 2024 | https://download.geofabrik.de/ (dated extracts with .md5) | Networks, bike infrastructure, nature, public-sector surfaces, PT stops |
| Overture places | Release in use, archived | Public S3 GeoParquet, read with DuckDB | Comparison of job keys; foreign jobs |
| GTFS | 2026 feeds | transport.data.gouv.fr API; foreign portals | Public transport, rebuilt per state (section 5.6) |
| National travel survey (EMP 2019) | 2018–2019 | SDES public tables, open licence (also on data.gouv.fr) | Daily energy budget; trip rates by purpose |
| Households by number of cars (census, via the Tableau de bord des mobilités durables) | 2011, 2016, 2022; communes | https://www.data.gouv.fr/datasets/part-des-menages-selon-le-nombre-de-voiture-a-disposition | Car ownership grid (section 6.4) |
| Territorial travel surveys (EMC², Cerema) | 14 territories, surveys 2018–2022 (section 5.4) | Cerema [TO CONFIRM: access conditions] | Daily energy budget at local scale; trip rates by purpose; validation |
| Cycle infrastructure (Géovélo, national schema) | Monthly files since mid-2022 [TO CONFIRM: earlier version for 2021] | https://transport.data.gouv.fr/datasets/amenagements-cyclables-france-metropolitaine | Validation of OSM bike infrastructure; possibly the base bike network (section 8.1) |
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
- **GTFS history.** A 2026 feed cannot be filtered back to 2021 or 2023: its calendars only cover its own validity period. No archive goes further back than 2026 (transport.data.gouv.fr resource history, Mobility Database, Transitland), so past supply is rebuilt (section 5.6).
- **IGN Géoplateforme download:** `https://data.geopf.fr/telechargement/capabilities` lists resources, then `/resource/{name}`, `/resource/{name}/{sub}` and `/download/{name}/{sub}/{file}`; limited to 10 requests per second per IP address.
- **Overture:** `s3://overturemaps-us-west-2/release/{release}/theme=places/type=place/*`, queried with DuckDB and a bounding-box filter. Release 2026-09-23.0 (schema v2.0.0) removed the `categories` field: queries must use `taxonomy.primary`, `taxonomy.hierarchy`, `taxonomy.alternates` or `basic_category`, and can filter on `operating_status`. The current scripts use `categories.primary` and will fail on newer releases. Releases stay online for 60 days, so the extract used must be archived locally.
- **INSEE:** BPE 2023 and 2024 (situation at 1 January) are described in INSEE's metadata but cannot be downloaded, so BPE 2025 is used for the 2023 state; its two-year lead is a limitation of the back-test for services. The API catalogue also offers Sirene, BDM, Données locales and Métadonnées. Large files (Filosofi, MOBPRO, EMP) are downloaded as versioned zip or Parquet files.
- **EMP 2019:** the SDES public tables include households, individuals and daily trips (`K_DEPLOC`, with modes and distances), with residence and trip ends coded by density grid, urban unit, attraction area and region, not by commune.
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

1. **Engine consistency.** The changes observed between the two states (new roads and lines, speed limits, bike infrastructure, new buildings, services, jobs) are written as scenario edits and applied to the 2021 baseline with the incremental engine. The resulting O-D costs, opportunities and accessibility must match a direct build of 2023. This measures the error of the engine itself (section 11.8).
2. **Behavioural back-test.** The economic model, run on the 2021 baseline plus those edits, predicts changes in flows and mode shares that are compared with observed changes between MOBPRO 2021 and MOBPRO 2023.
- **Caveats:** OSM differences between snapshots mix real infrastructure changes and mapping improvements, so the infrastructure edits must be curated (known projects, major road classes, PT lines). Census results pool five annual collections, so observed changes in commuting are smoothed. PT supply in both states is rebuilt from 2026 timetables (section 5.6), so the PT back-test is limited to line openings and extensions.

## 5.6 Rebuilding past public transport supply from current GTFS

Both states use a representative school-period weekday of the 2026 feeds, from which the lines that did not exist at the state date are removed. The test is whether a line's stops were already mapped in OpenStreetMap at that date.

1. **OSM stops at the state date.** From the dated extract (1 January 2022 or 2024): nodes and ways tagged `public_transport=platform`, `stop_position` or `station`, `highway=bus_stop`, `railway=station`, `halt`, `tram_stop` or `stop`, and `amenity=bus_station`. Objects carrying lifecycle prefixes (`construction:`, `proposed:`, `disused:`, `abandoned:`) or `railway=construction` are excluded.
2. **Match each GTFS stop.** A stop is matched if an OSM stop of a compatible mode lies within a distance r of it.
3. **Score each line** (GTFS route, per direction pattern): n stops, m matched, share s = m / n.
4. **Drop new lines.** A line whose share s is below a threshold θ, set per mode family (bus, tram, metro, rail), did not exist at the state date and is dropped.
5. **Cut extensions.** This is the main difficulty: a line extended between the state date and 2026 must lose only its new section, not disappear. The stops of each remaining pattern are read in order; a run of at least k consecutive unmatched stops at one end of the pattern is removed, and the pattern ends at the last matched stop. Trips keep their 2026 times on the remaining section. Isolated unmatched stops inside a pattern are kept, as they are more often gaps in OSM than new stations; a long unmatched run inside a pattern (a new branch or diversion) is listed for review. k, like θ, and the treatment of isolated unmatched stops are tested in the calibration.

**Calibration.** r, θ and k are chosen on cases where the truth is known:

- **Buses:** five test EPCIs covering very different networks: Bordeaux Métropole, Métropole de Lyon, CA Sète Agglopôle Méditerranée, CC Couserans-Pyrénées and CC Marche Occitane – Val d'Anglin, with the known changes listed below and bus changes checked by hand, with r in {25, 50, 100} m, θ in {0.5, 0.6, 0.7, 0.8, 0.9} and k in {1, 2, 3}.
- **Metros:** line 14 south to Orly and line 11 to Rosny-Bois-Perrier (opened June 2024) must lose their extensions in both states. Line 4 to Bagneux (January 2022) and line 12 to Mairie d'Aubervilliers (May 2022) must lose their extensions on 1 January 2022 and keep them on 1 January 2024. Rennes metro line b (September 2022) must be absent on 1 January 2022 and present on 1 January 2024.
- **Rail and tram:** the tram cases of Bordeaux and Lyon below; no rail case is available, so rail uses the metro thresholds and the lines dropped or cut are listed for manual review.
- **Score:** share of lines correctly kept, dropped or cut (precision and recall) per mode family and parameter set; the retained parameters are reported with their scores.

Known changes in the test EPCIs, with the expected result of the rule:

| EPCI | Change | Opened | Expected on 1 Jan 2022 / 1 Jan 2024 |
|---|---|---|---|
| Bordeaux Métropole | Tram A extended to the airport (about 5 km, 5 stations) | April 2023 | Extension cut / kept |
| Bordeaux Métropole | Bus Express G (BHNS), Saint-Jean – Saint-Aubin-de-Médoc | June 2024 | Dropped / dropped |
| Bordeaux Métropole | Circular Bus Express H (temporary routes) | 2025 | Dropped / dropped |
| Bordeaux Métropole | Tram lines E and F: new names and service patterns on existing tracks, replacing part of line A | December 2025 | Not detectable by stop matching: patterns of 2026 kept on old tracks (limitation) |
| Métropole de Lyon | Tram T6 extended north, Hôpitaux-Est – La Doua (5.4 km, 10 stations) | 14 February 2026 | Extension cut / cut |
| Métropole de Lyon | BHNS Part-Dieu – Sept-Chemins | [TO CONFIRM: opening date] | Dropped where opened after the state date |
| Métropole de Lyon | Trams T9 and T10 | Not opened by October 2026 | Absent from the 2026 feeds; kept as planned projects for scenarios |
| CA Sète Agglopôle Méditerranée | Express bus line A with the RD2 bus-priority corridor; network reorganised, more frequent | 5 January 2026 | Dropped / dropped; the reorganisation and frequencies are a limitation |
| CC Couserans-Pyrénées | No new high-level service found (regional coaches, demand-responsive transport, TER at Boussens and Foix) | — | Bus and coach changes checked by hand |
| CC Marche Occitane – Val d'Anglin | No new high-level service found yet (regional coaches, demand-responsive transport, rail connections) | — | Same |

**Limits.** Lines that closed before 2026 are not in the 2026 feeds and cannot be recovered. Frequencies and timetables remain those of 2026, and line renamings or reorganisations on existing infrastructure (Bordeaux trams E and F) cannot be detected. Stops can stay mapped after a line closes, and stops shared by several lines are matched whatever the line, which biases toward keeping lines; the calibration measures this bias.
