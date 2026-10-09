"""Offline regression tests for national metadata-only discovery."""

import csv
import json
from datetime import date
from pathlib import Path

import httpx
import pytest
from acquire.cli import main
from acquire.discovery import (
    ATOM,
    GPF,
    check_url,
    discover_bdalti,
    discover_gtfs,
    discover_osm,
    load_acquisition_config,
    merge_discovered,
    metadata,
    step0_coverage,
    write_gtfs_inventory,
)
from acquire.manifest import SourceFile, load_manifest, save_manifest

SETTINGS = load_acquisition_config(
    Path(__file__).parents[2] / "config" / "acquisition.yaml"
)
BDALTI_FEED = SETTINGS.bdalti_feed
TRANSPORT_API = SETTINGS.transport_api
OSM_REGIONS = SETTINGS.osm_regions


def dataset(id="one", title="Rennes STAR", area="Rennes Metropole", resources=None):
    return {
        "id": id,
        "slug": title.lower().replace(" ", "-"),
        "title": title,
        "type": "public-transit",
        "covered_area": [{"nom": area}],
        "resources": resources
        or [
            {
                "id": 123,
                "format": "GTFS",
                "url": "https://example.test/redirect",
                "original_url": "https://producer.test/file?key=published",
                "is_available": True,
            },
            {
                "id": 124,
                "format": "gtfs",
                "url": "https://example.test/unavailable",
                "is_available": False,
            },
            {"id": 125, "format": "GTFS-RT", "url": "https://example.test/realtime"},
        ],
    }


def test_gtfs_uses_live_array_and_keeps_overlaps_and_public_keys(tmp_path):
    payload = [dataset(), dataset(id="two")]
    other = dataset(id="not-transit")
    other["type"] = "carpooling-areas"
    payload.append(other)
    requests = []

    def respond(request):
        requests.append(request)
        assert request.method == "GET"
        assert str(request.url) == TRANSPORT_API
        return httpx.Response(200, json=payload)

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        records = discover_gtfs(client, "2026-10", SETTINGS)
    assert len(records) == 4
    assert len(requests) == 1
    assert records[0].url == "https://producer.test/file?key=published"
    assert records[0].local_path == "data/raw/gtfs/2026-10/one/123.zip"
    assert records[1].available is False
    assert len(step0_coverage(records, SETTINGS)["STAR Rennes"]) == 2
    path = tmp_path / "gtfs_inventory.csv"
    write_gtfs_inventory(path, records)
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 4
    assert json.loads(rows[0]["covered_area"]) == [{"nom": "Rennes Metropole"}]
    assert rows[1]["available"] == "False"
    assert rows[0]["dataset_gtfs_resource_count"] == "2"
    assert rows[0]["multiple_gtfs_resources"] == "True"
    with (tmp_path / "gtfs_multiple_resources.csv").open(encoding="utf-8") as stream:
        assert len(list(csv.DictReader(stream))) == 2


def test_gtfs_excludes_community_resources_by_id_or_publisher():
    payload = dataset()
    payload["community_resources"] = [payload["resources"][0]]
    payload["resources"].append(
        {
            "id": 126,
            "format": "GTFS",
            "url": "https://example.test/community",
            "community_resource_publisher": "Third party",
        }
    )
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=[payload])
        )
    ) as client:
        records = discover_gtfs(client, "2026-10", SETTINGS)
    assert [record.resource_id for record in records] == ["124"]


def test_gtfs_missing_format_is_reported(caplog):
    payload = [
        dataset(
            resources=[
                {"id": 1, "url": "https://example.test/no-format"},
                {"id": 2, "format": "GTFS", "url": "https://example.test/feed"},
            ]
        )
    ]
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    ) as client:
        assert len(discover_gtfs(client, "2026-10", SETTINGS)) == 1
    assert "has no format" in caplog.text


def test_step0_does_not_confuse_tcl_limoges_or_star_roanne():
    payload = [
        dataset(title="TCL", area="Limoges Metropole"),
        dataset(id="two", title="Star", area="Roannais Agglomeration"),
    ]
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    ) as client:
        coverage = step0_coverage(discover_gtfs(client, "2026-10", SETTINGS), SETTINGS)
    assert not coverage["TCL Lyon"]
    assert not coverage["STAR Rennes"]


