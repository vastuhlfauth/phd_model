#!/usr/bin/env python3
"""Extract park centroids and sea-beach centroids from OSM PBF.

Must run under WSL Python (pyosmium is not available on Windows Python 3.14).

Usage (from WSL):
  python3 /mnt/c/codes/simple_mobility_model/codes/00_extract_parks_coast.py

  # Force re-extraction (delete caches):
  python3 /mnt/c/codes/simple_mobility_model/codes/00_extract_parks_coast.py --reextract

  # Only coast / only parks:
  python3 .../00_extract_parks_coast.py --only coast
  python3 .../00_extract_parks_coast.py --only parks

Writes:
  outputs/12_car_nature/park_points.gpkg
      boundary=national_park or boundary=protected_area centroids, area >= PARK_MIN_AREA_KM2

  outputs/12_car_nature/urban_park_points.gpkg
      leisure=park centroids (urban parks), area >= URBAN_PARK_MIN_AREA_KM2

  outputs/12_car_nature/coast_points.gpkg
      natural=beach centroids that lie within COAST_PROXIMITY_M metres of a
      natural=coastline way — i.e. sea/ocean beaches only.
      Inland lake/river beaches (e.g. "Cergy Plage") are excluded.

Sea-beach filtering logic
─────────────────────────
1. Extract all natural=coastline way geometries from the PBF(s) → list of LineStrings.
2. Build a single unified geometry (unary_union) and buffer by COAST_PROXIMITY_M in
   EPSG:2154 (Lambert-93, metric).
3. Load existing natural=beach centroids from
   outputs/00_data_import_preparation/osm_area_points.gpkg.
4. Keep only beaches whose centroid falls inside the buffer.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import osmium
from shapely import wkb as shapely_wkb

if sys.platform == "win32":
    ROOT = Path("C:/codes/simple_mobility_model")
else:
    ROOT = Path("/mnt/c/codes/simple_mobility_model")
DEFAULT_OSM_PBF = ROOT / "data" / "france-220101.osm.pbf"
NEIGHBOR_PBF_DIR = ROOT / "data" / "osm"
OUTPUT_DIR = ROOT / "outputs" / "12_car_nature"
OSM_AREA_POINTS = ROOT / "outputs" / "00_data_import_preparation" / "osm_area_points.gpkg"

PARK_CACHE = OUTPUT_DIR / "park_points.gpkg"
URBAN_PARK_CACHE = OUTPUT_DIR / "urban_park_points.gpkg"
COAST_CACHE = OUTPUT_DIR / "coast_points.gpkg"

PARK_MIN_AREA_KM2 = 1.0
URBAN_PARK_MIN_AREA_KM2 = 0.0   # no minimum — urban parks are typically small (< 1 km²)
COAST_PROXIMITY_M = 2000.0   # beaches within 2 km of a coastline way are kept

WGS84_CRS = "EPSG:4326"
LAMBERT93_CRS = "EPSG:2154"


# ---------------------------------------------------------------------------
# OSM handlers
# ---------------------------------------------------------------------------

class _ParkHandler(osmium.SimpleHandler):
    """Extract boundary=national_park and boundary=protected_area as polygons."""

    def __init__(self) -> None:
        super().__init__()
        self.parks: list[dict] = []
        self.wkbfab = osmium.geom.WKBFactory()

    def area(self, a) -> None:
        btype = a.tags.get("boundary")
        if btype not in ("national_park", "protected_area"):
            return
        try:
            wkb = self.wkbfab.create_multipolygon(a)
            geom = shapely_wkb.loads(wkb, hex=True)
        except Exception:
            return
        self.parks.append({
            "osm_id": a.orig_id() if hasattr(a, "orig_id") else a.id,
            "name": a.tags.get("name", ""),
            "boundary": btype,
            "protect_class": a.tags.get("protect_class", ""),
            "geometry": geom,
        })


_URBAN_PARK_BOUNDARY_TYPES = {"protected_area", "national_park"}


class _UrbanParkHandler(osmium.SimpleHandler):
    """Extract leisure=park and boundary=protected_area/national_park polygons."""

    def __init__(self) -> None:
        super().__init__()
        self.parks: list[dict] = []
        self.wkbfab = osmium.geom.WKBFactory()

    def area(self, a) -> None:
        is_leisure_park = a.tags.get("leisure") == "park"
        is_protected = a.tags.get("boundary") in _URBAN_PARK_BOUNDARY_TYPES
        if not (is_leisure_park or is_protected):
            return
        try:
            wkb = self.wkbfab.create_multipolygon(a)
            geom = shapely_wkb.loads(wkb, hex=True)
        except Exception:
            return
        self.parks.append({
            "osm_id": a.orig_id() if hasattr(a, "orig_id") else a.id,
            "name": a.tags.get("name", ""),
            "leisure": a.tags.get("leisure", ""),
            "boundary": a.tags.get("boundary", ""),
            "geometry": geom,
        })


class _CoastlineHandler(osmium.SimpleHandler):
    """Extract natural=coastline way geometries as LineStrings."""

    def __init__(self) -> None:
        super().__init__()
        self.segments: list = []
        self.wkbfab = osmium.geom.WKBFactory()

    def way(self, w) -> None:
        if w.tags.get("natural") != "coastline":
            return
        try:
            wkb = self.wkbfab.create_linestring(w)
            geom = shapely_wkb.loads(wkb, hex=True)
            self.segments.append(geom)
        except Exception:
            return


# ---------------------------------------------------------------------------
# Parks
# ---------------------------------------------------------------------------

def _extract_parks(pbf_files: list[Path]) -> gpd.GeoDataFrame:
    import time

    all_parks: list[dict] = []
    for pbf in pbf_files:
        if not pbf.exists():
            print(f"  [SKIP] {pbf}")
            continue
        t0 = time.time()
        h = _ParkHandler()
        h.apply_file(str(pbf), locations=True)
        print(f"  {pbf.name}: {len(h.parks):,} raw areas ({time.time()-t0:.1f}s)")
        all_parks.extend(h.parks)

    if not all_parks:
        print("  No parks found.")
        return gpd.GeoDataFrame(
            columns=["osm_id", "name", "boundary", "protect_class", "lon", "lat", "geometry"],
            crs=WGS84_CRS,
        )

    gdf = gpd.GeoDataFrame(all_parks, crs=WGS84_CRS)

    # Dedup
    before = len(gdf)
    gdf = gdf.drop_duplicates(subset="osm_id", keep="first").copy()
    print(f"  Dedup: {before:,} → {len(gdf):,}")

    # Area filter
    gdf_l93 = gdf.to_crs(LAMBERT93_CRS)
    area_km2 = gdf_l93.geometry.area / 1e6
    mask = area_km2 >= PARK_MIN_AREA_KM2
    gdf = gdf[mask].copy()
    print(f"  Area >= {PARK_MIN_AREA_KM2} km²: {mask.sum():,} parks kept")

    # Centroids (in Lambert-93, back to WGS84)
    gdf_l93 = gdf.to_crs(LAMBERT93_CRS).copy()
    gdf_l93["geometry"] = gdf_l93.geometry.centroid
    gdf = gdf_l93.to_crs(WGS84_CRS)
    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y

    return gdf


def _extract_urban_parks(pbf_files: list[Path], min_area_km2: float) -> gpd.GeoDataFrame:
    import time

    all_parks: list[dict] = []
    for pbf in pbf_files:
        if not pbf.exists():
            print(f"  [SKIP] {pbf}")
            continue
        t0 = time.time()
        h = _UrbanParkHandler()
        h.apply_file(str(pbf), locations=True)
        print(f"  {pbf.name}: {len(h.parks):,} raw urban park areas ({time.time()-t0:.1f}s)")
        all_parks.extend(h.parks)

    if not all_parks:
        print("  No urban parks found.")
        return gpd.GeoDataFrame(
            columns=["osm_id", "name", "leisure", "boundary", "lon", "lat", "geometry"],
            crs=WGS84_CRS,
        )

    gdf = gpd.GeoDataFrame(all_parks, crs=WGS84_CRS)

    # Dedup
    before = len(gdf)
    gdf = gdf.drop_duplicates(subset="osm_id", keep="first").copy()
    lp = (gdf["leisure"] == "park").sum()
    bp = gdf["boundary"].isin(_URBAN_PARK_BOUNDARY_TYPES).sum()
    print(f"  Dedup: {before:,} → {len(gdf):,}  (leisure=park: {lp:,}, boundary protected/national: {bp:,})")

    # Optional area filter
    if min_area_km2 > 0:
        gdf_l93 = gdf.to_crs(LAMBERT93_CRS)
        area_km2 = gdf_l93.geometry.area / 1e6
        mask = area_km2 >= min_area_km2
        gdf = gdf[mask].copy()
        print(f"  Area >= {min_area_km2} km²: {mask.sum():,} urban parks kept")

    # Centroids (in Lambert-93, back to WGS84)
    gdf_l93 = gdf.to_crs(LAMBERT93_CRS).copy()
    gdf_l93["geometry"] = gdf_l93.geometry.centroid
    gdf = gdf_l93.to_crs(WGS84_CRS)
    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y

    return gdf


# ---------------------------------------------------------------------------
# Coast (sea beaches only)
# ---------------------------------------------------------------------------

def _extract_coastline_segments(pbf_files: list[Path]) -> list:
    """Return list of shapely LineString for natural=coastline ways."""
    import time

    all_segments: list = []
    for pbf in pbf_files:
        if not pbf.exists():
            continue
        t0 = time.time()
        h = _CoastlineHandler()
        h.apply_file(str(pbf), locations=True)
        print(f"  {pbf.name}: {len(h.segments):,} coastline segments ({time.time()-t0:.1f}s)")
        all_segments.extend(h.segments)
    return all_segments


def _filter_sea_beaches(
    beach_gdf: gpd.GeoDataFrame,
    pbf_files: list[Path],
    proximity_m: float,
) -> gpd.GeoDataFrame:
    """Keep only beaches within *proximity_m* metres of a natural=coastline way.

    Uses sjoin_nearest to avoid building a massive unary_union + buffer polygon.
    """
    print(f"Extracting natural=coastline from {len(pbf_files)} PBF(s)...")
    segments = _extract_coastline_segments(pbf_files)

    if not segments:
        print("  [WARN] No coastline segments found — returning all beaches unfiltered")
        return beach_gdf

    print(f"  Building coastline GeoDataFrame from {len(segments):,} segments...")
    coast_gdf = gpd.GeoDataFrame(geometry=segments, crs=WGS84_CRS)

    # Project to Lambert-93 for metric distance check
    coast_l93 = coast_gdf.to_crs(LAMBERT93_CRS)
    beach_l93 = beach_gdf[["geometry"]].to_crs(LAMBERT93_CRS).copy()
    beach_l93["_idx"] = range(len(beach_l93))

    print(f"  Finding beaches within {proximity_m:.0f} m of coastline (sjoin_nearest)...")
    matched = gpd.sjoin_nearest(
        beach_l93,
        coast_l93,
        how="left",
        max_distance=proximity_m,
        distance_col="_dist",
    )
    # Keep original rows that had a match (distance is not NaN)
    matched_idx = matched.loc[matched["_dist"].notna(), "_idx"].unique()
    result = beach_gdf.iloc[matched_idx].copy()
    print(
        f"  Beaches within {proximity_m:.0f} m of coastline: "
        f"{len(result):,} / {len(beach_gdf):,} kept"
    )
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _collect_pbf_files() -> list[Path]:
    pbf_files: list[Path] = []
    if DEFAULT_OSM_PBF.exists():
        pbf_files.append(DEFAULT_OSM_PBF)
    if NEIGHBOR_PBF_DIR.exists():
        pbf_files.extend(sorted(NEIGHBOR_PBF_DIR.glob("*.osm.pbf")))
    return pbf_files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract park and sea-beach centroids from OSM PBF (WSL only)"
    )
    parser.add_argument("--only", choices=["parks", "urban-parks", "coast", "all"], default="all",
                        help="Which extraction to run (default: all)")
    parser.add_argument("--reextract", action="store_true", default=False,
                        help="Delete the cache for the selected --only type and re-extract")
    parser.add_argument("--park-min-area-km2", type=float, default=PARK_MIN_AREA_KM2)
    parser.add_argument("--urban-park-min-area-km2", type=float, default=URBAN_PARK_MIN_AREA_KM2,
                        help="Min area in km² for urban parks (default: %(default)s = no filter)")
    parser.add_argument("--coast-proximity-m", type=float, default=COAST_PROXIMITY_M,
                        help="Max distance (m) from coastline to keep a beach (default: 2000)")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pbf_files = _collect_pbf_files()
    if not pbf_files:
        print(
            f"[ERROR] No PBF files found at {DEFAULT_OSM_PBF} or in {NEIGHBOR_PBF_DIR}",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"PBF files: {[p.name for p in pbf_files]}")

    # ── Parks ─────────────────────────────────────────────────────────────
    if args.only in ("parks", "all"):
        if PARK_CACHE.exists() and not args.reextract:
            print(f"\nPark cache exists, skipping: {PARK_CACHE}")
            print("  Pass --reextract to force re-extraction.")
        else:
            if args.reextract and PARK_CACHE.exists():
                PARK_CACHE.unlink()
                print(f"\nDeleted old park cache: {PARK_CACHE}")
            print("\nExtracting parks from PBF...")
            park_gdf = _extract_parks(pbf_files)
            if len(park_gdf):
                park_gdf.to_file(PARK_CACHE, driver="GPKG")
                print(f"  Saved {len(park_gdf):,} park centroids → {PARK_CACHE}")

    # ── Urban parks ───────────────────────────────────────────────────────
    if args.only in ("urban-parks", "all"):
        if URBAN_PARK_CACHE.exists() and not args.reextract:
            print(f"\nUrban park cache exists, skipping: {URBAN_PARK_CACHE}")
            print("  Pass --reextract to force re-extraction.")
        else:
            if args.reextract and URBAN_PARK_CACHE.exists():
                URBAN_PARK_CACHE.unlink()
                print(f"\nDeleted old urban park cache: {URBAN_PARK_CACHE}")
            print("\nExtracting urban parks (leisure=park + boundary=protected_area/national_park) from PBF...")
            urban_park_gdf = _extract_urban_parks(pbf_files, args.urban_park_min_area_km2)
            if len(urban_park_gdf):
                urban_park_gdf.to_file(URBAN_PARK_CACHE, driver="GPKG")
                print(f"  Saved {len(urban_park_gdf):,} urban park centroids → {URBAN_PARK_CACHE}")

    # ── Sea beaches ───────────────────────────────────────────────────────
    if args.only in ("coast", "all"):
        if COAST_CACHE.exists() and not args.reextract:
            print(f"\nCoast cache exists, skipping: {COAST_CACHE}")
            print("  Pass --reextract to force re-extraction.")
        else:
            if args.reextract and COAST_CACHE.exists():
                COAST_CACHE.unlink()
                print(f"\nDeleted old coast cache: {COAST_CACHE}")

            if not OSM_AREA_POINTS.exists():
                print(
                    f"[ERROR] Beach source not found: {OSM_AREA_POINTS}\n"
                    "Run 00_data_import_preparation.py first.",
                    file=sys.stderr,
                )
                sys.exit(1)

            print(f"\nLoading beach centroids from: {OSM_AREA_POINTS}")
            osm_pts = gpd.read_file(str(OSM_AREA_POINTS))
            beach_gdf = osm_pts[osm_pts["osm_value"] == "beach"].copy()
            if "lon" not in beach_gdf.columns:
                beach_gdf["lon"] = beach_gdf.geometry.x
                beach_gdf["lat"] = beach_gdf.geometry.y
            print(f"  {len(beach_gdf):,} total natural=beach centroids")

            sea_beaches = _filter_sea_beaches(beach_gdf, pbf_files, args.coast_proximity_m)

            if len(sea_beaches):
                sea_beaches.to_file(COAST_CACHE, driver="GPKG")
                print(f"  Saved {len(sea_beaches):,} sea-beach centroids → {COAST_CACHE}")
            else:
                print("  [WARN] No sea beaches remained after filtering.")

    print("\nDone.")


if __name__ == "__main__":
    main()
