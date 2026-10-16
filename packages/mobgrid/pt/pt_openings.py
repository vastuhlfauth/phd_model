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
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import duckdb

from mobgrid.pt.pt_changes import OpeningDerivedChange
from mobgrid.pt.pt_text import normalise_text
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


def normalise_line_name(value: str | None, *, mode: str | None = None) -> str:
    """Extract and normalise the short code of a CSV ``line_2026`` value.

    Strips a leading ``TER``/``RER``/``Ligne``/``Line`` word prefix, then
    keeps only the first remaining token -- the actual line code -- so
    ``"TER 42 Bordeaux - Pointe-de-Grave"`` normalises to ``"42"`` (not the
    whole corridor description) and compares equal to a GTFS
    ``route_short_name`` of ``"42"``. Already-clean codes such as
    ``"T13"``, ``"RER C"`` or ``"Ligne A"`` normalise to ``"t13"``, ``"c"``
    and ``"a"`` respectively, matching real feeds that already carry the
    ``T`` letter as part of their own short name.

    2026-10-16 fix: a numbered Paris metro line is conventionally written
    ``"M4"``/``"M11"``/``"M12"``/``"M14"`` in the openings CSV, but every
    checked metro feed's own ``route_short_name`` (IDFM, Lyon, Rennes)
    never carries the ``M`` -- Paris's own numbered lines are bare ``"4"``
    etc. in GTFS, and letter-coded metro lines (Lyon ``A``-``D``, Rennes
    ``a``/``b``) were never ``M``-prefixed in the CSV to begin with. So
    when ``mode`` is ``"metro"`` and the code is a leading ``M``/``m``
    immediately followed by a digit (never for a bare letter code, which
    needs no stripping and must not be touched), the ``M`` is dropped
    before matching. Passing no ``mode`` (the default) keeps the old,
    mode-unaware behaviour for any caller that does not have one.
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
    normalised = re.sub(r"[^a-z0-9]+", "", first_token.casefold())
    if mode == "metro":
        normalised = re.sub(r"^m(?=\d)", "", normalised)
    return normalised


@dataclass(frozen=True)
class OpeningRow:
    """One row of the PT openings CSV, reduced to what matching needs."""

    opening_id: str
    network: str
    mode: str
    line_2026: str | None
    section_from: str | None
    section_to: str | None
    # The fields below are only populated for the 2026-10-15/16 national
    # policy's auto-application step (``apply_openings_matches``); they are
    # ``None`` for callers that never read them, such as ``propose_route_matches``.
    confidence: str | None = None
    state_2022: str | None = None
    state_2024: str | None = None
    change_type: str | None = None


def load_openings_rows(
    path: str | Path, network_contains: str
) -> list[OpeningRow]:
    """Read openings CSV rows whose ``network`` contains ``network_contains``.

    Case-insensitive substring match, since the CSV's free-text network
    column rarely matches a config network key exactly (for example
    ``"TBM (Bordeaux Métropole)"``). An empty ``network_contains`` matches
    every row (used by ``apply_openings_matches`` to read the whole CSV).
    """
    return load_openings_rows_for_networks(path, [network_contains])


def load_openings_rows_for_networks(
    path: str | Path, network_substrings: list[str]
) -> list[OpeningRow]:
    """Read openings CSV rows whose ``network`` contains any substring.

    Each row is read once per matching CSV line, even when more than one
    substring matches it (for example a row named ``"RATP (IDFM)"``
    matches both ``"IDFM"`` and ``"RATP (IDFM)"``): used to map every
    network-name alias of one GTFS resource in a single pass over the CSV
    (``mobgrid.pt.cli.run_mapping_for_networks``, 2026-10-16 fix), instead
    of one pass -- and one re-read of the shared resource -- per alias.
    """
    needles = [value.casefold() for value in network_substrings]
    rows: list[OpeningRow] = []
    with Path(path).open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            network_value = (row.get("network") or "").casefold()
            if any(needle in network_value for needle in needles):
                rows.append(
                    OpeningRow(
                        row["id"],
                        row["network"],
                        row["mode"],
                        row.get("line_2026") or None,
                        row.get("section_from") or None,
                        row.get("section_to") or None,
                        row.get("confidence") or None,
                        row.get("state_2022") or None,
                        row.get("state_2024") or None,
                        row.get("change_type") or None,
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


def _probe_route_stop_names(
    connection: duckdb.DuckDBPyConnection,
    gtfs_tables_dir: Path,
    route_ids: list[str],
) -> dict[str, set[str]]:
    """Normalised stop names served by each of ``route_ids``.

    Restricts ``trips.txt``/``stop_times.txt``/``stops.txt`` to
    ``route_ids`` on a scratch copy of ``gtfs_tables_dir`` -- never the
    whole feed, and never the shared extraction directory -- before
    reading them, so this stays cheap even against a national feed.
    """
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
            return {}
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
    stop_names: dict[str, set[str]] = {}
    for route_id, stop_name in rows:
        stop_names.setdefault(route_id, set()).add(normalise_text(stop_name))
    return stop_names


def _disambiguate_by_stops(
    connection: duckdb.DuckDBPyConnection,
    gtfs_tables_dir: Path,
    route_ids: list[str],
    section_from: str | None,
    section_to: str | None,
) -> list[str]:
    """Narrow ``route_ids`` to those with a stop matching a section hint.

    A single matching hint is enough (``any``, not ``all``): this narrows
    an already name-matched handful of candidates sharing one code or
    corridor, where one hint is already good evidence of which of them is
    the real match (see ``_match_by_stop_names_within_mode`` for the
    stricter, whole-mode-family fallback that requires every hint).
    """
    hints = [
        normalise_text(value) for value in (section_from, section_to) if value
    ]
    if not hints:
        return []
    stop_names = _probe_route_stop_names(connection, gtfs_tables_dir, route_ids)
    matched = {
        route_id
        for route_id, names in stop_names.items()
        if any(hint in name for hint in hints for name in names)
    }
    return sorted(matched)


def _match_by_stop_names_within_mode(
    connection: duckdb.DuckDBPyConnection,
    gtfs_tables_dir: Path,
    candidates: list[tuple[str, str | None, str | None]],
    section_from: str | None,
    section_to: str | None,
) -> tuple[str, str | None] | None:
    """The one route of a whole mode family whose stops cover every hint.

    Fallback for a row whose ``line_2026`` text matched no route at all,
    or matched several distinct corridors that ``section_from``/
    ``section_to`` could not narrow to one (section 5.6 point 4, 2026-
    10-16 fix): searches every route of the opening's own mode family by
    stop name alone, ignoring line names entirely. Unlike
    ``_disambiguate_by_stops`` (narrows an already name-matched handful of
    candidates, where matching *either* hint is enough to break a tie),
    this requires *every* non-empty hint to be served by the *same*
    route -- a single-hint match across a whole family (which can be
    hundreds of routes) is far more likely to be coincidental than a real
    corridor match. Returns ``None`` (never guesses) unless exactly one
    route qualifies.
    """
    hints = [normalise_text(value) for value in (section_from, section_to) if value]
    if not hints or not candidates:
        return None
    route_ids = [candidate[0] for candidate in candidates]
    stop_names = _probe_route_stop_names(connection, gtfs_tables_dir, route_ids)
    matched = [
        route_id
        for route_id, names in stop_names.items()
        if all(any(hint in name for name in names) for hint in hints)
    ]
    if len(matched) != 1:
        return None
    ref_by_id = {candidate[0]: candidate[1] for candidate in candidates}
    return matched[0], ref_by_id.get(matched[0])


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

    A ``new_station``/``extension`` row matched to several same-corridor
    route id variants (unlike ``new_line``/``reopening``, which may apply
    identically to every variant by identity alone) is narrowed the same
    way, to only the variants that actually call at the hinted stop
    (section 5.6 point 2, 2026-10-16 fix): a variant that does not is
    excluded from the proposal, never guessed in.

    A row still left unmatched or ambiguous after all of the above falls
    back to searching every route of its own mode family by
    ``section_from``/``section_to`` stop names alone, ignoring line names
    entirely (section 5.6 point 4, 2026-10-16 fix); accepted only when
    that narrows to exactly one route, otherwise the row is left as it
    was (``none``/``ambiguous``), to be logged, not guessed.
    """
    directory = Path(gtfs_tables_dir)
    register_mode_family_udf(connection)
    connection.read_csv(
        str(directory / "routes.txt"), header=True, all_varchar=True, delimiter=","
    ).create_view("routes")
    proposals = []
    for opening in openings:
        proposals.append(_propose_one_match(connection, directory, opening))
    return proposals


