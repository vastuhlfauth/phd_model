"""Synthetic tests for the income supplement."""

import duckdb
import numpy as np
import pytest
from mobgrid.budget import entd2008, zahavi_income, zahavi_modes


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
        "idENT_MEN;V1_JNBVEH;label\n"
        "00001;0;véhicule\n00002;1;x\n00003;3;x\n00004;;x\n",
        encoding="cp1252",
    )
    actual = zahavi_income.load_entd_household_cars(source, tmp_path / "scratch")
    assert actual == {"00001": "0", "00002": "1", "00003": "2+", "00004": "unknown"}


def test_entd_household_car_count_rejects_duplicate_households(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("idENT_MEN;V1_JNBVEH\n1;0\n1;1\n", encoding="cp1252")
    with pytest.raises(ValueError, match="Duplicate"):
        zahavi_income.load_entd_household_cars(source, tmp_path / "scratch")


def test_gap_change_interval_uses_paired_replicates():
    q1_2008 = zahavi_income.Metric(10.0, np.array([9.0, 10.0, 11.0]))
    q5_2008 = zahavi_income.Metric(20.0, np.array([19.0, 20.0, 21.0]))
    q1_2019 = zahavi_income.Metric(11.0, np.array([12.0, 10.0, 11.0]))
    q5_2019 = zahavi_income.Metric(23.0, np.array([24.0, 24.0, 23.0]))
    change = zahavi_income.gap_change(q1_2008, q5_2008, q1_2019, q5_2019)
    assert change.value == pytest.approx(2.0)
    np.testing.assert_array_equal(change.replicates, [2.0, 4.0, 2.0])
    assert zahavi_modes._interval(change.replicates) == pytest.approx((2.0, 3.9))


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
