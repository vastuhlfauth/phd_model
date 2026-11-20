"""Synthetic tests for the mode-user-day analysis, section 9.9."""

import csv
from dataclasses import replace
from pathlib import Path

import duckdb
import numpy as np
import pytest
import yaml
from mobgrid.budget import modes_cache, scope, variation
from mobgrid.budget import zahavi_groupings as groupings
from mobgrid.budget import zahavi_income as income
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
        [
            ["employed", "dense", "q1"],
            ["employed", "dense", "q1"],
            ["retired", "sparse", "q2"],
        ]
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
        weight=np.array([1.0]),
        trips=np.array([2.0]),
        distance_km=np.array([10.0]),
        time_min=np.array([20.0]),
    )
    b = variation.PersonDays(
        weight=np.array([1.0]),
        trips=np.array([2.0]),
        distance_km=np.array([20.0]),
        time_min=np.array([40.0]),
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
        a,
        b,
        draws,
        draws,
        selected=scope.REFERENCE_SCOPE,
        minimum_n=2,
        caution_n=3,
        margins=(0.15, 0.10),
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
        sample,
        sample,
        draws,
        draws,
        selected=selected,
        minimum_n=2,
        caution_n=3,
        margins=(0.15, 0.10),
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
        sample,
        sample,
        draws,
        draws,
        selected=scope.REFERENCE_SCOPE,
        minimum_n=2,
        caution_n=3,
        margins=(0.15, 0.10),
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
        day=households,
        mode=np.repeat("walk", n),
        household=households,
        weight=np.ones(n),
        minutes=np.repeat(10.0, n),
        distance_km=np.ones(n),
        energy_kj=np.full(n, np.nan),
    )
    sample = cells.ModeCellSample(data, labels)
    draws = modes.Draws(households, np.ones((5, n)), 0)
    rows = {
        row["cell"]: row
        for row in cells.mode_cell_statistics(
            sample,
            sample,
            draws,
            draws,
            selected=scope.REFERENCE_SCOPE,
            minimum_n=50,
            caution_n=100,
            margins=(0.15, 0.10),
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
        a,
        b,
        draws,
        draws,
        selected=scope.REFERENCE_SCOPE,
        minimum_n=1,
        caution_n=2,
        margins=(0.15, 0.10),
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
            cache,
            selected,
            income={"p1": "q1", "p2": "q2"},
            density={"p1": "dense", "p2": "sparse"},
            vehicles={"123": "1", "456": "0"},
            household_type={"123": "couple", "456": "single_person"},
        )
        assert data.days.day.tolist() == ["d1", "d1", "d2"]
        assert data.attributes["day_purpose"].tolist() == [
            "work_study",
            "work_study",
            "other",
        ]
        assert data.attributes["vehicles"].tolist() == ["1", "1", "0"]
        assert data.attributes["population"].tolist() == [
            "employed",
            "employed",
            "retired",
        ]
        draws = modes.Draws(np.array(["123", "456"]), np.ones((5, 2)), 0)
        rows = cells.evaluate_mode_scope(
            data,
            data,
            draws,
            draws,
            selected=selected,
            merge_config=groupings.MergeConfig(checkpoint_dir=tmp_path, dimensions={}),
            minimum_n=1,
            caution_n=2,
            margins=(0.15, 0.10),
        )
        assert {row["grouping"] for row in rows} == {
            "density",
            "population",
            "income",
            "vehicles",
            "household_type",
            "day_purpose",
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
        data,
        data,
        draws,
        draws,
        selected=scope.REFERENCE_SCOPE,
        merge_config=config,
        minimum_n=2,
        caution_n=3,
        margins=(0.15, 0.10),
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
        day=households,
        mode=np.repeat("walk", n),
        household=households,
        weight=np.ones(n),
        minutes=np.array(minutes),
        distance_km=np.ones(n),
        energy_kj=np.full(n, np.nan),
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
        a,
        b,
        draws,
        draws,
        selected=scope.REFERENCE_SCOPE,
        merge_config=groupings.MergeConfig(checkpoint_dir=tmp_path, dimensions={}),
        minimum_n=1,
        caution_n=2,
        max_lost_share=0.01,
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
        a,
        b,
        draws,
        draws,
        selected=scope.REFERENCE_SCOPE,
        merge_config=groupings.MergeConfig(checkpoint_dir=tmp_path, dimensions={}),
        minimum_n=1,
        caution_n=2,
        max_lost_share=0.01,
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
        a,
        b,
        draws,
        draws,
        selected=scope.REFERENCE_SCOPE,
        merge_config=groupings.MergeConfig(checkpoint_dir=tmp_path, dimensions={}),
        minimum_n=1,
        caution_n=2,
        max_lost_share=0.01,
    )[0]
    assert row["parent_fallback_share"] == pytest.approx(1)
    assert row["fixed_2008_mean"] == pytest.approx(15)


def test_reweighting_support_cutoff_is_strict() -> None:
    args = (
        np.array([0, 1]),
        np.array([99.0, 1.0]),
        np.array([0]),
        np.array([1.0]),
        np.array([20.0]),
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
        data,
        data,
        draws,
        draws,
        selected=selected,
        merge_config=groupings.MergeConfig(checkpoint_dir=tmp_path, dimensions={}),
        minimum_n=1,
        caution_n=2,
        max_lost_share=0.01,
    )[0]
    assert np.isnan(row["ratio_before"])
    assert np.isnan(row["ratio_after"])
    assert "not compared" in row["status"]


def _mode_trips(minutes: list[float], distance: list[float]) -> cells.ModeTrips:
    n = len(minutes)
    households = np.array([f"h{i}" for i in range(n)])
    return cells.ModeTrips(
        day=households,
        household=households,
        mode=np.repeat("walk", n),
        weight=np.ones(n),
        minutes=np.array(minutes),
        published_km=np.array(distance),
        crow_fly_km=np.array(distance),
    )


def test_per_mode_b2_and_whole_km_2019_variant() -> None:
    a = _mode_trips([10, 10], [2, 2])
    b = _mode_trips([20, 20], [3.6, 3.6])
    draws = modes.Draws(np.array(["h0", "h1"]), np.ones((5, 2)), 0)
    rows = cells.mode_decompositions(
        a,
        b,
        draws,
        draws,
        selected=scope.REFERENCE_SCOPE,
        minimum_n=1,
        caution_n=2,
    )
    published = next(row for row in rows if row["variant"] == "published")
    rounded = next(row for row in rows if row["variant"] == "rounded_crow_fly")
    assert published["delta"] == pytest.approx(10)
    assert sum(
        published[name] for name in ("trips", "distance", "speed", "selection")
    ) == pytest.approx(10)
    assert published["distance_b_km"] == pytest.approx(3.6)
    assert rounded["distance_b_km"] == pytest.approx(4)


def test_per_mode_rounding_uses_c4_nearest_and_up_bounds() -> None:
    a = _mode_trips([11, 11], [1, 1])
    b = _mode_trips([10, 10], [1, 1])
    config = variation.MeasurementConfig(
        rounding_draws=3,
        rounding_levels=(1, 5, 15, 30),
        duration_upper_min=(5, 10, 15, 30, 60),
        minimum_duration_min=5,
        short_duration_min=5,
        short_distance_km=1,
    )
    row = cells.mode_rounding_bounds(
        a,
        b,
        selected=scope.REFERENCE_SCOPE,
        config=config,
        minimum_n=1,
        caution_n=2,
        seed=3,
    )[0]
    assert row["lower_min"] == pytest.approx(-1)
    assert row["upper_min"] == pytest.approx(4)
    assert row["unmatched_2008_trip_share"] == 0


def test_rounding_marks_missing_target_duration_cells() -> None:
    a = _mode_trips([11, 11], [1, 1])
    b = _mode_trips([30, 30], [1, 1])
    config = variation.MeasurementConfig(
        rounding_draws=3,
        rounding_levels=(1, 5, 15, 30),
        duration_upper_min=(5, 10, 15, 30, 60),
        minimum_duration_min=5,
        short_duration_min=5,
        short_distance_km=1,
    )
    row = cells.mode_rounding_bounds(
        a,
        b,
        selected=scope.REFERENCE_SCOPE,
        config=config,
        minimum_n=1,
        caution_n=2,
        seed=3,
    )[0]
    assert row["unmatched_2008_trip_share"] == 1
    assert "incomplete" in row["status"]


def test_trip_loader_uses_published_not_corrected_distance(tmp_path: Path) -> None:
    cache = modes_cache.SurveyCache(tmp_path)
    with duckdb.connect() as con:
        con.execute(
            """CREATE TABLE trip_legs AS SELECT 'd1' day_id, 1 num_dep,
                40.0 distance_km_declared"""
        )
        con.execute(
            """COPY (SELECT 'd1' day_id, 1 num_dep, '123' ident_men,
                'walk' mode7, 1.0 pond_jour, 10.0 duration_min,
                1.0 distance_km, 4.5 crow_fly_km) TO ? (FORMAT PARQUET)""",
            [str(cache.trips(scope.REFERENCE_SCOPE))],
        )
        result = cells.read_mode_trips(con, cache, scope.REFERENCE_SCOPE)
        assert result.published_km.tolist() == [40.0]
        assert result.crow_fly_km.tolist() == [4.5]
        con.execute("DELETE FROM trip_legs")
        with pytest.raises(ValueError, match="exactly one"):
            cells.read_mode_trips(con, cache, scope.REFERENCE_SCOPE)


def test_decomposition_and_rounding_daytable_are_not_compared() -> None:
    data = _mode_trips([10, 10], [2, 2])
    draws = modes.Draws(np.array(["h0", "h1"]), np.ones((5, 2)), 0)
    selected = next(s for s in scope.ALL_SCOPES if s.distance == "daytable")
    config = variation.MeasurementConfig(
        rounding_draws=3,
        rounding_levels=(1, 5, 15, 30),
        duration_upper_min=(5, 10, 15, 30, 60),
        minimum_duration_min=5,
        short_duration_min=5,
        short_distance_km=1,
    )
    rows = cells.mode_decompositions(
        data, data, draws, draws, selected=selected, minimum_n=1, caution_n=2
    )
    rounding = cells.mode_rounding_bounds(
        data, data, selected=selected, config=config, minimum_n=1, caution_n=2, seed=3
    )
    assert all(
        np.isnan(row["delta"]) and "not compared" in row["status"] for row in rows
    )
    assert np.isnan(rounding[0]["lower_min"])
    assert "not compared" in rounding[0]["status"]


@pytest.mark.parametrize("rate", ["kh", "cp"])
def test_energy_collapse_symmetric_and_identical_distributions(rate: str) -> None:
    data = cells.aggregate_mode_days(
        day=np.array(["d1", "d2", "d3", "d4"]),
        mode=np.array(["walk", "walk", "car_driver", "car_driver"]),
        household=np.array(["h1", "h2", "h3", "h4"]),
        weight=np.ones(4),
        minutes=np.array([10.0, 20.0, 10.0, 20.0]),
        distance_km=np.ones(4),
        energy_kj=np.array([30.0, 60.0, 30.0, 60.0]),
    )
    draws = modes.Draws(np.array(["h1", "h2", "h3", "h4"]), np.ones((5, 4)), 0)
    rows = cells.energy_collapse(
        data,
        data,
        draws,
        draws,
        selected=scope.REFERENCE_SCOPE,
        rate=rate,
        minimum_n=2,
        caution_n=3,
    )
    pair = next(
        row for row in rows if row["kind"] == "within_year_pair" and row["year"] == 2008
    )
    assert pair["time_ks"] == pytest.approx(0)
    assert pair["energy_ks"] == pytest.approx(0)
    summary = next(
        row
        for row in rows
        if row["kind"] == "within_year_median" and row["year"] == 2019
    )
    assert summary["time_ks"] == pytest.approx(0)
    assert summary["energy_ks"] == pytest.approx(0)
    assert summary["energy_ks_high"] == pytest.approx(0)


def test_collapse_keeps_time_for_modes_without_energy() -> None:
    data = cells.aggregate_mode_days(
        day=np.array(["d1", "d2", "d3", "d4"]),
        mode=np.array(["walk", "walk", "other", "other"]),
        household=np.array(["h1", "h2", "h3", "h4"]),
        weight=np.ones(4),
        minutes=np.array([10.0, 20.0, 30.0, 40.0]),
        distance_km=np.ones(4),
        energy_kj=np.array([30.0, 60.0, np.nan, np.nan]),
    )
    draws = modes.Draws(np.array(["h1", "h2", "h3", "h4"]), np.ones((5, 4)), 0)
    rows = cells.energy_collapse(
        data,
        data,
        draws,
        draws,
        selected=scope.REFERENCE_SCOPE,
        rate="kh",
        minimum_n=2,
        caution_n=3,
    )
    pair = next(
        row for row in rows if row["kind"] == "within_year_pair" and row["year"] == 2008
    )
    assert pair["time_ks"] == pytest.approx(1)
    assert np.isnan(pair["energy_ks"])
    assert "energy" in pair["status"]


def test_energy_mode_loader_uses_reconstructed_step11_energy(tmp_path: Path) -> None:
    cache = modes_cache.SurveyCache(tmp_path)
    with duckdb.connect() as con:
        con.execute(
            """CREATE TABLE trip_legs AS SELECT 'd1' day_id, 1 num_dep,
                40.0 energy_kh_kj, 30.0 energy_cp_kj"""
        )
        con.execute(
            """COPY (SELECT 'd1' day_id, 1 num_dep, '123' ident_men,
                'walk' mode7, 1.0 pond_jour, 10.0 duration_min,
                1.0 distance_km) TO ? (FORMAT PARQUET)""",
            [str(cache.trips(scope.REFERENCE_SCOPE))],
        )
        kh = cells.read_mode_energy(con, cache, scope.REFERENCE_SCOPE, rate="kh")
        cp = cells.read_mode_energy(con, cache, scope.REFERENCE_SCOPE, rate="cp")
        assert kh.energy_kj.tolist() == [40.0]
        assert cp.energy_kj.tolist() == [30.0]


def _energy_survey(factor: float) -> cells.EnergySurvey:
    labels = {
        "population": np.array(["employed", "employed", "employed"]),
        "density": np.array(["dense", "dense", "dense"]),
        "income": np.array(["q1", "q1", "q1"]),
        "vehicles": np.array(["1", "1", "1"]),
    }
    return cells.EnergySurvey(
        roster_household=np.array(["1", "2", "3"]),
        roster_weight=np.array([10.0, 10.0, 10.0]),
        roster_labels=labels,
        day_id=np.array(["d1", "d2"]),
        day_household=np.array(["1", "1"]),
        day_weight=np.array([2.0, 3.0]),
        day_labels={name: values[:2] for name, values in labels.items()},
        day_mode=np.array(["car_driver", "unknown"]),
        is_open=np.array([False, True]),
        has_trips=np.array([True, False]),
        energy_kj=np.array([30.0 * factor, 0.0]),
        mode_kj={
            "walk": np.array([10.0 * factor, 0.0]),
            "car_driver": np.array([20.0 * factor, 0.0]),
        },
        mode_used={
            "walk": np.array([True, False]),
            "car_driver": np.array([True, False]),
        },
    )


@pytest.mark.parametrize(("rate", "factor"), [("kh", 1.0), ("cp", 2.0)])
def test_grouped_energy_and_mode_person_sum(rate: str, factor: float) -> None:
    data = _energy_survey(factor)
    draws = modes.Draws(np.array(["1", "2", "3"]), np.ones((5, 3)), 0)
    rows = cells.energy_statistics(
        data,
        data,
        draws,
        draws,
        selected=scope.REFERENCE_SCOPE,
        rate=rate,
        minimum_n=1,
        caution_n=2,
        margins=(0.15, 0.10),
        merge_config=groupings.MergeConfig(checkpoint_dir=Path("."), dimensions={}),
    )
    total = next(
        r for r in rows if r["grouping"] == "overall" and r["basis"] == "person"
    )
    modes_rows = [r for r in rows if r["grouping"] == "mode" and r["basis"] == "person"]
    assert total["mean_2008"] == pytest.approx(60 * factor / 27)
    assert sum(r["mean_2008"] for r in modes_rows) == pytest.approx(total["mean_2008"])
    assert all(r["ratio"] == pytest.approx(1) for r in modes_rows)
    mode_group = next(
        r for r in rows if r["grouping"] == "day_mode_group" and r["basis"] == "person"
    )
    assert np.isnan(mode_group["mean_2008"])
    assert "not defined" in mode_group["status"]
    category = next(
        r for r in rows if r["grouping"] == "population" and r["basis"] == "travel_day"
    )
    assert category["mean_2008"] == pytest.approx(30 * factor)


def test_energy_cache_join_and_unknown_only_days(tmp_path: Path) -> None:
    cache = modes_cache.SurveyCache(tmp_path)
    with duckdb.connect() as con:
        con.execute(
            """COPY (SELECT * FROM (VALUES
                ('d1', 'p1', '1', 2.0),
                ('d2', 'p1', '1', 3.0),
                ('d3', 'p2', '2', 4.0)
            ) AS x(day_id, ident_ind, ident_men, pond_jour))
            TO ? (FORMAT PARQUET)""",
            [str(cache.day_base)],
        )
        con.execute(
            """COPY (SELECT * FROM (VALUES
                ('d1', 30.0, 'car_driver'),
                ('d3', NULL, 'other')
            ) AS x(day_id, total_energy_kh_kj, day_mode_group))
            TO ? (FORMAT PARQUET)""",
            [str(cache.days(scope.REFERENCE_SCOPE))],
        )
    cached = income.CachedIncome(
        people=income.People(
            np.array(["p1", "p2", "p3"]),
            np.array(["1", "2", "3"]),
            np.array(["q1", "q1", "q1"]),
            np.array([10.0, 10.0, 10.0]),
        ),
        days=income.Days(
            np.array(["p1", "p1", "p2"]),
            np.array(["1", "1", "2"]),
            np.array(["q1", "q1", "q1"]),
            np.array([2.0, 3.0, 4.0]),
            np.array([10.0, 0.0, 10.0]),
            np.array([False, True, False]),
            np.array([True, False, True]),
        ),
        population=np.array(["employed"] * 3),
        density=np.array(["dense"] * 3),
        cars=np.array(["1"] * 3),
        weekday=np.array(["monday"] * 3),
    )
    mode_days = cells.aggregate_mode_days(
        day=np.array(["d1", "d1", "d3"]),
        mode=np.array(["walk", "car_driver", "other"]),
        household=np.array(["1", "1", "2"]),
        weight=np.array([2.0, 2.0, 4.0]),
        minutes=np.array([5.0, 5.0, 10.0]),
        distance_km=np.ones(3),
        energy_kj=np.array([10.0, 20.0, np.nan]),
    )
    survey = cells.read_energy_survey(cache, cached, mode_days, rate="kh")
    draws = modes.Draws(np.array(["1", "2", "3"]), np.ones((5, 3)), 0)
    rows = cells.energy_statistics(
        survey,
        survey,
        draws,
        draws,
        selected=scope.REFERENCE_SCOPE,
        rate="kh",
        minimum_n=1,
        caution_n=2,
        margins=(0.15, 0.10),
        merge_config=groupings.MergeConfig(checkpoint_dir=tmp_path, dimensions={}),
    )
    total = next(
        r for r in rows if r["grouping"] == "overall" and r["basis"] == "person"
    )
    assert total["mean_2008"] == pytest.approx(60 / (30 - 3 - 4))
    assert total["unknown_energy_days_2008"] == 1
    assert total["unknown_energy_weight_share_2008"] == pytest.approx(4 / 6)


def test_energy_person_mode_accounting_in_every_draw() -> None:
    data = _energy_survey(1)
    draws = modes.Draws(
        np.array(["1", "2", "3"]),
        np.array([[1.0, 2.0, 1.0], [2.0, 1.0, 1.0], [0.0, 1.0, 2.0]]),
        0,
    )
    rw = cells._energy_draw_weights(data.roster_household, data.roster_weight, draws)
    dw = cells._energy_draw_weights(data.day_household, data.day_weight, draws)
    roster = np.ones(3, dtype=bool)
    days = np.ones(2, dtype=bool)
    total = cells._energy_metric(data, roster, days, data.energy_kj, "person", rw, dw)
    by_mode = [
        cells._energy_metric(data, roster, days, values, "person", rw, dw)
        for values in data.mode_kj.values()
    ]
    assert sum(value.value for value in by_mode) == pytest.approx(total.value)
    assert sum((value.replicates for value in by_mode)) == pytest.approx(
        total.replicates
    )
    invalid = replace(data, energy_kj=np.array([31.0, 0.0]))
    with pytest.raises(ValueError, match="does not sum"):
        cells._energy_survey_validate(invalid)


def test_zero_2019_energy_has_zero_ratio(tmp_path: Path) -> None:
    draws = modes.Draws(np.array(["1", "2", "3"]), np.ones((5, 3)), 0)
    rows = cells.energy_statistics(
        _energy_survey(1),
        _energy_survey(0),
        draws,
        draws,
        selected=scope.REFERENCE_SCOPE,
        rate="kh",
        minimum_n=1,
        caution_n=2,
        margins=(0.15, 0.10),
        merge_config=groupings.MergeConfig(checkpoint_dir=tmp_path, dimensions={}),
    )
    total = next(
        row for row in rows if row["grouping"] == "overall" and row["basis"] == "person"
    )
    assert total["ratio"] == 0
    assert total["ratio_low"] == 0


def test_synthetic_report_writes_all_tables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    caches = []
    connections = []
    attrs = []
    for year in (2008, 2019):
        root = tmp_path / str(year)
        root.mkdir()
        cache = modes_cache.SurveyCache(root)
        con = duckdb.connect()
        con.execute(
            """CREATE TABLE trip_legs AS
            SELECT 'd' || i AS day_id, 1 AS num_dep,
                2.0 AS distance_km_declared, 30.0 AS energy_kh_kj,
                20.0 AS energy_cp_kj FROM range(4) t(i)"""
        )
        con.execute(
            """COPY (SELECT 'p' || i ident_ind, 'h' || i ident_men,
                'employed' population_category, 1.0 weight
                FROM range(4) t(i)) TO ? (FORMAT PARQUET)""",
            [str(cache.roster)],
        )
        con.execute(
            """COPY (SELECT 'd' || i day_id, 'p' || i ident_ind,
                'h' || i ident_men, 1.0 pond_jour, TRUE is_round
                FROM range(4) t(i)) TO ? (FORMAT PARQUET)""",
            [str(cache.day_base)],
        )
        for selected in scope.ALL_SCOPES:
            con.execute(
                """COPY (SELECT 'd' || i day_id, 'p' || i ident_ind,
                    'h' || i ident_men, 1 num_dep,
                    CASE WHEN i % 2 = 0 THEN 'walk' ELSE 'car_driver' END mode7,
                    1.0 pond_jour, 10.0 duration_min, 2.0 distance_km,
                    1.8 crow_fly_km, 'employed' population_category,
                    'q1' income_quintile, 1.4 motive, 'monday' described_weekday_name
                    FROM range(4) t(i)) TO ? (FORMAT PARQUET)""",
                [str(cache.trips(selected))],
            )
            con.execute(
                """COPY (SELECT 'd' || i day_id, 10.0 total_time_min,
                    'q1' income_quintile, 30.0 total_energy_kh_kj,
                    20.0 total_energy_cp_kj,
                    CASE WHEN i % 2 = 0 THEN 'walking_only'
                         ELSE 'car_driver' END day_mode_group
                    FROM range(4) t(i)) TO ? (FORMAT PARQUET)""",
                [str(cache.days(selected))],
            )
        caches.append(cache)
        connections.append(con)
        attrs.append(
            (
                {f"p{i}": "q1" for i in range(4)},
                {f"p{i}": "dense" for i in range(4)},
                income.HouseholdVehicles({f"h{i}": "1" for i in range(4)}, {}),
                {f"h{i}": "single_person" for i in range(4)},
            )
        )
    draws = modes.Draws(np.array([f"h{i}" for i in range(4)]), np.ones((5, 4)), 0)
    measurement = variation.MeasurementConfig(
        rounding_draws=3,
        rounding_levels=(1, 5, 15, 30),
        duration_upper_min=(5, 10, 15, 30, 60),
        minimum_duration_min=5,
        short_duration_min=5,
        short_distance_km=1,
    )
    out = tmp_path / "report"
    try:
        cells.run_report(
            out,
            caches,
            connections,
            attrs,
            [draws, draws],
            merge_config=groupings.MergeConfig(checkpoint_dir=tmp_path, dimensions={}),
            measurement=measurement,
            minimum_n=1,
            caution_n=2,
            max_lost_share=0.01,
            margins=(0.15, 0.10),
            seed=0,
        )
    finally:
        for con in connections:
            con.close()
    for name in (
        "mode_cells",
        "reweighted",
        "decomposition",
        "rounding",
        "energy",
        "collapse",
    ):
        with (out / f"{name}.csv").open(encoding="utf-8", newline="") as stream:
            assert list(csv.DictReader(stream)), name
    with (out / "mode_cells.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert {row["scope"] for row in rows} == {item.id for item in scope.ALL_SCOPES}
    assert all(not row["ratio"] for row in rows if "daytable" in row["scope"])
    reference = next(
        row
        for row in rows
        if row["scope"] == scope.REFERENCE_SCOPE.id
        and row["mode"] == "walk"
        and row["grouping"] == "population"
    )
    assert float(reference["minutes_2008"]) == pytest.approx(10)
    assert float(reference["ratio"]) == pytest.approx(1)
    with (out / "energy.csv").open(encoding="utf-8", newline="") as stream:
        energy_rows = list(csv.DictReader(stream))
    for rate, expected in (("kh", 30.0), ("cp", 20.0)):
        energy_row = next(
            row
            for row in energy_rows
            if row["rate"] == rate
            and row["grouping"] == "overall"
            and row["basis"] == "person"
        )
        assert float(energy_row["mean_2008"]) == pytest.approx(expected)
        assert float(energy_row["ratio"]) == pytest.approx(1)
    with (out / "collapse.csv").open(encoding="utf-8", newline="") as stream:
        collapse_rows = list(csv.DictReader(stream))
    assert all(
        float(row["time_ks"]) == pytest.approx(0)
        and float(row["energy_ks"]) == pytest.approx(0)
        for row in collapse_rows
        if row["kind"] == "within_year_median"
    )
    assert (tmp_path / "report.md").is_file()
    configs = {
        "merge": {"checkpoint_dir": "checkpoint", "dimensions": {}},
        "income": {
            "entd_cars": "cars.csv",
            "caution_cell_n": 2,
            "checkpoint_dir": "checkpoint",
            "regression_level_order": {},
            "max_lost_target_share": 0.01,
        },
        "modes": {
            "trip_grid_max_min": 240,
            "day_grid_max_min": 360,
            "minimum_cell_n": 1,
            "thresholds_min": [15],
            "bootstrap_reps": 5,
            "seed": 0,
            "cache_dir": "cache",
            "b3_report": "b3.md",
            "logs_dir": "logs",
            "reference_2008_min": 52,
            "reference_2019_min": 57,
            "reference_tolerance_min": 0.05,
        },
        "variation": {
            "equivalence_margin": 0.15,
            "secondary_equivalence_margin": 0.10,
            "measurement": measurement.model_dump(),
            "scope": {"activity_stay_min": 15},
        },
    }
    for name, config in configs.items():
        (tmp_path / f"{name}.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    monkeypatch.setattr(cells.vr, "ROOT", tmp_path)
    monkeypatch.setattr(
        cells.income_module,
        "read_signed_cache",
        lambda survey, *_args, **_kwargs: caches[0 if survey is cells.entd2008 else 1],
    )
    monkeypatch.setattr(
        cells.groupings,
        "extract_attributes",
        lambda survey, *_args, **_kwargs: attrs[0 if survey is cells.entd2008 else 1],
    )
    monkeypatch.setattr(cells, "load_energy_config", lambda *_args: None)
    monkeypatch.setattr(cells.modes, "make_draws", lambda *_args, **_kwargs: draws)
    for survey in (cells.entd2008, cells.emp2019):
        monkeypatch.setattr(survey, "extract_tables", lambda *_args: {})
        monkeypatch.setattr(survey, "register_views", lambda *_args: None)
        monkeypatch.setattr(
            survey,
            "build_trip_legs",
            lambda con, *_args, **_kwargs: con.execute(
                """CREATE TABLE trip_legs AS
                SELECT 'd' || i AS day_id, 1 AS num_dep,
                    2.0 AS distance_km_declared, 30.0 AS energy_kh_kj,
                    20.0 AS energy_cp_kj FROM range(4) t(i)"""
            ),
        )
    cli_out = tmp_path / "cli-report"
    assert (
        cells.main(
            [
                "--out",
                str(cli_out),
                "--merge-config",
                str(tmp_path / "merge.yaml"),
                "--income-config",
                str(tmp_path / "income.yaml"),
                "--modes-config",
                str(tmp_path / "modes.yaml"),
                "--variation-config",
                str(tmp_path / "variation.yaml"),
                "--config",
                str(tmp_path / "unused.yaml"),
                "--entd2008-data-path",
                str(tmp_path / "entd"),
                "--emp2019-data-path",
                str(tmp_path / "emp"),
            ]
        )
        == 0
    )
    for name in (
        "mode_cells",
        "reweighted",
        "decomposition",
        "rounding",
        "energy",
        "collapse",
    ):
        with (cli_out / f"{name}.csv").open(encoding="utf-8", newline="") as stream:
            assert list(csv.DictReader(stream)), name
    assert (tmp_path / "cli-report.md").is_file()
    assert list((tmp_path / "logs").glob("*_zahavi_mode_cells_summary.md"))
