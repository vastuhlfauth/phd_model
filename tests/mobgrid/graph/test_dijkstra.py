import heapq
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from mobgrid.graph.config import load_search_config
from mobgrid.graph.csr import csr_from_indexed_edges
from mobgrid.graph.dijkstra import SearchWorkspace, path_time_splits, search
from pydantic import ValidationError


def _random_graph(seed):
    rng = np.random.default_rng(seed)
    n = 60
    sources = rng.integers(0, n, 300)
    targets = rng.integers(0, n, 300)
    times = rng.integers(1, 200, 300).astype(np.float32) / 10
    return csr_from_indexed_edges(
        "car",
        np.arange(n, dtype=np.int64),
        sources,
        targets,
        {
            "time_s": times,
            "distance_m": rng.integers(1, 300, 300).astype(np.float32),
            "energy_kj": rng.integers(1, 100, 300).astype(np.float32),
        },
        reference_mass_kg=74,
        bike_mass_kg=15,
    )


def _reference(graph, sources, offsets, cutoff, times):
    result = np.full(len(graph.node_ids), np.inf)
    heap = []
    for node, offset in zip(sources, offsets, strict=True):
        if offset < result[node] and offset <= cutoff:
            result[node] = offset
            heapq.heappush(heap, (offset, node))
    while heap:
        distance, node = heapq.heappop(heap)
        if distance != result[node]:
            continue
        for edge in range(graph.indptr[node], graph.indptr[node + 1]):
            target = graph.indices[edge]
            candidate = distance + times[edge]
            if candidate <= cutoff and candidate < result[target]:
                result[target] = candidate
                heapq.heappush(heap, (candidate, target))
    return result


@pytest.mark.parametrize("seed", [4, 17, 91])
def test_heap_matches_reference_and_predecessor_weights(seed):
    graph = _random_graph(seed)
    workspace = SearchWorkspace(graph, ("distance_m", "energy_kj"), max_dial_ticks=600)
    sources = np.array([3, 11, 3])
    offsets = np.array([1.5, 0.0, 3.0])
    result = search(graph, workspace, sources, offsets, cutoff_s=50.0)
    expected = _reference(graph, sources, offsets, 50.0, graph.weights["time_s"])
    np.testing.assert_array_equal(result.time_s, expected)
    for node in result.settled:
        predecessor = result.predecessor_node[node]
        if predecessor >= 0:
            edge = result.predecessor_edge[node]
            assert graph.indices[edge] == node
            assert graph.indptr[predecessor] <= edge < graph.indptr[predecessor + 1]
            for index, name in enumerate(("distance_m", "energy_kj")):
                assert result.secondary[node, index] == (
                    result.secondary[predecessor, index] + graph.weights[name][edge]
                )


def test_workspace_reuse_and_dial_match_rounded_heap():
    graph = _random_graph(22)
    workspace = SearchWorkspace(graph, ("distance_m", "energy_kj"), max_dial_ticks=600)
    for sources, offsets, cutoff in [
        (np.array([2, 8]), np.array([0.0, 0.2]), 60.0),
        (np.array([49]), np.array([0.0]), 4.0),
        (np.array([1, 2]), np.array([0.0, 0.3]), 40.0),
    ]:
        rounded = np.rint(graph.weights["time_s"] / 0.1).astype(np.int64)
        dial = search(
            graph, workspace, sources, offsets, cutoff, queue="dial", resolution_s=0.1
        )
        dial_ticks = dial.time_s.copy()
        rounded_graph = replace(
            graph, weights={**graph.weights, "time_s": rounded.astype(np.float32)}
        )
        rounded_workspace = SearchWorkspace(rounded_graph, ("distance_m", "energy_kj"))
        rounded_heap = search(
            rounded_graph,
            rounded_workspace,
            sources,
            np.rint(offsets / 0.1),
            cutoff / 0.1,
        )
        actual_ticks = np.where(
            workspace.stamps == dial.generation, workspace.times, np.inf
        )
        np.testing.assert_array_equal(actual_ticks, rounded_heap.time_s)
        expected = _reference(graph, sources, offsets / 0.1, cutoff / 0.1, rounded)
        np.testing.assert_allclose(dial_ticks / 0.1, expected, rtol=0, atol=1e-10)
        heap = search(graph, workspace, sources, offsets, cutoff, queue="heap")
        expected_float = _reference(
            graph, sources, offsets, cutoff, graph.weights["time_s"]
        )
        np.testing.assert_array_equal(heap.time_s, expected_float)


