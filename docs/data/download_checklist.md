# Download checklist

Store original files under `data/raw/` and never edit or unpack archives in place.
The file-level catalog is [config/sources.yaml](../../config/sources.yaml).
No data files were downloaded while resolving these URLs (2026-10-09).
The [saved dry-run output](acquire_dry_run.txt) lists 690 HTTP downloads proposed,
1 Overture extraction, 27 unavailable/checksum-blocked entries and 8
manual/restricted skips (exit 0).

```powershell
# Metadata discovery only: bounded JSON/Atom GETs and OSM HEADs, no data GETs.
uv run python -m acquire --manifest config\sources.yaml --all --discover
# Offline preview; does not discover, download, or change the manifest.
uv run python -m acquire --manifest config\sources.yaml --all --dry-run
# Actual download only when explicitly requested:
uv run python -m acquire --manifest config\sources.yaml --dataset filosofi
```

Discovery can also select `gtfs`, `bdalti`, or `osm` individually. It writes the
resolved file entries back to the catalog. Re-discovery preserves acquisition
records only when the URL and local path are unchanged. Downloads resume `.part`
files and record size, SHA-256, date, and independent verification status.
Discovery URLs, raw-path templates, départements, neighbouring regions, vintages,
step-0 feed patterns and request/retry limits are validated from
[config/acquisition.yaml](../../config/acquisition.yaml), adjacent to the manifest
(or selected with `--acquisition-config`). DuckDB is declared as a direct
acquisition dependency for the Overture extraction; it was already installed
as part of the project's stack.
Extensionless endpoints use the entry id plus the known file extension locally.
Published producer URL keys are retained verbatim; no private credentials are used.

## Already available / register only

- [ ] BPE 2021: `data/raw/bpe/INSEE_bpe21-ensemble-xy-csv/`
- [ ] BPE 2021 equipment lists: `data/raw/bpe/nomenclature/`
- [ ] Eurostat 2021 census grid: `data/raw/eurostat_grid/Eurostat_Census-GRID_2021_V3/`
- [ ] Fichiers fonciers, all départements, 2021/2022/2024:
  `data/raw/fichiers_fonciers/{ff2021,ff2022,ff2024}/`
- [ ] EMC² Gironde 2021 and the other 13 surveys when received:
  `data/raw/emc2/gironde_2021/` and `data/raw/emc2/other_surveys/`.
  The latter is a receipt staging directory, not an invented survey list.

Restricted files are never downloaded. After receipt, register the files:

```powershell
uv run python -m acquire --manifest config\sources.yaml --register-restricted fichiers_fonciers
uv run python -m acquire --manifest config\sources.yaml --register-restricted emc2
```

## National discovery and spatial sources

### GTFS: one October 2026 snapshot

