import numpy as np
from mobgrid.graph.csr import csr_from_indexed_edges
from mobgrid.graph.simplify import (
    contract_degree_two,
    largest_strong_component,
)


def _graph(edges, mode="bike"):
    node_ids = np.asarray(sorted({node for edge in edges for node in edge[:2]}))
    node_index = {node: index for index, node in enumerate(node_ids)}
    sources = np.asarray([node_index[edge[0]] for edge in edges], dtype=np.int64)
    targets = np.asarray([node_index[edge[1]] for edge in edges], dtype=np.int64)
    weights = {
        "time_s": np.asarray([edge[2] for edge in edges], dtype=np.float32),
        "distance_m": np.asarray([edge[3] for edge in edges], dtype=np.float32),
        "energy_kj": np.asarray([edge[4] for edge in edges], dtype=np.float32),
        "climb_m": np.asarray([edge[5] for edge in edges], dtype=np.float32),
        "separated_length_m": np.asarray([edge[6] for edge in edges], dtype=np.float32),
        "bike_energy_per_kg_kj_per_kg": np.asarray(
            [edge[7] for edge in edges], dtype=np.float32
        ),
    }
    return csr_from_indexed_edges(
        mode,
        node_ids,
        sources,
        targets,
        weights,
        reference_mass_kg=74.0,
        bike_mass_kg=15.0,
    )


def _weight(graph, source_id, target_id, name):
    source = int(np.flatnonzero(graph.node_ids == source_id)[0])
    target = int(np.flatnonzero(graph.node_ids == target_id)[0])
    for position in range(graph.indptr[source], graph.indptr[source + 1]):
        if graph.indices[position] == target:
            return graph.weights[name][position]
    raise AssertionError(f"missing edge {source_id}->{target_id}")


def test_contracts_bidirectional_chain_with_exact_sums_for_every_weight():
    graph = _graph(
        [
            (10, 20, 1, 10, 2, 1, 3, 0.1),
            (20, 10, 1.5, 11, 3, 2, 4, 0.2),
            (20, 30, 2, 20, 4, 3, 5, 0.3),
            (30, 20, 2.5, 21, 5, 4, 6, 0.4),
            (30, 40, 3, 30, 6, 5, 7, 0.5),
            (40, 30, 3.5, 31, 7, 6, 8, 0.6),
        ]
    )
    kept = np.asarray([True, False, False, True])

    contracted = contract_degree_two(graph, kept)

    np.testing.assert_array_equal(contracted.node_ids, [10, 40])
    assert len(contracted.indices) == 2
    for name in graph.weights:
        np.testing.assert_allclose(
            _weight(contracted, 10, 40, name),
            sum(
                _weight(graph, a, b, name)
                for a, b in (
                    (10, 20),
                    (20, 30),
                    (30, 40),
                )
            ),
        )
        np.testing.assert_allclose(
            _weight(contracted, 40, 10, name),
            sum(
                _weight(graph, a, b, name)
                for a, b in (
                    (40, 30),
                    (30, 20),
                    (20, 10),
                )
            ),
        )


def test_contracts_one_way_chain_but_stops_at_kept_node():
    graph = _graph(
        [
            (1, 2, 2, 20, 4, 1, 5, 0.3),
            (2, 3, 3, 30, 6, 2, 7, 0.4),
            (3, 4, 4, 40, 8, 3, 9, 0.5),
        ]
    )
    kept = np.asarray([True, False, True, True])

    contracted = contract_degree_two(graph, kept)

    np.testing.assert_array_equal(contracted.node_ids, [1, 3, 4])
    assert len(contracted.indices) == 2
    np.testing.assert_allclose(_weight(contracted, 1, 3, "time_s"), 5.0)
    np.testing.assert_allclose(_weight(contracted, 1, 3, "distance_m"), 50.0)
    np.testing.assert_allclose(_weight(contracted, 1, 3, "energy_kj"), 10.0)


def test_largest_strong_component_drops_smaller_disconnected_cycle():
    graph = _graph(
        [
            (1, 2, 1, 1, 1, 0, 0, 0),
            (2, 1, 1, 1, 1, 0, 0, 0),
            (2, 3, 1, 1, 1, 0, 0, 0),
            (3, 2, 1, 1, 1, 0, 0, 0),
            (4, 5, 1, 1, 1, 0, 0, 0),
            (5, 4, 1, 1, 1, 0, 0, 0),
        ]
    )

    largest = largest_strong_component(graph)

    np.testing.assert_array_equal(largest.node_ids, [1, 2, 3])
    assert len(largest.indices) == 4


def test_unanchored_degree_two_cycle_is_left_intact():
    graph = _graph(
        [
            (1, 2, 1, 1, 1, 0, 0, 0),
            (2, 3, 1, 1, 1, 0, 0, 0),
            (3, 4, 1, 1, 1, 0, 0, 0),
            (4, 1, 1, 1, 1, 0, 0, 0),
        ]
    )

    contracted = contract_degree_two(graph, np.zeros(4, dtype=np.bool_))

    np.testing.assert_array_equal(contracted.node_ids, graph.node_ids)
    np.testing.assert_array_equal(contracted.indptr, graph.indptr)
    np.testing.assert_array_equal(contracted.indices, graph.indices)
