"""Offline GTFS inventory acceptance tests (sections 5.1 and 5.6)."""

import csv
from datetime import date

import httpx
import pytest
from acquire.cli import main
from acquire.discovery import merge_discovered, write_gtfs_inventory
from acquire.gtfs import inspect_gtfs
from acquire.manifest import SourceFile, load_manifest, save_manifest


def test_inspection_calendar_exceptions_and_metadata(tmp_path, gtfs_zip):
    path = tmp_path / "feed.zip"
    path.write_bytes(
        gtfs_zip(
            {
                "locations.geojson": '{"type":"FeatureCollection","features":[]}',
                "booking_rules.txt": "booking_rule_id\nB\n",
            }
        )
    )
    check = inspect_gtfs(path, date(2026, 10, 9))
    assert check.valid_zip and check.is_gtfs
    assert check.missing_files == []
    assert check.first_service_date == date(2026, 10, 6)
    assert check.last_service_date == date(2026, 10, 12)
    assert check.expired is False
    assert check.stop_count == 2 and check.trip_count == 2
    assert check.agency_names == ["Fixture Transit"]
    assert check.bbox == (3.2, 45.1, 4.3, 46.2)
    assert check.has_locations_geojson and check.has_booking_rules


def test_calendar_dates_only_expired_and_unused_service(tmp_path, gtfs_zip):
    path = tmp_path / "feed.zip"
    path.write_bytes(
        gtfs_zip(
            {
                "calendar_dates.txt": (
                    "service_id,date,exception_type\nS,20260101,1\n"
                    "S,20260102,2\nUNUSED,20271231,1\n"
                ),
            },
            omit=("calendar.txt",),
        )
    )
    check = inspect_gtfs(path, date(2026, 10, 9))
    assert check.is_gtfs and check.expired
    assert check.first_service_date == check.last_service_date == date(2026, 1, 1)


def test_calendar_only_respects_weekdays(tmp_path, gtfs_zip):
    path = tmp_path / "feed.zip"
    path.write_bytes(gtfs_zip(omit=("calendar_dates.txt",)))
    check = inspect_gtfs(path, date(2026, 10, 10))
    assert check.is_gtfs and check.expired
    assert check.first_service_date == date(2026, 10, 5)
    assert check.last_service_date == date(2026, 10, 9)


@pytest.mark.parametrize("kind", ["proto", "missing", "corrupt"])
def test_non_gtfs_is_flagged_without_deletion(tmp_path, gtfs_zip, kind):
    path = tmp_path / "feed.zip"
    body = (
        b"syntax = 'proto2';"
        if kind == "proto"
        else gtfs_zip(omit=("trips.txt",))
        if kind == "missing"
        else gtfs_zip()[:-30]
    )
    path.write_bytes(body)
    check = inspect_gtfs(path, date(2026, 10, 9))
    assert check.is_gtfs is False
    assert check.error or check.missing_files
    assert check.valid_zip is (kind == "missing")
    assert path.read_bytes() == body


def _source(resource_id, dataset_id="dataset"):
    return SourceFile(
        id=f"gtfs-{resource_id}",
        source="gtfs",
        provider="test",
        vintage="fixture",
        url=f"https://example.test/{resource_id}",
        dataset_id=dataset_id,
        resource_id=resource_id,
        local_path=f"data/raw/gtfs/{resource_id}.zip",
    )


