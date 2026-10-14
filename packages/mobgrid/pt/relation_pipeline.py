"""End-to-end relation-based calibration for historical GTFS rebuilding."""

from __future__ import annotations

import hashlib
import json
import logging
import pickle
import time
from dataclasses import dataclass, field
from pathlib import Path

import duckdb
import pyarrow as pa

from mobgrid.pt.calibrate import (
    load_all_network_patterns,
    reduce_to_main_test_area_patterns,
)
from mobgrid.pt.config import GtfsRebuildConfig, ModeFamily
from mobgrid.pt.epci import pattern_ids_within_epci
from mobgrid.pt.relation_tables import (
    CachedRouteRun,
    PrecomputeSummary,
    evaluate_cached_grid,
    precompute_relation_tables,
)
from mobgrid.pt.route_calibration import FamilyScore, RouteEvaluation, score_family
from mobgrid.pt.route_relations import (
    OSMRelation,
    RelationMatch,
    RoutePattern,
    RouteResult,
    choose_main_patterns,
    classify_network,
    evaluate_route,
    match_route,
    qualify_fallback_stops,
)

logger = logging.getLogger(__name__)
_CALIBRATED_FAMILIES: tuple[ModeFamily, ...] = ("bus", "tram", "metro")


@dataclass(frozen=True)
class RouteRun:
    """One route/date result with calibration and reporting metadata."""

    network: str
    date_key: str
    pattern: RoutePattern
    match: RelationMatch
    result: RouteResult
    expected: str
    known_case: bool
    case_id: str | None


@dataclass(frozen=True)
class GridPoint:
    """Metrics for one family-specific parameter combination."""

    mode_family: str
    r_m: int
    k: int
    theta: float
    geometry_share: float
    score: FamilyScore


@dataclass
class RelationCalibrationRun:
    """Persistent output of the relation-based calibration."""

    grid: list[GridPoint] = field(default_factory=list)
    chosen: dict[str, GridPoint] = field(default_factory=dict)
    final_routes: list[RouteRun] = field(default_factory=list)
    rural_epci_coverage: dict[str, dict[str, int]] = field(default_factory=dict)
    flagged_networks: set[tuple[str, str]] = field(default_factory=set)
    rail_route_modes: dict[str, str] = field(default_factory=dict)
    epci_routes: dict[str, set[tuple[str, str]]] = field(default_factory=dict)


def network_relation_coverage(
    run: RelationCalibrationRun,
) -> dict[tuple[str, str], float]:
    """Share of each network/date's routes that found any OSM relation.

    Computed over every family's final evaluation together (section 5.6
    point 5's basis), at a finer grain than the 50% not-testable cutoff;
    used to gate the 2026-10-14 review-list reduction at 90% coverage.
    """
    counts: dict[tuple[str, str], list[int]] = {}
    for route in run.final_routes:
        key = (route.network, route.date_key)
        matched, total = counts.setdefault(key, [0, 0])
        total += 1
        if route.match.relation_ids:
            matched += 1
        counts[key] = [matched, total]
    return {
        key: (matched / total if total else 0.0)
        for key, (matched, total) in counts.items()
    }


def _replace_checkpoint(temporary: Path, destination: Path) -> None:
    """Atomically publish a checkpoint despite transient Windows file locks."""
    for attempt in range(5):
        try:
            temporary.replace(destination)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.05 * (attempt + 1))


def patterns_from_table(table: pa.Table) -> list[RoutePattern]:
    """Convert ordered Arrow stop rows to one record per GTFS pattern."""
    rows = table.to_pylist()
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["pattern_id"]), []).append(row)
    patterns = []
    for pattern_id, stops in grouped.items():
        first = stops[0]
        patterns.append(
            RoutePattern(
                pattern_id,
                str(first["route_id"]),
                first["route_short_name"],
                first["route_long_name"],
                first["transport_mode"],
                first["agency_name"],
                int(first["trip_count"]),
                tuple((float(row["x"]), float(row["y"])) for row in stops),
            )
        )
    return patterns


def _expected(
    config: GtfsRebuildConfig,
    network: str,
    route_id: str,
    route_short_name: str | None,
    date_key: str,
) -> tuple[str, bool, str | None]:
    for case in config.known_cases:
        if (
            case.network == network
            and case.route_id in {route_id, route_short_name}
        ):
            expected = (
                case.expected_2022
                if date_key == "2022-01-01"
                else case.expected_2024
            )
            if expected is None:
                return "kept", False, case.id
            return expected, True, case.id
    return "kept", False, None