def atom(entries, page=1, pages=1):
    return (
        f'<feed xmlns="{ATOM[1:-1]}" xmlns:g="{GPF[1:-1]}" '
        f'g:page="{page}" g:pagecount="{pages}">{entries}</feed>'
    )


def ign_entry(department, datum="IGN69"):
    title = f"BDALTIV2_2-0_25M_ASC_LAMB93-{datum}_D{department}_2023-08-08"
    return f"<entry><title>{title}</title><id>https://ign.test/{title}</id></entry>"


def test_ign_paginates_and_handles_corsica_without_downloading_archives(caplog):
    requests = []

    def respond(request):
        requests.append(str(request.url))
        assert request.method == "GET"
        assert not request.url.path.endswith(".7z")
        if str(request.url) == BDALTI_FEED:
            return httpx.Response(200, text=atom(ign_entry("033"), pages=2))
        if str(request.url) == BDALTI_FEED + "?page=2":
            return httpx.Response(
                200,
                text=atom(
                    ign_entry("02A", "IGN78") + ign_entry("971"), page=2, pages=2
                ),
            )
        filename = request.url.path.rsplit("/", 1)[-1] + ".7z"
        return httpx.Response(
            200,
            text=atom(
                f'<entry><link href="https://ign.test/{filename}" g:length="1234"/>'
                "</entry>"
            ),
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        records = discover_bdalti(client, SETTINGS)
    assert len(records) == 2
    assert any("D02A" in record.id for record in records)
    assert not any("D971" in url for url in requests)
    assert all(record.edition_date == date(2023, 8, 8) for record in records)
    assert all(record.expected_size_bytes == 1234 for record in records)
    assert "missing metropolitan department" in caplog.text


def test_osm_uses_exact_names_and_head_for_both_files_and_md5():
    requests = []

    def respond(request):
        requests.append(request)
        assert request.method == "HEAD"
        return httpx.Response(404 if "monaco" in request.url.path else 200)

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        records = discover_osm(client, SETTINGS)
    assert len(records) == 2 * len(OSM_REGIONS) == 26
    assert len(requests) == 52
    assert all(record.available is False for record in records if "monaco" in record.id)
    assert any(
        "germany/baden-wuerttemberg-220101.osm.pbf" in str(r.url) for r in requests
    )
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(405))
    ) as client:
        assert check_url(client, "https://example.test/file")[0] is None


def test_merge_preserves_checksums_only_for_unchanged_url():
    old = SourceFile(
        id="gtfs-a-1",
        source="gtfs",
        provider="test",
        vintage="2026-10",
        url="https://example.test/file",
        local_path="data/raw/gtfs/a/1.zip",
        sha256="a" * 64,
        size_bytes=5,
        verified=True,
    )
    assert (
        merge_discovered([old], [old.model_copy(update={"sha256": None})], "gtfs")[
            0
        ].sha256
        == "a" * 64
    )
    new = old.model_copy(update={"url": "https://example.test/new", "sha256": None})
    assert merge_discovered([old], [new], "gtfs")[0].sha256 is None


def test_dry_run_s3_and_unavailable_gtfs_never_access_network(tmp_path, capsys):
    manifest = tmp_path / "config" / "sources.yaml"
    records = [
        SourceFile(
            id="overture",
            source="overture",
            provider="test",
            vintage="2026-09-23.1",
            url="s3://bucket/places/*",
            local_path="data/raw/overture/places.parquet",
            access="s3",
            bbox=(-5.5, 40.4, 10, 51.6),
            s3_region="us-west-2",
        ),
        SourceFile(
            id="gtfs",
            source="gtfs",
            provider="test",
            vintage="2026-10",
            url="https://example.test/file",
            local_path="data/raw/gtfs/file.zip",
            available=False,
            availability_note="API reports unavailable",
        ),
    ]
    save_manifest(manifest, records)
    before = manifest.read_bytes()
    assert main(["--manifest", str(manifest), "--all", "--dry-run"]) == 0
    output = capsys.readouterr().out
    assert "would extract overture" in output
    assert "bbox=(-5.5, 40.4, 10.0, 51.6)" in output
    assert "unavailable gtfs" in output
    assert manifest.read_bytes() == before
    assert not (tmp_path / "data").exists()


