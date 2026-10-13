"""Resumable commands for OSM route extraction and GTFS calibration."""

from __future__ import annotations

import argparse
import logging
import pickle
import time
from dataclasses import replace
from datetime import date
from pathlib import Path

import duckdb
import yaml

from mobgrid.pt.config import load_gtfs_rebuild_config
from mobgrid.pt.osm_route_extraction import (
    configure_extraction_connection,
    estimate_run,
    extract_osm_pt_routes,
    process_peak_memory_bytes,
    write_extraction_summary,
)
from mobgrid.pt.relation_pipeline import (
    RelationCalibrationRun,
    run_relation_calibration,
)
from mobgrid.pt.report import write_report
from mobgrid.pt.stop_tables import write_osm_pt_stops_cache

logger = logging.getLogger("mobgrid.pt")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mobgrid.pt")
    subparsers = parser.add_subparsers(dest="command", required=True)
    extract = subparsers.add_parser("extract-osm-routes")
    extract.add_argument("--date", required=True)
    extract.add_argument("--pbf", type=Path, required=True)
    extract.add_argument(
        "--output-root", type=Path, default=Path("data/interim/osm_pt_routes")
    )
    extract.add_argument(
        "--estimate-pbf",
        type=Path,
        action="append",
        default=[],
        help="target PBF whose runtime/memory is estimated from this run",
    )
    extract.add_argument(
        "--estimate-size",
        action="append",
        default=[],
        metavar="NAME=BYTES",
        help="target label and size when the target PBF is not local",
    )
    extract.add_argument("--log", type=Path)
    extract.add_argument("--summary", type=Path)
    extract.add_argument(
        "--stop-cache-root",
        type=Path,
        default=Path("data/interim/osm_pt_stops"),
    )

    calibrate = subparsers.add_parser("calibrate")
    calibrate.add_argument(
        "--config", type=Path, default=Path("config/gtfs_rebuild.yaml")
    )
    calibrate.add_argument(
        "--gtfs-inventory", type=Path, default=Path("config/gtfs_inventory.csv")
    )
    calibrate.add_argument(
        "--sources", type=Path, default=Path("config/sources.yaml")
    )
    calibrate.add_argument(
        "--contours",
        type=Path,
        default=Path("data/raw/contours/2026/communes-5m.geojson.gz"),
    )
    calibrate.add_argument(
        "--report", type=Path, default=Path("docs/data/step0_gtfs_rebuild.md")
    )
    calibrate.add_argument(
        "--results-pickle",
        type=Path,
        default=Path("data/results/step0_gtfs_rebuild/relation_calibration.pkl"),
    )
    calibrate.add_argument("--scratch-dir", type=Path)
    calibrate.add_argument("--log", type=Path)
    calibrate.add_argument("--summary", type=Path)
    return parser


def _configure_logging(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(path, encoding="utf-8")],
    )


def _default_artifact(task: str, suffix: str) -> Path:
    return Path("logs") / f"{date.today().isoformat()}_{task}{suffix}"


