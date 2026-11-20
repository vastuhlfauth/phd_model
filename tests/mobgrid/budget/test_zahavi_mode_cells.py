"""Synthetic tests for the mode-user-day analysis, section 9.9."""

from pathlib import Path

import duckdb
import numpy as np
import pytest
from mobgrid.budget import modes_cache, scope, variation
from mobgrid.budget import zahavi_groupings as groupings
from mobgrid.budget import zahavi_mode_cells as cells
from mobgrid.budget import zahavi_modes as modes


def test_mode_days_sum_minutes_distance_and_constant_rate_energy() -> None:
    days = cells.aggregate_mode_days(
        day=np.array(["d1", "d1", "d1", "d2"]),
        mode=np.array(["walk", "walk", "car", "walk"]),
        household=np.array([123, 123, 123, 456]),
        weight=np.array([2.0, 2.0, 2.0, 1.0]),
        minutes=np.array([10.0, 5.0, 20.0, 15.0]),
        distance_km=np.array([1.0, 0.5, 5.0, np.nan]),
        energy_kj=np.array([30.0, 15.0, 60.0, 45.0]),
    )
    index = np.flatnonzero((days.day == "d1") & (days.mode == "walk"))[0]
    assert days.minutes[index] == pytest.approx(15)
    assert days.distance_km[index] == pytest.approx(1.5)
    assert days.trips[index] == 2
    assert days.energy_kj == pytest.approx(days.minutes * 3)
    assert days.household.tolist() == ["123", "123", "456"]
    missing = np.flatnonzero(days.day == "d2")[0]
    assert days.distance_trips[missing] == 0
    assert days.distance_minutes[missing] == 0


def test_mode_days_reject_inconsistent_day_weights() -> None:
    with pytest.raises(ValueError, match="weight"):
        cells.aggregate_mode_days(
            day=np.array(["d", "d"]),
            mode=np.array(["walk", "walk"]),
            household=np.array(["h", "h"]),
            weight=np.array([1.0, 2.0]),
            minutes=np.array([1.0, 1.0]),
            distance_km=np.array([1.0, 1.0]),
            energy_kj=np.array([1.0, 1.0]),
        )


def test_missing_trip_energy_is_not_treated_as_zero() -> None:
    days = cells.aggregate_mode_days(
        day=np.array(["d", "d"]),
        mode=np.array(["walk", "walk"]),
        household=np.array(["h", "h"]),
        weight=np.array([1.0, 1.0]),
        minutes=np.array([1.0, 2.0]),
        distance_km=np.array([1.0, 1.0]),
        energy_kj=np.array([1.0, np.nan]),
    )
    assert np.isnan(days.energy_kj[0])


def test_target_reweight_matches_joint_distribution_and_preserves_input() -> None:
    target_cells = np.array([["employed", "dense", "q1"], ["retired", "sparse", "q2"]])
    source_cells = np.array(
        [["employed", "dense", "q1"], ["employed", "dense", "q1"],
         ["retired", "sparse", "q2"]]
    )
    source_weight = np.array([1.0, 2.0, 9.0])
    result = cells.reweight_to_target(
        target_cells, np.array([3.0, 1.0]), source_cells, source_weight
    )
    assert result[:2].sum() / result.sum() == pytest.approx(0.75)
    assert result[2] / result.sum() == pytest.approx(0.25)
    assert source_weight.tolist() == [1, 2, 9]


def test_target_reweight_rejects_missing_support() -> None:
    with pytest.raises(ValueError, match="support"):
        cells.reweight_to_target(
            np.array([["employed"], ["retired"]]),
            np.array([1.0, 1.0]),
            np.array([["employed"]]),
            np.array([1.0]),
        )


def test_reweight_zeroes_source_only_cells_without_merging() -> None:
    result = cells.reweight_to_target(
        np.array([["employed"]]),
        np.array([1.0]),
        np.array([["employed"], ["retired"]]),
        np.array([1.0, 3.0]),
    )
    assert result == pytest.approx([4.0, 0.0])


def test_mode_decomposition_reproduces_change_without_selection() -> None:
    a = variation.PersonDays(
        weight=np.array([1.0]), trips=np.array([2.0]),
        distance_km=np.array([10.0]), time_min=np.array([20.0]),
    )
    b = variation.PersonDays(
        weight=np.array([1.0]), trips=np.array([2.0]),
        distance_km=np.array([20.0]), time_min=np.array([40.0]),
    )
    result = variation.decompose(a, b)
    assert result.selection_min == pytest.approx(0)
    assert result.trips_min + result.distance_min + result.speed_min == pytest.approx(
        result.delta_min
    )


