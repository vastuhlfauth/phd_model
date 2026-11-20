"""Grouping comparisons of daily travel time, section 9.9."""

import logging
from dataclasses import dataclass
from itertools import product
from typing import Self

import numpy as np
from pydantic import BaseModel, ConfigDict, model_validator

LOGGER = logging.getLogger(__name__)


class OrderedDimension(BaseModel):
    """Ordered levels and preferred neighbouring pairs."""

    model_config = ConfigDict(extra="forbid")

    levels: list[str]
    preferred: list[tuple[str, str]]

    @model_validator(mode="after")
    def validate_neighbours(self) -> Self:
        if len(set(self.levels)) != len(self.levels) or not self.levels:
            raise ValueError("Ordered dimension levels must be unique and nonempty")
        for left, right in self.preferred:
            if left not in self.levels or right not in self.levels:
                raise ValueError("Preferred neighbour is not a configured level")
            if abs(self.levels.index(left) - self.levels.index(right)) != 1:
                raise ValueError("Preferred neighbours must be adjacent")
        return self


class MergeConfig(BaseModel):
    """Configured ordered dimensions; unlisted dimensions never merge."""

    model_config = ConfigDict(extra="forbid")

    dimensions: dict[str, OrderedDimension]


@dataclass(frozen=True)
class CellSample:
    """Daily minutes, survey weights, cell and parent labels, section 9.9."""

    values: np.ndarray
    weights: np.ndarray
    cells: np.ndarray
    parents: np.ndarray


@dataclass(frozen=True)
class FixedDistribution:
    """2008 minutes reweighted to 2019 cells and fallback weight share."""

    values: np.ndarray
    weights: np.ndarray
    fallback_share: float


def fixed_cell_distribution(a: CellSample, b: CellSample) -> FixedDistribution:
    """Build the 2019-share mixture of 2008 daily minutes, section 9.9."""
    for sample in (a, b):
        if not len(sample.values) or any(
            len(column) != len(sample.values)
            for column in (sample.weights, sample.cells, sample.parents)
        ):
            raise ValueError("Cell sample arrays must be nonempty and aligned")
        if (
            not np.all(np.isfinite(sample.values))
            or not np.all(np.isfinite(sample.weights))
            or np.any(sample.weights < 0)
            or sample.weights.sum() <= 0
        ):
            raise ValueError("Cell samples require finite values and positive weight")
        for cell in np.unique(sample.cells):
            if len(np.unique(sample.parents[sample.cells == cell])) != 1:
                raise ValueError(f"Cell {cell!r} has more than one parent")
    weights = np.zeros(len(a.values), dtype=float)
    fallback = 0.0
    total_b = b.weights.sum()
    for cell in np.unique(b.cells):
        target = b.cells == cell
        share = float(b.weights[target].sum() / total_b)
        if share == 0:
            continue
        source = a.cells == cell
        parent = b.parents[target][0]
        if source.any() and np.any(a.parents[source] != parent):
            raise ValueError(f"Cell {cell!r} has inconsistent parents across years")
        if not source.any():
            source = a.parents == parent
            fallback += share
        elif a.weights[source].sum() <= 0:
            raise ValueError(f"No 2008 bootstrap support for cell {cell!r}")
        source_weight = a.weights[source].sum()
        if source_weight <= 0:
            raise ValueError(f"No 2008 support for cell {cell!r} or parent {parent!r}")
        weights[source] += share * a.weights[source] / source_weight
    return FixedDistribution(a.values, weights, fallback)


