"""Tests for acquire.download."""

import hashlib
from datetime import date

import httpx
import pytest
from acquire.download import ChecksumMismatchError, SizeMismatchError, download_source
from acquire.manifest import SourceFile


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
    client.close()


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
