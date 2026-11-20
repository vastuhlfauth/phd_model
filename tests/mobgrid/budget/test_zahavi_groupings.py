"""Synthetic tests for the grouping report, section 9.9."""

import numpy as np
import pytest
import yaml
from mobgrid.budget import zahavi_groupings as groupings
from mobgrid.budget import zahavi_modes as modes


@pytest.fixture
def merge_config():
    with open("config/zahavi_merges.yaml", encoding="utf-8") as stream:
        return groupings.MergeConfig.model_validate(yaml.safe_load(stream))


def test_ordered_merges_are_fixed_and_preserve_nominal_levels(merge_config):
    a = np.array(
        [["employed", "dense"]] * 3
        + [["employed", "intermediate"]] * 2
        + [["retired", "dense"]] * 2
    )
    b = np.array(
        [["employed", "dense"]] * 2
        + [["employed", "intermediate"]] * 3
        + [["retired", "dense"]] * 2
    )
    ids_a = np.array([f"a{i}" for i in range(len(a))])
    ids_b = np.array([f"b{i}" for i in range(len(b))])
    mapping = groupings.merge_cells(
        a,
        ids_a,
        b,
        ids_b,
        dimensions=("population", "density"),
        config=merge_config,
        minimum_n=3,
    )
    assert mapping[("employed", "dense")] == mapping[("employed", "intermediate")]
    assert mapping[("retired", "dense")] == ("retired", "dense")
    for cell, merged in mapping.items():
        assert cell[0] == merged[0]
    for multipliers in (np.ones(len(a)), np.arange(len(a)) % 2):
        mapped = [mapping[tuple(row)] for row in a[multipliers > 0]]
        assert [cell[0] for cell in mapped] == list(a[multipliers > 0, 0])
        assert mapping == groupings.merge_cells(
            a,
            ids_a,
            b,
            ids_b,
            dimensions=("population", "density"),
            config=merge_config,
            minimum_n=3,
        )


def test_merge_configuration_only_names_existing_adjacent_neighbours(merge_config):
    for rule in merge_config.dimensions.values():
        for left, right in rule.preferred:
            assert left in rule.levels and right in rule.levels
            assert abs(rule.levels.index(left) - rule.levels.index(right)) == 1


def test_eta_squared_extremes():
    assert groupings.weighted_eta_squared(
        np.array([1.0, 3.0]), np.ones(2), np.array([0, 0])
    ) == pytest.approx(0.0)
    assert groupings.weighted_eta_squared(
        np.array([1.0, 1.0, 3.0, 3.0]), np.ones(4), np.array([0, 0, 1, 1])
    ) == pytest.approx(1.0)


def test_fixed_cell_distribution_reproduces_unchanged_cell_distributions():
    a = groupings.CellSample(
        values=np.array([10.0, 20.0, 50.0, 60.0]),
        weights=np.ones(4),
        cells=np.array(["a", "a", "b", "b"]),
        parents=np.array(["all"] * 4),
    )
    b = groupings.CellSample(
        values=a.values,
        weights=np.array([3.0, 3.0, 1.0, 1.0]),
        cells=a.cells,
        parents=a.parents,
    )
    prediction = groupings.fixed_cell_distribution(a, b)
    assert prediction.weights == pytest.approx(b.weights / b.weights.sum())
    assert prediction.fallback_share == 0
    assert np.average(prediction.values, weights=prediction.weights) == pytest.approx(
        np.average(b.values, weights=b.weights)
    )
    assert modes.weighted_ks(
        modes.Observations(prediction.values, prediction.weights, np.array([])),
        modes.Observations(b.values, b.weights, np.array([])),
    ) == pytest.approx(0)


def test_absent_2008_cell_uses_parent_distribution_and_reports_share():
    a = groupings.CellSample(
        values=np.array([10.0, 30.0, 100.0]),
        weights=np.array([1.0, 3.0, 1.0]),
        cells=np.array(["mode_a", "mode_b", "other"]),
        parents=np.array(["mode", "mode", "other"]),
    )
    b = groupings.CellSample(
        values=np.array([50.0, 100.0]),
        weights=np.array([1.0, 1.0]),
        cells=np.array(["mode_missing", "other"]),
        parents=np.array(["mode", "other"]),
    )
    prediction = groupings.fixed_cell_distribution(a, b)
    assert prediction.weights == pytest.approx([0.125, 0.375, 0.5])
    assert prediction.fallback_share == pytest.approx(0.5)


def test_empty_bootstrap_cell_does_not_change_the_full_sample_fallback():
    a = groupings.CellSample(
        values=np.array([10.0, 30.0]),
        weights=np.array([0.0, 1.0]),
        cells=np.array(["a", "b"]),
        parents=np.array(["parent", "parent"]),
    )
    b = groupings.CellSample(
        values=np.array([50.0]),
        weights=np.array([1.0]),
        cells=np.array(["a"]),
        parents=np.array(["parent"]),
    )
    with pytest.raises(ValueError, match="2008 bootstrap support"):
        groupings.fixed_cell_distribution(a, b)
