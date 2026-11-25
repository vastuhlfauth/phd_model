"""Synthetic acceptance tests for Fichiers fonciers cell counts (section 6.3)."""

from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from landgrid.origins.fichiers_fonciers import (
    VintageConfig,
    aggregate_dwelling_rows,
    aggregate_staged_ff_cells,
    build_department_ff_cells,
    classify_dwelling,
    coordinate_to_200m_cell,
    derived_departments_for_pilot,
    load_origins_config,
)
from landgrid.origins.filosofi import build_natural_cell_lookup


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


def test_dwelling_without_filosofi_200m_row_gets_natural_cell(
    tmp_path: Path,
) -> None:
    natural_code = "CRS3035RES1000mN2400000E4000000"
    partition = tmp_path / "part-01.parquet"
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "idlocal": "synthetic",
                    "idcom": "33001",
                    "X": 4_000_210.0,
                    "Y": 2_400_210.0,
                    "logh": "t",
                    "ccthp": "P",
                    "proba_rprs": "RP",
                    "catpro2": None,
                    "npiece_i": 2,
                    "dnbniv": "1",
                    "stoth": 40,
                    "jannath": 2000,
                    "loghmais": None,
                    "loghappt": None,
                }
            ]
        ),
        partition,
    )
    config = load_origins_config()
    config.vintages[2022] = VintageConfig(
        parquet_pattern=str(tmp_path / "ccodep={department}" / "part-01.parquet"),
        second_home_column="proba_rprs",
        second_home_code="RS",
    )
    department_partition = tmp_path / "ccodep=33"
    department_partition.mkdir()
    partition.replace(department_partition / "part-01.parquet")
    connection = duckdb.connect()
    try:
        staging_table, _ = build_department_ff_cells(
            connection,
            2022,
            "33",
            config,
            {},
            build_natural_cell_lookup([natural_code]),
        )
        cells = aggregate_staged_ff_cells(
            connection,
            [staging_table],
            2022,
        ).to_pylist()
    finally:
        connection.close()

    assert cells[0]["natural_cell_id"] == natural_code


def test_department_cells_match_python_classification_and_ignore_other_idcoms(
    tmp_path: Path,
) -> None:
    natural_code = "CRS3035RES1000mN2400000E4000000"
    rows = [
        {
            "idlocal": "main-owner-social",
            "idcom": "33001",
            "X": 4_000_010.0,
            "Y": 2_400_010.0,
            "logh": "t",
            "ccthp": "P",
            "proba_rprs": "RP",
            "catpro2": "F1",
            "npiece_i": 3,
            "dnbniv": "2",
            "stoth": 60,
            "jannath": 1950,
            "loghmais": "t",
            "loghappt": None,
        },
        {
            "idlocal": "vacant",
            "idcom": "33001",
            "X": 4_000_010.0,
            "Y": 2_400_010.0,
            "logh": "t",
            "ccthp": "V",
            "proba_rprs": "NO",
            "catpro2": "F1",
            "npiece_i": 2,
            "dnbniv": "1",
            "stoth": 30,
            "jannath": 2000,
            "loghmais": None,
            "loghappt": None,
        },
        {
            "idlocal": "second-home",
            "idcom": "33001",
            "X": 4_000_010.0,
            "Y": 2_400_010.0,
            "logh": "t",
            "ccthp": "P",
            "proba_rprs": "RS",
            "catpro2": "F1",
            "npiece_i": 2,
            "dnbniv": "1",
            "stoth": 40,
            "jannath": 2000,
            "loghmais": None,
            "loghappt": None,
        },
        {
            "idlocal": "recent-transfer",
            "idcom": "33002",
            "X": 4_000_110.0,
            "Y": 2_400_010.0,
            "logh": "t",
            "ccthp": "P",
            "proba_rprs": "AC",
            "catpro2": "F1",
            "npiece_i": 4,
            "dnbniv": "3",
            "stoth": 70,
            "jannath": 1980,
            "loghmais": None,
            "loghappt": "t",
        },
        {
            "idlocal": "null-codes",
            "idcom": "33001",
            "X": 4_000_010.0,
            "Y": 2_400_010.0,
            "logh": "t",
            "ccthp": None,
            "proba_rprs": None,
            "catpro2": None,
            "npiece_i": None,
            "dnbniv": "80",
            "stoth": -1,
            "jannath": 1599,
            "loghmais": None,
            "loghappt": None,
        },
        {
            "idlocal": "coded-values",
            "idcom": "33001",
            "X": 4_000_010.0,
            "Y": 2_400_010.0,
            "logh": "t",
            "ccthp": "L",
            "proba_rprs": "NO",
            "catpro2": None,
            "npiece_i": 5,
            "dnbniv": "unknown",
            "stoth": 100,
            "jannath": 2022,
            "loghmais": None,
            "loghappt": None,
        },
        {
            "idlocal": "future-construction",
            "idcom": "33001",
            "X": 4_000_010.0,
            "Y": 2_400_010.0,
            "logh": "t",
            "ccthp": "L",
            "proba_rprs": "NO",
            "catpro2": None,
            "npiece_i": 1,
            "dnbniv": "1",
            "stoth": 20,
            "jannath": 2023,
            "loghmais": None,
            "loghappt": None,
        },
        {
            "idlocal": "non-dwelling-mismatch",
            "idcom": "33002",
            "X": 4_000_010.0,
            "Y": 2_400_010.0,
            "logh": None,
            "ccthp": "P",
            "proba_rprs": "NO",
            "catpro2": None,
            "npiece_i": 3,
            "dnbniv": "1",
            "stoth": 50,
            "jannath": 2000,
            "loghmais": None,
            "loghappt": None,
        },
    ]
    partition = tmp_path / "ccodep=33" / "part-01.parquet"
    partition.parent.mkdir()
    pq.write_table(pa.Table.from_pylist(rows), partition)
    config = load_origins_config()
    config.vintages[2022] = VintageConfig(
        parquet_pattern=str(
            tmp_path / "ccodep={department}" / "part-01.parquet"
        ),
        second_home_column="proba_rprs",
        second_home_code="RS",
    )
    cell_codes = {
        "CRS3035RES200mN2400000E4000000": "33001",
        "CRS3035RES200mN2400000E4000200": "33001",
    }

    connection = duckdb.connect()
    try:
        staging_table, diagnostics = build_department_ff_cells(
            connection,
            2022,
            "33",
            config,
            cell_codes,
            build_natural_cell_lookup([natural_code]),
        )
        cells = aggregate_staged_ff_cells(
            connection,
            [staging_table],
            2022,
        ).to_pylist()
    finally:
        connection.close()

    assert diagnostics["idcom_commune_mismatch"] == 1
    assert diagnostics["dnbniv_code_values"] == 2
    assert diagnostics["stoth_negative_missing"] == 1
    assert diagnostics["jannath_below_min"] == 1
    assert diagnostics["jannath_above_vintage"] == 1
    expected = aggregate_dwelling_rows(
        rows,
        "proba_rprs",
        "RS",
        "AC",
        vintage=2022,
    )
    cell = cells[0]
    assert cell["cell_id"] == coordinate_to_200m_cell(
        4_000_010.0,
        2_400_010.0,
    )
    assert cell["natural_cell_id"] == natural_code
    assert cell["dwellings"] == expected["dwellings"]
    assert cell["main_residences"] == expected["main_residences"]
    assert cell["vacant"] == expected["vacant"]
    assert cell["second_homes"] == expected["second_homes"]
    assert cell["recent_transfers"] == expected["recent_transfers"]
    assert cell["social_housing"] == expected["social_housing"]
    assert cell["houses"] == expected["houses"]
    assert cell["flats"] == expected["flats"]
    assert cell["owner_occupied_main_residences"] == expected[
        "owner_occupied_main_residences"
    ]
    assert cell["social_housing_main_residences"] == expected[
        "social_housing_main_residences"
    ]
    assert cell["npiece_i_sum"] == expected["npiece_i_sum"]
    assert cell["npiece_i_sum_sq"] == expected["npiece_i_sum_sq"]
    assert cell["dnbniv_sum"] == expected["dnbniv_sum"]
    assert cell["dnbniv_sum_sq"] == expected["dnbniv_sum_sq"]
    assert cell["stoth_median"] == expected["stoth_median"]
    assert cell["stoth_std"] == expected["stoth_std"]
    assert cell["jannath_median"] == expected["jannath_median"]
    assert cell["jannath_std"] == expected["jannath_std"]


