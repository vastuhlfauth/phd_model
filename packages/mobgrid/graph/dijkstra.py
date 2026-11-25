"""Reusable bounded multi-source shortest-path searches (sections 10.2, 14.7)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt
from numba import njit

from mobgrid.graph.csr import CSRGraph
from mobgrid.od.products import SearchProducts, record_settled


@njit(cache=True)
def _heap_push(keys, nodes, sequences, size, key, node, sequence):
    position = size
    while position:
        parent = (position - 1) // 2
        if keys[parent] < key or (
            keys[parent] == key and sequences[parent] <= sequence
        ):
            break
        keys[position] = keys[parent]
        nodes[position] = nodes[parent]
        sequences[position] = sequences[parent]
        position = parent
    keys[position] = key
    nodes[position] = node
    sequences[position] = sequence
    return size + 1


@njit(cache=True)
def _heap_pop(keys, nodes, sequences, size):
    key, node = keys[0], nodes[0]
    size -= 1
    if size:
        last_key, last_node, last_sequence = keys[size], nodes[size], sequences[size]
        position = 0
        while position * 2 + 1 < size:
            child = position * 2 + 1
            right = child + 1
            if right < size and (
                keys[right] < keys[child]
                or (keys[right] == keys[child] and sequences[right] < sequences[child])
            ):
                child = right
            if keys[child] > last_key or (
                keys[child] == last_key and sequences[child] >= last_sequence
            ):
                break
            keys[position] = keys[child]
            nodes[position] = nodes[child]
            sequences[position] = sequences[child]
            position = child
        keys[position] = last_key
        nodes[position] = last_node
        sequences[position] = last_sequence
    return key, node, size


@njit(cache=True)
def _run(
    indptr,
    indices,
    reverse_edge_indices,
    reverse,
    weights,
    secondary_weights,
    sources,
    offsets,
    source_secondary,
    cutoff,
    dial,
    resolution,
    generation,
    stamps,
    settled_stamps,
    source_stamps,
    times,
    secondary,
    predecessor_node,
    predecessor_edge,
    settled,
    heap_keys,
    heap_nodes,
    heap_sequences,
    bucket_heads,
    bucket_tails,
    bucket_next,
    product_arrays,
    distance_index,
    energy_index,
):
    size = 0
    entries = 0
    for i in range(len(sources)):
        node = sources[i]
        time = offsets[i]
        if dial:
            time = np.rint(time / resolution)
        if time > cutoff:
            continue
        if stamps[node] != generation or time < times[node]:
            stamps[node] = generation
            times[node] = time
            predecessor_node[node] = -1
            predecessor_edge[node] = -1
            for j in range(secondary.shape[1]):
                secondary[node, j] = (
                    source_secondary[i, j] if len(source_secondary) else 0.0
                )
    for i in range(len(sources)):
        node = sources[i]
        if stamps[node] == generation and source_stamps[node] != generation:
            source_stamps[node] = generation
            time = times[node]
            if dial:
                tick = int(time)
                heap_nodes[entries] = node
                heap_keys[entries] = time
                bucket_next[entries] = -1
                if bucket_heads[tick] == -1:
                    bucket_heads[tick] = entries
                else:
                    bucket_next[bucket_tails[tick]] = entries
                bucket_tails[tick] = entries
                entries += 1
            else:
                size = _heap_push(
                    heap_keys, heap_nodes, heap_sequences, size, time, node, entries
                )
                entries += 1
    count = 0
    tick = 0
    while True:
        if dial:
            while tick <= cutoff and bucket_heads[tick] == -1:
                tick += 1
            if tick > cutoff:
                break
            entry = bucket_heads[tick]
            bucket_heads[tick] = bucket_next[entry]
            if bucket_heads[tick] == -1:
                bucket_tails[tick] = -1
            time, node = heap_keys[entry], heap_nodes[entry]
        else:
            if size == 0:
                break
            time, node, size = _heap_pop(heap_keys, heap_nodes, heap_sequences, size)
        if (
            stamps[node] != generation
            or times[node] != time
            or settled_stamps[node] == generation
        ):
            continue
        settled_stamps[node] = generation
        settled[count] = node
        count += 1
        if product_arrays is not None:
            record_settled(
                node,
                time * resolution,
                secondary[node, distance_index],
                secondary[node, energy_index],
                product_arrays,
            )
        for position in range(indptr[node], indptr[node + 1]):
            target = indices[position]
            edge = reverse_edge_indices[position] if reverse else position
            edge_time = weights[edge]
            if dial:
                edge_time = np.rint(edge_time / resolution)
            candidate = time + edge_time
            if candidate <= cutoff and (
                stamps[target] != generation or candidate < times[target]
            ):
                stamps[target] = generation
                times[target] = candidate
                predecessor_node[target] = node
                predecessor_edge[target] = edge
                for j in range(secondary.shape[1]):
                    secondary[target, j] = (
                        secondary[node, j] + secondary_weights[edge, j]
                    )
                if dial:
                    bucket = int(candidate)
                    heap_nodes[entries] = target
                    heap_keys[entries] = candidate
                    bucket_next[entries] = -1
                    if bucket_heads[bucket] == -1:
                        bucket_heads[bucket] = entries
                    else:
                        bucket_next[bucket_tails[bucket]] = entries
                    bucket_tails[bucket] = entries
                    entries += 1
                else:
                    size = _heap_push(
                        heap_keys,
                        heap_nodes,
                        heap_sequences,
                        size,
                        candidate,
                        target,
                        entries,
                    )
                    entries += 1
    return count


class SearchWorkspace:
    """Preallocate search arrays; Dial's cutoff cannot exceed max_dial_ticks."""

    def __init__(
        self,
        graph: CSRGraph,
        secondary_names: tuple[str, ...],
        *,
        max_dial_ticks: int = 0,
    ) -> None:
        if max_dial_ticks < 0:
            raise ValueError("max_dial_ticks must be non-negative")
        n = len(graph.node_ids)
        capacity = len(graph.indices) + n
        self.graph = graph
        self.secondary_names = secondary_names
        edge_times = graph.weights["time_s"]
        if np.any(~np.isfinite(edge_times)) or np.any(edge_times < 0):
            raise ValueError("edge times must be finite and non-negative")
        self.secondary_weights = (
            np.column_stack([graph.weights[name] for name in secondary_names])
            if secondary_names
            else np.empty((len(graph.indices), 0), dtype=np.float32)
        )
        if not np.isfinite(self.secondary_weights).all():
            raise ValueError("secondary weights must be finite")
        self.nonnegative_secondary = np.all(self.secondary_weights >= 0, axis=0)
        self.zero_source_secondary = np.empty(
            (0, len(secondary_names)), dtype=np.float64
        )
        self.stamps = np.zeros(n, dtype=np.int64)
        self.settled_stamps = np.zeros(n, dtype=np.int64)
        self.source_stamps = np.zeros(n, dtype=np.int64)
        self.times = np.empty(n, dtype=np.float64)
        self.secondary = np.empty((n, len(secondary_names)), dtype=np.float64)
        self.predecessor_node = np.empty(n, dtype=np.int32)
        self.predecessor_edge = np.empty(n, dtype=np.int32)
        self.settle_order = np.empty(n, dtype=np.int32)
        self.heap_keys = np.empty(capacity, dtype=np.float64)
        self.heap_nodes = np.empty(capacity, dtype=np.int32)
        self.heap_sequences = np.empty(capacity, dtype=np.int64)
        self.bucket_next = np.empty(capacity, dtype=np.int64)
        self.bucket_heads = np.full(max_dial_ticks + 1, -1, dtype=np.int64)
        self.bucket_tails = np.full(max_dial_ticks + 1, -1, dtype=np.int64)
        self.generation = 0