def test_pairwise_weighted_ks_is_symmetric_and_zero_for_identical_modes() -> None:
    a = modes.Observations(
        np.array([2.0, 4.0]), np.array([1.0, 3.0]), np.array(["a", "b"])
    )
    b = modes.Observations(
        np.array([1.0, 4.0]), np.array([2.0, 1.0]), np.array(["c", "d"])
    )
    assert modes.weighted_ks(a, b) == pytest.approx(modes.weighted_ks(b, a))
    assert modes.weighted_ks(a, a) == pytest.approx(0)


def _cell_sample(minutes: list[float]) -> cells.ModeCellSample:
    data = cells.aggregate_mode_days(
        day=np.array(["d1", "d2", "d3"]),
        mode=np.array(["walk", "walk", "walk"]),
        household=np.array([1, 2, 3]),
        weight=np.ones(3),
        minutes=np.array(minutes),
        distance_km=np.array([5.0, 5.0, 20.0]),
        energy_kj=np.full(3, np.nan),
    )
    return cells.ModeCellSample(data, np.array(["dense", "dense", "sparse"]))


def test_mode_cells_include_hidden_days_in_national_comparison() -> None:
    a = _cell_sample([10.0, 10.0, 20.0])
    b = _cell_sample([20.0, 20.0, 60.0])
    draws = modes.Draws(np.array(["1", "2", "3"]), np.ones((5, 3)), 0)
    rows = cells.mode_cell_statistics(
        a, b, draws, draws, selected=scope.REFERENCE_SCOPE,
        minimum_n=2, caution_n=3, margins=(0.15, 0.10),
    )
    dense = next(row for row in rows if row["cell"] == "dense")
    sparse = next(row for row in rows if row["cell"] == "sparse")
    assert dense["minutes_2008"] == pytest.approx(10)
    assert dense["km_2008"] == pytest.approx(5)
    assert dense["speed_2008"] == pytest.approx(30)
    assert dense["ratio"] == pytest.approx(2)
    assert dense["ks_2008"] == pytest.approx(1 / 3)
    assert dense["distance_gap_2008"] + dense["speed_gap_2008"] == pytest.approx(
        10 - 40 / 3
    )
    assert dense["selection_gap_2008"] == pytest.approx(0)
    assert dense["caution_2008"]
    assert np.isnan(sparse["minutes_2008"])
    assert np.isnan(sparse["ks_2008"])
    assert np.isnan(sparse["ratio"])


def test_mode_cells_daytable_suppresses_cross_year_results() -> None:
    sample = _cell_sample([10.0, 10.0, 20.0])
    draws = modes.Draws(np.array(["1", "2", "3"]), np.ones((5, 3)), 0)
    selected = next(s for s in scope.ALL_SCOPES if s.distance == "daytable")
    rows = cells.mode_cell_statistics(
        sample, sample, draws, draws, selected=selected,
        minimum_n=2, caution_n=3, margins=(0.15, 0.10),
    )
    row = next(item for item in rows if item["cell"] == "dense")
    assert row["minutes_2008"] == pytest.approx(10)
    assert np.isnan(row["ratio"])
    assert row["verdict_15"] == ""
    assert "not compared" in row["comparison_status"]


def test_distance_selection_is_separate_and_missing_distance_is_reported() -> None:
    data = cells.aggregate_mode_days(
        day=np.array(["d1", "d2", "d3"]),
        mode=np.array(["walk", "walk", "walk"]),
        household=np.array([1, 2, 3]),
        weight=np.ones(3),
        minutes=np.array([10.0, 10.0, 20.0]),
        distance_km=np.array([5.0, np.nan, 20.0]),
        energy_kj=np.full(3, np.nan),
    )
    sample = cells.ModeCellSample(data, np.array(["dense", "dense", "sparse"]))
    draws = modes.Draws(np.array(["1", "2", "3"]), np.ones((5, 3)), 0)
    row = cells.mode_cell_statistics(
        sample, sample, draws, draws, selected=scope.REFERENCE_SCOPE,
        minimum_n=2, caution_n=3, margins=(0.15, 0.10),
    )[0]
    assert row["distance_status_2008"] == "incomplete"
    assert row["distance_trip_share_2008"] == pytest.approx(0.5)
    assert row["selection_gap_2008"] != pytest.approx(0)
    assert (
        row["distance_gap_2008"] + row["speed_gap_2008"] + row["selection_gap_2008"]
    ) == pytest.approx(10 - 40 / 3)


