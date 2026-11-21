# BD ALTI 25 m elevation grids

- **Source:** IGN BD ALTI, manifest source `bdalti`.
- **Vintage(s):** One configured departmental edition per metropolitan
  department; the manifest currently contains 96 archives.
- **Local path:** `data/raw/bdalti/25m/*.7z`; original archives are retained.
- **Files:** 7z archives contain metadata and tiled ESRI ASCII Grid (`.asc`)
  rasters. Tile names identify `25M`, `LAMB93` and the `IGN69` vertical datum.
- **CRS:** Lambert-93, EPSG:2154; elevations are metres referenced to IGN69.
- **Coverage:** The unpack command selects departments whose commune contours
  intersect the buffered pilot area and writes each archive under
  `data/interim/bdalti/D###/`.
- **Keys and joins:** OSM node `x`, `y` values are transformed from EPSG:3035
  to EPSG:2154 for sampling; edge profiles join to directed edges by `edge_key`.

## Raster header

The sampler reads the six ESRI ASCII Grid header lines: `ncols`, `nrows`,
`xllcorner` or `xllcenter`, `yllcorner` or `yllcenter`, `cellsize`, and
`NODATA_value`. It bilinearly interpolates from cell centers and reads only
requested raster rows. A no-data neighbour with nonzero interpolation weight
leaves the node sample null.

## Quirks

- Department archives have separate editions; the configured manifest entry
  is authoritative.
- Tile edges are interpolated across aligned neighboring grids. Unaligned
  grids are rejected rather than silently shifted.
- No-data and nodes outside all tile footprints are counted separately in the
  elevation report.