def _no_match_proposal(opening: OpeningRow, notes: str) -> MappingProposal:
    return MappingProposal(
        opening.opening_id,
        opening.network,
        opening.mode,
        opening.line_2026,
        opening.section_from,
        opening.section_to,
        (),
        (),
        "none",
        notes,
    )


def _propose_one_match(
    connection: duckdb.DuckDBPyConnection,
    directory: Path,
    opening: OpeningRow,
) -> MappingProposal:
    wanted = normalise_line_name(opening.line_2026, mode=opening.mode)
    families = _CSV_MODE_TO_FAMILIES.get(opening.mode, frozenset())
    if not families:
        return _no_match_proposal(opening, "no line_2026 text or unrecognised mode")
    candidates = _candidate_routes(connection, families)
    result = (
        _match_by_name(connection, directory, opening, wanted, candidates)
        if wanted
        else _no_match_proposal(opening, "no line_2026 text or unrecognised mode")
    )
    if result.match_confidence in ("none", "ambiguous"):
        fallback = _match_by_stop_names_within_mode(
            connection, directory, candidates, opening.section_from, opening.section_to
        )
        if fallback is not None:
            route_id, ref = fallback
            result = MappingProposal(
                opening.opening_id,
                opening.network,
                opening.mode,
                opening.line_2026,
                opening.section_from,
                opening.section_to,
                (route_id,),
                (ref,) if ref else (),
                "stop-confirmed",
                "matched by section_from/section_to stop names alone within "
                f"the {opening.mode!r} mode family -- no usable line-name "
                f"match (previously {result.match_confidence!r}: "
                f"{result.notes})",
            )
    return result


