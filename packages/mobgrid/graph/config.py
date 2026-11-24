"""Validated search-product settings for sections 10.2 and 14.7."""

from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from mobgrid.osm.config import Mode


class SearchConfig(BaseModel):
    """Resolution in seconds and curve bin widths in seconds, metres and kJ."""

    model_config = ConfigDict(extra="forbid")

    queue: Literal["heap", "dial"]
    dial_resolution_s: float = Field(gt=0, allow_inf_nan=False)
    time_bin_s: float = Field(gt=0, allow_inf_nan=False)
    distance_bin_m: float = Field(gt=0, allow_inf_nan=False)
    energy_bin_kj: float = Field(gt=0, allow_inf_nan=False)
    nearest_extra: int = Field(ge=0)
    benchmark_seed: int = Field(ge=0)
    benchmark_log_directory: Path
    cutoff_s_by_mode: dict[
        Mode, Annotated[float, Field(gt=0, allow_inf_nan=False)] | None
    ]

    @field_validator("cutoff_s_by_mode")
    @classmethod
    def require_all_modes(
        cls, value: dict[Mode, float | None]
    ) -> dict[Mode, float | None]:
        if set(value) != {"car", "bike", "foot"}:
            raise ValueError("cutoffs must include car, bike and foot")
        return value


def load_search_config(path: str | Path) -> SearchConfig:
    """Load and validate search settings from YAML."""
    with Path(path).open(encoding="utf-8") as stream:
        return SearchConfig.model_validate(yaml.safe_load(stream))
