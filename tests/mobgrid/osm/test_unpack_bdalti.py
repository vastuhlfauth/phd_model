import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path, PureWindowsPath

import duckdb
import pytest
from acquire.manifest import SourceFile
from mobgrid.osm.unpack_bdalti import (
    UnpackResult,
    intersecting_departments,
    main,
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
    destination = tmp_path / "interim" / "D033"
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
        assert "--strip-components" in arguments
        assert Path(arguments[arguments.index("-T") + 1]).read_text(
            encoding="utf-8"
        ) == "delivery/tile.asc\n"
        tile = extraction_dir / "tile.asc"
        tile.write_text("ASCII grid fixture", encoding="ascii")
        return subprocess.CompletedProcess(arguments, 0, stdout="", stderr="")

    monkeypatch.setattr("mobgrid.osm.unpack_bdalti.subprocess.run", fake_run)

    unpack_archive(archive, destination)
    assert (destination / "tile.asc").is_file()
    first_call_count = len(calls)

    unpack_archive(archive, destination)

    assert len(calls) == first_call_count
    (destination / "tile.asc").unlink()
    with pytest.raises(FileExistsError, match="incomplete or stale"):
        unpack_archive(archive, destination)


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


def test_real_nested_layout_extracts_only_flat_tiles(tmp_path):
    delivery = (
        "BDALTIV2_2-0_25M_ASC_LAMB93-IGN69_D016_2023-07-28/"
        "BDALTIV2/1_DONNEES_LIVRAISON_2024-02-00018/"
        "BDALTIV2_MNT_25M_ASC_LAMB93_IGN69_D016"
    )
    tile_name = "BDALTIV2_25M_FXX_0425_6475_MNT_LAMB93_IGN69.asc"
    source = tmp_path / "tiles"
    source.mkdir()
    tile = source / tile_name
    tile.write_text("ASCII grid fixture", encoding="ascii")
    metadata = source / "metadata.xml"
    metadata.write_text("not a tile", encoding="ascii")
    archive = tmp_path / "source.tar"
    with tarfile.open(archive, "w") as bundle:
        bundle.add(tile, arcname=f"{delivery}/{tile_name}")
        bundle.add(tile, arcname="other/depth/tile2.asc")
        bundle.add(metadata, arcname=f"{delivery}/metadata.xml")
    destination = tmp_path / "bdalti" / "D016"

    result = unpack_archive(archive, destination)

    assert result.tile_count == 2
    assert (destination / tile_name).read_text(encoding="ascii") == (
        "ASCII grid fixture"
    )
    assert (destination / "tile2.asc").is_file()
    assert sorted(path.name for path in destination.iterdir()) == sorted(
        [tile_name, "tile2.asc", "_bdalti_unpacked.json"]
    )
    target = PureWindowsPath(r"C:\work\phd_model\data\interim\bdalti\D016")
    assert len(str(target / tile_name)) < 160
    assert len(str(target / (".bdalti-" + delivery.split("/")[0] * 2)
                   / delivery / tile_name)) > 260


@pytest.mark.parametrize("second_name", ["tile.asc", "TILE.asc"])
def test_duplicate_tile_names_fail_before_extraction(
    tmp_path, monkeypatch, second_name,
):
    archive = tmp_path / "source.7z"
    archive.write_bytes(b"synthetic archive")

    def listing(arguments, **_options):
        assert "-tf" in arguments
        return subprocess.CompletedProcess(
            arguments, 0,
            stdout=f"one/tile.asc\ntwo/{second_name}\n", stderr="",
        )

    monkeypatch.setattr("mobgrid.osm.unpack_bdalti.subprocess.run", listing)
    with pytest.raises(ValueError, match="duplicate tile"):
        unpack_archive(archive, tmp_path / "D016")


def test_missing_tile_fails_and_removes_staging_directory(tmp_path, monkeypatch):
    archive = tmp_path / "source.7z"
    archive.write_bytes(b"synthetic archive")
    destination = tmp_path / "bdalti" / "D016"
    staging = []

    def fake_run(arguments, **_options):
        if "-tf" in arguments:
            return subprocess.CompletedProcess(
                arguments, 0,
                stdout="delivery/tile.asc\ndelivery/missing.asc\n", stderr="",
            )
        staging.append(Path(arguments[arguments.index("-C") + 1]))
        (staging[-1] / "tile.asc").write_text("fixture", encoding="ascii")
        return subprocess.CompletedProcess(arguments, 0, stdout="", stderr="")

    monkeypatch.setattr("mobgrid.osm.unpack_bdalti.subprocess.run", fake_run)
    with pytest.raises(OSError, match="tile.*not extracted"):
        unpack_archive(archive, destination)
    assert not destination.exists()
    assert staging and not staging[0].exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows long-path cleanup")
def test_failed_extraction_cleanup_uses_windows_extended_path(
    tmp_path, monkeypatch,
):
    archive = tmp_path / "source.7z"
    archive.write_bytes(b"synthetic archive")
    destination = tmp_path / "bdalti" / "D016"
    removed = []

    def fake_run(arguments, **_options):
        if "-tf" in arguments:
            return subprocess.CompletedProcess(
                arguments, 0, stdout="delivery/tile.asc\n", stderr=""
            )
        staging = Path(arguments[arguments.index("-C") + 1]).resolve()
        nested = Path("\\\\?\\" + str(staging)) / ("nested" * 20) / ("deep" * 20)
        nested.mkdir(parents=True)
        (nested / "partial.asc").write_text("partial", encoding="ascii")
        raise subprocess.CalledProcessError(1, arguments, stderr="tar failed")

    monkeypatch.setattr("mobgrid.osm.unpack_bdalti.subprocess.run", fake_run)
    rmtree = shutil.rmtree

    def remove(path):
        removed.append(str(path))
        rmtree(path)

    monkeypatch.setattr("mobgrid.osm.unpack_bdalti.shutil.rmtree", remove)
    with pytest.raises(subprocess.CalledProcessError):
        unpack_archive(archive, destination)
    assert len(removed) == 1
    assert removed[0].startswith("\\\\?\\")
    assert not destination.exists()
    assert not Path(removed[0]).exists()


def test_cli_outputs_tiles_directly_under_department(tmp_path, monkeypatch):
    sources = [
        SourceFile(
            id=source_id,
            source=source,
            provider="IGN",
            vintage="2021",
            local_path=local_path,
            access="manual",
        )
        for source_id, source, local_path in [
            ("contours-2021", "contours", "data/raw/contours/contours.geojson"),
            ("bdalti-016", "bdalti", "data/raw/bdalti/25m/archive_D016.7z"),
        ]
    ]
    destinations = []

    def fake_unpack(_archive, destination):
        destinations.append(destination)
        return UnpackResult(destination, 1, False)

    monkeypatch.setattr(
        "mobgrid.osm.unpack_bdalti.load_manifest", lambda _path: sources
    )
    monkeypatch.setattr(
        "mobgrid.osm.unpack_bdalti.intersecting_departments",
        lambda *_args, **_kwargs: ("16",),
    )
    monkeypatch.setattr("mobgrid.osm.unpack_bdalti.unpack_archive", fake_unpack)

    assert main(["--area", "pilot", "--output-directory", str(tmp_path)]) == 0
    assert destinations == [tmp_path / "D016"]
