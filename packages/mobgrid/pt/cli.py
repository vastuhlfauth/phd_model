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

from mobgrid.pt.config import (
    GtfsRebuildConfig,
    OpeningsListPolicy,
    load_gtfs_rebuild_config,
)
from mobgrid.pt.osm_route_extraction import (
    configure_extraction_connection,
    estimate_run,
    extract_osm_pt_routes,
    process_peak_memory_bytes,
    write_extraction_summary,
)
from mobgrid.pt.pt_changes import write_from_openings
from mobgrid.pt.pt_openings import (
    apply_openings_matches,
    resolve_and_extract,
    run_mapping,
    run_mapping_for_networks,
    run_mapping_grouped,
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

    map_openings = subparsers.add_parser("map-openings")
    map_openings.add_argument(
        "--openings-csv",
        type=Path,
        default=Path("config/French transit openings 2022 to 2026.csv"),
    )
    map_openings.add_argument(
        "--gtfs-inventory", type=Path, default=Path("config/gtfs_inventory.csv")
    )
    map_openings.add_argument("--resource-id", type=int, required=True)
    map_openings.add_argument(
        "--network-contains",
        required=True,
        help="Case-insensitive substring of the CSV's network column",
    )
    map_openings.add_argument("--scratch-dir", type=Path)
    map_openings.add_argument(
        "--output", type=Path, default=Path("config/pt_openings_mapping.csv")
    )
    map_openings.add_argument("--log", type=Path)

    apply_openings = subparsers.add_parser("apply-openings")
    apply_openings.add_argument(
        "--config", type=Path, default=Path("config/gtfs_rebuild.yaml")
    )
    apply_openings.add_argument(
        "--openings-csv",
        type=Path,
        default=Path("config/French transit openings 2022 to 2026.csv"),
    )
    apply_openings.add_argument(
        "--mapping-csv", type=Path, default=Path("config/pt_openings_mapping.csv")
    )
    apply_openings.add_argument(
        "--pt-changes", type=Path, default=Path("config/pt_changes.yaml")
    )
    apply_openings.add_argument("--log", type=Path)

    map_and_apply_all = subparsers.add_parser("map-and-apply-all")
    map_and_apply_all.add_argument(
        "--config", type=Path, default=Path("config/gtfs_rebuild.yaml")
    )
    map_and_apply_all.add_argument(
        "--openings-csv",
        type=Path,
        default=Path("config/French transit openings 2022 to 2026.csv"),
    )
    map_and_apply_all.add_argument(
        "--gtfs-inventory", type=Path, default=Path("config/gtfs_inventory.csv")
    )
    map_and_apply_all.add_argument(
        "--mapping-csv", type=Path, default=Path("config/pt_openings_mapping.csv")
    )
    map_and_apply_all.add_argument(
        "--pt-changes", type=Path, default=Path("config/pt_changes.yaml")
    )
    map_and_apply_all.add_argument(
        "--scratch-root", type=Path, default=Path("data/interim/pt_openings_mapping")
    )
    map_and_apply_all.add_argument(
        "--networks",
        nargs="+",
        default=None,
        help="Optional subset of CSV network strings to map (for testing)",
    )
    map_and_apply_all.add_argument("--log", type=Path)
    map_and_apply_all.add_argument("--summary", type=Path)
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


_INERT_OUTCOME_FAMILIES = frozenset(("bus", "ferry"))


def _write_chosen_config(path: Path, run: RelationCalibrationRun) -> None:
    """Write the calibration's recommended per-family parameters.

    Bus and ferry no longer use theta or cutting (``k``) to decide their
    outcome -- their rule is the fixed name/geometry-share threshold of
    section 5.6 point 2 (2026-10-15 decision) -- so both are written as
    ``null`` for those two families rather than the grid's arbitrary
    tie-break value, which would otherwise misleadingly look calibrated.
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw["chosen"] = {
        family: {
            "r_m": point.r_m,
            "k": None if family in _INERT_OUTCOME_FAMILIES else point.k,
            "geometry_share": point.geometry_share,
            "theta": (
                None if family in _INERT_OUTCOME_FAMILIES else point.theta
            ),
        }
        for family, point in sorted(run.chosen.items())
    }
    path.write_text(
        "# TODO(confirm): recommended by the relation-based calibration.\n"
        + yaml.safe_dump(raw, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


_RAIL_REVIEW_COVERAGE_THRESHOLD = 0.90
_RAIL_REVIEW_LIST_LIMIT = 30


def _candidate_family(mode: str) -> str:
    return "bus" if mode == "ferry" else mode


def _write_review_lists(path: Path, run: RelationCalibrationRun) -> None:
    """Split candidate route changes into a short review list and the rest.

    2026-10-15 decision (section 5.6 point 2): bus/ferry no longer use a
    calibrated theta or a network-coverage eligibility gate for their
    outcome, so their review list is simplified to match -- ``to_review``
    keeps every BHNS/express candidate plus every candidate dropped (on
    any date) under the new fixed name/geometry-share rule, ranked by
    trips, with no cap; every other bus/ferry candidate (kept-renamed,
    non-BHNS, never dropped) goes to ``not_applied``. Rail has no BHNS
    concept and is always screening-only like bus, so it keeps its own
    90%-network-coverage gate and top-30-by-trips cap (2026-10-14
    decision), unaffected by this change. ``network_coverage_by_date`` is
    still recorded for every candidate as context, even where it no
    longer gates eligibility. Candidates already in ``rejected`` (a
    reviewer's explicit no) are excluded so they are not re-surfaced on
    every rerun.
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
        family = _candidate_family(evidence.pattern.mode)
        dropped_any = any(
            outcome == "dropped" for outcome in outcomes_by_date.values()
        )
        if family == "rail":
            eligible = bool(coverage_by_date) and all(
                share >= _RAIL_REVIEW_COVERAGE_THRESHOLD
                for share in coverage_by_date.values()
            )
        else:
            eligible = evidence.pattern.is_bhns or dropped_any
        candidates.append(
            (
                family,
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
        eligible_candidates = sorted(
            (item for item in candidates if item[0] == family and item[1]),
            key=lambda item: (item[2], item[3]),
            reverse=True,
        )
        if family == "rail":
            eligible_candidates = eligible_candidates[:_RAIL_REVIEW_LIST_LIMIT]
        to_review_ids |= {item[4]["id"] for item in eligible_candidates}
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


def _run_map_openings(args: argparse.Namespace) -> int:
    scratch = args.scratch_dir or (
        Path("data/interim/pt_openings_mapping") / str(args.resource_id)
    )
    table_dir = resolve_and_extract(args.gtfs_inventory, args.resource_id, scratch)
    proposals = run_mapping(
        args.openings_csv, table_dir, args.network_contains, args.output
    )
    counts: dict[str, int] = {}
    for proposal in proposals:
        counts[proposal.match_confidence] = counts.get(proposal.match_confidence, 0) + 1
    logger.info(
        "proposed matches for %s rows (network contains %r): %s -> %s",
        len(proposals),
        args.network_contains,
        counts,
        args.output,
    )
    return 0


def _load_openings_list_policy(config_path: Path) -> OpeningsListPolicy:
    config = load_gtfs_rebuild_config(config_path)
    policy = config.national_policy
    if policy is None:
        raise ValueError(
            f"{config_path} has no national_policy; configure "
            "national_policy.openings_list before running apply-openings"
        )
    return policy.openings_list


def _log_openings_application(result, pt_changes_path: Path) -> None:
    """Log one ``apply_openings_matches`` result (2026-10-16 logging fix).

    WARNING only for a row carrying a real ``remove`` instruction that
    could not be applied (a genuine gap); everything not applied by
    design (low confidence, no ``remove`` state yet, or a change_type
    that never gives an instruction) is an INFO count per reason, never
    one line per row. "Applied" is reported by row (``opening_id``), with
    the route-level edit count given separately (2026-10-16 bookkeeping
    fix): a row may resolve to several routes, so the two numbers differ
    and must not be added together with the other, row-level counts.
    """
    for line in result.warnings:
        logger.warning("remove instruction not applied: %s", line)
    for reason, count in sorted(result.not_applied_by_design.items()):
        logger.info("not applied by design (%s): %d row(s)", reason, count)
    for line in result.closed_before_2026:
        logger.info("known gap: %s", line)
    logger.info(
        "applied %d openings-list rows (%d route-level edits) to %s (%d "
        "warnings -- remove instructions that failed to match, %d not "
        "applied by design, %d known gaps)",
        len(result.applied_opening_ids),
        len(result.applied),
        pt_changes_path,
        len(result.warnings),
        sum(result.not_applied_by_design.values()),
        len(result.closed_before_2026),
    )


def _run_apply_openings(args: argparse.Namespace) -> int:
    openings_list = _load_openings_list_policy(args.config)
    result = apply_openings_matches(
        args.openings_csv,
        args.mapping_csv,
        include_row_confidence=openings_list.include_row_confidence,
        apply_match_confidence=openings_list.apply_match_confidence,
    )
    write_from_openings(args.pt_changes, result.applied)
    _log_openings_application(result, args.pt_changes)
    return 0


def _write_map_and_apply_all_summary(
    path: Path,
    *,
    mapped_networks: list[str],
    failed_networks: list[str],
    elapsed_seconds: float,
    result,
    mapping_csv: Path,
    pt_changes: Path,
) -> None:
    text = f"""# PT openings: map and apply all networks, summary

## Inputs and outputs

- Mapping CSV: `{mapping_csv}`
- PT changes: `{pt_changes}`
- Networks mapped this run: {len(mapped_networks)}
- Networks that failed to map (download/extraction error; batch
  continued): {len(failed_networks)}
- Elapsed: {elapsed_seconds / 60:.1f} minutes

## Applied

- Applied: {len(result.applied_opening_ids)} rows ({len(result.applied)}
  route-level edits -- a row may resolve to several routes)
- Remove instructions not applied (needs attention; one WARNING logged
  for each): {len(result.warnings)}
- Not applied by design (low confidence, no remove state yet, or a
  change_type that never gives an instruction), by reason:
{chr(10).join(
    f"  - {reason}: {count}"
    for reason, count in sorted(result.not_applied_by_design.items())
) or "  - None."}
- Closed before 2026 (known gap): {len(result.closed_before_2026)}

## Warnings

{chr(10).join(f"- {line}" for line in failed_networks) or "- None."}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run_map_and_apply_all(args: argparse.Namespace) -> int:
    config = load_gtfs_rebuild_config(args.config)
    policy = config.national_policy
    if policy is None:
        raise ValueError(
            f"{args.config} has no national_policy; run map-and-apply-all after "
            "configuring national_policy.openings_list.network_resource_ids"
        )
    openings_list = policy.openings_list
    started = time.perf_counter()
    mapped: list[str] = []
    failed: list[str] = []
    wanted = set(args.networks) if args.networks else None

    # Resolved resource ids are shared across several network-name
    # aliases (e.g. "IDFM"/"RATP (IDFM)"/"Keolis Tisse (IDFM)" all read
    # resource 80921) and sometimes the mode-split entries too; extracted
    # at most once per run regardless of how many places reference it
    # (2026-10-16 fix, section 5.6 point 4).
    extracted_table_dirs: dict[int, Path] = {}

    def get_table_dir(resource_id: int) -> Path:
        if resource_id not in extracted_table_dirs:
            scratch = args.scratch_root / str(resource_id)
            extracted_table_dirs[resource_id] = resolve_and_extract(
                args.gtfs_inventory, resource_id, scratch
            )
        return extracted_table_dirs[resource_id]

    networks_by_resource: dict[int, list[str]] = {}
    for network, resource_id in openings_list.network_resource_ids.items():
        if wanted is not None and network not in wanted:
            continue
        networks_by_resource.setdefault(resource_id, []).append(network)

    for resource_id, networks in sorted(networks_by_resource.items()):
        networks = sorted(networks)
        label = ", ".join(networks)
        try:
            table_dir = get_table_dir(resource_id)
            proposals = run_mapping_for_networks(
                args.openings_csv, table_dir, networks, args.mapping_csv
            )
            logger.info(
                "mapped %s (resource %s): %d rows", label, resource_id, len(proposals)
            )
            mapped.extend(networks)
        except Exception as error:  # noqa: BLE001 -- one resource must not abort the batch
            logger.warning(
                "failed to map %s (resource %s): %s", label, resource_id, error
            )
            failed.append(f"{label} (resource {resource_id}): {error}")

    for network, resource_by_mode in sorted(
        openings_list.mode_split_network_resource_ids.items()
    ):
        if wanted is not None and network not in wanted:
            continue
        try:
            table_dirs = {
                mode: get_table_dir(resource_id)
                for mode, resource_id in resource_by_mode.items()
            }
            proposals = run_mapping_grouped(
                args.openings_csv, network, table_dirs, args.mapping_csv
            )
            logger.info("mapped %r (mode-split): %d rows", network, len(proposals))
            mapped.append(network)
        except Exception as error:  # noqa: BLE001 -- one network must not abort the batch
            logger.warning("failed to map %r (mode-split): %s", network, error)
            failed.append(f"{network} (mode-split): {error}")

    for network, reason in sorted(openings_list.unresolved_networks.items()):
        logger.info("skipped %r (no configured resource): %s", network, reason)

    result = apply_openings_matches(
        args.openings_csv,
        args.mapping_csv,
        include_row_confidence=openings_list.include_row_confidence,
        apply_match_confidence=openings_list.apply_match_confidence,
    )
    write_from_openings(args.pt_changes, result.applied)
    _log_openings_application(result, args.pt_changes)
    logger.info(
        "mapped %d networks (%d failed), applied %d openings-list rows to %s",
        len(mapped),
        len(failed),
        len(result.applied_opening_ids),
        args.pt_changes,
    )
    summary = args.summary or _default_artifact(
        "pt_openings_map_and_apply_all", "_summary.md"
    )
    _write_map_and_apply_all_summary(
        summary,
        mapped_networks=mapped,
        failed_networks=failed,
        elapsed_seconds=time.perf_counter() - started,
        result=result,
        mapping_csv=args.mapping_csv,
        pt_changes=args.pt_changes,
    )
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    """Run one resumable extraction or calibration job."""
    args = _parser().parse_args(argv)
    if args.command == "extract-osm-routes":
        task = f"osm_pt_routes_{args.date}"
    elif args.command == "map-openings":
        task = f"pt_openings_mapping_{args.resource_id}"
    elif args.command == "apply-openings":
        task = "pt_openings_apply"
    elif args.command == "map-and-apply-all":
        task = "pt_openings_map_and_apply_all"
    else:
        task = "gtfs_calibration"
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
    if args.command == "map-openings":
        return _run_map_openings(args)
    if args.command == "apply-openings":
        return _run_apply_openings(args)
    if args.command == "map-and-apply-all":
        return _run_map_and_apply_all(args)
    return _run_calibration(args)


if __name__ == "__main__":
    raise SystemExit(main())
