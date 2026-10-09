"""Checksum parsing and streaming verification for section 5."""

import hashlib
import re
from pathlib import Path

_CHECKSUM_LINE = re.compile(
    r"^\s*(?:(sha256|md5):)?([0-9a-fA-F]{32}|[0-9a-fA-F]{64})(?:\s+\*?(.+?))?\s*$"
)


def parse_checksum(value: str) -> tuple[str, str]:
    """Parse an MD5 or SHA-256 digest, including a Geofabrik .md5 line."""
    match = _CHECKSUM_LINE.fullmatch(value)
    if match is None:
        raise ValueError(
            "checksum must contain a 32-character MD5 or 64-character SHA-256"
        )
    named_algorithm, digest, _filename = match.groups()
    algorithm = named_algorithm or ("md5" if len(digest) == 32 else "sha256")
    if len(digest) != (32 if algorithm == "md5" else 64):
        raise ValueError(f"{algorithm} checksum has an invalid digest length")
    return algorithm, digest.lower()


def checksum_file(path: str | Path, algorithm: str = "sha256") -> str:
    """Calculate a file checksum without loading the file into memory."""
    try:
        digest = hashlib.new(algorithm)
    except ValueError as error:
        raise ValueError(f"unsupported checksum algorithm: {algorithm}") from error
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_checksum(path: str | Path, expected: str) -> bool:
    """Return whether a file matches a prefixed or bare checksum."""
    algorithm, digest = parse_checksum(expected)
    return checksum_file(path, algorithm) == digest
