"""Tests for preparing the nested Filosofi 2019 archives (sections 6.3, 6.5)."""

import io
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest
from landgrid.origins.unpack_filosofi import unpack_archive


def _outer_archive(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("nested.7z", b"synthetic archive")


def test_unpacks_once_and_rejects_stale_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "source.zip"
    _outer_archive(archive)
    calls: list[list[str]] = []

    def fake_tar(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        calls.append(args)
        if "-tf" in args:
            return subprocess.CompletedProcess(args, 0, stdout="folder/met.csv\n")
        output = kwargs["stdout"]
        output.write(b"column\nvalue\n")
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", fake_tar)
    target = tmp_path / "interim" / "unpacked"
    result = unpack_archive(archive, target, "met.csv", tmp_path / "interim")
    assert result.read_bytes() == b"column\nvalue\n"
    assert unpack_archive(archive, target, "met.csv", tmp_path / "interim") == result
    assert len(calls) == 2
    result.write_bytes(b"")
    with pytest.raises(ValueError, match="stale or incomplete"):
        unpack_archive(archive, target, "met.csv", tmp_path / "interim")


def test_rejects_destination_outside_interim(tmp_path: Path) -> None:
    archive = tmp_path / "source.zip"
    _outer_archive(archive)
    with pytest.raises(ValueError, match="interim"):
        unpack_archive(archive, tmp_path / "outside", "met.csv", tmp_path / "interim")


def test_failed_extraction_leaves_no_cached_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "source.zip"
    _outer_archive(archive)

    def fake_tar(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        if "-tf" in args:
            return subprocess.CompletedProcess(args, 0, stdout="met.csv\n")
        raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(subprocess, "run", fake_tar)
    target = tmp_path / "interim" / "unpacked"
    with pytest.raises(subprocess.CalledProcessError):
        unpack_archive(archive, target, "met.csv", tmp_path / "interim")
    assert not target.exists()


def test_rejects_unsafe_nested_member(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "source.zip"
    _outer_archive(archive)

    def fake_tar(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(args, 0, stdout="../met.csv\n")

    monkeypatch.setattr(subprocess, "run", fake_tar)
    target = tmp_path / "interim" / "unpacked"
    with pytest.raises(ValueError, match="unsafe archive member"):
        unpack_archive(archive, target, "met.csv", tmp_path / "interim")
    assert not target.exists()


def test_real_tar_streams_nested_member(tmp_path: Path) -> None:
    nested = io.BytesIO()
    content = b"column\nvalue\n"
    with tarfile.open(fileobj=nested, mode="w") as archive:
        info = tarfile.TarInfo("folder/met.csv")
        info.size = len(content)
        archive.addfile(info, io.BytesIO(content))
    outer = tmp_path / "source.zip"
    with zipfile.ZipFile(outer, "w") as archive:
        archive.writestr("nested.7z", nested.getvalue())

    result = unpack_archive(outer, tmp_path / "interim" / "out", "met.csv",
                            tmp_path / "interim")
    assert result.read_bytes() == content