def _match_by_name(
    connection: duckdb.DuckDBPyConnection,
    directory: Path,
    opening: OpeningRow,
    wanted: str,
    candidates: list[tuple[str, str | None, str | None]],
) -> MappingProposal:
    """Match one row by its ``line_2026`` short code and mode family alone."""
    short_matches = [
        candidate for candidate in candidates if normalise_text(candidate[1]) == wanted
    ]
    prefix_matches = []
    if not short_matches:
        # Catches circular/directional variants that share a code but
        # add a short numeric/letter suffix (e.g. "H1"/"H2" for "H"),
        # without the single-letter noise a bare contains check gives.
        prefix_matches = [
            candidate
            for candidate in candidates
            if normalise_text(candidate[1]).startswith(wanted)
            and 0 < len(normalise_text(candidate[1])) - len(wanted) <= 2
        ]
    pool = short_matches or prefix_matches
    if not pool and len(wanted) >= 2:
        # A single-letter code (e.g. "G") would match almost any long
        # name as a bare substring, so the contains fallback is only
        # used for codes of two characters or more.
        pool = [
            candidate
            for candidate in candidates
            if wanted in normalise_text(candidate[2])
        ]
    if not pool:
        return _no_match_proposal(
            opening, "no route_short_name/route_long_name matched"
        )
    distinct_long_names = {candidate[2] for candidate in pool}
    route_ids = [candidate[0] for candidate in pool]
    refs = sorted({candidate[1] for candidate in pool if candidate[1]})
    ref_by_id = {candidate[0]: candidate[1] for candidate in pool}
    if len(distinct_long_names) <= 1:
        final_ids = route_ids
        confidence = "exact"
        notes = "unique corridor by name and mode"
        if (
            opening.change_type in ("new_station", "extension")
            and len(route_ids) > 1
        ):
            # A cut/new-station edit needs the specific route(s) that
            # actually call at the hinted stop, not every same-corridor
            # variant by identity alone (unlike new_line/reopening):
            # exclude a variant the stop hint shows never calls there
            # (section 5.6 point 2, 2026-10-16 fix).
            calling_ids = _disambiguate_by_stops(
                connection,
                directory,
                route_ids,
                opening.section_from,
                opening.section_to,
            )
            if calling_ids and len(calling_ids) < len(route_ids):
                excluded_refs = sorted(
                    {
                        ref_by_id[route_id]
                        for route_id in route_ids
                        if route_id not in calling_ids and ref_by_id.get(route_id)
                    }
                )
                confidence = "stop-confirmed"
                final_ids = calling_ids
                notes = (
                    f"narrowed from {len(route_ids)} same-corridor route ids "
                    f"to {len(final_ids)} that call at the section_from/"
                    "section_to stop; excluded (no matching stop): "
                    + (", ".join(excluded_refs) or "n/a")
                )
        return MappingProposal(
            opening.opening_id,
            opening.network,
            opening.mode,
            opening.line_2026,
            opening.section_from,
            opening.section_to,
            tuple(sorted(final_ids)),
            tuple(refs),
            confidence,
            notes,
        )
    narrowed = _disambiguate_by_stops(
        connection, directory, route_ids, opening.section_from, opening.section_to
    )
    # Numbered/lettered variants of one circular or directional service
    # (e.g. Bordeaux's Bus Express H -> H1/H2) only ever reach ``pool``
    # through the ``prefix_matches`` fallback above (never
    # ``short_matches``, which requires an exact short-name equality).
    # Unlike a genuine same-name/mode collision between two unrelated
    # lines, every such variant belongs to the one reported line, so when
    # the generic stop-hint disambiguation fails to narrow them at all
    # (free-text hints like "Cenon Gare (circular H1/H2)" are not real
    # GTFS stop names and essentially never match), treating every
    # variant as the single correct match is a confirmed fact, not a
    # guess (2026-10-16 fix, section 5.6 point 4 -- confirmed on
    # Bordeaux's real NAQ-11 "H (Bus Express)" row).
    is_prefix_family = not short_matches and bool(prefix_matches)
    if len(narrowed) == 1:
        confidence = "stop-confirmed"
        final_ids = narrowed
    elif is_prefix_family and not narrowed:
        confidence = "exact"
        final_ids = route_ids
    elif narrowed:
        confidence = "ambiguous"
        final_ids = narrowed
    else:
        confidence = "ambiguous"
        final_ids = route_ids
    return MappingProposal(
        opening.opening_id,
        opening.network,
        opening.mode,
        opening.line_2026,
        opening.section_from,
        opening.section_to,
        tuple(sorted(final_ids)),
        tuple(refs),
        confidence,
        (
            "numbered/lettered variants of one circular or directional "
            "service, not a real ambiguity"
            if confidence == "exact" and is_prefix_family
            else f"{len(distinct_long_names)} distinct corridors shared "
            "this name/mode; narrowed by section_from/section_to"
        ),
    )


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


