#!/usr/bin/env python3
"""Phase 7: Evaluation pipeline against Google Maps Routes API.

Scope implemented in this file:
- Phase A: Build comparable O-D candidates from existing model outputs
- Phase B: Stratified random sampling (default: 100 O-D per mode)
- Phase C: Query Google Maps Routes API at fixed departure times
- Plotting: Scatter plots per mode x departure hour (x=model, y=Google)

Not implemented here (by design):
- Full Phase D metrics (MAE/RMSE/MAPE/...) in a separate file
"""

from __future__ import annotations

import argparse
import logging
import math
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import duckdb
import matplotlib.pyplot as plt
import pandas as pd
import requests
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parent.parent

DEFAULT_GRID_CSV = ROOT_DIR / "outputs" / "01_data_import_preparation" / "filosofi_grid_points.csv"
DEFAULT_GRID_ID_COL = "idcar_200m"

DEFAULT_WALK_MATRIX = ROOT_DIR / "outputs" / "03_car_bike_walk_accessibility" / "foot_grid_45min_fast.parquet"
DEFAULT_BIKE_MATRIX = ROOT_DIR / "outputs" / "03_car_bike_walk_accessibility" / "bicycle_grid_45min_fast.parquet"
DEFAULT_CAR_MATRIX = ROOT_DIR / "outputs" / "03_car_bike_walk_accessibility" / "car_grid_45min_fast.parquet"
DEFAULT_PT_DB = ROOT_DIR / "outputs" / "05_public_transit_od_matrix" / "pt_od_build.duckdb"

DEFAULT_OUTPUT_DIR = ROOT_DIR / "outputs" / "07_evaluation_pipeline"
DEFAULT_DATE = "2026-03-18"  # aligned with Phase 4 default
DEFAULT_TIMES = ["07:00", "08:20"]
DEFAULT_TIMEZONE = "Europe/Paris"
DEFAULT_SAMPLE_PER_MODE = 100
DEFAULT_SEED = 42
DEFAULT_MAX_CANDIDATE_ROWS = 250_000
DEFAULT_API_KEY_ENV = "GOOGLE_MAPS_API_KEY"
DEFAULT_REQUESTS_PER_SECOND = 5.0
DEFAULT_TIMEOUT_S = 30
DEFAULT_MAX_RETRIES = 3

