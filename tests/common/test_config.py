"""Tests for common.config."""

from pathlib import Path

import pytest
from common.config import load_base_config, load_pilot_config
from pydantic import ValidationError

ROOT = Path(__file__).parents[2]


def test_load_repository_configuration() -> None:
    base = load_base_config(ROOT / "config" / "base.yaml")
    pilot = load_pilot_config(ROOT / "config" / "pilot.yaml")

    assert base.coordinate_system == "EPSG:3035"
    assert base.resolutions_m == (200, 1000)
    assert pilot.department == "33"
    assert pilot.halo_km == 50
    assert pilot.years == (2021, 2023)
    assert all(path.startswith("data/") for path in pilot.paths.values())


def test_pilot_config_rejects_invalid_values(tmp_path: Path) -> None:
    invalid = tmp_path / "pilot.yaml"
    invalid.write_text(
        """
department: "33"
halo_km: 0
years: [2021, 2021]
paths:
  raw: data/raw
  interim: data/interim
  base: data/base
  derived: data/derived
  results: ../results
""",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_pilot_config(invalid)
