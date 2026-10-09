"""Tests for acquire.download."""

import hashlib
from datetime import date
from pathlib import Path

import httpx
import pytest
from acquire.discovery import load_acquisition_config
from acquire.download import (
    ChecksumMismatchError,
    SizeMismatchError,
    UnexpectedHtmlResponseError,
    download_source,
)
from acquire.manifest import SourceFile


@pytest.mark.parametrize("failure", ["timeout", "html", "204", "empty"])
def test_gtfs_uses_latest_resource_archive(tmp_path, gtfs_zip, failure) -> None:
    """Sections 5.1/5.4: latest own archive, clean restart, 300 s read timeout."""
    settings = load_acquisition_config(
        Path(__file__).parents[2] / "config" / "acquisition.yaml"
    )
    body = gtfs_zip()
    source = SourceFile(
        id="gtfs-one",
        source="gtfs",
        provider="test",
        vintage="2026-10",
        dataset_id="dataset",
        resource_id="42",
        url="https://producer.test/feed",
        local_path="data/raw/gtfs/42.zip",
    )
    partial = tmp_path / (source.local_path + ".part")
    partial.parent.mkdir(parents=True)
    partial.write_bytes(b"partial primary")
    requests = []

    def respond(request):
        requests.append(request)
        if request.url.host == "producer.test":
            assert request.extensions["timeout"]["read"] == 300
            if failure == "timeout":
                raise httpx.ReadTimeout("fixture timeout", request=request)
            if failure == "html":
                return _response(200, b"<html>broken</html>")
            return _response(204 if failure == "204" else 200, b"")
        if request.url.path.endswith("/dataset"):
            return httpx.Response(
                200,
                json={
                    "history": [
                        {
                            "resource_id": 42,
                            "payload": {
                                "permanent_url": "https://archive.test/older",
                                "download_datetime": "2026-10-07T10:00:00Z",
                            },
                        },
                        {
                            "resource_id": 99,
                            "payload": {
                                "permanent_url": "https://archive.test/sibling",
                                "download_datetime": "2026-10-09T10:00:00Z",
                            },
                        },
                        {
                            "resource_id": 42,
                            "payload": {
                                "permanent_url": "https://archive.test/latest",
                                "download_datetime": "2026-10-08T10:00:00Z",
                            },
                        },
                    ]
                },
            )
        assert request.url.path == "/latest"
        assert "Range" not in request.headers
        return _response(200, body)

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = download_source(
            source,
            tmp_path,
            client=client,
            downloaded_at="2026-10-09",
            settings=settings,
        )
    assert result.local_path.read_bytes() == body
    assert result.record.archive_url == "https://archive.test/latest"
    assert result.record.archive_date == date(2026, 10, 8)
    assert result.record.archive_resource_id == "42"
    assert result.record.url == source.url
    assert result.record.available is True
    assert len(requests) == 3


@pytest.mark.parametrize(
    "archive_date,body_kind",
    [
        ("2026-08-10T00:00:00Z", "valid"),
        ("2026-10-10T00:00:00Z", "valid"),
        ("2026-10-08T00:00:00Z", "html"),
        ("2026-10-08T00:00:00Z", "missing_tables"),
    ],
)
def test_gtfs_rejects_old_or_invalid_latest_archive(
    tmp_path, gtfs_zip, archive_date, body_kind
) -> None:
    """Section 5.4: no older-archive or sibling search; raw data not published."""
    settings = load_acquisition_config(
        Path(__file__).parents[2] / "config" / "acquisition.yaml"
    )
    source = SourceFile(
        id="gtfs-one",
        source="gtfs",
        provider="test",
        vintage="2026-10",
        dataset_id="dataset",
        resource_id="42",
        url="https://producer.test/feed",
        local_path="data/raw/gtfs/42.zip",
    )
    body = (
        b"<html>broken</html>"
        if body_kind == "html"
        else gtfs_zip(omit=("trips.txt",) if body_kind == "missing_tables" else ())
    )
    requests = []

    def respond(request):
        requests.append(request)
        if request.url.host == "producer.test":
            return httpx.Response(503)
        if request.url.path.endswith("/dataset"):
            return httpx.Response(
                200,
                json={
                    "history": [
                        {
                            "resource_id": 42,
                            "payload": {
                                "permanent_url": "https://archive.test/latest",
                                "download_datetime": archive_date,
                            },
                        },
                    ]
                },
            )
        return _response(200, body)

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(ValueError, match="archive|HTML"):
            download_source(
                source,
                tmp_path,
                client=client,
                downloaded_at="2026-10-09",
                settings=settings,
            )
    assert not (tmp_path / source.local_path).exists()
    assert len(requests) == (2 if body_kind == "valid" else 3)