def test_mode_cell_disclosure_thresholds_are_day_counts() -> None:
    labels = np.repeat(["n49", "n50", "n99", "n100"], [49, 50, 99, 100])
    n = len(labels)
    households = np.array([f"h{index:03d}" for index in range(n)])
    data = cells.aggregate_mode_days(
        day=households, mode=np.repeat("walk", n), household=households,
        weight=np.ones(n), minutes=np.repeat(10.0, n),
        distance_km=np.ones(n), energy_kj=np.full(n, np.nan),
    )
    sample = cells.ModeCellSample(data, labels)
    draws = modes.Draws(households, np.ones((5, n)), 0)
    rows = {
        row["cell"]: row for row in cells.mode_cell_statistics(
            sample, sample, draws, draws, selected=scope.REFERENCE_SCOPE,
            minimum_n=50, caution_n=100, margins=(0.15, 0.10),
        )
    }
    assert np.isnan(rows["n49"]["minutes_2008"])
    assert rows["n50"]["minutes_2008"] == pytest.approx(10)
    assert rows["n50"]["caution_2008"]
    assert rows["n99"]["caution_2008"]
    assert not rows["n100"]["caution_2008"]
    assert rows["n100"]["ratio_low"] == pytest.approx(1)
    assert rows["n100"]["verdict_15"] == "equivalent"


def test_absent_year_cell_is_not_compared() -> None:
    a = _cell_sample([10.0, 10.0, 20.0])
    b = cells.ModeCellSample(a.days, np.array(["dense", "dense", "dense"]))
    draws = modes.Draws(np.array(["1", "2", "3"]), np.ones((5, 3)), 0)
    rows = cells.mode_cell_statistics(
        a, b, draws, draws, selected=scope.REFERENCE_SCOPE,
        minimum_n=1, caution_n=2, margins=(0.15, 0.10),
    )
    row = next(item for item in rows if item["cell"] == "sparse")
    assert row["n_2019"] == 0
    assert np.isnan(row["minutes_2019"])
    assert np.isnan(row["ratio"])


def test_loads_mode_days_and_attributes_for_all_scopes(tmp_path: Path) -> None:
    cache = modes_cache.SurveyCache(tmp_path)
    with duckdb.connect() as con:
        for selected in scope.ALL_SCOPES:
            con.execute(
                """
                COPY (SELECT * FROM (VALUES
                    ('d1', 'p1', 123, 2.0, 'walk', 5.0, 0.5, 1.4,
                     'employed', 'q1'),
                    ('d1', 'p1', 123, 2.0, 'car_driver', 10.0, 4.0, 1.1,
                     'employed', 'q1'),
                    ('d2', 'p2', 456, 1.0, 'walk', 15.0, 1.5, 4.1,
                     'retired', 'q2')
                ) AS t(day_id, ident_ind, ident_men, pond_jour, mode7,
                       duration_min, distance_km, motive, population_category,
                       income_quintile)) TO ? (FORMAT PARQUET)
                """,
                [str(cache.trips(selected))],
            )
    for selected in scope.ALL_SCOPES:
        data = cells.read_mode_cell_data(
            cache, selected,
            income={"p1": "q1", "p2": "q2"},
            density={"p1": "dense", "p2": "sparse"},
            vehicles={"123": "1", "456": "0"},
            household_type={"123": "couple", "456": "single_person"},
        )
        assert data.days.day.tolist() == ["d1", "d1", "d2"]
        assert data.attributes["day_purpose"].tolist() == [
            "work_study", "work_study", "other"
        ]
        assert data.attributes["vehicles"].tolist() == ["1", "1", "0"]
        assert data.attributes["population"].tolist() == [
            "employed", "employed", "retired"
        ]
        draws = modes.Draws(np.array(["123", "456"]), np.ones((5, 2)), 0)
        rows = cells.evaluate_mode_scope(
            data, data, draws, draws, selected=selected,
            merge_config=groupings.MergeConfig(
                checkpoint_dir=tmp_path, dimensions={}
            ),
            minimum_n=1, caution_n=2, margins=(0.15, 0.10),
        )
        assert {row["grouping"] for row in rows} == {
            "density", "population", "income", "vehicles",
            "household_type", "day_purpose",
        }
        assert {row["mode"] for row in rows} == {"walk", "car_driver"}
        assert all(row["scope"] == selected.id for row in rows)
    config = groupings.MergeConfig(
        checkpoint_dir=tmp_path,
        dimensions={
            "density": groupings.OrderedDimension(
                levels=["dense", "sparse"], preferred=[("dense", "sparse")]
            )
        },
    )
    rows = cells.evaluate_mode_scope(
        data, data, draws, draws, selected=scope.REFERENCE_SCOPE,
        merge_config=config, minimum_n=2, caution_n=3, margins=(0.15, 0.10),
    )
    density_rows = [
        r for r in rows if r["mode"] == "walk" and r["grouping"] == "density"
    ]
    assert len(density_rows) == 1
    assert density_rows[0]["merged_from"] == "dense+sparse"
    population = [
        r for r in rows if r["mode"] == "walk" and r["grouping"] == "population"
    ]
    assert {row["cell"] for row in population} == {"employed", "retired"}


