"""Synthetic acceptance tests for Filosofi natural-cell downscaling."""

import duckdb
import pyarrow as pa
import pytest
from landgrid.origins.downscale import downscale_natural_cells


def _cell_id(northing: int, easting: int) -> int:
    return northing // 200 * 100_000 + easting // 200


def test_downscales_totals_and_uses_each_weight_fallback() -> None:
    natural_rows = [
        {
            "idcar_nat": "CRS3035RES1000mN2400000E4000000",
            "tmaille": 1000,
            "ind": 30.0,
            "men": 12.0,
            "men_1ind": 3.0,
        },
        {
            "idcar_nat": "CRS3035RES1000mN2401000E4000000",
            "tmaille": 1000,
            "ind": 20.0,
            "men": 8.0,
            "men_1ind": 2.0,
        },
        {
            "idcar_nat": "CRS3035RES1000mN2402000E4000000",
            "tmaille": 1000,
            "ind": 12.0,
            "men": 6.0,
            "men_1ind": 1.0,
        },
        {
            "idcar_nat": "CRS3035RES200mN2403000E4000000",
            "tmaille": 200,
            "ind": 4.0,
            "men": 2.0,
            "men_1ind": 1.0,
        },
    ]
    natural = pa.Table.from_pylist(natural_rows)
    ff_cells = pa.Table.from_pylist(
        [
            {
                "cell_id": _cell_id(2_400_000, 4_000_000),
                "natural_cell_id": natural_rows[0]["idcar_nat"],
                "main_residences": 2,
                "dwellings": 2,
            },
            {
                "cell_id": _cell_id(2_400_000, 4_000_200),
                "natural_cell_id": natural_rows[0]["idcar_nat"],
                "main_residences": 1,
                "dwellings": 1,
            },
            {
                "cell_id": _cell_id(2_401_000, 4_000_000),
                "natural_cell_id": natural_rows[1]["idcar_nat"],
                "main_residences": 0,
                "dwellings": 1,
            },
            {
                "cell_id": _cell_id(2_401_000, 4_000_200),
                "natural_cell_id": natural_rows[1]["idcar_nat"],
                "main_residences": 0,
                "dwellings": 3,
            },
        ]
    )
    filosofi_200m = pa.Table.from_pylist(
        [
            {"idcar_200m": "CRS3035RES200mN2402000E4000000", "men": 3.0},
            {"idcar_200m": "CRS3035RES200mN2402200E4000000", "men": 1.0},
        ]
    )
    scope_ids = [row["idcar_nat"] for row in natural_rows]
    connection = duckdb.connect()
    try:
        downscale_natural_cells(
            connection,
            natural,
            ff_cells,
            filosofi_200m,
            scope_ids,
            200,
        )
        output = connection.execute(
            "SELECT * FROM _downscaled_origins ORDER BY cell_id"
        ).to_arrow_table()
        fallback = connection.execute(
            """
            SELECT fallback_used, count(*) AS cell_count, sum(men) AS households
            FROM _downscaled_origins
            GROUP BY fallback_used
            """
        ).fetchall()
    finally:
        connection.close()

    assert output.num_rows == 76
    expected_totals = {
        row["idcar_nat"]: row for row in natural_rows
    }
    for row in output.to_pylist():
        expected = expected_totals[row["natural_cell_id"]]
        assert row["natural_cell_size_m"] == expected["tmaille"]
    for variable in ("ind", "men", "men_1ind"):
        totals = (
            duckdb.query(
                f"""
                SELECT natural_cell_id, sum("{variable}") AS value
                FROM output
                GROUP BY natural_cell_id
                """
            )
            .to_arrow_table()
            .to_pylist()
        )
        for row in totals:
            assert row["value"] == pytest.approx(
                expected_totals[row["natural_cell_id"]][variable],
                abs=1e-9,
            )

    direct = next(
        row
        for row in output.to_pylist()
        if row["natural_cell_id"] == natural_rows[3]["idcar_nat"]
    )
    assert direct["ind"] == 4.0
    assert direct["men"] == 2.0
    assert direct["fallback_used"] == "natural_200m"
    fallback_by_method = {
        row[0]: {"cell_count": row[1], "households": row[2]}
        for row in fallback
    }
    assert fallback_by_method["main_residences"]["cell_count"] == 25
    assert fallback_by_method["main_residences"]["households"] == pytest.approx(12)
    assert fallback_by_method["dwellings"]["cell_count"] == 25
    assert fallback_by_method["dwellings"]["households"] == pytest.approx(8)
    assert fallback_by_method["filosofi_households"]["cell_count"] == 25
    assert fallback_by_method["filosofi_households"]["households"] == pytest.approx(6)
