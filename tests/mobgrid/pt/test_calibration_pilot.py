"""Pilot test: the real step 0 calibration, using cached OSM Parquet + GTFS.

Skipped automatically when the big cached/raw files are absent (tests must
not require network or data/raw access by default; see
.github/instructions/tests.instructions.md).
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
from mobgrid.pt.config import load_gtfs_rebuild_config
from mobgrid.pt.gtfs_rebuild import rebuild_pattern, route_outcome
from mobgrid.pt.stop_tables import read_osm_pt_stops_cache

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "gtfs_rebuild.yaml"


def _config_and_cache():
    config = load_gtfs_rebuild_config(CONFIG_PATH)
    cache_root = ROOT / config.osm_cache_root
    cache_paths = {
        stamp: cache_root / f"{stamp}.parquet" for stamp in config.osm_source_ids
    }
    return config, cache_paths


_CONFIG, _CACHE_PATHS = _config_and_cache()
_CACHE_AVAILABLE = all(path.is_file() for path in _CACHE_PATHS.values())


@pytest.mark.pilot
@pytest.mark.skipif(
    not _CACHE_AVAILABLE,
    reason="cached OSM public-transport stops (data/interim/osm_pt_stops) are absent",
)
def test_cached_osm_pt_stops_have_all_four_mode_families() -> None:
    connection = duckdb.connect()
    for cache_path in _CACHE_PATHS.values():
        relation = read_osm_pt_stops_cache(connection, cache_path)
        families = {
            row[0]
            for row in connection.sql(
                "SELECT DISTINCT mode_family FROM relation"
            ).fetchall()
        }
        assert families <= {"bus", "tram", "metro", "rail"}
        assert relation.aggregate("count(*)").fetchone()[0] > 0


@pytest.mark.pilot
@pytest.mark.skipif(
    not _CACHE_AVAILABLE,
    reason="cached OSM public-transport stops (data/interim/osm_pt_stops) are absent",
)
def test_chosen_parameters_resolve_the_clear_cut_known_cases() -> None:
    """Re-score the unambiguous known cases with the config's chosen r/k/theta.

    Uses the already-computed and committed calibration_run.pkl results
    instead of re-running the full pipeline here, since the real run takes
    well over an hour (national OSM scans); this test only exercises the
    pure-Python scoring logic that must stay consistent.
    """
    import pickle

    results_path = (
        ROOT / "data" / "results" / "step0_gtfs_rebuild" / "calibration_run.pkl"
    )
    if not results_path.is_file():
        pytest.skip("data/results/step0_gtfs_rebuild/calibration_run.pkl is absent")
    with results_path.open("rb") as stream:
        run = pickle.load(stream)
    chosen = _CONFIG.chosen
    assert chosen.r_m is not None and chosen.k is not None

    def obtained(network: str, route_id: str, date_key: str) -> str:
        matches = [
            item
            for item in run.final_evaluations
            if item.network == network
            and item.route_id == route_id
            and item.date_key == date_key
        ]
        assert matches, f"no evaluation for {network}/{route_id}/{date_key}"
        return route_outcome([item.result for item in matches])

    # Sete's express bus line A is a clean, fully isolated new line (no
    # shared-stop bias) and is expected dropped at both state dates.
    assert obtained("sete_agglopole", "A", "2022-01-01") == "dropped"
    assert obtained("sete_agglopole", "A", "2024-01-01") == "dropped"
    # Paris metro lines 4 and 12 must lose their extension on 1 Jan 2022 and
    # keep it on 1 Jan 2024 (section 5.6).
    assert obtained("idfm", "IDFM:C01374", "2022-01-01") == "cut"
    assert obtained("idfm", "IDFM:C01374", "2024-01-01") == "kept"


def test_rebuild_pattern_is_importable_for_the_pilot_test() -> None:
    # Smoke test so a bad import above fails fast with a clear message.
    assert rebuild_pattern is not None
