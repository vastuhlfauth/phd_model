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
  - id: example-2026
    source: example
    provider: Example
    vintage: "2026"
    url: https://example.test/file.zip
    local_path: data/raw/example/file.zip
  - id: example-2027
    source: example
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
  - id: example-2026
    source: example
    provider: Example
    vintage: "2026"
    url: https://example.test/file.zip
    local_path: data/raw/../outside.zip
""",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_manifest(manifest)


def test_manifest_rejects_sources_without_an_id(tmp_path: Path) -> None:
    manifest = tmp_path / "sources.yaml"
    manifest.write_text(
        """
sources:
  - source: example
    provider: Example
    vintage: "2026"
    url: https://example.test/file.zip
    local_path: data/raw/example/file.zip
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="non-empty id.*example"):
        load_manifest(manifest)


def test_manifest_rejects_duplicate_ids(tmp_path: Path) -> None:
    manifest = tmp_path / "sources.yaml"
    manifest.write_text(
        """
sources:
  - id: dup
    source: example
    provider: Example
    vintage: "2026"
    url: https://example.test/file.zip
    local_path: data/raw/example/one.zip
  - id: dup
    source: example
    provider: Example
    vintage: "2027"
    url: https://example.test/file.zip
    local_path: data/raw/example/two.zip
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="source ids must be unique"):
        load_manifest(manifest)


def test_manifest_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "sources.yaml"
    source = SourceFile(
        id="example-2026",
        source="example",
        provider="Example",
        vintage="2026",
        url="https://example.test/file.zip",
        local_path="data/raw/example/file.zip",
    )

    save_manifest(path, [source])

    assert load_manifest(path) == [source]


@pytest.mark.parametrize("failures", [2, 5])
def test_atomic_manifest_retries_permission_errors(
    tmp_path, monkeypatch, failures
) -> None:
    """Section 5.1: transient Windows locks do not lose acquisition records."""
    import acquire.manifest as manifest_module

    path = tmp_path / "sources.yaml"
    source = load_manifest(ROOT / "config" / "sources.yaml")[0]
    path.write_text("previous manifest", encoding="utf-8")
    replace = Path.replace
    attempts = []
    waits = []

    def locked(self, target):
        attempts.append(target)
        if len(attempts) <= failures:
            raise PermissionError("file briefly locked")
        return replace(self, target)

    monkeypatch.setattr(Path, "replace", locked)
    monkeypatch.setattr(manifest_module.time, "sleep", waits.append)
    if failures == 5:
        with pytest.raises(PermissionError):
            save_manifest(path, [source])
        assert path.read_text(encoding="utf-8") == "previous manifest"
        assert len(attempts) == 5
        assert len(waits) == 4
    else:
        save_manifest(path, [source])
        assert load_manifest(path) == [source]
        assert len(attempts) == 3
        assert len(waits) == 2
    assert all(wait > 0 for wait in waits)


def test_atomic_manifest_does_not_retry_other_os_errors(tmp_path, monkeypatch):
    """Section 5.1: disk failures are explicit, not disguised as lock retries."""
    import acquire.manifest as manifest_module

    source = load_manifest(ROOT / "config" / "sources.yaml")[0]
    waits = []
    monkeypatch.setattr(manifest_module.time, "sleep", waits.append)

    def fail(self, target):
        raise OSError("disk error")

    monkeypatch.setattr(Path, "replace", fail)
    with pytest.raises(OSError, match="disk error"):
        save_manifest(tmp_path / "sources.yaml", [source])
    assert not waits
    assert not list(tmp_path.glob("*.tmp"))


def test_manifest_read_closes_file_before_yaml_parsing(tmp_path, monkeypatch):
    """Section 5.1: our own YAML readers must not hold Windows replacement locks."""
    import acquire.manifest as manifest_module

    source = load_manifest(ROOT / "config" / "sources.yaml")[0]
    path = tmp_path / "sources.yaml"
    save_manifest(path, [source])
    parse = manifest_module.yaml.safe_load

    def parse_after_replace(content):
        path.replace(tmp_path / "moved.yaml")
        return parse(content)

    monkeypatch.setattr(manifest_module.yaml, "safe_load", parse_after_replace)
    assert load_manifest(path) == [source]


def test_filosofi_2019_temporal_test_sources() -> None:
    """Section 6.5: both temporal-test archives use the 2019 directory."""
    sources = load_manifest(ROOT / "config" / "sources.yaml")
    selected = [s for s in sources if s.source == "filosofi" and s.vintage == "2019"]
    assert {s.id for s in selected} == {"filosofi-natural-2019", "filosofi-200m-2019"}
    assert all(s.local_path.startswith("data/raw/filosofi/2019/") for s in selected)
    assert {s.url for s in selected} == {
        "https://www.insee.fr/fr/statistiques/fichier/7655503/"
        "Filosofi2019_carreaux_nivNaturel_csv.zip",
        "https://www.insee.fr/fr/statistiques/fichier/7655475/"
        "Filosofi2019_carreaux_200m_csv.zip",
    }


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


def test_api_key_header_and_scheme_must_not_be_blank() -> None:
    with pytest.raises(ValidationError, match="api_key_header"):
        SourceFile(
            source="example",
            provider="Example",
            vintage="2026",
            url="https://example.test/api",
            local_path="data/raw/example/file.json",
            access="api",
            api_key_header="  ",
        )

    with pytest.raises(ValidationError, match="api_key_scheme"):
        SourceFile(
            source="example",
            provider="Example",
            vintage="2026",
            url="https://example.test/api",
            local_path="data/raw/example/file.json",
            access="api",
            api_key_scheme="  ",
        )


def test_api_key_header_and_scheme_are_configurable_per_source() -> None:
    source = SourceFile(
        source="example",
        provider="Example",
        vintage="2026",
        url="https://example.test/api",
        local_path="data/raw/example/file.json",
        access="api",
        api_key_env="EXAMPLE_API_KEY",
        api_key_header="X-Api-Key",
        api_key_scheme=None,
    )

    assert source.api_key_header == "X-Api-Key"
    assert source.api_key_scheme is None
