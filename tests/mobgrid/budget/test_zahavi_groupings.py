"""Synthetic tests for the grouping report, section 9.9."""

import duckdb
import numpy as np
import pytest
import yaml
from mobgrid.budget import modes_cache, scope
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


def test_grouping_statistics_keep_small_cells_and_hide_their_levels():
    a = groupings.GroupingDays(
        person=np.array(["p1", "p2", "p3"]),
        household=np.array(["h1", "h2", "h3"]),
        weights=np.ones(3),
        minutes=np.array([10.0, 30.0, 80.0]),
        attributes={"population": np.array(["employed", "employed", "retired"])},
    )
    b = groupings.GroupingDays(
        person=a.person,
        household=a.household,
        weights=np.ones(3),
        minutes=np.array([10.0, 30.0, 80.0]),
        attributes=a.attributes,
    )
    draws = modes.Draws(
        households=np.array(["h1", "h2", "h3"]),
        multipliers=np.ones((20, 3)),
        seed=0,
    )
    rows, summary = groupings.grouping_statistics(
        a,
        b,
        np.array(["employed", "employed", "retired"]),
        np.array(["employed", "employed", "retired"]),
        draws,
        draws,
        minimum_n=2,
        margins=(0.15, 0.10),
        compare=True,
    )
    assert rows[0]["mean_2008"] == pytest.approx(20.0)
    assert rows[1]["n_2008"] == 1
    assert np.isnan(rows[1]["mean_2008"])
    assert summary["eta2_2008"] == pytest.approx(12 / 13)
    assert summary["mean_abs_log_ratio"] == pytest.approx(0)
    assert summary["equivalent_10_share"] == pytest.approx(1)


def test_daytable_grouping_suppresses_every_cross_year_value():
    day = groupings.GroupingDays(
        person=np.array(["p1", "p2"]),
        household=np.array(["h1", "h2"]),
        weights=np.ones(2),
        minutes=np.array([10.0, 30.0]),
        attributes={},
    )
    draws = modes.Draws(households=day.household, multipliers=np.ones((20, 2)), seed=0)
    rows, summary = groupings.grouping_statistics(
        day,
        day,
        np.array(["all", "all"]),
        np.array(["all", "all"]),
        draws,
        draws,
        minimum_n=1,
        margins=(0.15, 0.10),
        compare=False,
    )
    assert rows[0]["mean_2008"] == pytest.approx(20.0)
    assert rows[0]["mean_2019"] == pytest.approx(20.0)
    assert np.isnan(rows[0]["ratio"])
    assert rows[0]["verdict_10"] == ""
    assert np.isnan(summary["mean_abs_log_ratio"])
    assert np.isnan(summary["equivalent_10_share"])
    assert summary["eta2_2008"] == pytest.approx(0)


def test_category_grouping_excludes_unknown_and_preserves_weight_share(merge_config):
    a = groupings.GroupingDays(
        person=np.array(["p1", "p2", "p3"]),
        household=np.array(["h1", "h2", "h3"]),
        weights=np.array([1.0, 2.0, 1.0]),
        minutes=np.array([10.0, 20.0, 30.0]),
        attributes={
            "population": np.array(["employed", "employed", "unknown"]),
            "density": np.array(["dense", "intermediate", "sparse"]),
            "income": np.array(["q1", "q1", "q2"]),
        },
    )
    grouping = groupings.prepare_grouping(
        a,
        a,
        ("population", "density", "income"),
        config=merge_config,
        minimum_n=2,
    )
    assert grouping.excluded_share_2008 == pytest.approx(0.25)
    assert grouping.excluded_share_2019 == pytest.approx(0.25)
    assert len(grouping.a.minutes) == 2
    assert len(np.unique(grouping.cells_a)) == 1
    assert set(grouping.parents_a) == {"employed"}
    assert grouping.merges


def test_grouping_catalog_has_each_requested_partition():
    catalog = groupings.grouping_catalog(household_type_available=False)
    assert len(catalog) == 13
    assert catalog["day_mode_group_x_category"] == ("day_mode_group", "population")
    assert catalog["category_x_density_x_income"] == (
        "population",
        "density",
        "income",
    )
    assert "household_type" not in catalog
    assert "household_type" in groupings.grouping_catalog(household_type_available=True)


