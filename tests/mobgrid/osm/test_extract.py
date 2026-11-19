import json
from pathlib import Path

import duckdb
import pytest
from mobgrid.osm.config import load_network_config
from mobgrid.osm.extract import (
    AreaGeometry,
    build_area,
    extract_osm_pbf,
    read_area_cache,
    write_area_cache,
)
from mobgrid.pt.osm_route_extraction import configure_extraction_connection


def _polygon_feature(department: str, west: float) -> dict:
    return {
        "type": "Feature",
        "properties": {"departement": department},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [west, 44.0],
                [west + 0.01, 44.0],
                [west + 0.01, 44.01],
                [west, 44.01],
                [west, 44.0],
            ]],
        },
    }


def test_network_config_loads_state_sources_and_tile_size() -> None:
    config = load_network_config("config/network.yaml")

    assert config.states == {2021: "osm-2022", 2023: "osm-2024"}
    assert config.tile_size_m == 50_000
    assert config.maxspeed_tokens_kmh["FR:urban"] == 50


def test_pilot_area_dissolves_communes_buffers_and_caches_bbox(tmp_path) -> None:
    contours = tmp_path / "communes.geojson"
    contours.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    _polygon_feature("33", -0.5),
                    _polygon_feature("33", -0.48),
                    _polygon_feature("44", -0.4),
                ],
            }
        ),
        encoding="utf-8",
    )
    connection = duckdb.connect()
    area = build_area(
        connection, contours, area="pilot", department="33", halo_km=5
    )

    assert area.west < -0.5
    assert area.east > -0.47
    assert area.south < 44.0
    assert area.north > 44.01

    cache = tmp_path / "area.parquet"
    write_area_cache(connection, cache, area)
    assert read_area_cache(connection, cache) == area


def test_national_area_excludes_corsica_and_overseas_departments(tmp_path) -> None:
    contours = tmp_path / "communes.geojson"
    contours.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    _polygon_feature("33", -0.5),
                    _polygon_feature("2A", 8.0),
                    _polygon_feature("971", -61.0),
                ],
            }
        ),
        encoding="utf-8",
    )
    area = build_area(
        duckdb.connect(),
        contours,
        area="national",
        department="33",
        halo_km=1,
    )

    assert area.west > -1
    assert area.east < 1


@pytest.mark.pilot
def test_monaco_pbf_extracts_cached_ways_and_nodes(tmp_path) -> None:
    pbf = Path("data/raw/osm/220101/monaco-220101.osm.pbf")
    if not pbf.is_file():
        pytest.skip("Monaco OSM extract is not available")

    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    configure_extraction_connection(connection, tmp_path / "interim")
    area_wkb = connection.execute(
        """
        SELECT ST_AsWKB(ST_Transform(
            ST_GeomFromText(
                'POLYGON ((7.40 43.72, 7.46 43.72, 7.46 43.77, '
                '7.40 43.77, 7.40 43.72))'
            ),
            'EPSG:4326', 'EPSG:3035', true
        ))
        """
    ).fetchone()[0]
    area = AreaGeometry(bytes(area_wkb), 7.4, 43.72, 7.46, 43.77)
    cache = tmp_path / "osm" / "2021" / "monaco"
    config = load_network_config("config/network.yaml")

    summary = extract_osm_pbf(
        connection,
        pbf,
        cache,
        area,
        config=config,
    )
    ways_stage = cache / "_stages" / "ways_candidates.parquet"
    ways_stage_mtime = ways_stage.stat().st_mtime_ns
    resumed = extract_osm_pbf(
        connection,
        pbf,
        cache,
        area,
        config=config,
    )

    assert summary.way_count > 0
    assert summary.node_count > 0
    assert (resumed.way_count, resumed.node_count) == (
        summary.way_count,
        summary.node_count,
    )
    assert ways_stage.stat().st_mtime_ns == ways_stage_mtime
    assert (cache / "_SUCCESS.json").is_file()
    assert (cache / "_stages" / "ways_candidates.parquet").is_file()
    out_of_bounds_controls = connection.execute(
        """
        SELECT count(*)
        FROM read_parquet(?)
        WHERE lon < ? OR lon > ? OR lat < ? OR lat > ?
        """,
        [
            str(cache / "_stages" / "control_nodes_candidates.parquet"),
            area.west,
            area.east,
            area.south,
            area.north,
        ],
    ).fetchone()[0]
    assert out_of_bounds_controls == 0
    missing_way_nodes = connection.execute(
        """
        WITH way_node_ids AS (
            SELECT DISTINCT unnest(refs) AS node_id
            FROM read_parquet(?)
        )
        SELECT count(*)
        FROM way_node_ids w
        LEFT JOIN read_parquet(?) n USING (node_id)
        WHERE n.node_id IS NULL
        """,
        [str(cache / "ways.parquet"), str(cache / "nodes.parquet")],
    ).fetchone()[0]
    assert missing_way_nodes == 0
