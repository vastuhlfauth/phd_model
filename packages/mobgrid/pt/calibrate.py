"""Driver for the step 0 GTFS rebuilding calibration (section 5.6).

Orchestrates: resolving configured GTFS/OSM sources to local files, loading
patterns per network (regional feeds restricted to the test EPCIs), caching
OSM public-transport stops once per dated extract, matching stops at each
candidate radius, and scoring/cutting patterns over the (r, theta, k) grid
against the known cases of section 5.6's calibration table.
"""

from __future__ import annotations

import csv
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.compute as pc
from acquire.manifest import load_manifest

from mobgrid.pt.config import GtfsRebuildConfig, KnownCase, ModeFamily
from mobgrid.pt.epci import load_epci_polygons_3035, pattern_ids_within_epci
from mobgrid.pt.gtfs_rebuild import (
    PatternMatch,
    PatternResult,
    match_stops,
    patterns_from_matches,
    rebuild_pattern,
    route_outcome,
)
from mobgrid.pt.stop_tables import (
    extract_gtfs_tables,
    load_gtfs_patterns,
    read_osm_pt_stops_cache,
    write_osm_pt_stops_cache,
)

logger = logging.getLogger(__name__)
_SCORED_FAMILIES: tuple[ModeFamily, ...] = ("bus", "tram", "metro")
_REGIONAL_NETWORKS = ("lio_occitanie", "remi")


def resolve_gtfs_local_path(inventory_csv: str | Path, resource_id: int) -> Path:
    """Resolve a configured transport.data.gouv.fr resource id to its local ZIP."""
    with Path(inventory_csv).open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row.get("resource_id") and int(row["resource_id"]) == resource_id:
                return Path(row["local_path"])
    raise KeyError(f"GTFS resource {resource_id} not found in {inventory_csv}")


def resolve_osm_local_path(sources_yaml: str | Path, source_id: str) -> Path:
    """Resolve a configured OSM source id (for example ``osm-2022``) to its PBF."""
    for source in load_manifest(sources_yaml):
        if source.id == source_id:
            return Path(source.local_path)
    raise KeyError(f"OSM source {source_id} not found in {sources_yaml}")


def load_all_network_patterns(
    connection: duckdb.DuckDBPyConnection,
    config: GtfsRebuildConfig,
    gtfs_inventory_csv: str | Path,
    contours_path: str | Path,
    scratch_dir: str | Path,
) -> tuple[dict[str, pa.Table], dict[str, dict[str, int]]]:
    """Load every configured network's patterns, restricting regional feeds.

    ``idfm``/``star_rennes`` are restricted to the metro route ids of the
    known cases (section 5.6's "Metros" calibration). ``lio_occitanie``,
    ``remi`` and the rail manual-review network are restricted to patterns
    with at least one stop inside one of the five test EPCI polygons
    (section 5.6's EPCI coverage note). Other networks (urban operators
    already scoped to one EPCI) are loaded in full. Returns the restricted
    pattern tables and, per test EPCI, how many patterns of each regional
    or manual-review network reach it (used for the rural coverage check).
    """
    metro_route_ids = {
        network: [
            case.route_id
            for case in config.known_cases
            if case.network == network
        ]
        for network in ("idfm", "star_rennes")
    }
    tables: dict[str, pa.Table] = {}
    for key, network in config.networks.items():
        local_path = resolve_gtfs_local_path(gtfs_inventory_csv, network.resource_id)
        table_dir = Path(scratch_dir) / key
        extract_gtfs_tables(local_path, table_dir)
        route_ids = metro_route_ids.get(key)
        start = time.time()
        tables[key] = load_gtfs_patterns(
            connection, table_dir, config.reference_date, route_ids=route_ids
        )
        logger.info(
            "loaded %s patterns for %s in %.1fs",
            tables[key].num_rows,
            key,
            time.time() - start,
        )

    sirens = {name: epci.siren for name, epci in config.test_epcis.items()}
    restricted_keys = [*_REGIONAL_NETWORKS, *config.manual_review_networks]
    restricted_keys = [key for key in restricted_keys if key in tables]
    coverage: dict[str, dict[str, int]] = {name: {} for name in config.test_epcis}
    if restricted_keys:
        start = time.time()
        load_epci_polygons_3035(connection, contours_path, list(sirens.values()))
        logger.info("loaded EPCI polygons in %.1fs", time.time() - start)
        for key in restricted_keys:
            table = tables[key]
            keep_ids: set[str] = set()
            if table.num_rows > 0:
                for epci_name, siren in sirens.items():
                    start = time.time()
                    ids = pattern_ids_within_epci(connection, table, siren)
                    logger.info(
                        "matched %s patterns of %s to %s in %.1fs",
                        len(ids),
                        key,
                        epci_name,
                        time.time() - start,
                    )
                    coverage[epci_name][key] = len(ids)
                    keep_ids |= ids
            mask = pc.is_in(
                table.column("pattern_id"),
                value_set=pa.array(sorted(keep_ids), type=pa.string()),
            )
            tables[key] = table.filter(mask)
    return tables, coverage


