"""Temporal census growth helpers for the approved section-6.3 exception."""

from __future__ import annotations

import math
import posixpath
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import duckdb

from landgrid.origins.fichiers_fonciers import _quoted_identifier


def projected_growth_factor(
    start_value: float,
    end_value: float,
    *,
    observed_years: float,
    projected_years: float,
) -> float:
    """Project a census growth factor across years using geometric growth."""
    values = (start_value, end_value, observed_years, projected_years)
    if (
        not all(math.isfinite(value) for value in values)
        or start_value <= 0
        or end_value < 0
        or observed_years <= 0
        or projected_years <= 0
    ):
        raise ValueError("invalid growth inputs")
    if end_value == 0:
        return 0.0
    exponent = projected_years / observed_years
    factor = math.exp((math.log(end_value) - math.log(start_value)) * exponent)
    if not math.isfinite(factor) or factor <= 0:
        raise ValueError("projected growth factor is not finite and positive")
    return factor


def rescale_age_margins(
    age_margins: Mapping[str, float],
    *,
    individual_total: float,
) -> tuple[dict[str, float], float]:
    """Rescale census age margins to grown individuals before age IPF (6.3)."""
    if (
        not math.isfinite(individual_total)
        or individual_total < 0
        or not age_margins
        or any(
            not name or not math.isfinite(value) or value < 0
            for name, value in age_margins.items()
        )
    ):
        raise ValueError("invalid age margin inputs")
    age_total = math.fsum(age_margins.values())
    if age_total == 0:
        if individual_total == 0:
            return dict(age_margins), 1.0
        raise ValueError("positive individuals have no age margin support")
    adjustment = individual_total / age_total
    return (
        {name: value * adjustment for name, value in age_margins.items()},
        adjustment,
    )


def derive_age_measures(
    measures: Mapping[str, float | None],
) -> dict[str, float | None]:
    """Derive the approved census age bands from their published components."""
    derived: dict[str, float | None] = {}
    direct = {
        "age_6_10": "age_6_10",
        "age_18_24": "age_18_24",
        "age_25_39": "age_25_39",
        "age_40_54": "age_40_54",
        "age_55_64": "age_55_64",
        "age_65_79": "age_65_79",
        "age_80p": "age_80p",
    }
    for output, source in direct.items():
        derived[output] = measures.get(source)
    under_15 = measures.get("under_15")
    age_6_10 = measures.get("age_6_10")
    age_11_14 = measures.get("age_11_14")
    age_15_17 = measures.get("age_15_17")
    derived["age_0_5"] = (
        under_15 - age_6_10 - age_11_14
        if under_15 is not None and age_6_10 is not None
        and age_11_14 is not None
        else None
    )
    derived["age_11_17"] = (
        age_11_14 + age_15_17
        if age_11_14 is not None and age_15_17 is not None
        else None
    )
    return derived


