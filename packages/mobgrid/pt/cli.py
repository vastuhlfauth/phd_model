"""Command-line entry point for the step 0 GTFS rebuilding calibration."""

from __future__ import annotations

import argparse
import logging
import pickle
from pathlib import Path
from tempfile import TemporaryDirectory

from mobgrid.pt.calibrate import run_calibration
from mobgrid.pt.config import load_gtfs_rebuild_config
from mobgrid.pt.report import write_report

logger = logging.getLogger("mobgrid.pt")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mobgrid.pt")
    parser.add_argument(
        "--config", type=Path, default=Path("config/gtfs_rebuild.yaml")
    )
    parser.add_argument(
        "--gtfs-inventory", type=Path, default=Path("config/gtfs_inventory.csv")
    )
    parser.add_argument("--sources", type=Path, default=Path("config/sources.yaml"))
    parser.add_argument(
        "--contours",
        type=Path,
        default=Path("data/raw/contours/2026/communes-5m.geojson.gz"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/data/step0_gtfs_rebuild.md"),
        help="where to write the committed markdown report",
    )
    parser.add_argument(
        "--results-pickle",
        type=Path,
        default=Path("data/results/step0_gtfs_rebuild/calibration_run.pkl"),
        help="where to persist the full CalibrationRun for later inspection",
    )
    parser.add_argument(
        "--scratch-dir",
        type=Path,
        default=None,
        help="kept GTFS extraction scratch directory (default: a temp dir)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the full step 0 calibration (section 5.6) and write the report.

    Reads real GTFS and OSM data under ``data/raw`` and caches extracted OSM
    public-transport stops under ``data/interim/osm_pt_stops`` (configured
    by ``osm_cache_root``); takes well over an hour on a full run because
    it reads the national OSM extracts, see docs/progress.md.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parser().parse_args(argv)
    config = load_gtfs_rebuild_config(args.config)

    def _run(scratch_dir: Path) -> int:
        result = run_calibration(
            config, args.gtfs_inventory, args.sources, args.contours, scratch_dir
        )
        args.results_pickle.parent.mkdir(parents=True, exist_ok=True)
        with args.results_pickle.open("wb") as stream:
            pickle.dump(result, stream)
        write_report(result, config, args.report)
        logger.info(
            "chosen: r=%s k=%s theta=%s",
            result.grid_result.chosen_r_m,
            result.grid_result.chosen_k,
            result.grid_result.chosen_theta,
        )
        logger.info("report written to %s", args.report)
        return 0

    if args.scratch_dir is not None:
        args.scratch_dir.mkdir(parents=True, exist_ok=True)
        return _run(args.scratch_dir)
    with TemporaryDirectory(prefix="gtfs-rebuild-") as scratch:
        return _run(Path(scratch))
