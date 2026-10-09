"""Idempotent, resumable downloads for section 5."""

import logging
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal

import httpx

from acquire.checksums import checksum_file, parse_checksum
from acquire.manifest import SourceFile

_CONTENT_RANGE = re.compile(r"^bytes (\d+)-(\d+)/(\d+|\*)$")
logger = logging.getLogger(__name__)


class ChecksumMismatchError(ValueError):
    """Raised when a completed download does not match its configured digest."""


class SizeMismatchError(ValueError):
    """Raised when a downloaded file does not match its expected size."""


class UnexpectedHtmlResponseError(ValueError):
    """Raised when a configured file URL returns an HTML page instead of a file."""


@dataclass(frozen=True)
class DownloadResult:
    """A downloaded or already verified file and its manifest record."""

    local_path: Path
    record: SourceFile
    skipped: bool


def _destination(root: Path, relative_path: str) -> Path:
    resolved_root = root.resolve()
    destination = (resolved_root / Path(relative_path)).resolve()
    if not destination.is_relative_to(resolved_root):
        raise ValueError("configured local_path resolves outside the project root")
    return destination


def _client_context(
    client: httpx.Client | None,
) -> tuple[httpx.Client, bool]:
    return (client or httpx.Client(follow_redirects=True), client is None)


def _expected_md5(
    source: SourceFile,
    client: httpx.Client,
) -> str | None:
    if source.expected_md5 is not None:
        return source.expected_md5.lower()
    if source.md5_url is None:
        return None
    response = client.get(source.md5_url)
    response.raise_for_status()
    algorithm, digest = parse_checksum(response.text)
    if algorithm != "md5":
        raise ValueError("configured checksum sidecar must contain an MD5 digest")
    return digest


def _matches_existing(
    source: SourceFile,
    destination: Path,
    expected_md5: str | None,
) -> bool:
    if not destination.is_file():
        return False
    if source.size_bytes is not None:
        if destination.stat().st_size != source.size_bytes:
            return False
    if source.expected_size_bytes is not None:
        if destination.stat().st_size != source.expected_size_bytes:
            return False
    if source.sha256 is None and expected_md5 is None:
        return False
    if source.sha256 is not None:
        if checksum_file(destination, "sha256") != source.sha256.lower():
            return False
    if expected_md5 is not None:
        if checksum_file(destination, "md5") != expected_md5:
            return False
    return True


def _check_content_range(
    value: str | None,
    offset: int,
) -> tuple[int | None, int]:
    if value is None:
        raise ValueError("server returned partial content without Content-Range")
    match = _CONTENT_RANGE.fullmatch(value)
    if match is None or int(match.group(1)) != offset:
        raise ValueError(
            "server returned an invalid Content-Range for the partial file"
        )
    start, end = int(match.group(1)), int(match.group(2))
    if end < start:
        raise ValueError("server returned an invalid Content-Range interval")
    total = int(match.group(3)) if match.group(3) != "*" else None
    if total is not None and end >= total:
        raise ValueError("server returned an invalid Content-Range total")
    return total, end - start + 1


def _reject_html_content_type(response: httpx.Response, url: str) -> None:
    content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
    if content_type.lower() == "text/html":
        raise UnexpectedHtmlResponseError(
            f"expected a data file but received an HTML page "
            f"(Content-Type: text/html) from {url}"
        )


def _looks_like_html(path: Path) -> bool:
    with path.open("rb") as stream:
        head = stream.read(512)
    stripped = head.lstrip().lower()
    return stripped.startswith(b"<!doctype") or stripped.startswith(b"<html")


def _stream_response(
    client: httpx.Client,
    url: str,
    partial_path: Path,
) -> int | None:
    while True:
        offset = partial_path.stat().st_size if partial_path.exists() else 0
        headers = {"Accept-Encoding": "identity"}
        if offset:
            headers["Range"] = f"bytes={offset}-"

        with client.stream("GET", url, headers=headers) as response:
            if response.status_code == 416 and offset:
                partial_path.unlink()
                continue
            response.raise_for_status()
            if response.status_code not in (200, 206):
                raise ValueError(
                    f"unexpected successful download status {response.status_code}"
                )
            _reject_html_content_type(response, url)

            if response.status_code == 206:
                total_size, expected_chunk_size = _check_content_range(
                    response.headers.get("Content-Range"),
                    offset,
                )
                mode = "ab"
            else:
                total_size = None
                expected_chunk_size = None
                offset = 0
                mode = "wb"
            content_length = response.headers.get("Content-Length")
            if total_size is None and content_length is not None:
                total_size = offset + int(content_length)

            with partial_path.open(mode) as stream:
                for chunk in response.iter_raw():
                    stream.write(chunk)

        if expected_chunk_size is not None:
            received_chunk_size = partial_path.stat().st_size - offset
            if received_chunk_size != expected_chunk_size:
                partial_path.unlink(missing_ok=True)
                raise SizeMismatchError(
                    f"received {received_chunk_size} bytes for a range of "
                    f"{expected_chunk_size} bytes"
                )
        return total_size


def _record_download(
    source: SourceFile,
    destination: Path,
    *,
    downloaded_at: date | str | None,
    verified: bool | Literal["size"],
    set_current_date: bool = True,
) -> SourceFile:
    recorded_date = downloaded_at
    if recorded_date is None and set_current_date:
        recorded_date = datetime.now(timezone.utc).date()
    elif isinstance(recorded_date, str):
        recorded_date = date.fromisoformat(recorded_date)
    return source.model_copy(
        update={
            "size_bytes": destination.stat().st_size,
            "sha256": checksum_file(destination, "sha256"),
            "download_date": recorded_date,
            "verified": verified,
        }
    )


