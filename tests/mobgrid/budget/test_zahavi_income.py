"""Synthetic tests for the income supplement."""

import csv

import duckdb
import numpy as np
import pyarrow as pa
import pytest
import yaml
from mobgrid.budget import (
    emp2019,
    entd2008,
    modes_cache,
    scope,
    zahavi_income,
    zahavi_modes,
)

LEVEL_ORDER = {
    "income": ["q1", "q2", "q3", "q4", "q5"],
    "population": ["employed", "retired"],
    "weekday": ["lundi", "mardi"],
    "density": ["dense", "sparse"],
    "cars": ["0", "1", "2+"],
}


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


def test_entd_household_vehicle_count_sums_cars_and_vul_camper(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text(
        "idENT_MEN;V1_JNBVEH;V1_JNBCCVUL;PONDV1;label\n"
        "00001;0;0;1;véhicule\n00002;1;0;1;x\n"
        "00003;0;2;2;x\n00004;1;1;1;x\n00005;1;;1;x\n",
        encoding="cp1252",
    )
    actual = zahavi_income.load_entd_household_vehicles(source, tmp_path / "scratch")
    assert actual.classes == {
        "00001": "0",
        "00002": "1",
        "00003": "2+",
        "00004": "2+",
        "00005": "unknown",
    }
    shares = zahavi_income.household_vehicle_share_rows(2008, actual)
    assert [row["share_percent"] for row in shares] == pytest.approx(
        [100 / 6, 100 / 6, 50, 100 / 6]
    )


def test_entd_household_car_count_rejects_duplicate_households(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text(
        "idENT_MEN;V1_JNBVEH;V1_JNBCCVUL;PONDV1\n1;0;0;1\n1;1;0;1\n",
        encoding="cp1252",
    )
    with pytest.raises(ValueError, match="Duplicate"):
        zahavi_income.load_entd_household_cars(source, tmp_path / "scratch")


def test_emp_household_car_count_preserves_unknown_and_rejects_duplicates():
    with duckdb.connect() as con:
        con.execute(
            """CREATE TABLE q_menage AS SELECT * FROM (VALUES
              ('h1', 0, 2, 1.0), ('h2', 1, 2, 1.0),
              ('h3', 4, 2, 1.0), ('h4', NULL, 2, 1.0)
            ) t(IDENT_MEN, JNBVEH, JNBVHS, pond_menC)"""
        )
        assert zahavi_income.emp_household_cars(con) == {
            "h1": "0",
            "h2": "1",
            "h3": "2+",
            "h4": "unknown",
        }
        con.execute("INSERT INTO q_menage VALUES ('h1', 2, 2, 1.0)")
        with pytest.raises(ValueError, match="Duplicate"):
            zahavi_income.emp_household_cars(con)


def test_emp_household_vehicle_count_subtracts_out_of_use_counts():
    with duckdb.connect() as con:
        con.execute(
            """CREATE TABLE q_menage AS SELECT * FROM (VALUES
              ('h0', 0, 2, NULL, NULL, NULL, 1.0),
              ('h1', 1, 2, NULL, NULL, NULL, 1.0),
              ('h2', 4, 1, 1, 1, 0, 2.0),
              ('h3', 3, 1, 0, 1, 0, 1.0),
              ('h4', 2, 1, NULL, 0, 0, 1.0)
            ) t(IDENT_MEN, JNBVEH, JNBVHS, JNBVPHS, JNBCCHS,
                JNBVULHS, pond_menC)"""
        )
        vehicles = zahavi_income.emp_household_vehicles(con)
    assert vehicles.classes == {
        "h0": "0",
        "h1": "1",
        "h2": "2+",
        "h3": "2+",
        "h4": "unknown",
    }
    assert vehicles.out_of_use_share is None


def test_emp_fallback_reports_weighted_out_of_use_household_share():
    with duckdb.connect() as con:
        con.execute(
            """CREATE TABLE q_menage AS SELECT * FROM (VALUES
              ('h1', 2, 1, 1.0), ('h2', 1, 2, 3.0)
            ) t(IDENT_MEN, JNBVEH, JNBVHS, pond_menC)"""
        )
        vehicles = zahavi_income.emp_household_vehicles(con)
    assert vehicles.classes == {"h1": "2+", "h2": "1"}
    assert vehicles.out_of_use_share == pytest.approx(0.25)


def test_emp_attributes_reuse_income_and_density_proxy():
    with duckdb.connect() as con:
        con.execute(
            """CREATE TABLE k_individu AS SELECT * FROM (VALUES
              ('p1', 1.0), ('p2', 1.0)
            ) t(IDENT_IND, pond_indC)"""
        )
        con.execute(
            """CREATE TABLE tcm_ind AS SELECT * FROM (VALUES
              ('p1', 'h1'), ('p2', 'h2')
            ) t(IDENT_IND, IDENT_MEN)"""
        )
        con.execute("CREATE TABLE tcm_ind_kish AS SELECT IDENT_IND FROM tcm_ind")
        con.execute(
            """CREATE TABLE tcm_men AS SELECT * FROM (VALUES
              ('h1', 1, 'C', '7', 1), ('h2', 9, 'H', '0', 4)
            ) t(IDENT_MEN, decile_rev_uc, STATUTCOM_UU_RES,
                TUU2017_RES, DENSITECOM_RES)"""
        )
        income, density = zahavi_income.respondent_attributes(con, emp2019)
        assert income == {"p1": "q3", "p2": "q5"}
        assert density == {"p1": "dense", "p2": "very_sparse"}
        con.execute("UPDATE tcm_men SET decile_rev_uc = NULL WHERE IDENT_MEN = 'h1'")
        with pytest.raises(ValueError, match="missing imputed income"):
            zahavi_income.respondent_attributes(con, emp2019)


def test_emp_attribute_extraction_uses_only_temporary_output(
    synthetic_emp_zip, tmp_path
):
    income, density, vehicles = zahavi_income.extract_attributes(
        emp2019, synthetic_emp_zip, tmp_path / "scratch"
    )
    assert len(income) == len(density) == len(vehicles.classes) == 13
    assert density["1"] == "dense"
    assert vehicles.classes["M1"] == "0"
    assert set(income.values()) <= {"q1", "q2", "q3", "q4", "q5"}


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


def test_ratio_interval_requires_sufficient_valid_paired_draws():
    a = {("person", "q1"): (60, zahavi_income.Metric(10, np.full(20, 10.0)))}
    draws = np.full(20, 11.0)
    draws[:2] = np.nan
    b = {("person", "q1"): (60, zahavi_income.Metric(11, draws))}
    rows = zahavi_income.level_rows(a, b, minimum_n=50, margins=(0.15, 0.1))
    q1 = next(r for r in rows if r["basis"] == "person" and r["quintile"] == "q1")
    assert q1["ratio"] == pytest.approx(1.1)
    assert np.isnan(q1["ratio_ci_low"]) and q1["verdict_15"] == ""
    draws[1] = 11
    rows = zahavi_income.level_rows(a, b, minimum_n=50, margins=(0.15, 0.1))
    q1 = next(r for r in rows if r["basis"] == "person" and r["quintile"] == "q1")
    assert q1["ratio_ci_low"] == pytest.approx(1.1)


def test_insufficient_intervals_are_warned_once_per_level_group(caplog):
    draws = np.full(20, 10.0)
    draws[:2] = np.nan
    metric = zahavi_income.Metric(10, draws)
    samples = {("person", q): (60, metric) for q in ("q1", "q2")}
    rows = zahavi_income.level_rows(samples, samples, minimum_n=50, margins=(0.15, 0.1))
    warnings = [r.message for r in caplog.records if r.levelname == "WARNING"]
    assert len(warnings) == 1
    assert "6" in warnings[0] and "18/20" in warnings[0]
    assert np.isnan(next(r for r in rows if r["quintile"] == "q1")["ci_2008_low"])


def test_regression_warns_once_and_preserves_coefficient_specific_intervals(caplog):
    design = np.array([[1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [1.0, 0.0, 1.0]])
    multipliers = np.ones((20, 3))
    multipliers[:2, 1] = 0
    draws = zahavi_income.Draws(np.array(["a", "b", "c"]), multipliers, 1)
    rows = zahavi_income.regression_effects(
        design,
        ["intercept", "income:q2", "income:q3"],
        np.array([1.0, 2.0, 3.0]),
        np.ones(3),
        np.array(["a", "b", "c"]),
        draws,
    )
    warnings = [r.message for r in caplog.records if r.levelname == "WARNING"]
    assert len(warnings) == 1
    assert "2" in warnings[0] and "18/20" in warnings[0]
    assert np.isnan(rows[0]["ci_low"]) and np.isfinite(rows[1]["ci_low"])


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


def test_sparse_joint_cells_pool_cars_then_sparse_density():
    cells = np.array(
        [
            ["q1", "dense", "1"],
            ["q1", "dense", "2+"],
            ["q1", "sparse", "0"],
            ["q1", "very_sparse", "0"],
        ]
    )
    people = np.array(["p1", "p2", "p3", "p4"])
    mapped_a, mapped_b, collapsed, unresolved = (
        zahavi_income.collapse_sparse_joint_cells(
            cells, people, cells, people, minimum_n=2
        )
    )
    assert mapped_a.tolist() == mapped_b.tolist()
    assert mapped_a.tolist() == [
        "q1|dense|1+",
        "q1|dense|1+",
        "q1|sparse+very_sparse|0",
        "q1|sparse+very_sparse|0",
    ]
    assert ("q1|dense|2+", "q1|dense|1+") in collapsed
    assert unresolved == []


def test_joint_cells_report_unresolved_small_group_without_inventing_a_merge():
    cells = np.array([["q1", "dense", "0"]])
    people = np.array(["p1"])
    _, _, _, unresolved = zahavi_income.collapse_sparse_joint_cells(
        cells, people, cells, people, minimum_n=2
    )
    assert unresolved == ["q1|dense|0"]


def test_draw_reweighting_rescales_common_support_below_strict_loss_limit():
    factors_a, factors_b, lost, accepted = zahavi_income.reweight_draw_target(
        np.array([99.0, 1.0]), np.array([100.0, 0.0]), max_lost_share=0.01
    )
    assert accepted and lost == pytest.approx(0.005)
    np.testing.assert_allclose(np.array([0.99, 0.01]) * factors_a, [1.0, 0.0])
    np.testing.assert_allclose(np.array([1.0, 0.0]) * factors_b, [1.0, 0.0])
    _, _, lost, accepted = zahavi_income.reweight_draw_target(
        np.array([98.0, 2.0]), np.array([100.0, 0.0]), max_lost_share=0.01
    )
    assert lost == pytest.approx(0.01)
    assert not accepted


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
    ma, mb, collapsed = zahavi_income.reweighted_metrics(
        a, b, da, db, minimum_n=1, max_lost_share=0.01
    )
    assert collapsed == []
    for basis in ("travel_day", "person"):
        assert ma[basis, "q1"][1].value == pytest.approx(20)
        assert mb[basis, "q1"][1].value == pytest.approx(30)
        assert ma[basis, "q5"][1].value == pytest.approx(30)
        assert mb[basis, "q5"][1].value == pytest.approx(40)


def test_person_reweighting_collapses_cells_emptied_by_open_day():
    def sample(prefix, is_open):
        people = zahavi_income.People(
            np.array([f"{prefix}1", f"{prefix}2"]),
            np.array([f"{prefix}h1", f"{prefix}h2"]),
            np.array(["q1", "q1"]),
            np.array([5.0, 5.0]),
        )
        days = zahavi_income.Days(
            people.person,
            people.household,
            people.income,
            people.weight,
            np.array([10.0, 20.0]),
            np.array([False, is_open]),
            np.array([True, not is_open]),
        )
        return zahavi_income.CachedIncome(
            people,
            days,
            np.array(["employed"] * 2),
            np.array(["dense", "sparse"]),
            np.array(["1", "1"]),
            np.array(["lundi", "lundi"]),
        )

    a, b = sample("a", True), sample("b", False)
    da = zahavi_modes.Draws(a.people.household, np.ones((20, 2)), 0)
    db = zahavi_modes.Draws(b.people.household, np.ones((20, 2)), 0)
    support = []
    ma, mb, collapsed = zahavi_income.reweighted_metrics(
        a, b, da, db, minimum_n=1, max_lost_share=0.01, support=support
    )
    assert ma["person", "q1"][1].value == pytest.approx(10)
    assert mb["person", "q1"][1].value == pytest.approx(15)
    assert ("person", "q1|sparse|1", "q1|all|all") in collapsed
    absent = next(
        row
        for row in support
        if row["group"] == "reweight_input_travel_day"
        and row["term"] == "q1|sparse|1"
        and row["year"] == 2008
    )
    assert (absent["respondents"], absent["households"], absent["empty_draws"]) == (
        0,
        0,
        20,
    )


def test_reweighting_retains_draw_with_small_lost_target_share():
    def sample(prefix):
        people = zahavi_income.People(
            np.array([prefix + "1", prefix + "5"]),
            np.array([prefix + "a", prefix + "b"]),
            np.array(["q1", "q5"]),
            np.array([1.0, 99.0]),
        )
        days = zahavi_income.Days(
            people.person,
            people.household,
            people.income,
            people.weight,
            np.array([10.0, 30.0]),
            np.zeros(2, dtype=bool),
            np.ones(2, dtype=bool),
        )
        return zahavi_income.CachedIncome(
            people,
            days,
            np.array(["employed"] * 2),
            np.array(["dense"] * 2),
            np.array(["1"] * 2),
            np.array(["lundi"] * 2),
        )

    a, b = sample("a"), sample("b")
    da = zahavi_modes.Draws(a.people.household, np.array([[0, 1]]), 0)
    db = zahavi_modes.Draws(b.people.household, np.array([[1, 1]]), 0)
    audit = []
    ma, mb, _ = zahavi_income.reweighted_metrics(
        a, b, da, db, minimum_n=1, max_lost_share=0.01, draw_audit=audit
    )
    assert ma["travel_day", "q5"][1].replicates[0] == pytest.approx(30)
    assert mb["travel_day", "q5"][1].replicates[0] == pytest.approx(30)
    assert audit[0]["accepted"] and audit[0]["lost_target_share"] == pytest.approx(
        0.005
    )


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


def test_wls_keeps_estimable_coefficients_when_a_nuisance_level_is_empty():
    x = np.array(
        [
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [1.0, 1.0, 0.0],
            [1.0, 0.0, 1.0],
        ]
    )
    y = np.array([1.0, 1.0, 3.0, 3.0, 4.0])
    households = np.array(["a", "b", "c", "d", "e"])
    draws = zahavi_modes.Draws(households, np.array([[1, 1, 1, 1, 0]]), 0)
    _, reps = zahavi_income.bootstrap_wls(x, y, np.ones(5), households, draws)
    np.testing.assert_allclose(reps[0, :2], [1, 2])
    assert np.isnan(reps[0, 2])


def test_wls_retains_only_identifiable_coefficients_with_nonzero_collinearity():
    x = np.array(
        [
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
            [1.0, 0.0, 1.0],
        ]
    )
    households = np.array(["a", "b", "c", "d", "e"])
    draws = zahavi_modes.Draws(households, np.array([[1, 1, 1, 1, 0]]), 0)
    _, reps = zahavi_income.bootstrap_wls(
        x, np.array([1.0, 1.0, 3.0, 3.0, 4.0]), np.ones(5), households, draws
    )
    assert reps[0, 0] == pytest.approx(1)
    assert np.isnan(reps[0, 1:]).all()


def test_regression_levels_merge_using_both_years_and_keep_unknown_separate():
    a = {
        "person": np.array(["a1", "a2", "a3", "a4"]),
        "income": np.array(["q1", "q1", "q2", "unknown"]),
    }
    b = {"person": np.array(["b1", "b2", "b3"]), "income": np.array(["q1", "q2", "q2"])}
    merged, changes = zahavi_income.merge_regression_levels(
        [a, b], minimum_n=2, orders={"income": ["q1", "q2"]}
    )
    assert set(merged[0]["income"]) == {"q1+q2", "unknown"}
    assert set(merged[1]["income"]) == {"q1+q2"}
    assert ("income", "q1", "q1+q2") in changes
    assert ("income", "q2", "q1+q2") in changes


def test_support_counts_distinct_people_households_and_empty_draws():
    rows = zahavi_income.support_counts(
        person=np.array(["p1", "p1", "p2", "p3"]),
        household=np.array(["a", "a", "b", "c"]),
        values=np.array(["rare", "rare", "rare", "other"]),
        labels=("rare", "missing"),
        draws=zahavi_modes.Draws(
            households=np.array(["a", "b", "c"]),
            multipliers=np.array([[1, 0, 1], [0, 1, 1], [0, 0, 1]]),
            seed=0,
        ),
    )
    assert rows["rare"] == (2, 2, 1)
    assert rows["missing"] == (0, 0, 3)


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
    _, names = zahavi_income.regression_design(
        income=np.array(["q1", "unknown", "q1", "q5"]),
        population=np.array(["employed"] * 4),
        weekday=np.array(["lundi"] * 4),
        survey=np.array(["2008", "2008", "2019", "2019"]),
    )
    assert "income:unknown" in names
    assert "survey:2019*income:unknown" not in names


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


def test_regression_models_include_controls_and_pooled_interaction():
    def sample(prefix, q5_multiplier):
        x = np.indices((2, 2, 2, 2, 2)).reshape(5, -1).T
        n = len(x)
        people = zahavi_income.People(
            np.array([f"{prefix}{i:02}" for i in range(n)]),
            np.array([f"{prefix}h{i:02}" for i in range(n)]),
            np.where(x[:, 0] == 0, "q1", "q5"),
            np.ones(n),
        )
        minutes = 10 * np.exp(
            x[:, 0] * np.log(q5_multiplier)
            + x[:, 1] * 0.1
            + x[:, 2] * 0.2
            + x[:, 3] * 0.05
            + x[:, 4] * 0.03
        )
        days = zahavi_income.Days(
            people.person,
            people.household,
            people.income,
            people.weight,
            minutes,
            np.zeros(n, dtype=bool),
            np.ones(n, dtype=bool),
        )
        data = zahavi_income.CachedIncome(
            people,
            days,
            np.where(x[:, 4] == 0, "employed", "retired"),
            np.where(x[:, 1] == 0, "dense", "sparse"),
            np.where(x[:, 2] == 0, "0", "1"),
            np.where(x[:, 3] == 0, "lundi", "mardi"),
        )
        draws = zahavi_modes.Draws(people.household, np.ones((20, n)), 0)
        return data, draws

    a, da = sample("a", 1.2)
    b, db = sample("b", 1.5)
    rows = zahavi_income.regression_rows(
        a, b, da, db, minimum_n=1, level_order=LEVEL_ORDER
    )
    m2 = next(
        r
        for r in rows
        if r["year"] == "2008" and r["model"] == "M2" and r["term"] == "income:q5"
    )
    interaction = next(
        r
        for r in rows
        if r["year"] == "pooled"
        and r["model"] == "pooled"
        and r["term"] == "survey:2019*income:q5"
    )
    assert m2["percent"] == pytest.approx(20)
    assert interaction["percent"] == pytest.approx(25)


def test_checkpoint_key_changes_when_input_changes(tmp_path):
    source = tmp_path / "input"
    source.write_text("first", encoding="utf-8")
    cache = modes_cache.SurveyCache(tmp_path / "cache-signature")
    first = zahavi_income.checkpoint_directory(tmp_path, [cache], (source,))
    source.write_text("second", encoding="utf-8")
    second = zahavi_income.checkpoint_directory(tmp_path, [cache], (source,))
    assert first != second


def test_report_writes_requested_tables_from_synthetic_caches(tmp_path, monkeypatch):
    def cache_and_attributes(prefix, multiplier):
        x = np.indices((5, 2, 2, 2, 2)).reshape(5, -1).T
        n = len(x)
        people = np.array([f"{prefix}p{i:03}" for i in range(n)])
        houses = np.array([f"{prefix}h{i:03}" for i in range(n)])
        days = np.array([f"{prefix}d{i:03}" for i in range(n)])
        income = np.array([f"q{i + 1}" for i in x[:, 0]])
        density = np.where(x[:, 1] == 0, "dense", "sparse")
        cars = np.where(x[:, 2] == 0, "0", "1")
        weekday = np.where(x[:, 3] == 0, "lundi", "mardi")
        population = np.where(x[:, 4] == 0, "employed", "retired")
        minutes = 20 * np.exp(
            x[:, 0] * np.log(multiplier)
            + x[:, 1] * 0.1
            + x[:, 2] * 0.2
            + x[:, 3] * 0.05
            + x[:, 4] * 0.03
        )
        cache = modes_cache.SurveyCache(tmp_path / prefix)
        cache.root.mkdir()
        tables = [
            (
                cache.roster,
                dict(
                    ident_ind=people,
                    ident_men=houses,
                    population_category=population,
                    weight=np.ones(n),
                ),
            ),
            (
                cache.day_base,
                dict(
                    day_id=days,
                    ident_ind=people,
                    ident_men=houses,
                    pond_jour=np.ones(n),
                    is_round=np.ones(n, dtype=bool),
                ),
            ),
            (
                cache.days(scope.REFERENCE_SCOPE),
                dict(day_id=days, total_time_min=minutes, income_quintile=income),
            ),
            (
                cache.trips(scope.REFERENCE_SCOPE),
                dict(day_id=days, described_weekday_name=weekday),
            ),
        ]
        with duckdb.connect() as con:
            for path, columns in tables:
                con.register("synthetic", pa.table(columns))
                con.execute("COPY synthetic TO ? (FORMAT PARQUET)", [str(path)])
                con.unregister("synthetic")
        attributes = (
            dict(zip(people, income, strict=True)),
            dict(zip(people, density, strict=True)),
            zahavi_income.HouseholdVehicles(
                dict(zip(houses, cars, strict=True)),
                dict.fromkeys(houses, 1.0),
            ),
        )
        draws = zahavi_modes.Draws(houses, np.ones((20, n)), 0)
        return cache, attributes, draws

    cache_a, attr_a, draws_a = cache_and_attributes("a", 1.05)
    cache_b, attr_b, draws_b = cache_and_attributes("b", 1.1)
    out = tmp_path / "report"
    zahavi_income.run_report(
        out,
        cache_a,
        cache_b,
        attr_a,
        attr_b,
        draws_a,
        draws_b,
        selected_scopes=[scope.REFERENCE_SCOPE],
        minimum_n=1,
        caution_n=2,
        margins=(0.15, 0.1),
        regression_level_order=LEVEL_ORDER,
        max_lost_share=0.01,
    )
    assert out.with_suffix(".md").is_file()
    assert {p.name for p in out.glob("*.csv")} == {
        "levels.csv",
        "gaps.csv",
        "reweighted.csv",
        "regression.csv",
        "quintile_density.csv",
        "support.csv",
    }
    report = out.with_suffix(".md").read_text(encoding="utf-8")
    assert "unknown" in report and "2019" in report and "M2" in report
    assert "V1_JNBVEH + V1_JNBCCVUL" in report and "JNBVPHS" in report
    assert "Share (%)" in report and "not directly comparable" not in report
    with (out / "support.csv").open(encoding="utf-8", newline="") as stream:
        audit = list(csv.DictReader(stream))
    q5 = next(
        row
        for row in audit
        if row["group"] == "regression_M2"
        and row["term"] == "income:q5"
        and row["year"] == "2008"
    )
    assert (q5["respondents"], q5["households"], q5["empty_draws"]) == ("16", "16", "0")
    assert any(
        row["group"] == "reweight_travel_day" and row["term"] == "q1|dense|0"
        for row in audit
    )
    assert any(row["group"] == "reweight_input_travel_day" for row in audit)
    with (out / "reweighted.csv").open(encoding="utf-8", newline="") as stream:
        draw_rows = [row for row in csv.DictReader(stream) if row["row_type"] == "draw"]
    assert len(draw_rows) == 40
    assert all(float(row["lost_target_share"]) == 0 for row in draw_rows)
    assert "Support audit" in report

    mode_config = {
        "trip_grid_max_min": 240,
        "day_grid_max_min": 360,
        "minimum_cell_n": 1,
        "thresholds_min": [15],
        "bootstrap_reps": 20,
        "seed": 0,
        "cache_dir": str(tmp_path / "caches"),
        "b3_report": str(tmp_path / "unused.md"),
        "logs_dir": str(tmp_path / "logs"),
        "reference_2008_min": 52.0,
        "reference_2019_min": 57.0,
        "reference_tolerance_min": 0.05,
    }
    mode_path = tmp_path / "modes.yaml"
    mode_path.write_text(yaml.safe_dump(mode_config), encoding="utf-8")
    income_path = tmp_path / "income.yaml"
    income_path.write_text(
        yaml.safe_dump(
            {
                "entd_cars": str(tmp_path / "cars.csv"),
                "caution_cell_n": 2,
                "checkpoint_dir": str(tmp_path / "checkpoints"),
                "regression_level_order": LEVEL_ORDER,
                "max_lost_target_share": 0.01,
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "cars.csv").write_text("synthetic", encoding="utf-8")
    monkeypatch.setattr(
        zahavi_income,
        "read_signed_cache",
        lambda survey, *args, **kwargs: cache_a if survey is entd2008 else cache_b,
    )
    monkeypatch.setattr(
        zahavi_income,
        "extract_attributes",
        lambda survey, *args, **kwargs: attr_a if survey is entd2008 else attr_b,
    )
    monkeypatch.setattr(
        zahavi_modes,
        "make_draws",
        lambda household, *, n_reps, seed: zahavi_modes.Draws(
            np.unique(household), np.ones((n_reps, len(np.unique(household)))), seed
        ),
    )
    cli_out = tmp_path / "cli_report"
    args = [
        "--out",
        str(cli_out),
        "--scope",
        scope.REFERENCE_SCOPE.id,
        "--modes-config",
        str(mode_path),
        "--income-config",
        str(income_path),
        "--entd2008-data-path",
        str(tmp_path / "entd"),
        "--emp2019-data-path",
        str(tmp_path / "emp.zip"),
    ]
    assert zahavi_income.main(args) == 0
    assert cli_out.with_suffix(".md").is_file()
    assert len(list((tmp_path / "logs").glob("*_zahavi_income_summary.md"))) == 1
    expected = (cli_out / "levels.csv").read_bytes()

    def fail_if_recomputed(*args, **kwargs):
        raise AssertionError("completed scope was recomputed")

    monkeypatch.setattr(zahavi_income, "read_cached_income", fail_if_recomputed)
    assert zahavi_income.main(args) == 0
    assert (cli_out / "levels.csv").read_bytes() == expected
