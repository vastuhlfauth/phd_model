"""Synthetic acceptance tests for section-6.5 validation."""

import duckdb
import pyarrow as pa
import pytest
from landgrid.origins.validation import (
    calculate_validation_metrics,
    render_validation_report,
)


def _cell_id(northing: int, easting: int) -> int:
    return northing // 200 * 100_000 + easting // 200


def test_validation_reports_errors_and_suppresses_small_counts() -> None:
    natural_cell_id = "CRS3035RES1000mN2400000E4000000"
    first_cell = _cell_id(2_400_000, 4_000_000)
    second_cell = _cell_id(2_400_000, 4_000_200)
    downscaled = pa.Table.from_pylist(
        [
            {
                "cell_id": first_cell,
                "natural_cell_id": natural_cell_id,
                "natural_cell_size_m": 1000,
                "ind": 2.0,
                "men": 2.0,
                "ind_0_3": 0.2,
                "ind_4_5": 0.2,
                "ind_6_10": 0.2,
                "ind_11_17": 0.4,
                "ind_65_79": 0.6,
                "ind_80p": 0.4,
            },
            {
                "cell_id": second_cell,
                "natural_cell_id": natural_cell_id,
                "natural_cell_size_m": 1000,
                "ind": 8.0,
                "men": 8.0,
                "ind_0_3": 0.8,
                "ind_4_5": 0.8,
                "ind_6_10": 0.8,
                "ind_11_17": 1.6,
                "ind_65_79": 2.4,
                "ind_80p": 1.6,
            },
        ]
    )
    insee = pa.Table.from_pylist(
        [
            {
                "idcar_200m": "CRS3035RES200mN2400000E4000000",
                "idcar_1km": natural_cell_id,
                "idcar_nat": natural_cell_id,
                "lcog_geo": "33001",
                "i_est_200": 0,
                "ind": 4.0,
                "men": 4.0,
                "ind_0_3": 0.4,
                "ind_4_5": 0.4,
                "ind_6_10": 0.4,
                "ind_11_17": 0.8,
                "ind_65_79": 1.2,
                "ind_80p": 0.8,
            },
            {
                "idcar_200m": "CRS3035RES200mN2400000E4000200",
                "idcar_1km": natural_cell_id,
                "idcar_nat": natural_cell_id,
                "lcog_geo": "33001",
                "i_est_200": 1,
                "ind": 8.0,
                "men": 8.0,
                "ind_0_3": 0.8,
                "ind_4_5": 0.8,
                "ind_6_10": 0.8,
                "ind_11_17": 1.6,
                "ind_65_79": 2.4,
                "ind_80p": 1.6,
            },
        ]
    )
    ff_cells = pa.Table.from_pylist(
        [
            {"cell_id": first_cell, "main_residences": 1},
            {"cell_id": second_cell, "main_residences": 3},
        ]
    )
    eurostat = pa.Table.from_pylist(
        [
            {
                "GRD_ID": natural_cell_id,
                "T": 250,
                "LAND_SURFACE": 1.0,
            },
            {"GRD_ID": "FR_unallocated", "T": 1, "LAND_SURFACE": 1.0},
        ]
    )
    connection = duckdb.connect()
    try:
        connection.execute("LOAD spatial")
        connection.execute(
            "CREATE TEMP TABLE department_boundary AS SELECT "
            "ST_GeomFromText('POLYGON ((4000000 2400000,4001000 2400000,"
            "4001000 2401000,4000000 2401000,4000000 2400000))') AS geom"
        )
        metrics_200m, metrics_1km = calculate_validation_metrics(
            connection,
            downscaled,
            insee,
            ff_cells,
            eurostat,
            department="33",
            cell_resolution_m=200,
            eurostat_resolution_m=1000,
            density_thresholds_population_km2=(300, 1500),
            within_tolerance_fraction=0.2,
        )
    finally:
        connection.close()

    proportional = next(
        row
        for row in metrics_200m
        if row["method"] == "proportional" and row["variable"] == "individuals"
    )
    equal_split = next(
        row
        for row in metrics_200m
        if row["method"] == "equal_split" and row["variable"] == "individuals"
    )
    assert proportional["cell_count"] == 1
    assert proportional["natural_cell_size_m"] == 1000
    assert proportional["density_class"] == "<300"
    assert proportional["mean_absolute_error"] == pytest.approx(2)
    assert proportional["median_absolute_relative_error"] == pytest.approx(0.5)
    assert proportional["share_within_tolerance"] == 0
    assert equal_split["mean_absolute_error"] == pytest.approx(1)
    assert equal_split["median_absolute_relative_error"] == pytest.approx(0.25)
    assert metrics_1km == [
        {
            "density_class": "<300",
            "cell_count": 1,
            "downscaled_individuals": 10.0,
            "eurostat_individuals": 250.0,
            "positive_reference_count": 1,
            "median_absolute_relative_error": pytest.approx(0.96),
        }
    ]

    report = render_validation_report(
        2021, "33", metrics_200m, metrics_1km, 50, 0.2
    )
    assert "| proportional | individuals | 1000 | <300 | <50 | <50 |" in report
    assert "| <300 | <50 | <50 | 250.0 | <50 |" in report
    assert "CRS3035" not in report