@dataclass(frozen=True)
class SearchResult:
    """Search labels, invalidated when reused; unvisited labels are masked."""

    workspace: SearchWorkspace
    generation: int
    count: int
    scale: float

    def _check_current(self) -> None:
        if self.workspace.generation != self.generation:
            raise ValueError("search result was invalidated by workspace reuse")

    @property
    def time_s(self) -> npt.NDArray[np.float64]:
        self._check_current()
        return np.where(
            self.workspace.stamps == self.generation,
            self.workspace.times * self.scale,
            np.inf,
        )

    @property
    def settled(self) -> npt.NDArray[np.int32]:
        self._check_current()
        return self.workspace.settle_order[: self.count]

    @property
    def predecessor_node(self) -> npt.NDArray[np.int32]:
        self._check_current()
        return np.where(
            self.workspace.stamps == self.generation,
            self.workspace.predecessor_node,
            np.int32(-1),
        )

    @property
    def predecessor_edge(self) -> npt.NDArray[np.int32]:
        self._check_current()
        return np.where(
            self.workspace.stamps == self.generation,
            self.workspace.predecessor_edge,
            np.int32(-1),
        )

    @property
    def secondary(self) -> npt.NDArray[np.float64]:
        self._check_current()
        return np.where(
            (self.workspace.stamps == self.generation)[:, None],
            self.workspace.secondary,
            np.nan,
        )


