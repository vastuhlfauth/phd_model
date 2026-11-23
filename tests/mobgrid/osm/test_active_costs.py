"""Section 9.3/9.7 active-mode edge-cost tests."""

from pathlib import Path

import duckdb
import pytest
from mobgrid.energy.bike import (
    bike_ride_energy_kj,
    climbing_work_j_per_kg,
    drag_work_j,
    ride_speed_and_power,
    rolling_work_j_per_kg,
)
from mobgrid.energy.rates import load_energy_config
from mobgrid.energy.walk import walking_time_and_energy
from mobgrid.osm.active_costs import enrich_active_edge_costs
from mobgrid.osm.bike_speed_table import BikeSpeedTable
from mobgrid.osm.config import load_network_config

ROOT = Path(__file__).resolve().parents[3]
ENERGY_PATH = ROOT / "config" / "energy.yaml"
NETWORK_PATH = ROOT / "config" / "network.yaml"


def _write_tables(tmp_path: Path) -> tuple[Path, Path]:
    connection = duckdb.connect()
    edges_path = tmp_path / "edges.parquet"
    nodes_path = tmp_path / "nodes.parquet"
    connection.execute("""
        CREATE TABLE nodes (
            node_id BIGINT,
            x DOUBLE,
            y DOUBLE,
            elevation_m DOUBLE,
            tags MAP(VARCHAR, VARCHAR),
            graph_node BOOLEAN
        )
    """)
    connection.execute("""
        INSERT INTO nodes VALUES
            (1, 0, 0, 0, map(), true),
            (2, 50, 0, 2.5, map(), true),
            (3, 100, 0, 10, map(), true)
    """)
    connection.execute("""
        CREATE TABLE edges (
            edge_key VARCHAR,
            way_id BIGINT,
            mode VARCHAR,
            node_ids BIGINT[],
            node_elevations_m DOUBLE[],
            length_m DOUBLE,
            highway VARCHAR,
            bike_infra VARCHAR,
            surface VARCHAR,
            tracktype VARCHAR,
            signal_count INTEGER,
            stop_count INTEGER,
            give_way_count INTEGER,
            crossing_count INTEGER,
            to_degree BIGINT,
            to_node_id BIGINT
        )
    """)
    connection.execute("""
        INSERT INTO edges VALUES
            ('walk:f', 10, 'foot', [1, 2, 3], [0, 2.5, 10], 100, 'residential', NULL,
             NULL, NULL, 0, 0, 0, 0, 2, 3),
            ('bike:f', 10, 'bike', [1, 2, 3], [0, 2.5, 10], 100, 'residential',
             'mixed_traffic', 'asphalt', NULL, 0, 0, 0, 0, 2, 3)
    """)
    connection.execute("COPY edges TO ? (FORMAT PARQUET)", [str(edges_path)])
    connection.execute("COPY nodes TO ? (FORMAT PARQUET)", [str(nodes_path)])
    connection.close()
    return edges_path, nodes_path


def test_sloped_edge_costs_match_energy_package_segment_by_segment(tmp_path):
    edges_path, nodes_path = _write_tables(tmp_path)
    energy = load_energy_config(ENERGY_PATH)
    network = load_network_config(NETWORK_PATH)
    costs_path = tmp_path / "active_costs.parquet"
    connection = duckdb.connect()
    try:
        summary = enrich_active_edge_costs(
            connection,
            edges_path,
            nodes_path,
            costs_path,
            energy=energy,
            network=network,
        )
        actual = connection.execute(
            "SELECT * FROM read_parquet(?) ORDER BY edge_key", [str(costs_path)]
        ).to_arrow_table().to_pylist()
    finally:
        connection.close()

    segments = [(50.0, 0.05), (50.0, 0.15)]
    body_mass = energy.reference_mass_kg
    c0 = energy.walking.c0_j_per_kg_m[energy.rate_set]
    walk_time, walk_energy = walking_time_and_energy(
        segments,
        body_mass,
        energy.walking.v0_kmh,
        c0,
        energy.walking.gradient_polynomial_j_per_kg_m,
    )
    bike = energy.bike
    mass_total = body_mass + bike.bike_mass_kg
    speed_cap = network.bike_speed_table.class_cap_kmh["mixed_traffic"] / 3.6
    bike_time = 0.0
    bike_energy = 0.0
    for length_m, grade in segments:
        speed, rider_power = ride_speed_and_power(
            grade,
            bike.power.p0_w,
            bike.power.k,
            bike.power.p_max_w,
            mass_total,
            bike.surface_crr["asphalt_concrete_paved_default"],
            bike.cda_m2,
            bike.rho_air_kg_per_m3,
            bike.drivetrain_efficiency,
            bike.power.v_max_descent_kmh / 3.6,
            speed_cap,
        )
        bike_time += length_m / speed
        bike_energy += bike_ride_energy_kj(
            rolling_work_j_per_kg(
                length_m, grade, bike.surface_crr["asphalt_concrete_paved_default"]
            ),
            climbing_work_j_per_kg(length_m, grade),
            0.0,
            drag_work_j(
                length_m, speed, bike.rho_air_kg_per_m3, bike.cda_m2
            ),
            mass_total,
            bike.gross_muscular_efficiency,
            rider_mass_kg=body_mass,
            pedalled_time_s=length_m / speed if rider_power > 0 else 0.0,
            unloaded_net_met_per_min=bike.pedalling_unloaded_net_met,
        )

    walk_row = next(row for row in actual if row["edge_key"] == "walk:f")
    bike_row = next(row for row in actual if row["edge_key"] == "bike:f")
    assert walk_row["walk_time_s"] == pytest.approx(walk_time)
    assert walk_row["walk_energy_kj"] == pytest.approx(walk_energy)
    assert bike_row["bike_time_s"] == pytest.approx(bike_time)
    assert bike_row["bike_energy_kj"] == pytest.approx(bike_energy)
    assert bike_row["bike_energy_kj"] == pytest.approx(
        bike_row["bike_energy_per_kg_kj_per_kg"] * mass_total
        + bike_row["bike_energy_drag_kj"]
        + bike_row["bike_pedalling_energy_kj"]
    )
    assert summary.edge_count == 2
    assert summary.incomplete_profile_count == 0


