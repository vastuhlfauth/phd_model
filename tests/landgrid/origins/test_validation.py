"""Synthetic acceptance tests for section-6.5 validation."""

import json
from dataclasses import replace
from pathlib import Path

import duckdb
import pyarrow as pa
import pytest
from landgrid.origins.validation import (
    calculate_validation_metrics,
    render_validation_report,
)


def _cell_id(northing: int, easting: int) -> int:
    return northing // 200 * 100_000 + easting // 200


def test_composition_comparison_and_eurostat_age_ratios() -> None:
    zone = "CRS3035RES1000mN2400000E4000000"
    values = {
        "ind": 10.0, "men": 5.0, "ind_0_3": 1.0, "ind_4_5": 1.0,
        "ind_6_10": 1.0, "ind_11_17": 1.0, "ind_65_79": 1.0,
        "ind_80p": 1.0, "men_1ind": 2.0, "men_5ind": 1.0,
        "men_prop": 3.0, "men_mais": 4.0, "log_soc": 1.0, "ind_snv": 100.0,
    }
    origins = pa.Table.from_pylist([
        {
            "cell_id": _cell_id(2_400_000, 4_000_000 + 200 * i),
            "natural_cell_id": zone, "natural_cell_size_m": 1000, **values,
        }
        for i in range(2)
    ])
    insee = pa.Table.from_pylist([
        {
            "idcar_200m": f"CRS3035RES200mN2400000E{4_000_000 + 200 * i}",
            "idcar_1km": zone, "idcar_nat": zone, "lcog_geo": "33001",
            "i_est_200": 0, **values,
        }
        for i in range(2)
    ])
    ff = pa.Table.from_pylist([
        {"cell_id": _cell_id(2_400_000, 4_000_000 + 200 * i), "main_residences": 1}
        for i in range(2)
    ])
    eurostat = pa.Table.from_pylist([
        {"GRD_ID": zone, "T": 100, "LAND_SURFACE": 1.0, "Y_LT15": 3, "Y_GE65": 5}
    ])
    with duckdb.connect() as connection:
        connection.execute("LOAD spatial")
        connection.execute(
            "CREATE TEMP TABLE department_boundary AS SELECT "
            "ST_GeomFromText('POLYGON ((4000000 2400000,4001000 2400000,"
            "4001000 2401000,4000000 2401000,4000000 2400000))') AS geom"
        )
        metrics, ages, reasons = calculate_validation_metrics(
            connection, origins, insee, ff, eurostat, composition=origins,
            department="33", cell_resolution_m=200, eurostat_resolution_m=1000,
            density_thresholds_population_km2=(300, 1500),
            within_tolerance_fraction=0.2,
        )
        duplicate = pa.concat_tables([origins, origins.slice(0, 1)])
        with pytest.raises(ValueError, match="duplicate cell ids"):
            calculate_validation_metrics(
                connection, origins, insee, ff, eurostat, composition=duplicate,
                department="33", cell_resolution_m=200, eurostat_resolution_m=1000,
                density_thresholds_population_km2=(300, 1500),
                within_tolerance_fraction=0.2,
            )
    assert {
        (row["method"], row["variable"]) for row in metrics
    } >= {
        (method, variable)
        for method in ("composition", "proportional", "equal_split")
        for variable in ("men_prop", "ind_snv", "individuals")
    }
    old = next(row for row in ages if (
        row["method"] == "composition" and row["variable"] == "age_65_plus"
    ))
    assert old["downscaled_total"] == pytest.approx(4)
    assert old["reference_total"] == 5
    young = next(row for row in ages if (
        row["method"] == "composition" and row["variable"] == "under_11_ratio"
    ))
    assert young["ratio"] == pytest.approx(2)
    checkpoint = json.loads(json.dumps({
        "metrics_200m": metrics, "metrics_1km": ages, "eurostat_reasons": reasons
    }))
    assert checkpoint["metrics_200m"][0]["positive_reference_count"] == 2
    assert checkpoint["metrics_1km"][0]["positive_reference_count"] == 1
    report = render_validation_report(2021, "33", metrics, ages, reasons, 50, 0.2)
    assert "information only" in report
    assert "ind_0_3" in report
    assert "CRS3035" not in report


