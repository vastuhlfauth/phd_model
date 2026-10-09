#!/usr/bin/env python3
"""
Prepare GTFS data for OpenTripPlanner routing.

This script processes multiple GTFS datasets to create a unified, preprocessed
feed suitable for public transport routing. It follows the same patterns as
the OSRM preprocessing pipeline but for public transport.

Main preprocessing steps:
1. GTFS validation (completeness check)
2. Make all IDs globally unique across datasets
3. Filter to weekdays only (for now)
4. Ensure coordinates are in Lambert 93 + add grid cell coordinates
5. Group nearby stops that are far from grid cells
6. Generate transfers.txt if missing
7. Merge all datasets into a unified GTFS feed

Designed to scale from Bordeaux to France-wide processing.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sqlite3
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point, box
from shapely import STRtree

# Suppress pandas future warnings for cleaner output
warnings.simplefilter(action='ignore', category=FutureWarning)

ROOT_DIR = Path(__file__).resolve().parent.parent

# GTFS required files for basic routing
# calendar.txt is not strictly required — GTFS allows calendar_dates.txt only
REQUIRED_FILES = {'agency.txt', 'stops.txt', 'routes.txt', 'trips.txt', 'stop_times.txt'}
OPTIONAL_FILES = {'calendar.txt', 'calendar_dates.txt', 'transfers.txt', 'shapes.txt', 'feed_info.txt'}

# Lambert 93 projection (EPSG:2154) for distance calculations
LAMBERT_CRS = "EPSG:2154"
WGS84_CRS = "EPSG:4326"
transformer_to_lambert = Transformer.from_crs(WGS84_CRS, LAMBERT_CRS, always_xy=True)
transformer_to_wgs84 = Transformer.from_crs(LAMBERT_CRS, WGS84_CRS, always_xy=True)

# Default parameters
MAX_GRID_DISTANCE_M = 250  # Max distance to assign to a grid cell
STOP_GROUPING_DISTANCE_M = 100  # Group stops closer than this when far from grid
DEFAULT_TRANSFER_TIME_S = 120  # Default transfer time (2 min)
WALK_SPEED_MS = 1.2  # Walking speed in m/s (4.3 km/h)

# Default reference date and time window
DATE_DEFAULT = "2026-03-18"  # Reference date for service filtering
TIME_WINDOW_DEFAULT = ("07:00:00", "09:30:00")  # Departure time window

# GTFS root directory (NUTS2 region subfolders with ZIP feeds)
GTFS_ROOT_DIR = ROOT_DIR / "data" / "GTFS"

def _cluster_labels_within_radius(xs: np.ndarray, ys: np.ndarray, radius_m: float) -> np.ndarray:
    """Build connected-component cluster labels using fixed-radius neighbor links.

    Same algorithm as ``02_destination_grid_preparation._cluster_labels_within_radius``
    but accepts raw coordinate arrays to avoid rebuilding Point objects.
    """
    n = len(xs)
    if n == 0:
        return np.array([], dtype=np.int64)

    from scipy.spatial import cKDTree
    tree = cKDTree(np.column_stack([xs, ys]))

    labels = np.full(n, -1, dtype=np.int64)
    cluster_id = 0

    for start in range(n):
        if labels[start] != -1:
            continue
        labels[start] = cluster_id
        stack = [start]

        while stack:
            i = stack.pop()
            neighbors = tree.query_ball_point([xs[i], ys[i]], r=radius_m)
            for j in neighbors:
                if labels[j] == -1:
                    labels[j] = cluster_id
                    stack.append(j)
        cluster_id += 1

    return labels


def _ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def _parse_time_to_seconds(time_str: str) -> int:
    """Convert HH:MM:SS time string to seconds since midnight."""
    if pd.isna(time_str) or not time_str:
        return 0
    
    # Handle times > 24:00:00 (next day)
    parts = str(time_str).split(':')
    hours = int(parts[0])
    minutes = int(parts[1]) if len(parts) > 1 else 0
    seconds = int(parts[2]) if len(parts) > 2 else 0
    
    return hours * 3600 + minutes * 60 + seconds

def _seconds_to_time_str(seconds: int) -> str:
    """Convert seconds since midnight to HH:MM:SS string."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def _get_date_range_for_weeks(weeks_spec: list) -> list:
    """Convert week specifications to date ranges."""
    from datetime import datetime, timedelta
    
    date_ranges = []
    for week_spec in weeks_spec:
        if isinstance(week_spec, tuple) and len(week_spec) == 2:
            start_date, end_date = week_spec
            date_ranges.append((start_date, end_date))
        elif isinstance(week_spec, str):
            # Parse as 'YYYY-MM-DD' and create week range
            start_date = datetime.strptime(week_spec, '%Y-%m-%d')
            # Find Monday of that week
            monday = start_date - timedelta(days=start_date.weekday())
            sunday = monday + timedelta(days=6)
            date_ranges.append((monday.strftime('%Y-%m-%d'), sunday.strftime('%Y-%m-%d')))
    
    return date_ranges

def _discover_gtfs_feeds(gtfs_root: Path) -> list[Path]:
    """Auto-discover GTFS feeds under a root directory.

    Handles two layouts:
    - Extracted directories containing stops.txt (e.g. 33_gironde/bordeaux.gtfs/)
    - ZIP files that are extracted on-the-fly into a sibling directory
    """
    import zipfile

    feeds: list[Path] = []

    if not gtfs_root.exists():
        raise FileNotFoundError(f"GTFS root not found: {gtfs_root}")

    for child in sorted(gtfs_root.iterdir()):
        if not child.is_dir():
            continue
        # Region folder (e.g. Nouvelle-Aquitaine/, 33_gironde/)
        # Check for ZIP files first
        zips = list(child.glob("*.zip"))
        if zips:
            for zf in sorted(zips):
                extract_dir = child / zf.stem
                if not (extract_dir / "stops.txt").exists():
                    print(f"  Extracting {zf.name} -> {extract_dir.name}/")
                    extract_dir.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(zf, "r") as z:
                        z.extractall(extract_dir)
                # Verify it has required files
                if (extract_dir / "stops.txt").exists():
                    feeds.append(extract_dir)
                else:
                    # Some ZIPs nest files one level deeper
                    subdirs = [d for d in extract_dir.iterdir() if d.is_dir() and (d / "stops.txt").exists()]
                    if subdirs:
                        feeds.extend(sorted(subdirs))
                    else:
                        print(f"  Warning: No stops.txt found after extracting {zf.name}")
        else:
            # Check for already-extracted subdirectories
            sub_feeds = [d for d in sorted(child.iterdir()) if d.is_dir() and (d / "stops.txt").exists()]
            if sub_feeds:
                feeds.extend(sub_feeds)
            elif (child / "stops.txt").exists():
                feeds.append(child)

    return feeds


