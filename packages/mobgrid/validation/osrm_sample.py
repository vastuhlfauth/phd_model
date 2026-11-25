"""Seeded pilot-node sampling for the section 13 OSRM comparison."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Literal

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import shapely
from pydantic import BaseModel, ConfigDict, Field, model_validator
from shapely import STRtree

from mobgrid.graph.config import load_search_config
from mobgrid.graph.csr import MODES, CSRGraph, load_graph
from mobgrid.graph.dijkstra import SearchWorkspace, search


class SampleSettings(BaseModel):
    """Sampling distances in metres, cutoff times in the search config."""

    model_config = ConfigDict(extra="forbid")

    graph_directory: Path
    edges_path: Path
    edge_costs_path: Path
    nodes_path: Path
    area_path: Path
    search_config: Path
    seed: int = Field(ge=0)
    count_by_mode: dict[Literal["car", "bike", "foot"], int]
    band_edges_m: list[float]
    bike_max_m: float = Field(gt=0, allow_inf_nan=False)
    long_car_min_m: float = Field(gt=0, allow_inf_nan=False)
    boundary_margin_m: float = Field(gt=0, allow_inf_nan=False)
    context_radius_m: float = Field(gt=0, allow_inf_nan=False)
    attempts_per_stratum: int = Field(gt=0)

    @model_validator(mode="after")
    def check_sampling(self) -> SampleSettings:
        if set(self.count_by_mode) != {"car", "bike", "foot"} or any(
            value <= 0 for value in self.count_by_mode.values()
        ):
            raise ValueError("positive sample sizes are required for all three modes")
        edges = self.band_edges_m
        if (
            len(edges) < 2
            or edges[0] != 0
            or any(
                not np.isfinite(a) or not np.isfinite(b) or a >= b
                for a, b in zip(edges, edges[1:])
            )
        ):
            raise ValueError("band edges must start at zero and strictly increase")
        if self.bike_max_m not in edges or self.long_car_min_m not in edges:
            raise ValueError("bike and long-car thresholds must be band edges")
        return self


def classify_origins(
    points: np.ndarray,
    edges: np.ndarray,
    edge_keys: np.ndarray,
    urban: np.ndarray,
    tagged: np.ndarray,
    max_distance_m: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Assign nearest car-edge context within metres, or rural beyond it."""
    if (
        len(edges) == 0
        or any(len(value) != len(edges) for value in (edge_keys, urban, tagged))
        or max_distance_m <= 0
    ):
        raise ValueError("invalid car-edge context inputs")
    contexts = np.full(len(points), "rural", dtype="<U5")
    methods = np.full(len(points), "beyond", dtype="<U7")
    matches, distances = STRtree(edges).query_nearest(
        points, max_distance=max_distance_m, all_matches=True, return_distance=True
    )
    if matches.shape[1]:
        point_indices, edge_indices = matches
        order = np.lexsort((edge_keys[edge_indices], distances, point_indices))
        point_indices = point_indices[order]
        edge_indices = edge_indices[order]
        first = np.r_[True, point_indices[1:] != point_indices[:-1]]
        point_indices = point_indices[first]
        edge_indices = edge_indices[first]
        contexts[point_indices] = np.where(urban[edge_indices], "urban", "rural")
        methods[point_indices] = np.where(tagged[edge_indices], "tagged", "density")
    return contexts, methods


def interior_mask(area: object, points: np.ndarray, margin_m: float) -> np.ndarray:
    """Flag points inside the area and at least margin_m from its boundary."""
    interior = shapely.buffer(area, -margin_m)
    if interior.is_empty:
        raise ValueError("pilot area has no interior at the requested margin")
    inside = shapely.covers(interior, points)
    inside[inside] = (
        shapely.distance(points[inside], shapely.boundary(area)) >= margin_m
    )
    return inside


