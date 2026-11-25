"""Cost-weighted CSR graph construction for sections 10.2 and 10.3."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import duckdb
import numpy as np
import numpy.typing as npt
import pyarrow as pa

from mobgrid.osm.config import Mode

FloatArray = npt.NDArray[np.float32]
IndexArray = npt.NDArray[np.int32]
OffsetArray = npt.NDArray[np.int64]
NodeIdArray = npt.NDArray[np.int64]
WeightMap = Mapping[str, FloatArray]
MODES: tuple[Mode, ...] = ("car", "bike", "foot")
GRAPH_BUILD_VERSION = 2


@dataclass(frozen=True)
class CSRGraph:
    """A directed mode graph and its transpose, with OSM node ids and weights."""

    mode: Mode
    node_ids: NodeIdArray
    indptr: OffsetArray
    indices: IndexArray
    weights: WeightMap
    reverse_indptr: OffsetArray
    reverse_indices: IndexArray
    reverse_edge_indices: IndexArray
    road_classes: tuple[str, ...]
    road_class_ids: npt.NDArray[np.uint8]
    speed_buckets: tuple[str, ...]
    speed_bucket_ids: npt.NDArray[np.uint8]
    member_offsets: OffsetArray
    member_edge_rows: OffsetArray
    reference_mass_kg: float
    bike_mass_kg: float


def _sql_path(path: str | Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/").replace("'", "''")


def _sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def validate_edge_cost_join(
    connection: duckdb.DuckDBPyConnection,
    edges_path: str | Path,
    edge_costs_path: str | Path,
) -> None:
    """Require one cost row for every directed edge and no unmatched cost rows."""
    edges_source = _sql_path(edges_path)
    costs_source = _sql_path(edge_costs_path)
    edge_rows, edge_duplicates = connection.execute(f"""
        SELECT count(*), count(*) - count(DISTINCT edge_key)
        FROM read_parquet('{edges_source}')
    """).fetchone()
    cost_rows, cost_duplicates = connection.execute(f"""
        SELECT count(*), count(*) - count(DISTINCT edge_key)
        FROM read_parquet('{costs_source}')
    """).fetchone()
    missing_costs = connection.execute(f"""
        SELECT count(*)
        FROM read_parquet('{edges_source}') e
        LEFT JOIN read_parquet('{costs_source}') c USING (edge_key)
        WHERE c.edge_key IS NULL
    """).fetchone()[0]
    extra_costs = connection.execute(f"""
        SELECT count(*)
        FROM read_parquet('{costs_source}') c
        LEFT JOIN read_parquet('{edges_source}') e USING (edge_key)
        WHERE e.edge_key IS NULL
    """).fetchone()[0]
    if edge_duplicates or cost_duplicates or missing_costs or extra_costs:
        raise ValueError(
            "edge/cost join must be one-to-one: "
            f"{edge_duplicates} duplicate edge rows, "
            f"{cost_duplicates} duplicate cost rows, "
            f"{missing_costs} edges without costs, "
            f"{extra_costs} costs without edges"
        )
    if edge_rows != cost_rows:
        raise ValueError(
            "edge/cost join must be one-to-one: "
            f"{edge_rows} edge rows but {cost_rows} cost rows"
        )


def _array(table: pa.Table, name: str, dtype: npt.DTypeLike) -> np.ndarray:
    column = table.column(name)
    if column.null_count:
        raise ValueError(f"{name} contains {column.null_count} null graph costs")
    values = np.asarray(column.to_numpy(zero_copy_only=False), dtype=dtype)
    if np.issubdtype(values.dtype, np.floating) and not np.isfinite(values).all():
        raise ValueError(f"{name} contains non-finite graph costs")
    return values


def _indptr(source_indices: np.ndarray, node_count: int) -> OffsetArray:
    offsets = np.empty(node_count + 1, dtype=np.int64)
    offsets[0] = 0
    np.cumsum(
        np.bincount(source_indices, minlength=node_count),
        dtype=np.int64,
        out=offsets[1:],
    )
    return offsets


def select_edge_members(
    offsets: OffsetArray, members: OffsetArray, order: np.ndarray
) -> tuple[OffsetArray, OffsetArray]:
    """Reorder or select ordered edge-member sequences."""
    lengths = np.diff(offsets)[order]
    result_offsets = np.empty(len(order) + 1, dtype=np.int64)
    result_offsets[0] = 0
    np.cumsum(lengths, out=result_offsets[1:])
    starts = np.repeat(offsets[order], lengths)
    relative = np.arange(result_offsets[-1]) - np.repeat(result_offsets[:-1], lengths)
    return result_offsets, members[starts + relative]


def csr_from_indexed_edges(
    mode: Mode,
    node_ids: NodeIdArray,
    source_indices: np.ndarray,
    target_indices: np.ndarray,
    weights: Mapping[str, np.ndarray],
    *,
    reference_mass_kg: float,
    bike_mass_kg: float,
    road_classes: tuple[str, ...] = ("",),
    road_class_ids: np.ndarray | None = None,
    speed_buckets: tuple[str, ...] = ("",),
    speed_bucket_ids: np.ndarray | None = None,
    member_offsets: OffsetArray | None = None,
    member_edge_rows: OffsetArray | None = None,
) -> CSRGraph:
    """Create stable CSR arrays from aligned indexed edges and float weights."""
    node_count = len(node_ids)
    edge_count = len(source_indices)
    if node_count > np.iinfo(np.int32).max:
        raise ValueError("the graph has too many nodes for int32 CSR indices")
    if len(target_indices) != edge_count:
        raise ValueError("source and target arrays have different lengths")
    if any(len(values) != edge_count for values in weights.values()):
        raise ValueError("edge weights are not aligned with the edge arrays")
    if not 1 <= len(road_classes) <= 256 or not 1 <= len(speed_buckets) <= 256:
        raise ValueError("category dictionaries must contain 1 to 256 values")
    if road_class_ids is None:
        road_class_ids = np.zeros(edge_count, dtype=np.uint8)
    if speed_bucket_ids is None:
        speed_bucket_ids = np.zeros(edge_count, dtype=np.uint8)
    for ids, categories in (
        (road_class_ids, road_classes),
        (speed_bucket_ids, speed_buckets),
    ):
        if len(ids) != edge_count or np.any(ids < 0) or np.any(ids >= len(categories)):
            raise ValueError("edge category ids are invalid or misaligned")
    if member_offsets is None and member_edge_rows is None:
        member_offsets = np.arange(edge_count + 1, dtype=np.int64)
        member_edge_rows = np.arange(edge_count, dtype=np.int64)
    if (
        member_offsets is None
        or member_edge_rows is None
        or len(member_offsets) != edge_count + 1
        or member_offsets[0] != 0
        or member_offsets[-1] != len(member_edge_rows)
        or np.any(np.diff(member_offsets) <= 0)
        or np.any(member_edge_rows < 0)
    ):
        raise ValueError("edge membership offsets or rows are invalid")
    if (
        np.any(source_indices < 0)
        or np.any(target_indices < 0)
        or np.any(source_indices >= node_count)
        or np.any(target_indices >= node_count)
    ):
        raise ValueError("edge endpoint index is outside the node map")

    order = np.lexsort((np.arange(edge_count), target_indices, source_indices))
    sources = source_indices[order].astype(np.int64, copy=False)
    targets = target_indices[order].astype(np.int64, copy=False)
    if edge_count > np.iinfo(np.int32).max:
        raise ValueError("the graph has too many edges for int32 CSR indices")
    indices = targets.astype(np.int32)
    indptr = _indptr(sources, node_count)
    ordered_weights = {
        name: np.asarray(values[order], dtype=np.float32)
        for name, values in weights.items()
    }

    reverse_order = np.argsort(targets, kind="stable")
    reverse_sources = sources[reverse_order]
    reverse_indptr = _indptr(targets[reverse_order], node_count)
    reverse_indices = reverse_sources.astype(np.int32)
    ordered_member_offsets, ordered_member_rows = select_edge_members(
        member_offsets, member_edge_rows, order
    )
    return CSRGraph(
        mode=mode,
        node_ids=np.asarray(node_ids, dtype=np.int64),
        indptr=indptr,
        indices=indices,
        weights=ordered_weights,
        reverse_indptr=reverse_indptr,
        reverse_indices=reverse_indices,
        reverse_edge_indices=reverse_order.astype(np.int32),
        road_classes=road_classes,
        road_class_ids=np.asarray(road_class_ids[order], dtype=np.uint8),
        speed_buckets=speed_buckets,
        speed_bucket_ids=np.asarray(speed_bucket_ids[order], dtype=np.uint8),
        member_offsets=ordered_member_offsets,
        member_edge_rows=ordered_member_rows,
        reference_mass_kg=reference_mass_kg,
        bike_mass_kg=bike_mass_kg,
    )


def _category_values(
    connection: duckdb.DuckDBPyConnection,
    source: str,
    field: str,
    mode: Mode,
    null_label: str,
) -> tuple[str, ...]:
    rows = connection.execute(f"""
        SELECT DISTINCT coalesce({field}, {_sql_text(null_label)}) AS value
        FROM read_parquet('{source}')
        WHERE mode = {_sql_text(mode)}
        ORDER BY value
    """).fetchall()
    return tuple(str(row[0]) for row in rows)


def build_csr_graph(
    connection: duckdb.DuckDBPyConnection,
    edges_path: str | Path,
    edge_costs_path: str | Path,
    mode: Mode,
    *,
    reference_mass_kg: float,
    bike_mass_kg: float,
    car_energy_kj_per_s: float,
) -> CSRGraph:
    """Build one CSR graph after ``validate_edge_cost_join`` (costs in SI units)."""
    if mode not in MODES:
        raise ValueError(f"unsupported graph mode: {mode}")
    if reference_mass_kg <= 0 or bike_mass_kg <= 0:
        raise ValueError("reference and bike masses must be positive")
    if not np.isfinite(car_energy_kj_per_s) or car_energy_kj_per_s < 0:
        raise ValueError("car energy rate must be finite and non-negative")

    edges_source = _sql_path(edges_path)
    costs_source = _sql_path(edge_costs_path)
    class_values = _category_values(
        connection, edges_source, "highway", mode, "(no highway)"
    )
    bucket_values: tuple[str, ...] = ("(not applicable)",)
    if mode == "car":
        bucket_values = tuple(
            str(row[0])
            for row in connection.execute(f"""
                SELECT DISTINCT coalesce(c.speed_limit_bucket,
                                         '(not applicable)') AS value
                FROM read_parquet('{edges_source}') e
                JOIN read_parquet('{costs_source}') c USING (edge_key)
                WHERE e.mode = {_sql_text(mode)}
                ORDER BY value
            """).fetchall()
        )

    if not class_values:
        class_values = ("(no highway)",)
    if not bucket_values:
        bucket_values = ("(not applicable)",)
    if len(class_values) > 256 or len(bucket_values) > 256:
        raise ValueError("graph has more than 256 road classes or speed buckets")
    mode_time = {
        "car": "c.car_time_s",
        "bike": "c.bike_time_s",
        "foot": "c.walk_time_s",
    }[mode]
    mode_energy = {
        "bike": "c.bike_energy_kj",
        "foot": "c.walk_energy_kj",
    }.get(mode)
    energy_sql = (
        f"{mode_energy} AS energy_kj"
        if mode_energy is not None
        else f"c.car_time_s * {car_energy_kj_per_s!r} AS energy_kj"
    )
    climb_sql = "e.climb_m" if mode == "car" else "c.climb_m"
    bike_parts_sql = ""
    if mode == "bike":
        bike_parts_sql = """,
            CASE WHEN lower(coalesce(e.highway, '')) = 'steps'
                 THEN coalesce(c.bike_energy_per_kg_kj_per_kg, 0)
                 ELSE c.bike_energy_per_kg_kj_per_kg END
                AS bike_energy_per_kg_kj_per_kg,
            CASE WHEN lower(coalesce(e.highway, '')) = 'steps'
                 THEN coalesce(c.bike_energy_drag_kj, 0)
                 ELSE c.bike_energy_drag_kj END AS bike_energy_drag_kj,
            CASE WHEN lower(coalesce(e.highway, '')) = 'steps'
                 THEN coalesce(c.bike_pedalling_energy_kj, 0)
                 ELSE c.bike_pedalling_energy_kj END AS bike_pedalling_energy_kj,
            CASE WHEN lower(coalesce(e.highway, '')) = 'steps'
                 THEN c.bike_energy_kj ELSE 0 END AS bike_energy_step_kj"""
    separated_sql = (
        "c.separated_length_m" if mode == "bike" else "0::FLOAT AS separated_length_m"
    )
    bucket_sql = (
        "coalesce(c.speed_limit_bucket, '(not applicable)')"
        if mode == "car"
        else "'(not applicable)'"
    )
    table = connection.execute(f"""
        WITH edges AS (
            SELECT *, row_number() OVER () - 1 AS edge_row
            FROM read_parquet('{edges_source}')
        )
        SELECT e.from_node_id, e.to_node_id, e.edge_row,
               coalesce(e.highway, '(no highway)') AS road_class,
               {bucket_sql} AS speed_bucket,
               {mode_time} AS time_s,
               c.length_m AS distance_m,
               {energy_sql},
               {climb_sql} AS climb_m,
               {separated_sql}
               {bike_parts_sql}
        FROM edges e
        JOIN read_parquet('{costs_source}') c USING (edge_key)
        WHERE e.mode = {_sql_text(mode)}
        ORDER BY e.from_node_id, e.to_node_id, e.edge_key
    """).to_arrow_table()
    from_node_ids = _array(table, "from_node_id", np.int64)
    to_node_ids = _array(table, "to_node_id", np.int64)
    node_ids = np.unique(np.concatenate((from_node_ids, to_node_ids)))
    if len(node_ids) > np.iinfo(np.int32).max:
        raise ValueError("the graph has too many nodes for int32 CSR indices")
    source_indices = np.searchsorted(node_ids, from_node_ids)
    target_indices = np.searchsorted(node_ids, to_node_ids)
    weights: dict[str, np.ndarray] = {
        "time_s": _array(table, "time_s", np.float32),
        "distance_m": _array(table, "distance_m", np.float32),
        "energy_kj": _array(table, "energy_kj", np.float32),
        "climb_m": _array(table, "climb_m", np.float32),
        "separated_length_m": _array(table, "separated_length_m", np.float32),
    }
    if mode == "bike":
        for name in (
            "bike_energy_per_kg_kj_per_kg",
            "bike_energy_drag_kj",
            "bike_pedalling_energy_kj",
            "bike_energy_step_kj",
        ):
            weights[name] = _array(table, name, np.float32)
    class_ids = np.searchsorted(
        class_values, table.column("road_class").to_numpy(zero_copy_only=False)
    )
    bucket_ids = np.searchsorted(
        bucket_values, table.column("speed_bucket").to_numpy(zero_copy_only=False)
    )
    return csr_from_indexed_edges(
        mode,
        node_ids,
        source_indices,
        target_indices,
        weights,
        reference_mass_kg=reference_mass_kg,
        bike_mass_kg=bike_mass_kg,
        road_classes=class_values,
        road_class_ids=class_ids,
        speed_buckets=bucket_values,
        speed_bucket_ids=bucket_ids,
        member_offsets=np.arange(len(from_node_ids) + 1, dtype=np.int64),
        member_edge_rows=_array(table, "edge_row", np.int64),
    )


def bike_energy_for_mass(graph: CSRGraph, body_mass_kg: float) -> FloatArray:
    """Return bike edge energy at a body mass without rebuilding the graph."""
    if graph.mode != "bike":
        raise ValueError("bike energy is only defined for bike graphs")
    if not np.isfinite(body_mass_kg) or body_mass_kg <= 0:
        raise ValueError("body mass must be finite and positive")
    scale = body_mass_kg / graph.reference_mass_kg
    energy = (
        graph.weights["bike_energy_per_kg_kj_per_kg"]
        * (graph.bike_mass_kg + body_mass_kg)
        + graph.weights["bike_energy_drag_kj"]
        + graph.weights["bike_pedalling_energy_kj"] * scale
        + graph.weights["bike_energy_step_kj"] * scale
    )
    return np.asarray(energy, dtype=np.float32)


def graph_memory_bytes(graph: CSRGraph) -> int:
    """Count all forward and transposed CSR array storage in bytes."""
    arrays = (
        graph.node_ids,
        graph.indptr,
        graph.indices,
        graph.reverse_indptr,
        graph.reverse_indices,
        *graph.weights.values(),
        graph.reverse_edge_indices,
        graph.road_class_ids,
        graph.speed_bucket_ids,
        graph.member_offsets,
        graph.member_edge_rows,
    )
    return sum(array.nbytes for array in arrays)


def legacy_graph_memory_bytes(graph: CSRGraph) -> int:
    """Estimate version-1 CSR array bytes for the same nodes and arcs."""
    weight_count = len(graph.weights)
    if graph.mode == "car":
        weight_count += len(graph.road_classes) + len(graph.speed_buckets)
    return (
        graph.node_ids.nbytes
        + graph.indptr.nbytes
        + graph.indices.nbytes
        + graph.reverse_indptr.nbytes
        + graph.reverse_indices.nbytes
        + 2 * len(graph.indices) * weight_count * np.dtype(np.float32).itemsize
    )


def save_graph(graph: CSRGraph, path: str | Path) -> None:
    """Atomically save a self-describing graph archive."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    names = tuple(sorted(graph.weights))
    arrays: dict[str, np.ndarray] = {
        "mode": np.asarray(graph.mode),
        "build_version": np.asarray(GRAPH_BUILD_VERSION),
        "node_ids": graph.node_ids,
        "indptr": graph.indptr,
        "indices": graph.indices,
        "reverse_indptr": graph.reverse_indptr,
        "reverse_indices": graph.reverse_indices,
        "reverse_edge_indices": graph.reverse_edge_indices,
        "road_classes": np.asarray(graph.road_classes, dtype=np.str_),
        "road_class_ids": graph.road_class_ids,
        "speed_buckets": np.asarray(graph.speed_buckets, dtype=np.str_),
        "speed_bucket_ids": graph.speed_bucket_ids,
        "member_offsets": graph.member_offsets,
        "member_edge_rows": graph.member_edge_rows,
        "weight_names": np.asarray(names, dtype=np.str_),
        "reference_mass_kg": np.asarray(graph.reference_mass_kg),
        "bike_mass_kg": np.asarray(graph.bike_mass_kg),
    }
    for index, name in enumerate(names):
        arrays[f"weight_{index}"] = graph.weights[name]
    temporary = destination.with_name(destination.name + ".tmp")
    try:
        with temporary.open("wb") as stream:
            np.savez(stream, **arrays)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def load_graph(path: str | Path) -> CSRGraph:
    """Load a graph archive written by :func:`save_graph`."""
    with np.load(path, allow_pickle=False) as archive:
        if (
            "build_version" not in archive
            or int(archive["build_version"]) != GRAPH_BUILD_VERSION
        ):
            raise ValueError("graph build version is obsolete; rebuild the graph")
        names = tuple(str(value) for value in archive["weight_names"])
        mode_value = str(archive["mode"].item())
        if mode_value not in MODES:
            raise ValueError(f"unsupported mode in graph archive: {mode_value}")
        mode = next(value for value in MODES if value == mode_value)
        weights = {
            name: archive[f"weight_{index}"].copy() for index, name in enumerate(names)
        }
        return CSRGraph(
            mode=mode,
            node_ids=archive["node_ids"].copy(),
            indptr=archive["indptr"].copy(),
            indices=archive["indices"].copy(),
            weights=weights,
            reverse_indptr=archive["reverse_indptr"].copy(),
            reverse_indices=archive["reverse_indices"].copy(),
            reverse_edge_indices=archive["reverse_edge_indices"].copy(),
            road_classes=tuple(str(value) for value in archive["road_classes"]),
            road_class_ids=archive["road_class_ids"].copy(),
            speed_buckets=tuple(str(value) for value in archive["speed_buckets"]),
            speed_bucket_ids=archive["speed_bucket_ids"].copy(),
            member_offsets=archive["member_offsets"].copy(),
            member_edge_rows=archive["member_edge_rows"].copy(),
            reference_mass_kg=float(archive["reference_mass_kg"]),
            bike_mass_kg=float(archive["bike_mass_kg"]),
        )