def _load_grid_points(grid_gpkg_path: Path) -> gpd.GeoDataFrame:
    """Load grid points from GeoPackage and ensure Lambert 93 projection."""
    if not grid_gpkg_path.exists():
        raise FileNotFoundError(f"Grid points file not found: {grid_gpkg_path}")
    
    gdf = gpd.read_file(grid_gpkg_path)
    if gdf.crs is None:
        print(f"  Warning: Grid points have no CRS, assuming WGS84")
        gdf = gdf.set_crs(WGS84_CRS)
    
    # Ensure Lambert 93 for distance calculations
    gdf = gdf.to_crs(LAMBERT_CRS)
    return gdf

def _load_boundary(boundary_path: Path) -> gpd.GeoDataFrame:
    """Load boundary polygon for clipping."""
    if not boundary_path.exists():
        raise FileNotFoundError(f"Boundary file not found: {boundary_path}")
    
    boundary = gpd.read_file(boundary_path)
    if len(boundary) == 0:
        raise ValueError(f"Boundary file is empty: {boundary_path}")
    
    # Union all geometries if multiple
    if hasattr(boundary.geometry, "union_all"):
        boundary_geom = boundary.geometry.union_all()
    else:
        boundary_geom = boundary.geometry.unary_union
    
    return gpd.GeoDataFrame(geometry=[boundary_geom], crs=boundary.crs).to_crs(LAMBERT_CRS)

class GTFSValidator:
    """Validate GTFS dataset completeness and basic integrity."""
    
    def __init__(self, gtfs_dir: Path):
        self.gtfs_dir = gtfs_dir
        self.errors = []
        self.warnings = []
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """Validate GTFS dataset. Returns (is_valid, errors, warnings)."""
        self.errors = []
        self.warnings = []
        
        # Check required files
        for required_file in REQUIRED_FILES:
            file_path = self.gtfs_dir / required_file
            if not file_path.exists():
                self.errors.append(f"Missing required file: {required_file}")
            elif file_path.stat().st_size == 0:
                self.errors.append(f"Empty required file: {required_file}")
        
        # At least one of calendar.txt or calendar_dates.txt must exist
        has_calendar = (self.gtfs_dir / 'calendar.txt').exists()
        has_calendar_dates = (self.gtfs_dir / 'calendar_dates.txt').exists()
        if not has_calendar and not has_calendar_dates:
            self.errors.append("Missing both calendar.txt and calendar_dates.txt (at least one required)")
        
        if self.errors:
            return False, self.errors, self.warnings
        
        # Check file formats and basic integrity
        self._check_stops()
        self._check_routes()
        self._check_trips()
        self._check_stop_times()
        if has_calendar:
            self._check_calendar()
        
        # Check referential integrity
        self._check_referential_integrity()
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _check_stops(self):
        """Validate stops.txt."""
        try:
            df = pd.read_csv(self.gtfs_dir / 'stops.txt')
            required_cols = {'stop_id', 'stop_name', 'stop_lat', 'stop_lon'}
            missing_cols = required_cols - set(df.columns)
            if missing_cols:
                self.errors.append(f"stops.txt missing columns: {missing_cols}")
                return
            
            # Check for missing coordinates
            invalid_coords = df[df['stop_lat'].isna() | df['stop_lon'].isna()]
            if len(invalid_coords) > 0:
                self.errors.append(f"stops.txt has {len(invalid_coords)} stops with missing coordinates")
            
            # Check coordinate ranges (rough check for France)
            lat_range = (df['stop_lat'].min(), df['stop_lat'].max())
            lon_range = (df['stop_lon'].min(), df['stop_lon'].max())
            if lat_range[0] < 41 or lat_range[1] > 52:
                self.warnings.append(f"stops.txt latitude range {lat_range} seems outside France")
            if lon_range[0] < -5 or lon_range[1] > 10:
                self.warnings.append(f"stops.txt longitude range {lon_range} seems outside France")
                
        except Exception as e:
            self.errors.append(f"Error reading stops.txt: {e}")
    
    def _check_routes(self):
        """Validate routes.txt."""
        try:
            df = pd.read_csv(self.gtfs_dir / 'routes.txt')
            required_cols = {'route_id', 'route_short_name', 'route_type'}
            missing_cols = required_cols - set(df.columns)
            if missing_cols:
                self.errors.append(f"routes.txt missing columns: {missing_cols}")
        except Exception as e:
            self.errors.append(f"Error reading routes.txt: {e}")
    
    def _check_trips(self):
        """Validate trips.txt."""
        try:
            df = pd.read_csv(self.gtfs_dir / 'trips.txt')
            required_cols = {'trip_id', 'route_id', 'service_id'}
            missing_cols = required_cols - set(df.columns)
            if missing_cols:
                self.errors.append(f"trips.txt missing columns: {missing_cols}")
        except Exception as e:
            self.errors.append(f"Error reading trips.txt: {e}")
    
    def _check_stop_times(self):
        """Validate stop_times.txt."""
        try:
            # Read a sample to check structure (file can be very large)
            df = pd.read_csv(self.gtfs_dir / 'stop_times.txt', nrows=1000)
            required_cols = {'trip_id', 'stop_id', 'stop_sequence'}
            missing_cols = required_cols - set(df.columns)
            if missing_cols:
                self.errors.append(f"stop_times.txt missing columns: {missing_cols}")
        except Exception as e:
            self.errors.append(f"Error reading stop_times.txt: {e}")
    
    def _check_calendar(self):
        """Validate calendar.txt."""
        try:
            df = pd.read_csv(self.gtfs_dir / 'calendar.txt')
            required_cols = {'service_id', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}
            missing_cols = required_cols - set(df.columns)
            if missing_cols:
                self.errors.append(f"calendar.txt missing columns: {missing_cols}")
        except Exception as e:
            self.errors.append(f"Error reading calendar.txt: {e}")
    
    def _check_referential_integrity(self):
        """Basic referential integrity checks."""
        try:
            # Load key files
            stops = pd.read_csv(self.gtfs_dir / 'stops.txt')
            routes = pd.read_csv(self.gtfs_dir / 'routes.txt')
            trips = pd.read_csv(self.gtfs_dir / 'trips.txt')
            
            # Check trip -> route references
            missing_routes = set(trips['route_id']) - set(routes['route_id'])
            if missing_routes:
                self.errors.append(f"trips.txt references missing routes: {len(missing_routes)} routes")
            
            # Check trip -> service references
            # GTFS allows services defined in calendar.txt, calendar_dates.txt, or both
            known_services = set()
            cal_path = self.gtfs_dir / 'calendar.txt'
            if cal_path.exists():
                calendar = pd.read_csv(cal_path)
                known_services = set(calendar['service_id'])
            cd_path = self.gtfs_dir / 'calendar_dates.txt'
            if cd_path.exists():
                cd = pd.read_csv(cd_path)
                known_services |= set(cd['service_id'])
            missing_services = set(trips['service_id']) - known_services
            if missing_services:
                self.errors.append(f"trips.txt references missing services: {len(missing_services)} services")
                
        except Exception as e:
            self.warnings.append(f"Could not check referential integrity: {e}")


