import json
from types import SimpleNamespace

import duckdb
import mobgrid.osm.geovelo_report as geovelo_report
import pytest
from mobgrid.osm.config import load_network_config
from mobgrid.osm.geovelo_report import write_geovelo_report_section


def _write_synthetic_inputs(tmp_path):
    connection = duckdb.connect()
    ways = tmp_path / "ways.parquet"
    nodes = tmp_path / "nodes.parquet"
    edges = tmp_path / "edges.parquet"
    connection.execute("""
        COPY (
            SELECT * FROM (VALUES
                (1::BIGINT, map {
                    'highway':'residential',
                    'cycleway:left':'lane',
                    'cycleway:right':'lane'
                }, [1::BIGINT, 2::BIGINT]),
                (2::BIGINT, map {
                    'highway':'path',
                    'bicycle':'designated',
                    'oneway':'no'
                }, [1::BIGINT, 2::BIGINT]),
                (3::BIGINT, map {
                    'highway':'residential',
                    'cycleway:both':'lane'
                }, [1::BIGINT, 2::BIGINT]),
                (4::BIGINT, map {
                    'highway':'path',
                    'bicycle':'yes'
                }, [3::BIGINT, 4::BIGINT]),
                (5::BIGINT, map {
                    'highway':'residential',
                    'cycleway:right':'track'
                }, [3::BIGINT, 4::BIGINT])
            ) AS ways(way_id, tags, refs)
        ) TO ? (FORMAT PARQUET)
    """, [str(ways)])
    connection.execute("""
        COPY (
            SELECT * FROM (VALUES
                (1::BIGINT, 48.85::DOUBLE, 2.35::DOUBLE),
                (2::BIGINT, 48.85::DOUBLE, 2.351::DOUBLE),
                (3::BIGINT, 48.85::DOUBLE, 2.36::DOUBLE),
                (4::BIGINT, 48.85::DOUBLE, 2.361::DOUBLE)
            ) AS nodes(node_id, lat, lon)
        ) TO ? (FORMAT PARQUET)
    """, [str(nodes)])
    connection.execute("""
        COPY (
            SELECT * FROM (VALUES
                (1::BIGINT, 'bike', true, true),
                (2::BIGINT, 'bike', false, true),
                (3::BIGINT, 'bike', true, true),
                (4::BIGINT, 'bike', false, true),
                (5::BIGINT, 'bike', true, true)
            ) AS edges(way_id, mode, car_access, bike_access)
        ) TO ? (FORMAT PARQUET)
    """, [str(edges)])
    connection.close()

    contours = tmp_path / "communes.geojson"
    contours.write_text(
        json.dumps({
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {
                    "code": "75056",
                    "nom": "Paris",
                    "departement": "75",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [2.34, 48.84],
                        [2.37, 48.84],
                        [2.37, 48.86],
                        [2.34, 48.86],
                        [2.34, 48.84],
                    ]],
                },
            }],
        }),
        encoding="utf-8",
    )
    geovelo = tmp_path / "geovelo.geojson"
    geovelo.write_text(
        json.dumps({
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "ame_d": "BANDE CYCLABLE",
                        "ame_g": "BANDE CYCLABLE",
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[2.35, 48.85], [2.351, 48.85]],
                    },
                },
                {
                    "type": "Feature",
                    "properties": {
                        "ame_d": "PISTE CYCLABLE",
                        "ame_g": "PISTE CYCLABLE",
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[2.35, 48.85], [2.351, 48.85]],
                    },
                },
                {
                    "type": "Feature",
                    "properties": {
                        "ame_d": "NOUVELLE VALEUR",
                        "ame_g": "AUCUN",
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[2.352, 48.85], [2.353, 48.85]],
                    },
                },
                {
                    "type": "Feature",
                    "properties": {
                        "ame_d": "DOUBLE SENS CYCLABLE NON MATERIALISE",
                        "ame_g": None,
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[2.354, 48.85], [2.355, 48.85]],
                    },
                },
                {
                    "type": "Feature",
                    "properties": {
                        "ame_d": "HORS DEPARTEMENT",
                        "ame_g": "HORS DEPARTEMENT",
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[2.38, 48.85], [2.381, 48.85]],
                    },
                },
            ],
        }),
        encoding="utf-8",
    )
    return ways, nodes, edges, contours, geovelo


