"""Synthetic report tests for census and Fichiers fonciers comparisons."""

import json
import zipfile
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import yaml
from landgrid.origins.fichiers_fonciers import (
    CensusVintageConfig,
    load_origins_config,
)
from landgrid.origins.report import (
    build_commune_report,
    calculate_report_summary,
    load_census_department,
    render_commune_report,
)


def test_comparison_natural_cells_require_full_geometric_containment() -> None:
    from landgrid.origins.report import calculate_natural_cell_ratios

    natural = pa.Table.from_pylist(
        [
            {
                "idcar_nat": "CRS3035RES200mN2400000E4000000",
                "tmaille": 200,
                "men": 100.0,
            },
            {
                "idcar_nat": "CRS3035RES200mN2400000E4000200",
                "tmaille": 200,
                "men": 100.0,
            },
            {
                "idcar_nat": "CRS3035RES200mN2400000E4000400",
                "tmaille": 200,
                "men": 100.0,
            },
        ]
    )
    own = pa.Table.from_pylist(
        [
            {"natural_cell_id": natural["idcar_nat"][0].as_py(), "main_residences": 80},
            {
                "natural_cell_id": natural["idcar_nat"][1].as_py(),
                "main_residences": 200,
            },
        ]
    )
    hybrid = pa.Table.from_pylist(
        [
            {
                "natural_cell_id": natural["idcar_nat"][0].as_py(),
                "main_residences": 120,
            },
            {
                "natural_cell_id": natural["idcar_nat"][1].as_py(),
                "main_residences": 200,
            },
        ]
    )
    connection = duckdb.connect()
    try:
        connection.execute("LOAD spatial")
        connection.execute(
            "CREATE TEMP TABLE department_boundary AS "
            "SELECT ST_GeomFromText(?) AS geom",
            [
                "POLYGON ((4000000 2400000,4000300 2400000,4000300 2400200,"
                "4000000 2400200,4000000 2400000))"
            ],
        )
        rows = calculate_natural_cell_ratios(connection, natural, own, hybrid)
    finally:
        connection.close()
    assert len(rows) == 1
    assert rows[0]["cells"] == 1
    assert rows[0]["own"][4] == pytest.approx(0.8)
    assert rows[0]["hybrid"][4] == pytest.approx(1.2)


def test_department_boundary_reads_and_transforms_synthetic_contours(
    tmp_path: Path,
) -> None:
    from landgrid.origins.report import _load_department_boundary

    path = tmp_path / "communes.geojson"
    path.write_text(
        json.dumps({
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {"departement": "33"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-0.7, 44.7], [-0.5, 44.7], [-0.5, 44.9],
                        [-0.7, 44.9], [-0.7, 44.7],
                    ]],
                },
            }],
        }),
        encoding="utf-8",
    )
    connection = duckdb.connect()
    try:
        _load_department_boundary(connection, path, "33")
        contained = connection.execute(
            "SELECT ST_Covers(geom, ST_Transform(ST_Point(-0.6, 44.8), "
            "'EPSG:4326', 'EPSG:3035', true)) FROM department_boundary"
        ).fetchone()[0]
        assert contained
        with pytest.raises(ValueError, match="no commune contours"):
            connection.execute("DROP TABLE department_boundary")
            _load_department_boundary(connection, path, "34")
    finally:
        connection.close()