def _attempt_download(
    source: SourceFile,
    url: str,
    destination: Path,
    partial_path: Path,
    client: httpx.Client,
    downloaded_at: date | str | None,
) -> DownloadResult:
    """Download from `url`, recording the result against the configured `source`."""
    if source.sha256 is not None and _matches_existing(
        source,
        destination,
        source.expected_md5.lower() if source.expected_md5 is not None else None,
    ):
        logger.info("Skipping recorded source file %s", destination)
        record = (
            source
            if source.verified is not None
            else _record_download(
                source,
                destination,
                downloaded_at=source.download_date,
                verified=True,
                set_current_date=False,
            )
        )
        return DownloadResult(destination, record, True)

    expected_md5 = _expected_md5(source, client)
    if _matches_existing(source, destination, expected_md5):
        logger.info("Skipping verified source file %s", destination)
        return DownloadResult(
            destination,
            _record_download(
                source,
                destination,
                downloaded_at=source.download_date,
                verified=True,
                set_current_date=False,
            ),
            True,
        )

    logger.info("Downloading %s (%s) to %s", source.source, source.vintage, destination)
    response_size = _stream_response(client, url, partial_path)
    if _looks_like_html(partial_path):
        partial_path.unlink(missing_ok=True)
        raise UnexpectedHtmlResponseError(
            f"expected a data file but downloaded content looks like an "
            f"HTML page from {url}"
        )
    actual_size = partial_path.stat().st_size
    if response_size is not None and actual_size != response_size:
        partial_path.unlink(missing_ok=True)
        raise SizeMismatchError(
            f"downloaded {actual_size} bytes but the server declared {response_size}"
        )
    if (
        source.expected_size_bytes is not None
        and actual_size != source.expected_size_bytes
    ):
        partial_path.unlink(missing_ok=True)
        raise SizeMismatchError(
            f"downloaded {actual_size} bytes but expected {source.expected_size_bytes}"
        )
    if expected_md5 is not None and checksum_file(partial_path, "md5") != expected_md5:
        partial_path.unlink(missing_ok=True)
        raise ChecksumMismatchError(f"MD5 mismatch for {source.local_path}")
    if source.sha256 is not None:
        actual_sha256 = checksum_file(partial_path, "sha256")
        if actual_sha256 != source.sha256.lower():
            partial_path.unlink(missing_ok=True)
            raise ChecksumMismatchError(f"SHA-256 mismatch for {source.local_path}")

    os.replace(partial_path, destination)
    verified: bool | Literal["size"]
    if expected_md5 is not None or source.sha256 is not None:
        verified = True
    elif source.expected_size_bytes is not None:
        verified = "size"
    else:
        verified = False
    record = _record_download(
        source, destination, downloaded_at=downloaded_at, verified=verified
    )
    if expected_md5 is not None:
        record = record.model_copy(update={"expected_md5": expected_md5})
    if verified is True:
        logger.info(
            "Verified %s (%s bytes, SHA-256 %s)",
            destination,
            record.size_bytes,
            record.sha256,
        )
    elif verified == "size":
        logger.info(
            "Verified by size only (no checksum sidecar) %s (%s bytes, SHA-256 %s)",
            destination,
            record.size_bytes,
            record.sha256,
        )
    else:
        logger.info(
            "Not verified: no size or checksum available for %s (%s bytes, SHA-256 %s)",
            destination,
            record.size_bytes,
            record.sha256,
        )
    return DownloadResult(destination, record, False)


def download_source(
    source: SourceFile,
    project_root: str | Path,
    *,
    client: httpx.Client | None = None,
    downloaded_at: date | str | None = None,
) -> DownloadResult:
    """Download one configured HTTP file, resuming and verifying before publish."""
    if source.restricted or source.access == "restricted":
        raise ValueError(
            f"source {source.source} is restricted and cannot be downloaded"
        )
    if source.access != "http" or source.url is None:
        raise ValueError(
            f"source {source.source} is not configured for direct HTTP download"
        )
    destination = _destination(Path(project_root), source.local_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial_path = destination.with_name(destination.name + ".part")

    active_client, should_close = _client_context(client)
    try:
        try:
            return _attempt_download(
                source,
                source.url,
                destination,
                partial_path,
                active_client,
                downloaded_at,
            )
        except (
            httpx.HTTPError,
            ChecksumMismatchError,
            SizeMismatchError,
            UnexpectedHtmlResponseError,
        ) as error:
            if source.fallback_url is None:
                raise
            logger.warning(
                "Primary URL failed for %s (%s); trying fallback %s",
                source.source,
                error,
                source.fallback_url,
            )
            result = _attempt_download(
                source,
                source.fallback_url,
                destination,
                partial_path,
                active_client,
                downloaded_at,
            )
            fallback_note = (
                f"Downloaded from fallback URL after primary failed: {error}"
            )
            record = result.record.model_copy(
                update={
                    "notes": (
                        f"{source.notes} {fallback_note}"
                        if source.notes
                        else fallback_note
                    ),
                }
            )
            return DownloadResult(result.local_path, record, result.skipped)
    finally:
        if should_close:
            active_client.close()