class GTFSProcessor:
    """Main GTFS processing class."""
    
    def __init__(self, 
                 input_dirs: List[Path],
                 output_dir: Path,
                 grid_points_path: Path,
                 boundary_path: Path | None = None,
                 weekdays_only: bool = True,
                 filter_days: List[str] | None = None,
                 filter_time_window: Tuple[str, str] | None = None,
                 filter_weeks: List[Tuple[str, str]] | None = None):
        self.input_dirs = input_dirs
        self.output_dir = output_dir
        self.grid_points_path = grid_points_path
        self.boundary_path = boundary_path
        self.weekdays_only = weekdays_only
        self.filter_days = filter_days
        self.filter_time_window = filter_time_window
        self.filter_weeks = filter_weeks
        
        _ensure_dir(output_dir)
        
        # Load grid points for stop assignment
        print("Loading grid points...")
        self.grid_points = _load_grid_points(grid_points_path)
        print(f"  Loaded {len(self.grid_points):,} grid points")
        
        # Load boundary for clipping if provided
        self.boundary = None
        if boundary_path:
            print("Loading boundary...")
            self.boundary = _load_boundary(boundary_path)
            print(f"  Boundary loaded")
        
        # Initialize ID counters for unique IDs across datasets
        self.id_counters = {
            'agency': 1,
            'route': 1,
            'trip': 1,
            'service': 1,
            'stop': 1
        }
        
        # Track ID mappings for each dataset
        self.id_mappings = {}
    
    def process_all(self):
        """Process all GTFS datasets and create unified output."""
        print(f"\nProcessing {len(self.input_dirs)} GTFS dataset(s)...")
        
        processed_datasets = []
        
        for i, gtfs_dir in enumerate(self.input_dirs, 1):
            print(f"\n--- Dataset {i}/{len(self.input_dirs)}: {gtfs_dir.name} ---")
            
            # Validate dataset
            validator = GTFSValidator(gtfs_dir)
            is_valid, errors, warnings = validator.validate()
            
            if warnings:
                for warning in warnings:
                    print(f"  [WARNING] {warning}")
            
            if not is_valid:
                print(f"  [ERROR] Dataset validation failed:")
                for error in errors:
                    print(f"    {error}")
                continue
            
            print(f"  Dataset validation: OK")
            
            # Process this dataset
            dataset_info = self._process_single_dataset(gtfs_dir, i)
            if dataset_info:
                processed_datasets.append(dataset_info)
        
        if not processed_datasets:
            raise RuntimeError("No valid datasets were processed")
        
        print(f"\n--- Merging {len(processed_datasets)} datasets ---")
        self._merge_datasets(processed_datasets)
        
        print(f"\n--- Generating transfers ---")
        self._generate_transfers()
        
        print(f"\nGTFS processing complete!")
        print(f"Output written to: {self.output_dir}")
    
    def _process_single_dataset(self, gtfs_dir: Path, dataset_id: int) -> Dict | None:
        """Process a single GTFS dataset."""
        try:
            # Create temp directory for this dataset
            temp_dir = self.output_dir / "temp" / f"dataset_{dataset_id}"
            _ensure_dir(temp_dir)
            
            # Create unique ID mappings for this dataset
            dataset_prefix = f"d{dataset_id:02d}_"
            self.id_mappings[dataset_id] = {}
            
            # Process each file
            self._process_agency(gtfs_dir, temp_dir, dataset_prefix, dataset_id)
            self._process_routes(gtfs_dir, temp_dir, dataset_prefix, dataset_id)
            self._process_calendar(gtfs_dir, temp_dir, dataset_prefix, dataset_id)
            self._process_trips(gtfs_dir, temp_dir, dataset_prefix, dataset_id)
            stop_info = self._process_stops(gtfs_dir, temp_dir, dataset_prefix, dataset_id)
            self._process_stop_times(gtfs_dir, temp_dir, dataset_prefix, dataset_id)
            
            # Copy optional files if they exist
            for optional_file in OPTIONAL_FILES:
                src_path = gtfs_dir / optional_file
                if src_path.exists() and optional_file != 'transfers.txt':  # We'll generate transfers
                    if optional_file == 'calendar_dates.txt':
                        # Remap service_ids to match processed calendar
                        self._process_calendar_dates(gtfs_dir, temp_dir, dataset_prefix, dataset_id)
                    else:
                        dst_path = temp_dir / optional_file
                        shutil.copy2(src_path, dst_path)
            
            return {
                'dataset_id': dataset_id,
                'temp_dir': temp_dir,
                'stop_info': stop_info,
                'gtfs_dir': gtfs_dir
            }
            
        except Exception as e:
            print(f"  [ERROR] Failed to process dataset: {e}")
            return None
    
    def _process_agency(self, gtfs_dir: Path, temp_dir: Path, prefix: str, dataset_id: int):
        """Process agency.txt with unique IDs."""
        df = pd.read_csv(gtfs_dir / 'agency.txt')
        
        # Create new unique agency IDs
        old_to_new = {}
        for old_id in df['agency_id'].unique():
            new_id = f"{prefix}agency_{self.id_counters['agency']:04d}"
            old_to_new[old_id] = new_id
            self.id_counters['agency'] += 1
        
        self.id_mappings[dataset_id]['agency'] = old_to_new
        
        # Update IDs
        df['agency_id'] = df['agency_id'].map(old_to_new)
        
        # Save
        df.to_csv(temp_dir / 'agency.txt', index=False)
        print(f"  agency.txt: {len(df)} agencies")
    
    def _process_routes(self, gtfs_dir: Path, temp_dir: Path, prefix: str, dataset_id: int):
        """Process routes.txt with unique IDs."""
        df = pd.read_csv(gtfs_dir / 'routes.txt')
        
        # Sanitise route_type: detect hex colour codes from column misalignment
        if 'route_type' in df.columns:
            rt_str = df['route_type'].astype(str)
            hex_mask = rt_str.str.fullmatch(r'[0-9A-Fa-f]{6}', na=False)
            if hex_mask.any():
                n_hex = int(hex_mask.sum())
                if 'route_color' in df.columns:
                    # Swap where route_color holds a plausible route_type int
                    rc_str = df.loc[hex_mask, 'route_color'].astype(str)
                    swap_mask = hex_mask.copy()
                    swap_mask[hex_mask] = rc_str.apply(
                        lambda v: v.isdigit() and int(v) <= 1700
                    ).values
                    if swap_mask.any():
                        orig_rt = df.loc[swap_mask, 'route_type'].copy()
                        df.loc[swap_mask, 'route_type'] = df.loc[swap_mask, 'route_color']
                        df.loc[swap_mask, 'route_color'] = orig_rt
                        print(f"    Fixed {int(swap_mask.sum())} routes: swapped route_type <-> route_color")
                # Default remaining non-numeric route_type to Bus (3)
                still_bad = df['route_type'].astype(str).str.fullmatch(r'[0-9A-Fa-f]{6}', na=False)
                if still_bad.any():
                    df.loc[still_bad, 'route_type'] = 3
                    print(f"    Defaulted {int(still_bad.sum())} routes with invalid route_type to Bus (3)")
            # Ensure route_type is integer
            df['route_type'] = pd.to_numeric(df['route_type'], errors='coerce').fillna(3).astype(int)
        
        # Create new unique route IDs
        old_to_new = {}
        for old_id in df['route_id'].unique():
            new_id = f"{prefix}route_{self.id_counters['route']:05d}"
            old_to_new[old_id] = new_id
            self.id_counters['route'] += 1
        
        self.id_mappings[dataset_id]['route'] = old_to_new
        
        # Update IDs
        df['route_id'] = df['route_id'].map(old_to_new)
        
        # Update agency_id if present
        if 'agency_id' in df.columns and dataset_id in self.id_mappings and 'agency' in self.id_mappings[dataset_id]:
            df['agency_id'] = df['agency_id'].map(self.id_mappings[dataset_id]['agency'])
        
        # Save
        df.to_csv(temp_dir / 'routes.txt', index=False)
        print(f"  routes.txt: {len(df)} routes")
    
    def _process_calendar(self, gtfs_dir: Path, temp_dir: Path, prefix: str, dataset_id: int):
        """Process calendar.txt - filter to specified days and weeks if requested."""
        cal_path = gtfs_dir / 'calendar.txt'
        if cal_path.exists():
            df = pd.read_csv(cal_path, dtype={'service_id': str})
        else:
            # Feed uses calendar_dates.txt only — start with empty calendar
            day_cols = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            df = pd.DataFrame(columns=['service_id'] + day_cols + ['start_date', 'end_date'])
            print(f"  calendar.txt: not present, using calendar_dates.txt only")
        original_count = len(df)
        
        # Filter by days if specified
        if self.filter_days:
            # Create day mask
            day_columns = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            day_mask = df[self.filter_days].sum(axis=1) > 0
            
            # Set non-selected days to 0
            for day in day_columns:
                if day not in self.filter_days:
                    df[day] = 0
                    
            df = df[day_mask].copy()
            print(f"  calendar.txt: filtered to {len(df)} services with {'/'.join(self.filter_days)} (from {original_count})")
        elif self.weekdays_only:
            # Keep only services that run on weekdays
            weekday_mask = (df[['monday', 'tuesday', 'wednesday', 'thursday', 'friday']].sum(axis=1) > 0)
            df = df[weekday_mask].copy()
            
            # Set weekend days to 0
            df[['saturday', 'sunday']] = 0
            
            print(f"  calendar.txt: filtered to {len(df)} weekday services (from {original_count})")
        
        # Filter by reference date if specified
        if self.filter_weeks:
            from datetime import datetime
            valid_services = set()
            
            for item in self.filter_weeks:
                if isinstance(item, tuple) and len(item) == 2:
                    start_date_str, end_date_str = item
                else:
                    # Single date: treat as both start and end
                    start_date_str = end_date_str = str(item)
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                
                # Convert GTFS date format (YYYYMMDD) for comparison
                df['start_date_dt'] = pd.to_datetime(df['start_date'].astype(str), format='%Y%m%d')
                df['end_date_dt'] = pd.to_datetime(df['end_date'].astype(str), format='%Y%m%d')
                
                # Find services that overlap with our target date range
                week_mask = (
                    (df['start_date_dt'] <= pd.Timestamp(end_date)) & 
                    (df['end_date_dt'] >= pd.Timestamp(start_date))
                )
                
                valid_services.update(df[week_mask]['service_id'].tolist())
            
            df = df[df['service_id'].isin(valid_services)].copy()
            df = df.drop(columns=['start_date_dt', 'end_date_dt'], errors='ignore')
            print(f"  calendar.txt: filtered to {len(df)} services active on reference date(s) (from {original_count})")
        
        # Include services defined only in calendar_dates.txt
        cd_path = gtfs_dir / 'calendar_dates.txt'
        if cd_path.exists():
            cd = pd.read_csv(cd_path, dtype={'service_id': str})
            cd_only_services = set(cd['service_id']) - set(df['service_id'])
            if cd_only_services and self.filter_weeks:
                from datetime import datetime as _dt
                # Check which calendar_dates-only services are active on reference dates
                cd_only = cd[cd['service_id'].isin(cd_only_services)].copy()
                cd_only['date_dt'] = pd.to_datetime(cd_only['date'].astype(str), format='%Y%m%d')
                active_cd = set()
                for item in self.filter_weeks:
                    if isinstance(item, tuple) and len(item) == 2:
                        s, e = item
                    else:
                        s = e = str(item)
                    sd = pd.Timestamp(_dt.strptime(s, '%Y-%m-%d'))
                    ed = pd.Timestamp(_dt.strptime(e, '%Y-%m-%d'))
                    mask = (
                        (cd_only['date_dt'] >= sd) & (cd_only['date_dt'] <= ed) &
                        (cd_only['exception_type'] == 1)
                    )
                    active_cd.update(cd_only.loc[mask, 'service_id'].tolist())
                if active_cd:
                    # Create synthetic calendar rows (all days=0, date range = reference date)
                    ref_date_int = int(self.filter_weeks[0][0].replace('-', ''))
                    day_cols = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                    synth = pd.DataFrame({'service_id': list(active_cd)})
                    for col in day_cols:
                        synth[col] = 0
                    synth['start_date'] = ref_date_int
                    synth['end_date'] = ref_date_int
                    df = pd.concat([df, synth], ignore_index=True)
                    print(f"  calendar_dates.txt: added {len(active_cd)} services active on reference date(s)")
            elif cd_only_services and not self.filter_weeks:
                # No date filter: include all calendar_dates-only services
                day_cols = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                synth = pd.DataFrame({'service_id': list(cd_only_services)})
                for col in day_cols:
                    synth[col] = 0
                synth['start_date'] = 20260101
                synth['end_date'] = 20271231
                df = pd.concat([df, synth], ignore_index=True)
                print(f"  calendar_dates.txt: added {len(cd_only_services)} services (no date filter)")
        
        # Create new unique service IDs
        old_to_new = {}
        for old_id in df['service_id'].unique():
            new_id = f"{prefix}service_{self.id_counters['service']:05d}"
            old_to_new[old_id] = new_id
            self.id_counters['service'] += 1
        
        self.id_mappings[dataset_id]['service'] = old_to_new
        
        # Update IDs
        df['service_id'] = df['service_id'].map(old_to_new)
        
        # Save
        df.to_csv(temp_dir / 'calendar.txt', index=False)
    
    def _process_calendar_dates(self, gtfs_dir: Path, temp_dir: Path, prefix: str, dataset_id: int):
        """Process calendar_dates.txt with remapped service IDs."""
        cd_path = gtfs_dir / 'calendar_dates.txt'
        if not cd_path.exists():
            return
        df = pd.read_csv(cd_path, dtype={'service_id': str})
        service_mapping = self.id_mappings[dataset_id].get('service', {})
        # Keep only entries whose service_id survived calendar processing
        df = df[df['service_id'].isin(service_mapping.keys())].copy()
        if len(df) == 0:
            return
        df['service_id'] = df['service_id'].map(service_mapping)
        df.to_csv(temp_dir / 'calendar_dates.txt', index=False)
        print(f"  calendar_dates.txt: {len(df)} entries (remapped)")
    
    def _process_trips(self, gtfs_dir: Path, temp_dir: Path, prefix: str, dataset_id: int):
        """Process trips.txt with unique IDs."""
        df = pd.read_csv(gtfs_dir / 'trips.txt', dtype=str)
        
        # Filter to services we kept in calendar
        if 'service' in self.id_mappings[dataset_id]:
            valid_services = set(self.id_mappings[dataset_id]['service'].keys())
            df = df[df['service_id'].isin(valid_services)].copy()
        
        # Create new unique trip IDs
        old_to_new = {}
        for old_id in df['trip_id'].unique():
            new_id = f"{prefix}trip_{self.id_counters['trip']:06d}"
            old_to_new[old_id] = new_id
            self.id_counters['trip'] += 1
        
        self.id_mappings[dataset_id]['trip'] = old_to_new
        
        # Update IDs
        df['trip_id'] = df['trip_id'].map(old_to_new)
        df['route_id'] = df['route_id'].map(self.id_mappings[dataset_id]['route'])
        df['service_id'] = df['service_id'].map(self.id_mappings[dataset_id]['service'])
        
        # Save
        df.to_csv(temp_dir / 'trips.txt', index=False)
        print(f"  trips.txt: {len(df)} trips")
    
    def _process_stops(self, gtfs_dir: Path, temp_dir: Path, prefix: str, dataset_id: int) -> Dict:
        """Process stops.txt - assign to grid cells and group nearby stops."""
        df = pd.read_csv(gtfs_dir / 'stops.txt')
        
        print(f"  stops.txt: processing {len(df)} stops...")
        
        # Validate coordinates: coerce to numeric and drop invalid rows
        df['stop_lat'] = pd.to_numeric(df['stop_lat'], errors='coerce')
        df['stop_lon'] = pd.to_numeric(df['stop_lon'], errors='coerce')
        valid_mask = (
            df['stop_lat'].notna() & df['stop_lon'].notna() &
            (df['stop_lat'].abs() > 0.1) & (df['stop_lon'].abs() > 0.001) &
            (df['stop_lat'] >= -90) & (df['stop_lat'] <= 90) &
            (df['stop_lon'] >= -180) & (df['stop_lon'] <= 180)
        )
        n_invalid = int((~valid_mask).sum())
        if n_invalid > 0:
            print(f"    Dropping {n_invalid} stops with invalid coordinates")
            df = df[valid_mask].copy()
        
        if len(df) == 0:
            print(f"    WARNING: No valid stops remain after coordinate validation")
            return {'n_stops': 0, 'n_near_grid': 0, 'n_far_grid': 0}
        
        # Convert coordinates to Lambert 93
        stop_x, stop_y = transformer_to_lambert.transform(df['stop_lon'].values, df['stop_lat'].values)
        df['x_lambert'] = stop_x
        df['y_lambert'] = stop_y
        
        # Create GeoDataFrame for spatial operations
        stop_gdf = gpd.GeoDataFrame(
            df, 
            geometry=gpd.points_from_xy(df['x_lambert'], df['y_lambert']), 
            crs=LAMBERT_CRS
        )
        
        # Clip to boundary if provided
        if self.boundary is not None:
            print(f"    Clipping stops to boundary...")
            boundary_geom = self.boundary.geometry.iloc[0]
            stop_gdf = stop_gdf[stop_gdf.intersects(boundary_geom)].copy()
            print(f"    Kept {len(stop_gdf)} stops after clipping")
        
        # Assign each stop to nearest grid cell
        print(f"    Assigning stops to grid cells...")
        grid_coords = np.column_stack([self.grid_points.geometry.x, self.grid_points.geometry.y])
        stop_coords = np.column_stack([stop_gdf['x_lambert'], stop_gdf['y_lambert']])
        
        # Find nearest grid cell for each stop using KDTree (memory-efficient)
        from scipy.spatial import cKDTree
        grid_tree = cKDTree(grid_coords)
        nearest_distances, nearest_indices = grid_tree.query(stop_coords, k=1)
        
        # Assign grid cell coordinates
        stop_gdf['grid_x'] = self.grid_points.geometry.x.iloc[nearest_indices].values
        stop_gdf['grid_y'] = self.grid_points.geometry.y.iloc[nearest_indices].values
        stop_gdf['grid_distance'] = nearest_distances
        
        # Handle stops far from grid cells
        far_stops_mask = stop_gdf['grid_distance'] > MAX_GRID_DISTANCE_M
        far_stops = stop_gdf[far_stops_mask].copy()
        near_stops = stop_gdf[~far_stops_mask].copy()
        
        print(f"    {len(near_stops)} stops within {MAX_GRID_DISTANCE_M}m of grid")
        print(f"    {len(far_stops)} stops need grouping")
        
        # Group far stops using connected-component clustering (same as 02_destination_grid_preparation)
        if len(far_stops) > 0:
            far_x = far_stops['x_lambert'].values
            far_y = far_stops['y_lambert'].values
            cluster_labels = _cluster_labels_within_radius(far_x, far_y, STOP_GROUPING_DISTANCE_M)
            far_stops['cluster'] = cluster_labels
            
            # For each cluster, use centroid as the parent station coordinates
            grouped_stops = []
            for cluster_id in np.unique(cluster_labels):
                cluster_stops = far_stops[far_stops['cluster'] == cluster_id].copy()
                
                # Calculate cluster centroid
                centroid_x = cluster_stops['x_lambert'].mean()
                centroid_y = cluster_stops['y_lambert'].mean()
                
                # Use centroid coordinates for all stops in this cluster
                cluster_stops['parent_x'] = centroid_x
                cluster_stops['parent_y'] = centroid_y
                
                grouped_stops.append(cluster_stops)
            
            far_stops = pd.concat(grouped_stops, ignore_index=True)
            
            # Convert parent coordinates back to WGS84
            parent_lon, parent_lat = transformer_to_wgs84.transform(far_stops['parent_x'].values, far_stops['parent_y'].values)
            far_stops['parent_lon'] = parent_lon
            far_stops['parent_lat'] = parent_lat
        
        # For near stops, use grid coordinates
        near_stops['parent_x'] = near_stops['grid_x']
        near_stops['parent_y'] = near_stops['grid_y']
        parent_lon, parent_lat = transformer_to_wgs84.transform(near_stops['parent_x'].values, near_stops['parent_y'].values)
        near_stops['parent_lon'] = parent_lon
        near_stops['parent_lat'] = parent_lat
        
        # Combine all stops
        all_stops = pd.concat([near_stops.drop(columns=['cluster'], errors='ignore'), 
                               far_stops.drop(columns=['cluster'], errors='ignore')], ignore_index=True)
        
        # Create new unique stop IDs
        old_to_new = {}
        for old_id in all_stops['stop_id'].unique():
            new_id = f"{prefix}stop_{self.id_counters['stop']:06d}"
            old_to_new[old_id] = new_id
            self.id_counters['stop'] += 1
        
        self.id_mappings[dataset_id]['stop'] = old_to_new
        
        # Update IDs
        all_stops['stop_id'] = all_stops['stop_id'].map(old_to_new)
        
        # Create parent_station column with routing coordinates
        all_stops['parent_station'] = all_stops['stop_id'] + "_PS"  # Parent station IDs
        
        # Prepare final output (keep original GTFS columns + our additions)
        gtfs_columns = ['stop_id', 'stop_code', 'stop_name', 'stop_lat', 'stop_lon', 'zone_id', 
                        'stop_url', 'location_type', 'parent_station', 'wheelchair_boarding']
        
        # Keep only columns that exist in the original data plus our additions
        keep_columns = [col for col in gtfs_columns if col in all_stops.columns]
        keep_columns.extend(['parent_lon', 'parent_lat', 'parent_x', 'parent_y', 'grid_distance'])
        
        output_df = all_stops[keep_columns].copy()
        
        # Save
        output_df.to_csv(temp_dir / 'stops.txt', index=False)
        print(f"    Processed {len(output_df)} stops with parent coordinates")
        
        return {
            'stops_df': output_df,
            'stops_with_grid': len(near_stops),
            'stops_grouped': len(far_stops) if len(far_stops) > 0 else 0
        }
    
    def _process_stop_times(self, gtfs_dir: Path, temp_dir: Path, prefix: str, dataset_id: int):
        """Process stop_times.txt with updated IDs and time filtering."""
        print(f"  stop_times.txt: processing...")
        
        # Use smaller chunks for large files
        chunk_size = 50000
        output_path = temp_dir / 'stop_times.txt'
        wrote_header = False
        
        trip_mapping = self.id_mappings[dataset_id]['trip']
        stop_mapping = self.id_mappings[dataset_id]['stop']
        total_rows = 0
        filtered_trips = set()  # Track trips that have stop_times in our time window
        
        # Parse time filter if specified
        filter_start_seconds = None
        filter_end_seconds = None
        if self.filter_time_window:
            filter_start_seconds = _parse_time_to_seconds(self.filter_time_window[0])
            filter_end_seconds = _parse_time_to_seconds(self.filter_time_window[1])
            print(f"    Filtering to time window: {self.filter_time_window[0]} - {self.filter_time_window[1]}")
        
        try:
            for chunk_idx, chunk in enumerate(pd.read_csv(gtfs_dir / 'stop_times.txt', chunksize=chunk_size, dtype=str), 1):
                # Filter to trips we kept
                chunk = chunk[chunk['trip_id'].isin(trip_mapping.keys())].copy()
                
                if len(chunk) == 0:
                    continue
                
                # Apply time window filter if specified
                if filter_start_seconds is not None and filter_end_seconds is not None:
                    # Parse arrival and departure times
                    chunk['arrival_seconds'] = chunk['arrival_time'].apply(_parse_time_to_seconds)
                    chunk['departure_seconds'] = chunk['departure_time'].apply(_parse_time_to_seconds)
                    
                    # Keep only records within time window
                    time_mask = (
                        (chunk['arrival_seconds'] >= filter_start_seconds) & 
                        (chunk['arrival_seconds'] <= filter_end_seconds)
                    ) | (
                        (chunk['departure_seconds'] >= filter_start_seconds) & 
                        (chunk['departure_seconds'] <= filter_end_seconds)
                    )
                    
                    chunk = chunk[time_mask].copy()
                    chunk = chunk.drop(columns=['arrival_seconds', 'departure_seconds'], errors='ignore')
                    
                    if len(chunk) == 0:
                        continue
                
                # Track trips that have stop_times in our filtered set
                filtered_trips.update(chunk['trip_id'].unique())
                
                # Update IDs
                chunk['trip_id'] = chunk['trip_id'].map(trip_mapping)
                chunk['stop_id'] = chunk['stop_id'].map(stop_mapping)
                
                # Save chunk
                chunk.to_csv(output_path, mode='a', header=not wrote_header, index=False)
                wrote_header = True
                total_rows += len(chunk)
                
                # Progress update for large files
                if chunk_idx % 10 == 0:
                    print(f"    Processed {chunk_idx} chunks, {total_rows:,} rows so far...")
        
        except Exception as e:
            print(f"    Error processing stop_times.txt: {e}")
            print(f"    Trying alternative approach...")
            
            # Fallback: load entire file (for smaller datasets)
            try:
                df = pd.read_csv(gtfs_dir / 'stop_times.txt', dtype=str)
                df = df[df['trip_id'].isin(trip_mapping.keys())].copy()
                
                # Apply time filter
                if filter_start_seconds is not None and filter_end_seconds is not None:
                    df['arrival_seconds'] = df['arrival_time'].apply(_parse_time_to_seconds)
                    df['departure_seconds'] = df['departure_time'].apply(_parse_time_to_seconds)
                    
                    time_mask = (
                        (df['arrival_seconds'] >= filter_start_seconds) & 
                        (df['arrival_seconds'] <= filter_end_seconds)
                    ) | (
                        (df['departure_seconds'] >= filter_start_seconds) & 
                        (df['departure_seconds'] <= filter_end_seconds)
                    )
                    
                    df = df[time_mask].copy()
                    df = df.drop(columns=['arrival_seconds', 'departure_seconds'], errors='ignore')
                
                if len(df) > 0:
                    filtered_trips.update(df['trip_id'].unique())
                    df['trip_id'] = df['trip_id'].map(trip_mapping)
                    df['stop_id'] = df['stop_id'].map(stop_mapping)
                    df.to_csv(output_path, index=False)
                    total_rows = len(df)
                else:
                    print(f"    Warning: No valid stop_times found")
            except Exception as e2:
                print(f"    Fallback also failed: {e2}")
                raise
        
        if self.filter_time_window:
            print(f"    Processed {total_rows:,} stop times (filtered by time window)")
            print(f"    {len(filtered_trips)} trips have stops in the time window")
            
            # Update trip mapping to only include trips with stop_times in time window
            original_trip_mapping = self.id_mappings[dataset_id]['trip'].copy()
            filtered_trip_mapping = {k: v for k, v in original_trip_mapping.items() if k in filtered_trips}
            self.id_mappings[dataset_id]['trip'] = filtered_trip_mapping
            
            # Re-read and filter trips.txt to match
            self._refilter_trips_by_stop_times(temp_dir, filtered_trips, prefix, dataset_id)
        else:
            print(f"    Processed {total_rows:,} stop times")
    
    def _refilter_trips_by_stop_times(self, temp_dir: Path, filtered_trips: set, prefix: str, dataset_id: int):
        """Re-filter trips.txt to only include trips that have stop_times in our filtered set."""
        trips_file = temp_dir / 'trips.txt'
        if trips_file.exists():
            df = pd.read_csv(trips_file)
            # The trip_id in the file is already mapped to new IDs, so we need to reverse map
            old_to_new = self.id_mappings[dataset_id]['trip']
            new_to_old = {v: k for k, v in old_to_new.items()}
            
            # Filter to only trips that have stop_times
            df['old_trip_id'] = df['trip_id'].map(new_to_old)
            df = df[df['old_trip_id'].isin(filtered_trips)].copy()
            df = df.drop(columns=['old_trip_id'])
            
            df.to_csv(trips_file, index=False)
            print(f"    Filtered trips.txt to {len(df)} trips (have stop_times in time window)")
    
    def _merge_datasets(self, processed_datasets: List[Dict]):
        """Merge all processed datasets into final GTFS.

        Small files use pd.concat for proper column alignment.
        Large files (stop_times, shapes) stream with a two-pass approach:
        first collect the union of columns, then write with consistent headers.
        """
        print("  Merging GTFS files...")
        
        # Files to merge — separate small vs large
        small_files = ['agency.txt', 'stops.txt', 'routes.txt', 'trips.txt',
                       'calendar.txt', 'calendar_dates.txt']
        large_files = ['stop_times.txt', 'shapes.txt']
        
        for gtfs_file in small_files:
            output_path = self.output_dir / gtfs_file
            dfs = []
            
            for dataset_info in processed_datasets:
                temp_file = dataset_info['temp_dir'] / gtfs_file
                if temp_file.exists():
                    dfs.append(pd.read_csv(temp_file, low_memory=False))
            
            if dfs:
                merged = pd.concat(dfs, ignore_index=True)
                merged.to_csv(output_path, index=False)
                print(f"    {gtfs_file}: {len(merged):,} rows")
        
        for gtfs_file in large_files:
            output_path = self.output_dir / gtfs_file
            # Pass 1: collect union of all column names
            all_columns = []
            source_files = []
            for dataset_info in processed_datasets:
                temp_file = dataset_info['temp_dir'] / gtfs_file
                if temp_file.exists():
                    header = pd.read_csv(temp_file, nrows=0).columns.tolist()
                    for col in header:
                        if col not in all_columns:
                            all_columns.append(col)
                    source_files.append(temp_file)
            
            if not source_files:
                continue
            
            # Pass 2: stream each file with aligned columns
            total_rows = 0
            with open(output_path, 'w', newline='', encoding='utf-8') as out_f:
                out_f.write(','.join(all_columns) + '\n')
                for temp_file in source_files:
                    for chunk in pd.read_csv(temp_file, chunksize=100_000, low_memory=False):
                        # Reindex to ensure all columns present and aligned
                        chunk = chunk.reindex(columns=all_columns)
                        chunk.to_csv(out_f, header=False, index=False)
                        total_rows += len(chunk)
            print(f"    {gtfs_file}: {total_rows:,} rows (streamed)")
        
        # Clean up temp directories
        temp_base = self.output_dir / "temp"
        if temp_base.exists():
            shutil.rmtree(temp_base)
    
    def _generate_transfers(self):
        """Generate transfers.txt based on stop locations and types."""
        print("  Generating transfers.txt...")
        
        # Load stops to analyze
        stops_df = pd.read_csv(self.output_dir / 'stops.txt')
        
        if 'parent_lon' not in stops_df.columns:
            print("    Warning: No parent coordinates found, skipping transfer generation")
            return
        
        transfers = []
        
        # Convert to Lambert for distance calculations
        stop_x, stop_y = transformer_to_lambert.transform(stops_df['parent_lon'].values, stops_df['parent_lat'].values)
        stops_df['x_lambert'] = stop_x
        stops_df['y_lambert'] = stop_y
        
        # Group stops by parent station (same routing coordinates)
        grouped = stops_df.groupby(['parent_lon', 'parent_lat'])
        
        for (parent_lon, parent_lat), group in grouped:
            if len(group) < 2:
                continue
                
            # Same parent station - allow transfers (transfer_type = 2, min_transfer_time = 2min)
            stop_ids = group['stop_id'].tolist()
            for i, from_stop in enumerate(stop_ids):
                for to_stop in stop_ids[i+1:]:
                    transfers.append({
                        'from_stop_id': from_stop,
                        'to_stop_id': to_stop,
                        'transfer_type': 2,  # Timed transfer
                        'min_transfer_time': DEFAULT_TRANSFER_TIME_S
                    })
                    transfers.append({
                        'from_stop_id': to_stop,
                        'to_stop_id': from_stop,
                        'transfer_type': 2,
                        'min_transfer_time': DEFAULT_TRANSFER_TIME_S
                    })
        
        # Distance-based transfers between different parent stations
        print("    Computing distance-based transfers...")
        unique_parents = stops_df.drop_duplicates(['parent_lon', 'parent_lat'])
        
        if len(unique_parents) > 1:
            coords = np.column_stack([unique_parents['x_lambert'], unique_parents['y_lambert']])
            
            # Use KDTree for efficient radius-based neighbor search (memory-efficient)
            from scipy.spatial import cKDTree
            tree = cKDTree(coords)
            pairs = tree.query_pairs(r=300)  # Max 300m for walking transfers
            
            parent_keys = list(zip(unique_parents['parent_lon'], unique_parents['parent_lat']))
            parent_to_stops = {}
            for key in parent_keys:
                parent_to_stops[key] = stops_df[
                    (stops_df['parent_lon'] == key[0]) & 
                    (stops_df['parent_lat'] == key[1])
                ]['stop_id'].tolist()
            
            for i, j in pairs:
                distance = np.linalg.norm(coords[i] - coords[j])
                walk_time_s = max(120, int(distance / WALK_SPEED_MS) + 60)  # Min 2min, add 1min buffer
                
                from_stops = parent_to_stops[parent_keys[i]]
                to_stops = parent_to_stops[parent_keys[j]]
                
                for from_stop in from_stops:
                    for to_stop in to_stops:
                        transfers.append({
                            'from_stop_id': from_stop,
                            'to_stop_id': to_stop,
                            'transfer_type': 2,
                            'min_transfer_time': walk_time_s
                        })
                        transfers.append({
                            'from_stop_id': to_stop,
                            'to_stop_id': from_stop,
                            'transfer_type': 2,
                            'min_transfer_time': walk_time_s
                        })
        
        # Save transfers.txt
        if transfers:
            transfers_df = pd.DataFrame(transfers)
            transfers_df.to_csv(self.output_dir / 'transfers.txt', index=False)
            print(f"    Generated {len(transfers_df):,} transfers")
        else:
            print("    No transfers generated")


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Prepare GTFS data for OpenTripPlanner routing",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--input-dirs",
        nargs="+",
        type=Path,
        default=None,
        help="One or more GTFS directories to process (default: auto-discover from --gtfs-root)"
    )
    
    parser.add_argument(
        "--gtfs-root",
        type=Path,
        default=GTFS_ROOT_DIR,
        help=f"Root directory with NUTS2 GTFS subfolders (default: {GTFS_ROOT_DIR})"
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/gtfs_processed"),
        help="Output directory for processed GTFS (default: data/gtfs_processed)"
    )
    
    parser.add_argument(
        "--grid-points",
        type=Path,
        default=Path("outputs/00_data_import_preparation/filosofi_grid_points.gpkg"),
        help="Grid points GeoPackage for stop assignment"
    )
    
    parser.add_argument(
        "--boundary",
        type=Path,
        help="Boundary GeoJSON for clipping stops (optional)"
    )
    
    parser.add_argument(
        "--include-weekends",
        action="store_true",
        help="Include weekend services (default: weekdays only)"
    )
    
    parser.add_argument(
        "--max-grid-distance",
        type=int,
        default=MAX_GRID_DISTANCE_M,
        help=f"Max distance (m) to assign stop to grid cell (default: {MAX_GRID_DISTANCE_M})"
    )
    
    parser.add_argument(
        "--grouping-distance", 
        type=int,
        default=STOP_GROUPING_DISTANCE_M,
        help=f"Distance (m) for grouping nearby stops (default: {STOP_GROUPING_DISTANCE_M})"
    )
    
    # Filtering options
    parser.add_argument(
        "--reference-date",
        type=str,
        default=DATE_DEFAULT,
        help=f"Reference date for service filtering, YYYY-MM-DD (default: {DATE_DEFAULT})"
    )
    
    parser.add_argument(
        "--filter-time-window",
        nargs=2,
        metavar=("START_TIME", "END_TIME"),
        default=list(TIME_WINDOW_DEFAULT),
        help=f"Departure time window HH:MM:SS (default: {TIME_WINDOW_DEFAULT[0]} {TIME_WINDOW_DEFAULT[1]})"
    )
    
    parser.add_argument(
        "--filter-days",
        nargs="*",
        choices=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        help="Filter to specific days of week (e.g., --filter-days tuesday thursday)"
    )
    
    parser.add_argument(
        "--no-time-filter",
        action="store_true",
        help="Disable default time-window filtering"
    )
    
    parser.add_argument(
        "--no-date-filter",
        action="store_true",
        help="Disable default reference-date filtering"
    )
    
    return parser


