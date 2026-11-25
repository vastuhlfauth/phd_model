# BD ALTI 25 m elevation grids

- **Source:** IGN BD ALTI, manifest source `bdalti`.
- **Vintage(s):** One configured departmental edition per metropolitan
  department; the manifest currently contains 96 archives.
- **Local path:** `data/raw/bdalti/25m/*.7z`; original archives are retained.
- **Files:** 7z archives contain metadata and tiled ESRI ASCII Grid (`.asc`)
  rasters. Tile names identify `25M`, `LAMB93` and the `IGN69` vertical datum.
- **CRS:** Lambert-93, EPSG:2154; elevations are metres referenced to IGN69.
- **Coverage:** The unpack command selects departments whose commune contours
  intersect the buffered pilot area and extracts only `.asc` tiles, flattened
  to `data/interim/bdalti/D###/<tile>.asc`.
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
- Windows `tar` lacks `-s`; tile-only file lists and `--strip-components`
  remove archive nesting, using short staging folders under the output root.
  Duplicate tile basenames (including case-only differences) are rejected.
- Every listed tile is checked by basename before promotion and on reuse.
  Failed staging folders are removed with Windows extended-length paths.
  Old nested or stale department outputs must be moved aside before retrying;
  the unpacker does not overwrite them.