def run_mapping_for_networks(
    openings_csv: str | Path,
    gtfs_tables_dir: str | Path,
    networks: list[str],
    output_csv: str | Path,
) -> list[MappingProposal]:
    """Map every network-name alias of one GTFS resource in a single pass.

    Several ``network_resource_ids`` keys can resolve to the same GTFS
    resource (for example ``"IDFM"``, ``"RATP (IDFM)"`` and ``"Keolis
    Tisse (IDFM)"`` all read resource 80921): mapping them together, one
    ``propose_route_matches`` call against one shared connection instead
    of one ``run_mapping`` call per alias, means that resource is read
    exactly once (``mobgrid.pt.cli._run_map_and_apply_all``, 2026-10-16
    fix, section 5.6 point 4).
    """
    openings = load_openings_rows_for_networks(openings_csv, networks)
    connection = duckdb.connect()
    proposals = propose_route_matches(connection, gtfs_tables_dir, openings)
    write_mapping_csv(output_csv, proposals)
    return proposals


def run_mapping_grouped(
    openings_csv: str | Path,
    network_contains: str,
    gtfs_tables_dir_by_mode: dict[str, str | Path],
    output_csv: str | Path,
) -> list[MappingProposal]:
    """Map one network's rows, each against its own mode's GTFS resource.

    Covers ``"TER Occitanie (liO)"`` (section 5.6 point 5): its rail rows
    describe TER services (resolved against SNCF's resource) and its
    bus/coach rows describe liO's own interurban coach lines (resolved
    against liO's own resource), two different physical operators sharing
    one reported brand. Each row is matched only against its own mode's
    resource, then every proposal is written in a single
    ``write_mapping_csv`` call, so a later mode group's run never
    overwrites an earlier one's correct match for a *different* row (the
    risk a plain two-call ``run_mapping`` sequence would have, since
    ``write_mapping_csv`` replaces by ``opening_id`` and both calls would
    otherwise share the same ``opening_id`` set).
    """
    rows = load_openings_rows(openings_csv, network_contains)
    connection = duckdb.connect()
    proposals: list[MappingProposal] = []
    covered_ids: set[str] = set()
    for mode, tables_dir in gtfs_tables_dir_by_mode.items():
        mode_rows = [row for row in rows if row.mode == mode]
        if not mode_rows:
            continue
        proposals.extend(propose_route_matches(connection, tables_dir, mode_rows))
        covered_ids |= {row.opening_id for row in mode_rows}
    proposals.extend(
        MappingProposal(
            row.opening_id,
            row.network,
            row.mode,
            row.line_2026,
            row.section_from,
            row.section_to,
            (),
            (),
            "none",
            f"mode {row.mode!r} has no configured resource for this network",
        )
        for row in rows
        if row.opening_id not in covered_ids
    )
    write_mapping_csv(output_csv, proposals)
    return proposals