def compute_bboxes(
    tables: dict[str, pa.Table], margin_deg: float = 0.05
) -> list[tuple[float, float, float, float]]:
    """WGS84 bounding boxes (with margin) of every network's pattern stops."""
    bboxes = []
    for table in tables.values():
        if table.num_rows == 0:
            continue
        lon = table.column("lon")
        lat = table.column("lat")
        bboxes.append((
            pc.min(lon).as_py() - margin_deg,
            pc.min(lat).as_py() - margin_deg,
            pc.max(lon).as_py() + margin_deg,
            pc.max(lat).as_py() + margin_deg,
        ))
    return bboxes


def ensure_osm_cache(
    connection: duckdb.DuckDBPyConnection,
    config: GtfsRebuildConfig,
    sources_yaml: str | Path,
    bboxes: list[tuple[float, float, float, float]],
) -> dict[str, Path]:
    """Build (if missing) and return the cached OSM stops Parquet per date."""
    cache_paths: dict[str, Path] = {}
    for stamp, source_id in config.osm_source_ids.items():
        cache_path = Path(config.osm_cache_root) / f"{stamp}.parquet"
        if not cache_path.is_file():
            start = time.time()
            pbf_path = resolve_osm_local_path(sources_yaml, source_id)
            write_osm_pt_stops_cache(connection, pbf_path, cache_path, bboxes)
            logger.info(
                "cached OSM public-transport stops for %s in %.1fs",
                stamp,
                time.time() - start,
            )
        cache_paths[stamp] = cache_path
    return cache_paths


@dataclass
class PatternEvaluation:
    """One pattern's result, with its expected outcome if known (section 5.6)."""

    network: str
    date_key: str
    pattern_id: str
    route_id: str
    mode_family: ModeFamily
    result: PatternResult
    expected: str | None  # None: no ground truth (default-kept or manual review)
    case_id: str | None = None


def _expected_outcome(
    network: str,
    route_id: str,
    date_key: str,
    known_cases_by_route: dict[tuple[str, str], KnownCase],
) -> tuple[str | None, str | None]:
    case = known_cases_by_route.get((network, route_id))
    if case is None:
        return "kept", None  # default: unlisted lines are expected unchanged
    expected = case.expected_2022 if date_key == "2022-01-01" else case.expected_2024
    return expected, case.id


def compute_matches(
    connection: duckdb.DuckDBPyConnection,
    tables: dict[str, pa.Table],
    osm_cache_paths: dict[str, Path],
    r_m: float,
) -> dict[tuple[str, str], list[PatternMatch]]:
    """Match every network's pattern stops at both OSM dates, for one radius r.

    Keyed by ``(date_key, network)``; reused across every ``(k, theta)``
    combination so the DuckDB spatial join only runs once per radius.
    """
    matches: dict[tuple[str, str], list[PatternMatch]] = {}
    start = time.time()
    for date_key, cache_path in osm_cache_paths.items():
        osm_stops = read_osm_pt_stops_cache(connection, cache_path)
        for network, table in tables.items():
            if table.num_rows == 0:
                matches[(date_key, network)] = []
                continue
            matched = match_stops(connection, table, osm_stops, r_m)
            matches[(date_key, network)] = patterns_from_matches(matched)
    logger.info("matched all networks at r=%sm in %.1fs", r_m, time.time() - start)
    return matches


def evaluate_matches(
    matches: dict[tuple[str, str], list[PatternMatch]],
    config: GtfsRebuildConfig,
    k: int,
    theta_by_family: dict[ModeFamily, float],
) -> list[PatternEvaluation]:
    """Score and cut precomputed matches (cheap: no DuckDB access here)."""
    known_cases_by_route = {
        (case.network, case.route_id): case for case in config.known_cases
    }
    evaluations: list[PatternEvaluation] = []
    for (date_key, network), pattern_matches in matches.items():
        for match in pattern_matches:
            theta = theta_by_family.get(match.mode_family)
            if theta is None:
                continue
            result = rebuild_pattern(match, theta, k)
            expected, case_id = _expected_outcome(
                network, match.route_id, date_key, known_cases_by_route
            )
            evaluations.append(
                PatternEvaluation(
                    network,
                    date_key,
                    match.pattern_id,
                    match.route_id,
                    match.mode_family,
                    result,
                    expected,
                    case_id,
                )
            )
    return evaluations


@dataclass
class ConfusionCounts:
    """Three-way outcome counts for one (mode_family, r, theta, k) combination."""

    mode_family: str
    r_m: float
    theta: float
    k: int
    correct: int = 0
    total: int = 0
    true_positive: int = 0  # expected != kept, obtained != kept
    false_positive: int = 0  # expected == kept, obtained != kept
    false_negative: int = 0  # expected != kept, obtained == kept

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    @property
    def precision(self) -> float:
        denominator = self.true_positive + self.false_positive
        return self.true_positive / denominator if denominator else 1.0

    @property
    def recall(self) -> float:
        denominator = self.true_positive + self.false_negative
        return self.true_positive / denominator if denominator else 1.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


