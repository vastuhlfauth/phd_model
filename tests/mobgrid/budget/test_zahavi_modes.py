"""Synthetic acceptance tests for the Zahavi mode supplement."""

from pathlib import Path

import duckdb
import numpy as np
import pytest
import yaml
from mobgrid.budget import modes_cache, scope, variation
from mobgrid.budget import zahavi_modes as modes


def test_distribution_shared_bandwidth_and_weighted_ecdf() -> None:
    """Section 9.9: the two years share a bandwidth and use day weights."""
    first = modes.Observations(
        values=np.array([5.0, 10.0, 30.0]),
        weights=np.array([1.0, 2.0, 1.0]),
        household=np.array(["a", "b", "c"]),
    )
    second = modes.Observations(
        values=np.array([10.0, 20.0]),
        weights=np.array([1.0, 1.0]),
        household=np.array(["d", "e"]),
    )
    rows = modes.distribution_rows(
        {("trip", "walk"): first},
        {("trip", "walk"): second},
        trip_max=30,
        day_max=40,
        minimum_n=1,
    )
    a = next(row for row in rows if row["year"] == 2008 and row["minute"] == 10)
    b = next(row for row in rows if row["year"] == 2019 and row["minute"] == 10)
    assert a["ecdf"] == pytest.approx(0.75)
    assert b["ecdf"] == pytest.approx(0.5)
    assert a["bandwidth"] == b["bandwidth"]
    assert a["bandwidth"] > 0


def test_distributions_hide_small_cells() -> None:
    sample = modes.Observations(
        values=np.array([5.0, 10.0]),
        weights=np.array([1.0, 1.0]),
        household=np.array(["a", "b"]),
    )
    rows = modes.distribution_rows(
        {("trip", "walk"): sample},
        {("trip", "walk"): sample},
        trip_max=2,
        day_max=2,
        minimum_n=3,
    )
    assert all(row["n"] == 2 and row["ecdf"] is None for row in rows)


def test_read_samples_distinguishes_mode_use_and_day_group(tmp_path: Path) -> None:
    cache = modes_cache.SurveyCache(tmp_path)
    with duckdb.connect() as con:
        con.execute(
            """
            COPY (SELECT * FROM (VALUES
              ('d1', 'h1', 2.0, 'walk', 5.0),
              ('d1', 'h1', 2.0, 'car_driver', 20.0),
              ('d1', 'h1', 2.0, 'car_driver', 10.0)
            ) t(day_id, ident_men, pond_jour, mode7, duration_min))
            TO ? (FORMAT PARQUET)
        """,
            [str(cache.trips(scope.REFERENCE_SCOPE))],
        )
        con.execute(
            """
            COPY (SELECT 'h1' ident_men, 2.0 pond_jour,
                         'car_driver' day_mode_group, 35.0 total_time_min)
            TO ? (FORMAT PARQUET)
        """,
            [str(cache.days(scope.REFERENCE_SCOPE))],
        )
    samples = modes.read_samples(cache, scope.REFERENCE_SCOPE)
    assert samples["trip", "car_driver"].values.tolist() == [20.0, 10.0]
    assert samples["mode_user_day", "car_driver"].values.tolist() == [30.0]
    assert samples["day_mode_group", "car_driver"].values.tolist() == [35.0]


def test_weighted_deciles_and_thresholds_against_brute_force() -> None:
    sample = modes.Observations(
        values=np.array([5.0, 10.0, 10.0, 30.0]),
        weights=np.array([1.0, 1.0, 1.0, 1.0]),
        household=np.array(["a", "b", "c", "d"]),
    )
    probabilities = np.arange(1, 10) / 10
    expected = np.interp(probabilities, [0.25, 0.75, 1.0], [5, 10, 30])
    assert modes.weighted_deciles(sample, probabilities) == pytest.approx(expected)
    assert modes.threshold_shares(sample, [10, 30]) == pytest.approx([0.75, 0.25])


def test_weighted_ks_is_zero_for_identical_samples() -> None:
    sample = modes.Observations(
        values=np.array([5.0, 10.0, 10.0, 30.0]),
        weights=np.array([1.0, 1.0, 1.0, 1.0]),
        household=np.array(["a", "b", "c", "d"]),
    )
    assert modes.weighted_ks(sample, sample) == pytest.approx(0.0)


