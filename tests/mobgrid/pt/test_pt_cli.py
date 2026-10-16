"""Tests for the review-list reduction of candidate route changes (5.6.3)."""

from __future__ import annotations

import time

import yaml
from mobgrid.pt.cli import _calibration_run_signature, _write_review_lists
from mobgrid.pt.config import GtfsRebuildConfig
from mobgrid.pt.relation_pipeline import RelationCalibrationRun, RouteRun
from mobgrid.pt.route_relations import RelationMatch, RoutePattern, RouteResult


def _signature_config(route_cache_root: str) -> GtfsRebuildConfig:
    return GtfsRebuildConfig.model_validate(
        {
            "reference_date": "2026-10-13",
            "osm_lifecycle_prefixes": ["construction"],
            "osm_source_ids": {"2022-01-01": "osm"},
            "osm_cache_root": "unused",
            "osm_route_cache_root": route_cache_root,
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


def _write_route_cache_files(root) -> None:
    root.mkdir(parents=True, exist_ok=True)
    cache = root / "2022-01-01"
    cache.mkdir()
    for name in ("relations", "ways", "stops"):
        (cache / f"{name}.parquet").write_text("stub", encoding="utf-8")


def test_calibration_run_signature_changes_when_a_route_cache_file_is_rebuilt(
    tmp_path,
) -> None:
    root = tmp_path / "routes"
    _write_route_cache_files(root)
    config = _signature_config(str(root))
    before = _calibration_run_signature(config, "inv.csv", "sources.yaml", "c.gz", None)

    # Simulate a ways.parquet schema upgrade: same name, new content/mtime.
    time.sleep(0.01)
    (root / "2022-01-01" / "ways.parquet").write_text(
        "stub-with-busway-column", encoding="utf-8"
    )
    after = _calibration_run_signature(config, "inv.csv", "sources.yaml", "c.gz", None)

    assert before != after


def test_calibration_run_signature_is_stable_for_unchanged_inputs(tmp_path) -> None:
    root = tmp_path / "routes"
    _write_route_cache_files(root)
    config = _signature_config(str(root))

    first = _calibration_run_signature(config, "inv.csv", "sources.yaml", "c.gz", None)
    second = _calibration_run_signature(config, "inv.csv", "sources.yaml", "c.gz", None)

    assert first == second


def _route_run(
    network: str,
    date_key: str,
    route_id: str,
    outcome: str,
    *,
    mode: str = "bus",
    trip_count: int = 1,
    is_bhns: bool = False,
    relation_ids: tuple[int, ...] = (1,),
) -> RouteRun:
    pattern = RoutePattern(
        route_id,
        route_id,
        route_id,
        route_id,
        mode,
        "Operator",
        trip_count,
        (),
        is_bhns=is_bhns,
    )
    match = RelationMatch("name", relation_ids, (), 0.8)
    result = RouteResult(
        route_id, outcome, "name", relation_ids, (), 10, 8, 0.8, 0, 9
    )
    return RouteRun(network, date_key, pattern, match, result, "kept", False, None)


def test_non_bhns_kept_renamed_candidate_stays_not_applied(tmp_path) -> None:
    path = tmp_path / "pt_changes.yaml"
    path.write_text(
        yaml.safe_dump({"confirmed": [], "to_review": [], "not_applied": []}),
        encoding="utf-8",
    )
    run = RelationCalibrationRun(
        final_routes=[
            # Not BHNS and never dropped (kept-renamed only): not eligible
            # under the new bus/ferry rule, regardless of network coverage
            # (2026-10-15 decision).
            _route_run("rural", "2022-01-01", "A", "kept-renamed"),
            *[
                _route_run("rural", "2022-01-01", f"z{i}", "kept", relation_ids=())
                for i in range(4)
            ],
        ]
    )

    _write_review_lists(path, run)

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert raw["to_review"] == []
    assert [c["route_id"] for c in raw["not_applied"]] == ["A"]
    assert raw["not_applied"][0]["network_coverage_by_date"] == {
        "2022-01-01": 0.2
    }


def test_dropped_non_bhns_candidate_is_eligible_regardless_of_coverage(
    tmp_path,
) -> None:
    path = tmp_path / "pt_changes.yaml"
    path.write_text(
        yaml.safe_dump({"confirmed": [], "to_review": [], "not_applied": []}),
        encoding="utf-8",
    )
    run = RelationCalibrationRun(
        final_routes=[
            # Low network/date coverage (1/5 matched = 20%), but dropped
            # under the new fixed name/geometry-share rule: eligible for
            # review regardless (2026-10-15 decision).
            _route_run("rural", "2022-01-01", "A", "dropped"),
            *[
                _route_run("rural", "2022-01-01", f"z{i}", "kept", relation_ids=())
                for i in range(4)
            ],
        ]
    )

    _write_review_lists(path, run)

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert [c["route_id"] for c in raw["to_review"]] == ["A"]
    assert raw["not_applied"] == []



def test_bhns_ranks_before_higher_coverage_non_bhns_by_trips(tmp_path) -> None:
    path = tmp_path / "pt_changes.yaml"
    path.write_text(
        yaml.safe_dump({"confirmed": [], "to_review": [], "not_applied": []}),
        encoding="utf-8",
    )
    # 9/10 matched in this network/date -> 90% coverage, eligible.
    well_covered = [
        _route_run("urban", "2022-01-01", "express", "dropped", trip_count=5,
                    is_bhns=True),
        _route_run("urban", "2022-01-01", "frequent", "dropped", trip_count=50),
        *[
            _route_run("urban", "2022-01-01", f"w{i}", "kept")
            for i in range(8)
        ],
    ]
    run = RelationCalibrationRun(final_routes=well_covered)

    _write_review_lists(path, run)

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    reviewed_ids = [c["route_id"] for c in raw["to_review"]]
    assert reviewed_ids == ["express", "frequent"]
    assert raw["not_applied"] == []


def test_rail_has_its_own_top_30_cap_separate_from_bus(tmp_path) -> None:
    path = tmp_path / "pt_changes.yaml"
    path.write_text(
        yaml.safe_dump({"confirmed": [], "to_review": [], "not_applied": []}),
        encoding="utf-8",
    )
    # Bus/ferry have no cap under the new rule (2026-10-15 decision): every
    # one of these 55 dropped routes is eligible for review.
    bus_routes = [
        _route_run(
            "net", "2022-01-01", f"b{i}", "dropped", trip_count=1000 - i
        )
        for i in range(55)
    ]
    # Rail keeps its own 90%-coverage gate and top-30-by-trips cap: every
    # route here is matched (100% network coverage, eligible), and with 35
    # dropped rail candidates, 5 must spill into not_applied.
    rail_routes = [
        _route_run(
            "net",
            "2022-01-01",
            f"r{i}",
            "dropped",
            mode="rail",
            trip_count=100 - i,
        )
        for i in range(35)
    ] + [
        _route_run("net", "2022-01-01", f"rk{i}", "kept", mode="rail")
        for i in range(4)
    ]
    run = RelationCalibrationRun(final_routes=[*bus_routes, *rail_routes])

    _write_review_lists(path, run)

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    reviewed = {c["route_id"] for c in raw["to_review"]}
    not_applied = {c["route_id"] for c in raw["not_applied"]}
    # All 55 bus candidates are reviewed; only 30 of the 35 rail
    # candidates are, capped independently of bus's own (uncapped) count.
    assert sum(1 for r in reviewed if r.startswith("b")) == 55
    assert sum(1 for r in reviewed if r.startswith("r")) == 30
    assert sum(1 for r in not_applied if r.startswith("r")) == 5
    assert not_applied == {f"r{i}" for i in range(30, 35)}


def test_confirmed_routes_are_excluded_from_both_lists(tmp_path) -> None:
    path = tmp_path / "pt_changes.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "confirmed": [
                    {
                        "id": "x",
                        "type": "pt_new_line",
                        "network": "urban",
                        "route_ids": ["express"],
                        "description": "d",
                    }
                ],
                "to_review": [],
                "not_applied": [],
            }
        ),
        encoding="utf-8",
    )
    run = RelationCalibrationRun(
        final_routes=[
            _route_run("urban", "2022-01-01", "express", "dropped"),
            *[_route_run("urban", "2022-01-01", f"w{i}", "kept") for i in range(9)],
        ]
    )

    _write_review_lists(path, run)

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    all_ids = [c["route_id"] for c in (*raw["to_review"], *raw["not_applied"])]
    assert "express" not in all_ids


def test_rejected_routes_are_not_re_surfaced_on_rerun(tmp_path) -> None:
    path = tmp_path / "pt_changes.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "confirmed": [],
                "to_review": [],
                "not_applied": [],
                "rejected": [
                    {
                        "id": "candidate_urban_05",
                        "network": "urban",
                        "route_id": "05",
                        "outcomes_by_date": {"2022-01-01": "dropped"},
                        "match_pass": "name",
                        "covered_share": 0.5,
                        "notes": "reviewer confirmed false positive",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    run = RelationCalibrationRun(
        final_routes=[
            _route_run("urban", "2022-01-01", "05", "dropped"),
            *[_route_run("urban", "2022-01-01", f"w{i}", "kept") for i in range(9)],
        ]
    )

    _write_review_lists(path, run)

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    all_ids = [c["route_id"] for c in (*raw["to_review"], *raw["not_applied"])]
    assert "05" not in all_ids
    assert raw["rejected"][0]["route_id"] == "05"
