"""Validated search-product settings for sections 10.2 and 14.7."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class SearchConfig(BaseModel):
    """Resolution in seconds and curve bin widths in seconds, metres and kJ."""

    model_config = ConfigDict(extra="forbid")

    dial_resolution_s: float = Field(gt=0, allow_inf_nan=False)
    time_bin_s: float = Field(gt=0, allow_inf_nan=False)
    distance_bin_m: float = Field(gt=0, allow_inf_nan=False)
    energy_bin_kj: float = Field(gt=0, allow_inf_nan=False)


def load_search_config(path: str | Path) -> SearchConfig:
    """Load and validate search settings from YAML."""
    with Path(path).open(encoding="utf-8") as stream:
        return SearchConfig.model_validate(yaml.safe_load(stream))
