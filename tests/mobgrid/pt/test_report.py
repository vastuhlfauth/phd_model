"""Smoke tests for the section 5.6 calibration report (2026-10-14 BHNS update)."""

from __future__ import annotations

import yaml
from mobgrid.pt.config import GtfsRebuildConfig
from mobgrid.pt.relation_pipeline import GridPoint, RelationCalibrationRun, RouteRun
from mobgrid.pt.report import write_report
from mobgrid.pt.route_calibration import FamilyScore
from mobgrid.pt.route_relations import RelationMatch, RoutePattern, RouteResult


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


def _route(route_id: str, *, is_bhns: bool, outcome: str) -> RouteRun:
    pattern = RoutePattern(
        route_id, route_id, route_id, f"Line {route_id}", "bus", "Op", 10, (),
        is_bhns=is_bhns,
    )
    match = RelationMatch("name", (1,), ("1",), 0.8)
    result = RouteResult(route_id, outcome, "name", (1,), ("1",), 10, 8, 0.8, 0, 9)
    return RouteRun("net", "2022-01-01", pattern, match, result, "kept", False, None)


def test_write_report_renders_bus_coverage_bhns_and_review_sections(
    tmp_path,
) -> None:
    pt_changes_path = tmp_path / "pt_changes.yaml"
    pt_changes_path.write_text(
        yaml.safe_dump(
            {
                "confirmed": [],
                "to_review": [
                    {
                        "id": "candidate_net_X",
                        "network": "net",
                        "route_id": "X",
                        "outcomes_by_date": {"2022-01-01": "cut"},
                        "match_pass": "name",
                        "relation_ids": [1],
                        "relation_refs": ["1"],
                        "covered_share": 0.6,
                        "trip_count": 50,
                        "is_bhns": True,
                        "network_coverage_by_date": {"2022-01-01": 0.95},
                    }
                ],
                "not_applied": [
                    {
                        "id": "candidate_net_Y",
                        "network": "net",
                        "route_id": "Y",
                        "outcomes_by_date": {"2022-01-01": "dropped"},
                        "match_pass": None,
                        "relation_ids": [],
                        "relation_refs": [],
                        "covered_share": 0.0,
                        "trip_count": 1,
                        "is_bhns": False,
                        "network_coverage_by_date": {"2022-01-01": 0.4},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    run = RelationCalibrationRun(
        grid=[
            GridPoint(
                "bus", 25, 2, 0.5, 0.5,
                FamilyScore("bus", 0, 0, 1.0, 1.0, 1.0, 1, 0.0),
            )
        ],
        chosen={
            family: GridPoint(
                family, 25, 2, 0.5, 0.5,
                FamilyScore(family, 0, 0, 1.0, 1.0, 1.0, 1, 0.0),
            )
            for family in ("bus", "tram", "metro", "rail", "ferry")
        },
        final_routes=[
            _route("X", is_bhns=True, outcome="cut"),
            _route("Y", is_bhns=False, outcome="dropped"),
        ],
    )
    destination = tmp_path / "report.md"

    write_report(run, _config(), destination, pt_changes_path=pt_changes_path)

    text = destination.read_text(encoding="utf-8")
    assert "Bus and ferry policy" in text
    assert "net | 2022-01-01 | 2 | 2 | 100%" in text
    assert "| net | X | X | Line X | 80% |" in text
    assert "candidate_net_X" not in text  # ids are internal, not rendered
    assert "| net | X | yes | 50 | name | 2022-01-01: cut | 60% |" in text
    assert "`net`: 1" in text
