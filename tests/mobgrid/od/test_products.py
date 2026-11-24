import heapq

import numpy as np
import pytest
from mobgrid.graph.csr import csr_from_indexed_edges
from mobgrid.graph.dijkstra import SearchWorkspace, search
from mobgrid.od.products import SearchProducts


def _fixture():
    graph = csr_from_indexed_edges(
        "foot",
        np.arange(6, dtype=np.int64),
        np.array([0, 0, 1, 2, 3, 4]),
        np.array([1, 2, 3, 3, 4, 5]),
        {
            "time_s": np.array([30, 55, 40, 30, 60, 30], dtype=np.float32),
            "distance_m": np.array([100, 300, 150, 100, 250, 50], dtype=np.float32),
            "energy_kj": np.array([4, 12, 6, 2, 10, 3], dtype=np.float32),
        },
        reference_mass_kg=74,
        bike_mass_kg=15,
    )
    od = np.array([False, True, False, True, False, True])
    counts = np.array([[0, 0], [3, 0], [0, 2], [4, 1], [0, 5], [2, 3]])
    nearest = np.array(
        [
            [False, False],
            [True, False],
            [False, True],
            [True, True],
            [True, True],
            [True, True],
        ]
    )
    return graph, od, counts, nearest


def _products(od, counts, nearest, bins=(8, 8, 8)):
    return SearchProducts(
        od,
        counts,
        nearest,
        np.array([1, 2]),
        nearest_extra=2,
        bin_widths=(60.0, 250.0, 10.0),
        bin_counts=bins,
    )


def _brute(graph, source, cutoff):
    labels = {source: (0.0, 0.0, 0.0)}
    queue = [(0.0, source)]
    while queue:
        time, node = heapq.heappop(queue)
        if time != labels[node][0]:
            continue
        for edge in range(graph.indptr[node], graph.indptr[node + 1]):
            target = int(graph.indices[edge])
            candidate = tuple(
                labels[node][i] + graph.weights[name][edge]
                for i, name in enumerate(("time_s", "distance_m", "energy_kj"))
            )
            if candidate[0] <= cutoff and (
                target not in labels or candidate[0] < labels[target][0]
            ):
                labels[target] = candidate
                heapq.heappush(queue, (candidate[0], target))
    return labels


@pytest.mark.parametrize("queue", ["heap", "dial"])
def test_products_match_brute_force_and_reset_between_origins(queue):
    graph, od, counts, nearest = _fixture()
    workspace = SearchWorkspace(graph, ("distance_m", "energy_kj"), max_dial_ticks=1800)
    products = _products(od, counts, nearest)
    for source, cutoff in [(0, 180.0), (3, 60.0), (0, 180.0)]:
        result = search(
            graph,
            workspace,
            np.array([source]),
            np.array([0.0]),
            cutoff,
            products=products,
            queue=queue,
            resolution_s=0.1,
        )
        labels = _brute(graph, source, cutoff)
        settled = sorted(labels, key=lambda node: (labels[node][0], node))
        np.testing.assert_array_equal(result.settled, settled)
        times = {node: values[0] for node, values in labels.items()}
        distances = {node: values[1] for node, values in labels.items()}
        energies = {node: values[2] for node, values in labels.items()}
        expected_od = [int(n) for n in settled if od[n]]
        np.testing.assert_array_equal(
            products.od_nodes[: products.od_count], expected_od
        )
        for i, node in enumerate(expected_od):
            np.testing.assert_array_equal(
                products.od_costs[i], [times[node], distances[node], energies[node]]
            )
        for metric, width, values in (
            (0, 60, times),
            (1, 250, distances),
            (2, 10, energies),
        ):
            expected = np.zeros_like(products.curves[metric])
            for node in settled:
                expected[:, int(values[node] // width)] += counts[node]
            np.testing.assert_array_equal(products.curves[metric], expected)
        for kind, limit in enumerate([3, 4]):
            expected = [n for n in settled if nearest[n, kind]][:limit]
            actual = products.nearest_nodes[kind, : products.nearest_counts[kind]]
            np.testing.assert_array_equal(actual, expected)
            for position, node in enumerate(expected):
                np.testing.assert_array_equal(
                    products.nearest_costs[kind, position],
                    [times[node], distances[node], energies[node]],
                )


def test_curves_signal_insufficient_bins():
    graph, od, counts, nearest = _fixture()
    workspace = SearchWorkspace(graph, ("distance_m", "energy_kj"))
    products = _products(od, counts, nearest, bins=(1, 8, 8))
    with pytest.raises(ValueError, match="bin"):
        search(
            graph,
            workspace,
            np.array([0]),
            np.array([0.0]),
            180.0,
            products=products,
        )


def test_accessibility_thresholds_and_first_three_nearest():
    graph = csr_from_indexed_edges(
        "foot",
        np.arange(5, dtype=np.int64),
        np.array([0, 1, 2, 3]),
        np.array([1, 2, 3, 4]),
        {
            "time_s": np.array([850, 50, 850, 950], dtype=np.float32),
            "distance_m": np.ones(4, dtype=np.float32),
            "energy_kj": np.ones(4, dtype=np.float32),
        },
        reference_mass_kg=74,
        bike_mass_kg=15,
    )
    counts = np.array([[0], [1], [1], [1], [1]])
    nearest = np.array([[False], [True], [True], [True], [True]])
    products = SearchProducts(
        np.zeros(5, dtype=np.bool_),
        counts,
        nearest,
        np.array([3]),
        nearest_extra=2,
        bin_widths=(60, 250, 10),
        bin_counts=(46, 1, 1),
    )
    result = search(
        graph,
        SearchWorkspace(graph, ("distance_m", "energy_kj")),
        np.array([0]),
        np.array([0.0]),
        2700,
        products=products,
    )
    assert result.count == 5
    assert [products.curves[0][0, : minute + 1].sum() for minute in (15, 30, 45)] == [
        2,
        3,
        4,
    ]
    np.testing.assert_array_equal(products.nearest_nodes[0, :3], [1, 2, 3])
