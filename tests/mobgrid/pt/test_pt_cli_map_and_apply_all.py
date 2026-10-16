"""Tests for the ``map-and-apply-all`` batch command (section 5.6 point 5)."""

from __future__ import annotations

import csv
import zipfile
from pathlib import Path

import yaml
from mobgrid.pt.cli import main


def _write_gtfs_zip(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "routes.txt",
            "route_id,route_short_name,route_long_name,route_type\n"
            "59,A,Tram A,0\n",
        )
        archive.writestr("trips.txt", "trip_id,route_id\nt1,59\n")
        archive.writestr(
            "stop_times.txt", "trip_id,stop_id,stop_sequence\nt1,s1,1\n"
        )
        archive.writestr("stops.txt", "stop_id,stop_name\ns1,Stop One\n")


def _write_inventory_csv(path: Path, resource_id: int, local_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["resource_id", "local_path"])
        writer.writerow([str(resource_id), str(local_path)])


def _write_openings_csv(path: Path) -> None:
    path.write_text(
        "id,region,city,network,mode,line_2026,change_type,section_from,"
        "section_to,state_2022,state_2024,confidence\n"
        "O1,R,C,NetworkA,tram,A,new_line,,,remove,remove,high\n"
        "O2,R,C,NetworkB,tram,Z,new_line,,,remove,remove,high\n",
        encoding="utf-8",
    )


def _write_config(
    path: Path, network_resource_ids: dict[str, int] | None = None
) -> None:
    raw = {
        "reference_date": "2026-10-13",
        "osm_lifecycle_prefixes": ["construction"],
        "osm_source_ids": {"2022-01-01": "osm"},
        "osm_cache_root": "unused",
        "osm_route_cache_root": "unused",
        "calibration": {
            "r_m": [25], "theta": [0.5], "k": [2], "geometry_share": [0.5],
        },
        "chosen": {
            family: {"r_m": None, "theta": None, "k": None, "geometry_share": None}
            for family in ("bus", "tram", "metro", "rail", "ferry")
        },
        "national_policy": {
            "decision_date": "2026-10-15",
            "precedence": ["openings_list", "tram_automatic_rule", "default_keep"],
            "families": {
                "tram": {"rule": "automatic_osm"},
                "metro": {"rule": "default_keep_except_openings"},
                "rail": {"rule": "default_keep_except_openings"},
                "bus": {"rule": "default_keep_except_openings"},
                "ferry": {"rule": "default_keep_except_openings"},
            },
            "openings_list": {
                "source_csv": "openings.csv",
                "mapping_csv": "mapping.csv",
                "include_row_confidence": ["high", "medium"],
                "apply_match_confidence": ["exact", "stop-confirmed"],
                "network_resource_ids": network_resource_ids
                or {"NetworkA": 1, "NetworkB": 2},
            },
        },
        "networks": {},
        "test_epcis": {},
        "known_cases": [],
    }
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")


def test_map_and_apply_all_continues_past_one_networks_failure(
    tmp_path, caplog
) -> None:
    # NetworkA (resource 1) resolves and maps successfully; NetworkB
    # (resource 2) has no inventory row at all, so resolution fails --
    # the batch must still complete and apply NetworkA's result.
    config_path = tmp_path / "gtfs_rebuild.yaml"
    _write_config(config_path)
    openings_csv = tmp_path / "openings.csv"
    _write_openings_csv(openings_csv)
    gtfs_zip = tmp_path / "feeds" / "a.zip"
    _write_gtfs_zip(gtfs_zip)
    inventory_csv = tmp_path / "inventory.csv"
    _write_inventory_csv(inventory_csv, 1, gtfs_zip)  # only resource 1 exists
    mapping_csv = tmp_path / "mapping.csv"
    pt_changes = tmp_path / "pt_changes.yaml"
    pt_changes.write_text(
        yaml.safe_dump({"confirmed": [], "to_review": [], "not_applied": []}),
        encoding="utf-8",
    )
    log_path = tmp_path / "run.log"
    summary_path = tmp_path / "summary.md"

    with caplog.at_level("WARNING", logger="mobgrid.pt"):
        rc = main(
            [
                "map-and-apply-all",
                "--config", str(config_path),
                "--openings-csv", str(openings_csv),
                "--gtfs-inventory", str(inventory_csv),
                "--mapping-csv", str(mapping_csv),
                "--pt-changes", str(pt_changes),
                "--scratch-root", str(tmp_path / "scratch"),
                "--log", str(log_path),
                "--summary", str(summary_path),
            ]
        )

    assert rc == 1  # one network failed; the batch still completed
    assert mapping_csv.is_file()
    with mapping_csv.open(encoding="utf-8", newline="") as stream:
        mapped_rows = {row["opening_id"]: row for row in csv.DictReader(stream)}
    assert mapped_rows["O1"]["match_confidence"] == "exact"
    assert mapped_rows["O1"]["candidate_route_ids"] == "59"

    changes = yaml.safe_load(pt_changes.read_text(encoding="utf-8"))
    applied_ids = {c["opening_id"] for c in changes["from_openings"]}
    assert "O1" in applied_ids  # NetworkA applied despite NetworkB's failure

    summary_text = summary_path.read_text(encoding="utf-8")
    assert "Networks mapped this run: 1" in summary_text
    assert any(
        "failed to map" in record.message and "NetworkB" in record.message
        for record in caplog.records
    )


