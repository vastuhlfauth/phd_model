"""Synthetic tests for step-3 job logs."""

from pathlib import Path

import pytest


def test_job_summary_suppresses_counts_and_records_failure(tmp_path: Path) -> None:
    from landgrid.origins.job import logged_job

    with pytest.raises(RuntimeError, match="interrupted"):
        with logged_job(tmp_path, "synthetic", ["synthetic input"], 50) as job:
            job.counts["cells"] = 4
            job.outputs.append("interim result")
            raise RuntimeError("interrupted synthetic record")
    summary = next(tmp_path.glob("*_synthetic_summary.md")).read_text()
    assert "cells: <50" in summary
    assert "interim result" in summary
    assert "failed" in summary
    assert "interrupted synthetic record" not in summary
    log = next(tmp_path.glob("*_synthetic.log")).read_text()
    assert "interrupted synthetic record" not in log


def test_restricted_duckdb_spill_stays_in_interim(tmp_path: Path) -> None:
    from landgrid.origins.job import open_restricted_connection

    connection, temporary = open_restricted_connection(tmp_path)
    try:
        spill = Path(connection.execute(
            "SELECT current_setting('temp_directory')"
        ).fetchone()[0])
        assert spill.parent == tmp_path
    finally:
        connection.close()
        temporary.cleanup()
    assert not spill.exists()