- [ ] Discover [transport.data.gouv.fr/api/datasets](https://transport.data.gouv.fr/api/datasets):
  every `public-transit` dataset, every producer-owned resource with format `GTFS`.
  Exclude resources listed in `community_resources` or marked with a community
  publisher. Keep all remaining resources, including overlaps and multiple
  resources per dataset. Use `original_url` (current published producer URL),
  falling back to the API's `url` if absent.
- Save to `data/raw/gtfs/2026-10/{dataset_id}/{resource_id}.zip`.
- [GTFS inventory](../../config/gtfs_inventory.csv) is next to the manifest and
  records dataset id, slug, title, resource id, URL, covered area, availability,
  check date, per-dataset GTFS resource count, and a multiple-resource flag.
- [Datasets with multiple GTFS resources](../../config/gtfs_multiple_resources.csv)
  lists their ids, slugs, titles, counts, and resource ids. Keep all for now.
- Discovery on 2026-10-09: initially 565 resources / 487 datasets; excluding 13
  community resources leaves **552 producer resources / 486 datasets**.
  **33 datasets** have multiple GTFS resources.
- API-marked unavailable resources are listed, not fetched. GTFS failures during
  a later acquisition are recorded and listed without terminating the batch.
- The retained TCL Lyon producer resource `65812` is currently API-marked
  unavailable. Its available community copy is deliberately excluded.

Step-0 prerequisites: IDFM, TCL Lyon, STAR Rennes, Sète Agglopôle Méditerranée,
TBM Bordeaux, SNCF (TER/Intercités/TGV), liO Occitanie and Rémi. IDFM's producer
file is <https://eu.ftp.opendatasoft.com/stif/GTFS/IDFM-gtfs.zip>; SNCF's is
<https://eu.ftp.opendatasoft.com/sncf/plandata/Export_OpenData_SNCF_GTFS_NewTripId.zip>.
The Nouvelle-Aquitaine aggregate is retained through discovery, at its published
URL <https://www.pigma.org/public/opendata/nouvelle_aquitaine_mobilites/publication/naq-aggregated-gtfs.zip>.

Couserans-Pyrénées and Marche Occitane – Val d'Anglin (SIREN **200035137**)
have no networks of their own. liO and Rémi producer feeds are present:

- liO: <https://app.mecatran.com/utw/ws/gtfsfeed/static/lio?apiKey=2b160d626f783808095373766f18714901325e45&type=gtfs_lio>
- Rémi: <https://fr.ftp.opendatasoft.com/centrevaldeloire/OKINAGTFS/GTFS_AO/REMI.zip>

**Coverage remains to be checked spatially in step 0:** stops inside the 2026
EPCI polygons, not matches against the EPCI/network names.

### BD ALTI 25 m

- [ ] Resolve the paginated IGN Atom feed
  <https://data.geopf.fr/telechargement/resource/BDALTI>, then each entry page.
  Keep every `25M_ASC_LAMB93` département edition in metropolitan France.
  Codes 001–095 except obsolete 020, plus 02A and 02B: **96 départements**.
  Corsica uses `IGN78C`; do not require `IGN69`. Exclude overseas entries.
- Save the original `.7z` names to `data/raw/bdalti/25m/`, without extraction.
  All 96 archive URLs, advertised sizes, and edition dates are in the manifest.
- At most one IGN request per second, including retries; allow five retries
  after the initial request, with increasing waits. Respect `Retry-After`
  (seconds or HTTP date) without shortening the server's requested wait.

### Overture places

- [ ] Release **2026-09-23.1**:
  `s3://overturemaps-us-west-2/release/2026-09-23.1/theme=places/type=place/*`
- Anonymous DuckDB extraction to
  `data/raw/overture/2026-09-23.1/overture-places.parquet`.
- Longitude **-5.5 to 10.0**, latitude **40.4 to 51.6**, including Corsica and the
  adjacent foreign NUTS3 envelope. Preserve all place columns; intersect record
  bounding boxes. Precise France/NUTS3 clipping happens later.
- Archive before approximately **2026-11-22** (release retention is about 60 days).
  A dry run does not access S3 or install DuckDB extensions.

### OSM France and neighbouring routing regions

- [ ] France: <https://download.geofabrik.de/europe/france-220101.osm.pbf> and
  <https://download.geofabrik.de/europe/france-240101.osm.pbf>, with their `.md5`.
- [ ] For each neighbouring region below, use exactly
  `https://download.geofabrik.de/europe/{region}-{220101|240101}.osm.pbf`
  and that URL plus `.md5`. Save originals to `data/raw/osm/{220101,240101}/`.
  No alternative region names are guessed.

| Region | 2022-01-01 PBF | 2024-01-01 PBF |
|---|---|---|
| belgium | <https://download.geofabrik.de/europe/belgium-220101.osm.pbf> | <https://download.geofabrik.de/europe/belgium-240101.osm.pbf> |
| luxembourg | <https://download.geofabrik.de/europe/luxembourg-220101.osm.pbf> | <https://download.geofabrik.de/europe/luxembourg-240101.osm.pbf> |
| switzerland | <https://download.geofabrik.de/europe/switzerland-220101.osm.pbf> | <https://download.geofabrik.de/europe/switzerland-240101.osm.pbf> |
| andorra | <https://download.geofabrik.de/europe/andorra-220101.osm.pbf> | <https://download.geofabrik.de/europe/andorra-240101.osm.pbf> |
| monaco | <https://download.geofabrik.de/europe/monaco-220101.osm.pbf> | <https://download.geofabrik.de/europe/monaco-240101.osm.pbf> |
| germany/baden-wuerttemberg | <https://download.geofabrik.de/europe/germany/baden-wuerttemberg-220101.osm.pbf> | <https://download.geofabrik.de/europe/germany/baden-wuerttemberg-240101.osm.pbf> |
| germany/rheinland-pfalz | <https://download.geofabrik.de/europe/germany/rheinland-pfalz-220101.osm.pbf> | <https://download.geofabrik.de/europe/germany/rheinland-pfalz-240101.osm.pbf> |
| germany/saarland | <https://download.geofabrik.de/europe/germany/saarland-220101.osm.pbf> | <https://download.geofabrik.de/europe/germany/saarland-240101.osm.pbf> |
| italy/nord-ovest | <https://download.geofabrik.de/europe/italy/nord-ovest-220101.osm.pbf> | <https://download.geofabrik.de/europe/italy/nord-ovest-240101.osm.pbf> |
| spain/pais-vasco | <https://download.geofabrik.de/europe/spain/pais-vasco-220101.osm.pbf> | <https://download.geofabrik.de/europe/spain/pais-vasco-240101.osm.pbf> |
| spain/navarra | <https://download.geofabrik.de/europe/spain/navarra-220101.osm.pbf> | <https://download.geofabrik.de/europe/spain/navarra-240101.osm.pbf> |
| spain/aragon | <https://download.geofabrik.de/europe/spain/aragon-220101.osm.pbf> | <https://download.geofabrik.de/europe/spain/aragon-240101.osm.pbf> |
| spain/cataluna | <https://download.geofabrik.de/europe/spain/cataluna-220101.osm.pbf> | <https://download.geofabrik.de/europe/spain/cataluna-240101.osm.pbf> |

HEAD checks on 2026-10-09: **all 26 neighbouring PBFs return 200**, but
**all 26 exact `.osm.pbf.md5` URLs return 404**. Record file and checksum
availability separately. The downloader lists checksum-blocked entries rather
than silently dropping checksum verification; resolve the missing sidecars
before acquisition. HEAD failure/unsupported HEAD is reported as unconfirmed,
not interpreted as a missing file. Destinations are adjacent NUTS3 plus a
50 km routing halo; clipping belongs to later processing.

## Direct national files

Each row is one file; listed URLs are kept as published. Direct HTTP access
includes redirecting SDES/data.gouv.fr endpoints and open INSEE Melodi endpoints
(no API key). Local filenames without URL extensions are based on entry ids.

| Dataset / file | Vintage | Direct URL | Local directory |
|---|---|---|---|
| FILOSOFI natural level | 2021 | <https://www.insee.fr/fr/statistiques/fichier/8735108/Filosofi2021_carreaux_nivNaturel_csv.zip> | `data/raw/filosofi/2021/` |
| FILOSOFI imputed 200 m benchmark | 2021 | <https://www.insee.fr/fr/statistiques/fichier/8735162/Filosofi2021_carreaux_200m_csv.zip> | `data/raw/filosofi/2021/` |
| Census dossier complet | 2021 | <https://www.insee.fr/fr/statistiques/fichier/5359146/dossier_complet_31_12_2024.zip> | `data/raw/census/2021/` |
| Census dossier complet | 2023 | <https://www.insee.fr/fr/statistiques/fichier/5359146/dossier_complet.parquet> | `data/raw/census/2023/` |
| Census guide | current | <https://www.insee.fr/fr/statistiques/fichier/5359146/guide_base_dossier_complet_comparateur.pdf> | `data/raw/census/` |
| EMP TD_EMP1 | 2021 | <https://www.insee.fr/fr/statistiques/fichier/8202930/TD_EMP1_2021_csv.zip> | `data/raw/emp/2021/` |
| EMP TD_EMP2 | 2021 | <https://www.insee.fr/fr/statistiques/fichier/8202930/TD_EMP2_2021_csv.zip> | `data/raw/emp/2021/` |
| EMP TD_EMP3 | 2021 | <https://www.insee.fr/fr/statistiques/fichier/8202930/TD_EMP3_2021_csv.zip> | `data/raw/emp/2021/` |
| EMP TD_EMP4 | 2021 | <https://www.insee.fr/fr/statistiques/fichier/8202930/TD_EMP4_2021_csv.zip> | `data/raw/emp/2021/` |
| EMP code passage | 2021 | <https://www.insee.fr/fr/statistiques/fichier/8202930/Table_passage_rp_emploi.xlsx> | `data/raw/emp/2021/` |
| EMP reading guide | 2021 | <https://www.insee.fr/fr/statistiques/fichier/8202930/Aide_lecture_rp_emploi.pdf> | `data/raw/emp/2021/` |
| EMP AGEEMPFORM | 2023 | <https://api.insee.fr/melodi/file/DS_RP_TD_EMPLOI_LT_AGEEMPFORM_COMP_2023/PARQUET> | `data/raw/emp/2023/` |
| EMP EMPFORMACTIVITY | 2023 | <https://api.insee.fr/melodi/file/DS_RP_TD_EMPLOI_LT_EMPFORMACTIVITY_COMP_2023/PARQUET> | `data/raw/emp/2023/` |
| EMP PCSACTIVITY | 2023 | <https://api.insee.fr/melodi/file/DS_RP_TD_EMPLOI_LT_PCSACTIVITY_COMP_2023/PARQUET> | `data/raw/emp/2023/` |
| EMP EMPFORMWKTIME | 2023 | <https://api.insee.fr/melodi/file/DS_RP_TD_EMPLOI_LT_EMPFORMWKTIME_COMP_2023/PARQUET> | `data/raw/emp/2023/` |
| EMP new dimension code passage | 2023 | <https://www.insee.fr/fr/statistiques/fichier/9004561/Table_passage_rp_emploi.xlsx> | `data/raw/emp/2023/` |
| MOBPRO flows | 2021 | <https://www.insee.fr/fr/statistiques/fichier/8205896/RP2021_mobpro.parquet> | `data/raw/mobpro/2021/` |
| MOBPRO dictionary | 2021 | <https://www.insee.fr/fr/statistiques/fichier/8205896/varmod_mobpro_2021.csv> | `data/raw/mobpro/2021/` |
| MOBPRO flows | 2023 | <https://www.insee.fr/fr/statistiques/fichier/9004795/RP2023_mobpro.parquet> | `data/raw/mobpro/2023/` |
| MOBPRO dictionary | 2023 | <https://www.insee.fr/fr/statistiques/fichier/9004795/varmod_mobpro_2023.csv> | `data/raw/mobpro/2023/` |
| BPE equipment | 2025 | <https://www.insee.fr/fr/statistiques/fichier/8217525/BPE25.parquet> | `data/raw/bpe/2025/` |
| BPE dictionary | 2025 | <https://www.insee.fr/fr/metadonnees/source/fichier/BPE25_anonymisee_varmod.csv> | `data/raw/bpe/2025/` |
| BPE types | 2025 | <https://www.insee.fr/fr/metadonnees/source/fichier/TYPEQU_2025.csv> | `data/raw/bpe/2025/` |
| COG communes to EPCI | 2026 | <https://www.insee.fr/fr/statistiques/fichier/2510634/epci_au_01-01-2026.zip> | `data/raw/cog/2026/` |
| COG all commune zonings | 2026 | <https://www.insee.fr/fr/statistiques/fichier/7671844/table-appartenance-geo-communes-2026.zip> | `data/raw/cog/2026/` |
| COG passage since 2003 | 2003–2026 | <https://www.insee.fr/fr/statistiques/fichier/7671867/table_passage_geo2003_geo2026.zip> | `data/raw/cog/passage/` |
| COG annual passage | 2026 | <https://www.insee.fr/fr/statistiques/fichier/7671867/table_passage_annuelle_2026.zip> | `data/raw/cog/passage/` |
| Commune contours, 5 m | 2021 | <https://etalab-datasets.geo.data.gouv.fr/2021/geojson/communes-5m.geojson.gz> | `data/raw/contours/2021/` |
| Commune contours, 5 m | 2023 | <https://etalab-datasets.geo.data.gouv.fr/2023/geojson/communes-5m.geojson.gz> | `data/raw/contours/2023/` |
| Commune contours, 5 m | 2026 | <https://etalab-datasets.geo.data.gouv.fr/2026/geojson/communes-5m.geojson.gz> | `data/raw/contours/2026/` |
| Géovélo earliest clean export | 2022-07-18 | <https://www.data.gouv.fr/api/1/datasets/r/97527ef1-8db5-42cf-a644-69db6d338d00> | `data/raw/geovelo/2022-07/` |
| Géovélo export | 2024-01-01 | <https://www.data.gouv.fr/api/1/datasets/r/95239ec5-ede2-451b-b5e2-5fe147909bac> | `data/raw/geovelo/2024-01/` |
| EMP2019 CSV data | 2018–2019 | <https://www.statistiques.developpement-durable.gouv.fr/media/5052/download> | `data/raw/emp2019/` |
| EMP2019 XLSX dictionary | 2018–2019 | <https://www.statistiques.developpement-durable.gouv.fr/media/5051/download> | `data/raw/emp2019/` |
| EMP2019 PDF categories | 2018–2019 | <https://www.statistiques.developpement-durable.gouv.fr/media/5049/download> | `data/raw/emp2019/` |
| EMP2019 PDF documentation | 2018–2019 | <https://www.statistiques.developpement-durable.gouv.fr/media/5050/download> | `data/raw/emp2019/` |
| CARS commune car ownership | 2022 | <https://static.data.gouv.fr/resources/part-des-menages-selon-le-nombre-de-voiture-a-disposition/20260414-111618/part-menages-equipement-voit-com.csv> | `data/raw/cars/2022/` |
| CARS field descriptions | 2022 | <https://static.data.gouv.fr/resources/part-des-menages-selon-le-nombre-de-voiture-a-disposition/20260414-111610/part-menages-equipement-voit-description-champs.csv> | `data/raw/cars/2022/` |
| NUTS region polygons, EPSG:3035 | 2024 | <https://gisco-services.ec.europa.eu/distribution/v2/nuts/gpkg/NUTS_RG_01M_2024_3035.gpkg> | `data/raw/nuts/2024/` |
| Eurostat NUTS3 employment, all years | download date | <https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/nama_10r_3empers?format=TSV&compressed=true> | `data/raw/eurostat/nama_10r_3empers/{download date}/` |
| Eurostat national employment, all years | download date | <https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/lfsi_emp_a?format=TSV&compressed=true> | `data/raw/eurostat/lfsi_emp_a/{download date}/` |

The 2021 census edition is dated **2024-12-31**; the 2023 edition is dated
**2026-09-03** and INSEE replaces its Parquet URL at each update. Géovélo July
2022 is a proxy for 2021, not a true 2021 snapshot. Eurostat revisions mean the
actual acquisition date, not observation years, is the vintage; the CLI updates
the directory and resets stale integrity metadata when that date changes.
The pilot's later processing area is the Gironde polygon plus 50 km, not an
acquisition bounding box.
