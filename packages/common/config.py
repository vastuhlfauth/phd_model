"""Configuration loading and validation for section 14.2."""

from pathlib import Path, PurePosixPath
from typing import Annotated

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_data_path(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or not path.parts or path.parts[0] != "data":
        raise ValueError("configured paths must be relative to the data/ directory")
    if ".." in path.parts:
        raise ValueError("configured paths must not traverse outside data/")
    return value


class BaseConfig(BaseModel):
    """Shared spatial and storage settings from sections 4.1 and 14.2."""

    model_config = ConfigDict(extra="forbid")

    data_root: str
    coordinate_system: Annotated[str, Field(pattern=r"^EPSG:\d{4,5}$")]
    resolutions_m: tuple[int, ...]

    @field_validator("data_root")
    @classmethod
    def validate_data_root(cls, value: str) -> str:
        return _validate_data_path(value)

    @field_validator("resolutions_m")
    @classmethod
    def validate_resolutions(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if not value or any(resolution <= 0 for resolution in value):
            raise ValueError("resolutions must contain positive integers")
        if len(value) != len(set(value)):
            raise ValueError("resolutions must be unique")
        return value


class PilotConfig(BaseModel):
    """Pilot area settings from sections 4.3, 4.4, and 14.2."""

    model_config = ConfigDict(extra="forbid")

    department: Annotated[str, Field(pattern=r"^\d{2}[AB]?$")]
    halo_km: Annotated[float, Field(gt=0)]
    years: tuple[Annotated[int, Field(gt=0)], ...]
    paths: dict[str, str]

    @field_validator("years")
    @classmethod
    def validate_years(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if not value:
            raise ValueError("at least one reference year is required")
        if len(value) != len(set(value)):
            raise ValueError("reference years must be unique")
        return value

    @field_validator("paths")
    @classmethod
    def validate_paths(cls, value: dict[str, str]) -> dict[str, str]:
        required = {"raw", "interim", "base", "derived", "results"}
        missing = required - value.keys()
        if missing:
            missing_paths = ", ".join(sorted(missing))
            raise ValueError(f"missing configured data paths: {missing_paths}")
        for path in value.values():
            _validate_data_path(path)
        return value


def _load_yaml(path: str | Path) -> object:
    with Path(path).open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def load_base_config(path: str | Path) -> BaseConfig:
    """Load and validate base settings from a YAML file."""
    return BaseConfig.model_validate(_load_yaml(path))


def load_pilot_config(path: str | Path) -> PilotConfig:
    """Load and validate pilot settings from a YAML file."""
    return PilotConfig.model_validate(_load_yaml(path))
