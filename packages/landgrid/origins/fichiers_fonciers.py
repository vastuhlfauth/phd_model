"""Fichiers fonciers dwelling counts for section 6."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import shutil
import statistics
import sys
import tempfile
import time
import zipfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import yaml
from common.duckdb_io import read_parquet, write_parquet
from common.grid import cell_id

from landgrid.origins.filosofi import (
    NaturalCellLookup,
    build_natural_cell_lookup,
    derived_departments,
)
from landgrid.origins.job import open_restricted_connection

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class VintageConfig:
    parquet_pattern: str
    second_home_column: str
    second_home_code: str
    second_home_source: str = "own"


@dataclass(frozen=True)
class CensusVintageConfig:
    format: str
    path: str
    geography_column: str
    measures: dict[str, str]
    member: str | None = None
    delimiter: str | None = None
    geography_type_column: str | None = None
    geography_type: str | None = None
    time_period_column: str | None = None
    time_period: str | None = None
    table_column: str | None = None
    table_id: str | None = None
    dataset_column: str | None = None
    dataset_id: str | None = None
    measure_column: str | None = None


@dataclass(frozen=True)
class ReportConfig:
    interim_directory: str
    output_directory: str
    ff_vintage_to_census: dict[int, int]
    ff_cells_pattern: str
    ff_natural_pattern: str
    ff_checkpoint_pattern: str
    ff_checkpoint_data_pattern: str
    ff_checkpoint_metadata_pattern: str
    ff_communes_pattern: str
    ff_extra_codes_pattern: str
    metadata_pattern: str
    report_pattern: str
    count_suppression_threshold: int
    top_second_home_gaps: int
    ratio_quantiles: tuple[float, ...]
    comparison_report_pattern: str
    contours_2021: str
    cell_ratio_quantiles: tuple[float, ...]


@dataclass(frozen=True)
class DownscaleConfig:
    output_year: int
    ff_vintage: int
    cell_resolution_m: int
    output_pattern: str
    metadata_pattern: str
    composition_output_pattern: str
    composition_report_pattern: str
    composition_model_pattern: str
    composition_metadata_pattern: str
    composition_failures_pattern: str
    composition_checkpoint_pattern: str
    composition_stage_pattern: str
    composition_checkpoint_state: str
    crossval_choice_pattern: str
    crossval_report_pattern: str
    crossval_checkpoint_pattern: str
    crossval_fold_checkpoint_pattern: str
    crossval_folds: int
    crossval_seed: int
    crossval_tie_tolerance: float
    poisson_folds: int
    poisson_seed: int
    poisson_tolerance: float
    poisson_max_iterations: int
    ipf_tolerance: float
    ipf_max_iterations: int


@dataclass(frozen=True)
class ValidationConfig:
    eurostat_grid: str
    eurostat_resolution_m: int
    density_thresholds_population_km2: tuple[int, int]
    within_tolerance_fraction: float
    report_pattern: str
    checkpoint_pattern: str


@dataclass(frozen=True)
class JobConfig:
    log_directory: str
    ff_task_pattern: str
    composition_task: str
    validation_task: str
    crossval_task: str


@dataclass(frozen=True)
class OriginsConfig:
    filosofi_200m_archive: str
    filosofi_natural_archive: str
    vintages: dict[int, VintageConfig]
    census: dict[int, CensusVintageConfig]
    report: ReportConfig
    downscale: DownscaleConfig
    validation: ValidationConfig
    jobs: JobConfig
    logh: str
    vacant_code: str
    owner_code: str
    let_code: str
    social_code: str
    recent_transfer: dict[int, str]
    jannath_min: int
    dniv_code_threshold: int
    stoth_negative_missing: bool
    nbetagemax_used: bool
    construction_period_starts: tuple[int, int, int]
    second_home_rescaling: float | None


def load_origins_config(path: str | Path = "config/origins.yaml") -> OriginsConfig:
    """Load and validate the step-3 origins configuration."""
    with Path(path).open(encoding="utf-8") as stream:
        raw = yaml.safe_load(stream)
    vintages = {
        int(vintage): VintageConfig(
            parquet_pattern=value["parquet_pattern"],
            second_home_column=value["second_home_column"],
            second_home_code=value["second_home_code"],
            second_home_source=value.get("second_home_source", "own"),
        )
        for vintage, value in raw["vintages"].items()
    }
    for vintage, vintage_config in vintages.items():
        if vintage_config.second_home_source not in {"own", "hybrid_2024"}:
            raise ValueError(f"invalid second_home_source for vintage {vintage}")
        if vintage_config.second_home_source == "hybrid_2024" and vintage not in {
            2021,
            2022,
        }:
            raise ValueError(
                "hybrid_2024 is only available for vintages 2021 and 2022"
            )
    census = {
        int(vintage): CensusVintageConfig(
            format=value["format"],
            path=value["path"],
            geography_column=value["geography_column"],
            measures=value["measures"],
            member=value.get("member"),
            delimiter=value.get("delimiter"),
            geography_type_column=value.get("geography_type_column"),
            geography_type=value.get("geography_type"),
            time_period_column=value.get("time_period_column"),
            time_period=value.get("time_period"),
            table_column=value.get("table_column"),
            table_id=value.get("table_id"),
            dataset_column=value.get("dataset_column"),
            dataset_id=value.get("dataset_id"),
            measure_column=value.get("measure_column"),
        )
        for vintage, value in raw["census"].items()
    }
    report = raw["report"]
    periods = tuple(
        int(value) for value in raw["cleaning"]["construction_period_starts"]
    )
    if len(periods) != 3 or list(periods) != sorted(set(periods)):
        raise ValueError("construction period starts must be three increasing years")
    downscale = raw["downscale"]
    if (
        int(downscale["poisson_folds"]) < 2
        or int(downscale["crossval_folds"]) != 5
        or not math.isfinite(float(downscale["crossval_tie_tolerance"]))
        or float(downscale["crossval_tie_tolerance"]) < 0
        or float(downscale["poisson_tolerance"]) <= 0
        or int(downscale["poisson_max_iterations"]) <= 0
        or float(downscale["ipf_tolerance"]) <= 0
        or int(downscale["ipf_max_iterations"]) <= 0
    ):
        raise ValueError("invalid composition model or IPF configuration")
    validation = raw["validation"]
    density_thresholds = tuple(
        int(value)
        for value in validation["density_thresholds_population_km2"]
    )
    if (
        len(density_thresholds) != 2
        or density_thresholds[0] <= 0
        or density_thresholds[0] >= density_thresholds[1]
    ):
        raise ValueError(
            "validation density thresholds must be two increasing positive values"
        )
    return OriginsConfig(
        filosofi_200m_archive=raw["filosofi"]["200m_archive"],
        filosofi_natural_archive=raw["filosofi"]["natural_archive"],
        vintages=vintages,
        census=census,
        report=ReportConfig(
            interim_directory=report["interim_directory"],
            output_directory=report["output_directory"],
            ff_vintage_to_census={
                int(vintage): int(census_vintage)
                for vintage, census_vintage in report[
                    "ff_vintage_to_census"
                ].items()
            },
            ff_cells_pattern=report["ff_cells_pattern"],
            ff_natural_pattern=report["ff_natural_pattern"],
            ff_checkpoint_pattern=report["ff_checkpoint_pattern"],
            ff_checkpoint_data_pattern=report["ff_checkpoint_data_pattern"],
            ff_checkpoint_metadata_pattern=report["ff_checkpoint_metadata_pattern"],
            ff_communes_pattern=report["ff_communes_pattern"],
            ff_extra_codes_pattern=report["ff_extra_codes_pattern"],
            metadata_pattern=report["metadata_pattern"],
            report_pattern=report["report_pattern"],
            count_suppression_threshold=int(
                report["count_suppression_threshold"]
            ),
            top_second_home_gaps=int(report["top_second_home_gaps"]),
            ratio_quantiles=tuple(
                float(value) for value in report["ratio_quantiles"]
            ),
            comparison_report_pattern=report["comparison_report_pattern"],
            contours_2021=report["contours_2021"],
            cell_ratio_quantiles=tuple(
                float(value) for value in report["cell_ratio_quantiles"]
            ),
        ),
        downscale=DownscaleConfig(
            output_year=int(raw["downscale"]["output_year"]),
            ff_vintage=int(raw["downscale"]["ff_vintage"]),
            cell_resolution_m=int(raw["downscale"]["cell_resolution_m"]),
            output_pattern=raw["downscale"]["output_pattern"],
            metadata_pattern=raw["downscale"]["metadata_pattern"],
            composition_output_pattern=raw["downscale"]["composition_output_pattern"],
            composition_report_pattern=raw["downscale"]["composition_report_pattern"],
            composition_model_pattern=raw["downscale"]["composition_model_pattern"],
            composition_metadata_pattern=raw["downscale"]["composition_metadata_pattern"],
            composition_failures_pattern=raw["downscale"]["composition_failures_pattern"],
            composition_checkpoint_pattern=raw["downscale"][
                "composition_checkpoint_pattern"
            ],
            composition_stage_pattern=raw["downscale"]["composition_stage_pattern"],
            composition_checkpoint_state=raw["downscale"][
                "composition_checkpoint_state"
            ],
            crossval_choice_pattern=raw["downscale"]["crossval_choice_pattern"],
            crossval_report_pattern=raw["downscale"]["crossval_report_pattern"],
            crossval_checkpoint_pattern=raw["downscale"][
                "crossval_checkpoint_pattern"
            ],
            crossval_fold_checkpoint_pattern=raw["downscale"][
                "crossval_fold_checkpoint_pattern"
            ],
            crossval_folds=int(raw["downscale"]["crossval_folds"]),
            crossval_seed=int(raw["downscale"]["crossval_seed"]),
            crossval_tie_tolerance=float(
                raw["downscale"]["crossval_tie_tolerance"]
            ),
            poisson_folds=int(raw["downscale"]["poisson_folds"]),
            poisson_seed=int(raw["downscale"]["poisson_seed"]),
            poisson_tolerance=float(raw["downscale"]["poisson_tolerance"]),
            poisson_max_iterations=int(raw["downscale"]["poisson_max_iterations"]),
            ipf_tolerance=float(raw["downscale"]["ipf_tolerance"]),
            ipf_max_iterations=int(raw["downscale"]["ipf_max_iterations"]),
        ),
        validation=ValidationConfig(
            eurostat_grid=validation["eurostat_grid"],
            eurostat_resolution_m=int(validation["eurostat_resolution_m"]),
            density_thresholds_population_km2=density_thresholds,
            within_tolerance_fraction=float(
                validation["within_tolerance_fraction"]
            ),
            report_pattern=validation["report_pattern"],
            checkpoint_pattern=validation["checkpoint_pattern"],
        ),
        jobs=JobConfig(**raw["jobs"]),
        logh=raw["dwelling"]["logh"],
        vacant_code=raw["vacant"]["ccthp"],
        owner_code=raw["owner_occupied"]["ccthp"],
        let_code=raw["let"]["ccthp"],
        social_code=raw["social_housing"]["catpro2"],
        recent_transfer={
            int(vintage): code for vintage, code in raw["recent_transfer"].items()
        },
        jannath_min=int(raw["cleaning"]["jannath_min"]),
        dniv_code_threshold=int(raw["cleaning"]["dniv_code_threshold"]),
        stoth_negative_missing=bool(raw["cleaning"]["stoth_negative_missing"]),
        nbetagemax_used=bool(raw["cleaning"]["nbetagemax_used"]),
        construction_period_starts=periods,
        second_home_rescaling=raw["second_home_rescaling"],
    )


def coordinate_to_200m_cell(easting_m: float, northing_m: float) -> int:
    """Assign EPSG:3035 coordinates to a 200 m cell by the floor rule."""
    if not math.isfinite(easting_m) or not math.isfinite(northing_m):
        raise ValueError("coordinates must be finite")
    if easting_m < 0 or northing_m < 0:
        raise ValueError("EPSG:3035 coordinates must be non-negative")
    return cell_id(northing_m, easting_m, 200)


def classify_dwelling(
    row: Mapping[str, Any],
    second_home_column: str,
    second_home_code: str,
    recent_transfer_code: str,
    *,
    logh: str = "t",
    vacant_code: str = "V",
    owner_code: str = "P",
    let_code: str = "L",
    social_code: str = "F1",
    second_home_source: str = "own",
) -> dict[str, int]:
    """Classify one Fichiers fonciers dwelling row (section 6.3)."""
    is_dwelling = row.get("logh") == logh
    is_vacant = is_dwelling and row.get("ccthp") == vacant_code
    second_value = row.get(second_home_column)
    if second_home_source not in {"own", "hybrid_2024"}:
        raise ValueError(f"invalid second_home_source: {second_home_source}")
    later_status = row.get("rppo_rs_2024")
    effective_second = (
        later_status if second_home_source == "hybrid_2024"
        and later_status in {"RS", "RPPO"} else second_value
    )
    is_second_home = is_dwelling and effective_second == second_home_code
    is_extra_dwelling = (
        is_dwelling
        and not is_vacant
        and not is_second_home
        and row.get("ccthp") not in {owner_code, let_code}
    )
    is_extra_dwelling_without_null = (
        is_extra_dwelling and row.get("ccthp") is not None
    )
    is_recent_transfer = (
        is_dwelling
        and not is_vacant
        and not is_second_home
        and second_value == recent_transfer_code
    )
    is_main = is_dwelling and not is_vacant and not is_second_home
    is_owner = is_main and row.get("ccthp") == owner_code
    is_owner_second_home = is_second_home and row.get("ccthp") == owner_code
    is_owner_recent_transfer = (
        is_recent_transfer and row.get("ccthp") == owner_code
    )
    is_social = is_dwelling and row.get("catpro2") == social_code
    is_social_main = is_social and is_main
    house = is_dwelling and row.get("loghmais") == "t"
    flat = is_dwelling and row.get("loghappt") == "t"
    return {
        "dwelling": int(is_dwelling),
        "vacant": int(is_vacant),
        "second_home": int(is_second_home),
        "main_residence": int(is_main),
        "extra_dwellings": int(is_extra_dwelling),
        "extra_dwellings_without_null": int(is_extra_dwelling_without_null),
        "broad_second_homes": int(is_second_home or is_extra_dwelling),
        "broad_second_homes_without_null": int(
            is_second_home or is_extra_dwelling_without_null
        ),
        "broad_main_residences": int(is_main and not is_extra_dwelling),
        "broad_main_residences_without_null": int(
            is_main and not is_extra_dwelling_without_null
        ),
        "recent_transfer": int(is_recent_transfer),
        "owner_occupied_main_residence": int(is_owner),
        "owner_occupied_second_home": int(is_owner_second_home),
        "owner_occupied_recent_transfer": int(is_owner_recent_transfer),
        "social_housing": int(is_social),
        "social_housing_main_residence": int(is_social_main),
        "house": int(house),
        "flat": int(flat),
    }


def _clean_dnbniv(value: Any, threshold: int) -> int | None:
    if value is None:
        return None
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return None if number >= threshold else number


def aggregate_dwelling_rows(
    rows: Iterable[Mapping[str, Any]],
    second_home_column: str,
    second_home_code: str,
    recent_transfer_code: str,
    *,
    vintage: int = 2022,
    logh: str = "t",
    vacant_code: str = "V",
    owner_code: str = "P",
    let_code: str = "L",
    social_code: str = "F1",
) -> dict[str, int | float | None]:
    """Aggregate a synthetic list of premises into one 200 m cell summary."""
    totals = {
        "dwellings": 0,
        "main_residences": 0,
        "vacant": 0,
        "second_homes": 0,
        "extra_dwellings": 0,
        "extra_dwellings_without_null": 0,
        "broad_second_homes": 0,
        "broad_second_homes_without_null": 0,
        "broad_main_residences": 0,
        "broad_main_residences_without_null": 0,
        "recent_transfers": 0,
        "owner_occupied_main_residences": 0,
        "owner_occupied_second_homes": 0,
        "owner_occupied_recent_transfers": 0,
        "social_housing": 0,
        "social_housing_main_residences": 0,
        "houses": 0,
        "flats": 0,
    }
    npiece_values: list[int] = []
    dnbniv_values: list[int] = []
    stoth_values: list[int] = []
    jannath_values: list[int] = []
    npiece_sum = npiece_sum_sq = 0
    dnbniv_sum = dnbniv_sum_sq = 0

    for row in rows:
        classified = classify_dwelling(
            row,
            second_home_column,
            second_home_code,
            recent_transfer_code,
            logh=logh,
            vacant_code=vacant_code,
            owner_code=owner_code,
            let_code=let_code,
            social_code=social_code,
        )
        if not classified["dwelling"]:
            continue
        totals["dwellings"] += 1
        totals["main_residences"] += classified["main_residence"]
        totals["vacant"] += classified["vacant"]
        totals["second_homes"] += classified["second_home"]
        for key in (
            "extra_dwellings",
            "extra_dwellings_without_null",
            "broad_second_homes",
            "broad_second_homes_without_null",
            "broad_main_residences",
            "broad_main_residences_without_null",
        ):
            totals[key] += classified[key]
        totals["recent_transfers"] += classified["recent_transfer"]
        totals["owner_occupied_main_residences"] += classified[
            "owner_occupied_main_residence"
        ]
        totals["owner_occupied_second_homes"] += classified[
            "owner_occupied_second_home"
        ]
        totals["owner_occupied_recent_transfers"] += classified[
            "owner_occupied_recent_transfer"
        ]
        totals["social_housing"] += classified["social_housing"]
        totals["social_housing_main_residences"] += classified[
            "social_housing_main_residence"
        ]
        totals["houses"] += classified["house"]
        totals["flats"] += classified["flat"]

        if classified["main_residence"]:
            try:
                npiece = int(row["npiece_i"])
            except (KeyError, TypeError, ValueError):
                npiece = None
            if npiece is not None:
                npiece_values.append(npiece)
                npiece_sum += npiece
                npiece_sum_sq += npiece * npiece

            dnbniv = _clean_dnbniv(row.get("dnbniv"), 80)
            if dnbniv is not None:
                dnbniv_values.append(dnbniv)
                dnbniv_sum += dnbniv
                dnbniv_sum_sq += dnbniv * dnbniv

            try:
                stoth = int(row["stoth"])
            except (KeyError, TypeError, ValueError):
                stoth = None
            if stoth is not None and stoth >= 0:
                stoth_values.append(stoth)

            try:
                jannath = int(row["jannath"])
            except (KeyError, TypeError, ValueError):
                jannath = None
            if jannath is not None and 1600 <= jannath <= vintage:
                jannath_values.append(jannath)

    totals.update(
        {
            "npiece_i_sum": npiece_sum,
            "npiece_i_sum_sq": npiece_sum_sq,
            "dnbniv_sum": dnbniv_sum,
            "dnbniv_sum_sq": dnbniv_sum_sq,
            "stoth_valid_count": len(stoth_values),
            "jannath_valid_count": len(jannath_values),
            "stoth_median": statistics.median(stoth_values) if stoth_values else None,
            "stoth_std": (
                statistics.pstdev(stoth_values) if len(stoth_values) > 1 else 0.0
                if stoth_values
                else None
            ),
            "jannath_median": (
                statistics.median(jannath_values) if jannath_values else None
            ),
            "jannath_std": (
                statistics.pstdev(jannath_values) if len(jannath_values) > 1 else 0.0
                if jannath_values
                else None
            ),
        }
    )
    return totals


def _file_signature(path: Path) -> dict[str, int | str]:
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def build_ff_cells_signature(
    vintage: int,
    config: OriginsConfig,
    input_files: Sequence[Path],
    code_version: int = 5,
) -> str:
    """Build the cache signature for one Fichiers fonciers vintage."""
    payload = {
        "version": code_version,
        "vintage": vintage,
        "config": {
            "dwelling": config.logh,
            "vacant": config.vacant_code,
            "owner": config.owner_code,
            "let": config.let_code,
            "social": config.social_code,
            "recent_transfer": config.recent_transfer[vintage],
            "jannath_min": config.jannath_min,
            "dniv_code_threshold": config.dniv_code_threshold,
            "stoth_negative_missing": config.stoth_negative_missing,
            "nbetagemax_used": config.nbetagemax_used,
            "construction_period_starts": config.construction_period_starts,
            "second_home_rescaling": config.second_home_rescaling,
            "vintage": vars(config.vintages[vintage]),
            "hybrid_vintage": (
                vars(config.vintages[2024])
                if config.vintages[vintage].second_home_source == "hybrid_2024"
                else None
            ),
        },
        "inputs": [_file_signature(path) for path in input_files],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _filosofi_200m_map(
    connection: duckdb.DuckDBPyConnection,
    archive: Path,
    temporary_directory: Path,
) -> dict[str, str]:
    """Read Filosofi 200 m commune intersections for location diagnostics."""
    with tempfile.TemporaryDirectory(
        prefix="filosofi_200m_", dir=temporary_directory
    ) as directory:
        csv_path = Path(directory) / "filosofi_200m.csv"
        with zipfile.ZipFile(archive) as zipped:
            member = next(
                name
                for name in zipped.namelist()
                if name.endswith("carreaux_200m_met.csv")
            )
            with zipped.open(member) as source, csv_path.open("wb") as target:
                shutil.copyfileobj(source, target)
        rows = connection.execute(
            """
            SELECT idcar_200m, lcog_geo
            FROM read_csv_auto(?, header=true)
            """,
            [str(csv_path)],
        ).fetchall()
    return {
        str(cell): "" if commune is None else str(commune)
        for cell, commune in rows
    }


def _filosofi_natural_ids(
    connection: duckdb.DuckDBPyConnection,
    archive: Path,
    temporary_directory: Path,
) -> NaturalCellLookup:
    """Read and index metropolitan Filosofi natural-level cell identifiers."""
    with tempfile.TemporaryDirectory(
        prefix="filosofi_natural_", dir=temporary_directory
    ) as directory:
        csv_path = Path(directory) / "filosofi_natural.csv"
        with zipfile.ZipFile(archive) as zipped:
            member = next(
                name
                for name in zipped.namelist()
                if name.endswith("carreaux_nivNaturel_met.csv")
            )
            with zipped.open(member) as source, csv_path.open("wb") as target:
                shutil.copyfileobj(source, target)
        rows = connection.execute(
            """
            SELECT DISTINCT idcar_nat
            FROM read_csv_auto(?, header=true)
            """,
            [str(csv_path)],
        ).fetchall()
    return build_natural_cell_lookup(str(row[0]) for row in rows)


def _partition_for_department(
    config: OriginsConfig,
    vintage: int,
    department: str,
) -> Path:
    pattern = config.vintages[vintage].parquet_pattern
    return Path(pattern.format(department=department))


def _quoted_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _temp_table_exists(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
) -> bool:
    return bool(
        connection.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_name = ?",
            [table_name],
        ).fetchone()[0]
    )


def _register_lookup_tables(
    connection: duckdb.DuckDBPyConnection,
    filosofi_200m: Mapping[str, str],
    natural_cell_lookup: NaturalCellLookup,
) -> None:
    if not _temp_table_exists(connection, "_filosofi_200m"):
        connection.register(
            "_filosofi_200m_input",
            pa.Table.from_pydict(
                {
                    "cell_code": list(filosofi_200m),
                    "lcog_geo": list(filosofi_200m.values()),
                }
            ),
        )
        try:
            connection.execute(
                """
                CREATE TEMP TABLE _filosofi_200m AS
                SELECT cell_code, lcog_geo FROM _filosofi_200m_input
                """
            )
        finally:
            connection.unregister("_filosofi_200m_input")

    if not _temp_table_exists(connection, "_natural_cells"):
        natural_rows = [
            {
                "natural_cell_id": code,
                "resolution_m": resolution,
                "northing_m": northing,
                "easting_m": easting,
            }
            for resolution, cells in natural_cell_lookup.items()
            for (northing, easting), code in cells.items()
        ]
        if not natural_rows:
            raise ValueError("Filosofi natural-level file contains no cells")
        connection.register(
            "_natural_cells_input",
            pa.Table.from_pylist(natural_rows),
        )
        try:
            connection.execute(
                """
                CREATE TEMP TABLE _natural_cells AS
                SELECT * FROM _natural_cells_input
                """
            )
        finally:
            connection.unregister("_natural_cells_input")


def _create_natural_cell_map(
    connection: duckdb.DuckDBPyConnection,
    partitions: Sequence[Path],
) -> None:
    paths = "[" + ", ".join(
        _sql_literal(str(path.resolve())) for path in partitions
    ) + "]"
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _ff_cell_map AS
        WITH grid_cells AS (
            SELECT DISTINCT
                CAST(floor(Y / 200) * 200 AS BIGINT) AS northing_m,
                CAST(floor(X / 200) * 200 AS BIGINT) AS easting_m
            FROM read_parquet({paths})
            WHERE X IS NOT NULL AND Y IS NOT NULL
                AND isfinite(X) AND isfinite(Y) AND X >= 0 AND Y >= 0
        ),
        matches AS (
            SELECT
                    CAST(floor(p.northing_m / 200) AS BIGINT)
                    * 100000
                    + CAST(floor(p.easting_m / 200) AS BIGINT)
                    AS cell_id,
                n.natural_cell_id
            FROM grid_cells AS p
            CROSS JOIN (
                SELECT DISTINCT resolution_m FROM _natural_cells
            ) AS resolutions
            JOIN _natural_cells AS n
              ON n.resolution_m = resolutions.resolution_m
             AND n.northing_m = floor(p.northing_m / n.resolution_m)
                * n.resolution_m
             AND n.easting_m = floor(p.easting_m / n.resolution_m)
                * n.resolution_m
        )
        SELECT cell_id,
            min(natural_cell_id) AS natural_cell_id,
            count(*) AS matching_natural_cells
        FROM matches
        GROUP BY cell_id
        """
    )
    ambiguous = connection.execute(
        """
        SELECT cell_id FROM _ff_cell_map
        WHERE matching_natural_cells > 1
        LIMIT 1
        """
    ).fetchone()
    if ambiguous is not None:
        raise ValueError(
            f"multiple natural-level cells match 200 m cell {ambiguous[0]}"
        )