def score(
    evaluations: list[PatternEvaluation],
    mode_family: str,
    r_m: float,
    theta: float,
    k: int,
) -> ConfusionCounts:
    """Route-level (worst-case across a route's patterns) confusion counts."""
    by_route: dict[tuple[str, str, str], list[PatternEvaluation]] = {}
    for evaluation in evaluations:
        if evaluation.mode_family != mode_family or evaluation.expected is None:
            continue
        by_route.setdefault(
            (evaluation.network, evaluation.route_id, evaluation.date_key), []
        ).append(evaluation)
    counts = ConfusionCounts(mode_family, r_m, theta, k)
    for route_evaluations in by_route.values():
        expected = route_evaluations[0].expected
        obtained = route_outcome([item.result for item in route_evaluations])
        counts.total += 1
        if obtained == expected:
            counts.correct += 1
        expected_positive = expected != "kept"
        obtained_positive = obtained != "kept"
        if expected_positive and obtained_positive:
            counts.true_positive += 1
        elif not expected_positive and obtained_positive:
            counts.false_positive += 1
        elif expected_positive and not obtained_positive:
            counts.false_negative += 1
    return counts


@dataclass
class GridSearchResult:
    """Full score table plus the recommended parameters (section 5.6)."""

    grid: list[ConfusionCounts] = field(default_factory=list)
    chosen_r_m: float = 0.0
    chosen_k: int = 0
    chosen_theta: dict[str, float] = field(default_factory=dict)


def grid_search(
    connection: duckdb.DuckDBPyConnection,
    tables: dict[str, pa.Table],
    osm_cache_paths: dict[str, Path],
    config: GtfsRebuildConfig,
) -> GridSearchResult:
    """Search r, theta (per mode family) and k against the known cases.

    The DuckDB spatial match only runs once per candidate ``r`` (reused
    across every ``k``/``theta``); ``theta`` is searched independently per
    mode family, since a pattern's drop/cut decision depends only on its
    own family's threshold. The final (r, k) pair maximises the summed F1
    of bus, tram and metro (the families with known cases); rail has no
    known case and reuses the chosen metro theta (section 5.6).
    """
    grid_rows: list[ConfusionCounts] = []
    best_by_rk: dict[tuple[float, int], dict[str, ConfusionCounts]] = {}
    for r_m in config.calibration.r_m:
        matches = compute_matches(connection, tables, osm_cache_paths, r_m)
        for k in config.calibration.k:
            best_per_family: dict[str, ConfusionCounts] = {}
            for theta in config.calibration.theta:
                theta_by_family = {
                    family: theta for family in ("bus", "tram", "metro", "rail")
                }
                evaluations = evaluate_matches(matches, config, k, theta_by_family)
                for family in _SCORED_FAMILIES:
                    counts = score(evaluations, family, r_m, theta, k)
                    grid_rows.append(counts)
                    current_best = best_per_family.get(family)
                    if current_best is None or (counts.f1, counts.accuracy) > (
                        current_best.f1,
                        current_best.accuracy,
                    ):
                        best_per_family[family] = counts
            best_by_rk[(r_m, k)] = best_per_family
    best_rk = max(
        best_by_rk, key=lambda rk: sum(c.f1 for c in best_by_rk[rk].values())
    )
    chosen = best_by_rk[best_rk]
    chosen_theta = {family: chosen[family].theta for family in _SCORED_FAMILIES}
    chosen_theta["rail"] = chosen_theta["metro"]
    return GridSearchResult(grid_rows, best_rk[0], best_rk[1], chosen_theta)


@dataclass
class CalibrationRun:
    """Full output of one step 0 calibration run (section 5.6)."""

    grid_result: GridSearchResult
    final_evaluations: list[PatternEvaluation]
    rural_epci_coverage: dict[str, dict[str, int]]


def run_calibration(
    config: GtfsRebuildConfig,
    gtfs_inventory_csv: str | Path,
    sources_yaml: str | Path,
    contours_path: str | Path,
    scratch_dir: str | Path,
) -> CalibrationRun:
    """Run the full step 0 calibration: load, cache, match, score and cut."""
    connection = duckdb.connect()
    tables, rural_epci_coverage = load_all_network_patterns(
        connection, config, gtfs_inventory_csv, contours_path, scratch_dir
    )
    bboxes = compute_bboxes(tables)
    osm_cache_paths = ensure_osm_cache(connection, config, sources_yaml, bboxes)
    grid_result = grid_search(connection, tables, osm_cache_paths, config)
    final_matches = compute_matches(
        connection, tables, osm_cache_paths, grid_result.chosen_r_m
    )
    final_evaluations = evaluate_matches(
        final_matches, config, grid_result.chosen_k, grid_result.chosen_theta
    )
    return CalibrationRun(grid_result, final_evaluations, rural_epci_coverage)

