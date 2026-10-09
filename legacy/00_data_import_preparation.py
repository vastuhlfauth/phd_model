#!/usr/bin/env python3
"""Phase 1: Data Import & Preparation.

What this script does:
1. Imports BPE points (opportunities/facilities) from INSEE CSV, filtered
   to a curated set of equipment types.
2. Imports Filosofi grid polygons and converts them to centroid points.
3. Applies boundary clipping and writes standardized WGS84 outputs.

Note: GTFS/PT preprocessing is handled separately by
`codes/00_prepare_public_transport.py`.

Default study area:
- France-wide with neighboring NUTS3 regions (--france-wide --with-neighbors
  --include-cross-border).

Primary outputs:
- `outputs/00_data_import_preparation/bpe_points.gpkg`
- `outputs/00_data_import_preparation/filosofi_grid_points.gpkg`
- `outputs/00_data_import_preparation/data_summary.txt`

Run examples:
- `python codes/00_data_import_preparation.py`
  (France-wide with cross-border neighbors)
- `python codes/00_data_import_preparation.py --no-france-wide --boundary-nuts3 FRI12`
  (single NUTS3 region)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import time

import geopandas as gpd
import numpy as np
import osmium
import pandas as pd
from pyproj import Transformer
from shapely import within
from shapely import wkb as shapely_wkb


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "outputs" / "00_data_import_preparation"

# OSM PBF paths
DEFAULT_OSM_PBF = DATA_DIR / "france-220101.osm.pbf"
NEIGHBOR_PBF_DIR = DATA_DIR / "osm"

# Default paths
DEFAULT_BPE_CSV = DATA_DIR / "INSEE_bpe21-ensemble-xy-csv" / "bpe21_ensemble_xy.csv"
DEFAULT_FILOSOFI_SHP = DATA_DIR / "INSEE_Filosofi2019_carreaux_200m_shp" / "Filosofi2019_carreaux_200m_shp"
DEFAULT_GTFS_DIRS = [DATA_DIR / "GTFS"]  # GTFS root; subfolders are NUTS2 region names
DEFAULT_BOUNDARY = DATA_DIR / "bordeaux_metropole.geojson"
DEFAULT_NUTS_GPKG = DATA_DIR / "NUTS_RG_20M_2021_3035.gpkg"
DEFAULT_NUTS_LAYER = "NUTS_RG_20M_2021_3035.gpkg"
DEFAULT_BOUNDARY_NUTS3 = ""  # empty = no single-NUTS3 default; use --france-wide

# Coordinate systems
WGS84_CRS = "EPSG:4326" 
LAMBERT93_CRS = "EPSG:2154"

# ---------------------------------------------------------------------------
# BPE equipment type filter
# ---------------------------------------------------------------------------
# Exact TYPEQU codes to keep
BPE_EXACT_CODES = {
    # Services aux particuliers
    "A101",  # Poste
    "A104",  # Banque / Caisse d'epargne (agence)
    "A122",  # Pole emploi
    "A124",  # Maison de l'emploi
    "A128",  # France Services
    "A129",  # Maison de services au public
    "A130",  # Point information médiation multi-services (PIMMS)
    "A203",  # Banque
    "A205",  # Assurance
    "A206",  # Agence immobiliere
    "A207",  # Pompes funèbres
    "A208",  # Agence de voyages
    "A304",  # Vétérinaire
    "A404",  # Coiffeur
    "A405",  # Institut de beauté
    "A501",  # Restaurant
    "A504",  # Boulangerie
    "A505",  # Boucherie
    "A506",  # Librairie / papeterie
    "A507",  # Fleuriste
    # Achat - Supermarches / hypermarchés
    "B101", "B102", "B103",
    # Achat - Commerces alimentaires
    "B201", "B202", "B203", "B204", "B206",
    # Achat - Autres commerces
    "B301", "B302", "B303", "B304", "B305",
    "B307", "B309", "B310", "B312", "B313", "B316",
    # Sante - autres
    "D302",  # Pharmacie
    "D307",  # Laboratoire d'analyses médicales
    "D502",  # Crèche / halte-garderie
    "D701",  # Ambulance
    # Loisirs - Sportif / Ski
    "F101",  # Stade
    "F107",  # Piscine couverte
    "F109",  # Piscine plein air
    "F111",  # Salle de remise en forme (fitness)
    "F116",  # Terrain de tennis
    "F117",  # Terrain de golf
    "F121",  # Patinoire
    # Loisirs - Culturel
    "F201",  # Cinéma
    "F203",  # Musée
    "F307",  # Bibliothèque / médiathèque
    "F312",  # Théâtre
    "F315",  # Salle de concert / salle des fêtes
    # Commerce - Jardinerie / Auto
    "G104",  # Station-service
}

# TYPEQU prefixes to keep (startswith match)
BPE_PREFIX_CODES = (
    "C1",  # Education - First degree
    "C2",  # Education - Second degree, first cycle
    "C3",  # Education - Second degree, second cycle
    "C4",  # Education - Superior non-university
    "C5",  # Education - University
    "D1",  # Sante - Hospitals, clinics
    "D2",  # Sante - Médecins, dentistes, paramédicaux
    "D4",  # Sante - Maisons de retraite / EHPAD
    "D6",  # Sante - Handicap / aide sociale
)


def _ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def _load_boundary(boundary_path: Path, to_crs: str) -> object:
    """Load and process boundary geometry."""
    print(f"Loading boundary: {boundary_path}")
    boundary = gpd.read_file(boundary_path)
    if len(boundary) == 0:
        raise ValueError(f"Boundary file is empty: {boundary_path}")
    
    # GeoPandas 1.1+ supports union_all(); unary_union is deprecated
    if hasattr(boundary.geometry, "union_all"):
        boundary_geom = boundary.geometry.union_all()
    else:
        boundary_geom = boundary.geometry.unary_union
    
    boundary_gdf = gpd.GeoDataFrame(geometry=[boundary_geom], crs=boundary.crs)
    boundary_gdf = boundary_gdf.to_crs(to_crs)
    return boundary_gdf.geometry.iloc[0]


def _build_boundary_from_nuts3(
    nuts_path: Path,
    nuts_layer: str,
    nuts3_id: str,
    output_dir: Path,
) -> Path:
    """Extract a NUTS3 polygon as a GeoJSON boundary file."""
    if not nuts_path.exists():
        raise FileNotFoundError(f"NUTS file not found: {nuts_path}")

    nuts = gpd.read_file(nuts_path, layer=nuts_layer)
    required_cols = {"NUTS_ID", "LEVL_CODE"}
    missing_cols = required_cols - set(nuts.columns)
    if missing_cols:
        raise ValueError(f"NUTS layer missing required columns: {sorted(missing_cols)}")

    target = nuts[(nuts["NUTS_ID"] == nuts3_id) & (nuts["LEVL_CODE"] == 3)].copy()
    if target.empty:
        raise ValueError(f"NUTS3 code not found in layer: {nuts3_id}")

    _ensure_dir(output_dir)
    out_path = output_dir / f"boundary_nuts3_{nuts3_id}.geojson"
    target.to_crs(WGS84_CRS)[["NUTS_ID", "geometry"]].to_file(out_path, driver="GeoJSON")
    print(f"Built NUTS3 boundary file: {out_path}")
    return out_path


def _find_neighboring_nuts3(
    nuts_path: Path,
    nuts_layer: str,
    nuts3_id: str,
    include_cross_border: bool = True,
) -> list[str]:
    """Find NUTS3 regions that share a border with the target region.
    
    Args:
        nuts_path: Path to NUTS GeoPackage
        nuts_layer: Layer name in GeoPackage
        nuts3_id: Target NUTS3 code
        include_cross_border: Include non-France NUTS3 (BE, DE, LU, CH, IT, ES)
    
    Returns:
        List of neighboring NUTS3 codes (including target)
    """
    if not nuts_path.exists():
        print(f"Warning: NUTS file not found: {nuts_path}")
        return [nuts3_id]
    
    nuts = gpd.read_file(nuts_path, layer=nuts_layer)
    nuts3_all = nuts[nuts["LEVL_CODE"] == 3].copy()
    
    # Get target geometry
    target = nuts3_all[nuts3_all["NUTS_ID"] == nuts3_id]
    if target.empty:
        print(f"Warning: NUTS3 code not found: {nuts3_id}")
        return [nuts3_id]
    
    target_geom = target.geometry.iloc[0]
    
    # Filter by country if not including cross-border
    if not include_cross_border:
        nuts3_all = nuts3_all[nuts3_all["CNTR_CODE"] == "FR"]
    else:
        # Include France + neighboring countries
        allowed_countries = ["FR", "BE", "DE", "LU", "CH", "IT", "ES"]
        nuts3_all = nuts3_all[nuts3_all["CNTR_CODE"].isin(allowed_countries)]
    
    # Find neighbors (geometries that touch or intersect)
    neighbors = []
    for _, row in nuts3_all.iterrows():
        if row["NUTS_ID"] == nuts3_id:
            neighbors.append(row["NUTS_ID"])
        elif row.geometry.touches(target_geom) or row.geometry.intersects(target_geom):
            neighbors.append(row["NUTS_ID"])
    
    print(f"Found {len(neighbors)} NUTS3 regions (target + {len(neighbors)-1} neighbors)")
    return sorted(neighbors)


def _build_boundary_with_neighbors(
    nuts_path: Path,
    nuts_layer: str,
    nuts3_id: str,
    output_dir: Path,
    include_cross_border: bool = True,
) -> tuple[Path, list[str]]:
    """Build a dissolved boundary containing target NUTS3 + all neighbors.
    
    Returns:
        Tuple of (boundary_path, list_of_nuts3_codes)
    """
    neighbors = _find_neighboring_nuts3(
        nuts_path, nuts_layer, nuts3_id, include_cross_border
    )
    
    if not nuts_path.exists():
        raise FileNotFoundError(f"NUTS file not found: {nuts_path}")
    
    nuts = gpd.read_file(nuts_path, layer=nuts_layer)
    nuts3_all = nuts[nuts["LEVL_CODE"] == 3]
    
    # Get all neighbor geometries
    neighbor_regions = nuts3_all[nuts3_all["NUTS_ID"].isin(neighbors)].copy()
    
    if neighbor_regions.empty:
        raise ValueError(f"No NUTS3 regions found for codes: {neighbors}")
    
    # Dissolve into single polygon
    dissolved = neighbor_regions.dissolve()
    dissolved = dissolved.reset_index(drop=True)
    dissolved["NUTS_IDS"] = ",".join(neighbors)
    
    _ensure_dir(output_dir)
    out_path = output_dir / f"boundary_nuts3_{nuts3_id}_with_neighbors.geojson"
    dissolved.to_crs(WGS84_CRS)[["NUTS_IDS", "geometry"]].to_file(out_path, driver="GeoJSON")
    
    print(f"Built extended NUTS3 boundary: {out_path}")
    print(f"  Includes: {', '.join(neighbors)}")
    
    # Also save neighbor list
    neighbors_csv = output_dir / f"nuts3_{nuts3_id}_neighbors.csv"
    pd.DataFrame({"nuts3_code": neighbors}).to_csv(neighbors_csv, index=False)
    
    return out_path, neighbors


def _build_france_boundary_with_neighbors(
    nuts_path: Path,
    nuts_layer: str,
    output_dir: Path,
    include_cross_border: bool = True,
) -> tuple[Path, list[str]]:
    """Build a dissolved boundary containing all French NUTS3 + neighboring countries' NUTS3.
    
    This creates a boundary covering all of France plus neighboring NUTS3 regions
    from BE, DE, LU, CH, IT, ES that touch the French border.
    
    Returns:
        Tuple of (boundary_path, list_of_nuts3_codes)
    """
    if not nuts_path.exists():
        raise FileNotFoundError(f"NUTS file not found: {nuts_path}")
    
    nuts = gpd.read_file(nuts_path, layer=nuts_layer)
    nuts3_all = nuts[nuts["LEVL_CODE"] == 3].copy()
    
    # Get all French NUTS3 regions
    france_nuts3 = nuts3_all[nuts3_all["CNTR_CODE"] == "FR"].copy()
    print(f"Found {len(france_nuts3)} French NUTS3 regions")
    
    # Build dissolved France boundary to find neighbors
    france_dissolved = france_nuts3.dissolve()
    france_geom = france_dissolved.geometry.iloc[0]
    
    included_codes = list(france_nuts3["NUTS_ID"].values)
    
    if include_cross_border:
        # Find non-French NUTS3 that touch France
        allowed_neighbors = ["BE", "DE", "LU", "CH", "IT", "ES"]
        neighbor_nuts3 = nuts3_all[nuts3_all["CNTR_CODE"].isin(allowed_neighbors)]
        
        # Find neighbors that touch France
        neighbor_codes = []
        for _, row in neighbor_nuts3.iterrows():
            if row.geometry.touches(france_geom) or row.geometry.intersects(france_geom):
                neighbor_codes.append(row["NUTS_ID"])
        
        print(f"Found {len(neighbor_codes)} neighboring NUTS3 regions (touching France)")
        included_codes.extend(neighbor_codes)
    
    # Get all included regions
    all_regions = nuts3_all[nuts3_all["NUTS_ID"].isin(included_codes)].copy()
    
    # Dissolve into single polygon
    dissolved = all_regions.dissolve()
    dissolved = dissolved.reset_index(drop=True)
    dissolved["NUTS_IDS"] = ",".join(sorted(included_codes))
    dissolved["n_regions"] = len(included_codes)
    
    _ensure_dir(output_dir)
    out_path = output_dir / "boundary_france_with_neighbors.geojson"
    dissolved.to_crs(WGS84_CRS)[["NUTS_IDS", "n_regions", "geometry"]].to_file(out_path, driver="GeoJSON")
    
    print(f"Built France-wide boundary with neighbors: {out_path}")
    print(f"  Total NUTS3 regions: {len(included_codes)}")
    
    # Save list of all NUTS3 codes
    codes_csv = output_dir / "france_with_neighbors_nuts3.csv"
    pd.DataFrame({
        "nuts3_code": sorted(included_codes),
        "country": [c[:2] for c in sorted(included_codes)]
    }).to_csv(codes_csv, index=False)
    print(f"  Saved NUTS3 list: {codes_csv}")
    
    return out_path, sorted(included_codes)


def _load_all_nuts3_boundaries(nuts_path: Path, nuts_layer: str) -> gpd.GeoDataFrame:
    """Load all NUTS3 boundaries for France and neighboring countries.
    
    Returns:
        GeoDataFrame with nuts3_code, cntr_code, geometry
    """
    if not nuts_path.exists():
        print(f"Warning: NUTS file not found: {nuts_path}")
        return gpd.GeoDataFrame(columns=["nuts3_code", "cntr_code", "geometry"])
    
    nuts = gpd.read_file(nuts_path, layer=nuts_layer)
    nuts3 = nuts[nuts["LEVL_CODE"] == 3].copy()
    
    # Include France + neighboring countries for cross-border
    allowed_countries = ["FR", "BE", "DE", "LU", "CH", "IT", "ES"]
    nuts3 = nuts3[nuts3["CNTR_CODE"].isin(allowed_countries)]
    
    nuts3 = nuts3.rename(columns={"NUTS_ID": "nuts3_code", "CNTR_CODE": "cntr_code"})
    print(f"Loaded {len(nuts3)} NUTS3 regions (FR + neighbors)")
    
    return nuts3[["nuts3_code", "cntr_code", "geometry"]].copy()


# ---------------------------------------------------------------------------
# OSM area extraction (beach, winter_sports)
# ---------------------------------------------------------------------------

# Tags to extract as area polygons
OSM_AREA_TAGS = {
    ("natural", "beach"),           # Beaches
    ("landuse", "winter_sports"),   # Ski stations
}


def _collect_all_pbf_files(main_pbf: Path) -> list[Path]:
    """Collect main France PBF + neighbor PBFs from data/osm/."""
    pbf_files = []
    if main_pbf.exists():
        pbf_files.append(main_pbf)
    if NEIGHBOR_PBF_DIR.exists():
        for f in sorted(NEIGHBOR_PBF_DIR.glob("*.osm.pbf")):
            pbf_files.append(f)
    return pbf_files


class _OSMAreaHandler(osmium.SimpleHandler):
    """Pyosmium handler to extract areas matching specific key=value tags."""

    def __init__(self, bbox, tag_pairs: set):
        super().__init__()
        if bbox is not None:
            self.minx, self.miny, self.maxx, self.maxy = bbox
        else:
            self.minx, self.miny, self.maxx, self.maxy = -180, -90, 180, 90
        self.tag_pairs = tag_pairs
        self.areas = []
        self.wkbfab = osmium.geom.WKBFactory()
        self._areas_processed = 0

    def _in_bbox(self, lon: float, lat: float) -> bool:
        return self.minx <= lon <= self.maxx and self.miny <= lat <= self.maxy

    def area(self, a):
        self._areas_processed += 1
        matched_key = matched_val = None
        for key, value in self.tag_pairs:
            if a.tags.get(key) == value:
                matched_key, matched_val = key, value
                break
        if matched_key is None:
            return

        try:
            wkb = self.wkbfab.create_multipolygon(a)
            geom = shapely_wkb.loads(wkb, hex=True)
        except Exception:
            return

        centroid = geom.centroid
        if not self._in_bbox(centroid.x, centroid.y):
            return

        self.areas.append({
            "osm_id": a.orig_id() if hasattr(a, "orig_id") else a.id,
            "name": a.tags.get("name", ""),
            "osm_key": matched_key,
            "osm_value": matched_val,
            "geometry": geom,
        })


def _extract_osm_areas_from_pbf(
    pbf_path: Path,
    bbox,
    region_geom,
    tag_pairs: set,
) -> gpd.GeoDataFrame:
    """Extract area features matching tag_pairs from a single PBF."""
    start = time.time()
    handler = _OSMAreaHandler(bbox, tag_pairs)
    handler.apply_file(str(pbf_path), locations=True)
    elapsed = time.time() - start
    print(f"  Pyosmium scan: {elapsed:.1f}s, areas processed: {handler._areas_processed:,}, matched: {len(handler.areas):,}")

    if not handler.areas:
        return gpd.GeoDataFrame(columns=["osm_id", "name", "osm_key", "osm_value", "geometry"])

    gdf = gpd.GeoDataFrame(handler.areas, crs=WGS84_CRS)

    if region_geom is not None:
        before = len(gdf)
        gdf = gdf[gdf.geometry.intersects(region_geom)].copy()
        print(f"  After boundary clip: {before:,} -> {len(gdf):,}")
    else:
        print(f"  No clip (full extent): {len(gdf):,}")

    return gdf


def prepare_osm_areas(
    boundary_path: Optional[Path] = None,
    output_dir: Path = OUTPUT_DIR,
    france_wide: bool = False,
) -> Optional[Path]:
    """Extract beach and ski-station areas from OSM PBF files.

    Outputs a single GeoPackage with polygon geometries (not converted to
    points) so that downstream steps can compute area-based metrics.
    """
    print("=" * 50)
    print("PREPARING OSM AREAS (beach, winter_sports)")
    print("=" * 50)

    main_pbf = DEFAULT_OSM_PBF
    if not main_pbf.exists():
        print(f"Warning: France PBF not found: {main_pbf} — skipping OSM areas")
        return None

    # Build boundary geometry for France PBF clipping
    region_geom = None
    bbox = None
    if boundary_path and boundary_path.exists():
        region_geom = _load_boundary(boundary_path, WGS84_CRS)
        bbox = region_geom.bounds  # (minx, miny, maxx, maxy)

    # Collect PBFs
    if france_wide:
        pbf_files = _collect_all_pbf_files(main_pbf)
    else:
        pbf_files = [main_pbf]

    main_pbf_resolved = main_pbf.resolve()

    all_areas = []
    for pbf in pbf_files:
        is_main = pbf.resolve() == main_pbf_resolved
        clip_geom = region_geom if is_main else None
        pbf_bbox = bbox if is_main else None
        label = "(with boundary clip)" if is_main and region_geom else "(full extent)"
        print(f"\nExtracting from: {pbf.name} {label}")
        gdf = _extract_osm_areas_from_pbf(pbf, pbf_bbox, clip_geom, OSM_AREA_TAGS)
        if not gdf.empty:
            all_areas.append(gdf)

    if not all_areas:
        print("No beach/winter_sports areas found.")
        return None

    areas = gpd.GeoDataFrame(pd.concat(all_areas, ignore_index=True), crs=WGS84_CRS)
    before_dedup = len(areas)
    areas = areas.drop_duplicates(subset="osm_id", keep="first")
    print(f"\nTotal areas before dedup: {before_dedup:,}, after: {len(areas):,}")

    # Per-type summary
    for (k, v), cnt in areas.groupby(["osm_key", "osm_value"]).size().items():
        print(f"  {k}={v}: {cnt:,}")

    _ensure_dir(output_dir)
    gpkg_path = output_dir / "osm_areas.gpkg"
    areas.to_file(gpkg_path, layer="osm_areas", driver="GPKG")
    print(f"Wrote: {gpkg_path} ({len(areas):,} areas)")

    # Also write centroid points for downstream grid-mapping steps
    # Reproject to Lambert 93 for accurate centroid computation, then back to WGS84
    areas_pts = areas.to_crs(LAMBERT93_CRS).copy()
    areas_pts["geometry"] = areas_pts.geometry.centroid
    areas_pts = areas_pts.to_crs(WGS84_CRS)
    pts_path = output_dir / "osm_area_points.gpkg"
    areas_pts.to_file(pts_path, layer="osm_area_points", driver="GPKG")
    print(f"Wrote: {pts_path} ({len(areas_pts):,} centroid points)")

    return gpkg_path


def prepare_bpe_data(bpe_csv_path: Path, 
                     boundary_path: Optional[Path] = None,
                     output_dir: Path = OUTPUT_DIR) -> None:
    """Prepare BPE points from INSEE CSV data."""
    print("=" * 50)
    print("PREPARING BPE DATA")
    print("=" * 50)
    
    if not bpe_csv_path.exists():
        raise FileNotFoundError(f"BPE CSV not found: {bpe_csv_path}")
    
    print(f"Reading BPE CSV: {bpe_csv_path}")
    # Read with low_memory=False to avoid dtype warnings, using semicolon separator
    bpe_df = pd.read_csv(bpe_csv_path, sep=';', low_memory=False)
    
    # Check for required columns
    required_cols = ['LAMBERT_X', 'LAMBERT_Y', 'TYPEQU', 'DEPCOM']
    missing_cols = [col for col in required_cols if col not in bpe_df.columns]
    if missing_cols:
        raise ValueError(f"BPE CSV missing required columns: {missing_cols}")
    
    # Filter to selected equipment types
    initial_count = len(bpe_df)
    exact_mask = bpe_df['TYPEQU'].isin(BPE_EXACT_CODES)
    prefix_mask = bpe_df['TYPEQU'].str.startswith(BPE_PREFIX_CODES)
    bpe_df = bpe_df[exact_mask | prefix_mask].copy()
    print(f"Filtered BPE by equipment type: {initial_count:,} -> {len(bpe_df):,} (kept {len(bpe_df):,} matching types)")
    
    # Filter out rows with missing coordinates
    before_coord = len(bpe_df)
    bpe_df = bpe_df.dropna(subset=['LAMBERT_X', 'LAMBERT_Y'])
    print(f"Filtered missing coordinates: {before_coord:,} -> {len(bpe_df):,} (removed {before_coord - len(bpe_df):,})")
    
    # Convert to GeoDataFrame in Lambert 93
    print("Converting to GeoDataFrame...")
    from shapely.geometry import Point
    geometry = [Point(x, y) for x, y in zip(bpe_df['LAMBERT_X'], bpe_df['LAMBERT_Y'])]
    gdf_l93 = gpd.GeoDataFrame(bpe_df, geometry=geometry, crs=LAMBERT93_CRS)
    
    # Clip to boundary if provided
    if boundary_path and boundary_path.exists():
        print("Clipping to boundary...")
        boundary_geom = _load_boundary(boundary_path, LAMBERT93_CRS)
        gdf_l93 = gdf_l93[gdf_l93.intersects(boundary_geom)]
        print(f"After boundary clipping: {len(gdf_l93):,} points")
    
    # Convert to WGS84 for routing compatibility
    print("Converting to WGS84...")
    gdf_wgs84 = gdf_l93.to_crs(WGS84_CRS)
    
    # Add lon/lat columns for easy CSV export
    gdf_wgs84['lon'] = gdf_wgs84.geometry.x
    gdf_wgs84['lat'] = gdf_wgs84.geometry.y
    
    # Prepare outputs
    _ensure_dir(output_dir)
    
    # Save GeoPackage (with geometry)
    gpkg_path = output_dir / "bpe_points.gpkg"
    print(f"Writing GeoPackage: {gpkg_path}")
    gdf_wgs84.to_file(gpkg_path, driver="GPKG")
    
    # Save CSV (coordinates only, for routing)
    csv_path = output_dir / "bpe_points.csv"
    print(f"Writing CSV: {csv_path}")
    csv_cols = ['TYPEQU', 'DEPCOM', 'LAMBERT_X', 'LAMBERT_Y', 'lon', 'lat']
    available_cols = [col for col in csv_cols if col in gdf_wgs84.columns]
    gdf_wgs84[available_cols].to_csv(csv_path, index=False)
    
    print(f"BPE data prepared: {len(gdf_wgs84):,} points")
    return gpkg_path, csv_path


def prepare_filosofi_grid(filosofi_shp_path: Path,
                          boundary_path: Optional[Path] = None,
                          output_dir: Path = OUTPUT_DIR) -> None:
    """Prepare Filosofi grid points from polygon shapefile."""
    print("=" * 50)
    print("PREPARING FILOSOFI GRID")
    print("=" * 50)
    
    if not filosofi_shp_path.exists():
        raise FileNotFoundError(f"Filosofi shapefile not found: {filosofi_shp_path}")
    
    print(f"Reading Filosofi shapefile: {filosofi_shp_path}")
    # Look for .shp file in the directory, prefer metropolitan France
    shp_files = list(filosofi_shp_path.glob("*.shp"))
    if not shp_files:
        raise FileNotFoundError(f"No .shp files found in: {filosofi_shp_path}")
    
    # Prefer metropolitan France shapefile (contains 'met' in name)
    met_files = [f for f in shp_files if 'met' in f.name.lower()]
    filosofi_shp = met_files[0] if met_files else shp_files[0]
    print(f"Using shapefile: {filosofi_shp}")
    
    gdf = gpd.read_file(filosofi_shp)
    print(f"Loaded {len(gdf):,} grid polygons")
    
    # Ensure we have the expected CRS (should be Lambert 93)
    if gdf.crs is None:
        print("Warning: No CRS found, assuming Lambert 93")
        gdf = gdf.set_crs(LAMBERT93_CRS)
    elif gdf.crs.to_string() != LAMBERT93_CRS:
        print(f"Converting from {gdf.crs} to {LAMBERT93_CRS}")
        gdf = gdf.to_crs(LAMBERT93_CRS)
    
    # Clip to boundary if provided
    if boundary_path and boundary_path.exists():
        print("Clipping to boundary...")
        boundary_geom = _load_boundary(boundary_path, LAMBERT93_CRS)
        gdf = gdf[gdf.intersects(boundary_geom)]
        print(f"After boundary clipping: {len(gdf):,} grid cells")
    
    # Convert polygons to centroids (points)
    print("Converting polygons to centroid points...")
    gdf['geometry'] = gdf.geometry.centroid
    
    # Add grid ID if missing (use index-based ID)
    if 'idcar_200m' not in gdf.columns:
        gdf['idcar_200m'] = [f"grid_{i:06d}" for i in range(len(gdf))]
        print("Added grid IDs (idcar_200m)")
    
    # Convert to WGS84
    print("Converting to WGS84...")
    gdf_wgs84 = gdf.to_crs(WGS84_CRS)
    
    # Add lon/lat columns
    gdf_wgs84['lon'] = gdf_wgs84.geometry.x
    gdf_wgs84['lat'] = gdf_wgs84.geometry.y
    
    # Prepare outputs  
    _ensure_dir(output_dir)
    
    # Save GeoPackage
    gpkg_path = output_dir / "filosofi_grid_points.gpkg"
    print(f"Writing GeoPackage: {gpkg_path}")
    gdf_wgs84.to_file(gpkg_path, driver="GPKG")
    
    # Save CSV
    csv_path = output_dir / "filosofi_grid_points.csv"
    print(f"Writing CSV: {csv_path}")
    csv_cols = ['idcar_200m', 'lon', 'lat']
    # Include NUTS3 code if present
    if 'nuts3_code' in gdf_wgs84.columns:
        csv_cols.append('nuts3_code')
    # Include any population/income columns that exist
    for col in gdf_wgs84.columns:
        if any(keyword in col.lower() for keyword in ['pop', 'men', 'ind', 'log']):
            csv_cols.append(col)
    
    available_cols = [col for col in csv_cols if col in gdf_wgs84.columns]
    gdf_wgs84[available_cols].to_csv(csv_path, index=False)
    
    print(f"Filosofi grid prepared: {len(gdf_wgs84):,} points")
    return gpkg_path, csv_path


def assign_nuts3_to_grid(
    gdf: gpd.GeoDataFrame,
    nuts_path: Path,
    nuts_layer: str,
) -> gpd.GeoDataFrame:
    """Assign NUTS3 codes to grid cells via spatial join.
    
    Args:
        gdf: Grid GeoDataFrame (points or polygons)
        nuts_path: Path to NUTS GeoPackage
        nuts_layer: Layer name
    
    Returns:
        GeoDataFrame with nuts3_code column added
    """
    print("Assigning NUTS3 codes to grid cells...")
    
    nuts3_gdf = _load_all_nuts3_boundaries(nuts_path, nuts_layer)
    if nuts3_gdf.empty:
        gdf["nuts3_code"] = None
        return gdf
    
    # Ensure same CRS
    nuts3_gdf = nuts3_gdf.to_crs(gdf.crs)
    
    # Spatial join
    joined = gpd.sjoin(gdf, nuts3_gdf[["nuts3_code", "geometry"]], 
                       how="left", predicate="within")
    
    # Handle duplicates
    if "index_right" in joined.columns:
        joined = joined.drop(columns=["index_right"])
    
    # Keep first match for each grid cell
    joined = joined.drop_duplicates(subset=[c for c in joined.columns if c not in ["geometry", "index_right"]])
    
    n_assigned = joined["nuts3_code"].notna().sum()
    print(f"  Assigned NUTS3 to {n_assigned:,}/{len(joined):,} grid cells")
    
    return joined


def prepare_gtfs_data(gtfs_dirs: list[Path],
                      output_dir: Path = OUTPUT_DIR,
                      boundary_path: Optional[Path] = None,
                      morning_peak: bool = True) -> None:
    """GTFS/PT preprocessing is not handled in this script. Please run the appropriate PT preprocessing script manually if needed."""
    print("GTFS/PT preprocessing is not handled in this script. Please run the appropriate PT preprocessing script manually if needed.")
    return None


def copy_boundary_file(boundary_path: Path, output_dir: Path) -> Path:
    """Copy boundary file to output directory."""
    if not boundary_path.exists():
        raise FileNotFoundError(f"Boundary file not found: {boundary_path}")
    
    _ensure_dir(output_dir)
    output_path = output_dir / "boundary.geojson"
    
    print(f"Copying boundary: {boundary_path} -> {output_path}")
    shutil.copy2(boundary_path, output_path)
    
    return output_path


def create_summary_report(output_dir: Path) -> None:
    """Create a summary report of prepared data."""
    print("=" * 50) 
    print("CREATING DATA SUMMARY")
    print("=" * 50)
    
    summary_path = output_dir / "data_summary.txt"
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("DATA IMPORT & PREPARATION SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Generated on: {pd.Timestamp.now()}\n\n")
        
        # Check each output file
        files_to_check = [
            ("BPE Points (GeoPackage)", "bpe_points.gpkg"),
            ("BPE Points (CSV)", "bpe_points.csv"), 
            ("Filosofi Grid (GeoPackage)", "filosofi_grid_points.gpkg"),
            ("Filosofi Grid (CSV)", "filosofi_grid_points.csv"),
            ("Boundary", "boundary.geojson"),
            ("GTFS Processed", "gtfs_processed"),
            ("OSM Areas (beach, ski)", "osm_areas.gpkg")
        ]
        
        f.write("FILES CREATED:\n")
        f.write("-" * 20 + "\n")
        
        for desc, filename in files_to_check:
            filepath = output_dir / filename
            if filepath.exists():
                if filepath.is_file():
                    size_mb = filepath.stat().st_size / (1024 * 1024)
                    f.write(f"[+] {desc}: {filename} ({size_mb:.1f} MB)\n")
                else:
                    f.write(f"[+] {desc}: {filename} (directory)\n")
            else:
                f.write(f"[-] {desc}: {filename} (missing)\n")
        
        # Try to get record counts
        f.write(f"\nRECORD COUNTS:\n")
        f.write("-" * 20 + "\n")
        
        try:
            bpe_gpkg = output_dir / "bpe_points.gpkg"
            if bpe_gpkg.exists():
                bpe_gdf = gpd.read_file(bpe_gpkg)
                f.write(f"BPE Points: {len(bpe_gdf):,}\n")
        except Exception as e:
            f.write(f"BPE Points: Error reading ({e})\n")
            
        try:
            grid_gpkg = output_dir / "filosofi_grid_points.gpkg"  
            if grid_gpkg.exists():
                grid_gdf = gpd.read_file(grid_gpkg)
                f.write(f"Grid Points: {len(grid_gdf):,}\n")
        except Exception as e:
            f.write(f"Grid Points: Error reading ({e})\n")
    
    print(f"Summary report: {summary_path}")


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        description="Phase 1: Data Import & Preparation",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Input paths
    parser.add_argument("--bpe-csv", type=Path, default=DEFAULT_BPE_CSV,
                       help="Path to BPE CSV file")
    parser.add_argument("--filosofi-shp", type=Path, default=DEFAULT_FILOSOFI_SHP,
                       help="Path to Filosofi shapefile directory")
    parser.add_argument("--gtfs-dirs", type=Path, nargs="*", default=DEFAULT_GTFS_DIRS,
                       help="Paths to GTFS directories")
    parser.add_argument("--boundary", type=Path, default=DEFAULT_BOUNDARY,
                       help="Path to boundary file (optional; ignored if --boundary-nuts3 is set)")
    parser.add_argument("--boundary-nuts3", type=str, default=DEFAULT_BOUNDARY_NUTS3,
                       help="NUTS3 code (e.g. FRI12 for Gironde). If set, overrides --boundary.")
    parser.add_argument("--nuts-gpkg", type=Path, default=DEFAULT_NUTS_GPKG,
                       help="Path to NUTS GeoPackage used with --boundary-nuts3")
    parser.add_argument("--nuts-layer", type=str, default=DEFAULT_NUTS_LAYER,
                       help="NUTS layer name used with --boundary-nuts3")
    
    # Output
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR,
                       help="Output directory")
    
    # Processing options
    parser.add_argument("--skip-bpe", action="store_true",
                       help="Skip BPE data preparation")
    parser.add_argument("--skip-filosofi", action="store_true", 
                       help="Skip Filosofi grid preparation")
    parser.add_argument("--skip-gtfs", action="store_true", default=True,
                       help="Skip GTFS data preparation (default: True; use 00_prepare_public_transport.py)")
    parser.add_argument("--skip-osm-areas", action="store_true",
                       help="Skip OSM area extraction (beach, winter_sports)")
    parser.add_argument("--no-morning-peak", action="store_true",
                       help="Don't apply morning peak preset for GTFS")
    
    # NUTS3 options
    parser.add_argument("--with-neighbors", action="store_true", default=True,
                       help="Include neighboring NUTS3 regions in boundary (default: True)")
    parser.add_argument("--include-cross-border", action="store_true", default=True,
                       help="Include non-France NUTS3 neighbors (default: True)")
    parser.add_argument("--assign-nuts3", action="store_true",
                       help="Assign NUTS3 codes to grid cells via spatial join")
    parser.add_argument("--france-wide", action="store_true", default=True,
                       help="Process all of France (default: True)")
    parser.add_argument("--no-france-wide", action="store_true",
                       help="Disable france-wide mode (use --boundary-nuts3 instead)")
    
    return parser


def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    
    # Handle --no-france-wide override
    if args.no_france_wide:
        args.france_wide = False

    print("PHASE 1: DATA IMPORT & PREPARATION")
    print("=" * 60)
    print(f"Output directory: {args.output_dir}")
    if args.france_wide:
        print("Mode: France-wide (no boundary clipping)")
    if args.with_neighbors:
        print("Mode: Include neighboring NUTS3 regions")
    if args.include_cross_border:
        print("Mode: Include cross-border NUTS3 (BE, DE, LU, CH, IT, ES)")
    if args.assign_nuts3:
        print("Mode: Assign NUTS3 codes to grid cells")
    print()

    boundary_path: Path | None = None
    neighbor_nuts3_codes: list[str] = []
    
    # France-wide mode
    if args.france_wide:
        if args.with_neighbors:
            # Build France + neighboring NUTS3 boundary
            boundary_path, neighbor_nuts3_codes = _build_france_boundary_with_neighbors(
                nuts_path=args.nuts_gpkg,
                nuts_layer=args.nuts_layer,
                output_dir=args.output_dir,
                include_cross_border=args.include_cross_border,
            )
            print(f"Using France-wide boundary with {len(neighbor_nuts3_codes)} NUTS3 regions")
        else:
            # France-wide without neighbors: no boundary clipping
            print("France-wide mode: no boundary clipping")
            boundary_path = None
    elif args.boundary_nuts3.strip():
        nuts3_id = args.boundary_nuts3.strip()
        
        if args.with_neighbors:
            # Build boundary with neighbors
            boundary_path, neighbor_nuts3_codes = _build_boundary_with_neighbors(
                nuts_path=args.nuts_gpkg,
                nuts_layer=args.nuts_layer,
                nuts3_id=nuts3_id,
                output_dir=args.output_dir,
                include_cross_border=args.include_cross_border,
            )
            print(f"Using extended NUTS3 boundary: {nuts3_id} + {len(neighbor_nuts3_codes)-1} neighbors")
        else:
            # Single NUTS3 boundary
            boundary_path = _build_boundary_from_nuts3(
                nuts_path=args.nuts_gpkg,
                nuts_layer=args.nuts_layer,
                nuts3_id=nuts3_id,
                output_dir=args.output_dir,
            )
            neighbor_nuts3_codes = [nuts3_id]
            print(f"Using NUTS3 boundary: {nuts3_id}")
    elif args.boundary and args.boundary.exists():
        boundary_path = args.boundary
        print(f"Using boundary file: {boundary_path}")
    else:
        print("No valid boundary provided; running without clipping boundary")
    
    try:
        # Prepare BPE data
        if not args.skip_bpe:
            prepare_bpe_data(
                bpe_csv_path=args.bpe_csv,
                boundary_path=boundary_path,
                output_dir=args.output_dir
            )
        else:
            print("Skipping BPE data preparation")
        
        print()
        
        # Prepare Filosofi grid
        if not args.skip_filosofi:
            prepare_filosofi_grid(
                filosofi_shp_path=args.filosofi_shp,
                boundary_path=boundary_path,
                output_dir=args.output_dir
            )
            
            # Assign NUTS3 codes to grid if requested
            if args.assign_nuts3:
                print()
                print("Assigning NUTS3 codes to grid cells...")
                gpkg_path = args.output_dir / "filosofi_grid_points.gpkg"
                if gpkg_path.exists():
                    gdf = gpd.read_file(gpkg_path)
                    gdf = assign_nuts3_to_grid(gdf, args.nuts_gpkg, args.nuts_layer)
                    gdf.to_file(gpkg_path, driver="GPKG")
                    
                    # Update CSV
                    csv_path = args.output_dir / "filosofi_grid_points.csv"
                    csv_cols = ['idcar_200m', 'lon', 'lat', 'nuts3_code']
                    for col in gdf.columns:
                        if any(kw in col.lower() for kw in ['pop', 'men', 'ind', 'log']):
                            csv_cols.append(col)
                    available_cols = [c for c in csv_cols if c in gdf.columns]
                    gdf[available_cols].to_csv(csv_path, index=False)
                    print(f"Updated grid with NUTS3 codes: {gpkg_path}")
        else:
            print("Skipping Filosofi grid preparation")
            
        print()
        
        # Prepare GTFS data
        if not args.skip_gtfs:
            prepare_gtfs_data(
                gtfs_dirs=args.gtfs_dirs,
                output_dir=args.output_dir,
                boundary_path=boundary_path,
                morning_peak=not args.no_morning_peak
            )
        else:
            print("Skipping GTFS data preparation")
            
        print()

        # Extract OSM areas (beach, winter_sports)
        if not args.skip_osm_areas:
            prepare_osm_areas(
                boundary_path=boundary_path,
                output_dir=args.output_dir,
                france_wide=args.france_wide,
            )
        else:
            print("Skipping OSM area extraction")

        print()
        
        # Copy boundary file
        if boundary_path and boundary_path.exists() and boundary_path.parent != args.output_dir:
            copy_boundary_file(boundary_path, args.output_dir)
        
        # Create summary
        create_summary_report(args.output_dir)
        
        print("=" * 60)
        print("PHASE 1 COMPLETED SUCCESSFULLY")
        print(f"All prepared data available in: {args.output_dir}")
        if neighbor_nuts3_codes:
            print(f"NUTS3 regions included: {', '.join(neighbor_nuts3_codes)}")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user.")
    except Exception as e:
        print(f"\n\nError during Phase 1: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()