def sample_mode(
    graph: CSRGraph,
    coordinates: np.ndarray,
    contexts: np.ndarray,
    methods: np.ndarray,
    inside: np.ndarray,
    bands_m: list[tuple[float, float]],
    count: int,
    cutoff_s: float,
    resolution_s: float,
    long_car_min_m: float,
    attempts_per_stratum: int,
    rng: np.random.Generator,
) -> tuple[list[dict], list[tuple[float, float, str]]]:
    """Sample distinct directed node pairs by distance band and origin context."""
    n = len(graph.node_ids)
    if (
        coordinates.shape != (n, 2)
        or any(len(value) != n for value in (contexts, methods, inside))
        or count <= 0
        or cutoff_s <= 0
        or resolution_s <= 0
        or attempts_per_stratum <= 0
    ):
        raise ValueError("invalid sample inputs")
    points = shapely.points(coordinates)
    tree = STRtree(points)
    workspace = SearchWorkspace(
        graph, (), max_dial_ticks=int(np.ceil(cutoff_s / resolution_s))
    )
    rows: list[dict] = []
    unavailable: list[tuple[float, float, str]] = []
    used: dict[int, set[int]] = {}
    for context_index, context in enumerate(("urban", "rural")):
        origin_pool = np.flatnonzero(contexts == context)
        if not len(origin_pool):
            raise ValueError(f"{graph.mode}: no {context} origins")
        active = list(bands_m)
        target_count = count // 2 + int(context_index < count % 2)
        generated = 0
        position = 0
        while generated < target_count:
            if not active:
                raise ValueError(f"{graph.mode}: insufficient distinct {context} pairs")
            lower, upper = active[position % len(active)]
            found = False
            pool = origin_pool
            if graph.mode == "car" and lower >= long_car_min_m:
                pool = origin_pool[inside[origin_pool]]
            if len(pool):
                for _ in range(attempts_per_stratum):
                    origin = int(rng.choice(pool))
                    if graph.mode == "foot":
                        result = search(
                            graph,
                            workspace,
                            np.array([origin], dtype=np.int64),
                            np.array([0.0]),
                            cutoff_s,
                            queue="dial",
                            resolution_s=resolution_s,
                        )
                        candidates = result.settled
                    else:
                        candidates = tree.query(
                            points[origin], predicate="dwithin", distance=upper
                        )
                    delta = coordinates[candidates] - coordinates[origin]
                    distance = np.hypot(delta[:, 0], delta[:, 1])
                    valid = (
                        (candidates != origin)
                        & (distance >= lower)
                        & (distance < upper)
                    )
                    if graph.mode == "car" and lower >= long_car_min_m:
                        valid &= inside[candidates]
                    if origin in used:
                        valid &= ~np.isin(candidates, list(used[origin]))
                    candidates, distance = candidates[valid], distance[valid]
                    if len(candidates):
                        choice = int(rng.integers(len(candidates)))
                        destination = int(candidates[choice])
                        used.setdefault(origin, set()).add(destination)
                        rows.append(
                            {
                                "origin_index": origin,
                                "destination_index": destination,
                                "context": context,
                                "context_method": str(methods[origin]),
                                "band_min_m": lower,
                                "band_max_m": upper,
                                "crow_fly_m": float(distance[choice]),
                            }
                        )
                        generated += 1
                        position += 1
                        found = True
                        break
            if not found:
                if graph.mode != "foot":
                    raise ValueError(
                        f"{graph.mode}: could not fill {context} stratum "
                        f"{lower:g}-{upper:g} m after {attempts_per_stratum} attempts"
                    )
                unavailable.append((lower, upper, context))
                active.remove((lower, upper))
    return rows, unavailable


def _signature(settings: SampleSettings, mode: str) -> str:
    paths = [
        settings.graph_directory / f"{mode}.npz",
        settings.edges_path,
        settings.edge_costs_path,
        settings.nodes_path,
        settings.area_path,
        settings.search_config,
    ]
    inputs = []
    for path in paths:
        stat = path.stat()
        inputs.append([str(path.resolve()), stat.st_size, stat.st_mtime_ns])
    signature = {
        "version": 1,
        "settings": settings.model_dump(mode="json"),
        "inputs": inputs,
    }
    return hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()


