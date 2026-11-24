import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from mobgrid.graph.csr import (
    bike_energy_for_mass,
    build_csr_graph,
    load_graph,
    save_graph,
    validate_edge_cost_join,
)


@pytest.fixture
def edge_files(tmp_path):
    edges = [
        {
            "edge_key": "c1",
            "mode": "car",
            "from_node_id": 101,
            "to_node_id": 12,
            "highway": "residential",
            "length_m": 100.0,
            "climb_m": 3.0,
        },
        {
            "edge_key": "c2",
            "mode": "car",
            "from_node_id": 50,
            "to_node_id": 101,
            "highway": "primary",
            "length_m": 200.0,
            "climb_m": 4.0,
        },
        {
            "edge_key": "b1",
            "mode": "bike",
            "from_node_id": 5,
            "to_node_id": 7,
            "highway": "residential",
            "length_m": 20.0,
            "climb_m": 1.5,
        },
        {
            "edge_key": "b2",
            "mode": "bike",
            "from_node_id": 7,
            "to_node_id": 9,
            "highway": "steps",
            "length_m": 5.0,
            "climb_m": 2.0,
        },
        {
            "edge_key": "f1",
            "mode": "foot",
            "from_node_id": 2,
            "to_node_id": 3,
            "highway": "footway",
            "length_m": 12.0,
            "climb_m": 0.5,
        },
    ]
    costs = [
        {
            "edge_key": row["edge_key"],
            "length_m": row["length_m"],
            "car_time_s": 2.0 + index,
            "walk_time_s": 4.0 + index,
            "walk_energy_kj": 1.0 + index,
            "bike_time_s": 3.0 + index,
            "bike_energy_kj": (
                2.1 * (74.0 + 15.0) + 2.2 + 2.3
                if row["edge_key"] == "b1"
                else 13.0
                if row["edge_key"] == "b2"
                else 10.0 + index
            ),
            "bike_energy_per_kg_kj_per_kg": (
                None if row["highway"] == "steps" else 0.1 + index
            ),
            "bike_energy_drag_kj": (None if row["highway"] == "steps" else 0.2 + index),
            "bike_pedalling_energy_kj": (
                None if row["highway"] == "steps" else 0.3 + index
            ),
            "climb_m": row["climb_m"],
            "separated_length_m": 4.0 if row["mode"] == "bike" else 0.0,
            "is_urban": True,
            "speed_limit_bucket": "30-50" if index % 2 == 0 else "50-80",
        }
        for index, row in enumerate(edges)
    ]
    edges_path = tmp_path / "edges.parquet"
    costs_path = tmp_path / "edge_costs.parquet"
    pq.write_table(pa.Table.from_pylist(edges), edges_path)
    pq.write_table(pa.Table.from_pylist(costs), costs_path)
    return edges_path, costs_path


def test_car_csr_uses_compact_categories_and_forward_edge_transpose(edge_files):
    edges_path, costs_path = edge_files
    connection = duckdb.connect()
    validate_edge_cost_join(connection, edges_path, costs_path)

    graph = build_csr_graph(
        connection,
        edges_path,
        costs_path,
        "car",
        reference_mass_kg=74.0,
        bike_mass_kg=15.0,
        car_energy_kj_per_s=0.1,
    )

    np.testing.assert_array_equal(graph.node_ids, [12, 50, 101])
    assert graph.node_ids.dtype == np.int64
    assert graph.indptr.dtype == np.int64
    assert graph.indices.dtype == np.int32
    assert graph.weights["time_s"].dtype == np.float32
    np.testing.assert_array_equal(graph.weights["time_s"], [3.0, 2.0])
    np.testing.assert_allclose(graph.weights["energy_kj"], [0.3, 0.2])
    assert graph.road_class_ids.dtype == np.uint8
    assert graph.speed_bucket_ids.dtype == np.uint8
    assert [graph.road_classes[i] for i in graph.road_class_ids] == [
        "primary",
        "residential",
    ]
    assert [graph.speed_buckets[i] for i in graph.speed_bucket_ids] == [
        "50-80",
        "30-50",
    ]
    assert not any(name.startswith("time_s:") for name in graph.weights)
    np.testing.assert_array_equal(graph.member_offsets, [0, 1, 2])
    np.testing.assert_array_equal(graph.member_edge_rows, [1, 0])
    np.testing.assert_array_equal(graph.reverse_indptr, [0, 1, 1, 2])
    np.testing.assert_array_equal(graph.reverse_indices, [2, 1])
    np.testing.assert_array_equal(graph.reverse_edge_indices, [1, 0])
    for name in graph.weights:
        np.testing.assert_array_equal(
            graph.weights[name][graph.reverse_edge_indices], graph.weights[name][::-1]
        )
    connection.close()


def test_bike_components_and_mass_sensitive_energy_are_preserved(edge_files):
    edges_path, costs_path = edge_files
    connection = duckdb.connect()
    validate_edge_cost_join(connection, edges_path, costs_path)

    graph = build_csr_graph(
        connection,
        edges_path,
        costs_path,
        "bike",
        reference_mass_kg=74.0,
        bike_mass_kg=15.0,
        car_energy_kj_per_s=0.0,
    )

    np.testing.assert_allclose(
        graph.weights["bike_energy_per_kg_kj_per_kg"], [2.1, 0.0]
    )
    np.testing.assert_allclose(graph.weights["bike_energy_drag_kj"], [2.2, 0.0])
    np.testing.assert_allclose(graph.weights["bike_pedalling_energy_kj"], [2.3, 0.0])
    np.testing.assert_array_equal(graph.weights["bike_energy_step_kj"], [0.0, 13.0])
    np.testing.assert_array_equal(
        bike_energy_for_mass(graph, 74.0), graph.weights["energy_kj"]
    )
    assert bike_energy_for_mass(graph, 84.0)[0] > graph.weights["energy_kj"][0]
    assert bike_energy_for_mass(graph, 84.0)[1] > graph.weights["energy_kj"][1]

    output = edge_files[0].parent / "bike.npz"
    save_graph(graph, output)
    restored = load_graph(output)
    np.testing.assert_array_equal(restored.node_ids, graph.node_ids)
    np.testing.assert_array_equal(restored.member_offsets, graph.member_offsets)
    np.testing.assert_array_equal(restored.member_edge_rows, graph.member_edge_rows)
    np.testing.assert_array_equal(
        restored.reverse_edge_indices, graph.reverse_edge_indices
    )
    for name in graph.weights:
        np.testing.assert_array_equal(restored.weights[name], graph.weights[name])
    connection.close()


def test_edge_cost_join_rejects_duplicate_cost_keys(edge_files, tmp_path):
    edges_path, costs_path = edge_files
    costs = pq.read_table(costs_path).to_pylist()
    duplicate_path = tmp_path / "duplicate_costs.parquet"
    pq.write_table(pa.Table.from_pylist(costs + [costs[0]]), duplicate_path)

    with duckdb.connect() as connection, pytest.raises(ValueError, match="one-to-one"):
        validate_edge_cost_join(connection, edges_path, duplicate_path)
