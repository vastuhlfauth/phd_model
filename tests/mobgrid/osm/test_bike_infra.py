import duckdb
import pytest
from mobgrid.osm.bike_infra import (
    bike_infrastructure_sql,
    classify_bike_infrastructure,
    parse_maxspeed_kmh,
)
from mobgrid.osm.config import load_network_config


@pytest.mark.parametrize(
    ("tags", "forward", "bike_access", "expected"),
    [
        ({"highway": "cycleway"}, True, True, "separated_track_path"),
        (
            {"highway": "path", "bicycle": "designated"},
            True,
            True,
            "separated_track_path",
        ),
        ({"cycleway": "track"}, False, True, "separated_track_path"),
        (
            {"cycleway:right": "track"},
            True,
            True,
            "separated_track_path",
        ),
        ({"cycleway:right": "track"}, False, True, "mixed_traffic"),
        ({"cycleway:left": "track"}, True, True, "mixed_traffic"),
        (
            {"cycleway:left": "track"},
            False,
            True,
            "separated_track_path",
        ),
        ({"cycleway": "lane"}, True, True, "painted_lane"),
        ({"cycleway": "lane"}, False, True, "painted_lane"),
        ({"cycleway:both": "lane"}, True, True, "painted_lane"),
        ({"cycleway:both": "lane"}, False, True, "painted_lane"),
        ({"cycleway": "share_busway"}, True, True, "bus_lane"),
        (
            {"highway": "residential", "busway": "lane"},
            True,
            True,
            "bus_lane",
        ),
        ({"highway": "living_street"}, True, True, "low_speed"),
        (
            {"highway": "residential", "maxspeed": "FR:zone30"},
            True,
            True,
            "low_speed",
        ),
        (
            {"highway": "residential", "bicycle_road": "yes"},
            False,
            True,
            "low_speed",
        ),
        ({"highway": "residential"}, True, True, "mixed_traffic"),
        ({"highway": "cycleway"}, True, False, None),
    ],
)
def test_bike_class_table_and_directional_cycleway_tags(
    tags, forward, bike_access, expected
) -> None:
    config = load_network_config("config/network.yaml")

    assert (
        classify_bike_infrastructure(
            tags,
            forward=forward,
            bike_access=bike_access,
            config=config,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("FR:urban", 50.0),
        ("FR:rural", 80.0),
        ("FR:zone30", 30.0),
        ("FR:motorway", 130.0),
        ("walk", 5.0),
        ("none", None),
        ("unknown", None),
        ("80 mph", 128.74752),
        ("30 km/h", 30.0),
    ],
)
def test_maxspeed_is_parsed_to_km_per_hour(value, expected) -> None:
    config = load_network_config("config/network.yaml")

    assert parse_maxspeed_kmh(value, config) == expected


def test_vectorized_bike_class_sql_matches_directional_classifier() -> None:
    config = load_network_config("config/network.yaml")
    connection = duckdb.connect()
    cases = [
        ({"highway": "cycleway"}, True, True),
        ({"cycleway:right": "track"}, True, True),
        ({"cycleway:right": "track"}, False, True),
        ({"cycleway:left": "lane"}, False, True),
        ({"cycleway": "lane"}, True, True),
        ({"cycleway": "lane"}, False, True),
        ({"cycleway:both": "lane"}, True, True),
        ({"cycleway:both": "lane"}, False, True),
        ({"busway": "lane"}, True, True),
        ({"maxspeed": "FR:zone30"}, True, True),
        ({"highway": "residential"}, True, False),
    ]

    for tags, forward, bike_access in cases:
        entries = ", ".join(
            f"'{key}':'{value}'" for key, value in tags.items()
        )
        expression = bike_infrastructure_sql(
            "tags", "forward", "bike_access", config
        )
        actual = connection.execute(
            f"""
            SELECT {expression}
            FROM (
                SELECT map {{{entries}}} AS tags,
                       {str(forward).upper()} AS forward,
                       {str(bike_access).upper()} AS bike_access
            )
            """
        ).fetchone()[0]
        expected = classify_bike_infrastructure(
            tags,
            forward=forward,
            bike_access=bike_access,
            config=config,
        )
        assert actual == expected