def _coordinates(
    connection: duckdb.DuckDBPyConnection, path: Path, graph: CSRGraph
) -> np.ndarray:
    connection.register(
        "_sample_nodes",
        pa.table(
            {"node_id": graph.node_ids, "node_index": np.arange(len(graph.node_ids))}
        ),
    )
    try:
        table = connection.execute(
            """
            SELECT s.node_id, n.x, n.y FROM _sample_nodes s
            LEFT JOIN read_parquet(?) n USING (node_id)
            ORDER BY s.node_index
            """,
            [str(path)],
        ).to_arrow_table()
    finally:
        connection.unregister("_sample_nodes")
    if table.num_rows != len(graph.node_ids) or any(
        table.column(name).null_count for name in ("x", "y")
    ):
        raise ValueError(f"{graph.mode} graph nodes do not match nodes.parquet")
    coordinates = np.column_stack(
        [table.column(name).to_numpy(zero_copy_only=False) for name in ("x", "y")]
    )
    if not np.isfinite(coordinates).all():
        raise ValueError(f"{graph.mode} graph coordinates are not finite")
    return coordinates


def _car_context_edges(
    connection: duckdb.DuckDBPyConnection, settings: SampleSettings
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    table = connection.execute(
        """
        SELECT e.edge_key, e.geometry_wkb, e.speed_context, c.is_urban
        FROM read_parquet(?) e LEFT JOIN read_parquet(?) c USING (edge_key)
        WHERE e.mode = 'car' ORDER BY e.edge_key
        """,
        [str(settings.edges_path), str(settings.edge_costs_path)],
    ).to_arrow_table()
    if not table.num_rows or any(
        table.column(name).null_count
        for name in ("edge_key", "geometry_wkb", "is_urban")
    ):
        raise ValueError("car edges must have geometry, unique keys and urban flags")
    keys = np.asarray(table.column("edge_key").to_pylist())
    if len(np.unique(keys)) != len(keys):
        raise ValueError("car edge keys are not unique")
    geometries = shapely.from_wkb(np.asarray(table.column("geometry_wkb").to_pylist()))
    urban = np.asarray(table.column("is_urban").to_pylist(), dtype=bool)
    tagged = np.isin(
        np.asarray(table.column("speed_context").to_pylist()), ["urban", "rural"]
    )
    return geometries, keys, urban, tagged


def _write_checkpoint(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload), encoding="utf-8")
    temporary.replace(path)