def calculate_growth_factors(
    base_measures: Mapping[str, float | None],
    target_measures: Mapping[str, float | None],
    *,
    variables: Sequence[str],
    measure_by_variable: Mapping[str, str | None],
    denominator_by_variable: Mapping[str, str],
    observed_years: float,
    projected_years: float,
    fallback_individual_growth: float | None = None,
    fallback_missing_to_individual: bool = False,
) -> tuple[dict[str, float], dict[str, int]]:
    """Calculate commune growth factors, with approved age and FF fallbacks."""
    variables = tuple(variables)
    if (
        not variables
        or len(variables) != len(set(variables))
        or set(variables) - set(measure_by_variable)
        or set(variables) - set(denominator_by_variable)
    ):
        raise ValueError("invalid census growth variable mapping")
    if fallback_individual_growth is not None and (
        not math.isfinite(fallback_individual_growth)
        or fallback_individual_growth < 0
    ):
        raise ValueError("invalid FF individual growth fallback")

    def measure_factor(name: str) -> float | None:
        start = base_measures.get(name)
        end = target_measures.get(name)
        if (
            start is None or end is None
            or not math.isfinite(start) or not math.isfinite(end)
            or start <= 0 or end < 0
        ):
            return None
        return projected_growth_factor(
            start, end, observed_years=observed_years,
            projected_years=projected_years,
        )

    individual_factor = measure_factor("individuals")
    fallbacks: dict[str, int] = {}
    if individual_factor is None:
        if fallback_individual_growth is None:
            raise ValueError("no valid individual census growth or FF fallback")
        individual_factor = fallback_individual_growth
        fallbacks["individual_from_ff"] = 1
    factors: dict[str, float] = {}
    age_measures = {
        "age_0_5", "age_6_10", "age_11_17", "age_18_24",
        "age_25_39", "age_40_54", "age_55_64", "age_65_79", "age_80p",
    }
    for variable in variables:
        measure = measure_by_variable[variable]
        if measure is None:
            denominator = denominator_by_variable[variable]
            factor = (
                individual_factor if denominator == "individuals"
                else measure_factor(denominator)
            )
            if factor is None:
                raise ValueError(
                    f"no valid census growth for denominator {denominator}"
                )
            factors[variable] = factor
            fallbacks["denominator"] = fallbacks.get("denominator", 0) + 1
        elif measure == "individuals":
            factors[variable] = individual_factor
        else:
            factor = measure_factor(measure)
            if factor is None and (
                measure in age_measures or fallback_missing_to_individual
            ):
                factor = individual_factor
                fallback_name = (
                    "age_to_individual" if measure in age_measures
                    else "measure_to_individual"
                )
                fallbacks[fallback_name] = fallbacks.get(fallback_name, 0) + 1
            if factor is None:
                raise ValueError(f"no valid census growth for measure {measure}")
            factors[variable] = factor
    return factors, fallbacks


def load_cog_passage_edges(
    path: str | Path,
    *,
    source_year: int,
    target_year: int,
) -> tuple[tuple[str, str], ...]:
    """Read year-specific commune passage edges from the INSEE COG workbook."""
    archive_path = Path(path)
    if not archive_path.is_file():
        raise FileNotFoundError(archive_path)
    if archive_path.suffix.casefold() == ".xlsx":
        workbook_bytes = archive_path.read_bytes()
    else:
        with zipfile.ZipFile(archive_path) as outer:
            workbooks = [
                member for member in outer.namelist()
                if member.casefold().endswith(".xlsx")
            ]
            if len(workbooks) != 1:
                raise ValueError("COG archive must contain exactly one workbook")
            workbook_bytes = outer.read(workbooks[0])

    namespace = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "office_rel": (
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        ),
        "package_rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    }
    with zipfile.ZipFile(BytesIO(workbook_bytes)) as workbook:
        workbook_xml = ET.fromstring(workbook.read("xl/workbook.xml"))
        relationships_xml = ET.fromstring(
            workbook.read("xl/_rels/workbook.xml.rels")
        )
        relationships = {
            relation.attrib["Id"]: relation.attrib["Target"]
            for relation in relationships_xml.findall(
                "package_rel:Relationship", namespace
            )
        }
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            with workbook.open("xl/sharedStrings.xml") as source:
                for _, item in ET.iterparse(source, events=("end",)):
                    if item.tag.endswith("}si"):
                        shared_strings.append("".join(
                            part.text or ""
                            for part in item.findall(".//main:t", namespace)
                        ))
                        item.clear()

        def cell_text(cell: ET.Element) -> str:
            value = cell.find("main:v", namespace)
            if cell.attrib.get("t") == "inlineStr":
                return "".join(
                    part.text or ""
                    for part in cell.findall(".//main:t", namespace)
                )
            if value is None or value.text is None:
                return ""
            if cell.attrib.get("t") == "s":
                return shared_strings[int(value.text)]
            return value.text

        def column_index(reference: str) -> int:
            letters = "".join(
                character for character in reference if character.isalpha()
            )
            result = 0
            for letter in letters.upper():
                result = result * 26 + ord(letter) - ord("A") + 1
            return result

        sheet = next(
            (
                item for item in workbook_xml.findall(
                    "main:sheets/main:sheet", namespace
                )
                if item.attrib.get("name") == "COM"
            ),
            None,
        )
        if sheet is None:
            raise ValueError("COG workbook lacks the COM passage sheet")
        relation_id = sheet.attrib[f"{{{namespace['office_rel']}}}id"]
        target = relationships[relation_id]
        sheet_path = (
            target.lstrip("/")
            if target.startswith("/")
            else posixpath.normpath(posixpath.join("xl", target))
        )
        source_column_name = f"CODGEO_{source_year}"
        target_column_name = f"CODGEO_{target_year}"
        required_headers = {"NIVGEO", source_column_name, target_column_name}
        header_columns: dict[int, str] | None = None
        edges: set[tuple[str, str]] = set()
        found_headers = False
        with workbook.open(sheet_path) as source:
            for _, row in ET.iterparse(source, events=("end",)):
                if not row.tag.endswith("}row"):
                    continue
                values = {
                    column_index(cell.attrib["r"]): cell_text(cell).strip()
                    for cell in row.findall("main:c", namespace)
                }
                if header_columns is None:
                    if required_headers.issubset(values.values()):
                        header_columns = {
                            index: value for index, value in values.items()
                            if value in required_headers
                        }
                        found_headers = True
                else:
                    header_indices = {
                        name: index for index, name in header_columns.items()
                    }
                    if values.get(header_indices["NIVGEO"]) == "COM":
                        start = values.get(header_indices[source_column_name], "")
                        end = values.get(header_indices[target_column_name], "")
                        if start and end:
                            edges.add((start, end))
                row.clear()
        if not found_headers:
            raise ValueError(
                f"COG workbook lacks headers for {source_year} and {target_year}"
            )
        if not edges:
            raise ValueError("COG workbook contains no commune passage rows")
        return tuple(sorted(edges))