def test_active_costs_use_way_specific_elevations(tmp_path):
    edges_path, nodes_path = _write_tables(tmp_path)
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE edges AS SELECT * FROM read_parquet(?)", [str(edges_path)]
    )
    connection.execute(
        "UPDATE edges SET node_elevations_m = [0, 0, 0] WHERE mode = 'foot'"
    )
    connection.execute("COPY edges TO ? (FORMAT PARQUET)", [str(edges_path)])
    energy = load_energy_config(ENERGY_PATH)
    try:
        enrich_active_edge_costs(
            connection, edges_path, nodes_path, tmp_path / "costs.parquet",
            energy=energy, network=load_network_config(NETWORK_PATH),
        )
        walk_time = connection.execute(
            "SELECT walk_time_s FROM read_parquet(?) WHERE edge_key = 'walk:f'",
            [str(tmp_path / "costs.parquet")],
        ).fetchone()[0]
    finally:
        connection.close()

    assert walk_time == pytest.approx(100 / (energy.walking.v0_kmh / 3.6))


def test_steps_use_configured_stair_formula(tmp_path):
    edges_path, nodes_path = _write_tables(tmp_path)
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE edges AS SELECT * FROM read_parquet(?)", [str(edges_path)]
    )
    connection.execute(
        "CREATE TABLE nodes AS SELECT * FROM read_parquet(?)", [str(nodes_path)]
    )
    connection.execute(
        "UPDATE edges SET highway = 'steps' WHERE edge_key = 'walk:f'"
    )
    connection.execute(
        "UPDATE edges SET node_elevations_m = [0, 5, 10] WHERE edge_key = 'walk:f'"
    )
    connection.execute("COPY edges TO ? (FORMAT PARQUET)", [str(edges_path)])
    connection.execute(
        "UPDATE nodes SET elevation_m = CASE node_id WHEN 1 THEN 0 "
        "ELSE CASE node_id WHEN 2 THEN 5 ELSE 10 END END"
    )
    connection.execute("COPY nodes TO ? (FORMAT PARQUET)", [str(nodes_path)])
    connection.close()

    energy = load_energy_config(ENERGY_PATH)
    network = load_network_config(NETWORK_PATH)
    connection = duckdb.connect()
    try:
        summary = enrich_active_edge_costs(
            connection,
            edges_path,
            nodes_path,
            tmp_path / "active_costs.parquet",
            energy=energy,
            network=network,
        )
        walk_time, walk_energy = connection.execute(
            "SELECT walk_time_s, walk_energy_kj FROM read_parquet(?) "
            "WHERE edge_key = 'walk:f'",
            [str(tmp_path / "active_costs.parquet")],
        ).fetchone()
    finally:
        connection.close()
    assert walk_time == pytest.approx(10.0 / energy.stairs.up_speed_m_per_s)
    assert walk_energy == pytest.approx(
        energy.reference_mass_kg * 9.81 * 10 / energy.stairs.up_efficiency / 1000
    )
    assert summary.unknown_surface_count == 0


