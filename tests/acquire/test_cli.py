"""Tests for acquire.cli."""

from pathlib import Path

import httpx
import pytest
import yaml
from acquire.cli import main
from acquire.download import download_source
from acquire.manifest import SourceFile, load_manifest, save_manifest

ROOT = Path(__file__).parents[2]


def test_completed_file_is_saved_before_next_download(tmp_path, monkeypatch) -> None:
    """Section 5.1: interruption cannot erase earlier completed records."""
    import acquire.cli as cli
    from acquire.download import DownloadResult

    manifest = tmp_path / "sources.yaml"
    sources = [
        SourceFile(
            id=str(i),
            source="example",
            provider="test",
            vintage="fixture",
            url=f"https://example.test/{i}",
            local_path=f"data/raw/example/{i}",
        )
        for i in range(2)
    ]
    save_manifest(manifest, sources)

    def download(source, root):
        if source.id == "1":
            assert load_manifest(manifest)[0].size_bytes == 7
            raise KeyboardInterrupt
        record = source.model_copy(update={"size_bytes": 7, "sha256": "a" * 64})
        return DownloadResult(root / source.local_path, record, False)

    monkeypatch.setattr(cli, "download_source", download)
    with pytest.raises(KeyboardInterrupt):
        main(["--manifest", str(manifest), "--all"])
    assert load_manifest(manifest)[0].sha256 == "a" * 64


@pytest.mark.parametrize("failed_source", ["osm", "overture"])
def test_all_continues_summarizes_and_persists_successes(
    tmp_path, monkeypatch, capsys, failed_source
) -> None:
    """Section 5.1: batch failures do not lose later files or rerun records."""
    import acquire.cli as cli

    manifest = tmp_path / "sources.yaml"
    sources = [
        SourceFile(
            id="broken",
            source=failed_source,
            provider="test",
            vintage="fixture",
            url="https://example.test/broken",
            local_path="data/raw/example/broken.bin",
        ),
        SourceFile(
            id="good",
            source="example",
            provider="test",
            vintage="fixture",
            url="https://example.test/good",
            local_path="data/raw/example/good.bin",
            expected_size_bytes=7,
        ),
        SourceFile(
            id="manual",
            source="example",
            provider="test",
            vintage="fixture",
            local_path="data/raw/example/manual",
            access="manual",
            notes="register locally",
        ),
    ]
    if failed_source == "overture":
        sources[0] = sources[0].model_copy(
            update={
                "access": "s3",
                "url": "s3://bucket/places/*",
                "local_path": "data/raw/example/broken.parquet",
                "bbox": (-5, 40, 10, 51),
                "s3_region": "us-west-2",
            }
        )
    save_manifest(manifest, sources)
    requests = []

    def respond(request):
        requests.append(request.url.path)
        if request.url.path == "/broken":
            return httpx.Response(404)
        return httpx.Response(200, stream=httpx.ByteStream(b"payload"))

    def fail_extract(source, root):
        raise OSError("extraction failed")

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        monkeypatch.setattr(
            cli,
            "download_source",
            lambda source, root: download_source(
                source, root, client=client, downloaded_at="2026-10-09"
            ),
        )
        monkeypatch.setattr(cli, "extract_places", fail_extract)
        argv = ["--manifest", str(manifest), "--project-root", str(tmp_path), "--all"]
        assert main(argv) == 1
        output = capsys.readouterr().out
        assert "downloaded: 1, already present: 0, skipped: 1, failed: 1" in output
        assert "failed broken:" in output
        assert ("404" if failed_source == "osm" else "extraction failed") in output
        record = load_manifest(manifest)[1]
        assert record.verified == "size"
        assert record.sha256 is not None
        assert main(argv) == 1
        output = capsys.readouterr().out
        assert "downloaded: 0, already present: 1, skipped: 1, failed: 1" in output
        assert requests.count("/good") == 1
        assert load_manifest(manifest)[1] == record


def test_all_counts_known_unavailable_as_failed(tmp_path, capsys) -> None:
    """Section 5.1: an unavailable entry is reported without fetching it."""
    manifest = tmp_path / "sources.yaml"
    save_manifest(
        manifest,
        [
            SourceFile(
                id="missing",
                source="osm",
                provider="test",
                vintage="fixture",
                url="https://example.test/missing",
                local_path="data/raw/osm/missing.pbf",
                available=False,
                availability_note="HEAD HTTP 404",
            )
        ],
    )
    assert main(["--manifest", str(manifest), "--all"]) == 1
    output = capsys.readouterr().out
    assert "failed: 1" in output
    assert "failed missing: HEAD HTTP 404" in output


def test_cli_dry_run_lists_configured_download_without_network(capsys) -> None:
    result = main(
        [
            "--manifest",
            str(ROOT / "config" / "sources.yaml"),
            "--dataset",
            "osm",
            "--dry-run",
        ]
    )

    output = capsys.readouterr().out
    assert result == 0
    assert "would download osm 2022-01-01" in output
    assert "would download osm 2024-01-01" in output


def test_cli_registers_restricted_local_files(tmp_path: Path, capsys) -> None:
    project_root = tmp_path / "project"
    restricted_dir = project_root / "data" / "raw" / "emc2" / "gironde_2021"
    restricted_dir.mkdir(parents=True)
    (restricted_dir / "survey.csv").write_bytes(b"local restricted fixture")
    manifest = tmp_path / "sources.yaml"
    manifest.write_text(
        """
sources:
  - id: emc2-gironde-2021
    source: emc2
    provider: Cerema
    vintage: "2021"
    url:
    local_path: data/raw/emc2/gironde_2021/
    access: restricted
    restricted: true
""",
        encoding="utf-8",
    )

    result = main(
        [
            "--manifest",
            str(manifest),
            "--project-root",
            str(project_root),
            "--register-restricted",
            "emc2",
        ]
    )

    updated = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert result == 0
    assert "registered emc2 2021:" in capsys.readouterr().out
    record = updated["sources"][1]
    assert record["id"] == "restricted:emc2:data/raw/emc2/gironde_2021/survey.csv"
    assert record["local_path"] == "data/raw/emc2/gironde_2021/survey.csv"
    assert record["size_bytes"] == len(b"local restricted fixture")
    assert len(record["sha256"]) == 64

    (restricted_dir / "survey.csv").write_bytes(b"updated local file")
    assert (
        main(
            [
                "--manifest",
                str(manifest),
                "--project-root",
                str(project_root),
                "--register-restricted",
                "emc2",
            ]
        )
        == 0
    )
    updated = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    records = [
        item
        for item in updated["sources"]
        if item["local_path"] == "data/raw/emc2/gironde_2021/survey.csv"
    ]
    assert len(records) == 1
    assert records[0]["size_bytes"] == len(b"updated local file")