@dataclass(frozen=True)
class StableGrowthUnits:
    """Connected commune groups used as stable temporal growth units."""

    code_to_unit: dict[str, str]
    source_codes_by_unit: dict[str, tuple[str, ...]]
    target_codes_by_unit: dict[str, tuple[str, ...]]
    combined_units: frozenset[str]


def build_stable_growth_units(
    edges: Sequence[tuple[str, str]],
) -> StableGrowthUnits:
    """Connect COG merge/split chains without dividing commune totals."""
    parents: dict[str, str] = {}

    def find(code: str) -> str:
        parents.setdefault(code, code)
        if parents[code] != code:
            parents[code] = find(parents[code])
        return parents[code]

    def union(first: str, second: str) -> None:
        first_root = find(first)
        second_root = find(second)
        if first_root != second_root:
            parents[second_root] = first_root

    unique_edges = set(edges)
    if not unique_edges or any(
        not source.strip() or not target.strip()
        for source, target in unique_edges
    ):
        raise ValueError("COG passage edges must contain commune codes")
    for source, target in unique_edges:
        union(source.strip(), target.strip())

    sources_by_root: dict[str, set[str]] = {}
    targets_by_root: dict[str, set[str]] = {}
    for source, target in unique_edges:
        root = find(source.strip())
        sources_by_root.setdefault(root, set()).add(source.strip())
        targets_by_root.setdefault(root, set()).add(target.strip())

    code_to_unit: dict[str, str] = {}
    source_codes_by_unit: dict[str, tuple[str, ...]] = {}
    target_codes_by_unit: dict[str, tuple[str, ...]] = {}
    combined_units: set[str] = set()
    members_by_root: dict[str, set[str]] = {}
    for code in parents:
        members_by_root.setdefault(find(code), set()).add(code)
    for root, members in members_by_root.items():
        sources = tuple(sorted(sources_by_root.get(root, set())))
        targets = tuple(sorted(targets_by_root.get(root, set())))
        unit = targets[0] if len(targets) == 1 else "|".join(targets)
        if len(sources) > 1 or len(targets) > 1:
            combined_units.add(unit)
        source_codes_by_unit[unit] = sources
        target_codes_by_unit[unit] = targets
        for code in members:
            code_to_unit[code] = unit
    return StableGrowthUnits(
        code_to_unit=code_to_unit,
        source_codes_by_unit=source_codes_by_unit,
        target_codes_by_unit=target_codes_by_unit,
        combined_units=frozenset(combined_units),
    )


