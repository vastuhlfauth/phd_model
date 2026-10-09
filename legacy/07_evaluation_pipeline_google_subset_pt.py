#!/usr/bin/env python3
"""PT-only evaluation test pipeline aligned with Google API request conditions.

This script compares model outputs to existing Google results for the same
public-transport O-D requests and departure times.

Pipeline stages:
1) Read `outputs/07_evaluation_pipeline/evaluation_google_results.csv`
2) Keep only `mode=public_transport` and requested departure times
3) Recompute stop-to-stop PT durations at exact departure times via Phase 4 RAPTOR logic
4) Aggregate to grid O-D durations with the same access/transit/egress formulation as Phase 5
5) Write comparison CSV and run Phase 8 visuals/metrics on that CSV
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import duckdb
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parent.parent

DEFAULT_GOOGLE_RESULTS = ROOT_DIR / "outputs" / "07_evaluation_pipeline" / "evaluation_google_results.csv"
DEFAULT_PT_STOPS_CATALOG = ROOT_DIR / "outputs" / "02_destination_grid_preparation" / "pt_stops_catalog.csv"
DEFAULT_WALK_MATRIX = ROOT_DIR / "outputs" / "03_car_bike_walk_accessibility" / "foot_grid_45min_fast.parquet"
DEFAULT_GTFS_DIR = ROOT_DIR / "outputs" / "01_data_import_preparation" / "gtfs_processed"
DEFAULT_STOPS_FILE = DEFAULT_GTFS_DIR / "stops.txt"

DEFAULT_OUTPUT_DIR = ROOT_DIR / "outputs" / "07_evaluation_pipeline_google_subset_pt"
DEFAULT_PHASE8_OUTPUT_DIR = ROOT_DIR / "outputs" / "08_evaluation_visuals_google_subset_pt"
DEFAULT_PHASE8_PLOTS_DIR = ROOT_DIR / "visuals" / "08_evaluation_visuals_google_subset_pt"

DEFAULT_DEPARTURE_DATE = "2026-03-18"
DEFAULT_DEPARTURE_TIMES = ["07:00", "08:20"]


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT_DIR / path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PT-only evaluation test pipeline on the exact Google-tested requests"
    )
    parser.add_argument("--google-results", type=Path, default=DEFAULT_GOOGLE_RESULTS)
    parser.add_argument("--pt-stops-catalog", type=Path, default=DEFAULT_PT_STOPS_CATALOG)
    parser.add_argument("--walk-matrix", type=Path, default=DEFAULT_WALK_MATRIX)
    parser.add_argument("--gtfs-dir", type=Path, default=DEFAULT_GTFS_DIR)
    parser.add_argument("--stops-file", type=Path, default=DEFAULT_STOPS_FILE)

    parser.add_argument("--departure-date", type=str, default=DEFAULT_DEPARTURE_DATE)
    parser.add_argument("--departure-times", nargs="+", default=DEFAULT_DEPARTURE_TIMES)
    parser.add_argument(
        "--model-time-offset-min",
        type=int,
        default=0,
        help="Offset (minutes) applied to model PT departure time while keeping Google request labels",
    )

    parser.add_argument("--max-duration-s", type=int, default=3600)
    parser.add_argument("--max-transfers", type=int, default=3)
    parser.add_argument("--access-max-s", type=int, default=900)
    parser.add_argument(
        "--max-access-stops-per-request",
        type=int,
        default=0,
        help="Keep only K best access stop-grids per request (by walk time); 0 means no cap",
    )
    parser.add_argument(
        "--max-egress-stops-per-request",
        type=int,
        default=0,
        help="Keep only K best egress stop-grids per request (by walk time); 0 means no cap",
    )
    parser.add_argument("--max-origin-stops", type=int, default=0, help="Optional cap on number of origin stops (0 = no cap)")
    parser.add_argument("--max-dest-stops", type=int, default=0, help="Optional cap on number of destination stops (0 = no cap)")

    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--phase8-output-dir", type=Path, default=DEFAULT_PHASE8_OUTPUT_DIR)
    parser.add_argument("--phase8-plots-dir", type=Path, default=DEFAULT_PHASE8_PLOTS_DIR)
    parser.add_argument("--skip-phase8", action="store_true")
    parser.add_argument("--python-bin", type=str, default=sys.executable)
    return parser.parse_args()


def _load_phase4_module(phase4_path: Path):
    spec = importlib.util.spec_from_file_location("phase4_module", str(phase4_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec from {phase4_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _normalize_hhmm(value: str) -> str:
    raw = str(value).strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%H:%M")
        except ValueError:
            continue
    if len(raw) >= 5:
        candidate = raw[:5]
        try:
            dt = datetime.strptime(candidate, "%H:%M")
            return dt.strftime("%H:%M")
        except ValueError:
            pass
    raise ValueError(f"Invalid departure time format: {value}")


def _shift_hhmm(value_hhmm: str, offset_min: int) -> str:
    base = datetime.strptime(value_hhmm, "%H:%M")
    shifted = base + timedelta(minutes=int(offset_min))
    return shifted.strftime("%H:%M")


def _load_google_requests(csv_path: Path, departure_times: list[str], departure_date: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    required = {
        "request_id",
        "sample_id",
        "mode",
        "departure_date",
        "departure_time_local",
        "origin_id",
        "dest_id",
        "google_duration_s",
        "google_distance_m",
        "google_status",
        "google_http_status",
        "google_error",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Google results CSV missing columns: {sorted(missing)}")

    normalized_times = [_normalize_hhmm(str(t)) for t in departure_times]
    out = df[df["mode"].astype(str) == "public_transport"].copy()
    out["departure_time_local"] = out["departure_time_local"].astype(str).map(_normalize_hhmm)
    out = out[out["departure_time_local"].isin(normalized_times)].copy()

    if "departure_date" in out.columns:
        out = out[out["departure_date"].astype(str) == str(departure_date)].copy()

    out["origin_id"] = out["origin_id"].astype(str)
    out["dest_id"] = out["dest_id"].astype(str)
    out = out.drop_duplicates(subset=["request_id"], keep="first").reset_index(drop=True)

    if out.empty:
        raise RuntimeError("No public_transport Google rows found for requested date/times")

    return out


def _prepare_stop_sets(
    pt_stops_catalog: Path,
    req_df: pd.DataFrame,
    walk_matrix: Path,
    access_max_s: int,
    max_access_stops_per_request: int,
    max_egress_stops_per_request: int,
) -> tuple[pd.DataFrame, dict[str, set[str]], set[str], set[str]]:
    cat = pd.read_csv(pt_stops_catalog, usecols=["stop_id", "dest_id"]).dropna(subset=["stop_id", "dest_id"])
    cat["stop_id"] = cat["stop_id"].astype(str)
    cat["dest_id"] = cat["dest_id"].astype(str)
    
    # Detect file type for walk_matrix
    walk_matrix_str = str(walk_matrix)
    if walk_matrix_str.endswith('.parquet'):
        walk_read_expr = f"read_parquet('{walk_matrix_str}')"
    else:
        walk_read_expr = f"""read_csv_auto(
            '{walk_matrix_str}',
            header=true,
            compression='gzip',
            delim=',',
            quote='"',
            strict_mode=false,
            null_padding=true,
            parallel=false
        )"""

    req = req_df[["request_id", "origin_id", "dest_id"]].drop_duplicates().copy()
    req["request_id"] = req["request_id"].astype(str)
    req["origin_id"] = req["origin_id"].astype(str)
    req["dest_id"] = req["dest_id"].astype(str)

    con = duckdb.connect(":memory:")
    try:
        con.register("req", req)
        con.register("pt_catalog", cat)

        con.execute(
            """
            CREATE TEMP TABLE origin_ref AS
            SELECT DISTINCT origin_id AS dest_id FROM req
            """
        )
        con.execute(
            """
            CREATE TEMP TABLE dest_ref AS
            SELECT DISTINCT dest_id AS dest_id FROM req
            """
        )

        con.execute(
            f"""
            CREATE TEMP TABLE walk_raw AS
            SELECT
                CAST(origin_id AS VARCHAR) AS origin_id,
                CAST(dest_id AS VARCHAR) AS dest_id,
                TRY_CAST(duration_s AS DOUBLE) AS duration_s
            FROM {walk_read_expr}
            WHERE origin_id IS NOT NULL
              AND dest_id IS NOT NULL
              AND TRY_CAST(duration_s AS DOUBLE) IS NOT NULL
              AND TRY_CAST(duration_s AS DOUBLE) >= 0
            """
        )

        access_stop_grids = con.execute(
            """
            SELECT DISTINCT w.dest_id AS stop_grid
            FROM walk_raw w
            JOIN origin_ref o ON o.dest_id = w.origin_id
            JOIN (SELECT DISTINCT dest_id FROM pt_catalog) p ON p.dest_id = w.dest_id
            WHERE w.duration_s <= ?
            """,
            [int(access_max_s)],
        ).fetchdf()["stop_grid"].astype(str).tolist()

        egress_stop_grids = con.execute(
            """
            SELECT DISTINCT w.origin_id AS stop_grid
            FROM walk_raw w
            JOIN dest_ref d ON d.dest_id = w.dest_id
            JOIN (SELECT DISTINCT dest_id FROM pt_catalog) p ON p.dest_id = w.origin_id
            WHERE w.duration_s <= ?
            """,
            [int(access_max_s)],
        ).fetchdf()["stop_grid"].astype(str).tolist()

        stop_pairs_df = con.execute(
            """
            WITH access_req_raw AS (
                SELECT DISTINCT
                    r.request_id,
                    w.dest_id AS stop_grid_o,
                    w.duration_s AS walk_s
                FROM req r
                JOIN walk_raw w
                  ON w.origin_id = r.origin_id
                 AND w.duration_s <= ?
                JOIN pt_catalog c
                  ON c.dest_id = w.dest_id
            ),
            access_req_ranked AS (
                SELECT
                    request_id,
                    stop_grid_o,
                    walk_s,
                    ROW_NUMBER() OVER (
                        PARTITION BY request_id
                        ORDER BY walk_s ASC, stop_grid_o ASC
                    ) AS rn
                FROM access_req_raw
            ),
            access_req AS (
                SELECT
                    request_id,
                    stop_grid_o
                FROM access_req_ranked
                WHERE (? <= 0 OR rn <= ?)
            ),
            egress_req_raw AS (
                SELECT DISTINCT
                    r.request_id,
                    w.origin_id AS stop_grid_d,
                    w.duration_s AS walk_s
                FROM req r
                JOIN walk_raw w
                  ON w.dest_id = r.dest_id
                 AND w.duration_s <= ?
                JOIN pt_catalog c
                  ON c.dest_id = w.origin_id
            ),
            egress_req_ranked AS (
                SELECT
                    request_id,
                    stop_grid_d,
                    walk_s,
                    ROW_NUMBER() OVER (
                        PARTITION BY request_id
                        ORDER BY walk_s ASC, stop_grid_d ASC
                    ) AS rn
                FROM egress_req_raw
            ),
            egress_req AS (
                SELECT
                    request_id,
                    stop_grid_d
                FROM egress_req_ranked
                WHERE (? <= 0 OR rn <= ?)
            ),
            access_stops AS (
                SELECT
                    a.request_id,
                    c.stop_id AS origin_stop_id
                FROM access_req a
                JOIN pt_catalog c
                  ON c.dest_id = a.stop_grid_o
            ),
            egress_stops AS (
                SELECT
                    e.request_id,
                    c.stop_id AS dest_stop_id
                FROM egress_req e
                JOIN pt_catalog c
                  ON c.dest_id = e.stop_grid_d
            )
            SELECT DISTINCT
                a.origin_stop_id,
                e.dest_stop_id
            FROM access_stops a
            JOIN egress_stops e
              ON e.request_id = a.request_id
            """,
            [
                int(access_max_s),
                int(max_access_stops_per_request),
                int(max_access_stops_per_request),
                int(access_max_s),
                int(max_egress_stops_per_request),
                int(max_egress_stops_per_request),
            ],
        ).fetchdf()
    finally:
        con.close()

    origin_stops = set(cat[cat["dest_id"].isin(set(access_stop_grids))]["stop_id"].astype(str).tolist())
    dest_stops = set(cat[cat["dest_id"].isin(set(egress_stop_grids))]["stop_id"].astype(str).tolist())

    if not origin_stops:
        raise RuntimeError("No PT stops found for selected origin grids")
    if not dest_stops:
        raise RuntimeError("No PT stops found for selected destination grids")

    if stop_pairs_df.empty:
        raise RuntimeError("No request-driven stop pairs found for selected PT Google subset")

    stop_pairs_df["origin_stop_id"] = stop_pairs_df["origin_stop_id"].astype(str)
    stop_pairs_df["dest_stop_id"] = stop_pairs_df["dest_stop_id"].astype(str)

    needed_dest_by_origin_stop: dict[str, set[str]] = {}
    for row in stop_pairs_df.itertuples(index=False):
        needed_dest_by_origin_stop.setdefault(str(row.origin_stop_id), set()).add(str(row.dest_stop_id))

    return cat, needed_dest_by_origin_stop, origin_stops, dest_stops


def _compute_pt_stop_matrix(
    phase4_mod,
    stops_file: Path,
    gtfs_dir: Path,
    departure_date: str,
    departure_times: list[str],
    needed_dest_by_origin_stop: dict[str, set[str]],
    max_duration_s: int,
    max_transfers: int,
    max_origin_stops: int,
    max_dest_stops: int,
    model_time_offset_min: int,
) -> pd.DataFrame:
    stops_df = phase4_mod.load_stops(stops_file)
    index, cache_path = phase4_mod._load_or_build_index(gtfs_dir, stops_df, departure_date)
    logger.info("Loaded RAPTOR index cache: %s", cache_path)

    stop_id_to_idx = {sid: i for i, sid in enumerate(index["stop_ids"])}
    origin_ids_sorted = [s for s in sorted(needed_dest_by_origin_stop.keys()) if s in stop_id_to_idx]
    if max_origin_stops > 0:
        origin_ids_sorted = origin_ids_sorted[:max_origin_stops]

    allowed_dest_ids: set[str] | None = None
    if max_dest_stops > 0:
        all_dest_ids = sorted(
            {
                d
                for o in origin_ids_sorted
                for d in needed_dest_by_origin_stop.get(o, set())
                if d in stop_id_to_idx
            }
        )
        allowed_dest_ids = set(all_dest_ids[:max_dest_stops])

    dest_indices_by_origin: dict[int, list[int]] = {}
    for origin_id in origin_ids_sorted:
        dest_ids = [d for d in sorted(needed_dest_by_origin_stop.get(origin_id, set())) if d in stop_id_to_idx]
        if allowed_dest_ids is not None:
            dest_ids = [d for d in dest_ids if d in allowed_dest_ids]
        if not dest_ids:
            continue
        dest_indices_by_origin[stop_id_to_idx[origin_id]] = [stop_id_to_idx[d] for d in dest_ids]

    if not dest_indices_by_origin:
        raise RuntimeError("No selected destination stop IDs exist in GTFS stops index")

    origin_indices = sorted(dest_indices_by_origin.keys())

    total_pairs = sum(len(v) for v in dest_indices_by_origin.values())
    logger.info(
        "Request-driven stop pairs after filtering: origins=%s pairs=%s",
        len(origin_indices),
        total_pairs,
    )

    rows: list[dict] = []
    for dep_time in departure_times:
        model_dep_time = _shift_hhmm(dep_time, model_time_offset_min)
        dep_s = phase4_mod.parse_hhmm_to_seconds(model_dep_time)
        logger.info(
            "Computing RAPTOR durations for request_time=%s using model_time=%s | origins=%s request_pairs=%s",
            dep_time,
            model_dep_time,
            len(origin_indices),
            total_pairs,
        )

        for i, o_idx in enumerate(origin_indices, start=1):
            dest_indices = dest_indices_by_origin.get(o_idx, [])
            if not dest_indices:
                continue
            arrivals = phase4_mod._raptor_earliest_arrivals(index, o_idx, dep_s, max_transfers)
            for d_idx in dest_indices:
                arr_t = arrivals[d_idx]
                if arr_t >= phase4_mod.RAPTOR_INF:
                    continue
                dur = int(arr_t - dep_s)
                if dur < 0 or dur > int(max_duration_s):
                    continue
                rows.append(
                    {
                        "departure_time_local": dep_time,
                        "model_departure_time_local": model_dep_time,
                        "origin_stop_id": index["stop_ids"][o_idx],
                        "dest_stop_id": index["stop_ids"][d_idx],
                        "mean_duration_s": dur,
                        "samples": 1,
                        "time_start": model_dep_time,
                        "time_end": model_dep_time,
                        "time_step_min": 1,
                        "max_duration_s": int(max_duration_s),
                        "mode": "public_transport",
                    }
                )

            if i % 25 == 0 or i == len(origin_indices):
                logger.info("RAPTOR origin progress %s/%s at request_time=%s", i, len(origin_indices), dep_time)

    if not rows:
        raise RuntimeError("No stop-to-stop PT durations were computed for selected subset")

    pt_df = pd.DataFrame(rows)
    pt_df = (
        pt_df.groupby(["departure_time_local", "origin_stop_id", "dest_stop_id"], as_index=False)
        .agg(
            mean_duration_s=("mean_duration_s", "min"),
            samples=("samples", "max"),
            model_departure_time_local=("model_departure_time_local", "first"),
            time_start=("time_start", "first"),
            time_end=("time_end", "first"),
            time_step_min=("time_step_min", "first"),
            max_duration_s=("max_duration_s", "first"),
            mode=("mode", "first"),
        )
    )
    return pt_df


def _compute_grid_od_from_phase5_formula(
    req_df: pd.DataFrame,
    pt_stop_df: pd.DataFrame,
    pt_catalog_df: pd.DataFrame,
    walk_matrix: Path,
    access_max_s: int,
) -> pd.DataFrame:
    con = duckdb.connect(":memory:")
    # Auto-detect Parquet vs CSV for walk matrix
    walk_str = str(walk_matrix)
    if walk_str.endswith(".parquet"):
        walk_read_expr = f"read_parquet('{walk_str}')"
    else:
        walk_read_expr = f"read_csv_auto('{walk_str}', header=true, compression='gzip', delim=',', quote='\"', strict_mode=false, null_padding=true, parallel=false)"
    try:
        req = req_df[["request_id", "sample_id", "departure_date", "departure_time_local", "origin_id", "dest_id"]].copy()
        req["origin_id"] = req["origin_id"].astype(str)
        req["dest_id"] = req["dest_id"].astype(str)

        cat = pt_catalog_df[["stop_id", "dest_id"]].drop_duplicates().copy()
        cat["stop_id"] = cat["stop_id"].astype(str)
        cat["dest_id"] = cat["dest_id"].astype(str)

        pt = pt_stop_df[["departure_time_local", "origin_stop_id", "dest_stop_id", "mean_duration_s"]].copy()
        pt["origin_stop_id"] = pt["origin_stop_id"].astype(str)
        pt["dest_stop_id"] = pt["dest_stop_id"].astype(str)
        pt["departure_time_local"] = pt["departure_time_local"].astype(str)

        con.register("req", req)
        con.register("pt_catalog", cat)
        con.register("pt_stop", pt)

        con.execute(
            """
            CREATE TEMP TABLE origin_ref AS
            SELECT DISTINCT origin_id AS dest_id FROM req
            """
        )
        con.execute(
            """
            CREATE TEMP TABLE dest_ref AS
            SELECT DISTINCT dest_id AS dest_id FROM req
            """
        )
        con.execute(
            """
            CREATE TEMP TABLE stop_grid_ref AS
            SELECT DISTINCT dest_id FROM pt_catalog
            """
        )

        con.execute(
            f"""
            CREATE TEMP TABLE walk_raw AS
            SELECT
                CAST(origin_id AS VARCHAR) AS origin_id,
                CAST(dest_id AS VARCHAR) AS dest_id,
                TRY_CAST(duration_s AS DOUBLE) AS duration_s
            FROM {walk_read_expr}
            WHERE origin_id IS NOT NULL
              AND dest_id IS NOT NULL
              AND TRY_CAST(duration_s AS DOUBLE) IS NOT NULL
              AND TRY_CAST(duration_s AS DOUBLE) >= 0
            """
        )

        con.execute(
            """
            CREATE TEMP TABLE access_best AS
            SELECT
                w.origin_id,
                w.dest_id AS stop_grid,
                CAST(MIN(w.duration_s) AS DOUBLE) AS walk_s
            FROM walk_raw w
            JOIN origin_ref o ON o.dest_id = w.origin_id
            JOIN stop_grid_ref s ON s.dest_id = w.dest_id
            WHERE w.duration_s <= ?
            GROUP BY 1, 2
            """,
            [int(access_max_s)],
        )

        con.execute(
            """
            CREATE TEMP TABLE egress_best AS
            SELECT
                w.origin_id AS stop_grid,
                w.dest_id,
                CAST(MIN(w.duration_s) AS DOUBLE) AS walk_s
            FROM walk_raw w
            JOIN stop_grid_ref s ON s.dest_id = w.origin_id
            JOIN dest_ref d ON d.dest_id = w.dest_id
            WHERE w.duration_s <= ?
            GROUP BY 1, 2
            """,
            [int(access_max_s)],
        )

        con.execute(
            """
            CREATE TEMP TABLE transit_best AS
            SELECT
                p.departure_time_local,
                co.dest_id AS stop_grid_o,
                cd.dest_id AS stop_grid_d,
                CAST(MIN(p.mean_duration_s) AS DOUBLE) AS pt_s
            FROM pt_stop p
            JOIN pt_catalog co ON co.stop_id = p.origin_stop_id
            JOIN pt_catalog cd ON cd.stop_id = p.dest_stop_id
            GROUP BY 1, 2, 3
            """
        )

        out = con.execute(
            """
            SELECT
                r.request_id,
                r.sample_id,
                r.departure_date,
                r.departure_time_local,
                r.origin_id,
                r.dest_id,
                CAST(MIN(a.walk_s + t.pt_s + e.walk_s) AS DOUBLE) AS model_duration_s
            FROM req r
            JOIN access_best a
              ON a.origin_id = r.origin_id
            JOIN transit_best t
              ON t.departure_time_local = r.departure_time_local
             AND t.stop_grid_o = a.stop_grid
            JOIN egress_best e
              ON e.stop_grid = t.stop_grid_d
             AND e.dest_id = r.dest_id
            GROUP BY 1, 2, 3, 4, 5, 6
            """
        ).fetchdf()

        out["model_duration_s"] = pd.to_numeric(out["model_duration_s"], errors="coerce")
        return out
    finally:
        con.close()


def _run_phase8(
    python_bin: str,
    results_csv: Path,
    output_dir: Path,
    plots_dir: Path,
) -> None:
    phase8_script = ROOT_DIR / "codes" / "08_evaluation_visuals.py"
    if not phase8_script.exists():
        raise FileNotFoundError(f"Missing Phase 8 script: {phase8_script}")

    cmd = [
        python_bin,
        str(phase8_script),
        "--results-csv",
        str(results_csv),
        "--output-dir",
        str(output_dir),
        "--plots-dir",
        str(plots_dir),
    ]
    completed = subprocess.run(cmd, cwd=str(ROOT_DIR), check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Phase 8 failed with return code {completed.returncode}")


def main() -> None:
    args = _parse_args()

    args.google_results = _resolve(args.google_results)
    args.pt_stops_catalog = _resolve(args.pt_stops_catalog)
    args.walk_matrix = _resolve(args.walk_matrix)
    args.gtfs_dir = _resolve(args.gtfs_dir)
    args.stops_file = _resolve(args.stops_file)
    args.output_dir = _resolve(args.output_dir)
    args.phase8_output_dir = _resolve(args.phase8_output_dir)
    args.phase8_plots_dir = _resolve(args.phase8_plots_dir)

    for required in [
        args.google_results,
        args.pt_stops_catalog,
        args.walk_matrix,
        args.gtfs_dir,
        args.stops_file,
    ]:
        if not required.exists():
            raise FileNotFoundError(f"Missing required input: {required}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.phase8_output_dir.mkdir(parents=True, exist_ok=True)
    args.phase8_plots_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Candidate caps | access_per_request=%s egress_per_request=%s (0 means unlimited)",
        args.max_access_stops_per_request,
        args.max_egress_stops_per_request,
    )
    logger.info("Model time offset for PT computation: %s min", args.model_time_offset_min)
    if args.max_access_stops_per_request > 0 or args.max_egress_stops_per_request > 0:
        logger.warning(
            "Per-request stop caps are enabled; this speeds up runtime but can reduce coverage and bias durations. "
            "Use 0/0 for highest-fidelity comparison to Google."
        )

    req_df = _load_google_requests(args.google_results, args.departure_times, args.departure_date)
    req_csv = args.output_dir / "public_transport_google_requests_subset.csv"
    req_df.to_csv(req_csv, index=False)
    logger.info("Selected Google PT requests: %s rows | wrote %s", len(req_df), req_csv)

    pt_catalog_df, needed_dest_by_origin_stop, origin_stops, dest_stops = _prepare_stop_sets(
        pt_stops_catalog=args.pt_stops_catalog,
        req_df=req_df,
        walk_matrix=args.walk_matrix,
        access_max_s=args.access_max_s,
        max_access_stops_per_request=args.max_access_stops_per_request,
        max_egress_stops_per_request=args.max_egress_stops_per_request,
    )
    logger.info(
        "Selected stop sets | origin_stops=%s dest_stops=%s",
        len(origin_stops),
        len(dest_stops),
    )

    phase4_path = ROOT_DIR / "codes" / "04_public_transit_od_matrix_network.py"
    phase4 = _load_phase4_module(phase4_path)

    pt_stop_df = _compute_pt_stop_matrix(
        phase4_mod=phase4,
        stops_file=args.stops_file,
        gtfs_dir=args.gtfs_dir,
        departure_date=args.departure_date,
        departure_times=[str(t) for t in args.departure_times],
        needed_dest_by_origin_stop=needed_dest_by_origin_stop,
        max_duration_s=args.max_duration_s,
        max_transfers=args.max_transfers,
        max_origin_stops=args.max_origin_stops,
        max_dest_stops=args.max_dest_stops,
        model_time_offset_min=args.model_time_offset_min,
    )
    pt_stop_csv = args.output_dir / "pt_stop_to_stop_subset_exact_times.csv"
    pt_stop_df.to_csv(pt_stop_csv, index=False)
    logger.info("Wrote PT stop matrix subset: %s (%s rows)", pt_stop_csv, len(pt_stop_df))

    model_df = _compute_grid_od_from_phase5_formula(
        req_df=req_df,
        pt_stop_df=pt_stop_df,
        pt_catalog_df=pt_catalog_df,
        walk_matrix=args.walk_matrix,
        access_max_s=args.access_max_s,
    )

    merged = req_df.merge(
        model_df[["request_id", "model_duration_s"]],
        on="request_id",
        how="left",
        suffixes=("", "_recomputed"),
    )
    merged = merged.rename(columns={"model_duration_s": "model_duration_s_baseline"})
    merged["model_duration_s"] = merged["model_duration_s_recomputed"]
    merged["mode"] = "public_transport"
    merged["google_travel_mode"] = "TRANSIT"
    merged = merged.drop(columns=["model_duration_s_recomputed"], errors="ignore")

    results_csv = args.output_dir / "evaluation_google_results_public_transport_exact_conditions.csv"
    merged.to_csv(results_csv, index=False)
    logger.info("Wrote recomputed comparison CSV: %s (%s rows)", results_csv, len(merged))

    coverage = merged["model_duration_s"].notna().mean()
    logger.info("Model coverage on selected PT requests: %.1f%%", 100.0 * float(coverage))

    if not args.skip_phase8:
        _run_phase8(
            python_bin=args.python_bin,
            results_csv=results_csv,
            output_dir=args.phase8_output_dir,
            plots_dir=args.phase8_plots_dir,
        )
        logger.info("Phase 8 completed on recomputed subset results")


if __name__ == "__main__":
    main()