GOOGLE_ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModeSpec:
    mode: str
    source_type: str  # road | pt
    travel_mode: str  # Google API mode
    source_path: Path


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT_DIR / path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 7 evaluation pipeline (sampling + Google API + plots)")

    parser.add_argument("--grid-csv", type=Path, default=DEFAULT_GRID_CSV)
    parser.add_argument("--grid-id-col", type=str, default=DEFAULT_GRID_ID_COL)

    parser.add_argument("--walk-matrix", type=Path, default=DEFAULT_WALK_MATRIX)
    parser.add_argument("--bike-matrix", type=Path, default=DEFAULT_BIKE_MATRIX)
    parser.add_argument("--car-matrix", type=Path, default=DEFAULT_CAR_MATRIX)
    parser.add_argument("--pt-db", type=Path, default=DEFAULT_PT_DB)

    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--sample-per-mode", type=int, default=DEFAULT_SAMPLE_PER_MODE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--max-candidate-rows", type=int, default=DEFAULT_MAX_CANDIDATE_ROWS)

    parser.add_argument("--departure-date", type=str, default=DEFAULT_DATE)
    parser.add_argument("--departure-times", nargs="+", default=DEFAULT_TIMES)
    parser.add_argument("--timezone", type=str, default=DEFAULT_TIMEZONE)

    parser.add_argument("--api-key", type=str, default="")
    parser.add_argument("--api-key-env", type=str, default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--requests-per-second", type=float, default=DEFAULT_REQUESTS_PER_SECOND)
    parser.add_argument("--timeout-s", type=int, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)

    parser.add_argument("--skip-api", action="store_true", help="Only build samples + request table, skip Google calls")
    parser.add_argument("--skip-plots", action="store_true", help="Skip scatter plot generation")
    parser.add_argument("--resume", action="store_true", help="Resume API calls from existing results file")

    return parser.parse_args()


def _validate_inputs(args: argparse.Namespace) -> None:
    for path in [args.grid_csv, args.walk_matrix, args.bike_matrix, args.car_matrix, args.pt_db]:
        if not path.exists():
            raise FileNotFoundError(f"Missing required input: {path}")

    if args.sample_per_mode <= 0:
        raise ValueError("--sample-per-mode must be > 0")
    if args.max_candidate_rows <= 0:
        raise ValueError("--max-candidate-rows must be > 0")
    if args.requests_per_second <= 0:
        raise ValueError("--requests-per-second must be > 0")
    if args.timeout_s <= 0:
        raise ValueError("--timeout-s must be > 0")
    if args.max_retries < 1:
        raise ValueError("--max-retries must be >= 1")

    datetime.strptime(args.departure_date, "%Y-%m-%d")
    for t in args.departure_times:
        datetime.strptime(t, "%H:%M")


def _load_grid_coords(grid_csv: Path, grid_id_col: str) -> pd.DataFrame:
    logger.info("Loading grid coordinates: %s", grid_csv)
    grid_df = pd.read_csv(grid_csv, usecols=[grid_id_col, "lon", "lat"])
    grid_df = grid_df.rename(columns={grid_id_col: "grid_id"}).copy()
    grid_df["grid_id"] = grid_df["grid_id"].astype(str)
    grid_df = grid_df.dropna(subset=["grid_id", "lon", "lat"]).drop_duplicates(subset=["grid_id"])
    return grid_df


def _duration_bin_series(s: pd.Series) -> pd.Series:
    # Fixed bins in minutes: <=15, <=30, <=45, <=60, >60
    edges = [-float("inf"), 900, 1800, 2700, 3600, float("inf")]
    labels = ["0-15", "15-30", "30-45", "45-60", "60+"]
    return pd.cut(s, bins=edges, labels=labels, include_lowest=True)


def _stratified_sample(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    if len(df) <= n:
        return df.sample(frac=1.0, random_state=seed).reset_index(drop=True)

    work = df.copy()
    work["duration_bin"] = _duration_bin_series(work["model_duration_s"])
    work["duration_bin"] = work["duration_bin"].astype(str)

    counts = work.groupby("duration_bin", dropna=False).size().sort_index()
    total = int(counts.sum())

    # Proportional allocation, then adjust to match n exactly
    alloc = {k: int(round(n * (v / total))) for k, v in counts.items()}

    # Enforce upper bound by available rows
    for k in list(alloc):
        alloc[k] = min(alloc[k], int(counts[k]))

    allocated = sum(alloc.values())

    # Fill deficit from bins with remaining capacity
    if allocated < n:
        deficit = n - allocated
        remaining = sorted(
            [(k, int(counts[k]) - alloc[k]) for k in counts.index],
            key=lambda x: x[1],
            reverse=True,
        )
        i = 0
        while deficit > 0 and remaining:
            k, cap = remaining[i % len(remaining)]
            if cap > 0:
                alloc[k] += 1
                deficit -= 1
                remaining[i % len(remaining)] = (k, cap - 1)
            i += 1
            if i > 10_000:
                break

    # Trim overflow if needed
    if allocated > n:
        overflow = allocated - n
        for k, _ in sorted(alloc.items(), key=lambda x: x[1], reverse=True):
            take = min(overflow, max(0, alloc[k] - 1))
            alloc[k] -= take
            overflow -= take
            if overflow == 0:
                break

    chunks: list[pd.DataFrame] = []
    for i, (bin_name, amount) in enumerate(alloc.items()):
        if amount <= 0:
            continue
        part = work[work["duration_bin"] == bin_name]
        if part.empty:
            continue
        chunks.append(part.sample(n=amount, random_state=seed + i))

    sampled = pd.concat(chunks, axis=0, ignore_index=True)

    if len(sampled) > n:
        sampled = sampled.sample(n=n, random_state=seed)
    elif len(sampled) < n:
        leftovers = work.drop(index=sampled.index, errors="ignore")
        needed = n - len(sampled)
        if needed > 0 and not leftovers.empty:
            sampled = pd.concat(
                [sampled, leftovers.sample(n=min(needed, len(leftovers)), random_state=seed + 123)],
                axis=0,
                ignore_index=True,
            )

    return sampled.drop(columns=["duration_bin"], errors="ignore").reset_index(drop=True)


def _fetch_road_candidates(
    con: duckdb.DuckDBPyConnection,
    grid_coords: pd.DataFrame,
    matrix_path: Path,
    max_candidate_rows: int,
    sample_seed: int,
) -> pd.DataFrame:
    con.register("grid_coords", grid_coords)
    
    # Detect file type and use appropriate reader
    path_str = str(matrix_path)
    if path_str.endswith('.parquet'):
        read_expr = f"read_parquet('{path_str}')"
    else:
        # CSV/gzipped CSV
        read_expr = f"""read_csv_auto(
            '{path_str}',
            header=true,
            compression='gzip',
            delim=',',
            quote='"',
            strict_mode=false,
            null_padding=true
        )"""

    sql = f"""
        WITH road_raw AS (
            SELECT
                CAST(origin_id AS VARCHAR) AS origin_id,
                CAST(dest_id AS VARCHAR) AS dest_id,
                TRY_CAST(duration_s AS DOUBLE) AS model_duration_s
            FROM {read_expr}
            WHERE origin_id IS NOT NULL
              AND dest_id IS NOT NULL
              AND TRY_CAST(duration_s AS DOUBLE) IS NOT NULL
              AND TRY_CAST(duration_s AS DOUBLE) >= 0
              AND CAST(origin_id AS VARCHAR) <> CAST(dest_id AS VARCHAR)
        ),
        sampled AS (
            SELECT *
            FROM road_raw
            USING SAMPLE reservoir({max_candidate_rows} ROWS) REPEATABLE({sample_seed})
        )
        SELECT
            s.origin_id,
            s.dest_id,
            s.model_duration_s,
            go.lat AS origin_lat,
            go.lon AS origin_lon,
            gd.lat AS dest_lat,
            gd.lon AS dest_lon
        FROM sampled s
        JOIN grid_coords go ON go.grid_id = s.origin_id
        JOIN grid_coords gd ON gd.grid_id = s.dest_id
    """
    return con.execute(sql).fetchdf()


def _fetch_pt_candidates(
    con: duckdb.DuckDBPyConnection,
    grid_coords: pd.DataFrame,
    pt_db_path: Path,
    max_candidate_rows: int,
    sample_seed: int,
) -> pd.DataFrame:
    con.register("grid_coords", grid_coords)
    pt_db_literal = str(pt_db_path).replace("'", "''")
    con.execute(f"ATTACH '{pt_db_literal}' AS ptdb")
    try:
        has_best_od_idx = bool(
            con.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_catalog='ptdb' AND table_schema='main' AND table_name='best_od_idx'
                """
            ).fetchone()[0]
        )
        has_best_od = bool(
            con.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_catalog='ptdb' AND table_schema='main' AND table_name='best_od'
                """
            ).fetchone()[0]
        )
        has_grid_dict = bool(
            con.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_catalog='ptdb' AND table_schema='main' AND table_name='grid_dict'
                """
            ).fetchone()[0]
        )

        pt_raw_sql: str
        if has_best_od_idx and has_grid_dict:
            pt_raw_sql = """
                SELECT
                    go.grid_id AS origin_id,
                    gd.grid_id AS dest_id,
                    CAST(b.total_s AS DOUBLE) AS model_duration_s
                FROM ptdb.main.best_od_idx b
                JOIN ptdb.main.grid_dict go ON go.grid_idx = b.origin_grid_idx
                JOIN ptdb.main.grid_dict gd ON gd.grid_idx = b.dest_grid_idx
                WHERE b.total_s IS NOT NULL
                  AND b.total_s >= 0
                  AND go.grid_id IS NOT NULL
                  AND gd.grid_id IS NOT NULL
                  AND go.grid_id <> gd.grid_id
            """
        elif has_best_od and has_grid_dict:
            pt_raw_sql = """
                SELECT
                    go.grid_id AS origin_id,
                    gd.grid_id AS dest_id,
                    CAST(b.total_s AS DOUBLE) AS model_duration_s
                FROM ptdb.main.best_od b
                JOIN ptdb.main.grid_dict go ON go.grid_idx = b.origin_grid
                JOIN ptdb.main.grid_dict gd ON gd.grid_idx = b.dest_grid
                WHERE b.total_s IS NOT NULL
                  AND b.total_s >= 0
                  AND go.grid_id IS NOT NULL
                  AND gd.grid_id IS NOT NULL
                  AND go.grid_id <> gd.grid_id
            """
        elif has_grid_dict:
            pt_final_path = pt_db_path.with_name("pt_od_final.duckdb")
            if not pt_final_path.exists():
                raise RuntimeError(
                    "PT DB compatibility error: found grid_dict but neither best_od_idx nor best_od, "
                    f"and fallback file not found: {pt_final_path}"
                )
            pt_final_literal = str(pt_final_path).replace("'", "''")
            con.execute(f"ATTACH '{pt_final_literal}' AS ptfinal")
            has_best_od_final = bool(
                con.execute(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_catalog='ptfinal' AND table_schema='main' AND table_name='best_od'
                    """
                ).fetchone()[0]
            )
            if not has_best_od_final:
                con.execute("DETACH ptfinal")
                raise RuntimeError(f"Fallback PT final DB missing best_od table: {pt_final_path}")

            pt_raw_sql = """
                SELECT
                    go.grid_id AS origin_id,
                    gd.grid_id AS dest_id,
                    CAST(b.total_s AS DOUBLE) AS model_duration_s
                FROM ptfinal.main.best_od b
                JOIN ptdb.main.grid_dict go ON go.grid_idx = b.origin_grid
                JOIN ptdb.main.grid_dict gd ON gd.grid_idx = b.dest_grid
                WHERE b.total_s IS NOT NULL
                  AND b.total_s >= 0
                  AND go.grid_id IS NOT NULL
                  AND gd.grid_id IS NOT NULL
                  AND go.grid_id <> gd.grid_id
            """
        else:
            raise RuntimeError(
                "PT DB compatibility error: expected one of [best_od_idx + grid_dict] or [best_od + grid_dict]."
            )

        sql = f"""
            WITH pt_raw AS (
                {pt_raw_sql}
            ),
            sampled AS (
                SELECT *
                FROM pt_raw
                USING SAMPLE reservoir({max_candidate_rows} ROWS) REPEATABLE({sample_seed})
            )
            SELECT
                s.origin_id,
                s.dest_id,
                s.model_duration_s,
                go.lat AS origin_lat,
                go.lon AS origin_lon,
                gd.lat AS dest_lat,
                gd.lon AS dest_lon
            FROM sampled s
            JOIN grid_coords go ON go.grid_id = s.origin_id
            JOIN grid_coords gd ON gd.grid_id = s.dest_id
        """

        out = con.execute(sql).fetchdf()
        if bool(
            con.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_catalog='ptfinal' AND table_schema='main'
                """
            ).fetchone()[0]
        ):
            con.execute("DETACH ptfinal")
        return out
    finally:
        con.execute("DETACH ptdb")


def _build_samples(args: argparse.Namespace, grid_coords: pd.DataFrame) -> pd.DataFrame:
    specs = [
        ModeSpec(mode="walk", source_type="road", travel_mode="WALK", source_path=args.walk_matrix),
        ModeSpec(mode="bicycle", source_type="road", travel_mode="BICYCLE", source_path=args.bike_matrix),
        ModeSpec(mode="car", source_type="road", travel_mode="DRIVE", source_path=args.car_matrix),
        ModeSpec(mode="public_transport", source_type="pt", travel_mode="TRANSIT", source_path=args.pt_db),
    ]

    con = duckdb.connect(":memory:")
    mode_samples: list[pd.DataFrame] = []

    for idx, spec in enumerate(specs):
        logger.info("Building candidate pool for mode=%s", spec.mode)
        if spec.source_type == "road":
            candidates = _fetch_road_candidates(
                con=con,
                grid_coords=grid_coords,
                matrix_path=spec.source_path,
                max_candidate_rows=args.max_candidate_rows,
                sample_seed=args.seed + idx,
            )
        else:
            candidates = _fetch_pt_candidates(
                con=con,
                grid_coords=grid_coords,
                pt_db_path=spec.source_path,
                max_candidate_rows=args.max_candidate_rows,
                sample_seed=args.seed + idx,
            )

        if candidates.empty:
            raise RuntimeError(f"No valid candidates available for mode={spec.mode}")

        sampled = _stratified_sample(candidates, n=args.sample_per_mode, seed=args.seed + 10 * (idx + 1))
        sampled["mode"] = spec.mode
        sampled["google_travel_mode"] = spec.travel_mode
        sampled["sample_rank"] = range(1, len(sampled) + 1)

        cols = [
            "mode",
            "google_travel_mode",
            "sample_rank",
            "origin_id",
            "dest_id",
            "model_duration_s",
            "origin_lat",
            "origin_lon",
            "dest_lat",
            "dest_lon",
        ]
        mode_samples.append(sampled[cols])

        logger.info("Sampled %s rows for mode=%s", len(sampled), spec.mode)

    all_samples = pd.concat(mode_samples, axis=0, ignore_index=True)

    # Stable sample_id across reruns with same seed/sample
    all_samples["sample_id"] = all_samples.apply(
        lambda r: f"{r['mode']}_{int(r['sample_rank']):03d}",
        axis=1,
    )

    return all_samples[
        [
            "sample_id",
            "mode",
            "google_travel_mode",
            "origin_id",
            "dest_id",
            "model_duration_s",
            "origin_lat",
            "origin_lon",
            "dest_lat",
            "dest_lon",
        ]
    ].sort_values(["mode", "sample_id"]).reset_index(drop=True)


def _expand_requests(samples_df: pd.DataFrame, departure_date: str, departure_times: Iterable[str]) -> pd.DataFrame:
    rows = []
    for dep_time in departure_times:
        tmp = samples_df.copy()
        tmp["departure_date"] = departure_date
        tmp["departure_time_local"] = dep_time
        rows.append(tmp)
    req = pd.concat(rows, axis=0, ignore_index=True)
    req["request_id"] = req.apply(
        lambda r: f"{r['sample_id']}__{r['departure_time_local'].replace(':', '')}",
        axis=1,
    )
    return req[
        [
            "request_id",
            "sample_id",
            "mode",
            "google_travel_mode",
            "departure_date",
            "departure_time_local",
            "origin_id",
            "dest_id",
            "model_duration_s",
            "origin_lat",
            "origin_lon",
            "dest_lat",
            "dest_lon",
        ]
    ]


def _local_departure_iso(date_yyyy_mm_dd: str, hhmm: str, timezone_name: str) -> str:
    dt_local = datetime.strptime(f"{date_yyyy_mm_dd} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(timezone_name))
    return dt_local.isoformat(timespec="seconds")


def _parse_google_duration_seconds(value: str | None) -> float | None:
    if not value:
        return None
    if value.endswith("s"):
        try:
            return float(value[:-1])
        except ValueError:
            return None
    return None


def _call_google_route(
    session: requests.Session,
    api_key: str,
    mode: str,
    travel_mode: str,
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    departure_iso: str,
    timeout_s: int,
    max_retries: int,
) -> dict:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters",
    }

    payload = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": float(origin_lat),
                    "longitude": float(origin_lon),
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": float(dest_lat),
                    "longitude": float(dest_lon),
                }
            }
        },
        "travelMode": travel_mode,
        "departureTime": departure_iso,
        "computeAlternativeRoutes": False,
        "languageCode": "fr-FR",
        "units": "METRIC",
    }

    if travel_mode == "DRIVE":
        payload["routingPreference"] = "TRAFFIC_AWARE"

    # Keep transit payload minimal for compatibility.
    if travel_mode == "TRANSIT":
        payload.pop("units", None)

    last_error = ""
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.post(GOOGLE_ROUTES_URL, headers=headers, json=payload, timeout=timeout_s)
            if resp.status_code == 200:
                data = resp.json()
                routes = data.get("routes", []) if isinstance(data, dict) else []
                if not routes:
                    return {
                        "google_status": "NO_ROUTE",
                        "google_http_status": 200,
                        "google_duration_s": None,
                        "google_distance_m": None,
                        "google_error": "No route returned",
                    }

                first = routes[0]
                return {
                    "google_status": "OK",
                    "google_http_status": 200,
                    "google_duration_s": _parse_google_duration_seconds(first.get("duration")),
                    "google_distance_m": first.get("distanceMeters"),
                    "google_error": "",
                }

            # Non-200
            snippet = resp.text[:500]
            last_error = f"HTTP {resp.status_code}: {snippet}"

        except requests.RequestException as exc:
            last_error = f"Request error: {exc}"

        if attempt < max_retries:
            time.sleep(2 ** (attempt - 1))

    return {
        "google_status": "ERROR",
        "google_http_status": None,
        "google_duration_s": None,
        "google_distance_m": None,
        "google_error": last_error,
    }


def _resolve_api_key(args: argparse.Namespace) -> str:
    if args.api_key:
        return args.api_key
    return os.environ.get(args.api_key_env, "").strip()


def _run_google_requests(args: argparse.Namespace, requests_df: pd.DataFrame, results_path: Path) -> pd.DataFrame:
    api_key = _resolve_api_key(args)
    if not api_key:
        raise RuntimeError(
            f"Missing API key. Set --api-key or env var {args.api_key_env}, or use --skip-api."
        )

    interval_s = 1.0 / args.requests_per_second
    session = requests.Session()

    done_ids: set[str] = set()
    existing_df = pd.DataFrame()
    if args.resume and results_path.exists():
        existing_df = pd.read_csv(results_path)
        done_ids = set(existing_df.get("request_id", pd.Series(dtype=str)).astype(str))
        logger.info("Resume mode: %s requests already done", len(done_ids))

    rows_out: list[dict] = []
    pending = requests_df[~requests_df["request_id"].astype(str).isin(done_ids)].copy()
    total_pending = len(pending)

    logger.info("Calling Google Routes API for %s requests", total_pending)

    for i, row in enumerate(pending.itertuples(index=False), start=1):
        departure_iso = _local_departure_iso(
            date_yyyy_mm_dd=str(row.departure_date),
            hhmm=str(row.departure_time_local),
            timezone_name=args.timezone,
        )

        result = _call_google_route(
            session=session,
            api_key=api_key,
            mode=str(row.mode),
            travel_mode=str(row.google_travel_mode),
            origin_lat=float(row.origin_lat),
            origin_lon=float(row.origin_lon),
            dest_lat=float(row.dest_lat),
            dest_lon=float(row.dest_lon),
            departure_iso=departure_iso,
            timeout_s=args.timeout_s,
            max_retries=args.max_retries,
        )

        out_row = {
            "request_id": row.request_id,
            "sample_id": row.sample_id,
            "mode": row.mode,
            "google_travel_mode": row.google_travel_mode,
            "departure_date": row.departure_date,
            "departure_time_local": row.departure_time_local,
            "departure_datetime_iso": departure_iso,
            "origin_id": row.origin_id,
            "dest_id": row.dest_id,
            "model_duration_s": row.model_duration_s,
            "google_duration_s": result["google_duration_s"],
            "google_distance_m": result["google_distance_m"],
            "google_status": result["google_status"],
            "google_http_status": result["google_http_status"],
            "google_error": result["google_error"],
        }
        rows_out.append(out_row)

        if i % 20 == 0 or i == total_pending:
            logger.info("Google API progress: %s/%s", i, total_pending)

        time.sleep(interval_s)

    new_df = pd.DataFrame(rows_out)
    if not existing_df.empty:
        final_df = pd.concat([existing_df, new_df], axis=0, ignore_index=True)
        final_df = final_df.drop_duplicates(subset=["request_id"], keep="last")
    else:
        final_df = new_df

    final_df = final_df.sort_values(["mode", "departure_time_local", "sample_id"]).reset_index(drop=True)
    final_df.to_csv(results_path, index=False)

    return final_df


def _write_plots(comparison_df: pd.DataFrame, plots_dir: Path) -> None:
    plots_dir.mkdir(parents=True, exist_ok=True)

    ok = comparison_df[(comparison_df["google_status"] == "OK") & comparison_df["google_duration_s"].notna()].copy()
    if ok.empty:
        logger.warning("No successful Google routes to plot")
        return

    for (mode, dep_time), group in ok.groupby(["mode", "departure_time_local"]):
        x = group["model_duration_s"].astype(float)
        y = group["google_duration_s"].astype(float)
        if x.empty or y.empty:
            continue

        lim = max(float(x.max()), float(y.max()))
        lim = max(lim, 1.0)

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.scatter(x, y, alpha=0.7)
        ax.plot([0, lim], [0, lim], linestyle="--")
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
        ax.set_xlabel("Model duration (s)")
        ax.set_ylabel("Google duration (s)")
        ax.set_title(f"{mode} @ {dep_time}")
        ax.grid(True, alpha=0.3)

        out_file = plots_dir / f"scatter_{mode}_{dep_time.replace(':', '')}.png"
        fig.tight_layout()
        fig.savefig(out_file, dpi=150)
        plt.close(fig)


def main() -> None:
    args = _parse_args()

    args.grid_csv = _resolve(args.grid_csv)
    args.walk_matrix = _resolve(args.walk_matrix)
    args.bike_matrix = _resolve(args.bike_matrix)
    args.car_matrix = _resolve(args.car_matrix)
    args.pt_db = _resolve(args.pt_db)
    args.output_dir = _resolve(args.output_dir)

    _validate_inputs(args)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    samples_path = args.output_dir / "evaluation_sample_od.csv"
    requests_path = args.output_dir / "evaluation_requests.csv"
    google_results_path = args.output_dir / "evaluation_google_results.csv"

    logger.info("Phase A/B: building sampled O-D table")
    grid_coords = _load_grid_coords(args.grid_csv, args.grid_id_col)
    samples_df = _build_samples(args, grid_coords)
    samples_df.to_csv(samples_path, index=False)
    logger.info("Wrote sampled O-D: %s (%s rows)", samples_path, len(samples_df))

    requests_df = _expand_requests(samples_df, args.departure_date, args.departure_times)
    requests_df.to_csv(requests_path, index=False)
    logger.info("Wrote request matrix: %s (%s rows)", requests_path, len(requests_df))

    if args.skip_api:
        logger.info("Skipping Google API calls (--skip-api)")
        return

    logger.info("Phase C: querying Google Routes API")
    comparison_df = _run_google_requests(args, requests_df, google_results_path)
    logger.info("Wrote Google results: %s (%s rows)", google_results_path, len(comparison_df))

    if not args.skip_plots:
        logger.info("Generating scatter plots (mode x hour)")
        _write_plots(comparison_df, args.output_dir / "plots")

    logger.info("Evaluation pipeline completed")


if __name__ == "__main__":
    main()