def test_grouping_days_read_only_scoped_cache_and_harmonised_attributes(tmp_path):
    cache = modes_cache.SurveyCache(tmp_path)
    with duckdb.connect() as con:
        con.execute(
            """COPY (SELECT * FROM (VALUES
              ('d1','p1','h1',2.0,30.0,'30','employed','q1','car_driver'),
              ('d2','p2','h2',1.0,10.0,'60','retired','q2','walking_only')
            ) t(day_id,ident_ind,ident_men,pond_jour,total_time_min,age_band,
                population_category,income_quintile,day_mode_group))
            TO ? (FORMAT PARQUET)""",
            [str(cache.days(scope.REFERENCE_SCOPE))],
        )
        con.execute(
            """COPY (SELECT * FROM (VALUES
              ('d1',9.1), ('d1',2.1), ('d2',2.1)
            ) t(day_id,motive))
            TO ? (FORMAT PARQUET)""",
            [str(cache.trips(scope.REFERENCE_SCOPE))],
        )
    sample = groupings.read_grouping_days(
        cache,
        scope.REFERENCE_SCOPE,
        income={"p1": "q1", "p2": "q2"},
        density={"p1": "dense", "p2": "sparse"},
        vehicles={"h1": "1", "h2": "0"},
    )
    assert sample.attributes["day_purpose"].tolist() == ["work_study", "other"]
    assert sample.attributes["age_band"].tolist() == ["30", "60"]
    assert sample.attributes["vehicles"].tolist() == ["1", "0"]
    assert sample.minutes.tolist() == [30, 10]


def test_missing_cached_trips_do_not_silently_remove_a_day(tmp_path):
    cache = modes_cache.SurveyCache(tmp_path)
    with duckdb.connect() as con:
        con.execute(
            """COPY (SELECT 'd1' day_id, 'p1' ident_ind, 'h1' ident_men,
              1.0 pond_jour, 10.0 total_time_min, '30' age_band,
              'employed' population_category, 'q1' income_quintile,
              'walking_only' day_mode_group)
            TO ? (FORMAT PARQUET)""",
            [str(cache.days(scope.REFERENCE_SCOPE))],
        )
        con.execute(
            """COPY (SELECT 'other' day_id, 2.1 motive)
            TO ? (FORMAT PARQUET)""",
            [str(cache.trips(scope.REFERENCE_SCOPE))],
        )
    with pytest.raises(ValueError, match="missing scoped trips"):
        groupings.read_grouping_days(
            cache,
            scope.REFERENCE_SCOPE,
            income={"p1": "q1"},
            density={"p1": "dense"},
            vehicles={"h1": "0"},
        )


def test_scope_evaluation_has_all_partitions_and_suppresses_daytable(merge_config):
    a = groupings.GroupingDays(
        person=np.array(["p1", "p2"]),
        household=np.array(["h1", "h2"]),
        weights=np.ones(2),
        minutes=np.array([10.0, 30.0]),
        attributes={
            "population": np.array(["employed", "retired"]),
            "age_band": np.array(["30", "60"]),
            "density": np.array(["dense", "sparse"]),
            "income": np.array(["q1", "q5"]),
            "vehicles": np.array(["1", "0"]),
            "day_purpose": np.array(["work_study", "other"]),
            "day_mode_group": np.array(["car_driver", "walking_only"]),
        },
    )
    draws = modes.Draws(a.household, np.ones((20, 2)), seed=0)
    selected = scope.Scope.parse("round-dest-daytable")
    result = groupings.evaluate_groupings(
        a,
        a,
        draws,
        draws,
        selected=selected,
        config=merge_config,
        minimum_n=1,
        margins=(0.15, 0.10),
        timings={},
    )
    assert len(result) == 13
    assert all(item.summary["scope"] == selected.id for item in result.values())
    assert all(np.isnan(item.summary["mean_abs_log_ratio"]) for item in result.values())
    assert all("not compared" in item.summary["status"] for item in result.values())


