"""Propose (never apply) 2026 GTFS route/stop matches for the PT openings CSV.

Reads the read-only ``config/French transit openings 2022 to 2026.csv``
(2026-10-15 follow-up) and, for one GTFS resource at a time, proposes which
2026 route(s) each row concerns, by normalised line name, GTFS mode family,
and the ``section_from``/``section_to`` stop-name hints when several
candidates share the same name or share a mode. Results are written to
``config/pt_openings_mapping.csv`` with a ``match_confidence`` column;
nothing here ever writes to ``config/pt_changes.yaml`` -- a human (or a
later, separate step) still confirms each row before it is applied.
"""

from __future__ import annotations

import csv
import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import duckdb

from mobgrid.pt.stop_tables import (
    extract_gtfs_tables,
    register_mode_family_udf,
    restrict_gtfs_tables_to_routes,
)

_MAPPING_CSV_COLUMNS = (
    "opening_id",
    "network",
    "mode",
    "line_2026",
    "section_from",
    "section_to",
    "candidate_route_ids",
    "candidate_refs",
    "match_confidence",
    "notes",
)

# A CSV mode maps to one or more rebuild mode families (gtfs_mode_family's
# output): tram_train and cable are ambiguous in real GTFS feeds (tagged as
# either tram/rail, or as an aerial-lift grouped with metro), so both
# families are accepted as candidates.
_CSV_MODE_TO_FAMILIES: dict[str, frozenset[str]] = {
    "metro": frozenset({"metro"}),
    "tram": frozenset({"tram"}),
    "tram_train": frozenset({"tram", "rail"}),
    "cable": frozenset({"metro"}),
    "rail": frozenset({"rail"}),
    "bus": frozenset({"bus"}),
    "bhns": frozenset({"bus"}),
    "trolleybus": frozenset({"bus"}),
    "ferry": frozenset({"ferry"}),
}


def _normalise_text(value: str | None) -> str:
    """Casefold, strip accents, and keep only alphanumerics."""
    if not value:
        return ""
    ascii_value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    return re.sub(r"[^a-z0-9]+", "", ascii_value.casefold())


