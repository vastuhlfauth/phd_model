import json
import subprocess
from pathlib import Path

import duckdb
import pytest
from acquire.manifest import SourceFile
from mobgrid.osm.unpack_bdalti import (
    intersecting_departments,
    select_bdalti_sources,
    unpack_archive,
)


def _feature(department, coordinates):
    return {
        "type": "Feature",
        "properties": {"departement": department},
        "geometry": {"type": "Polygon", "coordinates": [coordinates]},
    }


def test_intersecting_departments_use_the_pilot_buffer(tmp_path):
    contours = tmp_path / "communes.geojson"
    contours.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    _feature(
                        "33",
                        [
                            [-0.1, 44.9],
                            [0.1, 44.9],
                            [0.1, 45.1],
                            [-0.1, 45.1],
                            [-0.1, 44.9],
                        ],
                    ),
                    _feature(
                        "24",
                        [
                            [0.2, 44.9],
                            [0.4, 44.9],
                            [0.4, 45.1],
                            [0.2, 45.1],
                            [0.2, 44.9],
                        ],
                    ),
                    _feature(
                        "86",
                        [
                            [1.0, 44.9],
                            [1.2, 44.9],
                            [1.2, 45.1],
                            [1.0, 45.1],
                            [1.0, 44.9],
                        ],
                    ),
                ],
            }
        ),
        encoding="utf-8",
    )
    connection = duckdb.connect()
    try:
        departments = intersecting_departments(
            connection, contours, department="33", halo_km=50
        )
    finally:
        connection.close()

    assert departments == ("24", "33")


def test_manifest_selection_uses_only_requested_bdalti_departments():
    sources = [
        SourceFile(
            id=f"bdalti-{department}",
            source="bdalti",
            provider="IGN",
            vintage="2021",
            local_path=f"data/raw/bdalti/25m/archive_D{department}.7z",
            access="manual",
            notes=f"Departement D{department}",
        )
        for department in ("024", "033", "086")
    ]

    selected = select_bdalti_sources(sources, {"24", "33"})

    assert {department: source.id for department, source in selected.items()} == {
        "24": "bdalti-024",
        "33": "bdalti-033",
    }


def test_unpack_archive_is_atomic_and_resumable(tmp_path, monkeypatch):
    archive = tmp_path / "source.7z"
    archive.write_bytes(b"synthetic archive")
    destination = tmp_path / "interim" / "D033" / "source"
    calls = []

    def fake_run(arguments, **options):
        assert options == {
            "check": True,
            "capture_output": True,
            "text": True,
        }
        calls.append(arguments)
        if "-tf" in arguments:
            return subprocess.CompletedProcess(
                arguments, 0, stdout="delivery/tile.asc\n", stderr=""
            )
        extraction_dir = Path(arguments[arguments.index("-C") + 1])
        tile = extraction_dir / "delivery" / "tile.asc"
        tile.parent.mkdir(parents=True)
        tile.write_text("ASCII grid fixture", encoding="ascii")
        return subprocess.CompletedProcess(arguments, 0, stdout="", stderr="")

    monkeypatch.setattr("mobgrid.osm.unpack_bdalti.subprocess.run", fake_run)

    unpack_archive(archive, destination)
    assert (destination / "delivery" / "tile.asc").is_file()
    first_call_count = len(calls)

    unpack_archive(archive, destination)

    assert len(calls) == first_call_count


def test_unpack_archive_rejects_path_traversal(tmp_path, monkeypatch):
    archive = tmp_path / "source.7z"
    archive.write_bytes(b"synthetic archive")
    destination = tmp_path / "interim" / "D033" / "source"

    def list_traversal(arguments, **options):
        assert options == {
            "check": True,
            "capture_output": True,
            "text": True,
        }
        return subprocess.CompletedProcess(
            arguments, 0, stdout="../outside.asc\n", stderr=""
        )

    monkeypatch.setattr(
        "mobgrid.osm.unpack_bdalti.subprocess.run", list_traversal
    )

    with pytest.raises(ValueError, match="unsafe archive member"):
        unpack_archive(archive, destination)