def _write_calibration_summary(
    run: RelationCalibrationRun, path: Path, report: Path, results: Path
) -> None:
    chosen = "\n".join(
        f"- {family}: r={point.r_m} m, k={point.k}, theta={point.theta}, "
        f"geometry share={point.geometry_share}, known "
        f"{point.score.known_correct}/{point.score.known_total}, false-change "
        f"{point.score.false_change_rate:.2%}"
        for family, point in sorted(run.chosen.items())
    )
    warning = (
        "- Networks below 50% relation coverage are listed in the report."
        if run.flagged_networks
        else "- None."
    )
    text = f"""# GTFS relation calibration summary

## Inputs and outputs

- Route caches: `data/interim/osm_pt_routes/{{2022-01-01,2024-01-01}}`
- Results: `{results}`
- Report: `{report}`
- Route/date outcomes: {len(run.final_routes):,}
- Flagged network/date pairs: {len(run.flagged_networks):,}

## Recommended parameters

{chosen}

## Warnings

{warning}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_chosen_config(path: Path, run: RelationCalibrationRun) -> None:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw["chosen"] = {
        family: {
            "r_m": point.r_m,
            "k": point.k,
            "geometry_share": point.geometry_share,
            "theta": point.theta,
        }
        for family, point in sorted(run.chosen.items())
    }
    path.write_text(
        "# TODO(confirm): recommended by the relation-based calibration.\n"
        + yaml.safe_dump(raw, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def _write_candidates(path: Path, run: RelationCalibrationRun) -> None:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    confirmed = {
        (change["network"], route_id)
        for change in raw.get("confirmed", [])
        for route_id in change["route_ids"]
    }
    grouped: dict[tuple[str, str], list] = {}
    for route in run.final_routes:
        key = (route.network, route.pattern.route_id)
        if (
            route.result.outcome in ("dropped", "kept-renamed")
            and key not in confirmed
        ):
            grouped.setdefault(
                key, []
            ).append(route)
    candidates = []
    for (network, route_id), routes in sorted(grouped.items()):
        evidence = max(routes, key=lambda route: route.result.covered_share)
        candidates.append(
            {
                "id": f"candidate_{network}_{route_id}".replace(":", "_"),
                "network": network,
                "route_id": route_id,
                "outcomes_by_date": {
                    route.date_key: route.result.outcome for route in routes
                },
                "match_pass": evidence.result.match_pass,
                "relation_ids": list(evidence.result.relation_ids),
                "relation_refs": list(evidence.result.relation_refs),
                "covered_share": round(evidence.result.covered_share, 6),
            }
        )
    raw["candidates"] = candidates
    path.write_text(
        yaml.safe_dump(raw, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def _run_calibration(args: argparse.Namespace) -> int:
    config = load_gtfs_rebuild_config(args.config)

    def execute(scratch: Path) -> RelationCalibrationRun:
        if args.results_pickle.is_file():
            logger.info("checkpoint exists, loading %s", args.results_pickle)
            with args.results_pickle.open("rb") as stream:
                return pickle.load(stream)
        run = run_relation_calibration(
            config,
            args.gtfs_inventory,
            args.sources,
            args.contours,
            scratch,
        )
        args.results_pickle.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.results_pickle.with_suffix(".tmp")
        with temporary.open("wb") as stream:
            pickle.dump(run, stream)
        temporary.replace(args.results_pickle)
        return run

    scratch = args.scratch_dir or Path(
        "data/interim/gtfs_rebuild/calibration_scratch"
    )
    scratch.mkdir(parents=True, exist_ok=True)
    run = execute(scratch)
    write_report(run, config, args.report)
    _write_chosen_config(args.config, run)
    _write_candidates(Path("config/pt_changes.yaml"), run)
    summary = args.summary or _default_artifact("gtfs_calibration", "_summary.md")
    _write_calibration_summary(run, summary, args.report, args.results_pickle)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run one resumable extraction or calibration job."""
    args = _parser().parse_args(argv)
    task = (
        f"osm_pt_routes_{args.date}"
        if args.command == "extract-osm-routes"
        else "gtfs_calibration"
    )
    _configure_logging(args.log or _default_artifact(task, ".log"))
    if args.command == "extract-osm-routes":
        started = time.perf_counter()
        summary = args.summary or _default_artifact(task, "_summary.md")
        result = extract_osm_pt_routes(args.pbf, args.output_root / args.date)
        stop_cache = args.stop_cache_root / f"{args.date}.parquet"
        if not stop_cache.is_file():
            logger.info("building fallback stop cache %s", stop_cache)
            connection = duckdb.connect()
            configure_extraction_connection(connection, args.output_root.parent)
            write_osm_pt_stops_cache(connection, args.pbf, stop_cache, bboxes=None)
        result = replace(
            result,
            elapsed_seconds=time.perf_counter() - started,
            peak_memory_bytes=process_peak_memory_bytes(),
        )
        write_extraction_summary(result, summary)
        estimate_targets = [
            (str(target), target.stat().st_size)
            for target in args.estimate_pbf
        ]
        for value in args.estimate_size:
            try:
                label, size = value.rsplit("=", 1)
                estimate_targets.append((label, int(size)))
            except ValueError as error:
                raise ValueError(
                    f"invalid --estimate-size {value!r}; expected NAME=BYTES"
                ) from error
        if estimate_targets:
            estimates = ["\n## Input-size estimates\n"]
            for label, size in estimate_targets:
                seconds, peak = estimate_run(result, size)
                peak_text = (
                    f"{peak / 1024**3:.2f} GiB"
                    if peak is not None
                    else "not available"
                )
                estimates.append(
                    f"- `{label}`: {seconds / 60:.1f} minutes, "
                    f"{peak_text} linear memory upper bound"
                )
            estimates.append(
                "\nRuntime estimates and conservative memory upper bounds "
                "scale the smoke measurements by compressed PBF size. The "
                "extraction mostly streams; DuckDB is memory-capped and can "
                "spill to the configured temporary directory."
            )
            with summary.open("a", encoding="utf-8") as stream:
                stream.write("\n".join(estimates) + "\n")
        return 0
    return _run_calibration(args)


if __name__ == "__main__":
    raise SystemExit(main())
