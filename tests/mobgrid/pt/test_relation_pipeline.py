"""End-to-end synthetic tests for relation calibration orchestration."""

from mobgrid.pt.config import GtfsRebuildConfig
from mobgrid.pt.relation_pipeline import GridPoint, _rank, evaluate_networks
from mobgrid.pt.route_calibration import FamilyScore
from mobgrid.pt.route_relations import OSMRelation, OSMWay, RoutePattern


def _pattern(route_id: str, x: float) -> RoutePattern:
    return RoutePattern(
        route_id,
        route_id,
        route_id,
        route_id,
        "bus",
        "Operator",
        10,
        ((x, 0.0), (x + 10, 0.0)),
    )


def _config() -> GtfsRebuildConfig:
    return GtfsRebuildConfig.model_validate(
        {
            "reference_date": "2026-10-13",
            "osm_lifecycle_prefixes": ["construction"],
            "osm_source_ids": {"2022-01-01": "osm"},
            "osm_cache_root": "unused",
            "osm_route_cache_root": "unused",
            "calibration": {
                "r_m": [25],
                "theta": [0.5],
                "k": [2],
                "geometry_share": [0.5],
            },
            "chosen": {
                family: {
                    "r_m": None,
                    "theta": None,
                    "k": None,
                    "geometry_share": None,
                }
                for family in ("bus", "tram", "metro", "rail", "ferry")
            },
            "networks": {},
            "test_epcis": {},
            "known_cases": [],
        }
    )


def test_network_below_half_relations_retains_every_route_not_testable() -> None:
    patterns = {
        "network": [
            _pattern("A", 0),
            _pattern("B", 5_000),
            _pattern("C", 10_000),
        ]
    }
    relation = OSMRelation(
        1,
        "A",
        "A",
        None,
        "Operator",
        "bus",
        (),
        (OSMWay(((-10, 0), (20, 0)), highway="service"),),
    )
    runs, flagged = evaluate_networks(
        patterns,
        {"2022-01-01": [relation]},
        _config(),
        r_m=25,
        k=2,
        theta=0.5,
        geometry_share=0.5,
    )
    assert {run.result.outcome for run in runs} == {"not-testable"}
    assert flagged == {("2022-01-01", "network")}


def test_parameter_ranking_prefers_exact_known_cases_before_false_changes() -> None:
    exact = GridPoint(
        "bus",
        100,
        2,
        0.7,
        0.5,
        FamilyScore("bus", 2, 2, 1.0, 1.0, 1.0, 10, 0.2),
    )
    low_false_changes = GridPoint(
        "bus",
        25,
        1,
        0.5,
        0.3,
        FamilyScore("bus", 2, 1, 1.0, 0.5, 2 / 3, 10, 0.0),
    )
    assert _rank(exact) > _rank(low_false_changes)