def test_gtfs_download_failure_is_recorded_and_batch_continues(
    tmp_path,
    monkeypatch,
    capsys,
):
    import acquire.cli as cli

    manifest = tmp_path / "sources.yaml"
    records = [
        SourceFile(
            id=f"gtfs-{number}",
            source="gtfs",
            provider="test",
            vintage="2026-10",
            url=f"https://example.test/{number}",
            local_path=f"data/raw/gtfs/{number}.zip",
        )
        for number in (1, 2)
    ]
    save_manifest(manifest, records)
    attempted = []

    def fail(source, root):
        attempted.append(source.id)
        raise httpx.ConnectError("unavailable")

    monkeypatch.setattr(cli, "download_source", fail)
    assert main(["--manifest", str(manifest), "--all"]) == 0
    assert attempted == ["gtfs-1", "gtfs-2"]
    assert all(record.available is False for record in load_manifest(manifest))
    assert "unavailable resources: 2" in capsys.readouterr().out


def test_eurostat_uses_actual_download_date(tmp_path, monkeypatch):
    import acquire.cli as cli
    from acquire.download import DownloadResult

    fixed_date = date(2026, 10, 9)

    class FixedDate(date):
        @classmethod
        def today(cls):
            return fixed_date

    monkeypatch.setattr(cli, "date", FixedDate)
    manifest = tmp_path / "sources.yaml"
    record = SourceFile(
        id="eurostat",
        source="eurostat",
        provider="test",
        vintage="2000-01-01",
        url="https://example.test/file?format=TSV",
        local_path="data/raw/eurostat/test/2000-01-01/eurostat.tsv.gz",
        sha256="a" * 64,
    )
    save_manifest(manifest, [record])

    def download(source, root):
        assert source.vintage == fixed_date.isoformat()
        assert source.sha256 is None
        assert f"/{fixed_date.isoformat()}/" in source.local_path
        return DownloadResult(root / source.local_path, source, False)

    monkeypatch.setattr(cli, "download_source", download)
    assert main(["--manifest", str(manifest), "--all"]) == 0
    assert load_manifest(manifest)[0].vintage == fixed_date.isoformat()


@pytest.mark.parametrize("bbox", [(10, 40, -5, 51), (-5, 51, 10, 40)])
def test_invalid_overture_bbox_rejected(bbox):
    with pytest.raises(ValueError, match="bbox"):
        SourceFile(
            source="overture",
            provider="test",
            vintage="2026",
            url="s3://bucket/*",
            local_path="data/raw/overture/file.parquet",
            access="s3",
            bbox=bbox,
            s3_region="us-west-2",
        )


def test_repository_catalog_contains_exact_direct_files():
    sources = load_manifest(Path(__file__).parents[2] / "config" / "sources.yaml")
    by_id = {record.id: record for record in sources}
    assert by_id["filosofi-200m-2021"].url.endswith(
        "/8735162/Filosofi2021_carreaux_200m_csv.zip"
    )
    assert by_id["census-2021"].url.endswith("dossier_complet_31_12_2024.zip")
    assert by_id["census-2023"].url.endswith("dossier_complet.parquet")
    assert by_id["overture-places"].bbox == (-5.5, 40.4, 10, 51.6)
    emp = [record for record in sources if record.source == "emp"]
    assert len(emp) == 11
    assert all(record.access == "http" and record.api_key_env is None for record in emp)
    assert by_id["emp-2023-ageempform"].local_path.endswith(
        "emp-2023-ageempform.parquet"
    )


def test_ign_respects_retry_after_and_allows_five_retries(monkeypatch):
    import acquire.discovery as discovery

    waits = []
    requests = []
    monkeypatch.setattr(discovery.time, "sleep", waits.append)

    def respond(request):
        requests.append(request)
        if len(requests) <= 5:
            return httpx.Response(429, headers={"Retry-After": "200"})
        return httpx.Response(200, content=b"<feed/>")

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        assert metadata(client, BDALTI_FEED, SETTINGS) == b"<feed/>"
    assert len(requests) == 6
    assert waits.count(1) == 6
    assert [wait for wait in waits if wait != 1] == [200, 200, 200, 200, 200]