def _reweight_sample(minutes: list[float], population: list[str]) -> cells.ModeCellData:
    n = len(minutes)
    households = np.array([f"h{i}" for i in range(n)])
    data = cells.aggregate_mode_days(
        day=households, mode=np.repeat("walk", n), household=households,
        weight=np.ones(n), minutes=np.array(minutes),
        distance_km=np.ones(n), energy_kj=np.full(n, np.nan),
    )
    return cells.ModeCellData(
        data,
        {
            "population": np.array(population),
            "density": np.where(np.array(population) == "employed", "dense", "sparse"),
            "income": np.where(np.array(population) == "employed", "q1", "q2"),
        },
    )


def test_mode_reweighting_targets_2008_users(tmp_path: Path) -> None:
    a = _reweight_sample([10, 10, 10, 10], ["employed"] * 3 + ["retired"])
    b = _reweight_sample([20, 40, 40, 40], ["employed"] + ["retired"] * 3)
    draws = modes.Draws(np.array(["h0", "h1", "h2", "h3"]), np.ones((5, 4)), 0)
    rows = cells.mode_reweighting(
        a, b, draws, draws, selected=scope.REFERENCE_SCOPE,
        merge_config=groupings.MergeConfig(checkpoint_dir=tmp_path, dimensions={}),
        minimum_n=1, caution_n=2, max_lost_share=0.01,
    )
    assert len(rows) == 1
    assert rows[0]["ratio_before"] == pytest.approx(3.5)
    assert rows[0]["ratio_after"] == pytest.approx(2.5)
    assert rows[0]["ratio_after_low"] == pytest.approx(2.5)
    assert rows[0]["lost_target_share"] == pytest.approx(0)


def test_mode_reweighting_reports_unsupported_2008_target(tmp_path: Path) -> None:
    a = _reweight_sample([10, 10], ["employed", "retired"])
    b = _reweight_sample([20, 20], ["employed", "employed"])
    draws = modes.Draws(np.array(["h0", "h1"]), np.ones((5, 2)), 0)
    row = cells.mode_reweighting(
        a, b, draws, draws, selected=scope.REFERENCE_SCOPE,
        merge_config=groupings.MergeConfig(checkpoint_dir=tmp_path, dimensions={}),
        minimum_n=1, caution_n=2, max_lost_share=0.01,
    )[0]
    assert row["lost_target_share"] == pytest.approx(0.5)
    assert np.isnan(row["ratio_after"])
    assert "support" in row["status"]


def test_absent_2008_joint_cell_uses_population_parent(tmp_path: Path) -> None:
    a = _reweight_sample([10, 20], ["employed", "employed"])
    b = _reweight_sample([30, 30], ["employed", "employed"])
    b.attributes["density"] = np.array(["sparse", "sparse"])
    draws = modes.Draws(np.array(["h0", "h1"]), np.ones((5, 2)), 0)
    row = cells.mode_reweighting(
        a, b, draws, draws, selected=scope.REFERENCE_SCOPE,
        merge_config=groupings.MergeConfig(checkpoint_dir=tmp_path, dimensions={}),
        minimum_n=1, caution_n=2, max_lost_share=0.01,
    )[0]
    assert row["parent_fallback_share"] == pytest.approx(1)
    assert row["fixed_2008_mean"] == pytest.approx(15)


def test_reweighting_support_cutoff_is_strict() -> None:
    args = (
        np.array([0, 1]), np.array([99.0, 1.0]),
        np.array([0]), np.array([1.0]), np.array([20.0]),
    )
    estimate, lost = cells._target_mean(*args, size=2, max_lost_share=0.01)
    assert lost == pytest.approx(0.01)
    assert np.isnan(estimate)
    estimate, lost = cells._target_mean(*args, size=2, max_lost_share=0.011)
    assert lost == pytest.approx(0.01)
    assert estimate == pytest.approx(20)


def test_reweighting_daytable_does_not_compare_years(tmp_path: Path) -> None:
    data = _reweight_sample([10, 20], ["employed", "retired"])
    draws = modes.Draws(np.array(["h0", "h1"]), np.ones((5, 2)), 0)
    selected = next(s for s in scope.ALL_SCOPES if s.distance == "daytable")
    row = cells.mode_reweighting(
        data, data, draws, draws, selected=selected,
        merge_config=groupings.MergeConfig(checkpoint_dir=tmp_path, dimensions={}),
        minimum_n=1, caution_n=2, max_lost_share=0.01,
    )[0]
    assert np.isnan(row["ratio_before"])
    assert np.isnan(row["ratio_after"])
    assert "not compared" in row["status"]
