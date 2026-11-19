"""Reusable weekday survey cache for the mode report (section 9.9)."""

from __future__ import annotations

import hashlib
import json
import logging
import tempfile
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import duckdb
import pyarrow as pa

from mobgrid.budget import daily_energy, emp2019, entd2008
from mobgrid.budget import scope as scope_module
from mobgrid.budget import variation_report as vr
from mobgrid.energy.rates import load_energy_config

LOGGER = logging.getLogger(__name__)


@contextmanager
def _stage(name: str) -> Generator[None]:
    start = time.monotonic()
    LOGGER.info("%s: started", name)
    try:
        yield
    finally:
        LOGGER.info("%s: ended after %.1f s", name, time.monotonic() - start)


def _hash_file(update: Callable[[bytes], object], path: Path) -> None:
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            update(chunk)


def input_signature(
    survey: ModuleType,
    data_path: Path,
    activity_stay_min: float,
    config_path: Path = vr.DEFAULT_CONFIG_PATH,
) -> str:
    """Hash survey inputs, configuration and reconstruction code, section 9.9."""
    digest = hashlib.sha256()
    if survey is emp2019:
        raw_files = [data_path]
    elif survey is entd2008:
        raw_files = [data_path / name for name in sorted(entd2008.RAW_FILES)]
    else:
        raise ValueError(f"unsupported survey: {survey.__name__}")
    files = [
        *raw_files,
        config_path,
        *sorted(Path(__file__).parent.glob("*.py")),
        *sorted((Path(__file__).parent.parent / "energy").glob("*.py")),
    ]
    digest.update(
        json.dumps(
            {
                "survey": survey.SURVEY_NAME,
                "density_source": survey.DEFAULT_DENSITY_SOURCE,
                "activity_stay_min": activity_stay_min,
            },
            sort_keys=True,
        ).encode()
    )
    for path in files:
        digest.update(str(path.resolve()).encode())
        _hash_file(digest.update, path)
    return digest.hexdigest()


@dataclass(frozen=True)
class SurveyCache:
    """Paths to scoped weekday trips, days, roster and open-day inputs."""

    root: Path

    @property
    def roster(self) -> Path:
        return self.root / "roster.parquet"

    @property
    def day_base(self) -> Path:
        return self.root / "day_base.parquet"

    def trips(self, scope: scope_module.Scope) -> Path:
        return self.root / f"{scope.id}_trips.parquet"

    def days(self, scope: scope_module.Scope) -> Path:
        return self.root / f"{scope.id}_days.parquet"


def _copy(con: duckdb.DuckDBPyConnection, query: str, path: Path) -> None:
    con.execute(f"COPY ({query}) TO ? (FORMAT PARQUET)", [str(path)])


def _verify_cache(cache: SurveyCache, signature: str) -> None:
    paths = [cache.roster, cache.day_base]
    for selected in scope_module.ALL_SCOPES:
        paths.extend((cache.trips(selected), cache.days(selected)))
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise RuntimeError(f"incomplete survey cache: {', '.join(missing)}")
    signature_file = cache.root / "signature.json"
    if not signature_file.is_file():
        raise RuntimeError(f"survey cache missing input signature: {signature_file}")
    metadata = json.loads(signature_file.read_text(encoding="utf-8"))
    if metadata.get("signature") != signature:
        raise RuntimeError(f"survey cache signature mismatch: {signature_file}")


def load_survey(
    survey: ModuleType,
    data_path: Path,
    cache_dir: Path,
    *,
    activity_stay_min: float,
    config_path: Path = vr.DEFAULT_CONFIG_PATH,
) -> SurveyCache:
    """Build once or read the signed weekday cache for one survey, section 9.9."""
    with _stage(f"{survey.SURVEY_NAME} input signature"):
        signature = input_signature(survey, data_path, activity_stay_min, config_path)
    survey_dir = cache_dir / survey.__name__.rsplit(".", 1)[-1]
    cache = SurveyCache(survey_dir / signature)
    if cache.root.is_dir():
        with _stage(f"{survey.SURVEY_NAME} cache read"):
            _verify_cache(cache, signature)
        return cache

    survey_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=survey_dir, prefix="building-") as temp:
        staging = SurveyCache(Path(temp))
        with duckdb.connect() as con:
            with _stage(f"{survey.SURVEY_NAME} extract and register"):
                paths = survey.extract_tables(data_path, staging.root / "csv")
                survey.register_views(con, paths)
            with _stage(f"{survey.SURVEY_NAME} build trip legs"):
                survey.build_trip_legs(
                    con,
                    load_energy_config(config_path),
                    density_source=survey.DEFAULT_DENSITY_SOURCE,
                )
            with _stage(f"{survey.SURVEY_NAME} scope and roster"):
                scope_module.create_scope_views_from_trip_legs(
                    con, activity_stay_min=activity_stay_min
                )
                vr._PERSON_EXT_BY_SURVEY[survey.SURVEY_NAME](con)
                roster = vr._scope_person_weekday_rows(con, survey.SURVEY_NAME, None)
                if not roster:
                    raise ValueError(f"{survey.SURVEY_NAME}: empty respondent roster")
                columns = list(zip(*roster, strict=True))
                con.register(
                    "cache_roster",
                    pa.table(dict(zip(
                        ("ident_ind", "ident_men", "population_category", "weight"),
                        columns,
                        strict=True,
                    ))),
                )
                _copy(con, "SELECT * FROM cache_roster", staging.roster)
                _copy(
                    con,
                    """
                    SELECT t.day_id, any_value(t.ident_ind) AS ident_ind,
                        any_value(t.ident_men) AS ident_men,
                        any_value(t.pond_jour) AS pond_jour,
                        coalesce(any_value(d.is_round), FALSE) AS is_round
                    FROM trip_legs t LEFT JOIN scope_days d ON d.day_id = t.day_id
                    WHERE t.typejour = 1 AND t.pond_jour > 0
                    GROUP BY t.day_id
                    """,
                    staging.day_base,
                )
            for selected in scope_module.ALL_SCOPES:
                with _stage(f"{survey.SURVEY_NAME} {selected.id} tables"):
                    vr._create_frames_tables(
                        con, sample_pct=None, selected_scope=selected
                    )
                    daily_energy.create_day_summary(
                        con,
                        where_sql=(
                            "typejour = 1 AND pond_jour > 0 AND "
                            f"({selected.trip_filter_sql('trip_legs')})"
                        ),
                    )
                    _copy(
                        con,
                        """
                        SELECT v.*, t.mode_group
                        FROM vr_trips v JOIN trip_legs t
                            ON t.day_id = v.day_id AND t.num_dep = v.num_dep
                        """,
                        staging.trips(selected),
                    )
                    _copy(con, "SELECT * FROM day_summary", staging.days(selected))
        (staging.root / "signature.json").write_text(
            json.dumps({"signature": signature, "survey": survey.SURVEY_NAME}),
            encoding="utf-8",
        )
        _verify_cache(staging, signature)
        staging.root.rename(cache.root)
    return cache