def _family(mode: str) -> str:
    return "bus" if mode == "ferry" else mode


def evaluate_networks(
    patterns: dict[str, list[RoutePattern]],
    relations: dict[str, list[OSMRelation]],
    config: GtfsRebuildConfig,
    *,
    r_m: int,
    k: int,
    theta: float,
    geometry_share: float,
    only_family: str | None = None,
    fallback_stops: dict[tuple[str, str], tuple[tuple[float, float], ...]]
    | None = None,
    match_cache: dict[tuple[str, str, str, int, float], RelationMatch]
    | None = None,
    fallback_cache: dict[
        tuple[str, str, int], tuple[tuple[float, float], ...]
    ]
    | None = None,
) -> tuple[list[RouteRun], set[tuple[str, str]]]:
    """Match and verify every main route, applying network testability first."""
    runs: list[RouteRun] = []
    flagged: set[tuple[str, str]] = set()
    for date_key, date_relations in relations.items():
        qualified_fallback = {}
        for mode in ("tram", "metro", "rail"):
            fallback_key = (date_key, mode, r_m)
            if fallback_cache is not None and fallback_key in fallback_cache:
                qualified = fallback_cache[fallback_key]
            else:
                qualified = qualify_fallback_stops(
                    (fallback_stops or {}).get((date_key, mode), ()),
                    mode,
                    date_relations,
                    r_m,
                )
                if fallback_cache is not None:
                    fallback_cache[fallback_key] = qualified
            qualified_fallback[mode] = qualified
        for network, network_patterns in patterns.items():
            all_selected = list(
                choose_main_patterns(network_patterns).values()
            )
            selected = [
                pattern
                for pattern in all_selected
                if only_family is None or _family(pattern.mode) == only_family
            ]
            all_matches = {}
            for pattern in all_selected:
                match_key = (
                    date_key,
                    network,
                    pattern.route_id,
                    r_m,
                    geometry_share,
                )
                if match_cache is not None and match_key in match_cache:
                    match = match_cache[match_key]
                else:
                    match = match_route(
                        pattern,
                        date_relations,
                        r_m=r_m,
                        geometry_share=geometry_share,
                    )
                    if match_cache is not None:
                        match_cache[match_key] = match
                all_matches[pattern.route_id] = match
            matches = {
                pattern.route_id: all_matches[pattern.route_id]
                for pattern in selected
            }
            testable = (
                classify_network(
                    sum(
                        bool(match.relation_ids)
                        for match in all_matches.values()
                    ),
                    len(all_selected),
                )
                == "testable"
            )
            if not testable and selected:
                flagged.add((date_key, network))
            relation_lookup = {
                relation.relation_id: relation for relation in date_relations
            }
            for pattern in selected:
                match = matches[pattern.route_id]
                matched_relations = tuple(
                    relation_lookup[relation_id]
                    for relation_id in match.relation_ids
                )
                result = evaluate_route(
                    pattern,
                    matched_relations,
                    match_pass=match.pass_name,
                    r_m=r_m,
                    k=k,
                    theta=theta,
                    fallback_stops=qualified_fallback.get(pattern.mode, ()),
                )
                if not testable:
                    result = RouteResult(
                        result.route_id,
                        "not-testable",
                        result.match_pass,
                        result.relation_ids,
                        result.relation_refs,
                        result.n,
                        result.covered,
                        result.covered_share,
                        result.start_index,
                        result.end_index,
                    )
                expected, known, case_id = _expected(
                    config,
                    network,
                    pattern.route_id,
                    pattern.short_name,
                    date_key,
                )
                runs.append(
                    RouteRun(
                        network,
                        date_key,
                        pattern,
                        match,
                        result,
                        expected,
                        known,
                        case_id,
                    )
                )
    return runs, flagged


def _family_score(runs: list[RouteRun], family: str) -> FamilyScore:
    return score_family(
        [
            RouteEvaluation(
                f"{run.network}:{run.date_key}:{run.pattern.route_id}",
                _family(run.pattern.mode),
                run.expected,
                run.result.outcome,
                run.known_case,
            )
            for run in runs
        ],
        family,
    )


