"""Synthetic tests for the income supplement."""

import duckdb
import numpy as np
import pytest
from mobgrid.budget import entd2008, modes_cache, scope, zahavi_income, zahavi_modes


def test_income_uses_existing_entd_quintiles_and_preserves_unknown():
    with duckdb.connect() as con:
        con.execute(
            """CREATE TABLE k_individu AS
            SELECT * FROM (VALUES
                ('p1', 'h1', 1.0), ('p2', 'h2', 1.0),
                ('p3', 'h3', 1.0)
            ) t(IDENT_IND, IDENT_MEN, PONDKI)"""
        )
        con.execute(
            """CREATE TABLE q_tcm_menage AS
            SELECT * FROM (VALUES
                ('h1', 'Moins de 400 euros', 1.0),
                ('h2', 'De 1 200 euros a moins de 1 500 euros', 2.0),
                ('h3', NULL, 1.0)
            ) t(IDENT_MEN, TrancheRevenuMensuel, NBUC)"""
        )
        labels = zahavi_income.income_by_person(con, entd2008)
        assert labels == {"p1": "q3", "p2": "q5", "p3": "unknown"}


def test_unknown_income_shares_use_distinct_bases():
    respondents, day_weight = zahavi_income.unknown_income_shares(
        np.array(["q1", "unknown", "unknown"]),
        np.array(["q1", "unknown", "unknown"]),
        np.array([3.0, 1.0, 2.0]),
    )
    assert respondents == pytest.approx(2 / 3)
    assert day_weight == pytest.approx(0.5)