def test_report_counts_two_sided_lanes_and_two_way_paths_once(tmp_path) -> None:
    ways, nodes, edges, contours, geovelo = _write_synthetic_inputs(tmp_path)
    report = tmp_path / "step06.md"
    report.write_text(
        "# Step 6\n\n## Géovélo comparison\nSTALE_SECTION\n\n## Edge costs\nkeep",
        encoding="utf-8",
    )
    connection = duckdb.connect()
    connection.execute("INSTALL spatial; LOAD spatial")

    write_geovelo_report_section(
        connection,
        report,
        ways_path=ways,
        nodes_path=nodes,
        edges_path=edges,
        geovelo_path=geovelo,
        contours_path=contours,
        department="75",
        source_id="geovelo-2022",
        config=load_network_config("config/network.yaml"),
    )

    text = report.read_text(encoding="utf-8")
    rows = {
        line.split("|")[3].strip(): [
            float(line.split("|")[4].strip().replace(",", "")),
            float(line.split("|")[5].strip().replace(",", "")),
        ]
        for line in text.splitlines()
        if line.startswith("| 75056 |")
        and len(line.split("|")) == 7
    }
    assert rows["painted_lane"][0] == pytest.approx(
        rows["separated_track_path"][0] * 2, abs=0.2
    )
    assert rows["separated_track_path"][0] == pytest.approx(
        rows["separated_track_path"][1] * 2, abs=0.2
    )
    assert rows["painted_lane"][1] == pytest.approx(
        rows["separated_track_path"][1] * 2, abs=0.2
    )
    assert rows["low_speed"][1] > 0
    assert "BANDE CYCLABLE" in text
    assert "PISTE CYCLABLE" in text
    assert "NOUVELLE VALEUR" in text
    assert "HORS DEPARTEMENT" not in text
    assert "STALE_SECTION" not in text
    assert "## Edge costs\nkeep" in text
    assert "| ame_g | AUCUN | 1 |" in text
    assert "| 100.0% |" in text
    assert "Other car-free paths open to bikes (reported separately)" in text
    assert "| 75056 | Paris |" in text
    assert (
        "classification against Géovélo's, not OSM's completeness" in text
    )
    connection.close()


def test_standalone_command_uses_configured_pilot_sources(
    tmp_path, monkeypatch
) -> None:
    config = load_network_config("config/network.yaml")
    interim = tmp_path / "interim"
    base = tmp_path / "base"
    geovelo_path = tmp_path / "geovelo.geojson"
    contours_path = tmp_path / "contours.geojson"
    report_path = tmp_path / "step06.md"
    pilot = SimpleNamespace(
        paths={"interim": str(interim), "base": str(base)},
        department="75",
    )
    sources = [
        SimpleNamespace(id="geovelo-2022", local_path=geovelo_path),
        SimpleNamespace(id="contours-2021", local_path=contours_path),
    ]
    captured = {}

    monkeypatch.setattr(geovelo_report, "load_network_config", lambda _: config)
    monkeypatch.setattr(geovelo_report, "load_pilot_config", lambda _: pilot)
    monkeypatch.setattr(geovelo_report, "load_manifest", lambda _: sources)

    def capture_report(*call_args, **kwargs):
        captured["destination"] = call_args[1]
        captured.update(kwargs)

    monkeypatch.setattr(
        geovelo_report, "write_geovelo_report_section", capture_report
    )
    assert geovelo_report.main([
        "--state", "2021",
        "--config", str(tmp_path / "network.yaml"),
        "--manifest", str(tmp_path / "sources.yaml"),
        "--pilot-config", str(tmp_path / "pilot.yaml"),
        "--report", str(report_path),
    ]) == 0

    assert captured["destination"] == report_path
    assert captured["department"] == "75"
    assert captured["source_id"] == "geovelo-2022"
    assert captured["ways_path"] == (
        interim / "osm" / "2021" / "pilot" / "ways.parquet"
    )
    assert captured["nodes_path"] == (
        interim / "osm" / "2021" / "pilot" / "nodes.parquet"
    )
    assert captured["edges_path"] == (
        base / "network" / "2021" / "pilot" / "edges.parquet"
    )
    assert captured["geovelo_path"] == geovelo_path
    assert captured["contours_path"] == contours_path