def test_gtfs_archive_rerun_preserves_provenance_offline(tmp_path, gtfs_zip) -> None:
    """Section 5.1: archive records are idempotent without a metadata request."""
    body = gtfs_zip()
    source = _source("data/raw/gtfs/feed.zip", body).model_copy(
        update={
            "source": "gtfs",
            "id": "archive",
            "dataset_id": "dataset",
            "resource_id": "42",
            "archive_resource_id": "42",
            "archive_url": "https://archive.test/42",
            "archive_date": date(2026, 10, 8),
            "download_date": date(2026, 10, 9),
            "verified": False,
            "size_bytes": len(body),
        }
    )
    path = tmp_path / source.local_path
    path.parent.mkdir(parents=True)
    path.write_bytes(body)
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: pytest.fail("archive rerun must be offline")
        )
    ) as client:
        result = download_source(source, tmp_path, client=client)
    assert result.skipped and result.record == source


def test_fresh_primary_download_clears_old_archive_provenance(tmp_path, gtfs_zip):
    """Section 5.1: provenance describes the actual downloaded bytes."""
    body = gtfs_zip()
    source = _source("data/raw/gtfs/feed.zip", body).model_copy(
        update={
            "source": "gtfs",
            "archive_url": "https://archive.test/old",
            "archive_date": date(2026, 10, 8),
            "archive_resource_id": "42",
        }
    )
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: _response(200, body))
    ) as client:
        result = download_source(source, tmp_path, client=client)
    assert not result.skipped
    assert result.record.archive_url is None
    assert result.record.archive_date is None
    assert result.record.archive_resource_id is None


def _source(path: str, content: bytes = b"payload") -> SourceFile:
    return SourceFile(
        source="example",
        provider="Example",
        vintage="2026",
        url="https://example.test/file.bin",
        local_path=path,
        sha256=hashlib.sha256(content).hexdigest(),
    )


def _response(
    status_code: int,
    content: bytes,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    return httpx.Response(
        status_code,
        headers=headers,
        stream=httpx.ByteStream(content),
    )


def test_download_records_size_checksum_and_date(tmp_path) -> None:
    content = b"sample payload"
    source = _source("data/raw/example/file.bin", content)
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: _response(
                200,
                content,
                {"Content-Length": str(len(content))},
            )
        )
    )

    result = download_source(
        source,
        tmp_path,
        client=client,
        downloaded_at="2026-10-09",
    )

    assert result.local_path.read_bytes() == content
    assert result.record.size_bytes == len(content)
    assert result.record.sha256 == hashlib.sha256(content).hexdigest()
    assert result.record.download_date == date(2026, 10, 9)
    client.close()


def test_download_resumes_partial_file(tmp_path) -> None:
    content = b"payload"
    partial = tmp_path / "data" / "raw" / "example" / "file.bin.part"
    partial.parent.mkdir(parents=True)
    partial.write_bytes(content[:3])
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["Range"] == "bytes=3-"
        remaining = content[3:]
        return _response(
            206,
            remaining,
            {
                "Content-Length": str(len(remaining)),
                "Content-Range": f"bytes 3-{len(content) - 1}/{len(content)}",
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(respond))
    source = _source("data/raw/example/file.bin", content)

    result = download_source(source, tmp_path, client=client)

    assert len(requests) == 1
    assert result.local_path.read_bytes() == content
    client.close()


def test_download_restarts_when_range_is_rejected(tmp_path) -> None:
    content = b"complete file"
    partial = tmp_path / "data" / "raw" / "example" / "file.bin.part"
    partial.parent.mkdir(parents=True)
    partial.write_bytes(b"old")
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.headers.get("Range"):
            return _response(416, b"")
        return _response(
            200,
            content,
            {"Content-Length": str(len(content))},
        )

    client = httpx.Client(transport=httpx.MockTransport(respond))
    source = _source("data/raw/example/file.bin", content)

    result = download_source(source, tmp_path, client=client)

    assert len(requests) == 2
    assert requests[0].headers["Range"] == "bytes=3-"
    assert "Range" not in requests[1].headers
    assert result.local_path.read_bytes() == content
    client.close()


def test_download_checks_geofabrik_md5_sidecar(tmp_path) -> None:
    content = b"osm pbf fixture"
    md5 = hashlib.md5(content).hexdigest()
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith(".md5"):
            return _response(200, f"{md5}  france.osm.pbf".encode())
        return _response(
            200,
            content,
            {"Content-Length": str(len(content))},
        )

    client = httpx.Client(transport=httpx.MockTransport(respond))
    source = SourceFile(
        source="osm",
        provider="Geofabrik",
        vintage="2022-01-01",
        url="https://example.test/france.osm.pbf",
        md5_url="https://example.test/france.osm.pbf.md5",
        local_path="data/raw/osm/france.osm.pbf",
    )

    result = download_source(source, tmp_path, client=client)

    assert [request.url.path for request in requests] == [
        "/france.osm.pbf.md5",
        "/france.osm.pbf",
    ]
    assert result.record.expected_md5 == md5
    assert result.record.sha256 == hashlib.sha256(content).hexdigest()
    client.close()


def test_matching_file_is_skipped_without_http_request(tmp_path) -> None:
    content = b"already present"
    source = _source("data/raw/example/file.bin", content)
    destination = tmp_path / source.local_path
    destination.parent.mkdir(parents=True)
    destination.write_bytes(content)
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: pytest.fail("matching file must not be downloaded")
        )
    )

    result = download_source(source, tmp_path, client=client)

    assert result.skipped
    assert result.record.sha256 == hashlib.sha256(content).hexdigest()
    assert result.record.verified is True
    client.close()


