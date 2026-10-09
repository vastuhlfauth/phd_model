"""Repository skeleton smoke tests."""

import acquire
import common
import landgrid
import mobgrid


def test_workspace_packages_import() -> None:
    assert all(package.__doc__ for package in (common, acquire, landgrid, mobgrid))
