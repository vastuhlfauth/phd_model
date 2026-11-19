import json

import duckdb
from mobgrid.osm.config import load_network_config
from mobgrid.osm.extract import build_area, read_area_cache, write_area_cache


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