@pytest.mark.parametrize("verified", [True, "size", False])
@pytest.mark.parametrize(
    "expected_md5", [None, hashlib.md5(b"already recorded").hexdigest().upper()]
)
def test_recorded_file_rerun_preserves_verification_without_network(
    tmp_path, verified, expected_md5
) -> None:
    """Section 5.1: matching local records are idempotent, even offline."""
    content = b"already recorded"
    source = _source("data/raw/example/file.bin", content).model_copy(
        update={
            "size_bytes": len(content),
            "expected_size_bytes": len(content),
            "verified": verified,
            "download_date": date(2026, 10, 9),
            "md5_url": "https://example.test/file.bin.md5",
            "expected_md5": expected_md5,
        }
    )
    destination = tmp_path / source.local_path
    destination.parent.mkdir(parents=True)
    destination.write_bytes(content)
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: pytest.fail("recorded file must not use the network")
        )
    ) as client:
        result = download_source(source, tmp_path, client=client)
    assert result.skipped
    assert result.record == source


def test_size_verified_download_rerun_keeps_size_classification(tmp_path) -> None:
    """Section 5.1: a stored local digest is not a provider checksum."""
    content = b"osm fixture"
    source = _source("data/raw/osm/file.pbf", content).model_copy(
        update={"sha256": None, "expected_size_bytes": len(content)}
    )
    requests = []

    def respond(request):
        requests.append(request)
        return _response(200, content, {"Content-Length": str(len(content))})

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        first = download_source(
            source, tmp_path, client=client, downloaded_at="2026-10-09"
        )
        second = download_source(first.record, tmp_path, client=client)
    assert len(requests) == 1
    assert second.skipped
    assert second.record == first.record
    assert second.record.verified == "size"


@pytest.mark.parametrize("existing", [b"corrupt", b"truncated"])
def test_recorded_file_is_redownloaded_if_local_content_changed(
    tmp_path, existing
) -> None:
    """Section 5.1: a record is skipped only when local bytes still match."""
    source = _source("data/raw/example/file.bin").model_copy(
        update={"size_bytes": 7, "verified": True}
    )
    destination = tmp_path / source.local_path
    destination.parent.mkdir(parents=True)
    destination.write_bytes(existing)
    requests = []

    def respond(request):
        requests.append(request)
        return _response(200, b"payload", {"Content-Length": "7"})

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = download_source(
            source, tmp_path, client=client, downloaded_at="2026-10-09"
        )
    assert not result.skipped
    assert len(requests) == 1
    assert destination.read_bytes() == b"payload"


