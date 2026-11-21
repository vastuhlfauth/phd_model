"""Unpack configured BD ALTI 25 m archives for the pilot area (section 8.1)."""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Sequence

import duckdb
from acquire.manifest import SourceFile, load_manifest
from common.config import load_pilot_config
from common.duckdb_io import open_connection

from mobgrid.osm.config import load_network_config
from mobgrid.osm.extract import build_area

logger = logging.getLogger(__name__)
_DEPARTMENT_PATTERN = re.compile(r"D(\d{1,3}[AB]?)", re.IGNORECASE)
_MARKER_NAME = "_bdalti_unpacked.json"


@dataclass(frozen=True)
class UnpackResult:
    """One archive's extracted ASCII-grid tile count and reuse status."""

    output_directory: Path
    tile_count: int
    reused: bool


def _sql_path(path: str | Path) -> str:
    return str(Path(path).resolve()).replace("\\", "/").replace("'", "''")


def _normalise_department(value: str) -> str:
    suffix = value[-1].upper() if value[-1:].upper() in ("A", "B") else ""
    digits = value[:-1] if suffix else value
    return (digits.lstrip("0") or "0") + suffix


def intersecting_departments(
    connection: duckdb.DuckDBPyConnection,
    contours_path: str | Path,
    *,
    department: str,
    halo_km: float,
) -> tuple[str, ...]:
    """Find department codes whose commune polygons intersect the pilot buffer."""
    area = build_area(
        connection,
        contours_path,
        area="pilot",
        department=department,
        halo_km=halo_km,
    )
    connection.execute("LOAD spatial")
    rows = connection.execute(
        f"""
        SELECT DISTINCT departement
        FROM ST_Read('{_sql_path(contours_path)}')
        WHERE ST_Intersects(
            ST_Transform(
                ST_MakeValid(geom),
                'EPSG:4326', 'EPSG:3035', true
            ),
            ST_GeomFromWKB(?)
        )
        ORDER BY departement
        """,
        [area.geometry_wkb],
    ).fetchall()
    if not rows:
        raise ValueError("the buffered pilot area intersects no department contours")
    return tuple(str(row[0]) for row in rows)


def _source_department(source: SourceFile) -> str:
    for candidate in (source.local_path, source.notes or "", source.id):
        match = _DEPARTMENT_PATTERN.search(candidate)
        if match:
            return _normalise_department(match.group(1))
    raise ValueError(f"cannot identify department for BD ALTI source {source.id!r}")


def select_bdalti_sources(
    sources: Sequence[SourceFile], departments: set[str]
) -> dict[str, SourceFile]:
    """Resolve exactly one manifest archive for each requested department."""
    requested = {_normalise_department(department) for department in departments}
    selected: dict[str, SourceFile] = {}
    for source in sources:
        if source.source != "bdalti":
            continue
        department = _source_department(source)
        if department not in requested:
            continue
        if department in selected:
            raise ValueError(
                f"multiple BD ALTI archives configured for department {department}"
            )
        selected[department] = source
    missing = sorted(requested - selected.keys())
    if missing:
        raise ValueError(
            "no BD ALTI archive configured for departments: "
            + ", ".join(missing)
        )
    return selected


def _safe_members(listing: str) -> tuple[str, ...]:
    members = []
    for raw_member in listing.splitlines():
        if not raw_member:
            continue
        member = PurePosixPath(raw_member.replace("\\", "/"))
        if (
            member.is_absolute()
            or ".." in member.parts
            or (member.parts and ":" in member.parts[0])
        ):
            raise ValueError(f"unsafe archive member path: {raw_member!r}")
        members.append(member.as_posix())
    if not any(member.lower().endswith(".asc") for member in members):
        raise ValueError("BD ALTI archive contains no .asc raster tiles")
    if len(members) != len(set(members)):
        raise ValueError("BD ALTI archive contains duplicate member paths")
    return tuple(members)


def _archive_signature(archive: Path, members: Sequence[str]) -> dict[str, object]:
    stat = archive.stat()
    return {
        "archive": archive.name,
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "members": list(members),
    }