def normalise_line_name(value: str | None) -> str:
    """Extract and normalise the short code of a CSV ``line_2026`` value.

    Strips a leading ``TER``/``RER``/``Ligne``/``Line`` word prefix, then
    keeps only the first remaining token -- the actual line code -- so
    ``"TER 42 Bordeaux - Pointe-de-Grave"`` normalises to ``"42"`` (not the
    whole corridor description) and compares equal to a GTFS
    ``route_short_name`` of ``"42"``. Already-clean codes such as
    ``"T13"``, ``"RER C"`` or ``"Ligne A"`` normalise to ``"t13"``, ``"c"``
    and ``"a"`` respectively, matching real feeds that already carry the
    ``T``/``M`` letter as part of their own short name (no further
    single-letter stripping is applied, to avoid double-stripping).
    """
    text = (
        unicodedata.normalize("NFKD", value or "")
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    text = re.sub(r"^\s*(?:ter|rer)\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*(?:ligne|line)\s+", "", text, flags=re.IGNORECASE)
    tokens = text.split()
    first_token = tokens[0] if tokens else text
    return re.sub(r"[^a-z0-9]+", "", first_token.casefold())


@dataclass(frozen=True)
class OpeningRow:
    """One row of the PT openings CSV, reduced to what matching needs."""

    opening_id: str
    network: str
    mode: str
    line_2026: str | None
    section_from: str | None
    section_to: str | None


def load_openings_rows(
    path: str | Path, network_contains: str
) -> list[OpeningRow]:
    """Read openings CSV rows whose ``network`` contains ``network_contains``.

    Case-insensitive substring match, since the CSV's free-text network
    column rarely matches a config network key exactly (for example
    ``"TBM (Bordeaux Métropole)"``).
    """
    needle = network_contains.casefold()
    rows: list[OpeningRow] = []
    with Path(path).open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if needle in (row.get("network") or "").casefold():
                rows.append(
                    OpeningRow(
                        row["id"],
                        row["network"],
                        row["mode"],
                        row.get("line_2026") or None,
                        row.get("section_from") or None,
                        row.get("section_to") or None,
                    )
                )
    return rows


@dataclass(frozen=True)
class MappingProposal:
    """One proposed (never applied) match for one opening row."""

    opening_id: str
    network: str
    mode: str
    line_2026: str | None
    section_from: str | None
    section_to: str | None
    candidate_route_ids: tuple[str, ...]
    candidate_refs: tuple[str, ...]
    match_confidence: str  # "exact" | "stop-confirmed" | "ambiguous" | "none"
    notes: str


def _candidate_routes(
    connection: duckdb.DuckDBPyConnection, families: frozenset[str]
) -> list[tuple[str, str | None, str | None]]:
    family_list = ", ".join(f"'{family}'" for family in families)
    return connection.execute(
        f"""
        SELECT routes.route_id, routes.route_short_name, routes.route_long_name
        FROM routes
        WHERE gtfs_mode_family(TRY_CAST(routes.route_type AS INTEGER))
            IN ({family_list})
        """
    ).fetchall()


def _disambiguate_by_stops(
    connection: duckdb.DuckDBPyConnection,
    gtfs_tables_dir: Path,
    route_ids: list[str],
    section_from: str | None,
    section_to: str | None,
) -> list[str]:
    """Narrow ``route_ids`` to those with a stop matching a section hint."""
    hints = [
        _normalise_text(value) for value in (section_from, section_to) if value
    ]
    if not hints:
        return []
    scratch = gtfs_tables_dir.parent / f"_openings_probe_{gtfs_tables_dir.name}"
    if scratch.exists():
        shutil.rmtree(scratch)
    shutil.copytree(gtfs_tables_dir, scratch)
    try:
        restrict_gtfs_tables_to_routes(scratch, route_ids)
        stop_times_path = scratch / "stop_times.txt"
        stops_path = scratch / "stops.txt"
        trips_path = scratch / "trips.txt"
        if not (stop_times_path.is_file() and stops_path.is_file()):
            return []
        for name, source in (
            ("trips", trips_path),
            ("stop_times", stop_times_path),
            ("stops", stops_path),
        ):
            connection.read_csv(
                str(source), header=True, all_varchar=True, delimiter=","
            ).create_view(f"probe_{name}")
        rows = connection.execute(
            """
            SELECT DISTINCT trips.route_id, stops.stop_name
            FROM probe_trips trips
            JOIN probe_stop_times st USING (trip_id)
            JOIN probe_stops stops USING (stop_id)
            """
        ).fetchall()
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    matched = {
        route_id
        for route_id, stop_name in rows
        if any(hint in _normalise_text(stop_name) for hint in hints)
    }
    return sorted(matched)


def propose_route_matches(
    connection: duckdb.DuckDBPyConnection,
    gtfs_tables_dir: str | Path,
    openings: list[OpeningRow],
) -> list[MappingProposal]:
    """Propose candidate 2026 routes for each opening row of one GTFS feed.

    Reads ``routes.txt`` only (lightweight) to shortlist by normalised line
    name and mode family; for rows left ambiguous after that (several
    distinct corridors sharing a name or mode), restricts
    ``trips.txt``/``stop_times.txt``/``stops.txt`` to just the ambiguous
    candidates on a scratch copy -- never the whole feed, and never the
    shared extraction directory -- and uses ``section_from``/
    ``section_to`` as stop-name hints to narrow further.
    """
    directory = Path(gtfs_tables_dir)
    register_mode_family_udf(connection)
    connection.read_csv(
        str(directory / "routes.txt"), header=True, all_varchar=True, delimiter=","
    ).create_view("routes")
    proposals = []
    for opening in openings:
        wanted = normalise_line_name(opening.line_2026)
        families = _CSV_MODE_TO_FAMILIES.get(opening.mode, frozenset())
        if not wanted or not families:
            proposals.append(
                MappingProposal(
                    opening.opening_id,
                    opening.network,
                    opening.mode,
                    opening.line_2026,
                    opening.section_from,
                    opening.section_to,
                    (),
                    (),
                    "none",
                    "no line_2026 text or unrecognised mode",
                )
            )
            continue
        candidates = _candidate_routes(connection, families)
        short_matches = [
            candidate
            for candidate in candidates
            if _normalise_text(candidate[1]) == wanted
        ]
        prefix_matches = []
        if not short_matches:
            # Catches circular/directional variants that share a code but
            # add a short numeric/letter suffix (e.g. "H1"/"H2" for "H"),
            # without the single-letter noise a bare contains check gives.
            prefix_matches = [
                candidate
                for candidate in candidates
                if _normalise_text(candidate[1]).startswith(wanted)
                and 0
                < len(_normalise_text(candidate[1])) - len(wanted)
                <= 2
            ]
        pool = short_matches or prefix_matches
        if not pool and len(wanted) >= 2:
            # A single-letter code (e.g. "G") would match almost any long
            # name as a bare substring, so the contains fallback is only
            # used for codes of two characters or more.
            pool = [
                candidate
                for candidate in candidates
                if wanted in _normalise_text(candidate[2])
            ]
        if not pool:
            proposals.append(
                MappingProposal(
                    opening.opening_id,
                    opening.network,
                    opening.mode,
                    opening.line_2026,
                    opening.section_from,
                    opening.section_to,
                    (),
                    (),
                    "none",
                    "no route_short_name/route_long_name matched",
                )
            )
            continue
        distinct_long_names = {candidate[2] for candidate in pool}
        route_ids = [candidate[0] for candidate in pool]
        refs = sorted({candidate[1] for candidate in pool if candidate[1]})
        if len(distinct_long_names) <= 1:
            proposals.append(
                MappingProposal(
                    opening.opening_id,
                    opening.network,
                    opening.mode,
                    opening.line_2026,
                    opening.section_from,
                    opening.section_to,
                    tuple(sorted(route_ids)),
                    tuple(refs),
                    "exact",
                    "unique corridor by name and mode",
                )
            )
            continue
        narrowed = _disambiguate_by_stops(
            connection,
            directory,
            route_ids,
            opening.section_from,
            opening.section_to,
        )
        if len(narrowed) == 1:
            confidence = "stop-confirmed"
            final_ids = narrowed
        elif narrowed:
            confidence = "ambiguous"
            final_ids = narrowed
        else:
            confidence = "ambiguous"
            final_ids = route_ids
        proposals.append(
            MappingProposal(
                opening.opening_id,
                opening.network,
                opening.mode,
                opening.line_2026,
                opening.section_from,
                opening.section_to,
                tuple(sorted(final_ids)),
                tuple(refs),
                confidence,
                f"{len(distinct_long_names)} distinct corridors shared this "
                "name/mode; narrowed by section_from/section_to",
            )
        )
    return proposals


def write_mapping_csv(path: str | Path, proposals: list[MappingProposal]) -> None:
    """Append/replace ``proposals`` in ``config/pt_openings_mapping.csv``.

    Keyed by ``opening_id``: existing rows for ids not in ``proposals`` are
    kept untouched (so mapping one network never discards another's
    results), rows for the same id are replaced with the fresh proposal.
    """
    destination = Path(path)
    existing: dict[str, dict[str, str]] = {}
    if destination.is_file():
        with destination.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                existing[row["opening_id"]] = row
    for proposal in proposals:
        existing[proposal.opening_id] = {
            "opening_id": proposal.opening_id,
            "network": proposal.network,
            "mode": proposal.mode,
            "line_2026": proposal.line_2026 or "",
            "section_from": proposal.section_from or "",
            "section_to": proposal.section_to or "",
            "candidate_route_ids": "|".join(proposal.candidate_route_ids),
            "candidate_refs": "|".join(proposal.candidate_refs),
            "match_confidence": proposal.match_confidence,
            "notes": proposal.notes,
        }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=_MAPPING_CSV_COLUMNS)
        writer.writeheader()
        for opening_id in sorted(existing):
            writer.writerow(existing[opening_id])


def run_mapping(
    openings_csv: str | Path,
    gtfs_tables_dir: str | Path,
    network_contains: str,
    output_csv: str | Path,
) -> list[MappingProposal]:
    """End-to-end: load rows for one network, propose matches, write them."""
    openings = load_openings_rows(openings_csv, network_contains)
    connection = duckdb.connect()
    proposals = propose_route_matches(connection, gtfs_tables_dir, openings)
    write_mapping_csv(output_csv, proposals)
    return proposals


def resolve_and_extract(
    gtfs_inventory_csv: str | Path, resource_id: int, scratch_dir: str | Path
) -> Path:
    """Resolve a resource id to its local ZIP and extract it once.

    Thin wrapper kept here (rather than imported from ``calibrate.py``) so
    this module has no dependency on the calibration pipeline's own
    ``GtfsRebuildConfig``; the CLI command only needs a resource id.
    """
    from mobgrid.pt.calibrate import resolve_gtfs_local_path

    local_path = resolve_gtfs_local_path(gtfs_inventory_csv, resource_id)
    table_dir = Path(scratch_dir)
    extract_gtfs_tables(local_path, table_dir)
    return table_dir
