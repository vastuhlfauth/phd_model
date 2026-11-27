"""Prepare nested Filosofi archives for the section 6.5 temporal test."""

import argparse
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Sequence

import yaml

from landgrid.origins.job import logged_job


def unpack_archive(
    archive_path: str | Path,
    destination: str | Path,
    member_name: str,
    interim_directory: str | Path,
) -> Path:
    """Unpack one metropolitan CSV once, under interim (sections 6.3 and 6.5)."""
    archive = Path(archive_path).resolve()
    target = Path(destination).resolve()
    interim = Path(interim_directory).resolve()
    if not target.is_relative_to(interim) or target == interim:
        raise ValueError("Filosofi destination must be inside the interim directory")
    if not archive.is_file():
        raise FileNotFoundError(archive)
    if (
        member_name in {"", ".", ".."}
        or PurePosixPath(member_name).name != member_name
        or "\\" in member_name
    ):
        raise ValueError("Filosofi member must be a plain file name")
    stat = archive.stat()
    signature = {
        "archive": str(archive),
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "member": member_name,
    }
    marker = target / "_unpacked.json"
    result = target / member_name
    if target.exists():
        if marker.is_file() and result.is_file():
            saved = json.loads(marker.read_text(encoding="utf-8"))
            if (
                saved.get("signature") == signature
                and saved.get("output_size") == result.stat().st_size
                and result.stat().st_size > 0
            ):
                return result
        raise ValueError(f"stale or incomplete Filosofi unpack at {target}")

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="filosofi_unpack_", dir=target.parent
    ) as tmp:
        staging = Path(tmp)
        nested = staging / "source.7z"
        with zipfile.ZipFile(archive) as source:
            members = [
                info for info in source.infolist() if info.filename.endswith(".7z")
            ]
            if len(members) != 1:
                raise ValueError("Filosofi ZIP must contain exactly one 7z archive")
            with source.open(members[0]) as src, nested.open("wb") as dst:
                shutil.copyfileobj(src, dst)
        listing = subprocess.run(
            ["tar", "-tf", str(nested)], check=True, capture_output=True, text=True
        )
        matches = []
        for raw in listing.stdout.splitlines():
            member = PurePosixPath(raw.replace("\\", "/"))
            if member.is_absolute() or ".." in member.parts or (
                member.parts and ":" in member.parts[0]
            ):
                raise ValueError(f"unsafe archive member: {raw!r}")
            if member.name == member_name:
                matches.append(raw)
        if len(matches) != 1:
            raise ValueError(f"expected exactly one Filosofi member {member_name}")
        unpacked = staging / "unpacked"
        unpacked.mkdir()
        extracted = unpacked / member_name
        with extracted.open("wb") as output:
            subprocess.run(
                ["tar", "-xOf", str(nested), "--", matches[0]],
                check=True,
                stdout=output,
                stderr=subprocess.PIPE,
            )
        if extracted.stat().st_size == 0:
            raise ValueError(f"empty Filosofi member: {member_name}")
        (unpacked / "_unpacked.json").write_text(
            json.dumps(
                {"signature": signature, "output_size": extracted.stat().st_size}
            ),
            encoding="utf-8",
        )
        unpacked.replace(target)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    """Prepare configured 2019 CSVs, retaining resumable outputs under interim."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/origins.yaml"))
    args = parser.parse_args(argv)
    with args.config.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    inputs = config["filosofi"]["temporal_2019"]
    report = config["report"]
    jobs = config["jobs"]
    archives = [inputs["natural_archive"], inputs["200m_archive"]]
    with logged_job(
        Path(jobs["log_directory"]),
        jobs["unpack_filosofi_task"],
        archives,
        report["count_suppression_threshold"],
    ) as summary:
        for kind in ("natural", "200m"):
            result = unpack_archive(
                inputs[f"{kind}_archive"],
                inputs[f"{kind}_destination"],
                inputs[f"{kind}_member"],
                report["interim_directory"],
            )
            summary.outputs.append(str(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