def derived_departments_for_pilot(
    connection: duckdb.DuckDBPyConnection,
    pilot_department: str,
) -> set[str]:
    """Derive departments sharing natural cells reached by the pilot."""
    rows = connection.execute(
        """
        WITH cells AS (
            SELECT cell_code, lcog_geo,
                CAST(regexp_extract(
                    cell_code, 'RES200mN([0-9]+)E([0-9]+)', 1
                ) AS BIGINT) AS northing_m,
                CAST(regexp_extract(
                    cell_code, 'RES200mN([0-9]+)E([0-9]+)', 2
                ) AS BIGINT) AS easting_m
            FROM _filosofi_200m
            WHERE lcog_geo IS NOT NULL
        ),
        pilot_natural AS (
            SELECT DISTINCT natural_cells.natural_cell_id
            FROM cells
            JOIN _natural_cells AS natural_cells
              ON natural_cells.northing_m
                    = floor(cells.northing_m / natural_cells.resolution_m)
                      * natural_cells.resolution_m
             AND natural_cells.easting_m
                    = floor(cells.easting_m / natural_cells.resolution_m)
                      * natural_cells.resolution_m
            CROSS JOIN UNNEST(string_split(cells.lcog_geo, ',')) AS commune(code)
            WHERE left(trim(commune.code), length(?)) = ?
        ),
        neighbor_communes AS (
            SELECT DISTINCT trim(commune.code) AS commune_code
            FROM cells
            JOIN _natural_cells AS natural_cells
              ON natural_cells.northing_m <= cells.northing_m
             AND cells.northing_m
                    < natural_cells.northing_m + natural_cells.resolution_m
             AND natural_cells.easting_m <= cells.easting_m
             AND cells.easting_m
                    < natural_cells.easting_m + natural_cells.resolution_m
            JOIN pilot_natural
              ON pilot_natural.natural_cell_id = natural_cells.natural_cell_id
            CROSS JOIN UNNEST(string_split(cells.lcog_geo, ',')) AS commune(code)
        )
        SELECT commune_code FROM neighbor_communes
        """,
        [pilot_department, pilot_department],
    ).fetchall()
    departments = derived_departments(str(row[0]) for row in rows)
    if pilot_department not in departments:
        raise ValueError(
            f"Filosofi 200 m map does not reach pilot department "
            f"{pilot_department!r}"
        )
    return departments


