"""Resumable commands for OSM route extraction and GTFS calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import pickle
import time
from dataclasses import replace
from datetime import date
from pathlib import Path

import duckdb
import yaml

from mobgrid.pt.config import GtfsRebuildConfig, load_gtfs_rebuild_config
from mobgrid.pt.osm_route_extraction import (
    configure_extraction_connection,
    estimate_run,
    extract_osm_pt_routes,
    process_peak_memory_bytes,
    write_extraction_summary,
)
from mobgrid.pt.relation_pipeline import (
    RelationCalibrationRun,
    network_relation_coverage,
    run_relation_calibration,
)
from mobgrid.pt.report import write_report
from mobgrid.pt.stop_tables import write_osm_pt_stops_cache

logger = logging.getLogger("mobgrid.pt")


def _file_stat(path: str | Path) -> tuple[int, int] | None:
    candidate = Path(path)
    if not candidate.is_file():
        return None
    stat = candidate.stat()
    return (stat.st_size, stat.st_mtime_ns)


def _calibration_run_signature(
    config: GtfsRebuildConfig,
    gtfs_inventory_csv: str | Path,
    sources_yaml: str | Path,
    contours_path: str | Path,
    restrict_networks: list[str] | None,
) -> str:
    """Hash every input a calibration run depends on.

    Covers the OSM route caches' own files (so a ways.parquet rebuild, such
    as the 2026-10-14 busway/lanes_bus schema upgrade, is detected), the
    config content, and the GTFS/sources/contours files, so the top-level
    results checkpoint is invalidated exactly like the lower-level
    relation-table and grid checkpoints already are.
    """
    payload = {
        "config": config.model_dump(mode="json"),
        "gtfs_inventory": _file_stat(gtfs_inventory_csv),
        "sources": _file_stat(sources_yaml),
        "contours": _file_stat(contours_path),
        "restrict_networks": sorted(restrict_networks) if restrict_networks else None,
        "route_caches": {
            date_key: {
                name: _file_stat(
                    Path(config.osm_route_cache_root) / date_key / f"{name}.parquet"
                )
                for name in ("relations", "ways", "stops")
            }
            for date_key in config.osm_source_ids
        },
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()


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
    calibrate.add_argument(
        "--networks",
        nargs="+",
        default=None,
        help="Optional subset of network ids to calibrate (for a single test site)",
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


_REVIEW_COVERAGE_THRESHOLD = 0.90
_REVIEW_LIST_LIMIT = 50
_RAIL_REVIEW_LIST_LIMIT = 30


def _candidate_family(mode: str) -> str:
    return "bus" if mode == "ferry" else mode


def _write_review_lists(path: Path, run: RelationCalibrationRun) -> None:
    """Split candidate route changes into a short review list and the rest.

    Section 5.6 point 3 (2026-10-14 decision): a candidate is eligible for
    review only if every date it was flagged on belongs to a network/date
    with at least 90% OSM relation coverage; eligible candidates are then
    ranked BHNS/express first, then by trips on the reference date. Bus and
    ferry candidates are capped at the top 50; rail candidates (kept by
    default like bus -- 2026-10-14 decision) get their own top-30-by-trips
    cap, since rail has no BHNS concept and would otherwise compete with
    bus/ferry for the same 50 slots. Every other candidate, of any family,
    is kept in ``not_applied`` with its evidence -- nothing is deleted, and
    neither list is ever applied automatically (only ``confirmed`` edits
    are). Candidates already in ``rejected`` (a reviewer's explicit no) are
    excluded so they are not re-surfaced on every rerun.
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    excluded = {
        (change["network"], route_id)
        for change in raw.get("confirmed", [])
        for route_id in change["route_ids"]
    }
    excluded |= {
        (candidate["network"], candidate["route_id"])
        for candidate in raw.get("rejected", [])
    }
    coverage = network_relation_coverage(run)
    grouped: dict[tuple[str, str], list] = {}
    for route in run.final_routes:
        key = (route.network, route.pattern.route_id)
        if (
            route.result.outcome in ("dropped", "kept-renamed")
            and key not in excluded
        ):
            grouped.setdefault(key, []).append(route)

    candidates = []
    for (network, route_id), routes in sorted(grouped.items()):
        evidence = max(routes, key=lambda route: route.result.covered_share)
        outcomes_by_date = {
            route.date_key: route.result.outcome for route in routes
        }
        coverage_by_date = {
            date_key: round(coverage.get((network, date_key), 0.0), 6)
            for date_key in outcomes_by_date
        }
        eligible = bool(coverage_by_date) and all(
            share >= _REVIEW_COVERAGE_THRESHOLD
            for share in coverage_by_date.values()
        )
        candidates.append(
            (
                _candidate_family(evidence.pattern.mode),
                eligible,
                evidence.pattern.is_bhns,
                evidence.pattern.trip_count,
                {
                    "id": f"candidate_{network}_{route_id}".replace(":", "_"),
                    "network": network,
                    "route_id": route_id,
                    "outcomes_by_date": outcomes_by_date,
                    "match_pass": evidence.result.match_pass,
                    "relation_ids": list(evidence.result.relation_ids),
                    "relation_refs": list(evidence.result.relation_refs),
                    "covered_share": round(evidence.result.covered_share, 6),
                    "trip_count": evidence.pattern.trip_count,
                    "is_bhns": evidence.pattern.is_bhns,
                    "network_coverage_by_date": coverage_by_date,
                },
            )
        )

    to_review_ids: set[str] = set()
    for family in {item[0] for item in candidates}:
        limit = (
            _RAIL_REVIEW_LIST_LIMIT if family == "rail" else _REVIEW_LIST_LIMIT
        )
        eligible_candidates = sorted(
            (item for item in candidates if item[0] == family and item[1]),
            key=lambda item: (item[2], item[3]),
            reverse=True,
        )
        to_review_ids |= {
            item[4]["id"] for item in eligible_candidates[:limit]
        }
    raw["to_review"] = [
        item[4] for item in candidates if item[4]["id"] in to_review_ids
    ]
    raw["not_applied"] = [
        item[4] for item in candidates if item[4]["id"] not in to_review_ids
    ]
    path.write_text(
        yaml.safe_dump(raw, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def _run_calibration(args: argparse.Namespace) -> int:
    config = load_gtfs_rebuild_config(args.config)

    def execute(scratch: Path) -> RelationCalibrationRun:
        signature = _calibration_run_signature(
            config,
            args.gtfs_inventory,
            args.sources,
            args.contours,
            args.networks,
        )
        signature_path = args.results_pickle.with_suffix(".signature.json")
        if args.results_pickle.is_file() and signature_path.is_file():
            previous = json.loads(signature_path.read_text(encoding="utf-8"))
            if previous.get("signature") == signature:
                logger.info(
                    "checkpoint exists and inputs unchanged, loading %s",
                    args.results_pickle,
                )
                with args.results_pickle.open("rb") as stream:
                    return pickle.load(stream)
            logger.info(
                "checkpoint inputs changed (e.g. a re-extracted OSM route "
                "cache or a config edit); recomputing %s",
                args.results_pickle,
            )
        run = run_relation_calibration(
            config,
            args.gtfs_inventory,
            args.sources,
            args.contours,
            scratch,
            restrict_networks=args.networks,
        )
        args.results_pickle.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.results_pickle.with_suffix(".tmp")
        with temporary.open("wb") as stream:
            pickle.dump(run, stream)
        temporary.replace(args.results_pickle)
        signature_path.write_text(
            json.dumps({"signature": signature}), encoding="utf-8"
        )
        return run

    scratch = args.scratch_dir or Path(
        "data/interim/gtfs_rebuild/calibration_scratch"
    )
    scratch.mkdir(parents=True, exist_ok=True)
    run = execute(scratch)
    pt_changes_path = Path("config/pt_changes.yaml")
    if args.networks is None:
        _write_chosen_config(args.config, run)
        _write_review_lists(pt_changes_path, run)
    else:
        logger.info(
            "subset calibration: leaving chosen config and candidates unchanged"
        )
    write_report(run, config, args.report, pt_changes_path=pt_changes_path)
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