def test_map_and_apply_all_reads_each_resource_once(tmp_path, monkeypatch) -> None:
    # "NetworkA" and "NetworkA (alias)" both resolve to resource 1 (the
    # real case: "IDFM"/"RATP (IDFM)"/"Keolis Tisse (IDFM)" all resolve to
    # the same resource) -- the shared resource must be extracted exactly
    # once, not once per network-name alias (section 5.6 point 4,
    # 2026-10-16 fix).
    config_path = tmp_path / "gtfs_rebuild.yaml"
    _write_config(
        config_path,
        network_resource_ids={
            "NetworkA": 1,
            "NetworkA (alias)": 1,
            "NetworkB": 2,
        },
    )
    openings_csv = tmp_path / "openings.csv"
    openings_csv.write_text(
        "id,region,city,network,mode,line_2026,change_type,section_from,"
        "section_to,state_2022,state_2024,confidence\n"
        "O1,R,C,NetworkA,tram,A,new_line,,,remove,remove,high\n"
        "O2,R,C,NetworkA (alias),tram,A,new_line,,,remove,remove,high\n"
        "O3,R,C,NetworkB,tram,A,new_line,,,remove,remove,high\n",
        encoding="utf-8",
    )
    gtfs_zip_a = tmp_path / "feeds" / "a.zip"
    _write_gtfs_zip(gtfs_zip_a)
    gtfs_zip_b = tmp_path / "feeds" / "b.zip"
    _write_gtfs_zip(gtfs_zip_b)
    inventory_csv = tmp_path / "inventory.csv"
    with inventory_csv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["resource_id", "local_path"])
        writer.writerow(["1", str(gtfs_zip_a)])
        writer.writerow(["2", str(gtfs_zip_b)])
    mapping_csv = tmp_path / "mapping.csv"
    pt_changes = tmp_path / "pt_changes.yaml"
    pt_changes.write_text(
        yaml.safe_dump({"confirmed": [], "to_review": [], "not_applied": []}),
        encoding="utf-8",
    )

    import mobgrid.pt.cli as cli_module

    original_resolve_and_extract = cli_module.resolve_and_extract
    calls: list[int] = []

    def counting_resolve_and_extract(gtfs_inventory_csv, resource_id, scratch_dir):
        calls.append(resource_id)
        return original_resolve_and_extract(
            gtfs_inventory_csv, resource_id, scratch_dir
        )

    monkeypatch.setattr(cli_module, "resolve_and_extract", counting_resolve_and_extract)

    rc = main(
        [
            "map-and-apply-all",
            "--config", str(config_path),
            "--openings-csv", str(openings_csv),
            "--gtfs-inventory", str(inventory_csv),
            "--mapping-csv", str(mapping_csv),
            "--pt-changes", str(pt_changes),
            "--scratch-root", str(tmp_path / "scratch"),
            "--log", str(tmp_path / "run.log"),
            "--summary", str(tmp_path / "summary.md"),
        ]
    )

    assert rc == 0
    # Resource 1 is shared by two network-name aliases but read once;
    # resource 2 is read once too.
    assert calls.count(1) == 1
    assert calls.count(2) == 1
    assert sorted(calls) == [1, 2]

    with mapping_csv.open(encoding="utf-8", newline="") as stream:
        mapped_rows = {row["opening_id"]: row for row in csv.DictReader(stream)}
    # Both aliases' rows were still mapped correctly despite sharing one read.
    assert mapped_rows["O1"]["match_confidence"] == "exact"
    assert mapped_rows["O2"]["match_confidence"] == "exact"
    assert mapped_rows["O3"]["match_confidence"] == "exact"