def test_comparison_report_builds_from_two_synthetic_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from landgrid.origins import report as report_module

    def boundary(
        connection: duckdb.DuckDBPyConnection, path: Path, department: str
    ) -> None:
        connection.execute("LOAD spatial")
        connection.execute(
            "CREATE TEMP TABLE department_boundary AS SELECT ST_GeomFromText("
            "'POLYGON ((4000000 2400000,4000200 2400000,4000200 2400200,"
            "4000000 2400200,4000000 2400000))') AS geom"
        )

    monkeypatch.setattr(report_module, "_load_department_boundary", boundary)
    config = yaml.safe_load(Path("config/origins.yaml").read_text(encoding="utf-8"))
    census = tmp_path / "census.zip"
    with zipfile.ZipFile(census, "w") as archive:
        archive.writestr(
            "dossier_complet.csv",
            "CODGEO;P21_LOG;P21_RP;P21_RSECOCC;P21_LOGVAC\n33001;150;100;30;20\n",
        )
    natural = tmp_path / "natural.zip"
    with zipfile.ZipFile(natural, "w") as archive:
        archive.writestr(
            "carreaux_nivNaturel_met.csv",
            "idcar_nat,tmaille,men\nCRS3035RES200mN2400000E4000000,200,100\n",
        )
    config["census"][2021]["path"] = str(census)
    config["filosofi"]["natural_archive"] = str(natural)
    config_path = tmp_path / "origins.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    for label, main, second in (("own", 80, 50), ("hybrid_2024", 100, 30)):
        folder = tmp_path / label
        folder.mkdir()
        pq.write_table(
            pa.Table.from_pylist(
                [
                    {
                        "commune_code": "33001",
                        "dwellings": 150,
                        "main_residences": main,
                        "second_homes": second,
                        "vacant": 20,
                        "recent_transfers": 10,
                        "owner_occupied_main_residences": main,
                        "owner_occupied_second_homes": second,
                        "owner_occupied_recent_transfers": 10,
                    }
                ]
            ),
            folder / "ff_communes_2022.parquet",
        )
        pq.write_table(
            pa.Table.from_pylist(
                [
                    {
                        "natural_cell_id": "CRS3035RES200mN2400000E4000000",
                        "main_residences": main,
                    }
                ]
            ),
            folder / "ff_cells_2022.parquet",
        )
        (folder / "ff_cells_2022.json").write_text(
            json.dumps(
                {
                    "second_home_source": label,
                    "departments": ["33"],
                    "department_diagnostics": {
                        "33": {
                            "hybrid_settled_rs": 60,
                            "hybrid_settled_rppo": 80,
                            "hybrid_fallback": 10,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
    result = report_module.build_comparison_report(
        "33",
        tmp_path / "own",
        tmp_path / "hybrid_2024",
        config_path=config_path,
        output=tmp_path,
    )
    text = result.read_text(encoding="utf-8")
    assert "own" in text and "hybrid_2024" in text
    assert "80.0%" in text and "100.0%" in text
    assert "hybrid fallback | <50" in text
    assert "Largest" in text and "Recent-transfer interpretations" in text
    assert result.name == "ff_commune_comparison_2022.md"


def test_comparison_cli_uses_separate_input_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from landgrid.origins import report

    calls = []

    def build(department: str, own: Path, hybrid: Path, **options: object) -> Path:
        calls.append((department, own, hybrid, options["output"]))
        return tmp_path / "report.md"

    monkeypatch.setattr(report, "build_comparison_report", build)
    assert report.main([
        "--vintage", "2022", "--department", "33",
        "--compare-own", str(tmp_path / "own"),
        "--compare-hybrid", str(tmp_path / "hybrid"),
        "--output", str(tmp_path / "reports"),
    ]) == 0
    assert calls == [(
        "33", tmp_path / "own", tmp_path / "hybrid", tmp_path / "reports"
    )]


def test_loads_2023_housing_observations_with_configured_selectors(
    tmp_path: Path,
) -> None:
    parquet_path = tmp_path / "census.parquet"
    measure_values = {
        "DWELLINGS": 120.0,
        "DWELLINGS_OCS_DW_MAIN": 80.0,
        "DWELLINGS_OCS_DW_SEC_DW_OCC": 20.0,
        "DWELLINGS_OCS_DW_VAC": 20.0,
    }
    rows = [
        {
            "GEO": f"COM-{code}",
            "GEO_OBJECT": "COM",
            "TIME_PERIOD": "2023",
            "ID_TAB": "LOG_T1",
            "DS": "DS_RP_SERIE_HISTORIQUE",
            "TAB_MEASURE": measure,
            "OBS_VALUE": value,
        }
        for code in ("33001", "33002")
        for measure, value in measure_values.items()
    ]
    pq.write_table(pa.Table.from_pylist(rows), parquet_path)
    config = load_origins_config()
    config.census[2023] = CensusVintageConfig(
        format="parquet",
        path=str(parquet_path),
        geography_column="GEO",
        geography_type_column="GEO_OBJECT",
        geography_type="COM",
        time_period_column="TIME_PERIOD",
        time_period="2023",
        table_column="ID_TAB",
        table_id="LOG_T1",
        dataset_column="DS",
        dataset_id="DS_RP_SERIE_HISTORIQUE",
        measure_column="TAB_MEASURE",
        measures={
            "dwellings": "DWELLINGS",
            "main_residences": "DWELLINGS_OCS_DW_MAIN",
            "second_homes": "DWELLINGS_OCS_DW_SEC_DW_OCC",
            "vacant": "DWELLINGS_OCS_DW_VAC",
        },
    )
    connection = duckdb.connect()
    try:
        table = load_census_department(connection, 2023, "33", config)
    finally:
        connection.close()

    assert table.num_rows == 2
    assert table.column("commune_code").to_pylist() == ["33001", "33002"]
    assert table.column("dwellings").to_pylist() == [120.0, 120.0]
    assert table.column("second_homes").to_pylist() == [20.0, 20.0]


def test_loads_2021_commune_columns_from_zip_without_full_extraction(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "census.zip"
    csv_content = (
        "CODGEO;P21_LOG;P21_RP;P21_RSECOCC;P21_LOGVAC\n"
        "33001;120;80;20;20\n"
        "34001;100;70;10;20\n"
    )
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("dossier_complet.csv", csv_content)
    config = load_origins_config()
    config.census[2021] = CensusVintageConfig(
        format="zip_csv",
        path=str(archive_path),
        member="dossier_complet.csv",
        delimiter=";",
        geography_column="CODGEO",
        measures={
            "dwellings": "P21_LOG",
            "main_residences": "P21_RP",
            "second_homes": "P21_RSECOCC",
            "vacant": "P21_LOGVAC",
        },
    )
    connection = duckdb.connect()
    try:
        table = load_census_department(connection, 2021, "33", config)
    finally:
        connection.close()

    assert table.num_rows == 1
    assert table.column("commune_code").to_pylist() == ["33001"]
    assert table.column("dwellings").to_pylist() == [120.0]


def test_report_scenarios_compare_matched_communes_and_suppress_small_counts() -> None:
    census = pa.Table.from_pylist(
        [
            {
                "commune_code": "33001",
                "dwellings": 120.0,
                "main_residences": 80.0,
                "second_homes": 20.0,
                "vacant": 20.0,
            },
            {
                "commune_code": "33002",
                "dwellings": 120.0,
                "main_residences": 100.0,
                "second_homes": 10.0,
                "vacant": 10.0,
            },
            {
                "commune_code": "33003",
                "dwellings": 40.0,
                "main_residences": 30.0,
                "second_homes": 5.0,
                "vacant": 5.0,
            },
        ]
    )
    ff_communes = pa.Table.from_pylist(
        [
            {
                "commune_code": "33001",
                "dwellings": 120,
                "main_residences": 90,
                "vacant": 15,
                "second_homes": 15,
                "recent_transfers": 10,
                "owner_occupied_main_residences": 50,
                "owner_occupied_second_homes": 10,
                "owner_occupied_recent_transfers": 10,
                "social_housing_main_residences": 50,
            },
            {
                "commune_code": "33002",
                "dwellings": 120,
                "main_residences": 90,
                "vacant": 10,
                "second_homes": 20,
                "recent_transfers": 10,
                "owner_occupied_main_residences": 45,
                "owner_occupied_second_homes": 5,
                "owner_occupied_recent_transfers": 5,
                "social_housing_main_residences": 45,
            },
            {
                "commune_code": "33004",
                "dwellings": 60,
                "main_residences": 40,
                "vacant": 10,
                "second_homes": 10,
                "recent_transfers": 2,
                "owner_occupied_main_residences": 20,
                "owner_occupied_second_homes": 5,
                "owner_occupied_recent_transfers": 2,
                "social_housing_main_residences": 20,
            },
        ]
    )

    summary = calculate_report_summary(
        census,
        ff_communes,
        (0.1, 0.5, 0.9),
        10,
    )
    config = load_origins_config()
    report = render_commune_report(
        summary,
        2024,
        2023,
        "33",
        config.census[2023],
        (0.1, 0.5, 0.9),
        {"premises_without_coordinates": 4},
        (60.0, 70.0),
        50,
    )

    assert summary.matched_communes == 2
    assert summary.census_only_communes == 1
    assert summary.ff_only_communes == 1
    assert summary.top_second_home_gaps[0]["commune_code"] == "33002"
    assert summary.scenario_nmae["configured"] is not None
    assert summary.scenario_nmae["split_recent"] is not None
    split_main = next(
        row
        for row in summary.statistics
        if row["scenario"] == "split_recent" and row["metric"] == "main_residences"
    )
    assert split_main["matched_ff_total"] == pytest.approx(
        176.8888888889,
        abs=1e-8,
    )
    closest = min(
        summary.scenario_nmae,
        key=lambda scenario: (
            summary.scenario_nmae[scenario]
            if summary.scenario_nmae[scenario] is not None
            else float("inf")
        ),
    )
    assert closest == "split_recent", summary.scenario_nmae
    assert "<50" in report
    assert "Closest under the stated error metric:" in report
    assert "COM-33001" not in report


def test_build_commune_report_includes_social_housing_aggregates(
    tmp_path: Path,
) -> None:
    config_values = yaml.safe_load(
        Path("config/origins.yaml").read_text(encoding="utf-8")
    )
    output_directory = tmp_path / "interim"
    output_directory.mkdir()
    census_path = tmp_path / "census.parquet"
    measure_values = {
        "DWELLINGS": 120.0,
        "DWELLINGS_OCS_DW_MAIN": 80.0,
        "DWELLINGS_OCS_DW_SEC_DW_OCC": 20.0,
        "DWELLINGS_OCS_DW_VAC": 20.0,
    }
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "GEO": f"COM-{code}",
                    "GEO_OBJECT": "COM",
                    "TIME_PERIOD": "2023",
                    "ID_TAB": "LOG_T1",
                    "DS": "DS_RP_SERIE_HISTORIQUE",
                    "TAB_MEASURE": measure,
                    "OBS_VALUE": value,
                }
                for code in ("33001", "33002")
                for measure, value in measure_values.items()
            ]
        ),
        census_path,
    )
    config_values["census"][2023]["path"] = str(census_path)
    config_values["report"]["output_directory"] = str(output_directory)

    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "vintage": 2024,
                    "commune_code": code,
                    "dwellings": 120,
                    "main_residences": 90,
                    "vacant": 15,
                    "second_homes": 15,
                    "recent_transfers": 10,
                    "owner_occupied_main_residences": 50,
                    "owner_occupied_second_homes": 10,
                    "owner_occupied_recent_transfers": 10,
                    "social_housing_main_residences": 60,
                }
                for code in ("33001", "33002")
            ]
        ),
        output_directory / "ff_communes_2024.parquet",
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "cell_id": 1_200_020_000,
                    "social_housing_main_residences": 60,
                }
            ]
        ),
        output_directory / "ff_cells_2024.parquet",
    )
    (output_directory / "ff_cells_2024.json").write_text(
        json.dumps({"diagnostics": {"premises_without_coordinates": 4}}),
        encoding="utf-8",
    )
    filosofi_archive = tmp_path / "filosofi.zip"
    with zipfile.ZipFile(filosofi_archive, "w") as archive:
        archive.writestr(
            "carreaux_200m_met.csv",
            "idcar_200m,lcog_geo,log_soc\nCRS3035RES200mN2400000E4000000,33001,70\n",
        )
    config_values["filosofi"]["200m_archive"] = str(filosofi_archive)
    config_path = tmp_path / "origins.yaml"
    config_path.write_text(
        yaml.safe_dump(config_values, sort_keys=False),
        encoding="utf-8",
    )

    report_path = build_commune_report(
        2024,
        "33",
        config_path=config_path,
    )
    content = report_path.read_text(encoding="utf-8")

    assert report_path.name == "ff_commune_report_2024.md"
    assert "FF social main residences: 60.0" in content
    assert "Filosofi `log_soc`: 70.0" in content
    assert "Closest under the stated error metric:" in content