def test_download_rejects_content_length_and_checksum_mismatches(tmp_path) -> None:
    source = SourceFile(
        source="example",
        provider="Example",
        vintage="2026",
        url="https://example.test/file.bin",
        local_path="data/raw/example/file.bin",
        expected_size_bytes=9,
        sha256="0" * 64,
    )
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: _response(
                200,
                b"payload",
                {"Content-Length": "7"},
            )
        )
    )

    with pytest.raises(SizeMismatchError):
        download_source(source, tmp_path, client=client)
    client.close()

    source = SourceFile(
        source="example",
        provider="Example",
        vintage="2026",
        url="https://example.test/file.bin",
        local_path="data/raw/example/file.bin",
        sha256="0" * 64,
    )
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: _response(
                200,
                b"payload",
                {"Content-Length": "7"},
            )
        )
    )

    with pytest.raises(ChecksumMismatchError):
        download_source(source, tmp_path, client=client)
    assert not (tmp_path / source.local_path).exists()
    client.close()


def test_restricted_source_is_never_downloaded(tmp_path) -> None:
    source = SourceFile(
        source="emc2",
        provider="Cerema",
        vintage="2021",
        url=None,
        local_path="data/raw/emc2/gironde_2021/",
        access="restricted",
        restricted=True,
    )
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: pytest.fail("restricted source must not use HTTP")
        )
    )

    with pytest.raises(ValueError, match="restricted"):
        download_source(source, tmp_path, client=client)
    client.close()


def test_download_without_size_or_checksum_is_recorded_as_unverified(tmp_path) -> None:
    content = b"page content with no configured checksum"
    source = SourceFile(
        source="example",
        provider="Example",
        vintage="2026",
        url="https://example.test/file.bin",
        local_path="data/raw/example/file.bin",
    )
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: _response(
                200,
                content,
                {"Content-Length": str(len(content))},
            )
        )
    )

    result = download_source(source, tmp_path, client=client)

    assert result.record.verified is False
    assert result.record.sha256 == hashlib.sha256(content).hexdigest()
    client.close()


def test_download_with_expected_size_only_is_recorded_as_size_verified(
    tmp_path,
) -> None:
    content = b"sized content"
    source = SourceFile(
        source="example",
        provider="Example",
        vintage="2026",
        url="https://example.test/file.bin",
        local_path="data/raw/example/file.bin",
        expected_size_bytes=len(content),
    )
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: _response(
                200,
                content,
                {"Content-Length": str(len(content))},
            )
        )
    )

    result = download_source(source, tmp_path, client=client)

    assert result.record.verified == "size"
    client.close()


def test_download_falls_back_when_primary_url_fails(tmp_path) -> None:
    content = b"sytral feed content"
    source = SourceFile(
        source="gtfs",
        provider="transport.data.gouv.fr",
        vintage="2026-10",
        url="https://example.test/primary.zip",
        fallback_url="https://example.test/fallback.zip",
        local_path="data/raw/gtfs/2026-10/example.zip",
    )

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/primary.zip":
            return httpx.Response(503)
        return _response(200, content, {"Content-Length": str(len(content))})

    client = httpx.Client(transport=httpx.MockTransport(respond))

    result = download_source(source, tmp_path, client=client)

    assert result.local_path.read_bytes() == content
    assert result.record.url == "https://example.test/primary.zip"
    assert "fallback" in result.record.notes
    client.close()


def test_download_raises_when_fallback_also_fails(tmp_path) -> None:
    source = SourceFile(
        source="gtfs",
        provider="transport.data.gouv.fr",
        vintage="2026-10",
        url="https://example.test/primary.zip",
        fallback_url="https://example.test/fallback.zip",
        local_path="data/raw/gtfs/2026-10/example.zip",
    )
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(503))
    )

    with pytest.raises(httpx.HTTPStatusError):
        download_source(source, tmp_path, client=client)
    client.close()


def test_download_rejects_html_content_type(tmp_path) -> None:
    source = _source("data/raw/example/file.bin", b"<html>not the real file</html>")
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: _response(
                200,
                b"<html>not the real file</html>",
                {"Content-Type": "text/html; charset=utf-8"},
            )
        )
    )

    with pytest.raises(UnexpectedHtmlResponseError, match="HTML page"):
        download_source(source, tmp_path, client=client)
    assert not (tmp_path / source.local_path).exists()
    assert not (tmp_path / (source.local_path + ".part")).exists()
    client.close()


def test_download_rejects_html_body_without_content_type_header(tmp_path) -> None:
    body = b"<!DOCTYPE html>\n<html><body>error page</body></html>"
    source = _source("data/raw/example/file.bin", body)
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: _response(
                200,
                body,
                {"Content-Length": str(len(body))},
            )
        )
    )

    with pytest.raises(UnexpectedHtmlResponseError, match="HTML page"):
        download_source(source, tmp_path, client=client)
    assert not (tmp_path / source.local_path).exists()
    client.close()