def _pilot_department(path: str | Path = "config/pilot.yaml") -> str:
    with Path(path).open(encoding="utf-8") as stream:
        value = yaml.safe_load(stream)["department"]
    department = str(value).strip()
    if not department:
        raise ValueError("config/pilot.yaml has an empty department")
    return department


def build_department_ff_cells(
    connection: duckdb.DuckDBPyConnection,
    vintage: int,
    department: str,
    config: OriginsConfig,
    filosofi_200m: Mapping[str, str],
    natural_cell_lookup: NaturalCellLookup,
) -> tuple[str, dict[str, int]]:
    """Classify one department in DuckDB and return its staging table."""
    started = time.perf_counter()
    vintage_config = config.vintages[vintage]
    partition = _partition_for_department(config, vintage, department)
    if not partition.is_file():
        raise FileNotFoundError(partition)

    _register_lookup_tables(connection, filosofi_200m, natural_cell_lookup)
    if not _temp_table_exists(connection, "_ff_cell_map"):
        _create_natural_cell_map(connection, [partition])

    source = str(partition.resolve())
    available = {
        row[0]
        for row in connection.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)",
            [source],
        ).fetchall()
    }
    vintage_config = config.vintages[vintage]
    required = {
        "idcom",
        "X",
        "Y",
        "logh",
        "ccthp",
        vintage_config.second_home_column,
    }
    hybrid = vintage_config.second_home_source == "hybrid_2024"
    if hybrid:
        if vintage not in {2021, 2022}:
            raise ValueError(
                "hybrid_2024 is only available for vintages 2021 and 2022"
            )
        required.add("idlocal")
    missing = required - available
    if missing:
        raise ValueError(
            f"department {department} is missing required FF columns: "
            + ", ".join(sorted(missing))
        )

    def field(name: str, alias: str | None = None) -> str:
        output_name = alias or name
        expression = (
            f"source.{_quoted_identifier(name)}"
            if name in available
            else "NULL"
        )
        return f"{expression} AS {_quoted_identifier(output_name)}"

    fields = [
        "idlocal",
        "X",
        "Y",
        "logh",
        "ccthp",
        "catpro2",
        "npiece_i",
        "dnbniv",
        "stoth",
        "jannath",
        "loghmais",
        "loghappt",
    ]
    source_fields = [field(name) for name in fields]
    source_fields.extend(
        [
            field("idcom"),
            field(vintage_config.second_home_column, "second_home_value"),
        ]
    )
    join_sql = ""
    parameters = [source]
    if hybrid:
        later_partition = _partition_for_department(config, 2024, department)
        if not later_partition.is_file():
            raise FileNotFoundError(later_partition)
        later_source = str(later_partition.resolve())
        duplicate = connection.execute(
            "SELECT count(*) FROM (SELECT idlocal FROM read_parquet(?) "
            "WHERE idlocal IS NOT NULL GROUP BY idlocal HAVING count(*) > 1)",
            [later_source],
        ).fetchone()[0]
        if duplicate:
            raise ValueError(
                f"duplicate 2024 idlocal values in department {department}"
            )
        source_fields.append("later.rppo_rs AS rppo_rs_2024")
        join_sql = (
            "LEFT JOIN read_parquet(?) AS later "
            "ON source.idlocal = later.idlocal"
        )
        parameters.append(later_source)
    else:
        source_fields.append("NULL AS rppo_rs_2024")
    second_value = (
        "CASE WHEN rppo_rs_2024 IN ('RS', 'RPPO') THEN rppo_rs_2024 "
        "ELSE second_home_value END"
        if hybrid else _quoted_identifier("second_home_value")
    )
    original_value = _quoted_identifier("second_home_value")
    logh = _sql_literal(config.logh)
    vacant = _sql_literal(config.vacant_code)
    owner = _sql_literal(config.owner_code)
    let = _sql_literal(config.let_code)
    social = _sql_literal(config.social_code)
    second_home = _sql_literal(vintage_config.second_home_code)
    recent = _sql_literal(config.recent_transfer[vintage])
    dnbniv_threshold = config.dniv_code_threshold
    jannath_min = config.jannath_min
    stoth_valid = "TRY_CAST(stoth AS BIGINT) IS NOT NULL"
    stoth_negative_diagnostic = "FALSE"
    if config.stoth_negative_missing:
        stoth_valid += " AND TRY_CAST(stoth AS BIGINT) >= 0"
        stoth_negative_diagnostic = "TRY_CAST(stoth AS BIGINT) < 0"
    cell_code = (
        "'CRS3035RES200mN' || CAST(CAST(floor(Y / 200) * 200 AS BIGINT) AS VARCHAR)"
        " || 'E' || CAST(CAST(floor(X / 200) * 200 AS BIGINT) AS VARCHAR)"
    )
    valid_location = (
        "X IS NOT NULL AND Y IS NOT NULL AND isfinite(X) AND isfinite(Y) "
        "AND X >= 0 AND Y >= 0"
    )
    table_name = f"_ff_department_{department.lower()}"
    separator_pattern = _sql_literal(r"\s*,\s*")
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE {_quoted_identifier(table_name)} AS
        WITH source AS (
            SELECT {', '.join(source_fields)}
            FROM read_parquet(?) AS source
            {join_sql}
        ),
        located AS (
            SELECT *,
                CASE WHEN {valid_location}
                    THEN CAST(floor(Y / 200) AS BIGINT) * 100000
                        + CAST(floor(X / 200) AS BIGINT)
                END AS cell_id,
                CASE WHEN {valid_location} THEN {cell_code} END AS cell_code,
                ({valid_location}) AS valid_location
            FROM source
        ),
        classified AS (
            SELECT location.*,
                CASE WHEN logh = {logh} THEN 1 ELSE 0 END AS dwelling,
                CASE WHEN logh = {logh} AND ccthp = {vacant}
                    THEN 1 ELSE 0 END AS vacant,
                CASE WHEN logh = {logh} AND {second_value} = {second_home}
                    THEN 1 ELSE 0 END AS second_home,
                CASE WHEN logh = {logh} AND ccthp IS DISTINCT FROM {vacant}
                    AND {original_value} = {recent}
                    AND ({second_value}) IS DISTINCT FROM {second_home}
                    THEN 1 ELSE 0 END AS recent_transfer,
                CASE WHEN logh = {logh}
                    AND ccthp IS DISTINCT FROM {vacant}
                    AND {second_value} IS DISTINCT FROM {second_home}
                    THEN 1 ELSE 0 END AS main_residence,
                CASE WHEN logh = {logh}
                    AND ccthp IS DISTINCT FROM {vacant}
                    AND {second_value} IS DISTINCT FROM {second_home}
                    AND ccthp IS DISTINCT FROM {owner}
                    AND ccthp IS DISTINCT FROM {let}
                    THEN 1 ELSE 0 END AS extra_dwellings,
                CASE WHEN logh = {logh}
                    AND ccthp IS DISTINCT FROM {vacant}
                    AND {second_value} IS DISTINCT FROM {second_home}
                    AND ccthp IS DISTINCT FROM {owner}
                    AND ccthp IS DISTINCT FROM {let}
                    AND ccthp IS NOT NULL
                    THEN 1 ELSE 0 END AS extra_dwellings_without_null,
                CASE WHEN logh = {logh}
                    AND ccthp IS DISTINCT FROM {vacant}
                    AND {second_value} IS DISTINCT FROM {second_home}
                    AND ccthp = {owner}
                    THEN 1 ELSE 0 END AS owner_occupied_main_residence,
                CASE WHEN logh = {logh}
                    AND {second_value} = {second_home}
                    AND ccthp = {owner}
                    THEN 1 ELSE 0 END AS owner_occupied_second_home,
                CASE WHEN logh = {logh}
                    AND ccthp IS DISTINCT FROM {vacant}
                    AND {original_value} = {recent}
                    AND ({second_value}) IS DISTINCT FROM {second_home}
                    AND ccthp = {owner}
                    THEN 1 ELSE 0 END AS owner_occupied_recent_transfer,
                CASE WHEN logh = {logh} AND catpro2 = {social}
                    THEN 1 ELSE 0 END AS social_housing,
                CASE WHEN logh = {logh} AND catpro2 = {social}
                    AND ccthp IS DISTINCT FROM {vacant}
                    AND {second_value} IS DISTINCT FROM {second_home}
                    THEN 1 ELSE 0 END AS social_housing_main_residence,
                CASE WHEN logh = {logh} AND loghmais = 't'
                    THEN 1 ELSE 0 END AS house,
                CASE WHEN logh = {logh} AND loghappt = 't'
                    THEN 1 ELSE 0 END AS flat,
                TRY_CAST(npiece_i AS BIGINT) AS npiece_i_clean,
                CASE
                    WHEN regexp_full_match(trim(CAST(dnbniv AS VARCHAR)),
                                           '^[+-]?[0-9]+$')
                     AND TRY_CAST(trim(CAST(dnbniv AS VARCHAR)) AS BIGINT)
                        < {dnbniv_threshold}
                        THEN TRY_CAST(trim(CAST(dnbniv AS VARCHAR)) AS BIGINT)
                END AS dnbniv_clean,
                CASE
                    WHEN {stoth_valid}
                        THEN TRY_CAST(stoth AS BIGINT)
                END AS stoth_clean,
                CASE
                    WHEN TRY_CAST(jannath AS INTEGER) BETWEEN {jannath_min}
                         AND {vintage}
                        THEN TRY_CAST(jannath AS INTEGER)
                END AS jannath_clean
            FROM located AS location
        ),
        categorized AS (
            SELECT classified.*,
                second_home + extra_dwellings AS broad_second_homes,
                second_home + extra_dwellings_without_null
                    AS broad_second_homes_without_null,
                main_residence - extra_dwellings AS broad_main_residences,
                main_residence - extra_dwellings_without_null
                    AS broad_main_residences_without_null
            FROM classified
        )
        SELECT categorized.*,
            nat_cell.natural_cell_id,
            CASE WHEN categorized.idcom IS NOT NULL
                AND filosofi.lcog_geo IS NOT NULL
                AND NOT list_contains(
                    regexp_split_to_array(
                        CAST(filosofi.lcog_geo AS VARCHAR), {separator_pattern}
                    ),
                    trim(CAST(categorized.idcom AS VARCHAR))
                )
                THEN 1 ELSE 0 END AS idcom_commune_mismatch
        FROM categorized
        LEFT JOIN _ff_cell_map AS nat_cell USING (cell_id)
        LEFT JOIN _filosofi_200m AS filosofi
          ON filosofi.cell_code = categorized.cell_code
        """,
        parameters,
    )
    diagnostic_keys = (
        "premises_without_coordinates",
        "main_residences_outside_natural_cells",
        "dnbniv_code_values",
        "stoth_negative_missing",
        "jannath_below_min",
        "jannath_above_vintage",
        "idcom_commune_mismatch",
    )
    diagnostic_values = connection.execute(
        f"""
            SELECT
                count(*) FILTER (WHERE NOT valid_location),
                count(*) FILTER (WHERE dwelling = 1 AND main_residence = 1
                    AND natural_cell_id IS NULL),
                count(*) FILTER (WHERE main_residence = 1
                    AND dnbniv IS NOT NULL AND dnbniv_clean IS NULL),
                count(*) FILTER (WHERE main_residence = 1
                    AND {stoth_negative_diagnostic}),
                count(*) FILTER (WHERE main_residence = 1
                    AND TRY_CAST(jannath AS INTEGER) < {jannath_min}),
                count(*) FILTER (WHERE main_residence = 1
                    AND TRY_CAST(jannath AS INTEGER) > {vintage}),
                count(*) FILTER (WHERE dwelling = 1
                    AND idcom_commune_mismatch = 1)
            FROM {_quoted_identifier(table_name)}
            """
    ).fetchone()
    diagnostics = {
        key: int(value)
        for key, value in zip(diagnostic_keys, diagnostic_values, strict=True)
    }
    if hybrid:
        branch_counts = connection.execute(
            f"""
            SELECT count(*) FILTER (WHERE rppo_rs_2024 = 'RS'),
                count(*) FILTER (WHERE rppo_rs_2024 = 'RPPO'),
                count(*) FILTER (WHERE rppo_rs_2024 IS NULL
                    OR rppo_rs_2024 NOT IN ('RS', 'RPPO'))
            FROM {_quoted_identifier(table_name)} WHERE dwelling = 1
            """
        ).fetchone()
        diagnostics.update(dict(zip(
            ("hybrid_settled_rs", "hybrid_settled_rppo", "hybrid_fallback"),
            map(int, branch_counts), strict=True,
        )))
    LOGGER.info(
        "Fichiers fonciers vintage %s department %s classified in %.2f seconds",
        vintage,
        department,
        time.perf_counter() - started,
    )
    return table_name, diagnostics


def _covariate_fields(config: OriginsConfig, cell_count: str) -> str:
    """Return dwelling-level SQL aggregates for section 6.3."""
    first, second, third = config.construction_period_starts
    periods = {
        "av45": f"jannath_clean < {first}",
        "45_70": f"jannath_clean >= {first} AND jannath_clean < {second}",
        "70_90": f"jannath_clean >= {second} AND jannath_clean < {third}",
        "ap90": f"jannath_clean >= {third}",
        "inc": "jannath_clean IS NULL",
    }
    fields = [
        "sum(house * main_residence) AS main_residence_houses",
        "sum(flat * main_residence) AS main_residence_flats",
        "sum(house * main_residence) / nullif(sum(main_residence), 0) AS house_share",
        "sum(owner_occupied_main_residence) / nullif(sum(main_residence), 0) "
        "AS owner_share",
        "sum(second_home) / nullif(sum(dwelling), 0) AS second_home_share",
        "sum(social_housing_main_residence) / nullif(sum(main_residence), 0) "
        "AS social_share",
        f"sum(main_residence) / ({cell_count}) AS main_residences_per_200m",
    ]
    for column in ("npiece_i_clean", "dnbniv_clean"):
        name = column.removesuffix("_clean")
        for operation, suffix in (("avg", "mean"), ("stddev_pop", "std")):
            fields.append(
                f"{operation}({column}) FILTER (WHERE main_residence = 1) "
                f"AS {name}_{suffix}"
            )
    for name, condition in periods.items():
        count = f"count(*) FILTER (WHERE main_residence = 1 AND {condition})"
        fields.extend((
            f"{count} AS construction_{name}",
            f"{count} / nullif(sum(main_residence), 0) AS construction_{name}_share",
        ))
    return ",\n".join(fields)


def aggregate_staged_ff_cells(
    connection: duckdb.DuckDBPyConnection,
    staging_tables: Sequence[str],
    vintage: int,
    config: OriginsConfig | None = None,
) -> pa.Table:
    """Aggregate staged premise classifications per 200 m cell in DuckDB."""
    if not staging_tables:
        raise ValueError("at least one staged department table is required")
    if config is None:
        config = load_origins_config()
    union = " UNION ALL ".join(
        f"SELECT * FROM {_quoted_identifier(table)}" for table in staging_tables
    )
    return connection.execute(
        f"""
        SELECT ? AS vintage, cell_id,
            coalesce(natural_cell_id, '') AS natural_cell_id,
            sum(dwelling) AS dwellings,
            sum(main_residence) AS main_residences,
            sum(vacant) AS vacant,
            sum(second_home) AS second_homes,
            sum(extra_dwellings) AS extra_dwellings,
            sum(extra_dwellings_without_null)
                AS extra_dwellings_without_null,
            sum(broad_second_homes) AS broad_second_homes,
            sum(broad_second_homes_without_null)
                AS broad_second_homes_without_null,
            sum(broad_main_residences) AS broad_main_residences,
            sum(broad_main_residences_without_null)
                AS broad_main_residences_without_null,
            sum(recent_transfer) AS recent_transfers,
            sum(owner_occupied_main_residence)
                AS owner_occupied_main_residences,
            sum(owner_occupied_second_home) AS owner_occupied_second_homes,
            sum(owner_occupied_recent_transfer)
                AS owner_occupied_recent_transfers,
            sum(social_housing) AS social_housing,
            sum(social_housing_main_residence)
                AS social_housing_main_residences,
            sum(house) AS houses,
            sum(flat) AS flats,
            coalesce(sum(npiece_i_clean) FILTER (WHERE main_residence = 1), 0)
                AS npiece_i_sum,
            coalesce(sum(npiece_i_clean * npiece_i_clean)
                FILTER (WHERE main_residence = 1), 0) AS npiece_i_sum_sq,
            coalesce(sum(dnbniv_clean) FILTER (WHERE main_residence = 1), 0)
                AS dnbniv_sum,
            coalesce(sum(dnbniv_clean * dnbniv_clean)
                FILTER (WHERE main_residence = 1), 0) AS dnbniv_sum_sq,
            median(stoth_clean) FILTER (WHERE main_residence = 1)
                AS stoth_median,
            stddev_pop(stoth_clean) FILTER (WHERE main_residence = 1)
                AS stoth_std,
            count(stoth_clean) FILTER (WHERE main_residence = 1)
                AS stoth_valid_count,
            median(jannath_clean) FILTER (WHERE main_residence = 1)
                AS jannath_median,
            stddev_pop(jannath_clean) FILTER (WHERE main_residence = 1)
                AS jannath_std,
            count(jannath_clean) FILTER (WHERE main_residence = 1)
                AS jannath_valid_count,
            {_covariate_fields(config, "1.0")}
        FROM ({union}) AS staged
        WHERE valid_location AND dwelling = 1
        GROUP BY cell_id, natural_cell_id
        ORDER BY cell_id
        """,
        [vintage],
    ).to_arrow_table()


def aggregate_staged_ff_natural(
    connection: duckdb.DuckDBPyConnection,
    staging_tables: Sequence[str],
    vintage: int,
    config: OriginsConfig,
) -> pa.Table:
    """Aggregate dwellings directly at natural level for section 6.3."""
    if not staging_tables:
        raise ValueError("at least one staged department table is required")
    union = " UNION ALL ".join(
        f"SELECT * FROM {_quoted_identifier(table)}" for table in staging_tables
    )
    resolution = config.downscale.cell_resolution_m
    cell_count = (
        f"pow(CAST(regexp_extract(natural_cell_id, 'RES([0-9]+)mN', 1) "
        f"AS DOUBLE) / {resolution}, 2)"
    )
    return connection.execute(
        f"""
        SELECT ? AS vintage, natural_cell_id,
            sum(dwelling) AS dwellings, sum(main_residence) AS main_residences,
            median(stoth_clean) FILTER (WHERE main_residence = 1) AS stoth_median,
            stddev_pop(stoth_clean) FILTER (WHERE main_residence = 1) AS stoth_std,
            median(jannath_clean) FILTER (WHERE main_residence = 1) AS jannath_median,
            stddev_pop(jannath_clean) FILTER (WHERE main_residence = 1) AS jannath_std,
            {_covariate_fields(config, cell_count)}
        FROM ({union}) AS staged
        WHERE valid_location AND dwelling = 1 AND natural_cell_id IS NOT NULL
        GROUP BY natural_cell_id
        ORDER BY natural_cell_id
        """,
        [vintage],
    ).to_arrow_table()


def aggregate_staged_ff_communes(
    connection: duckdb.DuckDBPyConnection,
    staging_tables: Sequence[str],
    vintage: int,
) -> pa.Table:
    """Aggregate section-6.5 dwelling counts by FF commune code."""
    if not staging_tables:
        raise ValueError("at least one staged department table is required")
    union = " UNION ALL ".join(
        f"SELECT * FROM {_quoted_identifier(table)}" for table in staging_tables
    )
    return connection.execute(
        f"""
        SELECT ? AS vintage,
            trim(CAST(idcom AS VARCHAR)) AS commune_code,
            sum(dwelling) AS dwellings,
            sum(main_residence) AS main_residences,
            sum(vacant) AS vacant,
            sum(second_home) AS second_homes,
            sum(extra_dwellings) AS extra_dwellings,
            sum(extra_dwellings_without_null)
                AS extra_dwellings_without_null,
            sum(broad_second_homes) AS broad_second_homes,
            sum(broad_second_homes_without_null)
                AS broad_second_homes_without_null,
            sum(broad_main_residences) AS broad_main_residences,
            sum(broad_main_residences_without_null)
                AS broad_main_residences_without_null,
            sum(recent_transfer) AS recent_transfers,
            sum(owner_occupied_main_residence)
                AS owner_occupied_main_residences,
            sum(owner_occupied_second_home) AS owner_occupied_second_homes,
            sum(owner_occupied_recent_transfer)
                AS owner_occupied_recent_transfers,
            sum(social_housing_main_residence)
                AS social_housing_main_residences
        FROM ({union}) AS staged
        WHERE dwelling = 1 AND idcom IS NOT NULL
            AND trim(CAST(idcom AS VARCHAR)) <> ''
        GROUP BY commune_code
        ORDER BY commune_code
        """,
        [vintage],
    ).to_arrow_table()


def aggregate_staged_ff_extra_codes(
    connection: duckdb.DuckDBPyConnection,
    staging_tables: Sequence[str],
    residence_code_column: str,
) -> list[dict[str, int | str]]:
    """Aggregate additional dwelling counts by occupancy and residence code."""
    if not staging_tables:
        raise ValueError("at least one staged department table is required")
    if residence_code_column not in {"proba_rprs", "rppo_rs"}:
        raise ValueError(f"unsupported residence code column: {residence_code_column}")
    union = " UNION ALL ".join(
        f"SELECT * FROM {_quoted_identifier(table)}" for table in staging_tables
    )
    return (
        connection.execute(
            f"""
            WITH staged AS ({union})
            SELECT 'ccthp' AS code_type,
                coalesce(CAST(ccthp AS VARCHAR), '(null)') AS code,
                sum(extra_dwellings) AS extra_with_null,
                sum(extra_dwellings_without_null) AS extra_without_null
            FROM staged
            WHERE dwelling = 1 AND extra_dwellings = 1
            GROUP BY ccthp
            UNION ALL
            SELECT '{residence_code_column}' AS code_type,
                coalesce(CAST(second_home_value AS VARCHAR), '(null)') AS code,
                sum(extra_dwellings) AS extra_with_null,
                sum(extra_dwellings_without_null) AS extra_without_null
            FROM staged
            WHERE dwelling = 1 AND extra_dwellings = 1
            GROUP BY second_home_value
            ORDER BY code_type, code
            """
        )
        .to_arrow_table()
        .to_pylist()
    )


def build_ff_cells(
    vintage: int,
    departments: Sequence[str] | None = None,
    *,
    filosofi_200m_archive: str | Path | None = None,
    filosofi_natural_archive: str | Path | None = None,
    config_path: str | Path = "config/origins.yaml",
    pilot_config_path: str | Path = "config/pilot.yaml",
    output: str | Path | None = None,
    force: bool = False,
    second_home_source: str | None = None,
) -> dict[str, object]:
    """Build or reuse combined department 200 m dwelling cells."""
    config = load_origins_config(config_path)
    if vintage not in config.vintages:
        raise ValueError(f"unsupported origins vintage: {vintage}")
    configured_source = config.vintages[vintage].second_home_source
    if second_home_source is not None:
        if second_home_source not in {"own", "hybrid_2024"}:
            raise ValueError(f"invalid second_home_source: {second_home_source}")
        config.vintages[vintage] = replace(
            config.vintages[vintage], second_home_source=second_home_source
        )
    hybrid = config.vintages[vintage].second_home_source == "hybrid_2024"
    if hybrid and vintage not in {2021, 2022}:
        raise ValueError(
            "hybrid_2024 is only available for vintages 2021 and 2022"
        )
    if (
        not hybrid
        and configured_source == "hybrid_2024"
        and (
            output is None
            or Path(output).resolve()
            == Path(config.report.output_directory).resolve()
        )
    ):
        raise ValueError("the own comparison requires a separate output directory")

    output_directory = Path(output or config.report.output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    connection, spill = open_restricted_connection(output_directory)
    try:
        filosofi_archive = Path(
            filosofi_200m_archive or config.filosofi_200m_archive
        )
        natural_archive = Path(
            filosofi_natural_archive or config.filosofi_natural_archive
        )
        if not filosofi_archive.is_file():
            raise FileNotFoundError(filosofi_archive)
        if not natural_archive.is_file():
            raise FileNotFoundError(natural_archive)
        filosofi_map = _filosofi_200m_map(
            connection, filosofi_archive, output_directory
        )
        natural_cell_lookup = _filosofi_natural_ids(
            connection, natural_archive, output_directory
        )
        _register_lookup_tables(connection, filosofi_map, natural_cell_lookup)
        if departments is None:
            pilot_department = _pilot_department(pilot_config_path)
            resolved_departments = sorted(
                derived_departments_for_pilot(connection, pilot_department)
            )
        else:
            resolved_departments = sorted({str(value).strip() for value in departments})
        if not resolved_departments or any(not value for value in resolved_departments):
            raise ValueError("at least one valid department is required")

        input_files = [
            filosofi_archive,
            natural_archive,
            *[
                _partition_for_department(config, vintage, department)
                for department in resolved_departments
            ],
        ]
        if hybrid:
            input_files.extend(
                _partition_for_department(config, 2024, department)
                for department in resolved_departments
            )
        if any(not path.is_file() for path in input_files):
            missing = [str(path) for path in input_files if not path.is_file()]
            raise FileNotFoundError("; ".join(missing))

        output_path = output_directory / config.report.ff_cells_pattern.format(
            vintage=vintage
        )
        natural_output_path = output_directory / (
            config.report.ff_natural_pattern.format(vintage=vintage)
        )
        commune_output_path = output_directory / (
            config.report.ff_communes_pattern.format(vintage=vintage)
        )
        extra_codes_output_path = output_directory / (
            config.report.ff_extra_codes_pattern.format(vintage=vintage)
        )
        metadata_path = output_directory / config.report.metadata_pattern.format(
            vintage=vintage
        )
        signature = build_ff_cells_signature(vintage, config, input_files)

        if (
            not force
            and output_path.is_file()
            and natural_output_path.is_file()
            and commune_output_path.is_file()
            and extra_codes_output_path.is_file()
            and metadata_path.is_file()
        ):
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get("signature") == signature:
                return {
                    "output": str(output_path),
                    "natural_output": str(natural_output_path),
                    "communes_output": str(commune_output_path),
                    "extra_codes_output": str(extra_codes_output_path),
                    "cached": True,
                    "signature": signature,
                    "departments": resolved_departments,
                    "row_count": int(
                        read_parquet(connection, output_path).aggregate(
                            "count(*)"
                        ).fetchone()[0]
                    ),
                    "commune_row_count": int(
                        read_parquet(connection, commune_output_path).aggregate(
                            "count(*)"
                        ).fetchone()[0]
                    ),
                    "extra_codes_row_count": int(
                        read_parquet(connection, extra_codes_output_path).aggregate(
                            "count(*)"
                        ).fetchone()[0]
                    ),
                }

        metadata_path.unlink(missing_ok=True)
        _create_natural_cell_map(
            connection,
            [
                _partition_for_department(config, vintage, department)
                for department in resolved_departments
            ],
        )

        diagnostics = {
            "premises_without_coordinates": 0,
            "main_residences_outside_natural_cells": 0,
            "dnbniv_code_values": 0,
            "stoth_negative_missing": 0,
            "jannath_below_min": 0,
            "jannath_above_vintage": 0,
            "idcom_commune_mismatch": 0,
        }
        if hybrid:
            diagnostics.update({
                "hybrid_settled_rs": 0,
                "hybrid_settled_rppo": 0,
                "hybrid_fallback": 0,
            })
        department_diagnostics_all = {}
        staging_tables = []
        checkpoint_directory = output_directory / (
            config.report.ff_checkpoint_pattern.format(vintage=vintage)
        )
        checkpoint_directory.mkdir(parents=True, exist_ok=True)
        for department in resolved_departments:
            stage_path = checkpoint_directory / (
                config.report.ff_checkpoint_data_pattern.format(department=department)
            )
            stage_metadata_path = checkpoint_directory / (
                config.report.ff_checkpoint_metadata_pattern.format(
                    department=department
                )
            )
            stage_metadata = {}
            if not force and stage_path.is_file() and stage_metadata_path.is_file():
                stage_metadata = json.loads(
                    stage_metadata_path.read_text(encoding="utf-8")
                )
            if stage_metadata.get("signature") == signature:
                table_name = f"_ff_department_{department.lower()}"
                connection.execute(
                    f"CREATE TEMP VIEW {_quoted_identifier(table_name)} AS "
                    f"SELECT * FROM read_parquet({_sql_literal(str(stage_path))})"
                )
                department_diagnostics = stage_metadata["diagnostics"]
                LOGGER.info("Reused FF department %s checkpoint", department)
            else:
                table_name, department_diagnostics = build_department_ff_cells(
                    connection,
                    vintage,
                    department,
                    config,
                    filosofi_map,
                    natural_cell_lookup,
                )
                temporary_stage = stage_path.with_suffix(".tmp.parquet")
                write_parquet(
                    connection,
                    f"SELECT * FROM {_quoted_identifier(table_name)}",
                    temporary_stage,
                )
                temporary_stage.replace(stage_path)
                temporary_metadata = stage_metadata_path.with_suffix(".tmp.json")
                temporary_metadata.write_text(
                    json.dumps({
                        "signature": signature, "diagnostics": department_diagnostics
                    }, sort_keys=True),
                    encoding="utf-8",
                )
                temporary_metadata.replace(stage_metadata_path)
            staging_tables.append(table_name)
            department_diagnostics_all[department] = department_diagnostics
            for key, value in department_diagnostics.items():
                diagnostics[key] += value
        table = aggregate_staged_ff_cells(connection, staging_tables, vintage, config)
        natural_table = aggregate_staged_ff_natural(
            connection, staging_tables, vintage, config
        )
        commune_table = aggregate_staged_ff_communes(
            connection,
            staging_tables,
            vintage,
        )
        extra_codes = aggregate_staged_ff_extra_codes(
            connection,
            staging_tables,
            config.vintages[vintage].second_home_column,
        )
        extra_codes_table = pa.Table.from_pylist(
            extra_codes,
            schema=pa.schema(
                [
                    ("code_type", pa.string()),
                    ("code", pa.string()),
                    ("extra_with_null", pa.int64()),
                    ("extra_without_null", pa.int64()),
                ]
            ),
        )
        connection.register("_ff_cells", table)
        connection.register("_ff_natural", natural_table)
        connection.register("_ff_communes", commune_table)
        connection.register("_ff_extra_codes", extra_codes_table)
        try:
            temporary = output_path.with_suffix(".tmp.parquet")
            natural_temporary = natural_output_path.with_suffix(".tmp.parquet")
            commune_temporary = commune_output_path.with_suffix(".tmp.parquet")
            extra_codes_temporary = extra_codes_output_path.with_suffix(
                ".tmp.parquet"
            )
            write_parquet(
                connection,
                "SELECT * FROM _ff_cells",
                temporary,
            )
            write_parquet(connection, "SELECT * FROM _ff_natural", natural_temporary)
            write_parquet(
                connection,
                "SELECT * FROM _ff_communes",
                commune_temporary,
            )
            write_parquet(
                connection,
                "SELECT * FROM _ff_extra_codes",
                extra_codes_temporary,
            )
            temporary.replace(output_path)
            natural_temporary.replace(natural_output_path)
            commune_temporary.replace(commune_output_path)
            extra_codes_temporary.replace(extra_codes_output_path)
        finally:
            connection.unregister("_ff_cells")
            connection.unregister("_ff_natural")
            connection.unregister("_ff_communes")
            connection.unregister("_ff_extra_codes")

        metadata_path.with_suffix(".tmp.json").write_text(
            json.dumps(
                {
                    "signature": signature,
                    "diagnostics": diagnostics,
                    "department_diagnostics": department_diagnostics_all,
                    "second_home_source": config.vintages[vintage].second_home_source,
                    "departments": resolved_departments,
                    "commune_row_count": commune_table.num_rows,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        metadata_path.with_suffix(".tmp.json").replace(metadata_path)
        return {
            "output": str(output_path),
            "natural_output": str(natural_output_path),
            "communes_output": str(commune_output_path),
            "extra_codes_output": str(extra_codes_output_path),
            "cached": False,
            "signature": signature,
            "departments": resolved_departments,
            "row_count": table.num_rows,
            "commune_row_count": commune_table.num_rows,
            "extra_codes_row_count": extra_codes_table.num_rows,
            "diagnostics": diagnostics,
        }
    finally:
        connection.close()
        spill.cleanup()


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for building one FF vintage."""
    arguments = list(argv) if argv is not None else sys.argv[1:]
    if arguments and arguments[0] == "report":
        from landgrid.origins.report import main as report_main

        return report_main(arguments[1:])

    parser = argparse.ArgumentParser(
        description=(
            "Build step-3 dwelling cells; use the report command for "
            "commune validation"
        )
    )
    parser.add_argument("--vintage", type=int, required=True)
    parser.add_argument("--department", action="append")
    parser.add_argument(
        "--filosofi-200m",
        type=Path,
    )
    parser.add_argument("--filosofi-natural", type=Path)
    parser.add_argument("--config", type=Path, default=Path("config/origins.yaml"))
    parser.add_argument(
        "--output",
        type=Path,
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--second-home-source", choices=("own", "hybrid_2024"))
    args = parser.parse_args(arguments)
    logging.basicConfig(level=logging.INFO)
    from landgrid.origins.job import logged_job

    config = load_origins_config(args.config)
    threshold = config.report.count_suppression_threshold
    with logged_job(
        Path(config.jobs.log_directory),
        config.jobs.ff_task_pattern.format(vintage=args.vintage),
        [
            str(args.filosofi_200m or config.filosofi_200m_archive),
            str(args.filosofi_natural or config.filosofi_natural_archive),
            config.vintages[args.vintage].parquet_pattern,
        ],
        threshold,
    ) as job:
        result = build_ff_cells(
            args.vintage,
            args.department,
            filosofi_200m_archive=args.filosofi_200m,
            filosofi_natural_archive=args.filosofi_natural,
            config_path=args.config,
            output=args.output,
            force=args.force,
            second_home_source=args.second_home_source,
        )
        job.outputs.extend(
            str(result[name]) for name in (
                "output", "natural_output", "communes_output", "extra_codes_output"
            )
        )
        for key in ("row_count", "commune_row_count", "extra_codes_row_count"):
            job.counts[key] = int(result[key])
    displayed = dict(result)
    for key in ("row_count", "commune_row_count", "extra_codes_row_count"):
        value = displayed.get(key)
        if isinstance(value, int) and value < threshold:
            displayed[key] = f"<{threshold}"
    diagnostics = displayed.get("diagnostics")
    if isinstance(diagnostics, dict):
        displayed["diagnostics"] = {
            key: f"<{threshold}" if value < threshold else value
            for key, value in diagnostics.items()
        }
    print(json.dumps(displayed, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