def test_missing_node_elevation_leaves_edge_costs_null_and_is_counted(tmp_path):
    edges_path, nodes_path = _write_tables(tmp_path)
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE nodes AS SELECT * FROM read_parquet(?)", [str(nodes_path)]
    )
    connection.execute(
        "UPDATE nodes SET elevation_m = NULL WHERE node_id = 2"
    )
    connection.execute("COPY nodes TO ? (FORMAT PARQUET)", [str(nodes_path)])
    connection.execute(
        "CREATE TABLE edges AS SELECT * FROM read_parquet(?)", [str(edges_path)]
    )
    connection.execute("UPDATE edges SET node_elevations_m = [0, NULL, 10]")
    connection.execute("COPY edges TO ? (FORMAT PARQUET)", [str(edges_path)])
    connection.close()

    connection = duckdb.connect()
    costs_path = tmp_path / "active_costs.parquet"
    try:
        summary = enrich_active_edge_costs(
            connection,
            edges_path,
            nodes_path,
            costs_path,
            energy=load_energy_config(ENERGY_PATH),
            network=load_network_config(NETWORK_PATH),
        )
        null_costs = connection.execute(
            "SELECT count(*) FROM read_parquet(?) "
            "WHERE walk_time_s IS NULL AND bike_time_s IS NULL AND climb_m IS NULL",
            [str(costs_path)],
        ).fetchone()[0]
    finally:
        connection.close()
    assert null_costs == 2
    assert summary.incomplete_profile_count == 2


def test_tracktype_surface_fallback_precedes_highway_default(tmp_path):
    edges_path, nodes_path = _write_tables(tmp_path)
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE edges AS SELECT * FROM read_parquet(?)", [str(edges_path)]
    )
    connection.execute(
        "UPDATE edges SET surface = NULL, tracktype = 'grade2' "
        "WHERE mode = 'bike'"
    )
    connection.execute("COPY edges TO ? (FORMAT PARQUET)", [str(edges_path)])
    connection.close()

    energy = load_energy_config(ENERGY_PATH)
    network = load_network_config(NETWORK_PATH)
    connection = duckdb.connect()
    try:
        enrich_active_edge_costs(
            connection,
            edges_path,
            nodes_path,
            tmp_path / "active_costs.parquet",
            energy=energy,
            network=network,
        )
        bike_time = connection.execute(
            "SELECT bike_time_s FROM read_parquet(?) WHERE edge_key = 'bike:f'",
            [str(tmp_path / "active_costs.parquet")],
        ).fetchone()[0]
    finally:
        connection.close()

    bike = energy.bike
    crr = bike.surface_crr["fine_gravel"]
    cap = network.bike_speed_table.class_cap_kmh["mixed_traffic"] / 3.6
    expected_time = 0.0
    for length_m, grade in ((50.0, 0.05), (50.0, 0.15)):
        speed, _ = ride_speed_and_power(
            grade,
            bike.power.p0_w,
            bike.power.k,
            bike.power.p_max_w,
            energy.reference_mass_kg + bike.bike_mass_kg,
            crr,
            bike.cda_m2,
            bike.rho_air_kg_per_m3,
            bike.drivetrain_efficiency,
            bike.power.v_max_descent_kmh / 3.6,
            cap,
        )
        expected_time += length_m / speed
    assert bike_time == pytest.approx(expected_time)