def test_fixed_counterfactual_reproduces_unchanged_cell_distributions(merge_config):
    a = groupings.GroupingDays(
        person=np.array(["p1", "p2", "p3", "p4"]),
        household=np.array(["h1", "h2", "h3", "h4"]),
        weights=np.ones(4),
        minutes=np.array([10.0, 20.0, 50.0, 60.0]),
        attributes={"population": np.array(["a", "a", "b", "b"])},
    )
    b = groupings.GroupingDays(
        person=a.person,
        household=a.household,
        weights=np.array([3.0, 3.0, 1.0, 1.0]),
        minutes=a.minutes,
        attributes=a.attributes,
    )
    partition = groupings.prepare_grouping(
        a, b, ("population",), config=merge_config, minimum_n=2
    )
    draws = modes.Draws(a.household, np.ones((20, 4)), seed=0)
    result = groupings.counterfactual_statistics(partition, draws, draws, compare=True)
    assert result["observed_2019"] == pytest.approx(25.0)
    assert result["predicted_2019"] == pytest.approx(25.0)
    assert result["observed_over_predicted"] == pytest.approx(1.0)
    assert result["ratio_low"] == pytest.approx(1.0)
    assert result["ratio_high"] == pytest.approx(1.0)
    assert result["mix_term"] == pytest.approx(-10.0)
    assert result["ks_d"] == pytest.approx(0.0)
    assert result["ks_low"] == pytest.approx(0.0)
    assert result["ks_high"] == pytest.approx(0.0)
    assert result["predicted_deciles"] == pytest.approx(result["observed_deciles"])


def test_fixed_counterfactual_daytable_is_not_compared(merge_config):
    a = groupings.GroupingDays(
        person=np.array(["p1", "p2"]),
        household=np.array(["h1", "h2"]),
        weights=np.ones(2),
        minutes=np.array([10.0, 30.0]),
        attributes={},
    )
    partition = groupings.prepare_grouping(a, a, (), config=merge_config, minimum_n=1)
    draws = modes.Draws(a.household, np.ones((20, 2)), seed=0)
    result = groupings.counterfactual_statistics(partition, draws, draws, compare=False)
    assert result["observed_2019"] == pytest.approx(20)
    assert np.isnan(result["predicted_2019"])
    assert np.isnan(result["ks_d"])
    assert np.isnan(result["observed_over_predicted"])


def test_fixed_counterfactual_reports_missing_cell_parent_share(merge_config):
    a = groupings.GroupingDays(
        person=np.array(["p1", "p2"]),
        household=np.array(["h1", "h2"]),
        weights=np.ones(2),
        minutes=np.array([10.0, 30.0]),
        attributes={
            "day_mode_group": np.array(["car_driver", "car_driver"]),
            "population": np.array(["employed", "employed"]),
        },
    )
    b = groupings.GroupingDays(
        person=a.person,
        household=a.household,
        weights=a.weights,
        minutes=a.minutes,
        attributes={
            "day_mode_group": a.attributes["day_mode_group"],
            "population": np.array(["retired", "retired"]),
        },
    )
    partition = groupings.prepare_grouping(
        a,
        b,
        ("day_mode_group", "population"),
        config=merge_config,
        minimum_n=2,
    )
    draws = modes.Draws(a.household, np.ones((20, 2)), seed=0)
    result = groupings.counterfactual_statistics(partition, draws, draws, compare=True)
    assert result["fallback_share"] == pytest.approx(1.0)
    assert result["predicted_2019"] == pytest.approx(20.0)
    assert result["ks_d"] == pytest.approx(0.0)


