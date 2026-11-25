"""Synthetic acceptance tests for Fichiers fonciers cell counts (section 6.3)."""

import pytest
from landgrid.origins.fichiers_fonciers import (
    aggregate_dwelling_rows,
    classify_dwelling,
    coordinate_to_200m_cell,
)


@pytest.mark.parametrize(
    ("second_home_column", "second_home_value"),
    [("proba_rprs", "RS"), ("rppo_rs", "RS")],
)
def test_occupancy_rule_for_second_home_columns(
    second_home_column: str,
    second_home_value: str,
) -> None:
    row = {
        "logh": "t",
        "ccthp": "L",
        second_home_column: second_home_value,
    }

    result = classify_dwelling(row, second_home_column, "RS", "AC")

    assert result["dwelling"] == 1
    assert result["vacant"] == 0
    assert result["second_home"] == 1
    assert result["main_residence"] == 0


def test_nulls_count_as_neither_vacant_nor_second_home() -> None:
    result = classify_dwelling(
        {"logh": "t", "ccthp": None, "proba_rprs": None},
        "proba_rprs",
        "RS",
        "AC",
    )

    assert result["vacant"] == 0
    assert result["second_home"] == 0
    assert result["main_residence"] == 1


def test_floor_rule_on_exact_grid_multiples() -> None:
    assert coordinate_to_200m_cell(4_000_000.0, 2_400_000.0) == (
        2_400_000 // 200 * 100_000 + 4_000_000 // 200
    )
    assert coordinate_to_200m_cell(4_000_200.0, 2_400_200.0) == (
        2_400_200 // 200 * 100_000 + 4_000_200 // 200
    )


def test_cleaning_rules_and_main_residence_statistics() -> None:
    rows = [
        {
            "logh": "t",
            "ccthp": "P",
            "proba_rprs": "RP",
            "catpro2": "F1",
            "npiece_i": 3,
            "dnbniv": "2",
            "stoth": 60,
            "jannath": 1950,
            "X": 2_400_001,
            "Y": 4_000_001,
        },
        {
            "logh": "t",
            "ccthp": "P",
            "proba_rprs": "RP",
            "catpro2": "F1",
            "npiece_i": 5,
            "dnbniv": "99",
            "stoth": -1,
            "jannath": 1500,
            "X": 2_400_001,
            "Y": 4_000_001,
        },
    ]

    aggregates = aggregate_dwelling_rows(rows, "proba_rprs", "RS", "AC")

    assert aggregates["dwellings"] == 2
    assert aggregates["main_residences"] == 2
    assert aggregates["social_housing"] == 2
    assert aggregates["social_housing_main_residences"] == 2
    assert aggregates["owner_occupied_main_residences"] == 2
    assert aggregates["houses"] == 0
    assert aggregates["flats"] == 0
    assert aggregates["npiece_i_sum"] == 8
    assert aggregates["npiece_i_sum_sq"] == 34
    assert aggregates["dnbniv_sum"] == 2
    assert aggregates["dnbniv_sum_sq"] == 4
    assert aggregates["stoth_valid_count"] == 1
    assert aggregates["jannath_valid_count"] == 1
    assert aggregates["stoth_median"] == 60.0
    assert aggregates["jannath_median"] == 1950.0


def test_category_sums_preserve_dwelling_total() -> None:
    rows = [
        {"logh": "t", "ccthp": "V", "proba_rprs": "NO"},
        {"logh": "t", "ccthp": "P", "proba_rprs": "RS"},
        {"logh": "t", "ccthp": "P", "proba_rprs": "RP"},
    ]

    aggregates = aggregate_dwelling_rows(
        rows,
        "proba_rprs",
        "RS",
        "AC",
    )

    assert (
        aggregates["main_residences"]
        + aggregates["vacant"]
        + aggregates["second_homes"]
        == aggregates["dwellings"]
    )