def test_rounded_short_intercommunal_trip_stays_out_of_same_commune() -> None:
    bands = modes.crow_fly_bands(np.array([0.0, 0.4, 1.6, 2.0]), rounded=True)
    assert bands.tolist() == ["same commune", "under 2 km", "2-5 km", "2-5 km"]


def test_comparison_outputs_and_suppression() -> None:
    sample = modes.Observations(
        values=np.array([5.0, 10.0, 30.0]),
        weights=np.array([1.0, 2.0, 1.0]),
        household=np.array(["a", "b", "c"]),
    )
    draws = modes.make_draws(sample.household, n_reps=20, seed=7)
    inputs = {("trip", "walk"): sample}
    deciles, thresholds, ks = modes.comparison_rows(
        inputs, inputs, draws, draws, thresholds=[10], minimum_n=1
    )
    assert deciles[4]["shift"] == pytest.approx(0)
    assert deciles[4]["ci_low"] == pytest.approx(0)
    assert thresholds[0]["share_2008"] == pytest.approx(0.75)
    assert thresholds[0]["change_points"] == pytest.approx(0)
    assert ks[0]["D"] == pytest.approx(0)
    deciles, thresholds, ks = modes.comparison_rows(
        inputs, inputs, draws, draws, thresholds=[10], minimum_n=4
    )
    assert np.isnan(deciles[0]["interpolated_2008"])
    assert np.isnan(thresholds[0]["change_points"])
    assert np.isnan(ks[0]["D"])


def test_person_mode_minutes_sum_to_total_with_open_and_zero_days(
    tmp_path: Path,
) -> None:
    cache = modes_cache.SurveyCache(tmp_path)
    with duckdb.connect() as con:
        con.execute(
            """
            COPY (SELECT * FROM (VALUES
              ('h1', 10.0), ('h2', 10.0)
            ) t(ident_men, weight)) TO ? (FORMAT PARQUET)
        """,
            [str(cache.roster)],
        )
        con.execute(
            """
            COPY (SELECT * FROM (VALUES
              ('d1', 'h1', 2.0, TRUE), ('d2', 'h1', 2.0, FALSE)
            ) t(day_id, ident_men, pond_jour, is_round)) TO ? (FORMAT PARQUET)
        """,
            [str(cache.day_base)],
        )
        con.execute(
            """
            COPY (SELECT * FROM (VALUES
              ('d1', 'walk', 10.0), ('d1', 'car_driver', 20.0)
            ) t(day_id, mode7, duration_min)) TO ? (FORMAT PARQUET)
        """,
            [str(cache.trips(scope.REFERENCE_SCOPE))],
        )
    draws = modes.make_draws(np.array(["h1", "h2"]), n_reps=20, seed=3)
    metrics = modes.person_mode_metrics(cache, scope.REFERENCE_SCOPE, draws)
    assert metrics["walk"].value == pytest.approx(20 / 18)
    assert metrics["car_driver"].value == pytest.approx(40 / 18)
    assert sum(metrics[mode].value for mode in modes.vr.MODE7_LABELS) == pytest.approx(
        metrics["All"].value
    )
    assert sum(metrics[mode].replicates for mode in modes.vr.MODE7_LABELS) == (
        pytest.approx(metrics["All"].replicates)
    )


def test_mode_shares_use_trip_and_minute_weights() -> None:
    samples = {
        ("trip", "walk"): modes.Observations(
            np.array([10.0, 20.0]), np.array([1.0, 2.0]), np.array(["a", "b"])
        ),
        ("trip", "car_driver"): modes.Observations(
            np.array([30.0]), np.array([1.0]), np.array(["c"])
        ),
    }
    trip_share, minute_share, n = modes.mode_shares(samples, "walk")
    assert n == 2
    assert trip_share == pytest.approx(3 / 4)
    assert minute_share == pytest.approx(50 / 80)


