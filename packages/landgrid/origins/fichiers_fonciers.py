"""Fichiers fonciers dwelling counts for section 6."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import tempfile
import zipfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import yaml
from common.duckdb_io import open_connection, read_parquet, write_parquet
from common.grid import cell_id, inspire_code

from landgrid.origins.filosofi import (
    NaturalCellLookup,
    build_natural_cell_lookup,
    natural_cell_for_200m_cell,
)


@dataclass(frozen=True)
class VintageConfig:
    parquet_pattern: str
    second_home_column: str
    second_home_code: str


@dataclass(frozen=True)
class OriginsConfig:
    filosofi_200m_archive: str
    filosofi_natural_archive: str
    vintages: dict[int, VintageConfig]
    logh: str
    vacant_code: str
    owner_code: str
    social_code: str
    recent_transfer: dict[int, str]
    jannath_min: int
    dniv_code_threshold: int
    stoth_negative_missing: bool
    nbetagemax_used: bool
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
        )
        for vintage, value in raw["vintages"].items()
    }
    return OriginsConfig(
        filosofi_200m_archive=raw["filosofi"]["200m_archive"],
        filosofi_natural_archive=raw["filosofi"]["natural_archive"],
        vintages=vintages,
        logh=raw["dwelling"]["logh"],
        vacant_code=raw["vacant"]["ccthp"],
        owner_code=raw["owner_occupied"]["ccthp"],
        social_code=raw["social_housing"]["catpro2"],
        recent_transfer={
            int(vintage): code for vintage, code in raw["recent_transfer"].items()
        },
        jannath_min=int(raw["cleaning"]["jannath_min"]),
        dniv_code_threshold=int(raw["cleaning"]["dniv_code_threshold"]),
        stoth_negative_missing=bool(raw["cleaning"]["stoth_negative_missing"]),
        nbetagemax_used=bool(raw["cleaning"]["nbetagemax_used"]),
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
    social_code: str = "F1",
) -> dict[str, int]:
    """Classify one Fichiers fonciers dwelling row (section 6.3)."""
    is_dwelling = row.get("logh") == logh
    is_vacant = is_dwelling and row.get("ccthp") == vacant_code
    second_value = row.get(second_home_column)
    is_second_home = is_dwelling and second_value == second_home_code
    is_recent_transfer = is_dwelling and second_value == recent_transfer_code
    is_main = is_dwelling and not is_vacant and not is_second_home
    is_owner = is_main and row.get("ccthp") == owner_code
    is_social = is_dwelling and row.get("catpro2") == social_code
    is_social_main = is_social and is_main
    house = is_dwelling and row.get("loghmais") == "t"
    flat = is_dwelling and row.get("loghappt") == "t"
    return {
        "dwelling": int(is_dwelling),
        "vacant": int(is_vacant),
        "second_home": int(is_second_home),
        "main_residence": int(is_main),
        "recent_transfer": int(is_recent_transfer),
        "owner_occupied_main_residence": int(is_owner),
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
    social_code: str = "F1",
) -> dict[str, int | float | None]:
    """Aggregate a synthetic list of premises into one 200 m cell summary."""
    totals = {
        "dwellings": 0,
        "main_residences": 0,
        "vacant": 0,
        "second_homes": 0,
        "recent_transfers": 0,
        "owner_occupied_main_residences": 0,
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
            social_code=social_code,
        )
        if not classified["dwelling"]:
            continue
        totals["dwellings"] += 1
        totals["main_residences"] += classified["main_residence"]
        totals["vacant"] += classified["vacant"]
        totals["second_homes"] += classified["second_home"]
        totals["recent_transfers"] += classified["recent_transfer"]
        totals["owner_occupied_main_residences"] += classified[
            "owner_occupied_main_residence"
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
    code_version: int = 2,
) -> str:
    """Build the cache signature for one Fichiers fonciers vintage."""
    payload = {
        "version": code_version,
        "vintage": vintage,
        "config": {
            "dwelling": config.logh,
            "vacant": config.vacant_code,
            "owner": config.owner_code,
            "social": config.social_code,
            "recent_transfer": config.recent_transfer[vintage],
            "jannath_min": config.jannath_min,
            "dniv_code_threshold": config.dniv_code_threshold,
            "stoth_negative_missing": config.stoth_negative_missing,
            "nbetagemax_used": config.nbetagemax_used,
            "second_home_rescaling": config.second_home_rescaling,
            "vintage": vars(config.vintages[vintage]),
        },
        "inputs": [_file_signature(path) for path in input_files],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()


@dataclass
class _CellAccumulator:
    natural_cell_id: str
    dwellings: int = 0
    main_residences: int = 0
    vacant: int = 0
    second_homes: int = 0
    recent_transfers: int = 0
    owner_occupied_main_residences: int = 0
    social_housing: int = 0
    social_housing_main_residences: int = 0
    houses: int = 0
    flats: int = 0
    npiece_i_values: list[int] | None = None
    dnbniv_values: list[int] | None = None
    stoth_values: list[int] | None = None
    jannath_values: list[int] | None = None

    def __post_init__(self) -> None:
        self.npiece_i_values = []
        self.dnbniv_values = []
        self.stoth_values = []
        self.jannath_values = []


def _filosofi_200m_map(
    connection: duckdb.DuckDBPyConnection,
    archive: Path,
) -> dict[str, str]:
    """Read Filosofi 200 m commune intersections for location diagnostics."""
    with tempfile.TemporaryDirectory(prefix="filosofi_200m_") as directory:
        csv_path = Path(directory) / "filosofi_200m.csv"
        with zipfile.ZipFile(archive) as zipped:
            member = next(
                name
                for name in zipped.namelist()
                if name.endswith("carreaux_200m_met.csv")
            )
            with zipped.open(member) as source, csv_path.open("wb") as target:
                target.write(source.read())
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
) -> NaturalCellLookup:
    """Read and index metropolitan Filosofi natural-level cell identifiers."""
    with tempfile.TemporaryDirectory(prefix="filosofi_natural_") as directory:
        csv_path = Path(directory) / "filosofi_natural.csv"
        with zipfile.ZipFile(archive) as zipped:
            member = next(
                name
                for name in zipped.namelist()
                if name.endswith("carreaux_nivNaturel_met.csv")
            )
            with zipped.open(member) as source, csv_path.open("wb") as target:
                target.write(source.read())
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


def _clean_integer(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_department_ff_cells(
    connection: duckdb.DuckDBPyConnection,
    vintage: int,
    department: str,
    config: OriginsConfig,
    filosofi_200m: Mapping[str, str],
    natural_cell_lookup: NaturalCellLookup,
) -> tuple[dict[int, _CellAccumulator], dict[str, int]]:
    """Build synthetic 200 m dwelling aggregates for one department."""
    vintage_config = config.vintages[vintage]
    partition = _partition_for_department(config, vintage, department)
    if not partition.is_file():
        raise FileNotFoundError(partition)

    columns = [
        "idlocal",
        "idcom",
        "X",
        "Y",
        "logh",
        "ccthp",
        vintage_config.second_home_column,
        "catpro2",
        "npiece_i",
        "dnbniv",
        "stoth",
        "jannath",
        "loghmais",
        "loghappt",
    ]
    source = str(partition.resolve()).replace("'", "''")
    available = {
        row[0]
        for row in connection.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{source}')"
        ).fetchall()
    }
    columns = [column for column in columns if column in available]
    relation = connection.execute(
        f"SELECT {', '.join(columns)} FROM read_parquet('{source}')"
    )
    names = [description[0] for description in relation.description]

    cells: dict[int, _CellAccumulator] = {}
    diagnostics = {
        "premises_without_coordinates": 0,
        "main_residences_outside_natural_cells": 0,
        "dnbniv_code_values": 0,
        "stoth_negative_missing": 0,
        "jannath_below_min": 0,
        "jannath_above_vintage": 0,
        "idcom_commune_mismatch": 0,
    }
    recent_code = config.recent_transfer[vintage]

    for batch in relation.fetch_record_batch(rows_per_batch=100_000):
        for row in batch.to_pylist():
            dwelling_row = dict(zip(names, (row[name] for name in names), strict=True))
            if dwelling_row["X"] is None or dwelling_row["Y"] is None:
                diagnostics["premises_without_coordinates"] += 1
                continue
            try:
                cell_id_value = coordinate_to_200m_cell(
                    float(dwelling_row["X"]),
                    float(dwelling_row["Y"]),
                )
            except (TypeError, ValueError):
                diagnostics["premises_without_coordinates"] += 1
                continue

            easting = float(dwelling_row["X"])
            northing = float(dwelling_row["Y"])
            inspire = inspire_code(northing, easting, 200)
            natural_id = natural_cell_for_200m_cell(inspire, natural_cell_lookup) or ""
            commune_list = filosofi_200m.get(inspire, "")

            idcom = dwelling_row.get("idcom")
            if idcom is not None and commune_list:
                commune_codes = {code.strip() for code in commune_list.split(",")}
                if str(idcom).strip() not in commune_codes:
                    diagnostics["idcom_commune_mismatch"] += 1

            classified = classify_dwelling(
                dwelling_row,
                vintage_config.second_home_column,
                vintage_config.second_home_code,
                recent_code,
                logh=config.logh,
                vacant_code=config.vacant_code,
                owner_code=config.owner_code,
                social_code=config.social_code,
            )
            if not classified["dwelling"]:
                continue
            if classified["main_residence"] and not natural_id:
                diagnostics["main_residences_outside_natural_cells"] += 1

            accumulator = cells.setdefault(
                cell_id_value,
                _CellAccumulator(natural_cell_id=natural_id),
            )
            accumulator.dwellings += classified["dwelling"]
            accumulator.main_residences += classified["main_residence"]
            accumulator.vacant += classified["vacant"]
            accumulator.second_homes += classified["second_home"]
            accumulator.recent_transfers += classified["recent_transfer"]
            accumulator.owner_occupied_main_residences += classified[
                "owner_occupied_main_residence"
            ]
            accumulator.social_housing += classified["social_housing"]
            accumulator.social_housing_main_residences += classified[
                "social_housing_main_residence"
            ]
            accumulator.houses += classified["house"]
            accumulator.flats += classified["flat"]

            if classified["main_residence"]:
                npiece = _clean_integer(dwelling_row.get("npiece_i"))
                if npiece is not None:
                    accumulator.npiece_i_values.append(npiece)

                dnbniv = _clean_dnbniv(
                    dwelling_row.get("dnbniv"),
                    config.dniv_code_threshold,
                )
                if dnbniv is not None:
                    accumulator.dnbniv_values.append(dnbniv)
                elif dwelling_row.get("dnbniv") is not None:
                    diagnostics["dnbniv_code_values"] += 1

                stoth = _clean_integer(dwelling_row.get("stoth"))
                if stoth is not None:
                    if stoth < 0:
                        diagnostics["stoth_negative_missing"] += 1
                    else:
                        accumulator.stoth_values.append(stoth)

                jannath = _clean_integer(dwelling_row.get("jannath"))
                if jannath is not None:
                    if jannath < config.jannath_min:
                        diagnostics["jannath_below_min"] += 1
                    elif jannath > vintage:
                        diagnostics["jannath_above_vintage"] += 1
                    else:
                        accumulator.jannath_values.append(jannath)

    return cells, diagnostics


def _accumulator_output_row(
    vintage: int,
    cell: int,
    accumulator: _CellAccumulator,
) -> dict[str, object]:
    npiece_values = accumulator.npiece_i_values or []
    dnbniv_values = accumulator.dnbniv_values or []
    stoth_values = accumulator.stoth_values or []
    jannath_values = accumulator.jannath_values or []
    return {
        "vintage": vintage,
        "cell_id": cell,
        "natural_cell_id": accumulator.natural_cell_id,
        "dwellings": accumulator.dwellings,
        "main_residences": accumulator.main_residences,
        "vacant": accumulator.vacant,
        "second_homes": accumulator.second_homes,
        "recent_transfers": accumulator.recent_transfers,
        "owner_occupied_main_residences": (
            accumulator.owner_occupied_main_residences
        ),
        "social_housing": accumulator.social_housing,
        "social_housing_main_residences": (
            accumulator.social_housing_main_residences
        ),
        "houses": accumulator.houses,
        "flats": accumulator.flats,
        "npiece_i_sum": sum(npiece_values),
        "npiece_i_sum_sq": sum(value * value for value in npiece_values),
        "dnbniv_sum": sum(dnbniv_values),
        "dnbniv_sum_sq": sum(value * value for value in dnbniv_values),
        "stoth_median": statistics.median(stoth_values) if stoth_values else None,
        "stoth_std": (
            statistics.pstdev(stoth_values) if len(stoth_values) > 1 else 0.0
            if stoth_values
            else None
        ),
        "stoth_valid_count": len(stoth_values),
        "jannath_median": (
            statistics.median(jannath_values) if jannath_values else None
        ),
        "jannath_std": (
            statistics.pstdev(jannath_values) if len(jannath_values) > 1 else 0.0
            if jannath_values
            else None
        ),
        "jannath_valid_count": len(jannath_values),
    }


def build_ff_cells(
    vintage: int,
    departments: Sequence[str],
    *,
    filosofi_200m_archive: str | Path | None = None,
    filosofi_natural_archive: str | Path | None = None,
    config_path: str | Path = "config/origins.yaml",
    output: str | Path = "data/interim/landgrid",
    force: bool = False,
) -> dict[str, object]:
    """Build or reuse combined department 200 m dwelling cells."""
    config = load_origins_config(config_path)
    if vintage not in config.vintages:
        raise ValueError(f"unsupported origins vintage: {vintage}")

    connection = open_connection()
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
        filosofi_map = _filosofi_200m_map(connection, filosofi_archive)
        natural_cell_lookup = _filosofi_natural_ids(connection, natural_archive)

        input_files = [
            filosofi_archive,
            natural_archive,
            *[
                _partition_for_department(config, vintage, department)
                for department in departments
            ],
        ]
        if any(not path.is_file() for path in input_files):
            missing = [str(path) for path in input_files if not path.is_file()]
            raise FileNotFoundError("; ".join(missing))

        output_directory = Path(output)
        output_directory.mkdir(parents=True, exist_ok=True)
        output_path = output_directory / f"ff_cells_{vintage}.parquet"
        metadata_path = output_directory / f"ff_cells_{vintage}.json"
        signature = build_ff_cells_signature(vintage, config, input_files)

        if not force and output_path.is_file() and metadata_path.is_file():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get("signature") == signature:
                return {
                    "output": str(output_path),
                    "cached": True,
                    "signature": signature,
                    "row_count": int(
                        read_parquet(connection, output_path).aggregate(
                            "count(*)"
                        ).fetchone()[0]
                    ),
                }

        combined: dict[int, _CellAccumulator] = {}
        diagnostics = {
            "premises_without_coordinates": 0,
            "main_residences_outside_natural_cells": 0,
            "dnbniv_code_values": 0,
            "stoth_negative_missing": 0,
            "jannath_below_min": 0,
            "jannath_above_vintage": 0,
            "idcom_commune_mismatch": 0,
        }
        for department in departments:
            department_cells, department_diagnostics = build_department_ff_cells(
                connection,
                vintage,
                department,
                config,
                filosofi_map,
                natural_cell_lookup,
            )
            for key, value in department_diagnostics.items():
                diagnostics[key] += value
            for cell, accumulator in department_cells.items():
                target = combined.setdefault(
                    cell,
                    _CellAccumulator(
                        natural_cell_id=accumulator.natural_cell_id,
                    ),
                )
                target.dwellings += accumulator.dwellings
                target.main_residences += accumulator.main_residences
                target.vacant += accumulator.vacant
                target.second_homes += accumulator.second_homes
                target.recent_transfers += accumulator.recent_transfers
                target.owner_occupied_main_residences += (
                    accumulator.owner_occupied_main_residences
                )
                target.social_housing += accumulator.social_housing
                target.social_housing_main_residences += (
                    accumulator.social_housing_main_residences
                )
                target.houses += accumulator.houses
                target.flats += accumulator.flats
                target.npiece_i_values.extend(
                    accumulator.npiece_i_values or []
                )
                target.dnbniv_values.extend(accumulator.dnbniv_values or [])
                target.stoth_values.extend(accumulator.stoth_values or [])
                target.jannath_values.extend(accumulator.jannath_values or [])

        rows = [
            _accumulator_output_row(vintage, cell, accumulator)
            for cell, accumulator in sorted(combined.items())
        ]
        table = pa.Table.from_pylist(rows)
        connection.register("_ff_cells", table)
        try:
            temporary = output_path.with_suffix(".tmp.parquet")
            write_parquet(
                connection,
                "SELECT * FROM _ff_cells",
                temporary,
            )
            temporary.replace(output_path)
        finally:
            connection.unregister("_ff_cells")

        metadata_path.with_suffix(".tmp.json").write_text(
            json.dumps(
                {"signature": signature, "diagnostics": diagnostics},
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        metadata_path.with_suffix(".tmp.json").replace(metadata_path)
        return {
            "output": str(output_path),
            "cached": False,
            "signature": signature,
            "row_count": len(rows),
            "diagnostics": diagnostics,
        }
    finally:
        connection.close()


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for building one FF vintage."""
    parser = argparse.ArgumentParser(description="Build step-3 dwelling cells")
    parser.add_argument("--vintage", type=int, required=True)
    parser.add_argument("--department", action="append", required=True)
    parser.add_argument(
        "--filosofi-200m",
        type=Path,
    )
    parser.add_argument("--filosofi-natural", type=Path)
    parser.add_argument("--config", type=Path, default=Path("config/origins.yaml"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/interim/landgrid"),
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    result = build_ff_cells(
        args.vintage,
        args.department,
        filosofi_200m_archive=args.filosofi_200m,
        filosofi_natural_archive=args.filosofi_natural,
        config_path=args.config,
        output=args.output,
        force=args.force,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