@dataclass(frozen=True)
class OpeningsApplication:
    """Result of applying the PT openings CSV/mapping (section 5.6 point 4).

    ``applied`` are auto-applied, ready for ``write_from_openings``.

    ``warnings`` is one line per row that carries a real ``remove``
    instruction -- an accepted-confidence, instruction-capable
    (``new_line``/``reopening``/``extension``/``new_station``) row whose
    ``state_2022``/``state_2024`` is ``remove`` at some date -- but could
    not be applied because matching failed (no proposal, rejected
    ``match_confidence``, or resolved to 0 route ids): the national
    policy expects an edit here, so a failure is a real gap worth
    surfacing at WARNING (section 5.6 point 6, 2026-10-16 logging fix).

    ``not_applied_by_design`` counts every row skipped on purpose, one
    count per reason, never one line per row: ``"low_confidence"`` (CSV
    ``confidence`` outside ``include_row_confidence``), ``"no_remove_state"``
    (an instruction-capable row whose state is ``keep``/``keep`` --
    nothing to apply yet, e.g. a planned line not yet open) and
    ``"non_instruction_change_type"`` (``restructuring``/``renaming``/
    ``suspension``/``closure``/``relocation``, which never give an
    instruction regardless of state). These never reach the matching step
    at all, since no match result could change their outcome.

    ``closed_before_2026`` is one line per row whose state is ``add`` at
    either reference date (section 5.6 point 5): a line/section closed
    before 2026, with no 2026 GTFS counterpart, left out of every state
    and reported as a known gap, logged at INFO alongside it.

    ``len(applied)`` counts *route-level* edits, not rows: a
    ``new_station``/``extension`` row matching several same-corridor
    route variants, or a ``new_line``/``reopening`` row matching several
    numbered/lettered variants of one service, contributes one entry per
    route. Use ``applied_opening_ids``/``row_counts`` for row-level counts
    (2026-10-16 bookkeeping fix): every opening-list row falls into
    exactly one of six categories (``applied``, ``warnings``, the three
    ``not_applied_by_design`` reasons, ``closed_before_2026``), so these
    always sum to the number of CSV rows read -- checked by
    ``apply_openings_matches`` itself.
    """

    applied: tuple[OpeningDerivedChange, ...]
    warnings: tuple[str, ...]
    not_applied_by_design: dict[str, int]
    closed_before_2026: tuple[str, ...]

    @property
    def applied_opening_ids(self) -> frozenset[str]:
        """Distinct rows actually applied (row-level, not route-level)."""
        return frozenset(change.opening_id for change in self.applied)

    def row_counts(self) -> dict[str, int]:
        """One count per row category; always sums to the CSV row count.

        Keys: ``"applied"`` (row-level, via ``applied_opening_ids``),
        ``"remove_not_applied"`` (``warnings``, one per row),
        ``"low_confidence"``/``"no_remove_state"``/
        ``"non_instruction_change_type"`` (``not_applied_by_design``) and
        ``"closed_before_2026"``.
        """
        counts = dict(self.not_applied_by_design)
        counts["applied"] = len(self.applied_opening_ids)
        counts["remove_not_applied"] = len(self.warnings)
        counts["closed_before_2026"] = len(self.closed_before_2026)
        return counts