def test_pilot_departments_include_only_natural_cell_neighbours() -> None:
    connection = duckdb.connect()
    connection.register(
        "_filosofi_200m",
        pa.Table.from_pylist(
            [
                {
                    "cell_code": "CRS3035RES200mN2400000E4000000",
                    "lcog_geo": "33001",
                },
                {
                    "cell_code": "CRS3035RES200mN2400000E4000200",
                    "lcog_geo": "17001",
                },
                {
                    "cell_code": "CRS3035RES200mN2401000E4000000",
                    "lcog_geo": "24001",
                },
            ]
        ),
    )
    connection.register(
        "_natural_cells",
        pa.Table.from_pylist(
            [
                {
                    "natural_cell_id": "CRS3035RES1000mN2400000E4000000",
                    "resolution_m": 1000,
                    "northing_m": 2_400_000,
                    "easting_m": 4_000_000,
                }
            ]
        ),
    )
    try:
        assert derived_departments_for_pilot(connection, "33") == {"17", "33"}
    finally:
        connection.close()


@pytest.mark.parametrize(
    ("vintage", "second_home_column", "proba_value", "rppo_value"),
    [
        (2022, "proba_rprs", "RS", "RP"),
        (2024, "rppo_rs", "RP", "RS"),
    ],
)
def test_sql_uses_vintage_second_home_column(
    tmp_path: Path,
    vintage: int,
    second_home_column: str,
    proba_value: str,
    rppo_value: str,
) -> None:
    partition = tmp_path / "ccodep=33" / "part-01.parquet"
    partition.parent.mkdir()
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "idlocal": "second-home",
                    "idcom": "33001",
                    "X": 4_000_010.0,
                    "Y": 2_400_010.0,
                    "logh": "t",
                    "ccthp": "P",
                    "proba_rprs": proba_value,
                    "rppo_rs": rppo_value,
                    "catpro2": None,
                    "npiece_i": 1,
                    "dnbniv": "1",
                    "stoth": 20,
                    "jannath": 2000,
                    "loghmais": None,
                    "loghappt": None,
                }
            ]
        ),
        partition,
    )
    config = load_origins_config()
    config.vintages[vintage] = VintageConfig(
        parquet_pattern=str(
            tmp_path / "ccodep={department}" / "part-01.parquet"
        ),
        second_home_column=second_home_column,
        second_home_code="RS",
    )
    connection = duckdb.connect()
    try:
        staging_table, _ = build_department_ff_cells(
            connection,
            vintage,
            "33",
            config,
            {},
            build_natural_cell_lookup(
                ["CRS3035RES1000mN2400000E4000000"]
            ),
        )
        cells = aggregate_staged_ff_cells(
            connection,
            [staging_table],
            vintage,
        ).to_pylist()
    finally:
        connection.close()

    assert cells[0]["second_homes"] == 1
    assert cells[0]["main_residences"] == 0
