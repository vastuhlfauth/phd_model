"""Tests for acquire.manifest."""

from pathlib import Path

import pytest
from acquire.manifest import SourceFile, load_manifest, save_manifest
from pydantic import ValidationError

ROOT = Path(__file__).parents[2]


def test_load_repository_manifest() -> None:
    sources = load_manifest(ROOT / "config" / "sources.yaml")

    assert sources
    assert any(source.source == "osm" for source in sources)
    assert all(source.local_path.startswith("data/raw/") for source in sources)


def test_manifest_rejects_duplicate_paths_and_unsafe_paths(tmp_path: Path) -> None:
    manifest = tmp_path / "sources.yaml"
    manifest.write_text(
        """
sources:
  - source: example
    provider: Example
    vintage: "2026"
    url: https://example.test/file.zip
    local_path: data/raw/example/file.zip
  - source: example
    provider: Example
    vintage: "2027"
    url: https://example.test/file.zip
    local_path: data/raw/example/file.zip
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="local_path values must be unique"):
        load_manifest(manifest)

    manifest.write_text(
        """
sources:
  - source: example
    provider: Example
    vintage: "2026"
    url: https://example.test/file.zip
    local_path: data/raw/../outside.zip
""",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_manifest(manifest)


def test_manifest_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "sources.yaml"
    source = SourceFile(
        source="example",
        provider="Example",
        vintage="2026",
        url="https://example.test/file.zip",
        local_path="data/raw/example/file.zip",
    )

    save_manifest(path, [source])

    assert load_manifest(path) == [source]


def test_restricted_source_cannot_have_download_url() -> None:
    with pytest.raises(ValidationError):
        SourceFile(
            source="restricted",
            provider="Cerema",
            vintage="2026",
            url="https://example.test/file.zip",
            local_path="data/raw/restricted/file.zip",
            restricted=True,
        )
