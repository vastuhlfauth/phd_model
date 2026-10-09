"""Command-line acquisition entry point."""

import argparse
import logging
from pathlib import Path

import httpx

from acquire.checksums import checksum_file
from acquire.download import download_source
from acquire.manifest import SourceFile, load_manifest, save_manifest

logger = logging.getLogger("acquire")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="acquire")
    parser.add_argument("--manifest", required=True, type=Path)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--dataset", help="source name or configured file id")
    selection.add_argument(
        "--all", action="store_true", help="process every pilot entry"
    )
    selection.add_argument(
        "--register-restricted",
        metavar="SOURCE",
        help=(
            "register files already placed under a restricted source's configured path"
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--project-root", type=Path)
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
    """Run one source or the configured pilot list without implicit network access."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _parser().parse_args(argv)
    manifest_path = args.manifest.resolve()
    sources = load_manifest(manifest_path)
    root = _project_root(manifest_path, args.project_root)

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

    updated_by_path: dict[str, SourceFile] = {}
    skipped = 0
    for source in selected:
        if source.access != "http" or source.restricted:
            reason = source.notes or f"access method is {source.access}"
            print(f"skip {source.source} {source.vintage}: {reason}")
            skipped += 1
            continue
        destination = root / source.local_path
        if args.dry_run:
            print(
                f"would download {source.source} {source.vintage}: "
                f"{source.url} -> {destination}"
            )
            continue
        try:
            result = download_source(source, root)
        except (httpx.HTTPError, OSError, ValueError) as error:
            logger.error(
                "failed to acquire %s (%s): %s", source.source, source.vintage, error
            )
            return 1
        updated_by_path[result.record.local_path] = result.record
        if result.skipped:
            status = "verified"
        elif result.record.verified:
            status = "downloaded and verified"
        else:
            status = "downloaded (not verified: no checksum configured)"
        print(f"{status} {result.local_path}")

    if updated_by_path and not args.dry_run:
        sources = [
            updated_by_path.get(source.local_path, source) for source in sources
        ]
        save_manifest(manifest_path, sources)
    if skipped and not args.dry_run:
        logger.error(
            "%s configured source entries require non-HTTP or manual acquisition",
            skipped,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