def test_cli_check_is_offline_and_writes_inventory(tmp_path, monkeypatch, gtfs_zip):
    monkeypatch.setattr(
        httpx.Client, "send", lambda *a, **k: pytest.fail("offline check")
    )
    sources = [_source("good"), _source("proto"), _source("absent")]
    for source, body in zip(sources, [gtfs_zip(), b"not a zip"], strict=False):
        path = tmp_path / source.local_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    manifest = tmp_path / "sources.yaml"
    save_manifest(manifest, sources)
    before = manifest.read_bytes()
    assert (
        main(
            [
                "--manifest",
                str(manifest),
                "--project-root",
                str(tmp_path),
                "--check-gtfs",
            ]
        )
        == 0
    )
    with (tmp_path / "gtfs_inventory.csv").open(encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert rows[0]["gtfs_valid_zip"] == "True"
    assert rows[0]["gtfs_stop_count"] == "2"
    assert rows[1]["gtfs_is_gtfs"] == "False"
    assert rows[2]["gtfs_error"] == "not downloaded"
    assert manifest.read_bytes() == before


def test_inventory_checks_and_archive_provenance_survive_refresh(tmp_path, gtfs_zip):
    source = _source("42").model_copy(
        update={
            "archive_url": "https://archive.test/feed",
            "archive_date": date(2026, 10, 8),
            "archive_resource_id": "42",
            "excluded_reason": "broken resource, dataset covered by sibling",
        }
    )
    path = tmp_path / "feed.zip"
    path.write_bytes(gtfs_zip())
    check = inspect_gtfs(path, date(2026, 10, 9))
    inventory = tmp_path / "inventory.csv"
    write_gtfs_inventory(inventory, [source], {source.id: check})
    write_gtfs_inventory(inventory, [source])
    with inventory.open(encoding="utf-8") as stream:
        row = next(csv.DictReader(stream))
    assert row["gtfs_stop_count"] == "2"
    assert row["archive_date"] == "2026-10-08"
    refreshed = merge_discovered([source], [_source("42")], "gtfs")[0]
    assert refreshed.archive_url == source.archive_url
    assert refreshed.excluded_reason == source.excluded_reason


@pytest.mark.parametrize("valid_sibling", [True, False])
def test_failed_resource_excluded_only_if_dataset_has_valid_local_feed(
    tmp_path, monkeypatch, capsys, gtfs_zip, valid_sibling
):
    import acquire.cli as cli

    broken, sibling = _source("83905"), _source("83906")
    broken = broken.model_copy(update={"available": False})
    path = tmp_path / sibling.local_path
    path.parent.mkdir(parents=True)
    path.write_bytes(gtfs_zip() if valid_sibling else b"not GTFS")
    manifest = tmp_path / "sources.yaml"
    save_manifest(manifest, [broken, sibling])

    def fail(source, root):
        raise httpx.ReadTimeout("broken primary")

    monkeypatch.setattr(cli, "download_source", fail)
    result = main(
        [
            "--manifest",
            str(manifest),
            "--project-root",
            str(tmp_path),
            "--dataset",
            broken.id,
        ]
    )
    assert result == (0 if valid_sibling else 1)
    record = load_manifest(manifest)[0]
    if valid_sibling:
        assert record.excluded_reason == "broken resource, dataset covered by 83906"
        assert "failed: 0" in capsys.readouterr().out
    else:
        assert record.excluded_reason is None


def test_exclusion_rechecked_if_covering_feed_disappears(
    tmp_path, monkeypatch, gtfs_zip
):
    """Section 5.1: an old exclusion must not hide lost dataset coverage."""
    import acquire.cli as cli

    broken, sibling = _source("broken"), _source("sibling")
    broken = broken.model_copy(
        update={
            "excluded_reason": "broken resource, dataset covered by sibling",
            "available": False,
        }
    )
    manifest = tmp_path / "sources.yaml"
    save_manifest(manifest, [broken, sibling])
    attempted = []

    def fail(source, root):
        attempted.append(source.id)
        raise httpx.ReadTimeout("still broken")

    monkeypatch.setattr(cli, "download_source", fail)
    assert (
        main(
            [
                "--manifest",
                str(manifest),
                "--project-root",
                str(tmp_path),
                "--dataset",
                broken.id,
            ]
        )
        == 1
    )
    assert attempted == [broken.id]
    assert load_manifest(manifest)[0].excluded_reason is None
