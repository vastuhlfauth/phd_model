"""Directional walking and cycling edge costs for sections 9.3 and 9.7."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import numpy.typing as npt
import pyarrow as pa
import pyarrow.compute as pc
from common.duckdb_io import write_parquet

from mobgrid.energy.rates import (
    GRAVITY_M_S2,
    MET_MINUTE_KJ_PER_KG,
    EnergyConfig,
)
from mobgrid.osm.bike_speed_table import BikeSpeedTable
from mobgrid.osm.config import NetworkConfig

FloatArray = npt.NDArray[np.float64]
_EDGE_BATCH_SIZE = 25_000
_CONTROLLED_HIGHWAYS = {"traffic_signals", "stop", "give_way", "mini_roundabout"}


@dataclass(frozen=True)
class ActiveCostSummary:
    """Counts for one active-mode edge-cost enrichment."""

    edge_count: int
    incomplete_profile_count: int
    unknown_surface_count: int
    unknown_surface_values: dict[str, int]
    clipped_segments_by_class: dict[tuple[str, str], tuple[int, float]]
    longest_clipped_edges: tuple[tuple[str, int, str, str, float, float], ...]


def _summarize_clipped_grades(
    connection: duckdb.DuckDBPyConnection, table: str, limit: int
) -> tuple[
    dict[tuple[str, str], tuple[int, float]],
    tuple[tuple[str, int, str, str, float, float], ...],
]:
    name = '"' + table.replace('"', '""') + '"'
    by_class = {
        (mode, highway): (int(count), float(length))
        for mode, highway, count, length in connection.execute(f"""
            SELECT mode, highway, count(*), sum(segment_length_m)
            FROM {name} GROUP BY mode, highway ORDER BY mode, highway
        """).fetchall()
    }
    longest = tuple(connection.execute(f"""
        SELECT edge_key, way_id, mode, highway, max(edge_length_m),
               arg_max(grade, abs(grade))
        FROM {name}
        GROUP BY edge_key, way_id, mode, highway
        ORDER BY max(edge_length_m) DESC, edge_key LIMIT ?
    """, [limit]).fetchall())
    return by_class, longest


def _grade_report_lines(
    by_class: dict[tuple[str, str], tuple[int, float]],
    longest: tuple[tuple[str, int, str, str, float, float], ...],
) -> list[str]:
    lines = [
        "Lengths are metres; grades are the original signed segment grades.",
        "Classes are OSM highway classes, separated by directed travel mode.",
        "",
        "| Mode | Highway class | Segments | Length (m) |",
        "|---|---|---:|---:|",
    ]
    for (mode, highway), (count, length) in by_class.items():
        lines.append(f"| {mode} | {highway} | {count} | {length:.1f} |")
    lines.extend([
        "",
        "| Edge key | Way id | Mode | Highway class | Edge length (m) | Grade |",
        "|---|---:|---|---|---:|---:|",
    ])
    for edge_key, way_id, mode, highway, length, grade in longest:
        lines.append(
            f"| {edge_key} | {way_id} | {mode} | {highway} | "
            f"{length:.1f} | {grade:.3f} |"
        )
    return lines


def _sql_path(path: str | Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/").replace("'", "''")


def _float_column(table: pa.Table, name: str) -> FloatArray:
    return np.asarray(
        table.column(name).to_numpy(zero_copy_only=False), dtype=np.float64
    )


def _text_column(table: pa.Table, name: str) -> npt.NDArray[np.str_]:
    values = pc.fill_null(table.column(name), "").to_numpy(zero_copy_only=False)
    return np.char.lower(np.char.strip(np.asarray(values, dtype=str)))


def _sum_by_edge(values: FloatArray, groups: npt.NDArray[np.int64]) -> FloatArray:
    return np.bincount(groups, weights=values, minlength=int(groups.max()) + 1)


def _active_edge_batch(
    connection: duckdb.DuckDBPyConnection,
    nodes_path: str,
    edge_batch: pa.RecordBatch,
) -> pa.Table:
    connection.register("_active_edge_batch", edge_batch)
    try:
        return connection.execute(f"""
            WITH ordered_nodes AS (
                SELECT e.edge_key, e.mode, e.highway, e.bike_infra, e.surface,
                       e.tracktype, e.length_m, e.signal_count, e.stop_count,
                       e.give_way_count, e.crossing_count, e.to_degree,
                       e.to_highway, e.to_crossing, e.node_ids,
                       edge_node.node_sequence, n.x, n.y,
                       list_extract(e.node_elevations_m, edge_node.node_sequence)
                           AS elevation_m,
                       lag(n.x) OVER edge_order AS previous_x,
                       lag(n.y) OVER edge_order AS previous_y,
                       lag(list_extract(
                           e.node_elevations_m, edge_node.node_sequence
                       )) OVER edge_order AS previous_elevation_m
                FROM _active_edge_batch e
                CROSS JOIN UNNEST(e.node_ids) WITH ORDINALITY
                    AS edge_node(node_id, node_sequence)
                LEFT JOIN read_parquet('{nodes_path}') n USING (node_id)
                WINDOW edge_order AS (
                    PARTITION BY e.edge_key ORDER BY edge_node.node_sequence
                )
            )
            SELECT * FROM ordered_nodes
            WHERE node_sequence > 1
            ORDER BY edge_key, node_sequence
        """).to_arrow_table()
    finally:
        connection.unregister("_active_edge_batch")


def _calculate_batch(
    edge_batch: pa.RecordBatch,
    segments: pa.Table,
    energy: EnergyConfig,
    network: NetworkConfig,
    speed_tables: dict[tuple[str, float], BikeSpeedTable],
) -> tuple[pa.Table, int, Counter[str], int, pa.Table]:
    batch_keys = np.asarray(
        edge_batch.column("edge_key").to_numpy(zero_copy_only=False), dtype=str
    )
    segment_keys = np.asarray(segments.column("edge_key").to_pylist(), dtype=object)
    if not len(segment_keys):
        raise ValueError("active edge batch has no ordered node segments")
    unique_keys, groups = np.unique(segment_keys, return_inverse=True)
    groups = groups.astype(np.int64, copy=False)
    group_count = len(unique_keys)
    if group_count != edge_batch.num_rows:
        raise ValueError("an active edge has no ordered node segments")
    metadata_indices = np.searchsorted(batch_keys, unique_keys)
    if not np.array_equal(batch_keys[metadata_indices], unique_keys):
        raise ValueError("edge and segment rows do not align by edge_key")
    edge_modes = _text_column(edge_batch, "mode")[metadata_indices]
    highways = _text_column(edge_batch, "highway")[metadata_indices]
    bike_classes = _text_column(edge_batch, "bike_infra")[metadata_indices]
    edge_lengths = _float_column(edge_batch, "length_m")[metadata_indices]
    signal_counts = _float_column(edge_batch, "signal_count")[metadata_indices]
    stop_counts = _float_column(edge_batch, "stop_count")[metadata_indices]
    give_way_counts = _float_column(edge_batch, "give_way_count")[metadata_indices]
    crossing_counts = _float_column(edge_batch, "crossing_count")[metadata_indices]
    to_degrees = _float_column(edge_batch, "to_degree")[metadata_indices]
    to_highways = _text_column(edge_batch, "to_highway")[metadata_indices]
    to_crossings = _text_column(edge_batch, "to_crossing")[metadata_indices]
    foot_edges = edge_modes == "foot"
    bike_edges = edge_modes == "bike"

    x = _float_column(segments, "x")
    y = _float_column(segments, "y")
    elevation = _float_column(segments, "elevation_m")
    previous_x = _float_column(segments, "previous_x")
    previous_y = _float_column(segments, "previous_y")
    previous_elevation = _float_column(segments, "previous_elevation_m")
    horizontal = np.hypot(x - previous_x, y - previous_y)
    height_change = elevation - previous_elevation
    projected_edge_lengths = _sum_by_edge(horizontal, groups)
    scale = np.divide(
        edge_lengths,
        projected_edge_lengths,
        out=np.zeros(group_count, dtype=np.float64),
        where=projected_edge_lengths > 0,
    )
    segment_lengths = horizontal * scale[groups]
    grades = np.divide(
        height_change,
        horizontal,
        out=np.zeros_like(height_change),
        where=horizontal > 0,
    )
    complete_segment = (
        np.isfinite(x) & np.isfinite(y) & np.isfinite(elevation)
        & np.isfinite(previous_x) & np.isfinite(previous_y)
        & np.isfinite(previous_elevation)
    )
    complete_edges = np.bincount(
        groups, weights=(~complete_segment).astype(np.int64), minlength=group_count
    ) == 0
    complete_edges &= projected_edge_lengths > 0

    mass = energy.reference_mass_kg
    c0 = energy.walking.c0_j_per_kg_m[energy.rate_set]
    walking_lowwater, walking_highwater = energy.walking.gradient_valid_range
    non_stair_walk = foot_edges & (highways != "steps")
    walking_grades = np.clip(grades, walking_lowwater, walking_highwater)
    bike_grades = np.clip(
        grades, network.bike_speed_table.grade_min, network.bike_speed_table.grade_max
    )
    clipped = complete_edges[groups] & (
        (non_stair_walk[groups] & (grades != walking_grades))
        | (bike_edges[groups] & (grades != bike_grades))
    )
    clipped_groups = groups[clipped]
    way_ids = np.asarray(
        edge_batch.column("way_id").to_numpy(zero_copy_only=False), dtype=np.int64
    )[metadata_indices]
    diagnostics = pa.table({
        "edge_key": pa.array(unique_keys[clipped_groups], type=pa.string()),
        "way_id": pa.array(way_ids[clipped_groups], type=pa.int64()),
        "mode": pa.array(edge_modes[clipped_groups], type=pa.string()),
        "highway": pa.array(highways[clipped_groups], type=pa.string()),
        "edge_length_m": pa.array(edge_lengths[clipped_groups], type=pa.float64()),
        "segment_length_m": pa.array(segment_lengths[clipped], type=pa.float64()),
        "grade": pa.array(grades[clipped], type=pa.float64()),
    })

    walking_v0 = energy.walking.v0_kmh / 3.6
    walking_speed = walking_v0 * np.exp(
        -3.5 * np.abs(walking_grades + 0.05)
    ) / math.exp(-0.175)
    coefficients = np.asarray(
        energy.walking.gradient_polynomial_j_per_kg_m, dtype=np.float64
    )
    gradient_cost = np.polyval(coefficients, walking_grades) / np.polyval(
        coefficients, 0.0
    )
    walk_time_segment = np.divide(
        segment_lengths, walking_speed, out=np.zeros_like(segment_lengths),
        where=walking_speed > 0,
    )
    walk_energy_segment = mass * c0 * segment_lengths * gradient_cost / 1000.0
    stair = foot_edges[groups] & (highways[groups] == "steps")
    stair_height = np.abs(height_change)
    stair_time_segment = np.where(
        height_change >= 0,
        stair_height / energy.stairs.up_speed_m_per_s,
        stair_height / energy.stairs.down_speed_m_per_s,
    )
    stair_energy_segment = np.where(
        height_change >= 0,
        mass * GRAVITY_M_S2 * stair_height / energy.stairs.up_efficiency / 1000.0,
        mass * GRAVITY_M_S2 * stair_height
        / energy.stairs.up_efficiency
        * energy.stairs.down_to_up_energy_ratio
        / 1000.0,
    )
    walk_time_segment = np.where(stair, stair_time_segment, walk_time_segment)
    walk_energy_segment = np.where(stair, stair_energy_segment, walk_energy_segment)
    walk_time = _sum_by_edge(walk_time_segment, groups)
    walk_energy = _sum_by_edge(walk_energy_segment, groups)

    bike_segment = bike_edges[groups] & complete_edges[groups]
    raw_surfaces = _text_column(edge_batch, "surface")[metadata_indices]
    raw_tracktypes = _text_column(edge_batch, "tracktype")[metadata_indices]
    raw_surfaces = raw_surfaces.astype(str)
    raw_tracktypes = raw_tracktypes.astype(str)
    resolved_surfaces = np.full(group_count, "", dtype=object)
    unknown_surfaces: Counter[str] = Counter()
    for surface_alias, resolved in network.bike_edge_costs.surface_aliases.items():
        resolved_surfaces[bike_edges & (raw_surfaces == surface_alias)] = resolved
    no_surface = bike_edges & (raw_surfaces == "")
    for tracktype, resolved in network.bike_edge_costs.surface_by_tracktype.items():
        resolved_surfaces[
            no_surface & (raw_tracktypes == tracktype)
        ] = resolved
    unknown_surface = bike_edges & (raw_surfaces != "") & (resolved_surfaces == "")
    if unknown_surface.any():
        unknown_values, unknown_counts = np.unique(
            raw_surfaces[unknown_surface], return_counts=True
        )
        unknown_surfaces.update(
            dict(zip(unknown_values.tolist(), unknown_counts.tolist(), strict=True))
        )
    needs_default = bike_edges & (resolved_surfaces == "")
    for highway, resolved in (
        network.bike_edge_costs.surface_default_by_highway.items()
    ):
        resolved_surfaces[needs_default & (highways == highway)] = resolved
    unresolved_surface = bike_edges & (resolved_surfaces == "")
    if unresolved_surface.any():
        index = int(np.flatnonzero(unresolved_surface)[0])
        raise ValueError(
            f"no configured bike surface default for highway={highways[index]!r}"
        )
    unknown_key = bike_edges & ~np.isin(
        resolved_surfaces, tuple(energy.bike.surface_crr)
    )
    if unknown_key.any():
        index = int(np.flatnonzero(unknown_key)[0])
        raise ValueError(
            f"bike surface mapping resolves to unknown Crr: "
            f"{resolved_surfaces[index]!r}"
        )

    class_caps = network.bike_speed_table.class_cap_kmh
    cap_by_edge = np.full(group_count, np.inf, dtype=np.float64)
    for bike_class, cap in class_caps.items():
        cap_by_edge[bike_classes == bike_class] = cap
    invalid_class = bike_edges & ~np.isfinite(cap_by_edge)
    if invalid_class.any():
        index = int(np.flatnonzero(invalid_class)[0])
        raise ValueError(
            f"bike edge {unique_keys[index]} has unconfigured infrastructure "
            f"class {bike_classes[index]!r}"
        )
    for highway, cap in network.bike_speed_table.highway_cap_kmh.items():
        cap_by_edge[(bike_edges) & (highways == highway)] = np.minimum(
            cap_by_edge[bike_edges & (highways == highway)], cap
        )

    speeds = np.zeros(len(segment_keys), dtype=np.float64)
    bike_work_per_kg_segment = np.zeros(len(segment_keys), dtype=np.float64)
    bike_drag_segment = np.zeros(len(segment_keys), dtype=np.float64)
    bike_pedalled_time_segment = np.zeros(len(segment_keys), dtype=np.float64)
    bike = energy.bike
    for surface in np.unique(resolved_surfaces[bike_edges]):
        surface_edges = bike_edges & (resolved_surfaces == surface)
        for cap in np.unique(cap_by_edge[surface_edges]):
            selected = (
                bike_segment
                & (resolved_surfaces[groups] == surface)
                & (cap_by_edge[groups] == cap)
            )
            table = speed_tables.get((surface, cap))
            if table is None:
                table = BikeSpeedTable(
                    energy,
                    network.bike_speed_table,
                    energy.bike.surface_crr[surface],
                    cap,
                )
                speed_tables[(surface, cap)] = table
            group_speeds, group_powers = table.lookup(bike_grades[selected])
            speeds[selected] = group_speeds
            crr = energy.bike.surface_crr[surface]
            angle_cosine = 1.0 / np.sqrt(1.0 + bike_grades[selected] ** 2)
            rolling = GRAVITY_M_S2 * crr * angle_cosine * segment_lengths[selected]
            climbing = (
                GRAVITY_M_S2
                * bike_grades[selected]
                / np.sqrt(1.0 + bike_grades[selected] ** 2)
                * segment_lengths[selected]
            )
            pedalled = group_powers > 0
            separated = bike_classes[groups[selected]] == "separated_track_path"
            calmer_factor = np.where(
                separated, bike.separated_infra_factor, 1.0
            )
            bike_work_per_kg_segment[selected] = np.where(
                pedalled,
                (rolling + climbing)
                / bike.gross_muscular_efficiency
                * calmer_factor
                / 1000.0,
                0.0,
            )
            drag = (
                0.5 * bike.rho_air_kg_per_m3 * bike.cda_m2
                * group_speeds**2 * segment_lengths[selected]
            )
            bike_drag_segment[selected] = np.where(
                pedalled,
                drag / bike.gross_muscular_efficiency
                * calmer_factor / 1000.0,
                0.0,
            )
            bike_pedalled_time_segment[selected] = np.where(
                pedalled,
                segment_lengths[selected] / group_speeds,
                0.0,
            )

    bike_time_ride = _sum_by_edge(
        np.divide(
            segment_lengths, speeds, out=np.zeros_like(segment_lengths),
            where=bike_segment & (speeds > 0),
        ),
        groups,
    )
    bike_work_per_kg = _sum_by_edge(bike_work_per_kg_segment, groups)
    bike_drag = _sum_by_edge(bike_drag_segment, groups)
    bike_pedalled_time = _sum_by_edge(bike_pedalled_time_segment, groups)
    bike_pedalling_energy = (
        mass * bike.pedalling_unloaded_net_met
        * MET_MINUTE_KJ_PER_KG * bike_pedalled_time / 60.0
    )
    total_mass = mass + bike.bike_mass_kg
    edge_average_speed = np.divide(
        edge_lengths,
        bike_time_ride,
        out=np.zeros(group_count, dtype=np.float64),
        where=bike_time_ride > 0,
    )
    stops = bike.stops
    signal_probability = stops.red_time_s / stops.signal_cycle_s
    if signal_probability > 1:
        raise ValueError("configured bike red time exceeds the signal cycle")
    expected_signal_wait = stops.red_time_s**2 / (2.0 * stops.signal_cycle_s)
    controlled = np.isin(to_highways, tuple(_CONTROLLED_HIGHWAYS))
    controlled |= to_crossings == "traffic_signals"
    junction_count = (to_degrees >= 3) & ~controlled & bike_edges
    junction_probability = np.zeros(group_count, dtype=np.float64)
    crossing_probability = np.zeros(group_count, dtype=np.float64)
    for bike_class, probability in (
        network.bike_edge_costs.uncontrolled_junction_probability_by_class.items()
    ):
        class_mask = bike_classes == bike_class
        junction_probability[class_mask] = probability
    for bike_class, probability in (
        network.bike_edge_costs.crossing_probability_by_class.items()
    ):
        crossing_probability[bike_classes == bike_class] = probability
    expected_stops = (
        signal_counts * signal_probability
        + stop_counts * network.bike_edge_costs.stop_sign_probability
        + give_way_counts * network.bike_edge_costs.give_way_probability
        + junction_count * junction_probability
        + crossing_counts * crossing_probability
    )
    bike_stop_time = (
        edge_average_speed / (2 * stops.deceleration_m_per_s2)
        + edge_average_speed / (2 * stops.acceleration_m_per_s2)
    ) * expected_stops + signal_counts * expected_signal_wait
    separated_edges = bike_edges & (bike_classes == "separated_track_path")
    bike_stop_work_per_kg = (
        expected_stops * 0.5 * edge_average_speed**2
        / bike.gross_muscular_efficiency / 1000.0
        * np.where(separated_edges, bike.separated_infra_factor, 1.0)
    )

    bike_work_per_kg += bike_stop_work_per_kg
    bike_energy = bike_work_per_kg * total_mass + bike_drag + bike_pedalling_energy
    bike_time = bike_time_ride + bike_stop_time

    climb_segment = np.maximum(height_change, 0.0)
    climb = _sum_by_edge(climb_segment, groups)
    incomplete_count = int(np.count_nonzero(~complete_edges))
    valid_walk = foot_edges & complete_edges
    valid_bike = bike_edges & complete_edges

    def nullable(values: FloatArray, mask: npt.NDArray[np.bool_]) -> pa.Array:
        return pa.array(values, mask=~mask, type=pa.float64())

    result = pa.table(
        {
            "edge_key": pa.array(unique_keys, type=pa.string()),
            "walk_time_s": nullable(walk_time, valid_walk),
            "walk_energy_kj": nullable(walk_energy, valid_walk),
            "bike_time_s": nullable(bike_time, valid_bike),
            "bike_energy_kj": nullable(bike_energy, valid_bike),
            "bike_energy_per_kg_kj_per_kg": nullable(
                bike_work_per_kg, valid_bike
            ),
            "bike_energy_drag_kj": nullable(bike_drag, valid_bike),
            "bike_pedalling_energy_kj": nullable(
                bike_pedalling_energy, valid_bike
            ),
            "climb_m": nullable(climb, complete_edges),
            "separated_length_m": pa.array(
                np.where(separated_edges, edge_lengths, 0.0),
                type=pa.float64(),
            ),
        }
    )
    return result, incomplete_count, unknown_surfaces, group_count, diagnostics


def enrich_active_edge_costs(
    connection: duckdb.DuckDBPyConnection,
    edges_path: str | Path,
    nodes_path: str | Path,
    output_path: str | Path,
    *,
    energy: EnergyConfig,
    network: NetworkConfig,
) -> ActiveCostSummary:
    """Write section 9.3/9.7 costs for directed foot and bike edges.

    Way-specific edge elevations are metres, coordinates and lengths are metres, grades
    are dimensionless, times are seconds, and energies are kJ. Inputs are
    existing OSM edge and node Parquet tables; this function is intended to
    be called by the later B2 stage, not as a standalone command.
    """
    edges = Path(edges_path)
    nodes = Path(nodes_path)
    output = Path(output_path)
    for path in (edges, nodes):
        if not path.is_file():
            raise FileNotFoundError(path)
    if output.resolve() in (edges.resolve(), nodes.resolve()):
        raise ValueError("active costs must be written separately from input tables")
    if energy.bike.power.p0_w is None or energy.bike.power.k is None \
            or energy.bike.power.p_max_w is None \
            or energy.bike.power.v_max_descent_kmh is None:
        raise ValueError("bike power parameters must be configured")

    edge_source = _sql_path(edges)
    node_source = _sql_path(nodes)
    node_columns = {
        row[0] for row in connection.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{node_source}')"
        ).fetchall()
    }
    missing_node_columns = {"node_id", "x", "y", "tags"} - node_columns
    if missing_node_columns:
        raise ValueError(
            f"node table is missing required columns: "
            f"{sorted(missing_node_columns)}"
        )
    required_edges = {
        "edge_key", "way_id", "mode", "node_ids", "node_elevations_m",
        "length_m", "highway", "bike_infra",
        "surface", "tracktype", "signal_count", "stop_count", "give_way_count",
        "crossing_count", "to_degree", "to_node_id",
    }
    edge_columns = {
        row[0] for row in connection.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{edge_source}')"
        ).fetchall()
    }
    missing_columns = required_edges - edge_columns
    if missing_columns:
        raise ValueError(
            f"edge table is missing required columns: {sorted(missing_columns)}"
        )
    invalid_profiles = connection.execute(f"""
        SELECT count(*) FROM read_parquet('{edge_source}')
        WHERE mode IN ('foot', 'bike')
          AND (node_elevations_m IS NULL
               OR len(node_elevations_m) <> len(node_ids))
    """).fetchone()[0]
    if invalid_profiles:
        raise ValueError(f"{invalid_profiles} edges have misaligned elevation profiles")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.stem + ".tmp.parquet")
    if temporary.exists():
        temporary.unlink()
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _active_cost_result (
            edge_key VARCHAR,
            walk_time_s DOUBLE,
            walk_energy_kj DOUBLE,
            bike_time_s DOUBLE,
            bike_energy_kj DOUBLE,
            bike_energy_per_kg_kj_per_kg DOUBLE,
            bike_energy_drag_kj DOUBLE,
            bike_pedalling_energy_kj DOUBLE,
            climb_m DOUBLE,
            separated_length_m DOUBLE
        )
    """)
    connection.execute("""
        CREATE OR REPLACE TEMP TABLE _active_clipped_grades (
            edge_key VARCHAR, way_id BIGINT, mode VARCHAR, highway VARCHAR,
            edge_length_m DOUBLE, segment_length_m DOUBLE, grade DOUBLE
        )
    """)
    speed_tables: dict[tuple[str, float], BikeSpeedTable] = {}
    unknown_surfaces: Counter[str] = Counter()
    edge_count = 0
    incomplete_count = 0
    reader_connection = connection.cursor()
    try:
        edge_reader = reader_connection.execute(f"""
            SELECT e.edge_key, e.way_id, e.mode, e.node_ids, e.node_elevations_m,
                   e.length_m, e.highway,
                   e.bike_infra, e.surface, e.tracktype, e.signal_count,
                   e.stop_count, e.give_way_count, e.crossing_count,
                   e.to_degree, e.to_node_id,
                   to_node.tags['highway'] AS to_highway,
                   to_node.tags['crossing'] AS to_crossing
            FROM read_parquet('{edge_source}') e
            LEFT JOIN read_parquet('{node_source}') to_node
                ON e.to_node_id = to_node.node_id
            WHERE e.mode IN ('foot', 'bike')
            ORDER BY e.edge_key
        """).to_arrow_reader(batch_size=_EDGE_BATCH_SIZE)
        for edge_batch in edge_reader:
            segments = _active_edge_batch(
                connection, node_source, edge_batch
            )
            result, missing, batch_unknown, count, diagnostics = _calculate_batch(
                edge_batch, segments, energy, network, speed_tables
            )
            connection.register("_active_cost_batch", result)
            try:
                connection.execute(
                    "INSERT INTO _active_cost_result "
                    "SELECT * FROM _active_cost_batch"
                )
            finally:
                connection.unregister("_active_cost_batch")
            connection.register("_active_clipped_batch", diagnostics)
            try:
                connection.execute(
                    "INSERT INTO _active_clipped_grades "
                    "SELECT * FROM _active_clipped_batch"
                )
            finally:
                connection.unregister("_active_clipped_batch")
            edge_count += count
            incomplete_count += missing
            unknown_surfaces.update(batch_unknown)

        clipped_by_class, longest = _summarize_clipped_grades(
            connection, "_active_clipped_grades",
            network.bike_speed_table.clipped_grade_report_limit,
        )
        write_parquet(connection, "SELECT * FROM _active_cost_result", temporary)
        temporary.replace(output)
    finally:
        reader_connection.close()
        temporary.unlink(missing_ok=True)

    summary = ActiveCostSummary(
        edge_count=edge_count,
        incomplete_profile_count=incomplete_count,
        unknown_surface_count=sum(unknown_surfaces.values()),
        unknown_surface_values=dict(sorted(unknown_surfaces.items())),
        clipped_segments_by_class=clipped_by_class,
        longest_clipped_edges=longest,
    )
    write_active_grade_report(summary, output.with_suffix(".grades.md"))
    return summary


def write_active_grade_report(summary: ActiveCostSummary, path: str | Path) -> None:
    """Report clipped directed segments and longest affected edges (9.3, 9.7)."""
    lines = ["# Active-mode clipped grades", ""]
    lines.extend(_grade_report_lines(
        summary.clipped_segments_by_class, summary.longest_clipped_edges
    ))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
