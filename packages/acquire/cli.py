"""Command-line acquisition entry point."""

import argparse
import logging
from datetime import date
from pathlib import Path

import duckdb
import httpx

from acquire.checksums import checksum_file
from acquire.discovery import (
    discover_bdalti,
    discover_gtfs,
    discover_osm,
    load_acquisition_config,
    merge_discovered,
    step0_coverage,
    write_gtfs_inventory,
)
from acquire.download import download_source
from acquire.manifest import SourceFile, load_manifest, save_manifest
from acquire.overture import extract_places

logger = logging.getLogger("acquire")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="acquire")
    parser.add_argument("--manifest", required=True, type=Path)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--dataset", help="source name or configured file id")
    selection.add_argument(
        "--all", action="store_true", help="process every configured entry"
    )
    selection.add_argument(
        "--register-restricted",
        metavar="SOURCE",
        help=(
            "register files already placed under a restricted source's configured path"
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--discover",
        action="store_true",
        help="metadata GETs and OSM HEADs only; write manifest and GTFS inventory",
    )
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--acquisition-config", type=Path)
    return parser


def _project_root(manifest_path: Path, configured_root: Path | None) -> Path:
    if configured_root is not None:
        return configured_root.resolve()
    return manifest_path.resolve().parent.parent


def _select(sources: list[SourceFile], selector: str) -> list[SourceFile]:
    selected = [
        source
        for source in sources
        if source.id == selector or source.source == selector
    ]
    if not selected:
        raise ValueError(f"no configured source matches {selector!r}")
    return selected


def _register_restricted(
    sources: list[SourceFile],
    selector: str,
    project_root: Path,
) -> list[SourceFile]:
    configured = _select(sources, selector)
    if any(not source.restricted for source in configured):
        raise ValueError(f"{selector!r} is not a restricted source")

    records: list[SourceFile] = []
    for source in configured:
        if source.size_bytes is not None and source.sha256 is not None:
            continue
        configured_path = (project_root / source.local_path).resolve()
        if not configured_path.is_relative_to(project_root):
            raise ValueError(
                f"restricted path escapes project root: {source.local_path}"
            )
        if configured_path.is_file():
            files = [configured_path]
        elif configured_path.is_dir():
            files = sorted(
                path for path in configured_path.rglob("*") if path.is_file()
            )
        else:
            files = []
        for path in files:
            relative = path.relative_to(project_root).as_posix()
            records.append(
                source.model_copy(
                    update={
                        "id": f"restricted:{source.source}:{relative}",
                        "local_path": relative,
                        "size_bytes": path.stat().st_size,
                        "sha256": checksum_file(path),
                    }
                )
            )
    if not records:
        raise ValueError(f"no local files found for restricted source {selector!r}")
    return records


def main(argv: list[str] | None = None) -> int:
    """Run selected sources; dry runs have no implicit network access."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _parser().parse_args(argv)
    manifest_path = args.manifest.resolve()
    sources = load_manifest(manifest_path)
    root = _project_root(manifest_path, args.project_root)
    if args.discover:
        if args.dry_run or args.register_restricted:
            logger.error("--discover cannot be combined with --dry-run or registration")
            return 1
        names = ("gtfs", "bdalti", "osm") if args.all else (args.dataset,)
        if any(name not in ("gtfs", "bdalti", "osm") for name in names):
            logger.error("discovery supports --dataset gtfs, bdalti, osm or --all")
            return 1
        try:
            settings = load_acquisition_config(
                args.acquisition_config or manifest_path.with_name("acquisition.yaml")
            )
            with httpx.Client(
                follow_redirects=True,
                timeout=settings.request_timeout_seconds,
            ) as client:
                for name in names:
                    if name == "gtfs":
                        configured = _select(sources, "gtfs")
                        vintages = {record.vintage for record in configured}
                        if len(vintages) != 1:
                            raise ValueError("GTFS discovery requires one snapshot")
                        records = discover_gtfs(client, vintages.pop(), settings)
                        print(
                            f"GTFS: {len(records)} producer resources across "
                            f"{len({record.dataset_id for record in records})} "
                            "distinct datasets"
                        )
                        for network, matches in step0_coverage(
                            records, settings
                        ).items():
                            print(
                                f"step-0 {network}: "
                                f"{len(matches)} available resource(s)"
                                if matches
                                else f"step-0 MISSING: {network}"
                            )
                    elif name == "bdalti":
                        records = discover_bdalti(client, settings)
                    else:
                        records = discover_osm(
                            client, settings, _select(sources, "osm")
                        )
                    for record in records:
                        if record.available is False:
                            print(
                                f"unavailable {record.id}: {record.url}; "
                                f"{record.availability_note}"
                            )
                        elif record.availability_note and record.available is None:
                            print(
                                f"unconfirmed {record.id}: {record.availability_note}"
                            )
                    sources = merge_discovered(sources, records, name)
                    save_manifest(manifest_path, sources)
                    if name == "gtfs":
                        write_gtfs_inventory(
                            manifest_path.with_name("gtfs_inventory.csv"), records
                        )
                    print(f"discovered {name}: {len(records)} file entries")
        except (httpx.HTTPError, OSError, ValueError) as error:
            logger.error("discovery failed: %s", error)
            return 1
        return 0

    if args.register_restricted:
        try:
            records = _register_restricted(sources, args.register_restricted, root)
            if args.dry_run:
                for record in records:
                    print(
                        f"would register {record.source} {record.vintage}: "
                        f"{record.local_path}"
                    )
                return 0
            records_by_path = {record.local_path: record for record in records}
            existing_paths = {source.local_path for source in sources}
            sources = [
                records_by_path.get(source.local_path, source) for source in sources
            ]
            sources.extend(
                record for record in records if record.local_path not in existing_paths
            )
            save_manifest(manifest_path, sources)
        except (OSError, ValueError) as error:
            logger.error("%s", error)
            return 1
        for record in records:
            print(f"registered {record.source} {record.vintage}: {record.local_path}")
        return 0

    try:
        selected = sources if args.all else _select(sources, args.dataset)
    except ValueError as error:
        logger.error("%s", error)
        return 1

    updated_by_id: dict[str, SourceFile] = {}
    skipped = 0
    downloaded = 0
    already_present = 0
    failures: dict[str, str] = {}
    for source in selected:
        if source.available is False:
            print(f"unavailable {source.id}: {source.availability_note}")
            failures[source.id] = source.availability_note or "reported unavailable"
            continue
        if source.access not in ("http", "s3") or source.restricted:
            reason = source.notes or f"access method is {source.access}"
            print(f"skip {source.source} {source.vintage}: {reason}")
            skipped += 1
            continue
        if source.source == "eurostat":
            today = date.today().isoformat()
            parts = Path(source.local_path).parts
            source = source.model_copy(
                update={
                    "vintage": today,
                    "local_path": "/".join((*parts[:-2], today, parts[-1])),
                    **(
                        {
                            "size_bytes": None,
                            "sha256": None,
                            "download_date": None,
                            "verified": None,
                        }
                        if source.vintage != today
                        else {}
                    ),
                }
            )
        destination = root / source.local_path
        if args.dry_run:
            print(
                f"would {'extract' if source.access == 's3' else 'download'} "
                f"{source.source} {source.vintage}: {source.url} -> {destination}"
                + (f" bbox={source.bbox}" if source.bbox else "")
                + (f" fallback={source.fallback_url}" if source.fallback_url else "")
            )
            continue
        try:
            result = (
                extract_places(source, root)
                if source.access == "s3"
                else download_source(source, root)
            )
        except (httpx.HTTPError, OSError, ValueError, duckdb.Error) as error:
            logger.error(
                "failed to acquire %s (%s): %s", source.source, source.vintage, error
            )
            failures[source.id] = str(error) or type(error).__name__
            if source.source == "gtfs":
                updated_by_id[source.id] = source.model_copy(
                    update={
                        "available": False,
                        "availability_note": str(error),
                        "checked_date": date.today(),
                    }
                )
            continue
        updated_by_id[result.record.id] = result.record
        if result.skipped:
            already_present += 1
            status = "already present"
        else:
            downloaded += 1
            if result.record.verified is True:
                status = "downloaded and verified"
            elif result.record.verified == "size":
                status = "downloaded (verified by size only: no checksum sidecar)"
            else:
                status = "downloaded (not verified: no checksum configured)"
        print(f"{status} {result.local_path}")

    if updated_by_id and not args.dry_run:
        sources = [updated_by_id.get(source.id, source) for source in sources]
        save_manifest(manifest_path, sources)
        gtfs = [source for source in sources if source.source == "gtfs"]
        if gtfs and all(source.dataset_id is not None for source in gtfs):
            write_gtfs_inventory(manifest_path.with_name("gtfs_inventory.csv"), gtfs)
    if not args.dry_run:
        print(
            f"Summary: downloaded: {downloaded}, already present: {already_present}, "
            f"skipped: {skipped}, failed: {len(failures)}"
        )
        for source_id, reason in failures.items():
            print(f"failed {source_id}: {reason}")
        if failures:
            return 1
    if skipped and not args.dry_run:
        logger.error(
            "%s configured source entries require non-HTTP or manual acquisition",
            skipped,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
