"""Configured source files and acquisition records for section 5."""

from datetime import date
from pathlib import Path, PurePosixPath
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class SourceFile(BaseModel):
    """A source file and its acquisition metadata from section 5."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default="")
    source: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    provider: str = Field(min_length=1)
    vintage: str = Field(min_length=1)
    url: str | None = None
    local_path: str = Field(min_length=1)
    access: Literal["http", "api", "manual", "restricted", "todo"] = "http"
    expected_size_bytes: int | None = Field(default=None, gt=0)
    expected_md5: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{32}$")
    md5_url: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    download_date: date | None = None
    license: str | None = None
    api_query: str | None = None
    api_key_env: str | None = None
    api_key_header: str = "Authorization"
    api_key_scheme: str | None = "Bearer"
    restricted: bool = False
    notes: str | None = None
    verified: bool | None = None

    @model_validator(mode="after")
    def validate_source(self) -> "SourceFile":
        path = PurePosixPath(self.local_path.replace("\\", "/"))
        if path.is_absolute() or not path.parts or path.parts[0:2] != ("data", "raw"):
            raise ValueError("local_path must be relative to data/raw/")
        if ".." in path.parts:
            raise ValueError("local_path must not traverse outside data/raw/")
        if self.url is not None:
            HttpUrl(self.url)
        if self.md5_url is not None:
            HttpUrl(self.md5_url)
        if self.restricted and (self.url is not None or self.access != "restricted"):
            raise ValueError("restricted sources must not have a download URL")
        if self.access == "http" and self.url is None:
            raise ValueError("HTTP sources require a URL")
        if self.access == "restricted" and not self.restricted:
            raise ValueError("restricted access requires restricted: true")
        if self.api_key_env is not None and not self.api_key_env.strip():
            raise ValueError("api_key_env must not be empty")
        if not self.api_key_header.strip():
            raise ValueError("api_key_header must not be empty")
        if self.api_key_scheme is not None and not self.api_key_scheme.strip():
            raise ValueError("api_key_scheme must not be empty")
        return self


def _validate_manifest(sources: list[SourceFile]) -> list[SourceFile]:
    blank = sorted({source.source for source in sources if not source.id})
    if blank:
        names = ", ".join(blank)
        raise ValueError(
            f"every source must have a non-empty id; missing an id for: {names}"
        )
    ids = [source.id for source in sources]
    if len(ids) != len(set(ids)):
        raise ValueError("manifest source ids must be unique")
    paths = [source.local_path.replace("\\", "/") for source in sources]
    if len(paths) != len(set(paths)):
        raise ValueError("manifest local_path values must be unique")
    return sources


def load_manifest(path: str | Path) -> list[SourceFile]:
    """Load and validate configured source files from a YAML manifest."""
    with Path(path).open(encoding="utf-8") as stream:
        document = yaml.safe_load(stream)
    if not isinstance(document, dict) or set(document) != {"sources"}:
        raise ValueError("manifest must contain only a top-level 'sources' list")
    raw_sources = document["sources"]
    if not isinstance(raw_sources, list):
        raise ValueError("manifest 'sources' must be a list")
    return _validate_manifest([SourceFile.model_validate(item) for item in raw_sources])


def save_manifest(path: str | Path, sources: list[SourceFile]) -> None:
    """Atomically write source definitions and completed file records."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    checked = _validate_manifest(sources)
    content = yaml.safe_dump(
        {
            "sources": [
                source.model_dump(mode="json", exclude_defaults=True)
                for source in checked
            ]
        },
        sort_keys=False,
        allow_unicode=True,
    )
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(destination)
