"""Tests for acquire.checksums."""

import hashlib

from acquire.checksums import checksum_file, parse_checksum


def test_checksum_file_supports_configured_digest(tmp_path) -> None:
    path = tmp_path / "sample.bin"
    path.write_bytes(b"sample payload")

    assert (
        checksum_file(path, "sha256") == hashlib.sha256(b"sample payload").hexdigest()
    )
    assert checksum_file(path, "md5") == hashlib.md5(b"sample payload").hexdigest()


def test_parse_checksum_accepts_geofabrik_md5_line() -> None:
    assert parse_checksum("0123456789abcdef0123456789abcdef  france.osm.pbf") == (
        "md5",
        "0123456789abcdef0123456789abcdef",
    )