def test_b3_quote_preserves_existing_terms_and_hides_small_mode(tmp_path: Path) -> None:
    report = tmp_path / "step12.md"
    report.write_text(
        "# Variation (`round-dest-local`)\n"
        "## B3. Mode shift-share, 2008 -> 2019\n"
        "| Term | Minutes/day | 95% CI |\n"
        "|---|---|---|\n"
        "| trips volume | -2.6 | [-3.8, -1.5] |\n"
        "| mode | n 2008 | n 2019 | share 2008 | share 2019 | "
        "min/trip 2008 | min/trip 2019 | mix (min) | within (min) | "
        "of which km/trip | of which speed | interaction (min) | "
        "distance-known share 2008 | distance-known share 2019 | "
        "within selection (min) |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| walk | 100 | 120 | 20% | 21% | 10 | 12 | 0.2 | 2 | 0.5 | "
        "1 | 0.1 | 100% | 100% | 0.5 |\n"
        "| train | 5 | 120 | 1% | 1% | 40 | 45 | 1 | 2 | 1 | "
        "1 | 0 | 100% | 100% | 0 |\n"
        "## B4a. Next\n",
        encoding="utf-8",
    )
    quoted = modes.b3_excerpt(report, minimum_n=50)
    assert "[-3.8, -1.5]" in quoted
    assert "25.0%" in quoted
    assert "| train | 5 | 120 | - |" in quoted
    assert "| train | 5 | 120 | 1%" not in quoted


def test_missing_b3_mode_intervals_use_shared_household_draws() -> None:
    households = np.array([f"h{i}" for i in range(60)])
    sample = variation.TripSample(
        day_weight=np.ones(60),
        day_household=households,
        trip_weight=np.ones(60),
        trip_household=households,
        trip_minutes=10.0 + np.arange(60) % 3,
        trip_km=np.full(60, 4.0),
        trip_group=np.full(60, "car_driver"),
    )
    draws = modes.make_draws(households, n_reps=20, seed=3)
    intervals = modes.b3_missing_intervals(sample, sample, draws, draws, minimum_n=50)
    assert intervals["car_driver"]["within"] == pytest.approx((0.0, 0.0))
    assert intervals["car_driver"]["mix"] == pytest.approx((0.0, 0.0))


def test_report_reads_cached_parquet_and_writes_all_csvs(tmp_path: Path) -> None:
    caches = []
    for year in (2008, 2019):
        root = tmp_path / str(year)
        root.mkdir()
        cache = modes_cache.SurveyCache(root)
        caches.append(cache)
        with duckdb.connect() as con:
            con.execute(
                """
                COPY (SELECT 'h' || i::VARCHAR ident_men, 5.0 weight
                      FROM range(60) t(i)) TO ? (FORMAT PARQUET)
            """,
                [str(cache.roster)],
            )
            con.execute(
                """
                COPY (SELECT 'd' || i::VARCHAR day_id, 'h' || i::VARCHAR ident_men,
                             1.0 pond_jour, TRUE is_round FROM range(60) t(i))
                TO ? (FORMAT PARQUET)
            """,
                [str(cache.day_base)],
            )
            con.execute(
                """
                COPY (SELECT 'd' || i::VARCHAR day_id, 'h' || i::VARCHAR ident_men,
                             1.0 pond_jour, 'walk' mode7, 5.0 + i % 10 duration_min,
                             2.0 crow_fly_km, 4.0 distance_km FROM range(60) t(i))
                TO ? (FORMAT PARQUET)
            """,
                [str(cache.trips(scope.REFERENCE_SCOPE))],
            )
            con.execute(
                """
                COPY (SELECT 'h' || i::VARCHAR ident_men, 1.0 pond_jour,
                             'walking_only' day_mode_group,
                             5.0 + i % 10 total_time_min FROM range(60) t(i))
                TO ? (FORMAT PARQUET)
            """,
                [str(cache.days(scope.REFERENCE_SCOPE))],
            )
    source = tmp_path / "b3.md"
    source.write_text(
        "# Variation (`round-dest-local`)\n"
        "## B3. Mode shift-share, 2008 -> 2019\n"
        "| Term | Minutes/day | 95% CI |\n"
        "| trips volume | 0 | [0, 0] |\n"
        "| walk | 60 | 60 | 100% | 100% | 10 | 10 | 0 | 0 | 0 | "
        "0 | 0 | 100% | 100% | 0 |\n"
        "## B4a. Next\n",
        encoding="utf-8",
    )
    config = modes.ReportConfig(
        trip_grid_max_min=240,
        day_grid_max_min=360,
        minimum_cell_n=50,
        thresholds_min=[14, 15],
        bootstrap_reps=200,
        seed=0,
        cache_dir="cache",
        b3_report=str(source),
        logs_dir="logs",
        reference_2008_min=52.0,
        reference_2019_min=57.0,
        reference_tolerance_min=0.05,
    )
    out = tmp_path / "step12_modes"
    timings = modes.run_report(
        out,
        caches[0],
        caches[1],
        config,
        selected_scopes=[scope.REFERENCE_SCOPE],
        equivalence_margin=0.15,
        secondary_margin=0.10,
    )
    for name in (
        "distributions.csv",
        "deciles.csv",
        "thresholds.csv",
        "ks.csv",
        "band_deciles.csv",
        "stability.csv",
    ):
        assert (out / name).is_file()
    text = out.with_suffix(".md").read_text(encoding="utf-8")
    assert "round-dest-local" in text
    assert "B3" in text
    assert "the table below adds 95% intervals" in text
    assert "DIFFERS" in text
    assert timings["distributions"] >= 0