def _rank(point: GridPoint) -> tuple[float, ...]:
    score = point.score
    return (
        score.known_correct,
        score.f1,
        -score.false_change_rate,
        -point.r_m,
        -point.geometry_share,
        -point.theta,
        -point.k,
    )


def calibrate_relations(
    connection: duckdb.DuckDBPyConnection,
    precompute: PrecomputeSummary,
    config: GtfsRebuildConfig,
    checkpoint_path: str | Path | None = None,
) -> tuple[
    list[GridPoint],
    dict[str, GridPoint],
    dict[
        tuple[str, int, int, float, float],
        tuple[list[CachedRouteRun], set[tuple[str, str]]],
    ],
]:
    """Search the parameter grid using cached scalar tables only."""
    signature_payload = {
        "format": "relation-table-grid-v1",
        "grid": config.calibration.model_dump(mode="json"),
        "precompute": json.loads(
            (precompute.cache_directory / "precompute.json").read_text(
                encoding="utf-8"
            )
        ),
    }
    signature = hashlib.sha256(
        json.dumps(signature_payload, sort_keys=True).encode()
    ).hexdigest()
    checkpoint = Path(checkpoint_path) if checkpoint_path is not None else None
    if checkpoint is not None and checkpoint.is_file():
        with checkpoint.open("rb") as stream:
            payload = pickle.load(stream)
        if payload.get("signature") == signature:
            grid: list[GridPoint] = payload["grid"]
            logger.info("loaded %s completed calibration points", len(grid))
        else:
            grid = []
            logger.info("calibration inputs changed; ignoring old checkpoint")
    else:
        grid = []
    completed = {
        (
            point.mode_family,
            point.r_m,
            point.k,
            point.theta,
            point.geometry_share,
        )
        for point in grid
    }
    chosen: dict[str, GridPoint] = {}
    total_points = (
        len(_CALIBRATED_FAMILIES)
        * len(config.calibration.r_m)
        * len(config.calibration.k)
        * len(config.calibration.theta)
        * len(config.calibration.geometry_share)
    )
    run_started = time.perf_counter()
    initial_completed = len(grid)
    table_started = time.perf_counter()
    evaluations = evaluate_cached_grid(
        connection,
        precompute,
        config,
        r_values=config.calibration.r_m,
        k_values=config.calibration.k,
        theta_values=config.calibration.theta,
        geometry_values=config.calibration.geometry_share,
    )
    logger.info(
        "evaluated cached route outcomes for the complete grid in %.1fs",
        time.perf_counter() - table_started,
    )
    for family in _CALIBRATED_FAMILIES:
        for r_m in config.calibration.r_m:
            for k in config.calibration.k:
                for theta in config.calibration.theta:
                    for geometry_share in config.calibration.geometry_share:
                        key = (family, r_m, k, theta, geometry_share)
                        if key in completed:
                            continue
                        point_started = time.perf_counter()
                        runs, _ = evaluations.get(
                            key,
                            ([], set()),
                        )
                        point = GridPoint(
                            family,
                            r_m,
                            k,
                            theta,
                            geometry_share,
                            _family_score(runs, family),
                        )
                        grid.append(point)
                        completed.add(key)
                        pt_elapsed = time.perf_counter() - point_started
                        new_completed = len(grid) - initial_completed
                        mean_elapsed = (
                            (time.perf_counter() - run_started) / new_completed
                        )
                        remaining = max(0, total_points - len(grid)) * mean_elapsed
                        logger.info(
                            "calibration point %s/%s: family=%s r=%s k=%s "
                            "theta=%s geometry_share=%s in %.1fs "
                            "(est. remaining %.1fs)",
                            len(grid),
                            total_points,
                            family,
                            r_m,
                            k,
                            theta,
                            geometry_share,
                            pt_elapsed,
                            remaining,
                        )
                        if checkpoint is not None:
                            checkpoint.parent.mkdir(parents=True, exist_ok=True)
                            temporary = checkpoint.with_suffix(".tmp")
                            with temporary.open("wb") as stream:
                                pickle.dump(
                                    {"signature": signature, "grid": grid},
                                    stream,
                                )
                            _replace_checkpoint(temporary, checkpoint)
    for point in grid:
        family = point.mode_family
        if family not in chosen or _rank(point) > _rank(chosen[family]):
            chosen[family] = point
    # Rail reuses metro's parameters (section 5.6 has no labelled rail known
    # case), but it is its own distinct family in `evaluations` (unlike
    # ferry, which is always merged into "bus"), so its score must be
    # recomputed on rail's own routes rather than aliasing metro's GridPoint
    # (which would silently report metro's known-case/false-change numbers
    # under the "rail" label).
    rail_params = chosen["metro"]
    rail_runs, _ = evaluations.get(
        (
            "rail",
            rail_params.r_m,
            rail_params.k,
            rail_params.theta,
            rail_params.geometry_share,
        ),
        ([], set()),
    )
    chosen["rail"] = GridPoint(
        "rail",
        rail_params.r_m,
        rail_params.k,
        rail_params.theta,
        rail_params.geometry_share,
        _family_score(rail_runs, "rail"),
    )
    chosen["ferry"] = chosen["bus"]
    return grid, chosen, evaluations


