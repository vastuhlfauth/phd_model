"""Aggregate-only logs and summaries for resumable origins jobs."""

import logging
import tempfile
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import duckdb
from common.duckdb_io import open_connection


def open_restricted_connection(
    directory: Path,
) -> tuple[duckdb.DuckDBPyConnection, tempfile.TemporaryDirectory]:
    """Keep DuckDB spill files under the restricted interim directory."""
    temporary = tempfile.TemporaryDirectory(prefix="duckdb_origins_", dir=directory)
    connection = open_connection()
    try:
        connection.execute("SET temp_directory = ?", [temporary.name])
    except BaseException:
        connection.close()
        temporary.cleanup()
        raise
    return connection, temporary


@dataclass
class JobSummary:
    """Aggregate outputs and counts to include in a job summary."""

    outputs: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@contextmanager
def logged_job(
    directory: Path, task: str, inputs: Sequence[str], threshold: int
) -> Iterator[JobSummary]:
    """Log a job and write a suppressed-count summary, including on failure."""
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"{datetime.now():%Y-%m-%d}_{task}"
    log_path = directory / f"{stem}.log"
    summary_path = directory / f"{stem}_summary.md"
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    root = logging.getLogger()
    root.addHandler(handler)
    logger = logging.getLogger(__name__)
    started = time.monotonic()
    summary = JobSummary()
    status = "completed"
    try:
        logger.warning("Starting %s", task)
        yield summary
    except BaseException as error:
        status = "failed"
        summary.warnings.append(f"{type(error).__name__}; see terminal for details")
        logger.error(
            "Job %s failed (%s); see terminal for details", task, type(error).__name__
        )
        raise
    finally:
        elapsed = time.monotonic() - started
        logger.warning("Job %s %s in %.2f seconds", task, status, elapsed)
        root.removeHandler(handler)
        handler.close()
        lines = [
            f"# {task}",
            "",
            f"Status: {status}",
            f"Elapsed: {elapsed:.2f} seconds",
            "",
            "## Inputs",
            *[f"- {value}" for value in inputs],
            "",
            "## Counts",
            *[
                f"- {name}: {f'<{threshold}' if value < threshold else value}"
                for name, value in summary.counts.items()
            ],
            "",
            "## Warnings",
            *([f"- {value}" for value in summary.warnings] or ["- None"]),
            "",
            "## Outputs",
            *[f"- {value}" for value in summary.outputs],
            "",
        ]
        temporary = summary_path.with_suffix(".tmp.md")
        temporary.write_text("\n".join(lines), encoding="utf-8")
        temporary.replace(summary_path)
