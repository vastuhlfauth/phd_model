"""End-to-end relation-based calibration for historical GTFS rebuilding."""

from __future__ import annotations

import hashlib
import json
import logging
import pickle
from dataclasses import dataclass, field
from pathlib import Path

import duckdb
import pyarrow as pa

from mobgrid.pt.calibrate import (
    load_all_network_patterns,
)
from mobgrid.pt.config import GtfsRebuildConfig, ModeFamily
from mobgrid.pt.epci import pattern_ids_within_epci
from mobgrid.pt.route_calibration import FamilyScore, RouteEvaluation, score_family
from mobgrid.pt.route_relations import (
    OSMRelation,
    OSMWay,
    RelationMatch,
    RoutePattern,
    RouteResult,
    choose_main_patterns,
    classify_network,
    evaluate_route,
    match_route,
    qualify_fallback_stops,
)
from mobgrid.pt.stop_tables import read_osm_pt_stops_cache

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


def _route_mode(route: str) -> str:
    return {
        "bus": "bus",
        "trolleybus": "bus",
        "coach": "bus",
        "tram": "tram",
        "light_rail": "tram",
        "subway": "metro",
        "monorail": "metro",
        "train": "rail",
        "ferry": "ferry",
    }[route]


def load_osm_relations(
    connection: duckdb.DuckDBPyConnection, directory: str | Path
) -> list[OSMRelation]:
    """Load one dated relation cache into compact matching records."""
    root = Path(directory)
    relation_rows = connection.execute(
        "SELECT relation_id, ref, name, network, operator, route "
        "FROM read_parquet(?)",
        [str(root / "relations.parquet")],
    ).fetchall()
    ways_by_relation: dict[int, list[OSMWay]] = {}
    for row in connection.execute(
        "SELECT relation_id, points, railway, highway, construction, lifecycle "
        "FROM read_parquet(?) ORDER BY relation_id, sequence",
        [str(root / "ways.parquet")],
    ).fetchall():
        points = tuple((float(point["x"]), float(point["y"])) for point in row[1])
        ways_by_relation.setdefault(row[0], []).append(
            OSMWay(points, row[2], row[3], row[4], row[5])
        )
    stops_by_relation: dict[int, list[tuple[float, float]]] = {}
    for relation_id, x, y in connection.execute(
        "SELECT relation_id, x, y FROM read_parquet(?) "
        "ORDER BY relation_id, sequence",
        [str(root / "stops.parquet")],
    ).fetchall():
        stops_by_relation.setdefault(relation_id, []).append((x, y))
    return [
        OSMRelation(
            relation_id,
            ref,
            name,
            network,
            operator,
            _route_mode(route),
            tuple(stops_by_relation.get(relation_id, ())),
            tuple(ways_by_relation.get(relation_id, ())),
        )
        for relation_id, ref, name, network, operator, route in relation_rows
    ]


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
    patterns: dict[str, list[RoutePattern]],
    relations: dict[str, list[OSMRelation]],
    config: GtfsRebuildConfig,
    fallback_stops: dict[tuple[str, str], tuple[tuple[float, float], ...]]
    | None = None,
    checkpoint_path: str | Path | None = None,
) -> tuple[list[GridPoint], dict[str, GridPoint]]:
    """Search each mode family, prioritising exact known cases then false changes."""
    signature_payload = {
        "grid": config.calibration.model_dump(mode="json"),
        "patterns": {
            network: [
                (pattern.pattern_id, pattern.trip_count)
                for pattern in network_patterns
            ]
            for network, network_patterns in patterns.items()
        },
        "relations": {
            date_key: [relation.relation_id for relation in date_relations]
            for date_key, date_relations in relations.items()
        },
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
    match_cache: dict[
        tuple[str, str, str, int, float], RelationMatch
    ] = {}
    fallback_cache: dict[
        tuple[str, str, int], tuple[tuple[float, float], ...]
    ] = {}
    for family in _CALIBRATED_FAMILIES:
        for r_m in config.calibration.r_m:
            for k in config.calibration.k:
                for theta in config.calibration.theta:
                    for geometry_share in config.calibration.geometry_share:
                        key = (family, r_m, k, theta, geometry_share)
                        if key in completed:
                            continue
                        runs, _ = evaluate_networks(
                            patterns,
                            relations,
                            config,
                            r_m=r_m,
                            k=k,
                            theta=theta,
                            geometry_share=geometry_share,
                            only_family=family,
                            fallback_stops=fallback_stops,
                            match_cache=match_cache,
                            fallback_cache=fallback_cache,
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
                        if checkpoint is not None:
                            checkpoint.parent.mkdir(parents=True, exist_ok=True)
                            temporary = checkpoint.with_suffix(".tmp")
                            with temporary.open("wb") as stream:
                                pickle.dump(
                                    {"signature": signature, "grid": grid},
                                    stream,
                                )
                            temporary.replace(checkpoint)
    for point in grid:
        family = point.mode_family
        if family not in chosen or _rank(point) > _rank(chosen[family]):
            chosen[family] = point
    chosen["rail"] = chosen["metro"]
    chosen["ferry"] = chosen["bus"]
    return grid, chosen


def run_relation_calibration(
    config: GtfsRebuildConfig,
    gtfs_inventory_csv: str | Path,
    sources_yaml: str | Path,
    contours_path: str | Path,
    scratch_dir: str | Path,
) -> RelationCalibrationRun:
    """Load GTFS/caches, calibrate, and evaluate selected family parameters."""
    connection = duckdb.connect()
    tables, rural_coverage = load_all_network_patterns(
        connection, config, gtfs_inventory_csv, contours_path, scratch_dir
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
    relation_caches: dict[str, list[OSMRelation]] = {}
    fallback_stops: dict[
        tuple[str, str], tuple[tuple[float, float], ...]
    ] = {}
    for date_key, source_id in config.osm_source_ids.items():
        cache = Path(config.osm_route_cache_root) / date_key
        if not (cache / "_SUCCESS.json").is_file():
            raise FileNotFoundError(
                f"OSM relation cache missing for {date_key}: run extraction first"
            )
        relation_caches[date_key] = load_osm_relations(connection, cache)
        stop_cache = Path(config.osm_cache_root) / f"{date_key}.parquet"
        if stop_cache.is_file():
            rows = read_osm_pt_stops_cache(connection, stop_cache).fetchall()
            for mode in ("tram", "metro", "rail"):
                stops = tuple(
                    (float(row[3]), float(row[4]))
                    for row in rows
                    if row[2] == mode
                )
                fallback_stops[(date_key, mode)] = stops

    grid, chosen = calibrate_relations(
        patterns,
        relation_caches,
        config,
        fallback_stops,
        Path(scratch_dir) / "calibration_grid.pkl",
    )
    final_routes: list[RouteRun] = []
    flagged: set[tuple[str, str]] = set()
    for family in _CALIBRATED_FAMILIES:
        point = chosen[family]
        runs, family_flagged = evaluate_networks(
            patterns,
            relation_caches,
            config,
            r_m=point.r_m,
            k=point.k,
            theta=point.theta,
            geometry_share=point.geometry_share,
            only_family=family,
            fallback_stops=fallback_stops,
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