def test_validation_reuses_aggregate_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import landgrid.origins.validation as validation
    from landgrid.origins.composition import composition_input_signature
    from landgrid.origins.fichiers_fonciers import load_origins_config

    output = tmp_path / "interim"
    output.mkdir()
    config = load_origins_config()
    archive = tmp_path / "filosofi.zip"
    natural = tmp_path / "natural.zip"
    eurostat = tmp_path / "eurostat.parquet"
    boundary = tmp_path / "boundary.geojson"
    config_path = tmp_path / "config.yaml"
    pilot = tmp_path / "pilot.yaml"
    for path in (archive, natural, eurostat, boundary, config_path):
        path.write_text("synthetic")
    pilot.write_text('department: "33"\n')
    config = replace(
        config, filosofi_200m_archive=str(archive),
        filosofi_natural_archive=str(natural),
        report=replace(
            config.report, output_directory=str(output), contours_2021=str(boundary)
        ),
        validation=replace(config.validation, eurostat_grid=str(eurostat)),
    )
    for name in (
        "origins_2021_200m.parquet", "origins_2021_200m_composition.parquet",
        "ff_cells_2022.parquet", "ff_natural_2022.parquet",
    ):
        (output / name).write_text("synthetic")
    (output / "ff_cells_2022.json").write_text(json.dumps({
        "second_home_source": "hybrid_2024", "signature": "synthetic",
    }))
    (output / "origins_2021_composition.json").write_text(json.dumps({
        "completed": True, "ff_signature": "synthetic",
        "signature": composition_input_signature((
            config_path, pilot, natural, output / "ff_cells_2022.parquet",
            output / "ff_natural_2022.parquet", output / "ff_cells_2022.json",
            output / "origins_2021_200m.parquet",
        )),
    }))
    monkeypatch.setattr(validation, "load_origins_config", lambda *args: config)
    monkeypatch.setattr(validation, "_load_department_boundary", lambda *args: None)
    monkeypatch.setattr(validation, "_extract_filosofi_200m", lambda *args: archive)
    calls = []

    def metrics(
        *args: object, **kwargs: object
    ) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, int]]:
        calls.append(1)
        return ([{
            "method": "composition", "variable": "individuals",
            "natural_cell_size_m": 1000, "density_class": "<300",
            "cell_count": 1, "positive_reference_count": 1,
            "mean_absolute_error": 1.0, "median_absolute_relative_error": 0.1,
            "share_within_tolerance": 1.0,
        }], [], {})

    monkeypatch.setattr(validation, "calculate_validation_metrics", metrics)
    first = validation.build_validation_report(
        config_path=config_path, pilot_config_path=pilot
    )
    second = validation.build_validation_report(
        config_path=config_path, pilot_config_path=pilot
    )
    assert first == second and first.is_file()
    assert len(calls) == 1
    natural.write_text("changed synthetic input")
    with pytest.raises(ValueError, match="stale"):
        validation.build_validation_report(
            config_path=config_path, pilot_config_path=pilot
        )


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
        metrics_200m, metrics_1km, eurostat_reasons = calculate_validation_metrics(
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
    json.dumps({
        "metrics_200m": metrics_200m,
        "metrics_1km": metrics_1km,
        "eurostat_reasons": eurostat_reasons,
    })

    report = render_validation_report(
        2021, "33", metrics_200m, metrics_1km, eurostat_reasons, 50, 0.2
    )
    assert "| proportional | individuals | 1000 | <300 | <50 | <50 |" in report
    assert "| <300 | <50 | <50 | 250.0 | <50 |" in report
    assert "| no_match | <50 |" in report
    assert "CRS3035" not in report


@pytest.mark.parametrize(
    ("population", "surface", "matched", "reasons_expected", "density"),
    [
        (None, None, False, ("no_match",), "unmatched"),
        (-9999, 1.0, True, ("population_unavailable",), "population unavailable"),
        (None, 1.0, True, ("population_unavailable",), "population unavailable"),
        (400, None, True, ("land_surface_null",), "300-<1500"),
        (400, 0.0, True, ("land_surface_zero",), "300-<1500"),
        (400, -1.0, True, ("land_surface_negative",), "300-<1500"),
        (None, None, True, ("population_unavailable", "land_surface_null"),
         "population unavailable"),
        (400, 0.2, True, (), ">=1500"),
    ],
)
def test_eurostat_missing_data_reasons_and_density(
    population: int | None,
    surface: float | None,
    matched: bool,
    reasons_expected: tuple[str, ...],
    density: str,
) -> None:
    codes = [
        "CRS3035RES1000mN2400000E4000000",
        "CRS3035RES1000mN2400000E4001000",
    ]
    counts = {
        "ind": 10.0,
        "men": 5.0,
        "ind_0_3": 1.0,
        "ind_4_5": 1.0,
        "ind_6_10": 1.0,
        "ind_11_17": 1.0,
        "ind_65_79": 1.0,
        "ind_80p": 1.0,
    }
    downscaled = pa.Table.from_pylist([
        {
            "cell_id": _cell_id(2_400_000, 4_000_000 + i * 1000),
            "natural_cell_id": code,
            "natural_cell_size_m": 1000,
            **counts,
        }
        for i, code in enumerate(codes)
    ])
    insee = pa.Table.from_pylist([
        {
            "idcar_200m": f"CRS3035RES200mN2400000E{4_000_000 + i * 1000}",
            "idcar_1km": code,
            "idcar_nat": code,
            "lcog_geo": "33001",
            "i_est_200": 0,
            **counts,
        }
        for i, code in enumerate(codes)
    ])
    ff_cells = pa.Table.from_pylist([
        {
            "cell_id": _cell_id(2_400_000, 4_000_000 + i * 1000),
            "main_residences": 1,
        }
        for i in range(2)
    ])
    eurostat_rows = [{"GRD_ID": codes[0], "T": 100, "LAND_SURFACE": 1.0}]
    if matched:
        eurostat_rows.append(
            {"GRD_ID": codes[1], "T": population, "LAND_SURFACE": surface}
        )
    connection = duckdb.connect()
    try:
        connection.execute("LOAD spatial")
        connection.execute(
            "CREATE TEMP TABLE department_boundary AS SELECT "
            "ST_GeomFromText('POLYGON ((4000000 2400000,4002000 2400000,"
            "4002000 2401000,4000000 2401000,4000000 2400000))') AS geom"
        )
        metrics_200m, metrics_1km, reasons = calculate_validation_metrics(
            connection,
            downscaled,
            insee,
            ff_cells,
            pa.Table.from_pylist(eurostat_rows),
            department="33",
            cell_resolution_m=200,
            eurostat_resolution_m=1000,
            density_thresholds_population_km2=(300, 1500),
            within_tolerance_fraction=0.2,
        )
        if not matched:
            empty_eurostat = pa.Table.from_pylist([
                {"GRD_ID": "FR_unallocated", "T": 1, "LAND_SURFACE": 1.0}
            ])
            all_unmatched, no_1km, all_reasons = calculate_validation_metrics(
                connection,
                downscaled,
                insee,
                ff_cells,
                empty_eurostat,
                department="33",
                cell_resolution_m=200,
                eurostat_resolution_m=1000,
                density_thresholds_population_km2=(300, 1500),
                within_tolerance_fraction=0.2,
            )
            assert no_1km == []
            assert all_reasons["no_match"] == 2
            empty_report = render_validation_report(
                2021, "33", all_unmatched, no_1km, all_reasons, 1, 0.2
            )
            assert "No Eurostat cells with valid population" in empty_report
    finally:
        connection.close()

    expected_reasons = {
        "no_match": 0,
        "population_unavailable": 0,
        "land_surface_null": 0,
        "land_surface_zero": 0,
        "land_surface_negative": 0,
    }
    for reason in reasons_expected:
        expected_reasons[reason] = 1
    assert reasons == expected_reasons
    row = next(
        row for row in metrics_200m
        if row["method"] == "proportional"
        and row["variable"] == "individuals"
        and row["density_class"] == density
    )
    assert row["cell_count"] == 1
    assert row["mean_absolute_error"] == pytest.approx(0.0)
    if population is not None and population >= 0 and matched:
        assert any(
            row["density_class"] == density
            and row["eurostat_individuals"] == population
            for row in metrics_1km
        )
    else:
        assert sum(row["cell_count"] for row in metrics_1km) == 1
    report = render_validation_report(
        2021, "33", metrics_200m, metrics_1km, reasons, 1, 0.2
    )
    for reason in reasons_expected:
        assert f"| {reason} | 1 |" in report
    assert "otherwise 1 km²" in report
