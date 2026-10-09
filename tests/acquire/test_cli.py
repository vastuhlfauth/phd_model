"""Tests for acquire.cli."""

from pathlib import Path

import yaml
from acquire.cli import main

ROOT = Path(__file__).parents[2]


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