def test_splits_follow_predecessors_only_when_requested():
    graph = csr_from_indexed_edges(
        "car",
        np.arange(4, dtype=np.int64),
        np.array([0, 1, 2]),
        np.array([1, 2, 3]),
        {"time_s": np.array([2, 3, 5], dtype=np.float32)},
        reference_mass_kg=74,
        bike_mass_kg=15,
        road_classes=("a", "b"),
        road_class_ids=np.array([0, 1, 0]),
        speed_buckets=("x", "y"),
        speed_bucket_ids=np.array([0, 0, 1]),
    )
    workspace = SearchWorkspace(graph, ())
    result = search(graph, workspace, np.array([0]), np.array([1.0]), 20)
    classes, buckets = path_time_splits(graph, result, np.array([2, 3]))
    np.testing.assert_array_equal(classes, [[2, 3], [7, 3]])
    np.testing.assert_array_equal(buckets, [[5, 0], [5, 5]])
    search(graph, workspace, np.array([3]), np.array([0.0]), 20)
    with pytest.raises(ValueError, match="current search"):
        path_time_splits(graph, result, np.array([2]))


def test_rejects_negative_or_nonfinite_inputs():
    graph = _random_graph(1)
    workspace = SearchWorkspace(graph, ("distance_m",))
    with pytest.raises(ValueError):
        search(graph, workspace, np.array([1]), np.array([-1.0]), 10.0)


def test_search_configuration_rejects_invalid_cutoffs_and_resolution():
    config = load_search_config(
        Path(__file__).resolve().parents[3] / "config" / "search.yaml"
    )
    values = config.model_dump()
    values["dial_resolution_s"] = 0
    with pytest.raises(ValidationError):
        type(config).model_validate(values)
    values["dial_resolution_s"] = config.dial_resolution_s
    values["cutoff_s_by_mode"] = {"car": -1, "bike": None, "foot": None}
    with pytest.raises(ValidationError):
        type(config).model_validate(values)


def test_reused_workspace_masks_unreached_labels():
    graph = _random_graph(99)
    workspace = SearchWorkspace(graph, ("distance_m",))
    old = search(graph, workspace, np.array([0]), np.array([0.0]), 100)
    result = search(graph, workspace, np.array([1]), np.array([0.0]), 0)
    with pytest.raises(ValueError, match="invalidated"):
        _ = old.time_s
    unreachable = np.arange(len(graph.node_ids)) != 1
    assert np.isinf(result.time_s[unreachable]).all()
    assert (result.predecessor_node[unreachable] == -1).all()
    assert (result.predecessor_edge[unreachable] == -1).all()
    assert np.isnan(result.secondary[unreachable]).all()


def test_reverse_search_uses_forward_weights_and_predecessor_edges():
    graph = csr_from_indexed_edges(
        "foot",
        np.arange(3, dtype=np.int64),
        np.array([0, 1, 0]),
        np.array([1, 2, 2]),
        {
            "time_s": np.array([1, 2, 10], dtype=np.float32),
            "distance_m": np.array([5, 6, 90], dtype=np.float32),
        },
        reference_mass_kg=74,
        bike_mass_kg=15,
    )
    result = search(
        graph,
        SearchWorkspace(graph, ("distance_m",)),
        np.array([2]),
        np.array([0.0]),
        20,
        reverse=True,
    )
    np.testing.assert_array_equal(result.time_s, [3, 2, 0])
    assert result.secondary[0, 0] == 11
    for node in [0, 1]:
        edge = result.predecessor_edge[node]
        assert graph.indices[edge] == result.predecessor_node[node]
        assert graph.indptr[node] <= edge < graph.indptr[node + 1]