def run_relation_calibration(
    config: GtfsRebuildConfig,
    gtfs_inventory_csv: str | Path,
    sources_yaml: str | Path,
    contours_path: str | Path,
    scratch_dir: str | Path,
    *,
    restrict_networks: list[str] | None = None,
) -> RelationCalibrationRun:
    """Load GTFS/caches, calibrate, and evaluate selected family parameters."""
    connection = duckdb.connect()
    tables, rural_coverage = load_all_network_patterns(
        connection,
        config,
        gtfs_inventory_csv,
        contours_path,
        scratch_dir,
        restrict_networks,
    )
    tables = reduce_to_main_test_area_patterns(
        connection, tables, config, contours_path
    )
    patterns = {
        network: patterns_from_table(table) for network, table in tables.items()
    }
    epci_routes: dict[str, set[tuple[str, str]]] = {
        epci: set() for epci in config.test_epcis
    }
    for epci, reference in config.test_epcis.items():
        for network, table in tables.items():
            pattern_ids = pattern_ids_within_epci(
                connection, table, reference.siren
            )
            route_by_pattern = {
                pattern.pattern_id: pattern.route_id
                for pattern in patterns[network]
            }
            epci_routes[epci].update(
                (network, route_by_pattern[pattern_id])
                for pattern_id in pattern_ids
                if pattern_id in route_by_pattern
            )
    route_cache_directories = {}
    stop_cache_paths = {}
    for date_key in config.osm_source_ids:
        cache = Path(config.osm_route_cache_root) / date_key
        if not (cache / "_SUCCESS.json").is_file():
            raise FileNotFoundError(
                f"OSM relation cache missing for {date_key}: run extraction first"
            )
        route_cache_directories[date_key] = cache
        stop_cache = Path(config.osm_cache_root) / f"{date_key}.parquet"
        if stop_cache.is_file():
            stop_cache_paths[date_key] = stop_cache

    precompute_started = time.perf_counter()
    precompute = precompute_relation_tables(
        connection,
        tables,
        route_cache_directories,
        stop_cache_paths,
        Path(scratch_dir) / "relation_tables",
        config,
        max_r_m=max(config.calibration.r_m),
    )
    logger.info(
        "relation precompute: %s patterns, %s candidate relations, "
        "%s distance rows, %s name rows in %.1fs",
        precompute.pattern_count,
        precompute.candidate_relation_count,
        precompute.distance_count,
        precompute.name_count,
        time.perf_counter() - precompute_started,
    )
    grid, chosen, evaluations = calibrate_relations(
        connection,
        precompute,
        config,
        Path(scratch_dir) / "calibration_grid_tables.pkl",
    )
    final_routes: list[RouteRun] = []
    flagged: set[tuple[str, str]] = set()
    for family in (*_CALIBRATED_FAMILIES, "rail"):
        point = chosen[family]
        runs, family_flagged = evaluations.get(
            (
                family,
                point.r_m,
                point.k,
                point.theta,
                point.geometry_share,
            ),
            ([], set()),
        )
        final_routes.extend(runs)
        flagged |= family_flagged
    rail_modes = {
        str(run.pattern.short_name): run.pattern.mode
        for run in final_routes
        if run.network == "sncf"
        and run.pattern.short_name in {"7601", "951", "952", "953"}
    }
    return RelationCalibrationRun(
        grid,
        chosen,
        final_routes,
        rural_coverage,
        flagged,
        rail_modes,
        epci_routes,
    )
