import json
from pathlib import Path

import duckdb
import pytest
from mobgrid.osm.config import load_network_config
from mobgrid.osm.extract import (
    AreaGeometry,
    _build_kept_nodes_query,
    _build_nodes_outside_bbox_query,
    _build_ways_candidates_query,
    _prepare_area_polygon,
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
    assert config.area_simplify_tolerance_m == 10
    assert config.maxspeed_tokens_kmh["FR:urban"] == 50
    assert {
        "zone:traffic",
        "source:maxspeed",
        "maxspeed:type",
        "zone:maxspeed",
        "tracktype",
        "service",
        "area",
    } <= set(config.kept_tags)


def test_point_in_area_uses_configured_simplified_polygon() -> None:
    connection = duckdb.connect()
    connection.execute("LOAD spatial")
    geometry = connection.execute(
        """
        SELECT ST_AsWKB(ST_GeomFromText(
            'POLYGON ((0 0, 0 100, 40 100, 40 90, 60 90, '
            '60 100, 100 100, 100 0, 0 0))'
        ))
        """
    ).fetchone()[0]
    area = AreaGeometry(bytes(geometry), 0, 0, 100, 100)
    config = load_network_config("config/network.yaml")

    _prepare_area_polygon(connection, area, config.area_simplify_tolerance_m)

    exact, simplified = connection.execute(
        """
        SELECT ST_Covers(
                   ST_GeomFromWKB(from_hex(?)), ST_Point(50, 91)
               ),
               ST_Covers(_osm_area.geom, ST_Point(50, 91))
        FROM _osm_area
        """,
        [area.geometry_wkb.hex()],
    ).fetchone()
    assert exact is False
    assert simplified is True


def test_extraction_passes_keep_area_ways_and_all_their_nodes(tmp_path) -> None:
    connection = duckdb.connect()
    connection.execute("""
        CREATE TABLE _osm_area_node_ids (node_id BIGINT);
        INSERT INTO _osm_area_node_ids VALUES (2), (5);
        CREATE TABLE osm_ways (
            kind VARCHAR,
            id BIGINT,
            tags MAP(VARCHAR, VARCHAR),
            refs BIGINT[]
        );
        INSERT INTO osm_ways VALUES
            ('way', 10, map {
                'highway':'residential', 'zone:traffic':'FR:urban',
                'source:maxspeed':'FR:rural', 'maxspeed:type':'FR:zone30',
                'zone:maxspeed':'FR:motorway', 'tracktype':'grade2',
                'service':'driveway', 'area':'yes'
            }, [1, 2]),
            ('way', 11, map {'highway':'service'}, [3, 4]),
            ('way', 12, map {'railway':'platform'}, [2, 3]),
            ('relation', 13, map {'highway':'residential'}, [2]);
        CREATE TABLE osm_nodes (
            kind VARCHAR,
            id BIGINT,
            tags MAP(VARCHAR, VARCHAR),
            lat DOUBLE,
            lon DOUBLE
        );
        INSERT INTO osm_nodes VALUES
            ('node', 1, map(), 44, -0.5),
            ('node', 2, map(), 44, -0.4),
            ('node', 3, map(), 44, -0.3),
            ('node', 4, map(), 44, -0.2),
            ('node', 5, map {'highway':'traffic_signals'}, 44, -0.1),
            ('node', 6, map(), 44, 0);
    """)
    config = load_network_config("config/network.yaml")
    ways_path = tmp_path / "ways.parquet"
    nodes_bbox_path = tmp_path / "nodes_in_bbox.parquet"
    nodes_outside_path = tmp_path / "nodes_outside_bbox.parquet"
    kept_nodes_path = tmp_path / "nodes.parquet"

    ways_query = _build_ways_candidates_query("osm_ways", config)
    connection.execute(f"CREATE TABLE kept_ways AS {ways_query}")
    assert connection.execute(
        "SELECT way_id FROM kept_ways ORDER BY way_id"
    ).fetchall() == [(10,), (12,)]
    assert connection.execute(
        """
        SELECT tags['zone:traffic'], tags['source:maxspeed'],
               tags['maxspeed:type'], tags['zone:maxspeed'],
               tags['tracktype'], tags['service'], tags['area']
        FROM kept_ways WHERE way_id = 10
        """
    ).fetchone() == (
        "FR:urban",
        "FR:rural",
        "FR:zone30",
        "FR:motorway",
        "grade2",
        "driveway",
        "yes",
    )
    connection.execute("COPY kept_ways TO ? (FORMAT PARQUET)", [str(ways_path)])
    connection.execute("""
        CREATE TABLE nodes_in_bbox AS
        SELECT id AS node_id, tags, lat, lon
        FROM osm_nodes
        WHERE id IN (2, 5)
    """)
    connection.execute(
        "COPY nodes_in_bbox TO ? (FORMAT PARQUET)", [str(nodes_bbox_path)]
    )
    outside_query = _build_nodes_outside_bbox_query(
        "osm_nodes", str(ways_path), str(nodes_bbox_path)
    )
    connection.execute(f"CREATE TABLE nodes_outside AS {outside_query}")
    assert connection.execute(
        "SELECT node_id FROM nodes_outside ORDER BY node_id"
    ).fetchall() == [(1,), (3,)]
    connection.execute(
        "COPY nodes_outside TO ? (FORMAT PARQUET)",
        [str(nodes_outside_path)],
    )
    kept_nodes_query = _build_kept_nodes_query(
        str(ways_path),
        str(nodes_bbox_path),
        str(nodes_outside_path),
        config.control_highways,
    )
    connection.execute(
        f"COPY ({kept_nodes_query}) TO ? (FORMAT PARQUET)",
        [str(kept_nodes_path)],
    )
    assert connection.execute(
        "SELECT node_id FROM read_parquet(?) ORDER BY node_id",
        [str(kept_nodes_path)],
    ).fetchall() == [(1,), (2,), (3,), (5,)]


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
    assert (cache / "_stages" / "nodes_in_bbox.parquet").is_file()
    assert (cache / "_stages" / "nodes_outside_bbox.parquet").is_file()
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
