# Eurostat census grid

- **Source:** Eurostat Census Grid 2021, version 3.0. The supplied `read.me`
  states the EU reuse notice and data definitions.
- **Vintage:** 2021 census.
- **Local path:** `data/raw/eurostat_grid/Eurostat_Census-GRID_2021_V3/`.
- **Files:** `ESTAT_Census_2021_V3.parquet` (Parquet, 76,307,745 bytes,
  4,595,932 rows); `ESTAT_Census_2021_V3.csv` (CSV, 339,625,996 bytes);
  `ESTAT_Census_2021_V3.gpkg` (GeoPackage, 1,302,953,984 bytes);
  `ESTAT_Census_2021_V3.tiff` (GeoTIFF, 32,327,795 bytes);
  `ESTAT_Census_2021_LAND_SURFACE_V3.tiff` (GeoTIFF, 5,977,689 bytes);
  `read.me` (5,428 bytes); `ESTAT_Census_2021_country.csv.zip`
  (257,389,035 bytes); and `ESTAT_Census_2021_V3_SDMX_Metadata.zip`
  (343,891 bytes).
- **Archive contents:** the country CSV ZIP contains
  `CENSUS_GRID_N_<CC>_2021.csv` for AT, BE, BG, CH, CY, CZ, DE, DK, EE, EL,
  ES, FI, FR, HR, HU, IE, IT, LI, LT, LU, LV, MT, NL, NO, PL, PT, RO, SE,
  SI and SK. The metadata ZIP contains one
  `CENSUS_INS21ES_A_<CC>_2021_0000.sdmx.xml` per same country code, plus its
  `read.me`.
- **CRS:** ETRS89-LAEA, EPSG:3035. The cell identifiers encode the 1 km
  resolution and grid corner.
- **Keys and joins:** `GRD_ID` has the same
  `CRS3035RES1000mN{northing}E{easting}` form used by
  [`inspire_code`](../../packages/common/grid.py). All 4,595,919 grid-coded
  rows round-trip at 1 km with no alignment errors. The other 13 IDs are
  unallocated records: `BE_unallocated`, `BG_unallocated`, `DE_unallocated`,
  `DK_unallocated`, `EL_unallocated`, `FI_unallocated`, `FR_unallocated`,
  `IT_unallocated`, `LU_unallocated`, `LV_unallocated`, `NO_unallocated`,
  `SE_unallocated` and `SI_unallocated`.

## Columns: Parquet table

| Column | Type | Unit / meaning |
|---|---|---|
| `GRD_ID` | `VARCHAR` | Grid-cell identifier |
| `T` | `BIGINT` | Total population |
| `M`, `F` | `BIGINT` | Male and female population |
| `Y_LT15`, `Y_1564`, `Y_GE65` | `BIGINT` | Population aged under 15, 15–64, and 65+ |
| `EMP` | `BIGINT` | Employed population |
| `NAT`, `EU_OTH`, `OTH` | `BIGINT` | Place of birth: reporting country, another EU member state, elsewhere |
| `SAME`, `CHG_IN`, `CHG_OUT` | `BIGINT` | Usual residence unchanged, moved within reporting country, moved from outside reporting country, respectively, compared with 2020 |
| `LAND_SURFACE` | `DOUBLE` | Land area within cell, km², from 0 to 1 |
| `POPULATED` | `BIGINT` | 1 if populated, 0 otherwise |
| `CNTR_ID` | `VARCHAR` | Reporting-country codes associated with the cell |

The special integer values `-8888` (confidentiality) and `-9999` (other
unavailable value) are documented by Eurostat. The parquet table has the
same variables as the supplied CSV and GeoPackage.

## Department-33 population

The 2021 200 m Filosofi file links cells to intersecting commune codes and
to their `idcar_1km`. Joining the distinct 1 km IDs from the 55,040
department-33-linked Filosofi 200 m rows to `GRD_ID` matches 6,992 Eurostat
cells. Their whole-cell `T` total is 1,656,946; `CHG_IN` totals 195,730 and
`CHG_OUT` totals 7,814. No matched `T` value is negative or unavailable.
These are whole 1 km cell totals, not population clipped to the department.
The join covers cells represented by a 200 m Filosofi row; a direct boundary
overlay was not completed within the task's one-minute query limit, so cells
with no such row are not certified as included.

## Sample

First 20 grid-coded rows returned by DuckDB:

| `GRD_ID` | `T` | `CHG_IN` | `CHG_OUT` | `CNTR_ID` |
|---|---:|---:|---:|---|
| `CRS3035RES1000mN2683000E4285000` | 0 | 0 | 0 | AT-CH-LI |
| `CRS3035RES1000mN2684000E4285000` | 25 | 0 | 0 | AT-CH-LI |
| `CRS3035RES1000mN2682000E4286000` | 0 | 0 | 0 | AT-LI |
| `CRS3035RES1000mN2683000E4286000` | 116 | 7 | 0 | AT-LI |
| `CRS3035RES1000mN2684000E4286000` | 185 | 16 | 4 | AT-CH |
| `CRS3035RES1000mN2685000E4286000` | 439 | 15 | 3 | AT-CH |
| `CRS3035RES1000mN2673000E4287000` | 0 | 0 | 0 | AT-LI |
| `CRS3035RES1000mN2678000E4287000` | 157 | 7 | 2 | AT-LI |
| `CRS3035RES1000mN2679000E4287000` | 664 | 28 | 5 | AT-LI |
| `CRS3035RES1000mN2680000E4287000` | 182 | 12 | 0 | AT-LI |
| `CRS3035RES1000mN2681000E4287000` | 49 | 1 | 0 | AT-LI |
| `CRS3035RES1000mN2682000E4287000` | 570 | 35 | 16 | AT-LI |
| `CRS3035RES1000mN2685000E4287000` | 0 | 0 | 0 | AT-CH |
| `CRS3035RES1000mN2686000E4287000` | 0 | 0 | 0 | AT-CH |
| `CRS3035RES1000mN2687000E4287000` | 0 | 0 | 0 | AT-CH |
| `CRS3035RES1000mN2709000E4287000` | 13 | 4 | 0 | AT-CH |
| `CRS3035RES1000mN2710000E4287000` | 0 | 0 | 0 | AT-CH |
| `CRS3035RES1000mN2711000E4287000` | 0 | 0 | 0 | AT-CH |
| `CRS3035RES1000mN2712000E4287000` | 0 | 0 | 0 | AT-CH |
| `CRS3035RES1000mN2713000E4287000` | 0 | 0 | 0 | AT-CH |