def test_person_mode_use_and_time_decomposition_with_zero_days():
    households = np.array(["h1", "h2", "h3"])
    a = groupings.PersonModeData(
        roster_household=households,
        roster_weight=np.ones(3),
        day_household=households,
        day_weight=np.ones(3),
        is_open=np.array([False, False, False]),
        minutes=np.array([[10.0, 0], [0, 20.0], [0, 0]]),
        used=np.array([[True, False], [False, True], [False, False]]),
        modes=("walk", "car"),
    )
    b = groupings.PersonModeData(
        roster_household=households,
        roster_weight=np.ones(3),
        day_household=households,
        day_weight=np.ones(3),
        is_open=np.array([False, False, False]),
        minutes=np.array([[20.0, 0], [0, 30.0], [0, 10.0]]),
        used=np.array([[True, False], [False, True], [False, True]]),
        modes=("walk", "car"),
    )
    draws = modes.Draws(households, np.ones((20, 3)), seed=0)
    result = groupings.person_mode_statistics(
        a, b, draws, draws, compare=True, minimum_n=1
    )
    assert result["rows"][0]["use_2008"] == pytest.approx(1 / 3)
    assert result["rows"][1]["use_2019"] == pytest.approx(2 / 3)
    assert result["rows"][1]["user_minutes_2019"] == pytest.approx(20)
    assert result["use_effect"] == pytest.approx(20 / 3)
    assert result["time_effect"] == pytest.approx(10 / 3)
    assert result["observed_2008"] == pytest.approx(10)
    assert result["observed_2019"] == pytest.approx(20)
    assert result["predicted_2019"] == pytest.approx(50 / 3)
    assert result["use_effect_low"] == pytest.approx(20 / 3)
    assert result["time_effect_high"] == pytest.approx(10 / 3)
    assert result["ks_d"] == pytest.approx(1 / 3)


def test_person_mode_daytable_keeps_levels_but_suppresses_change():
    households = np.array(["h1", "h2"])
    data = groupings.PersonModeData(
        roster_household=households,
        roster_weight=np.ones(2),
        day_household=households,
        day_weight=np.ones(2),
        is_open=np.zeros(2, dtype=bool),
        minutes=np.array([[10.0], [0.0]]),
        used=np.array([[True], [False]]),
        modes=("walk",),
    )
    draws = modes.Draws(households, np.ones((20, 2)), seed=0)
    result = groupings.person_mode_statistics(
        data, data, draws, draws, compare=False, minimum_n=1
    )
    assert result["rows"][0]["use_2019"] == pytest.approx(0.5)
    assert result["rows"][0]["user_minutes_2019"] == pytest.approx(10)
    assert np.isnan(result["use_effect"])
    assert np.isnan(result["predicted_2019"])


def test_person_mode_excludes_open_day_from_denominator():
    households = np.array(["h1", "h2", "h3"])
    data = groupings.PersonModeData(
        roster_household=households,
        roster_weight=np.ones(3),
        day_household=households,
        day_weight=np.ones(3),
        is_open=np.array([False, False, True]),
        minutes=np.array([[10.0], [0.0], [0.0]]),
        used=np.array([[True], [False], [False]]),
        modes=("walk",),
    )
    draws = modes.Draws(households, np.ones((20, 3)), seed=0)
    result = groupings.person_mode_statistics(
        data, data, draws, draws, compare=True, minimum_n=1
    )
    assert result["rows"][0]["use_2008"] == pytest.approx(0.5)
    assert result["observed_2008"] == pytest.approx(5.0)
    assert result["ks_d"] == pytest.approx(0)


def test_person_mode_cache_loader_preserves_zero_days_and_open_days(tmp_path):
    cache = modes_cache.SurveyCache(tmp_path)
    with duckdb.connect() as con:
        con.execute(
            """COPY (SELECT * FROM (VALUES
              ('h1', 1.0), ('h2', 1.0), ('h3', 1.0)
            ) t(ident_men, weight)) TO ? (FORMAT PARQUET)""",
            [str(cache.roster)],
        )
        con.execute(
            """COPY (SELECT * FROM (VALUES
              ('d1', 'h1', 1.0, TRUE), ('d2', 'h2', 1.0, FALSE)
            ) t(day_id,ident_men,pond_jour,is_round)) TO ? (FORMAT PARQUET)""",
            [str(cache.day_base)],
        )
        con.execute(
            """COPY (SELECT 'd1' day_id, 'walk' mode7, 10.0 duration_min)
            TO ? (FORMAT PARQUET)""",
            [str(cache.trips(scope.REFERENCE_SCOPE))],
        )
    data = groupings.read_person_modes(cache, scope.REFERENCE_SCOPE)
    assert data.roster_weight.sum() == pytest.approx(3)
    assert data.is_open.tolist() == [False, True]
    walk = data.modes.index("walk")
    assert data.minutes[:, walk].tolist() == [10, 0]
    assert data.used[:, walk].tolist() == [True, False]