# change_type values that ever give a route-presence instruction when
# paired with a ``remove`` state (section 5.6 point 2); every other
# change_type (``restructuring``, ``renaming``, ``relocation``,
# ``suspension``, ``closure``) never does, regardless of state, and is
# counted as a by-design, not-applied reason rather than attempted at all
# (2026-10-16 logging fix, section 5.6 point 6). The same four types may
# also resolve to several 2026 route ids: ``new_line``/``reopening``
# identically for every numbered/lettered variant of one circular or
# directional service (a drop needs only route identity); ``extension``/
# ``new_station`` only for the variants that ``mobgrid.pt map-openings``
# confirmed actually call at the hinted stop, since a cut or new-station
# edit needs a single route's own stop pattern (2026-10-16 fix, section
# 5.6 point 2 -- see ``_match_by_name``'s same-corridor narrowing).
_INSTRUCTION_CHANGE_TYPES = frozenset(
    ("new_line", "reopening", "extension", "new_station")
)


def apply_openings_matches(
    openings_csv: str | Path,
    mapping_csv: str | Path,
    *,
    include_row_confidence: Sequence[str] = ("high", "medium"),
    apply_match_confidence: Sequence[str] = ("exact", "stop-confirmed"),
) -> OpeningsApplication:
    """Turn mapped openings rows into auto-applied per-route edit instructions.

    2026-10-15/16 national policy, section 5.6 point 4: a row is
    auto-applied only when its own CSV ``confidence`` is in
    ``include_row_confidence`` *and* its ``change_type`` can ever give an
    instruction (``_INSTRUCTION_CHANGE_TYPES``) *and* its state is
    ``remove`` at some date *and* its ``map-openings`` proposal's
    ``match_confidence`` is in ``apply_match_confidence`` *and* that
    proposal resolves to one or more 2026 route ids. Callers must pass
    ``national_policy.openings_list.include_row_confidence``/
    ``apply_match_confidence`` from `config/gtfs_rebuild.yaml` (the
    keyword defaults here only match the values configured there today,
    for callers with no loaded policy, e.g. a report rendered for a
    config with no ``national_policy`` at all). A row whose state is
    ``add`` at either date (point 5) is a structural gap (no 2026
    counterpart exists at all), reported separately, never a matching
    failure.

    What an applied row's ``remove`` state actually does (``drop``,
    ``cut`` or ``new_station``) is *not* decided here -- it depends on
    ``change_type`` and is resolved later by
    ``OpeningDerivedChange.instruction_at`` and
    ``mobgrid.pt.route_edits.resolve_route_edits``.

    Every row falls into exactly one of six row-level categories
    (``OpeningsApplication.row_counts``); this is checked before
    returning (2026-10-16 bookkeeping fix) and raises ``RuntimeError`` if
    they do not sum to the number of rows read, since that would mean a
    row fell through uncategorised or was counted twice.
    """
    rows = load_openings_rows(openings_csv, "")
    mapping: dict[str, dict[str, str]] = {}
    mapping_path = Path(mapping_csv)
    if mapping_path.is_file():
        with mapping_path.open(encoding="utf-8", newline="") as stream:
            mapping = {row["opening_id"]: row for row in csv.DictReader(stream)}

    applied: list[OpeningDerivedChange] = []
    warnings: list[str] = []
    not_applied_by_design: dict[str, int] = {}
    closed_before_2026: list[str] = []

    def count_by_design(reason: str) -> None:
        not_applied_by_design[reason] = not_applied_by_design.get(reason, 0) + 1

    for row in rows:
        label = f"{row.opening_id} ({row.network}, {row.line_2026 or row.mode})"
        if row.state_2022 == "add" or row.state_2024 == "add":
            closed_before_2026.append(
                f"{label}: state_2022={row.state_2022}, "
                f"state_2024={row.state_2024} -- closed before 2026, no "
                "2026 GTFS counterpart, left out of every state"
            )
            continue
        if row.confidence not in include_row_confidence:
            count_by_design("low_confidence")
            continue
        if row.change_type not in _INSTRUCTION_CHANGE_TYPES:
            # restructuring/renaming/suspension/closure/relocation: never
            # an instruction, whatever the match would have been.
            count_by_design("non_instruction_change_type")
            continue
        if row.state_2022 != "remove" and row.state_2024 != "remove":
            # An instruction-capable change_type, but nothing to remove
            # yet at either date (e.g. a planned line not yet open).
            count_by_design("no_remove_state")
            continue
        # From here, the national policy expects a real instruction: any
        # failure to match below is a genuine gap, logged at WARNING.
        mapped = mapping.get(row.opening_id)
        if mapped is None:
            warnings.append(f"{label}: no map-openings proposal found")
            continue
        match_confidence = mapped.get("match_confidence", "none")
        if match_confidence not in apply_match_confidence:
            warnings.append(
                f"{label}: match_confidence={match_confidence!r}, not applied"
            )
            continue
        route_ids = [
            value for value in (mapped.get("candidate_route_ids") or "").split("|")
            if value
        ]
        if not route_ids:
            warnings.append(
                f"{label}: {match_confidence} match resolved to 0 route ids, "
                "not applied"
            )
            continue
        if row.state_2022 not in ("keep", "remove", "modify") or row.state_2024 not in (
            "keep", "remove", "modify"
        ):
            warnings.append(
                f"{label}: unrecognised state_2022={row.state_2022!r}/"
                f"state_2024={row.state_2024!r}, not applied"
            )
            continue
        for route_id in route_ids:
            applied.append(
                OpeningDerivedChange(
                    opening_id=row.opening_id,
                    network=row.network,
                    route_id=route_id,
                    mode=row.mode,
                    change_type=row.change_type,
                    line_2026=row.line_2026,
                    section_from=row.section_from,
                    section_to=row.section_to,
                    match_confidence=match_confidence,
                    csv_confidence=row.confidence,
                    state_2022=row.state_2022,
                    state_2024=row.state_2024,
                    notes=mapped.get("notes") or None,
                )
            )
    application = OpeningsApplication(
        tuple(applied),
        tuple(warnings),
        dict(not_applied_by_design),
        tuple(closed_before_2026),
    )
    counted_rows = sum(application.row_counts().values())
    if counted_rows != len(rows):
        raise RuntimeError(
            f"openings-list row categories sum to {counted_rows}, expected "
            f"{len(rows)} rows read from {openings_csv} -- every row must "
            f"fall in exactly one category: {application.row_counts()}"
        )
    return application