def search(
    graph: CSRGraph,
    workspace: SearchWorkspace,
    sources: npt.NDArray[np.integer],
    offsets_s: npt.NDArray[np.floating],
    cutoff_s: float,
    *,
    queue: Literal["heap", "dial"] = "heap",
    resolution_s: float | None = None,
    source_secondary: npt.NDArray[np.floating] | None = None,
    products: SearchProducts | None = None,
    reverse: bool = False,
) -> SearchResult:
    """Minimise seconds up to cutoff; reverse predecessors use forward edge ids."""
    sources = np.asarray(sources)
    offsets_s = np.asarray(offsets_s, dtype=np.float64)
    if workspace.graph is not graph:
        raise ValueError("workspace belongs to a different graph")
    if (
        sources.ndim != 1
        or not np.issubdtype(sources.dtype, np.integer)
        or offsets_s.shape != sources.shape
        or np.any(sources < 0)
        or np.any(sources >= len(graph.node_ids))
        or np.any(~np.isfinite(offsets_s))
        or np.any(offsets_s < 0)
        or not np.isfinite(cutoff_s)
        or cutoff_s < 0
    ):
        raise ValueError("invalid sources, offsets or cutoff")
    times = graph.weights["time_s"]
    if queue not in ("heap", "dial"):
        raise ValueError("queue must be heap or dial")
    if source_secondary is None:
        source_secondary = workspace.zero_source_secondary
    else:
        source_secondary = np.asarray(source_secondary, dtype=np.float64)
        if (
            source_secondary.shape != (len(sources), len(workspace.secondary_names))
            or not np.isfinite(source_secondary).all()
        ):
            raise ValueError("invalid source secondary offsets")
    dial = queue == "dial"
    scale = 1.0
    cutoff = cutoff_s
    if dial:
        if resolution_s is None or not np.isfinite(resolution_s) or resolution_s <= 0:
            raise ValueError("Dial requires a finite positive resolution in seconds")
        scale = resolution_s
        cutoff = np.floor(np.nextafter(cutoff_s / scale, np.inf))
        if cutoff >= len(workspace.bucket_heads):
            raise ValueError("Dial cutoff exceeds workspace bucket capacity")
    product_arrays = None
    distance_index = -1
    energy_index = -1
    if products is not None:
        if len(products.od_flags) != len(graph.node_ids):
            raise ValueError("destination arrays must align with graph nodes")
        try:
            distance_index = workspace.secondary_names.index("distance_m")
            energy_index = workspace.secondary_names.index("energy_kj")
        except ValueError as exc:
            raise ValueError("products require distance_m and energy_kj") from exc
        if (
            not workspace.nonnegative_secondary[distance_index]
            or not workspace.nonnegative_secondary[energy_index]
            or (
                len(source_secondary)
                and (
                    np.any(source_secondary[:, distance_index] < 0)
                    or np.any(source_secondary[:, energy_index] < 0)
                )
            )
        ):
            raise ValueError("product distance and energy must be non-negative")
        products.reset()
        product_arrays = products.arrays
    if workspace.generation == np.iinfo(np.int64).max:
        workspace.stamps.fill(0)
        workspace.settled_stamps.fill(0)
        workspace.source_stamps.fill(0)
        workspace.generation = 0
    workspace.generation += 1
    count = _run(
        graph.reverse_indptr if reverse else graph.indptr,
        graph.reverse_indices if reverse else graph.indices,
        graph.reverse_edge_indices,
        reverse,
        times,
        workspace.secondary_weights,
        sources,
        offsets_s,
        source_secondary,
        cutoff,
        dial,
        scale,
        workspace.generation,
        workspace.stamps,
        workspace.settled_stamps,
        workspace.source_stamps,
        workspace.times,
        workspace.secondary,
        workspace.predecessor_node,
        workspace.predecessor_edge,
        workspace.settle_order,
        workspace.heap_keys,
        workspace.heap_nodes,
        workspace.heap_sequences,
        workspace.bucket_heads,
        workspace.bucket_tails,
        workspace.bucket_next,
        product_arrays,
        distance_index,
        energy_index,
    )
    if products is not None and products._overflow[0]:
        raise ValueError("product bin capacity is insufficient")
    return SearchResult(workspace, workspace.generation, count, scale)


@njit(cache=True)
def _split_times(order, parents, edges, times, class_ids, bucket_ids, classes, buckets):
    for node in order:
        parent = parents[node]
        if parent < 0:
            continue
        for i in range(classes.shape[1]):
            classes[node, i] = classes[parent, i]
        for i in range(buckets.shape[1]):
            buckets[node, i] = buckets[parent, i]
        edge = edges[node]
        classes[node, class_ids[edge]] += times[edge]
        buckets[node, bucket_ids[edge]] += times[edge]


def path_time_splits(
    graph: CSRGraph, result: SearchResult, destinations: npt.NDArray[np.integer]
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """Return original-edge class and bucket path seconds for recorded nodes."""
    workspace = result.workspace
    destinations = np.asarray(destinations)
    if (
        workspace.graph is not graph
        or workspace.generation != result.generation
        or destinations.ndim != 1
        or not np.issubdtype(destinations.dtype, np.integer)
        or np.any(destinations < 0)
        or np.any(destinations >= len(graph.node_ids))
        or np.any(workspace.settled_stamps[destinations] != result.generation)
    ):
        raise ValueError("destinations must be settled in the current search")
    classes = np.zeros((len(graph.node_ids), len(graph.road_classes)), dtype=np.float64)
    buckets = np.zeros(
        (len(graph.node_ids), len(graph.speed_buckets)), dtype=np.float64
    )
    _split_times(
        result.settled,
        workspace.predecessor_node,
        workspace.predecessor_edge,
        graph.weights["time_s"],
        graph.road_class_ids,
        graph.speed_bucket_ids,
        classes,
        buckets,
    )
    return classes[destinations], buckets[destinations]