def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    
    try:
        # Convert relative paths to absolute
        root = ROOT_DIR
        output_dir = root / args.output_dir if not args.output_dir.is_absolute() else args.output_dir
        grid_points = root / args.grid_points if not args.grid_points.is_absolute() else args.grid_points
        boundary = root / args.boundary if args.boundary and not args.boundary.is_absolute() else args.boundary
        gtfs_root = root / args.gtfs_root if not args.gtfs_root.is_absolute() else args.gtfs_root
        
        # Discover or validate input directories
        if args.input_dirs:
            input_dirs = [root / path if not path.is_absolute() else path for path in args.input_dirs]
            for gtfs_dir in input_dirs:
                if not gtfs_dir.exists():
                    raise FileNotFoundError(f"GTFS directory not found: {gtfs_dir}")
                if not gtfs_dir.is_dir():
                    raise NotADirectoryError(f"Not a directory: {gtfs_dir}")
        else:
            print(f"Auto-discovering GTFS feeds under: {gtfs_root}")
            input_dirs = _discover_gtfs_feeds(gtfs_root)
            if not input_dirs:
                raise FileNotFoundError(f"No GTFS feeds found under: {gtfs_root}")
            print(f"Found {len(input_dirs)} GTFS feed(s)")
        
        # Set global parameters
        global MAX_GRID_DISTANCE_M, STOP_GROUPING_DISTANCE_M
        MAX_GRID_DISTANCE_M = args.max_grid_distance
        STOP_GROUPING_DISTANCE_M = args.grouping_distance
        
        # Build filtering parameters from new defaults
        filter_days = args.filter_days if args.filter_days else None
        
        filter_time_window = None
        if not args.no_time_filter:
            filter_time_window = tuple(args.filter_time_window)
        
        filter_weeks = None
        if not args.no_date_filter and args.reference_date:
            # Use reference date as a single-day range
            filter_weeks = [(args.reference_date, args.reference_date)]
        
        print("GTFS Public Transport Preprocessing")
        print("=" * 50)
        print(f"Input datasets: {len(input_dirs)}")
        for i, gtfs_dir in enumerate(input_dirs, 1):
            print(f"  {i}. {gtfs_dir}")
        print(f"Output directory: {output_dir}")
        print(f"Grid points: {grid_points}")
        if boundary:
            print(f"Boundary: {boundary}")
        print(f"Weekend services: {'included' if args.include_weekends else 'excluded'}")
        if args.reference_date and not args.no_date_filter:
            print(f"Reference date: {args.reference_date}")
        if filter_days:
            print(f"Day filter: {', '.join(filter_days)}")
        if filter_time_window:
            print(f"Time filter: {filter_time_window[0]} - {filter_time_window[1]}")
        print(f"Max grid distance: {MAX_GRID_DISTANCE_M}m")
        print(f"Stop grouping distance: {STOP_GROUPING_DISTANCE_M}m")
        print()
        
        # Process GTFS data
        processor = GTFSProcessor(
            input_dirs=input_dirs,
            output_dir=output_dir,
            grid_points_path=grid_points,
            boundary_path=boundary,
            weekdays_only=not args.include_weekends,
            filter_days=filter_days,
            filter_time_window=filter_time_window,
            filter_weeks=filter_weeks
        )
        
        processor.process_all()
        
    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user.")
        print("Partial results may be available in the output directory.")
    except Exception as e:
        print(f"\n\nError during processing: {e}")
        import traceback
        traceback.print_exc()
        print("\nFor large GTFS files, try processing datasets individually.")


if __name__ == "__main__":
    main()