def generate_sample(
    settings: SampleSettings, sample_path: Path, log_directory: Path, date: str
) -> None:
    """Write or resume pilot pairs, their WGS84 coordinates and context provenance."""
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    log_directory.mkdir(parents=True, exist_ok=True)
    log_path = log_directory / f"{date}_osrm_sample.log"
    summary_path = log_directory / f"{date}_osrm_sample_summary.md"
    started = time.perf_counter()
    rows: list[dict] = []
    warnings: list[str] = []
    error = ""
    try:
        search_settings = load_search_config(settings.search_config)
        area_table = pq.read_table(settings.area_path, columns=["geometry_wkb"])
        if area_table.num_rows != 1:
            raise ValueError("pilot area cache must contain one geometry")
        area = shapely.from_wkb(area_table.column("geometry_wkb")[0].as_py())
        with duckdb.connect() as connection:
            connection.execute("SET autoinstall_known_extensions = false")
            connection.execute("LOAD spatial")
            edge_data = _car_context_edges(connection, settings)
            for mode_index, mode in enumerate(MODES):
                signature = _signature(settings, mode)
                checkpoint = sample_path.parent / f"sample_{mode}_{signature}.json"
                if checkpoint.exists():
                    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
                    if payload["signature"] != signature:
                        raise ValueError(f"invalid sampling checkpoint: {checkpoint}")
                    mode_rows = payload["rows"]
                    warnings.extend(payload["warnings"])
                    rows.extend(mode_rows)
                    continue
                graph = load_graph(settings.graph_directory / f"{mode}.npz")
                if graph.mode != mode:
                    raise ValueError(f"unexpected mode in {mode} graph")
                coordinates = _coordinates(connection, settings.nodes_path, graph)
                points = shapely.points(coordinates)
                contexts, methods = classify_origins(
                    points, *edge_data, max_distance_m=settings.context_radius_m
                )
                inside = (
                    interior_mask(area, points, settings.boundary_margin_m)
                    if mode == "car"
                    else np.zeros(len(points), dtype=bool)
                )
                band_edges = settings.band_edges_m
                bands = list(zip(band_edges, band_edges[1:]))
                if mode == "bike":
                    bands = [(lo, hi) for lo, hi in bands if hi <= settings.bike_max_m]
                cutoff = search_settings.cutoff_s_by_mode[mode]
                if cutoff is None:
                    raise ValueError(f"{mode} search cutoff is not configured")
                selected, unavailable = sample_mode(
                    graph,
                    coordinates,
                    contexts,
                    methods,
                    inside,
                    bands,
                    settings.count_by_mode[mode],
                    cutoff,
                    search_settings.dial_resolution_s,
                    settings.long_car_min_m,
                    settings.attempts_per_stratum,
                    np.random.default_rng(settings.seed + mode_index),
                )
                mode_warnings = [
                    f"{mode}: no additional {context} pairs in {lower:g}-{upper:g} m "
                    f"after {settings.attempts_per_stratum} attempts"
                    for lower, upper, context in unavailable
                ]
                warnings.extend(mode_warnings)
                mode_rows = []
                for index, selection in enumerate(selected):
                    origin = selection.pop("origin_index")
                    destination = selection.pop("destination_index")
                    mode_rows.append(
                        {
                            "pair_id": f"{mode}-{index:06d}",
                            "mode": mode,
                            "origin_node_id": int(graph.node_ids[origin]),
                            "destination_node_id": int(graph.node_ids[destination]),
                            "origin_x": float(coordinates[origin, 0]),
                            "origin_y": float(coordinates[origin, 1]),
                            "destination_x": float(coordinates[destination, 0]),
                            "destination_y": float(coordinates[destination, 1]),
                            **selection,
                        }
                    )
                _write_checkpoint(
                    checkpoint,
                    {
                        "signature": signature,
                        "rows": mode_rows,
                        "warnings": mode_warnings,
                    },
                )
                rows.extend(mode_rows)
            connection.register("_sample_pairs", pa.Table.from_pylist(rows))
            try:
                table = connection.execute(
                    """
                    SELECT *,
                      ST_X(ST_Transform(ST_Point(origin_x, origin_y),
                           'EPSG:3035', 'EPSG:4326', true)) AS origin_lon,
                      ST_Y(ST_Transform(ST_Point(origin_x, origin_y),
                           'EPSG:3035', 'EPSG:4326', true)) AS origin_lat,
                      ST_X(ST_Transform(ST_Point(destination_x, destination_y),
                           'EPSG:3035', 'EPSG:4326', true)) AS destination_lon,
                      ST_Y(ST_Transform(ST_Point(destination_x, destination_y),
                           'EPSG:3035', 'EPSG:4326', true)) AS destination_lat
                    FROM _sample_pairs
                    """
                ).to_arrow_table()
            finally:
                connection.unregister("_sample_pairs")
        temporary = sample_path.with_suffix(".tmp.parquet")
        pq.write_table(table, temporary)
        temporary.replace(sample_path)
    except (ValueError, OSError, RuntimeError, duckdb.Error) as exc:
        error = str(exc)
        raise
    finally:
        counts = {
            method: sum(row["context_method"] == method for row in rows)
            for method in ("tagged", "density", "beyond")
        }
        duration = time.perf_counter() - started
        origin_methods = {
            (row["mode"], row["origin_node_id"]): row["context_method"] for row in rows
        }
        origin_count = len(origin_methods)
        shares = {
            method: (
                sum(value == method for value in origin_methods.values()) / origin_count
                if origin_count
                else 0
            )
            for method in ("tagged", "density", "beyond")
        }
        lines = [
            "# OSRM sample",
            "",
            f"- Inputs: {settings.model_dump(mode='json')}",
            f"- Pairs: {len(rows)}; context assignment counts: {counts}",
            f"- Distinct origins: {origin_count}; context assignment shares: {shares}",
            f"- Seconds: {duration:.3f}; sample: {sample_path}",
            f"- Error: {error or 'none'}",
            *(f"- Warning: {warning}" for warning in warnings),
        ]
        summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with log_path.open("a", encoding="utf-8") as log:
            log.write("\n".join(lines[2:]) + "\n")