def merge_cells(
    cells_a: np.ndarray,
    people_a: np.ndarray,
    cells_b: np.ndarray,
    people_b: np.ndarray,
    *,
    dimensions: tuple[str, ...],
    config: MergeConfig,
    minimum_n: int,
) -> dict[tuple[str, ...], tuple[str, ...]]:
    """Fix ordered-secondary merges on full-sample respondent counts, section 9.9."""
    for cells, people in ((cells_a, people_a), (cells_b, people_b)):
        if (
            cells.ndim != 2
            or cells.shape[1] != len(dimensions)
            or len(cells) != len(people)
        ):
            raise ValueError("Cells and respondent identifiers must match dimensions")
    if minimum_n <= 0 or not len(dimensions) or not len(cells_a) or not len(cells_b):
        raise ValueError(
            "A positive threshold and nonempty survey samples are required"
        )
    original = [
        tuple(row)
        for row in np.unique(np.concatenate((cells_a, cells_b)).astype(str), axis=0)
    ]
    members = {cell: [set(), set()] for cell in original}
    for year, (cells, people) in enumerate(((cells_a, people_a), (cells_b, people_b))):
        for cell in original:
            mask = np.all(cells.astype(str) == cell, axis=1)
            members[cell][year].update(np.unique(people[mask]).astype(str))
    clusters = {cell: frozenset([cell]) for cell in original}

    def counts(cluster: frozenset[tuple[str, ...]]) -> int:
        return min(
            len(set().union(*(members[cell][year] for cell in cluster)))
            for year in (0, 1)
        )

    while True:
        groups = set(clusters.values())
        choice = None
        for cluster in sorted(groups, key=lambda group: (counts(group), sorted(group))):
            if counts(cluster) >= minimum_n:
                break
            for axis, dimension in enumerate(dimensions):
                if axis == 0 or dimension not in config.dimensions:
                    continue
                rule = config.dimensions[dimension]
                candidates = []
                for other in groups - {cluster}:
                    projections = (
                        {
                            tuple(row[i] for i in range(len(dimensions)) if i != axis)
                            for row in group
                        }
                        for group in (cluster, other)
                    )
                    left_projection, right_projection = projections
                    if left_projection != right_projection:
                        continue
                    left = {row[axis] for row in cluster}
                    right = {row[axis] for row in other}
                    pairs = [
                        (a, b)
                        for a, b in product(left, right)
                        if a in rule.levels
                        and b in rule.levels
                        and abs(rule.levels.index(a) - rule.levels.index(b)) == 1
                    ]
                    if not pairs:
                        continue
                    preferred = min(
                        (
                            i
                            for i, pair in enumerate(rule.preferred)
                            if pair in pairs or pair[::-1] in pairs
                        ),
                        default=len(rule.preferred),
                    )
                    candidates.append((preferred, -counts(other), sorted(other), other))
                if candidates:
                    other = min(candidates, key=lambda item: item[:3])[3]
                    choice = cluster | other
                    break
            if choice is not None:
                break
        if choice is None:
            break
        for cell in choice:
            clusters[cell] = choice
    result = {}
    for cell, cluster in clusters.items():
        result[cell] = tuple(
            "+".join(sorted({row[i] for row in cluster}))
            for i in range(len(dimensions))
        )
    return result


def weighted_eta_squared(
    values: np.ndarray, weights: np.ndarray, cells: np.ndarray
) -> float:
    """Weighted between-cell variance share for daily minutes, section 9.9."""
    if len(values) != len(weights) or len(values) != len(cells) or not len(values):
        raise ValueError("Values, weights and cell labels must be nonempty and aligned")
    if (
        not np.all(np.isfinite(values))
        or not np.all(np.isfinite(weights))
        or np.any(weights < 0)
    ):
        raise ValueError("Values and nonnegative weights must be finite")
    if weights.sum() <= 0:
        raise ValueError("Total weight must be positive")
    _, codes = np.unique(cells, return_inverse=True)
    cell_weight = np.bincount(codes, weights=weights)
    cell_sum = np.bincount(codes, weights=weights * values)
    mean = np.sum(weights * values) / np.sum(weights)
    total = np.sum(weights * (values - mean) ** 2)
    if total == 0:
        LOGGER.warning("Weighted eta-squared is undefined for zero total variance")
        return float("nan")
    means = np.divide(
        cell_sum, cell_weight, out=np.zeros_like(cell_sum), where=cell_weight > 0
    )
    return float(np.sum(cell_weight * (means - mean) ** 2) / total)


if __name__ == "__main__":
    raise NotImplementedError("The grouping report and CLI have not been implemented")