def build_unit_growth_factors(
    connection: duckdb.DuckDBPyConnection,
    *,
    source_relation: str,
    target_relation: str,
    code_units_relation: str,
    variables: Sequence[str],
    measure_by_variable: Mapping[str, str | None],
    denominator_by_variable: Mapping[str, str],
    observed_years: float,
    projected_years: float,
    fallback_relation: str | None = None,
    fallback_missing_to_individual: bool = False,
) -> dict[str, int]:
    """Aggregate census measures to stable units before computing growth."""
    variables = tuple(variables)
    if (
        not variables
        or len(variables) != len(set(variables))
        or set(variables) - set(measure_by_variable)
        or set(variables) - set(denominator_by_variable)
        or observed_years <= 0
        or projected_years <= 0
        or not math.isfinite(observed_years)
        or not math.isfinite(projected_years)
    ):
        raise ValueError("invalid unit growth inputs")
    measures = {
        measure
        for variable in variables
        for measure in (
            measure_by_variable[variable],
            denominator_by_variable[variable],
        )
        if measure is not None
    } | {"individuals"}
    quoted_source = _quoted_identifier(source_relation)
    quoted_target = _quoted_identifier(target_relation)
    quoted_mapping = _quoted_identifier(code_units_relation)
    for relation, required in (
        (quoted_source, {"commune_code", *measures}),
        (quoted_target, {"commune_code", *measures}),
        (quoted_mapping, {"commune_code", "unit_id"}),
    ):
        available = {
            str(row[0])
            for row in connection.execute(
                f"DESCRIBE SELECT * FROM {relation}"
            ).fetchall()
        }
        missing = required - available
        if missing:
            raise ValueError(
                f"growth input {relation} lacks columns: {', '.join(sorted(missing))}"
            )
    duplicate_mapping = connection.execute(
        f"""
        SELECT count(*) FROM (
            SELECT commune_code FROM {quoted_mapping}
            GROUP BY commune_code HAVING count(*) > 1
        )
        """
    ).fetchone()[0]
    if duplicate_mapping:
        raise ValueError("duplicate codes in stable growth-unit mapping")
    if fallback_relation is not None:
        quoted_fallback = _quoted_identifier(fallback_relation)
        fallback_columns = {
            str(row[0])
            for row in connection.execute(
                f"DESCRIBE SELECT * FROM {quoted_fallback}"
            ).fetchall()
        }
        if not {"unit_id", "fallback_individual_growth"}.issubset(
            fallback_columns
        ):
            raise ValueError("FF growth fallback lacks required columns")
    else:
        quoted_fallback = None

    source_fields = ",\n".join(
        f"sum(try_cast(s.{_quoted_identifier(name)} AS DOUBLE)) "
        f"AS {_quoted_identifier('source_' + name)}"
        for name in sorted(measures)
    )
    target_fields = ",\n".join(
        f"sum(try_cast(t.{_quoted_identifier(name)} AS DOUBLE)) "
        f"AS {_quoted_identifier('target_' + name)}"
        for name in sorted(measures)
    )
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _temporal_source_units AS
        SELECT m.unit_id, {source_fields}
        FROM {quoted_source} s
        JOIN {quoted_mapping} m USING (commune_code)
        GROUP BY m.unit_id
        """
    )
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _temporal_target_units AS
        SELECT m.unit_id, {target_fields}
        FROM {quoted_target} t
        JOIN {quoted_mapping} m USING (commune_code)
        GROUP BY m.unit_id
        """
    )
    joined_fields = ",\n".join(
        f"s.{_quoted_identifier('source_' + name)}, "
        f"t.{_quoted_identifier('target_' + name)}"
        for name in sorted(measures)
    )
    fallback_join = (
        f"LEFT JOIN {quoted_fallback} f USING (unit_id)"
        if quoted_fallback is not None else ""
    )
    fallback_field = (
        "f.fallback_individual_growth"
        if quoted_fallback is not None else "NULL::DOUBLE"
    )
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _temporal_growth_inputs AS
        SELECT coalesce(s.unit_id, t.unit_id) AS unit_id, {joined_fields},
            {fallback_field} AS fallback_individual_growth
        FROM _temporal_source_units s
        FULL OUTER JOIN _temporal_target_units t USING (unit_id)
        {fallback_join}
        """
    )

    exponent = projected_years / observed_years

    def raw_factor(measure: str) -> str:
        start = _quoted_identifier("source_" + measure)
        end = _quoted_identifier("target_" + measure)
        return (
            f"CASE WHEN isfinite({start}) AND isfinite({end}) "
            f"AND {start} > 0 AND {end} >= 0 "
            f"THEN pow({end} / {start}, {exponent!r}) END"
        )

    individual_raw = raw_factor("individuals")
    individual_factor = (
        "coalesce("
        + individual_raw
        + ", CASE WHEN isfinite(fallback_individual_growth) "
        "AND fallback_individual_growth >= 0 "
        "THEN fallback_individual_growth END)"
        if quoted_fallback is not None else individual_raw
    )
    household_raw = (
        raw_factor("households") if "households" in measures else "NULL::DOUBLE"
    )
    household_factor = (
        f"coalesce({household_raw}, {individual_factor})"
        if fallback_missing_to_individual else household_raw
    )

    age_measures = {
        "age_0_5", "age_6_10", "age_11_17", "age_18_24",
        "age_25_39", "age_40_54", "age_55_64", "age_65_79", "age_80p",
    }

    def factor_for_measure(measure: str) -> str:
        if measure == "individuals":
            return individual_factor
        if measure == "households":
            return household_factor
        factor = raw_factor(measure)
        if measure in age_measures or fallback_missing_to_individual:
            return f"coalesce({factor}, {individual_factor})"
        return factor

    def factor_for_variable(variable: str) -> str:
        measure = measure_by_variable[variable]
        if measure is None:
            measure = denominator_by_variable[variable]
        return (
            f"{factor_for_measure(measure)} "
            f"AS {_quoted_identifier(variable)}"
        )

    factor_fields = ",\n".join(
        factor_for_variable(variable) for variable in variables
    )
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _temporal_growth_candidates AS
        SELECT unit_id, {factor_fields}
        FROM _temporal_growth_inputs
        """
    )
    invalid_factors = " OR ".join(
        f"{_quoted_identifier(variable)} IS NULL "
        f"OR NOT isfinite({_quoted_identifier(variable)}) "
        f"OR {_quoted_identifier(variable)} < 0"
        for variable in variables
    )
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _temporal_growth_factors AS
        SELECT * FROM _temporal_growth_candidates
        WHERE NOT ({invalid_factors})
        """
    )
    invalid_units = int(connection.execute(
        f"""
        SELECT count(*) FROM _temporal_growth_candidates
        WHERE {invalid_factors}
        """
    ).fetchone()[0])
    matched_units = int(connection.execute(
        "SELECT count(*) FROM _temporal_growth_factors"
    ).fetchone()[0])
    unmatched_source_codes = int(connection.execute(
        f"""
        SELECT count(*) FROM {quoted_source} s
        LEFT JOIN {quoted_mapping} m USING (commune_code)
        WHERE m.unit_id IS NULL
        """
    ).fetchone()[0])
    unmatched_target_codes = int(connection.execute(
        f"""
        SELECT count(*) FROM {quoted_target} t
        LEFT JOIN {quoted_mapping} m USING (commune_code)
        WHERE m.unit_id IS NULL
        """
    ).fetchone()[0])
    individual_fallback_units = 0
    if quoted_fallback is not None:
        individual_fallback_units = int(connection.execute(
            f"""
            SELECT count(*) FROM _temporal_growth_inputs
            WHERE ({individual_raw}) IS NULL
                AND isfinite(fallback_individual_growth)
                AND fallback_individual_growth >= 0
            """
        ).fetchone()[0])
    return {
        "matched_growth_units": matched_units,
        "incomplete_growth_units": invalid_units,
        "unmatched_source_codes": unmatched_source_codes,
        "unmatched_target_codes": unmatched_target_codes,
        "individual_from_ff_units": individual_fallback_units,
    }


def allocate_commune_controls(
    connection: duckdb.DuckDBPyConnection,
    *,
    base_relation: str,
    growth_relation: str,
    weights_relation: str,
    variables: Sequence[str],
    age_variables: Sequence[str],
    individual_variable: str = "ind",
) -> dict[str, int | float]:
    """Grow commune controls and split them to target cells, preserving margins."""
    variables = tuple(variables)
    age_variables = tuple(age_variables)
    if (
        not variables
        or len(variables) != len(set(variables))
        or len(age_variables) != len(set(age_variables))
        or set(age_variables) - set(variables)
        or individual_variable not in variables
    ):
        raise ValueError("invalid temporal allocation variables")
    base = _quoted_identifier(base_relation)
    growth = _quoted_identifier(growth_relation)
    weights = _quoted_identifier(weights_relation)
    for relation, keys in (
        (base, ("commune_code", *variables)),
        (growth, ("commune_code", *variables)),
        (weights, ("cell_id", "commune_code", *variables)),
    ):
        columns = {
            str(row[0])
            for row in connection.execute(
                f"DESCRIBE SELECT * FROM {relation}"
            ).fetchall()
        }
        missing = set(keys) - columns
        if missing:
            raise ValueError(
                f"temporal input {relation} lacks columns: {', '.join(sorted(missing))}"
            )
    duplicate_queries = (
        (
            base,
            "commune_code",
            "duplicate base commune controls",
        ),
        (
            growth,
            "commune_code",
            "duplicate commune growth factors",
        ),
        (
            weights,
            "cell_id, commune_code",
            "duplicate target cell-commune weights",
        ),
    )
    for relation, keys, message in duplicate_queries:
        duplicate_count = connection.execute(
            f"""
            SELECT count(*) FROM (
                SELECT {keys} FROM {relation}
                GROUP BY {keys} HAVING count(*) > 1
            )
            """
        ).fetchone()[0]
        if duplicate_count:
            raise ValueError(message)
    for relation in (base, growth, weights):
        fields = (
            ("commune_code",) if relation != weights
            else ("cell_id", "commune_code")
        )
        key_checks = [
            f"{_quoted_identifier(name)} IS NULL" for name in fields
        ]
        key_checks.append(
            "trim(CAST(commune_code AS VARCHAR)) = ''"
        )
        values = " OR ".join(
            f"{_quoted_identifier(name)} IS NULL "
            f"OR NOT isfinite(try_cast({_quoted_identifier(name)} AS DOUBLE)) "
            f"OR try_cast({_quoted_identifier(name)} AS DOUBLE) < 0"
            for name in variables
        )
        invalid_count = connection.execute(
            f"SELECT count(*) FROM {relation} WHERE "
            f"{' OR '.join(key_checks)} "
            f"OR {values}"
        ).fetchone()[0]
        if invalid_count:
            raise ValueError(f"invalid numeric values in temporal input {relation}")

    grown = ",\n".join(
        f"CAST(b.{_quoted_identifier(name)} AS DOUBLE) "
        f"* CAST(g.{_quoted_identifier(name)} AS DOUBLE) "
        f"AS {_quoted_identifier(name)}"
        for name in variables
    )
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _temporal_controls_raw AS
        SELECT b.commune_code, {grown}
        FROM {base} b JOIN {growth} g USING (commune_code)
        """
    )
    overflow_checks = " OR ".join(
        f"NOT isfinite({_quoted_identifier(name)}) "
        f"OR {_quoted_identifier(name)} < 0"
        for name in variables
    )
    if connection.execute(
        f"SELECT count(*) FROM _temporal_controls_raw WHERE {overflow_checks}"
    ).fetchone()[0]:
        raise ValueError("grown commune controls are not finite")
    unmatched_base = int(connection.execute(
        f"""
        SELECT count(*) FROM {base} b
        LEFT JOIN {growth} g USING (commune_code)
        LEFT JOIN (
            SELECT DISTINCT commune_code FROM {weights}
        ) w USING (commune_code)
        WHERE g.commune_code IS NULL OR w.commune_code IS NULL
        """
    ).fetchone()[0])
    unmatched_target = int(connection.execute(
        f"""
        SELECT count(*) FROM (
            SELECT DISTINCT w.commune_code
            FROM {weights} w
            LEFT JOIN _temporal_controls_raw c USING (commune_code)
            WHERE c.commune_code IS NULL
        )
        """
    ).fetchone()[0])

    if age_variables:
        age_sum = " + ".join(
            _quoted_identifier(name) for name in age_variables
        )
        connection.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE _temporal_controls AS
            WITH totals AS (
                SELECT *, ({age_sum}) AS _age_total
                FROM _temporal_controls_raw
            )
            SELECT commune_code,
                {", ".join(
                    f"CASE WHEN _age_total > 0 "
                    f"THEN {_quoted_identifier(name)} * "
                    f"{_quoted_identifier(individual_variable)} / _age_total "
                    f"ELSE 0.0 END AS {_quoted_identifier(name)}"
                    if name in age_variables
                    else _quoted_identifier(name)
                    for name in variables
                )},
                CASE WHEN _age_total > 0
                    THEN {_quoted_identifier(individual_variable)} / _age_total
                    WHEN {_quoted_identifier(individual_variable)} = 0 THEN 1.0
                    ELSE NULL END AS _age_adjustment
            FROM totals
            """
        )
        unsupported = int(connection.execute(
            f"""
            SELECT count(*) FROM _temporal_controls_raw
            WHERE ({age_sum}) = 0
                AND {_quoted_identifier(individual_variable)} > 0
            """
        ).fetchone()[0])
        if unsupported:
            raise ValueError("positive individuals have no age margin support")
    else:
        connection.execute(
            """
            CREATE OR REPLACE TEMP TABLE _temporal_controls AS
            SELECT *, 1.0 AS _age_adjustment
            FROM _temporal_controls_raw
            """
        )

    weight_sums = ",\n".join(
        f"sum({_quoted_identifier(name)}) AS {_quoted_identifier(name)}"
        for name in variables
    )
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _temporal_weight_sums AS
        SELECT commune_code, {weight_sums}
        FROM {weights}
        GROUP BY commune_code
        """
    )
    for name in variables:
        unsupported = int(connection.execute(
            f"""
            SELECT count(*) FROM _temporal_controls c
            LEFT JOIN _temporal_weight_sums s USING (commune_code)
            WHERE c.{_quoted_identifier(name)} > 0
                AND coalesce(s.{_quoted_identifier(name)}, 0) <= 0
            """
        ).fetchone()[0])
        if unsupported:
            raise ValueError(
                f"positive {name} controls have zero target weights"
            )
    allocated = ",\n".join(
        f"CASE WHEN s.{_quoted_identifier(name)} > 0 "
        f"THEN c.{_quoted_identifier(name)} * w.{_quoted_identifier(name)} "
        f"/ s.{_quoted_identifier(name)} ELSE 0.0 END "
        f"AS {_quoted_identifier(name)}"
        for name in variables
    )
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _temporal_allocated AS
        SELECT w.cell_id, w.commune_code, {allocated}
        FROM {weights} w
        JOIN _temporal_controls c USING (commune_code)
        JOIN _temporal_weight_sums s USING (commune_code)
        """
    )
    cell_totals = ",\n".join(
        f"sum({_quoted_identifier(name)}) AS {_quoted_identifier(name)}"
        for name in variables
    )
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE _temporal_target_cells AS
        SELECT cell_id, {cell_totals}
        FROM _temporal_allocated
        GROUP BY cell_id
        ORDER BY cell_id
        """
    )
    for name in variables:
        mismatches = int(connection.execute(
            f"""
            SELECT count(*) FROM (
                SELECT c.commune_code, c.{_quoted_identifier(name)} AS control,
                    coalesce(sum(a.{_quoted_identifier(name)}), 0) AS allocated
                FROM _temporal_controls c
                LEFT JOIN _temporal_allocated a USING (commune_code)
                GROUP BY c.commune_code, c.{_quoted_identifier(name)}
                HAVING abs(control - allocated) >
                    1e-9 * greatest(1.0, abs(control))
            )
            """
        ).fetchone()[0])
        if mismatches:
            raise RuntimeError(f"temporal allocation did not preserve {name} totals")

    age_adjustments = connection.execute(
        """
        SELECT count(*) FILTER (WHERE abs(_age_adjustment - 1.0) > 1e-12),
            min(_age_adjustment), max(_age_adjustment)
        FROM _temporal_controls
        """
    ).fetchone()
    return {
        "matched_communes": int(connection.execute(
            "SELECT count(*) FROM _temporal_controls"
        ).fetchone()[0]),
        "unmatched_base_communes": unmatched_base,
        "unmatched_target_communes": unmatched_target,
        "age_adjusted_communes": int(age_adjustments[0] or 0),
        "age_adjustment_min": float(age_adjustments[1] or 1.0),
        "age_adjustment_max": float(age_adjustments[2] or 1.0),
    }