def test_bike_stops_use_configured_probabilities_and_unknown_surfaces_fallback(
    tmp_path,
):
    edges_path, nodes_path = _write_tables(tmp_path)
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE edges AS SELECT * FROM read_parquet(?)", [str(edges_path)]
    )
    connection.execute(
        "UPDATE edges SET bike_infra = 'separated_track_path', "
        "surface = 'mystery_road', signal_count = 1, stop_count = 1, "
        "give_way_count = 1, crossing_count = 1, to_degree = 3 "
        "WHERE mode = 'bike'"
    )
    connection.execute("COPY edges TO ? (FORMAT PARQUET)", [str(edges_path)])
    connection.close()

    energy = load_energy_config(ENERGY_PATH)
    network = load_network_config(NETWORK_PATH)
    costs_path = tmp_path / "active_costs.parquet"
    connection = duckdb.connect()
    try:
        summary = enrich_active_edge_costs(
            connection,
            edges_path,
            nodes_path,
            costs_path,
            energy=energy,
            network=network,
        )
        bike_time, bike_energy, separated_length = connection.execute(
            "SELECT bike_time_s, bike_energy_kj, separated_length_m "
            "FROM read_parquet(?) WHERE edge_key = 'bike:f'",
            [str(costs_path)],
        ).fetchone()
    finally:
        connection.close()

    bike = energy.bike
    mass = energy.reference_mass_kg
    mass_total = mass + bike.bike_mass_kg
    crr = bike.surface_crr["asphalt_concrete_paved_default"]
    cap = network.bike_speed_table.class_cap_kmh["separated_track_path"] / 3.6
    segment_specs = [(50.0, 0.05), (50.0, 0.15)]
    ride_time = 0.0
    roll_work = 0.0
    climb_work = 0.0
    drag_total = 0.0
    pedalled_time = 0.0
    for length_m, grade in segment_specs:
        speed, rider_power = ride_speed_and_power(
            grade,
            bike.power.p0_w,
            bike.power.k,
            bike.power.p_max_w,
            mass_total,
            crr,
            bike.cda_m2,
            bike.rho_air_kg_per_m3,
            bike.drivetrain_efficiency,
            bike.power.v_max_descent_kmh / 3.6,
            cap,
        )
        ride_time += length_m / speed
        if rider_power > 0:
            roll_work += rolling_work_j_per_kg(length_m, grade, crr)
            climb_work += climbing_work_j_per_kg(length_m, grade)
            drag_total += drag_work_j(
                length_m, speed, bike.rho_air_kg_per_m3, bike.cda_m2
            )
            pedalled_time += length_m / speed
    mean_speed = 100.0 / ride_time
    stops = bike.stops
    signal_probability = stops.red_time_s / stops.signal_cycle_s
    expected_stops = (
        signal_probability + 1.0 + 0.5 + 0.3 + 0.5
    )
    signal_wait = stops.red_time_s**2 / (2 * stops.signal_cycle_s)
    expected_stop_time = (
        (mean_speed / (2 * stops.deceleration_m_per_s2)
         + mean_speed / (2 * stops.acceleration_m_per_s2))
        * expected_stops + signal_wait
    )
    stop_work = expected_stops * 0.5 * mean_speed**2
    expected_energy = bike_ride_energy_kj(
        roll_work,
        climb_work,
        stop_work,
        drag_total,
        mass_total,
        bike.gross_muscular_efficiency,
        bike.separated_infra_factor,
        rider_mass_kg=mass,
        pedalled_time_s=pedalled_time,
        unloaded_net_met_per_min=bike.pedalling_unloaded_net_met,
    )
    assert bike_time == pytest.approx(ride_time + expected_stop_time)
    assert bike_energy == pytest.approx(expected_energy)
    assert separated_length == pytest.approx(100.0)
    assert summary.unknown_surface_count == 1
    assert summary.unknown_surface_values == {"mystery_road": 1}


def test_bike_stop_adds_only_time_beyond_cruising_at_15_kmh(tmp_path, monkeypatch):
    import numpy as np

    edges_path, nodes_path = _write_tables(tmp_path)
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE edges AS SELECT * FROM read_parquet(?)", [str(edges_path)]
    )
    connection.execute("UPDATE edges SET signal_count = 1 WHERE mode = 'bike'")
    connection.execute("COPY edges TO ? (FORMAT PARQUET)", [str(edges_path)])
    energy = load_energy_config(ENERGY_PATH)
    stops = energy.bike.stops.model_copy(
        update={"red_time_s": energy.bike.stops.signal_cycle_s}
    )
    energy = energy.model_copy(
        update={"bike": energy.bike.model_copy(update={"stops": stops})}
    )
    speed = 15.0 / 3.6
    monkeypatch.setattr(
        BikeSpeedTable,
        "lookup",
        lambda self, grades: (np.full_like(grades, speed), np.ones_like(grades)),
    )
    costs_path = tmp_path / "costs.parquet"
    try:
        enrich_active_edge_costs(
            connection,
            edges_path,
            nodes_path,
            costs_path,
            energy=energy,
            network=load_network_config(NETWORK_PATH),
        )
        bike_time = connection.execute(
            "SELECT bike_time_s FROM read_parquet(?) WHERE edge_key = 'bike:f'",
            [str(costs_path)],
        ).fetchone()[0]
    finally:
        connection.close()

    expected_wait = stops.red_time_s**2 / (2 * stops.signal_cycle_s)
    expected_loss = (
        speed / (2 * stops.deceleration_m_per_s2)
        + speed / (2 * stops.acceleration_m_per_s2)
    )
    assert bike_time == pytest.approx(100 / speed + expected_loss + expected_wait)


