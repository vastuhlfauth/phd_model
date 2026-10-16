"""Shared text normalisation for the PT-openings/relation matching tools."""

from __future__ import annotations

import re
import unicodedata


def normalise_text(value: str | None) -> str:
    """Casefold, strip accents, and keep only alphanumerics."""
    if not value:
        return ""
    ascii_value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    return re.sub(r"[^a-z0-9]+", "", ascii_value.casefold())
