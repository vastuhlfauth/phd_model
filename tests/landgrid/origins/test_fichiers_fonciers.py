"""Synthetic acceptance tests for Fichiers fonciers cell counts (section 6.3)."""

from dataclasses import replace
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from landgrid.origins.fichiers_fonciers import (
    VintageConfig,
    aggregate_dwelling_rows,
    aggregate_staged_ff_cells,
    aggregate_staged_ff_communes,
    build_department_ff_cells,
    build_ff_cells,
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


def test_hybrid_sql_matches_reference_for_each_status_and_missing_match(
    tmp_path: Path,
) -> None:
    statuses = ["RS", "RPPO", "MR", "NO", "PM", "INCONNU", None, "missing"]
    rows = [
        {
            "idlocal": f"{status}-{own}",
            "idcom": "33001",
            "X": 4_000_010.0,
            "Y": 2_400_010.0,
            "logh": "t",
            "ccthp": vacancy,
            "proba_rprs": own,
        }
        for status in statuses
        for own, vacancy in [("RS", "P"), ("RP", "V"), ("AC", "P")]
    ]
    later = [
        {"idlocal": f"{status}-{own}", "rppo_rs": status}
        for status in statuses if status != "missing"
        for own in ("RS", "RP", "AC")
    ]
    for year, values in ((2022, rows), (2024, later)):
        partition = tmp_path / str(year) / "ccodep=33" / "part.parquet"
        partition.parent.mkdir(parents=True)
        pq.write_table(pa.Table.from_pylist(values), partition)
    config = load_origins_config()
    for year in (2022, 2024):
        config.vintages[year] = replace(
            config.vintages[year],
            parquet_pattern=str(
                tmp_path / str(year) / "ccodep={department}" / "part.parquet"
            ),
            second_home_source="hybrid_2024" if year == 2022 else "own",
        )
    connection = duckdb.connect()
    try:
        table, diagnostics = build_department_ff_cells(
            connection, 2022, "33", config, {},
            build_natural_cell_lookup(["CRS3035RES1000mN2400000E4000000"]),
        )
        actual = connection.execute(
            f'SELECT idlocal, dwelling, vacant, second_home, main_residence, '
            f'recent_transfer FROM "{table}" ORDER BY idlocal'
        ).to_arrow_table().to_pylist()
    finally:
        connection.close()
    later_by_id = {row["idlocal"]: row["rppo_rs"] for row in later}
    for result in actual:
        source = next(row for row in rows if row["idlocal"] == result["idlocal"])
        reference = classify_dwelling(
            {**source, "rppo_rs_2024": later_by_id.get(source["idlocal"])},
            "proba_rprs", "RS", "AC", second_home_source="hybrid_2024",
        )
        for key in (
            "dwelling", "vacant", "second_home", "main_residence", "recent_transfer"
        ):
            assert result[key] == reference[key], (source, key)
        status = later_by_id.get(source["idlocal"])
        expected_second = status == "RS" if status in {"RS", "RPPO"} else (
            source["proba_rprs"] == "RS"
        )
        assert result["second_home"] == expected_second
        assert result["vacant"] == (source["ccthp"] == "V")
        assert result["main_residence"] == (
            source["ccthp"] != "V" and not expected_second
        )
    assert diagnostics["hybrid_settled_rs"] == 3
    assert diagnostics["hybrid_settled_rppo"] == 3
    assert diagnostics["hybrid_fallback"] == 18
    changed_transfer = next(row for row in actual if row["idlocal"] == "RS-AC")
    assert changed_transfer["second_home"] == 1
    assert changed_transfer["recent_transfer"] == 0


def test_hybrid_rejects_duplicate_2024_identifiers(tmp_path: Path) -> None:
    for year, rows in (
        (2022, [{"idlocal": "x", "idcom": "33001", "X": 4_000_000.0,
                 "Y": 2_400_000.0, "logh": "t", "ccthp": "P", "proba_rprs": "RS"}]),
        (2024, [{"idlocal": "x", "rppo_rs": "RS"},
                {"idlocal": "x", "rppo_rs": "RPPO"}]),
    ):
        folder = tmp_path / str(year) / "ccodep=33"
        folder.mkdir(parents=True)
        pq.write_table(pa.Table.from_pylist(rows), folder / "part.parquet")
    config = load_origins_config()
    for year in (2022, 2024):
        config.vintages[year] = replace(
            config.vintages[year],
            parquet_pattern=str(
                tmp_path / str(year) / "ccodep={department}" / "part.parquet"
            ),
            second_home_source="hybrid_2024" if year == 2022 else "own",
        )
    connection = duckdb.connect()
    try:
        with pytest.raises(ValueError, match="duplicate 2024 idlocal"):
            build_department_ff_cells(
                connection, 2022, "33", config, {},
                build_natural_cell_lookup(["CRS3035RES1000mN2400000E4000000"]),
            )
    finally:
        connection.close()


def test_hybrid_refuses_default_output_before_reading_sources() -> None:
    with pytest.raises(ValueError, match="separate output"):
        build_ff_cells(2022, second_home_source="hybrid_2024")
    with pytest.raises(ValueError, match="only available"):
        build_ff_cells(2024, second_home_source="hybrid_2024")


def test_cli_suppresses_small_build_counts(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    from landgrid.origins import fichiers_fonciers

    monkeypatch.setattr(
        fichiers_fonciers, "build_ff_cells",
        lambda *args, **kwargs: {
            "row_count": 4,
            "commune_row_count": 50,
            "diagnostics": {"hybrid_fallback": 2, "hybrid_settled_rs": 60},
        },
    )
    assert fichiers_fonciers.main(["--vintage", "2022"]) == 0
    import json
    result = json.loads(capsys.readouterr().out)
    assert result["row_count"] == "<50"
    assert result["commune_row_count"] == 50
    assert result["diagnostics"] == {
        "hybrid_fallback": "<50", "hybrid_settled_rs": 60
    }


def test_vacant_recent_transfer_is_not_counted_as_main_or_recent() -> None:
    result = classify_dwelling(
        {"logh": "t", "ccthp": "V", "proba_rprs": "AC"},
        "proba_rprs",
        "RS",
        "AC",
    )

    assert result["vacant"] == 1
    assert result["main_residence"] == 0
    assert result["recent_transfer"] == 0


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


def test_owner_occupied_classification_tracks_recent_transfers() -> None:
    rows = [
        {"logh": "t", "ccthp": "P", "proba_rprs": "RP"},
        {"logh": "t", "ccthp": "P", "proba_rprs": "RS"},
        {"logh": "t", "ccthp": "P", "proba_rprs": "AC"},
    ]

    aggregates = aggregate_dwelling_rows(rows, "proba_rprs", "RS", "AC")

    assert aggregates["owner_occupied_main_residences"] == 2
    assert aggregates["owner_occupied_second_homes"] == 1
    assert aggregates["owner_occupied_recent_transfers"] == 1


def test_origins_config_has_verified_census_selectors() -> None:
    config = load_origins_config()

    assert config.census[2023].table_id == "LOG_T1"
    assert config.census[2023].dataset_id == "DS_RP_SERIE_HISTORIQUE"
    assert config.census[2023].measures == {
        "dwellings": "DWELLINGS",
        "main_residences": "DWELLINGS_OCS_DW_MAIN",
        "second_homes": "DWELLINGS_OCS_DW_SEC_DW_OCC",
        "vacant": "DWELLINGS_OCS_DW_VAC",
    }
    assert config.report.ff_vintage_to_census == {2022: 2021, 2024: 2023}


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
        communes = aggregate_staged_ff_communes(
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
    assert communes == [
        {
            "vintage": 2022,
            "commune_code": "33001",
            "dwellings": 6,
            "main_residences": 4,
            "vacant": 1,
            "second_homes": 1,
            "recent_transfers": 0,
            "owner_occupied_main_residences": 1,
            "owner_occupied_second_homes": 1,
            "owner_occupied_recent_transfers": 0,
            "social_housing_main_residences": 1,
        },
        {
            "vintage": 2022,
            "commune_code": "33002",
            "dwellings": 1,
            "main_residences": 1,
            "vacant": 0,
            "second_homes": 0,
            "recent_transfers": 1,
            "owner_occupied_main_residences": 1,
            "owner_occupied_second_homes": 0,
            "owner_occupied_recent_transfers": 1,
            "social_housing_main_residences": 1,
        },
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
