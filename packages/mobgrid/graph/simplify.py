"""Largest-component filtering and degree-2 contraction for section 14.7."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
from numba import njit

from mobgrid.graph.csr import CSRGraph, csr_from_indexed_edges
from mobgrid.osm.edges import _strongly_connected_components

BoolArray = npt.NDArray[np.bool_]
IntArray = npt.NDArray[np.int64]


def _sources(graph: CSRGraph) -> IntArray:
    return np.repeat(
        np.arange(len(graph.node_ids), dtype=np.int64),
        np.diff(graph.indptr),
    )


def _reverse_csr(graph: CSRGraph) -> tuple[IntArray, IntArray]:
    return (
        graph.reverse_indptr,
        graph.reverse_indices.astype(np.int64, copy=False),
    )


def largest_strong_component(graph: CSRGraph) -> CSRGraph:
    """Keep the largest SCC of the mode graph, with deterministic tie handling."""
    node_count = len(graph.node_ids)
    if node_count == 0:
        return graph
    reverse_indptr, reverse_indices = _reverse_csr(graph)
    labels, sizes, component_count = _strongly_connected_components(
        graph.indptr,
        graph.indices.astype(np.int64, copy=False),
        reverse_indptr,
        reverse_indices,
    )
    if component_count == 0:
        return graph
    largest_label = int(np.argmax(sizes[:component_count]))
    keep = labels == largest_label
    if keep.all():
        return graph

    kept_indices = np.flatnonzero(keep)
    old_to_new = np.full(node_count, -1, dtype=np.int64)
    old_to_new[kept_indices] = np.arange(len(kept_indices), dtype=np.int64)
    sources = _sources(graph)
    targets = graph.indices.astype(np.int64, copy=False)
    edge_keep = keep[sources] & keep[targets]
    weights = {name: values[edge_keep] for name, values in graph.weights.items()}
    return csr_from_indexed_edges(
        graph.mode,
        graph.node_ids[kept_indices],
        old_to_new[sources[edge_keep]],
        old_to_new[targets[edge_keep]],
        weights,
        reference_mass_kg=graph.reference_mass_kg,
        bike_mass_kg=graph.bike_mass_kg,
    )


def weak_node_degrees(graph: CSRGraph) -> IntArray:
    """Return unique-neighbour degrees without counting parallel arcs twice."""
    sources = _sources(graph)
    targets = graph.indices.astype(np.int64, copy=False)
    if not len(sources):
        return np.zeros(len(graph.node_ids), dtype=np.int64)
    low = np.minimum(sources, targets)
    high = np.maximum(sources, targets)
    pairs = np.unique(np.column_stack((low, high)), axis=0)
    return np.bincount(
        np.concatenate((pairs[:, 0], pairs[:, 1])),
        minlength=len(graph.node_ids),
    ).astype(np.int64, copy=False)


@njit(cache=True)
def _contract_edges(
    indptr: IntArray,
    indices: IntArray,
    weights: np.ndarray,
    eligible: BoolArray,
    neighbours: IntArray,
    neighbour_pairs: IntArray,
    arc_lookup: IntArray,
) -> tuple[IntArray, IntArray, np.ndarray, int, bool]:
    edge_count = len(indices)
    node_count = len(indptr) - 1
    weight_count = weights.shape[1]
    out_sources = np.empty(edge_count, dtype=np.int64)
    out_targets = np.empty(edge_count, dtype=np.int64)
    out_weights = np.empty((edge_count, weight_count), dtype=np.float64)
    out_count = 0

    for source in range(node_count):
        if eligible[source]:
            continue
        for edge_position in range(indptr[source], indptr[source + 1]):
            target = indices[edge_position]
            for weight_index in range(weight_count):
                out_weights[out_count, weight_index] = weights[
                    edge_position, weight_index
                ]
            previous = source
            traversed = 0
            while eligible[target]:
                slot = 0
                if neighbours[target, 0] == previous:
                    slot = 1
                next_node = neighbours[target, slot]
                pair = neighbour_pairs[target, slot]
                direction = 0
                if target > next_node:
                    direction = 1
                next_edge = arc_lookup[pair, direction]
                if next_edge < 0:
                    return out_sources, out_targets, out_weights, out_count, True
                for weight_index in range(weight_count):
                    out_weights[out_count, weight_index] += weights[
                        next_edge, weight_index
                    ]
                previous = target
                target = next_node
                traversed += 1
                if traversed > node_count:
                    return out_sources, out_targets, out_weights, out_count, True
            out_sources[out_count] = source
            out_targets[out_count] = target
            out_count += 1
    return out_sources, out_targets, out_weights, out_count, False


def _contractible_nodes(
    graph: CSRGraph,
    kept_nodes: BoolArray,
) -> tuple[BoolArray, IntArray, IntArray, IntArray]:
    node_count = len(graph.node_ids)
    sources = _sources(graph)
    targets = graph.indices.astype(np.int64, copy=False)
    edge_count = len(sources)
    if not edge_count:
        return (
            np.zeros(node_count, dtype=np.bool_),
            np.empty((0, 2), dtype=np.int64),
            (np.empty((0, 2), dtype=np.int64)),
            np.empty((0, 2), dtype=np.int64),
        )

    low = np.minimum(sources, targets)
    high = np.maximum(sources, targets)
    pairs, edge_pair = np.unique(
        np.column_stack((low, high)), axis=0, return_inverse=True
    )
    pair_count = len(pairs)
    edge_direction = (sources > targets).astype(np.int64)
    direction_key = edge_pair * 2 + edge_direction
    arc_counts = np.bincount(direction_key, minlength=pair_count * 2).reshape(
        (pair_count, 2)
    )
    arc_lookup = np.full((pair_count, 2), -1, dtype=np.int64)
    arc_lookup[edge_pair, edge_direction] = np.arange(edge_count, dtype=np.int64)

    pair_ids = np.arange(pair_count, dtype=np.int64)
    incident_nodes = np.concatenate((pairs[:, 0], pairs[:, 1]))
    incident_pairs = np.concatenate((pair_ids, pair_ids))
    degree = np.bincount(incident_nodes, minlength=node_count)
    incident_order = np.argsort(incident_nodes, kind="stable")
    sorted_nodes = incident_nodes[incident_order]
    sorted_pairs = incident_pairs[incident_order]
    starts = np.cumsum(degree) - degree
    slots = np.arange(len(sorted_nodes)) - np.repeat(starts, degree)
    use = slots < 2
    sorted_nodes = sorted_nodes[use]
    sorted_pairs = sorted_pairs[use]
    slots = slots[use]

    neighbours = np.full((node_count, 2), -1, dtype=np.int64)
    neighbour_pairs = np.full((node_count, 2), -1, dtype=np.int64)
    neighbour_masks = np.zeros((node_count, 2), dtype=np.int8)
    pair_lows = pairs[sorted_pairs, 0]
    pair_highs = pairs[sorted_pairs, 1]
    is_low = sorted_nodes == pair_lows
    neighbours[sorted_nodes, slots] = np.where(is_low, pair_highs, pair_lows)
    neighbour_pairs[sorted_nodes, slots] = sorted_pairs
    forward_counts = arc_counts[:, 0]
    reverse_counts = arc_counts[:, 1]
    incoming = np.where(
        is_low, reverse_counts[sorted_pairs], forward_counts[sorted_pairs]
    )
    outgoing = np.where(
        is_low, forward_counts[sorted_pairs], reverse_counts[sorted_pairs]
    )
    neighbour_masks[sorted_nodes, slots] = (incoming + 2 * outgoing).astype(np.int8)

    bad_pairs = np.any(arc_counts > 1, axis=1) | (pairs[:, 0] == pairs[:, 1])
    bad_incident = (
        np.bincount(
            incident_nodes,
            weights=bad_pairs[incident_pairs].astype(np.int8),
            minlength=node_count,
        )
        > 0
    )
    first = neighbour_masks[:, 0]
    second = neighbour_masks[:, 1]
    same_bidirectional = (first == 3) & (second == 3)
    opposite_one_way = ((first == 1) & (second == 2)) | ((first == 2) & (second == 1))
    eligible = (
        (degree == 2)
        & ~kept_nodes
        & ~bad_incident
        & (same_bidirectional | opposite_one_way)
    )
    return eligible, neighbours, neighbour_pairs, arc_lookup


def contract_degree_two(graph: CSRGraph, kept_nodes: BoolArray) -> CSRGraph:
    """Contract accessible degree-2 chains, summing every weight on each arc."""
    kept = np.asarray(kept_nodes)
    if kept.dtype != np.bool_ or kept.shape != (len(graph.node_ids),):
        raise ValueError("kept_nodes must be a boolean array aligned to node_ids")
    eligible, neighbours, neighbour_pairs, arc_lookup = _contractible_nodes(
        graph,
        kept,
    )
    if not eligible.any() or eligible.all():
        return graph

    weight_names = tuple(graph.weights)
    edge_weights = np.column_stack(
        [graph.weights[name] for name in weight_names]
    ).astype(np.float32, copy=False)
    out_sources, out_targets, out_weights, out_count, failed = _contract_edges(
        graph.indptr,
        graph.indices.astype(np.int64, copy=False),
        edge_weights,
        eligible,
        neighbours,
        neighbour_pairs,
        arc_lookup,
    )
    if failed:
        raise RuntimeError("degree-2 chain traversal found an invalid continuation")

    boundary_nodes = np.flatnonzero(~eligible)
    old_to_new = np.full(len(graph.node_ids), -1, dtype=np.int64)
    old_to_new[boundary_nodes] = np.arange(len(boundary_nodes), dtype=np.int64)
    sources = old_to_new[out_sources[:out_count]]
    targets = old_to_new[out_targets[:out_count]]
    weights = {
        name: out_weights[:out_count, index].astype(np.float32)
        for index, name in enumerate(weight_names)
    }
    return csr_from_indexed_edges(
        graph.mode,
        graph.node_ids[boundary_nodes],
        sources,
        targets,
        weights,
        reference_mass_kg=graph.reference_mass_kg,
        bike_mass_kg=graph.bike_mass_kg,
    )