def test_cli_routes_survey_cache_and_writes_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "modes.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "trip_grid_max_min": 240,
                "day_grid_max_min": 360,
                "minimum_cell_n": 50,
                "thresholds_min": [15],
                "bootstrap_reps": 200,
                "seed": 0,
                "cache_dir": str(tmp_path / "cache"),
                "b3_report": str(tmp_path / "source.md"),
                "logs_dir": str(tmp_path / "logs"),
                "reference_2008_min": 52.0,
                "reference_2019_min": 57.0,
                "reference_tolerance_min": 0.05,
            }
        ),
        encoding="utf-8",
    )
    cache = modes_cache.SurveyCache(tmp_path / "cached")
    monkeypatch.setattr(modes.modes_cache, "load_survey", lambda *a, **k: cache)
    monkeypatch.setattr(modes, "_sample_counts", lambda *a, **k: (60, 55, 100))
    invoked = []

    def fake_report(*args: object, **kwargs: object) -> dict[str, float]:
        invoked.append((args, kwargs))
        return {"synthetic": 0.1}

    monkeypatch.setattr(modes, "run_report", fake_report)
    out = tmp_path / "report"
    assert (
        modes.main(
            [
                "--out",
                str(out),
                "--modes-config",
                str(config_path),
                "--scope",
                "round-dest-local",
            ]
        )
        == 0
    )
    assert invoked[0][0][0] == out
    summaries = list((tmp_path / "logs").glob("*_zahavi_modes_summary.md"))
    assert len(summaries) == 1
    assert "60 roster persons" in summaries[0].read_text(encoding="utf-8")


def test_cli_builds_and_reads_synthetic_survey_caches(
    synthetic_emp_zip: Path, synthetic_entd2008_raw_dir: Path, tmp_path: Path
) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "# Variation (`round-dest-local`)\n"
        "## B3. Mode shift-share, 2008 -> 2019\n"
        "| trips volume | 0 | [0, 0] |\n"
        "## B4a. Next\n",
        encoding="utf-8",
    )
    config = tmp_path / "modes.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "trip_grid_max_min": 240,
                "day_grid_max_min": 360,
                "minimum_cell_n": 50,
                "thresholds_min": [15, 30, 45, 60, 14, 29, 44, 59],
                "bootstrap_reps": 200,
                "seed": 0,
                "cache_dir": str(tmp_path / "cache"),
                "b3_report": str(source),
                "logs_dir": str(tmp_path / "logs"),
                "reference_2008_min": 52.0,
                "reference_2019_min": 57.0,
                "reference_tolerance_min": 0.05,
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "step12_modes"
    assert (
        modes.main(
            [
                "--out",
                str(out),
                "--modes-config",
                str(config),
                "--scope",
                "round-dest-local",
                "--emp2019-data-path",
                str(synthetic_emp_zip),
                "--entd2008-data-path",
                str(synthetic_entd2008_raw_dir),
            ]
        )
        == 0
    )
    assert (out / "stability.csv").is_file()
    assert out.with_suffix(".md").is_file()
    assert len(list((tmp_path / "cache").glob("*/*/signature.json"))) == 2
    summary = next((tmp_path / "logs").glob("*_summary.md")).read_text(encoding="utf-8")
    assert "Status: completed" in summary
    assert "load 2008 cache" in summary and "load 2019 cache" in summary