def _valid_existing_unpack(destination: Path, archive: Path) -> int | None:
    marker = destination / _MARKER_NAME
    if not marker.is_file():
        return None
    recorded = json.loads(marker.read_text(encoding="utf-8"))
    if not isinstance(recorded, dict):
        return None
    stat = archive.stat()
    if (
        recorded.get("archive") != archive.name
        or recorded.get("size_bytes") != stat.st_size
        or recorded.get("mtime_ns") != stat.st_mtime_ns
    ):
        return None
    raw_members = recorded.get("members")
    if not isinstance(raw_members, list) or not all(
        isinstance(member, str) for member in raw_members
    ):
        return None
    members = _safe_members("\n".join(raw_members))
    if not all(
        (destination / Path(*PurePosixPath(member).parts)).exists()
        for member in members
    ):
        return None
    return sum(member.lower().endswith(".asc") for member in members)


def unpack_archive(archive_path: str | Path, destination: str | Path) -> UnpackResult:
    """Atomically unpack one verified 7z listing with Windows ``tar``."""
    archive = Path(archive_path)
    if not archive.is_file():
        raise FileNotFoundError(archive)
    target = Path(destination)
    if target.exists():
        existing_count = _valid_existing_unpack(target, archive)
        if existing_count is not None:
            return UnpackResult(target, existing_count, True)
        raise FileExistsError(
            f"incomplete or stale BD ALTI output exists at {target}; "
            "move it aside before retrying"
        )
    listing = subprocess.run(
        ["tar", "-tf", str(archive.resolve())],
        check=True,
        capture_output=True,
        text=True,
    )
    members = _safe_members(listing.stdout)
    signature = _archive_signature(archive, members)

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{target.name}.", dir=target.parent
    ) as temporary_directory:
        temporary = Path(temporary_directory)
        subprocess.run(
            ["tar", "-xf", str(archive.resolve()), "-C", str(temporary)],
            check=True,
            capture_output=True,
            text=True,
        )
        for member in members:
            extracted = temporary / Path(*PurePosixPath(member).parts)
            if not extracted.exists():
                raise OSError(f"archive member was not extracted: {member}")
            if not extracted.resolve().is_relative_to(temporary.resolve()):
                raise ValueError(f"unsafe extracted archive member: {member!r}")
        tile_count = sum(member.lower().endswith(".asc") for member in members)
        (temporary / _MARKER_NAME).write_text(
            json.dumps(signature, indent=2), encoding="utf-8"
        )
        temporary.replace(target)
    return UnpackResult(target, tile_count, False)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mobgrid.osm.unpack_bdalti")
    parser.add_argument("--area", choices=("pilot",), default="pilot")
    parser.add_argument("--manifest", type=Path, default=Path("config/sources.yaml"))
    parser.add_argument(
        "--network-config", type=Path, default=Path("config/network.yaml")
    )
    parser.add_argument(
        "--pilot-config", type=Path, default=Path("config/pilot.yaml")
    )
    parser.add_argument("--output-directory", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Unpack only the manifest archives intersecting the configured pilot."""
    args = _parser().parse_args(argv)
    network = load_network_config(args.network_config)
    pilot = load_pilot_config(args.pilot_config)
    sources = load_manifest(args.manifest)
    project_root = args.manifest.resolve().parent.parent
    contours_source = next(
        (
            source for source in sources
            if source.id == network.contour_source_id
        ),
        None,
    )
    if contours_source is None:
        raise KeyError(
            f"contour source {network.contour_source_id!r} is not in the manifest"
        )
    contours_path = project_root / contours_source.local_path
    output_directory = args.output_directory or (
        Path(pilot.paths["interim"]) / "bdalti"
    )
    if not output_directory.is_absolute():
        output_directory = project_root / output_directory

    connection = open_connection()
    try:
        departments = intersecting_departments(
            connection,
            contours_path,
            department=pilot.department,
            halo_km=pilot.halo_km,
        )
    finally:
        connection.close()

    selected = select_bdalti_sources(sources, set(departments))
    unpacked = []
    for department, source in selected.items():
        archive = project_root / source.local_path
        department_folder = "D" + department.zfill(3)
        destination = output_directory / department_folder / source.id
        result = unpack_archive(archive, destination)
        unpacked.append(result)
        logger.info(
            "%s BD ALTI department %s: %s tiles at %s",
            "reused" if result.reused else "unpacked",
            department,
            result.tile_count,
            result.output_directory,
        )
    logger.info(
        "BD ALTI pilot selection: %s departments, %s raster tiles, output %s",
        len(unpacked),
        sum(result.tile_count for result in unpacked),
        output_directory,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