def test_dial_includes_cutoff_on_decimal_tick_boundary():
    graph = csr_from_indexed_edges(
        "foot",
        np.array([0, 1]),
        np.array([0]),
        np.array([1]),
        {"time_s": np.array([0.3], dtype=np.float32)},
        reference_mass_kg=74,
        bike_mass_kg=15,
    )
    workspace = SearchWorkspace(graph, (), max_dial_ticks=3)
    result = search(
        graph,
        workspace,
        np.array([0]),
        np.array([0.0]),
        0.3,
        queue="dial",
        resolution_s=0.1,
    )
    np.testing.assert_array_equal(result.settled, [0, 1])


def test_tied_rounded_paths_have_same_predecessors_and_secondary_costs():
    graph = csr_from_indexed_edges(
        "foot",
        np.arange(4, dtype=np.int64),
        np.array([0, 0, 1, 2]),
        np.array([1, 2, 3, 3]),
        {
            "time_s": np.array([1, 1, 1, 1], dtype=np.float32),
            "distance_m": np.array([2, 10, 3, 20], dtype=np.float32),
        },
        reference_mass_kg=74,
        bike_mass_kg=15,
    )
    workspace = SearchWorkspace(graph, ("distance_m",), max_dial_ticks=30)
    heap = search(graph, workspace, np.array([0]), np.array([0.0]), 3)
    heap_order = heap.settled.copy()
    heap_parents = heap.predecessor_node.copy()
    heap_secondary = heap.secondary.copy()
    dial = search(
        graph,
        workspace,
        np.array([0]),
        np.array([0.0]),
        3,
        queue="dial",
        resolution_s=0.1,
    )
    np.testing.assert_array_equal(dial.settled, heap_order)
    np.testing.assert_array_equal(dial.predecessor_node, heap_parents)
    np.testing.assert_array_equal(dial.secondary, heap_secondary)


def test_dial_rounding_error_is_bounded_by_path_lengths():
    graph = _random_graph(24)
    graph.weights["time_s"][:] += np.float32(0.037)
    workspace = SearchWorkspace(graph, (), max_dial_ticks=5000)
    sources, offsets = np.array([0]), np.array([0.0])
    dial = search(
        graph, workspace, sources, offsets, 500, queue="dial", resolution_s=0.1
    )
    dial_times = dial.time_s.copy()
    dial_parents = dial.predecessor_node.copy()
    heap = search(graph, workspace, sources, offsets, 500)
    heap_times = heap.time_s
    heap_parents = heap.predecessor_node

    def path_length(node, parents):
        length = 0
        while parents[node] >= 0:
            length += 1
            node = parents[node]
        return length

    for node in heap.settled:
        bound = 0.05 * max(
            path_length(node, dial_parents), path_length(node, heap_parents)
        )
        assert abs(dial_times[node] - heap_times[node]) <= bound + 1e-10


@pytest.mark.pilot
def test_synthetic_million_node_benchmark():
    n = 1_000_000
    sources = np.arange(n - 1, dtype=np.int64)
    graph = csr_from_indexed_edges(
        "foot",
        np.arange(n, dtype=np.int64),
        sources,
        sources + 1,
        {"time_s": np.ones(n - 1, dtype=np.float32)},
        reference_mass_kg=74,
        bike_mass_kg=15,
    )
    resolution = load_search_config(
        Path(__file__).resolve().parents[3] / "config" / "search.yaml"
    ).dial_resolution_s
    cutoff = 12_000.0
    workspace = SearchWorkspace(graph, (), max_dial_ticks=int(cutoff / resolution))
    origin, offset = np.array([0]), np.array([0.0])
    timings = {}
    for queue in ("heap", "dial"):
        search(
            graph,
            workspace,
            origin,
            offset,
            cutoff,
            queue=queue,
            resolution_s=resolution,
        )
        started = time.perf_counter()
        result = search(
            graph,
            workspace,
            origin,
            offset,
            cutoff,
            queue=queue,
            resolution_s=resolution,
        )
        elapsed = time.perf_counter() - started
        timings[queue] = elapsed
        print(
            f"{queue}: {result.count / elapsed:,.0f} settled nodes/s "
            f"({result.count:,} nodes)"
        )
    print(f"Faster queue: {min(timings, key=timings.get)}")
