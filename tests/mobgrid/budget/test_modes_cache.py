"""Synthetic tests for the section 9.9 mode-report cache."""

from pathlib import Path

import duckdb
import pytest
from mobgrid.budget import emp2019, entd2008, modes_cache, scope


@pytest.mark.parametrize(
    ("survey", "fixture"),
    [(emp2019, "synthetic_emp_zip"), (entd2008, "synthetic_entd2008_raw_dir")],
)
def test_cache_reuses_scoped_tables_and_preserves_open_days(
    survey, fixture: str, request: pytest.FixtureRequest, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cache hits must not reconstruct legs, and retain denominator inputs."""
    data_path = request.getfixturevalue(fixture)
    cache = modes_cache.load_survey(
        survey, data_path, tmp_path / "cache", activity_stay_min=15
    )
    with duckdb.connect() as con:
        trips = con.execute(
            "SELECT count(*) FROM read_parquet(?)",
            [str(cache.trips(scope.REFERENCE_SCOPE))],
        ).fetchone()
        days = con.execute(
            "SELECT count(*) FROM read_parquet(?)",
            [str(cache.days(scope.REFERENCE_SCOPE))],
        ).fetchone()
        roster = con.execute(
            "SELECT count(*) FROM read_parquet(?)", [str(cache.roster)]
        ).fetchone()
        open_days = con.execute(
            "SELECT count(*) FROM read_parquet(?) WHERE NOT is_round",
            [str(cache.day_base)],
        ).fetchone()
    assert trips is not None and trips[0] > 0
    assert days is not None and days[0] > 0
    assert roster is not None and roster[0] > 0
    assert open_days is not None
    if survey is emp2019:
        assert roster[0] == 13
        assert open_days[0] > 0

    def fail_build(*args: object, **kwargs: object) -> None:
        raise AssertionError("cache hit rebuilt trip legs")

    monkeypatch.setattr(survey, "build_trip_legs", fail_build)
    again = modes_cache.load_survey(
        survey, data_path, tmp_path / "cache", activity_stay_min=15
    )
    assert again.root == cache.root


def test_signature_changes_with_scope_parameter(
    synthetic_emp_zip: Path,
) -> None:
    """Changing the destination-activity rule invalidates the cache."""
    first = modes_cache.input_signature(emp2019, synthetic_emp_zip, 15)
    second = modes_cache.input_signature(emp2019, synthetic_emp_zip, 30)
    assert first != second
