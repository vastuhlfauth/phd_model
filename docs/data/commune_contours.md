# Commune contours

- **Source:** Etalab, configured as `contours-2021` in
  `config/sources.yaml`.
- **Vintage:** 2021 commune boundaries.
- **Local path:** `data/raw/contours/2021/communes-5m.geojson.gz`.
- **Files:** gzip-compressed GeoJSON; the raw file remains read-only.
- **CRS:** WGS 84 longitude/latitude, transformed to EPSG:3035 before
  buffering or intersecting.
- **Keys and joins:** `departement` selects pilot communes and identifies
  departments intersecting the buffered pilot area.

## Fields used

| Field | Type | Unit | Meaning |
|---|---|---|---|
| `code` | string | none | Commune code, used to identify report rows |
| `nom` | string | none | Commune name, used to label report rows |
| `departement` | string | none | Department code on each commune feature |
| `geom` | geometry | CRS coordinates | Commune polygon read by DuckDB `ST_Read` |

## Quirks

- The pilot shape is the union of communes in `config/pilot.yaml`'s department,
  buffered by its configured halo in EPSG:3035.
- Department selection tests every commune polygon against that same buffered
  shape; it does not rely on an adjacency list.