def resolve_and_extract(
    gtfs_inventory_csv: str | Path, resource_id: int, scratch_dir: str | Path
) -> Path:
    """Resolve a resource id to its local ZIP and extract it once, offline only.

    Thin wrapper kept here (rather than imported from ``calibrate.py``) so
    this module has no dependency on the calibration pipeline's own
    ``GtfsRebuildConfig``; the CLI command only needs a resource id.

    Never downloads: ``resolve_gtfs_local_path`` only reads the
    ``local_path`` already recorded in ``config/gtfs_inventory.csv`` by a
    prior ``acquire`` run, and this function only opens that local file.
    If it is not yet present on disk (the resource is configured but not
    yet downloaded by ``acquire``), this raises a clear
    ``FileNotFoundError`` naming the missing path and the ``acquire``
    command to run, rather than a less helpful error surfacing from deep
    inside ``zipfile`` -- it still never attempts a network request
    itself (2026-10-16 fix, map-and-apply-all/map-openings read already-
    acquired feeds offline; see ``tests/mobgrid/pt/test_pt_openings.py``'s
    ``test_resolve_and_extract_*`` for the no-network-call guarantee).
    """
    from mobgrid.pt.calibrate import resolve_gtfs_local_path

    local_path = resolve_gtfs_local_path(gtfs_inventory_csv, resource_id)
    if not local_path.is_file():
        raise FileNotFoundError(
            f"GTFS resource {resource_id} is configured in {gtfs_inventory_csv} "
            f"but not downloaded locally at {local_path}. mobgrid.pt reads "
            "already-acquired feeds offline only and never downloads; run "
            f"`acquire --manifest config/sources.yaml --dataset "
            f"<id of resource {resource_id}>` then `--check-gtfs` first."
        )
    table_dir = Path(scratch_dir)
    extract_gtfs_tables(local_path, table_dir)
    return table_dir