def test_entd_household_car_count_reads_cp1252_and_keeps_unknown(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text(
        "idENT_MEN;V1_JNBVEH;label\n00001;0;véhicule\n00002;1;x\n00003;3;x\n00004;;x\n",
        encoding="cp1252",
    )
    actual = zahavi_income.load_entd_household_cars(source, tmp_path / "scratch")
    assert actual == {"00001": "0", "00002": "1", "00003": "2+", "00004": "unknown"}


def test_entd_household_car_count_rejects_duplicate_households(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("idENT_MEN;V1_JNBVEH\n1;0\n1;1\n", encoding="cp1252")
    with pytest.raises(ValueError, match="Duplicate"):
        zahavi_income.load_entd_household_cars(source, tmp_path / "scratch")


def test_emp_household_car_count_preserves_unknown_and_rejects_duplicates():
    with duckdb.connect() as con:
        con.execute(
            """CREATE TABLE q_menage AS SELECT * FROM (VALUES
              ('h1', 0), ('h2', 1), ('h3', 4), ('h4', NULL)
            ) t(IDENT_MEN, JNBVEH)"""
        )
        assert zahavi_income.emp_household_cars(con) == {
            "h1": "0",
            "h2": "1",
            "h3": "2+",
            "h4": "unknown",
        }
        con.execute("INSERT INTO q_menage VALUES ('h1', 2)")
        with pytest.raises(ValueError, match="Duplicate"):
            zahavi_income.emp_household_cars(con)


def test_income_day_and_person_levels_include_zero_and_remove_open_days():
    people = zahavi_income.People(
        person=np.array(["p1", "p2", "p3"]),
        household=np.array(["h1", "h2", "h3"]),
        income=np.array(["q1", "q1", "q1"]),
        weight=np.array([5.0, 5.0, 5.0]),
    )
    days = zahavi_income.Days(
        person=np.array(["p1", "p2"]),
        household=np.array(["h1", "h2"]),
        income=np.array(["q1", "q1"]),
        weight=np.array([5.0, 5.0]),
        minutes=np.array([30.0, 90.0]),
        is_open=np.array([False, True]),
        has_trips=np.array([True, False]),
    )
    draws = zahavi_modes.Draws(
        households=np.array(["h1", "h2", "h3"]),
        multipliers=np.array([[1, 1, 1], [1, 0, 2]]),
        seed=0,
    )
    results = zahavi_income.income_metrics(people, days, draws)
    n_day, day = results["travel_day", "q1"]
    n_person, person = results["person", "q1"]
    assert (n_day, n_person) == (1, 3)
    assert day.value == 30.0
    assert person.value == 15.0
    assert person.replicates == pytest.approx([15.0, 10.0])


def test_cached_income_joins_full_roster_and_scope_days(tmp_path):
    cache = modes_cache.SurveyCache(tmp_path)
    with duckdb.connect() as con:
        con.execute(
            """COPY (SELECT * FROM (VALUES
              ('p1','h1','employed',5.0), ('p2','h2','retired',5.0),
              ('p3','h3','retired',5.0)
            ) t(ident_ind,ident_men,population_category,weight))
            TO ? (FORMAT PARQUET)""",
            [str(cache.roster)],
        )
        con.execute(
            """COPY (SELECT * FROM (VALUES
              ('d1','p1','h1',5.0,TRUE), ('d2','p2','h2',5.0,FALSE)
            ) t(day_id,ident_ind,ident_men,pond_jour,is_round))
            TO ? (FORMAT PARQUET)""",
            [str(cache.day_base)],
        )
        con.execute(
            """COPY (SELECT 'd1' day_id, 30.0 total_time_min, 'q1' income_quintile)
            TO ? (FORMAT PARQUET)""",
            [str(cache.days(scope.REFERENCE_SCOPE))],
        )
        con.execute(
            """COPY (SELECT 'd1' day_id, 'lundi' described_weekday_name)
            TO ? (FORMAT PARQUET)""",
            [str(cache.trips(scope.REFERENCE_SCOPE))],
        )
    loaded = zahavi_income.read_cached_income(
        cache,
        scope.REFERENCE_SCOPE,
        income={"p1": "q1", "p2": "q2", "p3": "unknown"},
        density={"p1": "dense", "p2": "sparse", "p3": "sparse"},
        cars={"h1": "0", "h2": "1", "h3": "2+"},
    )
    assert loaded.people.income.tolist() == ["q1", "q2", "unknown"]
    assert loaded.days.minutes.tolist() == [30, 0]
    assert loaded.days.is_open.tolist() == [False, True]
    assert loaded.days.has_trips.tolist() == [True, False]
    assert loaded.weekday.tolist() == ["lundi", ""]
    assert loaded.cars.tolist() == ["0", "1", "2+"]


def test_quintile_density_table_marks_small_cells_and_hides_below_minimum():
    people = zahavi_income.People(
        np.array(["p1", "p2", "p3"]),
        np.array(["h1", "h2", "h3"]),
        np.array(["q1", "q1", "q1"]),
        np.array([5.0, 5.0, 5.0]),
    )
    days = zahavi_income.Days(
        people.person,
        people.household,
        people.income,
        people.weight,
        np.array([10.0, 20.0, 40.0]),
        np.array([False, False, False]),
        np.array([True, True, True]),
    )
    data = zahavi_income.CachedIncome(
        people,
        days,
        np.array(["employed"] * 3),
        np.array(["dense", "dense", "sparse"]),
        np.array(["1"] * 3),
        np.array(["lundi"] * 3),
    )
    draws = zahavi_modes.Draws(
        households=people.household, multipliers=np.ones((20, 3)), seed=0
    )
    rows = zahavi_income.density_rows(
        data, data, draws, draws, minimum_n=2, caution_n=3, margins=(0.15, 0.1)
    )
    dense = next(
        r
        for r in rows
        if r["basis"] == "person" and r["quintile"] == "q1" and r["density"] == "dense"
    )
    sparse = next(
        r
        for r in rows
        if r["basis"] == "person" and r["quintile"] == "q1" and r["density"] == "sparse"
    )
    assert dense["small_cell"] is True and dense["ratio"] == pytest.approx(1.0)
    assert sparse["small_cell"] is True and np.isnan(sparse["mean_2008"])


def test_gap_change_interval_uses_paired_replicates():
    q1_2008 = zahavi_income.Metric(10.0, np.array([9.0, 10.0, 11.0]))
    q5_2008 = zahavi_income.Metric(20.0, np.array([19.0, 20.0, 21.0]))
    q1_2019 = zahavi_income.Metric(11.0, np.array([12.0, 10.0, 11.0]))
    q5_2019 = zahavi_income.Metric(23.0, np.array([24.0, 24.0, 23.0]))
    change = zahavi_income.gap_change(q1_2008, q5_2008, q1_2019, q5_2019)
    assert change.value == pytest.approx(2.0)
    np.testing.assert_array_equal(change.replicates, [2.0, 4.0, 2.0])
    assert zahavi_modes._interval(change.replicates) == pytest.approx((2.0, 3.9))


def test_level_rows_report_ratio_and_suppress_small_and_unknown():
    a = {
        ("person", "q1"): (60, zahavi_income.Metric(10, np.full(20, 10.0))),
        ("person", "q2"): (49, zahavi_income.Metric(20, np.full(20, 20.0))),
        ("person", "unknown"): (60, zahavi_income.Metric(15, np.full(20, 15.0))),
    }
    b = {
        ("person", "q1"): (80, zahavi_income.Metric(11, np.full(20, 11.0))),
        ("person", "q2"): (80, zahavi_income.Metric(25, np.full(20, 25.0))),
    }
    rows = zahavi_income.level_rows(a, b, minimum_n=50, margins=(0.15, 0.10))
    q1 = next(r for r in rows if r["basis"] == "person" and r["quintile"] == "q1")
    assert q1["ratio"] == pytest.approx(1.1)
    assert q1["verdict_15"] == "equivalent"
    q2 = next(r for r in rows if r["basis"] == "person" and r["quintile"] == "q2")
    assert np.isnan(q2["mean_2008"]) and np.isnan(q2["ratio"])
    unknown = next(
        r for r in rows if r["basis"] == "person" and r["quintile"] == "unknown"
    )
    assert unknown["mean_2008"] == 15
    assert np.isnan(unknown["mean_2019"]) and np.isnan(unknown["ratio"])


def test_gap_rows_use_paired_within_year_and_between_year_draws():
    a = {
        ("person", "q1"): (60, zahavi_income.Metric(10, np.array([9.0, 10.0, 11.0]))),
        ("person", "q5"): (60, zahavi_income.Metric(20, np.array([19.0, 20.0, 21.0]))),
    }
    b = {
        ("person", "q1"): (60, zahavi_income.Metric(11, np.array([12.0, 10.0, 11.0]))),
        ("person", "q5"): (60, zahavi_income.Metric(23, np.array([24.0, 24.0, 23.0]))),
    }
    rows = zahavi_income.gap_rows(a, b, minimum_n=50)
    diff = next(r for r in rows if r["basis"] == "person" and r["gap"] == "difference")
    assert diff["change"] == pytest.approx(2)
    assert (diff["change_ci_low"], diff["change_ci_high"]) == pytest.approx((2, 3.9))
    ratio = next(r for r in rows if r["basis"] == "person" and r["gap"] == "ratio")
    assert ratio["value_2008"] == pytest.approx(2)
    assert ratio["value_2019"] == pytest.approx(23 / 11)


def test_pooled_joint_reweighting_reproduces_target():
    cells_a = np.array([0, 0, 1, 2])
    cells_b = np.array([0, 1, 1, 2])
    weights_a = np.array([1.0, 1.0, 1.0, 1.0])
    weights_b = np.array([1.0, 1.0, 2.0, 2.0])
    adj_a, adj_b, target = zahavi_income.pooled_reweight(
        cells_a, weights_a, cells_b, weights_b
    )
    for cells, weights in ((cells_a, adj_a), (cells_b, adj_b)):
        actual = np.bincount(cells, weights=weights, minlength=3)
        np.testing.assert_allclose(actual / actual.sum(), target)


def test_pooled_reweight_rejects_empty_common_support():
    with pytest.raises(ValueError, match="support"):
        zahavi_income.pooled_reweight(
            np.array([0]), np.array([1.0]), np.array([1]), np.array([1.0])
        )


def test_joint_cells_collapse_unsupported_cars_within_density():
    a = np.array([["q1", "dense", "0"], ["q1", "dense", "1"]])
    b = np.array([["q1", "dense", "0"], ["q1", "dense", "2+"]])
    first, second, collapsed = zahavi_income.collapse_joint_cells(a, b)
    assert first.tolist() == second.tolist() == ["q1|dense|all", "q1|dense|all"]
    assert set(collapsed) == {
        ("q1|dense|0", "q1|dense|all"),
        ("q1|dense|1", "q1|dense|all"),
        ("q1|dense|2+", "q1|dense|all"),
    }


def test_joint_cells_collapse_density_when_one_year_lacks_density():
    a = np.array([["q1", "dense", "0"], ["q1", "sparse", "0"]])
    b = np.array([["q1", "dense", "0"]])
    first, second, collapsed = zahavi_income.collapse_joint_cells(a, b)
    assert first.tolist() == ["q1|all|all", "q1|all|all"]
    assert second.tolist() == ["q1|all|all"]
    assert len(collapsed) == 2


def test_joint_cells_reject_quintile_without_common_support():
    with pytest.raises(ValueError, match="quintile"):
        zahavi_income.collapse_joint_cells(
            np.array([["q1", "dense", "0"]]), np.array([["q2", "dense", "0"]])
        )


def test_reweighted_metrics_use_pooled_mix_for_each_quintile_and_basis():
    def sample(prefix, weights, minutes):
        people = zahavi_income.People(
            np.array([f"{prefix}{i}" for i in range(4)]),
            np.array([f"{prefix}h{i}" for i in range(4)]),
            np.array(["q1", "q1", "q5", "q5"]),
            np.array(weights, dtype=float),
        )
        days = zahavi_income.Days(
            people.person,
            people.household,
            people.income,
            people.weight,
            np.array(minutes, dtype=float),
            np.zeros(4, dtype=bool),
            np.ones(4, dtype=bool),
        )
        return zahavi_income.CachedIncome(
            people,
            days,
            np.array(["employed"] * 4),
            np.array(["dense", "sparse", "dense", "sparse"]),
            np.array(["1"] * 4),
            np.array(["lundi"] * 4),
        )

    a = sample("a", [3, 1, 3, 1], [10, 30, 20, 40])
    b = sample("b", [1, 3, 1, 3], [20, 40, 30, 50])
    da = zahavi_modes.Draws(a.people.household, np.ones((20, 4)), 0)
    db = zahavi_modes.Draws(b.people.household, np.ones((20, 4)), 0)
    ma, mb, collapsed = zahavi_income.reweighted_metrics(a, b, da, db)
    assert collapsed == []
    for basis in ("travel_day", "person"):
        assert ma[basis, "q1"][1].value == pytest.approx(20)
        assert mb[basis, "q1"][1].value == pytest.approx(30)
        assert ma[basis, "q5"][1].value == pytest.approx(30)
        assert mb[basis, "q5"][1].value == pytest.approx(40)


def test_wls_matches_lstsq_with_sqrt_weights():
    x = np.array([[1.0, 0.0], [1.0, 1.0], [1.0, 2.0]])
    y = np.array([1.0, 3.0, 4.0])
    weights = np.array([1.0, 4.0, 2.0])
    expected = np.linalg.lstsq(
        x * np.sqrt(weights)[:, None], y * np.sqrt(weights), rcond=None
    )[0]
    np.testing.assert_allclose(
        zahavi_income.weighted_least_squares(x, y, weights), expected
    )


def test_wls_bootstrap_uses_shared_household_multiplicities():
    x = np.array([[1.0, 0.0], [1.0, 1.0], [1.0, 2.0], [1.0, 3.0]])
    y = np.array([1.0, 2.0, 2.5, 5.0])
    weights = np.array([1.0, 2.0, 1.0, 1.0])
    households = np.array(["a", "a", "b", "c"])
    draws = zahavi_modes.Draws(
        households=np.array(["a", "b", "c"]),
        multipliers=np.array([[1, 1, 1], [1, 2, 0], [0, 0, 3]]),
        seed=0,
    )
    point, reps = zahavi_income.bootstrap_wls(x, y, weights, households, draws)
    np.testing.assert_allclose(
        point, zahavi_income.weighted_least_squares(x, y, weights)
    )
    np.testing.assert_allclose(
        reps[1], zahavi_income.weighted_least_squares(x, y, weights * [1, 1, 2, 0])
    )
    assert np.isnan(reps[2]).all()


def test_pooled_design_uses_q1_baseline_and_survey_interactions():
    design, names = zahavi_income.regression_design(
        income=np.array(["q1", "q5", "q1", "q5"]),
        population=np.array(["retired", "retired", "retired", "retired"]),
        weekday=np.array(["lundi", "lundi", "lundi", "lundi"]),
        survey=np.array(["2008", "2008", "2019", "2019"]),
    )
    assert names == ["intercept", "income:q5", "survey:2019", "survey:2019*income:q5"]
    np.testing.assert_array_equal(
        design,
        np.array([[1, 0, 0, 0], [1, 1, 0, 0], [1, 0, 1, 0], [1, 1, 1, 1]]),
    )


def test_regression_effects_are_log_coefficients_as_percent_differences():
    x = np.array([[1.0, 0.0], [1.0, 0.0], [1.0, 1.0], [1.0, 1.0]])
    y = np.log(np.array([10.0, 10.0, 20.0, 20.0]))
    household = np.array(["a", "b", "c", "d"])
    draws = zahavi_modes.Draws(
        households=household, multipliers=np.ones((20, 4)), seed=0
    )
    rows = zahavi_income.regression_effects(
        x, ["intercept", "income:q5"], y, np.ones(4), household, draws
    )
    assert rows[0]["term"] == "income:q5"
    assert rows[0]["percent"] == pytest.approx(100)
    assert rows[0]["ci_low"] == pytest.approx(100)
    assert rows[0]["ci_high"] == pytest.approx(100)