def test_extreme_grades_are_clipped_counted_and_reported(tmp_path):
    edges_path, nodes_path = _write_tables(tmp_path)
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE nodes AS SELECT * FROM read_parquet(?)", [str(nodes_path)]
    )
    connection.execute("UPDATE nodes SET elevation_m = (node_id - 1) * 30")
    connection.execute("COPY nodes TO ? (FORMAT PARQUET)", [str(nodes_path)])
    connection.execute(
        "CREATE TABLE edges AS SELECT * FROM read_parquet(?)", [str(edges_path)]
    )
    connection.execute("UPDATE edges SET node_elevations_m = [0, 30, 60]")
    connection.execute("COPY edges TO ? (FORMAT PARQUET)", [str(edges_path)])
    energy = load_energy_config(ENERGY_PATH)
    network = load_network_config(NETWORK_PATH)
    output = tmp_path / "costs.parquet"
    try:
        summary = enrich_active_edge_costs(
            connection, edges_path, nodes_path, output, energy=energy, network=network
        )
        walk_time = connection.execute(
            "SELECT walk_time_s FROM read_parquet(?) WHERE edge_key = 'walk:f'",
            [str(output)],
        ).fetchone()[0]
        bike_time = connection.execute(
            "SELECT bike_time_s FROM read_parquet(?) WHERE edge_key = 'bike:f'",
            [str(output)],
        ).fetchone()[0]
    finally:
        connection.close()

    expected_time, _ = walking_time_and_energy(
        [(50.0, 0.45), (50.0, 0.45)],
        energy.reference_mass_kg,
        energy.walking.v0_kmh,
        energy.walking.c0_j_per_kg_m[energy.rate_set],
        energy.walking.gradient_polynomial_j_per_kg_m,
    )
    assert walk_time == pytest.approx(expected_time)
    bike = energy.bike
    bike_speed, _ = ride_speed_and_power(
        0.2,
        bike.power.p0_w,
        bike.power.k,
        bike.power.p_max_w,
        energy.reference_mass_kg + bike.bike_mass_kg,
        bike.surface_crr["asphalt_concrete_paved_default"],
        bike.cda_m2,
        bike.rho_air_kg_per_m3,
        bike.drivetrain_efficiency,
        bike.power.v_max_descent_kmh / 3.6,
        network.bike_speed_table.class_cap_kmh["mixed_traffic"] / 3.6,
    )
    assert bike_time == pytest.approx(100 / bike_speed)
    assert summary.clipped_segments_by_class[("foot", "residential")] == (2, 100.0)
    assert summary.clipped_segments_by_class[("bike", "residential")] == (2, 100.0)
    report = output.with_suffix(".grades.md").read_text(encoding="utf-8")
    assert "walk:f" in report and "bike:f" in report
    assert "0.600" in report and "residential" in report


def test_clipped_report_lists_only_the_twenty_longest_edges(tmp_path, monkeypatch):
    import mobgrid.osm.active_costs as active_costs

    monkeypatch.setattr(active_costs, "_EDGE_BATCH_SIZE", 3)
    edges_path, nodes_path = _write_tables(tmp_path)
    connection = duckdb.connect()
    connection.execute(
        "CREATE TABLE nodes AS SELECT * FROM read_parquet(?)", [str(nodes_path)]
    )
    connection.execute("UPDATE nodes SET elevation_m = (node_id - 1) * 30")
    connection.execute("COPY nodes TO ? (FORMAT PARQUET)", [str(nodes_path)])
    connection.execute("""
        CREATE TABLE edges AS
        SELECT 'walk:' || i AS edge_key, 10 AS way_id, 'foot' AS mode,
               [1, 2, 3]::BIGINT[] AS node_ids,
               [0, 30, 60]::DOUBLE[] AS node_elevations_m,
               100.0 + i AS length_m,
               'residential' AS highway, NULL::VARCHAR AS bike_infra,
               NULL::VARCHAR AS surface, NULL::VARCHAR AS tracktype,
               0 AS signal_count, 0 AS stop_count, 0 AS give_way_count,
               0 AS crossing_count, 2 AS to_degree, 3 AS to_node_id
        FROM range(21) AS numbers(i)
    """)
    connection.execute("COPY edges TO ? (FORMAT PARQUET)", [str(edges_path)])
    try:
        summary = enrich_active_edge_costs(
            connection,
            edges_path,
            nodes_path,
            tmp_path / "costs.parquet",
            energy=load_energy_config(ENERGY_PATH),
            network=load_network_config(NETWORK_PATH),
        )
    finally:
        connection.close()

    assert len(summary.longest_clipped_edges) == 20
    assert summary.longest_clipped_edges[0][0] == "walk:20"
    assert summary.longest_clipped_edges[-1][0] == "walk:1"