def test_ign_respects_http_date_retry_after(monkeypatch):
    import acquire.discovery as discovery

    waits = []
    requests = []
    monkeypatch.setattr(discovery.time, "sleep", waits.append)

    def respond(request):
        requests.append(request)
        return (
            httpx.Response(
                429, headers={"Retry-After": "Fri, 01 Jan 2100 00:00:00 GMT"}
            )
            if len(requests) == 1
            else httpx.Response(200, content=b"<feed/>")
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        assert metadata(client, BDALTI_FEED, SETTINGS) == b"<feed/>"
    assert max(waits) > 120


def test_metadata_retries_exhaust_after_five_increasing_waits(monkeypatch):
    import acquire.discovery as discovery

    waits = []
    requests = []
    monkeypatch.setattr(discovery.time, "sleep", waits.append)

    def respond(request):
        requests.append(request)
        return httpx.Response(429)

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(httpx.HTTPStatusError):
            metadata(client, "https://example.test/feed", SETTINGS)
    assert len(requests) == 6
    assert waits == [10, 20, 40, 80, 160]


def test_osm_distinguishes_existing_files_from_missing_sidecars():
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                404 if request.url.path.endswith(".md5") else 200
            )
        )
    ) as client:
        records = discover_osm(client, SETTINGS)
    assert all(record.available is True for record in records)
    assert all(record.md5_available is False for record in records)


@pytest.mark.parametrize("update", [{"ign_interval_seconds": 0.9}, {"max_retries": 6}])
def test_acquisition_config_enforces_ign_request_limits(update):
    from acquire.discovery import AcquisitionConfig

    with pytest.raises(ValueError):
        AcquisitionConfig.model_validate(SETTINGS.model_dump() | update)


def test_cli_metadata_discovery_persists_producer_inventory(
    tmp_path,
    monkeypatch,
    capsys,
):
    import acquire.cli as cli

    manifest = tmp_path / "sources.yaml"
    source = SourceFile(
        id="gtfs-discovery",
        source="gtfs",
        provider="test",
        vintage="2026-10",
        url=TRANSPORT_API,
        local_path="data/raw/gtfs/2026-10/",
        access="api",
    )
    save_manifest(manifest, [source])
    requests = []

    def respond(request):
        requests.append(request)
        assert str(request.url) == TRANSPORT_API
        assert request.method == "GET"
        return httpx.Response(200, json=[dataset()])

    client = httpx.Client(transport=httpx.MockTransport(respond))
    monkeypatch.setattr(cli.httpx, "Client", lambda **kwargs: client)
    settings_path = Path(__file__).parents[2] / "config" / "acquisition.yaml"
    assert (
        main(
            [
                "--manifest",
                str(manifest),
                "--dataset",
                "gtfs",
                "--discover",
                "--acquisition-config",
                str(settings_path),
            ]
        )
        == 0
    )
    assert len(requests) == 1
    assert len(load_manifest(manifest)) == 2
    assert all(record.access == "http" for record in load_manifest(manifest))
    assert (tmp_path / "gtfs_inventory.csv").is_file()
    assert (tmp_path / "gtfs_multiple_resources.csv").is_file()
    assert "2 producer resources across 1 distinct datasets" in capsys.readouterr().out
    assert not (tmp_path / "data").exists()


def test_overture_parquet_filter_includes_corsica_and_box_edges(tmp_path):
    import duckdb
    from acquire.overture import write_places

    input_path = tmp_path / "places.parquet"
    output_path = tmp_path / "result.parquet"
    with duckdb.connect() as connection:
        connection.execute(
            """
            COPY (
                SELECT id, {'xmin': x, 'xmax': x, 'ymin': y, 'ymax': y} AS bbox,
                       'keep all columns' AS names
                FROM (VALUES ('france', 2.0, 48.0), ('corsica', 9.0, 42.0),
                             ('edge', -5.5, 40.4), ('outside', 11.0, 48.0),
                             ('south', 2.0, 40.0)) AS places(id, x, y)
            ) TO ? (FORMAT PARQUET)
            """,
            [str(input_path)],
        )
        write_places(connection, str(input_path), (-5.5, 40.4, 10, 51.6), output_path)
        rows = connection.execute(
            "SELECT id, names FROM read_parquet(?) ORDER BY id", [str(output_path)]
        ).fetchall()
    assert [row[0] for row in rows] == ["corsica", "edge", "france"]
    assert all(row[1] == "keep all columns" for row in rows)
