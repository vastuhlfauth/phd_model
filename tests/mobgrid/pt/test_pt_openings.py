"""Tests for the PT-openings-to-GTFS-route proposal tool (2026-10-15/16)."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import duckdb
from mobgrid.pt.config import load_gtfs_rebuild_config
from mobgrid.pt.pt_changes import PtChangeCatalogue, build_network_resource_ids
from mobgrid.pt.pt_openings import (
    OpeningRow,
    apply_openings_matches,
    load_openings_rows,
    normalise_line_name,
    propose_route_matches,
    resolve_and_extract,
    run_mapping_grouped,
    write_mapping_csv,
)
from mobgrid.pt.route_edits import collect_edit_specs

ROOT = Path(__file__).resolve().parents[3]


def _write_gtfs(root: Path, routes: list[tuple], stops: list[tuple]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "routes.txt").write_text(
        "route_id,route_short_name,route_long_name,route_type\n"
        + "\n".join(",".join(row) for row in routes)
        + "\n",
        encoding="utf-8",
    )
    # One trip and one stop per declared stop per route (sequential).
    trip_rows = ["trip_id,route_id"]
    stop_time_rows = ["trip_id,stop_id,stop_sequence"]
    stop_rows = ["stop_id,stop_name"]
    seen_stops: set[str] = set()
    for route_id, stop_ids_names in stops:
        trip_id = f"trip-{route_id}"
        trip_rows.append(f"{trip_id},{route_id}")
        for seq, (stop_id, stop_name) in enumerate(stop_ids_names, start=1):
            stop_time_rows.append(f"{trip_id},{stop_id},{seq}")
            if stop_id not in seen_stops:
                stop_rows.append(f"{stop_id},{stop_name}")
                seen_stops.add(stop_id)
    (root / "trips.txt").write_text("\n".join(trip_rows) + "\n", encoding="utf-8")
    (root / "stop_times.txt").write_text(
        "\n".join(stop_time_rows) + "\n", encoding="utf-8"
    )
    (root / "stops.txt").write_text("\n".join(stop_rows) + "\n", encoding="utf-8")


def test_normalise_line_name_strips_ter_and_line_prefixes() -> None:
    assert normalise_line_name("TER 42 Bordeaux - Pointe-de-Grave").startswith("42")
    assert normalise_line_name("Ligne A") == "a"
    assert normalise_line_name("T6") == "t6"


def test_normalise_line_name_strips_metro_m_prefix_for_numbered_lines() -> None:
    # 2026-10-16 fix: a numbered Paris metro line is conventionally
    # written "M4"/"M11"/"M12"/"M14" in the CSV, but IDFM's own
    # route_short_name is bare ("4", "11", "12", "14") -- only stripped
    # when mode="metro" and the code is "M"/"m" immediately followed by a
    # digit.
    assert normalise_line_name("M4", mode="metro") == "4"
    assert normalise_line_name("M14", mode="metro") == "14"
    # Letter-coded metro lines (Lyon A-D, Rennes a/b) were never
    # M-prefixed in the CSV and must not be touched.
    assert normalise_line_name("B", mode="metro") == "b"
    # No mode, or a different mode, keeps the old mode-unaware behaviour
    # (e.g. a literal "M4" bus/tram code must not be stripped).
    assert normalise_line_name("M4") == "m4"
    assert normalise_line_name("M4", mode="tram") == "m4"


def test_load_openings_rows_filters_by_network_substring(tmp_path) -> None:
    path = tmp_path / "openings.csv"
    path.write_text(
        "id,region,city,network,mode,line_2026,section_from,section_to\n"
        "A1,R,C,TBM (Bordeaux Métropole),tram,F,X,Y\n"
        "A2,R,C,TCL (SYTRAL Mobilités),tram,T6,X,Y\n",
        encoding="utf-8",
    )
    rows = load_openings_rows(path, "TBM")
    assert [row.opening_id for row in rows] == ["A1"]


def test_exact_match_by_route_short_name(tmp_path) -> None:
    root = tmp_path / "gtfs"
    _write_gtfs(
        root,
        routes=[("59", "A", "Tram A", "0")],
        stops=[("59", [("s1", "Stop One"), ("s2", "Stop Two")])],
    )
    connection = duckdb.connect()
    opening = OpeningRow("NAQ-99", "TBM", "tram", "A", "Stop One", "Stop Two")
    proposals = propose_route_matches(connection, root, [opening])

    assert len(proposals) == 1
    assert proposals[0].match_confidence == "exact"
    assert proposals[0].candidate_route_ids == ("59",)


def test_two_routes_for_the_same_corridor_are_both_included(tmp_path) -> None:
    # SNCF-style mission-code variants (L42/F42) of "the same" line 42.
    root = tmp_path / "gtfs"
    _write_gtfs(
        root,
        routes=[
            ("L42", "L42", "42. Le Verdon - Bordeaux", "2"),
            ("F42", "F42", "42. Le Verdon - Bordeaux", "2"),
        ],
        stops=[
            ("L42", [("s1", "Le Verdon"), ("s2", "Bordeaux")]),
            ("F42", [("s1", "Le Verdon"), ("s2", "Bordeaux")]),
        ],
    )
    connection = duckdb.connect()
    opening = OpeningRow(
        "NAQ-02", "TER", "rail", "TER 42 Bordeaux - Pointe-de-Grave", None, None
    )
    proposals = propose_route_matches(connection, root, [opening])

    assert proposals[0].match_confidence == "exact"
    assert proposals[0].candidate_route_ids == ("F42", "L42")


def test_metro_m_prefix_matches_the_bare_gtfs_short_name(tmp_path) -> None:
    # Real case (2026-10-16 fix): Paris metro line 14's GTFS
    # route_short_name is bare "14", but the openings CSV writes "M14".
    root = tmp_path / "gtfs"
    _write_gtfs(
        root,
        routes=[("IDFM:C01384", "14", "14", "1")],
        stops=[("IDFM:C01384", [("s1", "Olympiades"), ("s2", "Aéroport d'Orly")])],
    )
    connection = duckdb.connect()
    opening = OpeningRow("IDF-12", "RATP (IDFM)", "metro", "M14", None, None)
    proposals = propose_route_matches(connection, root, [opening])

    assert proposals[0].match_confidence == "exact"
    assert proposals[0].candidate_route_ids == ("IDFM:C01384",)


def test_metro_letter_codes_are_not_m_stripped(tmp_path) -> None:
    # Lyon metro B and Rennes metro b are already bare letter codes in
    # both the CSV and GTFS; the "M"-prefix fix must never touch them.
    root = tmp_path / "gtfs"
    _write_gtfs(
        root,
        routes=[("B", "B", "B - Perrache - Vaulx-en-Velin", "1")],
        stops=[("B", [("s1", "Charpennes"), ("s2", "Gare de Vénissieux")])],
    )
    connection = duckdb.connect()
    opening = OpeningRow("ARA-02", "TCL (SYTRAL Mobilités)", "metro", "B", None, None)
    proposals = propose_route_matches(connection, root, [opening])

    assert proposals[0].match_confidence == "exact"
    assert proposals[0].candidate_route_ids == ("B",)


def test_new_station_narrows_same_corridor_routes_to_those_calling_there(
    tmp_path,
) -> None:
    # Real case (section 5.6 point 2, 2026-10-16 fix): NAQ-02's new
    # station is only served by some of TER 42's lettered variants.
    root = tmp_path / "gtfs"
    _write_gtfs(
        root,
        routes=[
            ("421A", "421A", "42. Bordeaux - Pointe-de-Grave", "2"),
            ("421B", "421B", "42. Bordeaux - Pointe-de-Grave", "2"),
            ("421C", "421C", "42. Bordeaux - Pointe-de-Grave", "2"),
        ],
        stops=[
            ("421A", [("s1", "Bordeaux"), ("s2", "Le Bouscat-Sainte-Germaine")]),
            ("421B", [("s1", "Bordeaux"), ("s2", "Le Bouscat-Sainte-Germaine")]),
            # 421C is a semi-direct variant that skips the new station.
            ("421C", [("s1", "Bordeaux"), ("s3", "Le Verdon")]),
        ],
    )
    connection = duckdb.connect()
    opening = OpeningRow(
        "NAQ-02",
        "TER Nouvelle-Aquitaine",
        "rail",
        "TER 42 Bordeaux - Pointe-de-Grave",
        "Le Bouscat-Sainte-Germaine",
        None,
        change_type="new_station",
    )
    proposals = propose_route_matches(connection, root, [opening])

    assert proposals[0].match_confidence == "stop-confirmed"
    assert proposals[0].candidate_route_ids == ("421A", "421B")
    assert "421C" in proposals[0].notes


def test_extension_keeps_every_route_when_all_of_them_call_at_the_anchor(
    tmp_path,
) -> None:
    root = tmp_path / "gtfs"
    _write_gtfs(
        root,
        routes=[
            ("411A", "411A", "41. Bordeaux - Arcachon", "2"),
            ("411B", "411B", "41. Bordeaux - Arcachon", "2"),
        ],
        stops=[
            ("411A", [("s1", "Bordeaux"), ("s2", "Talence-Médoquine")]),
            ("411B", [("s1", "Bordeaux"), ("s2", "Talence-Médoquine")]),
        ],
    )
    connection = duckdb.connect()
    opening = OpeningRow(
        "NAQ-10",
        "TER Nouvelle-Aquitaine",
        "rail",
        "TER 41+ / 42",
        "Talence-Médoquine",
        None,
        change_type="extension",
    )
    proposals = propose_route_matches(connection, root, [opening])

    assert proposals[0].match_confidence == "exact"
    assert set(proposals[0].candidate_route_ids) == {"411A", "411B"}


def test_new_line_is_never_narrowed_by_the_new_station_extension_rule(
    tmp_path,
) -> None:
    # new_line/reopening drop a route by identity alone (section 5.6
    # point 4) -- unlike new_station/extension, every same-corridor
    # variant (a single shared route_long_name, as NAQ-02's "421A"/
    # "421B"/"421C" style match) still applies, even when a stop hint
    # would otherwise have excluded one of them.
    root = tmp_path / "gtfs"
    _write_gtfs(
        root,
        routes=[
            ("421A", "421A", "42. Bordeaux - Pointe-de-Grave", "2"),
            ("421B", "421B", "42. Bordeaux - Pointe-de-Grave", "2"),
            ("421C", "421C", "42. Bordeaux - Pointe-de-Grave", "2"),
        ],
        stops=[
            ("421A", [("s1", "Bordeaux"), ("s2", "Le Bouscat-Sainte-Germaine")]),
            ("421B", [("s1", "Bordeaux"), ("s2", "Le Bouscat-Sainte-Germaine")]),
            ("421C", [("s1", "Bordeaux"), ("s3", "Le Verdon")]),
        ],
    )
    connection = duckdb.connect()
    opening = OpeningRow(
        "NAQ-02",
        "TER Nouvelle-Aquitaine",
        "rail",
        "TER 42 Bordeaux - Pointe-de-Grave",
        "Le Bouscat-Sainte-Germaine",
        None,
        change_type="new_line",
    )
    proposals = propose_route_matches(connection, root, [opening])

    assert proposals[0].match_confidence == "exact"
    assert set(proposals[0].candidate_route_ids) == {"421A", "421B", "421C"}


def test_ambiguous_name_is_resolved_by_section_stop_hint(tmp_path) -> None:
    # Two different rail corridors coincidentally both named "C".
    root = tmp_path / "gtfs"
    _write_gtfs(
        root,
        routes=[
            ("railC1", "C", "Massy - Epinay - Versailles", "2"),
            ("railC2", "C", "Dourdan - Paris", "2"),
        ],
        stops=[
            ("railC1", [("s1", "Massy"), ("s2", "Epinay-sur-Orge")]),
            ("railC2", [("s3", "Dourdan"), ("s4", "Paris Austerlitz")]),
        ],
    )
    connection = duckdb.connect()
    opening = OpeningRow(
        "IDF-05", "SNCF", "rail", "RER C", "Massy", "Épinay-sur-Orge"
    )
    proposals = propose_route_matches(connection, root, [opening])

    assert proposals[0].match_confidence == "stop-confirmed"
    assert proposals[0].candidate_route_ids == ("railC1",)


def test_no_candidate_is_reported_as_none(tmp_path) -> None:
    root = tmp_path / "gtfs"
    _write_gtfs(
        root,
        routes=[("59", "A", "Tram A", "0")],
        stops=[("59", [("s1", "Stop One")])],
    )
    connection = duckdb.connect()
    opening = OpeningRow("X-1", "TBM", "tram", "Z", None, None)
    proposals = propose_route_matches(connection, root, [opening])

    assert proposals[0].match_confidence == "none"
    assert proposals[0].candidate_route_ids == ()


def test_stop_name_fallback_resolves_a_row_with_no_line_name_match(
    tmp_path,
) -> None:
    # Fix for IDF-17/GES-06/NAQ-03/PAC-05/OCC-05/OCC-13-style rows (section
    # 5.6 point 4, 2026-10-16 fix): the line name matches nothing at all,
    # but exactly one route of the same mode family serves both named
    # stops -- never guessed from a single hint, only accepted when both
    # are served by the one same route.
    root = tmp_path / "gtfs"
    _write_gtfs(
        root,
        routes=[
            ("BHNS-A", "A", "Some other corridor", "3"),
            ("BHNS-B", "Mystery", "Grand Périgueux corridor", "3"),
        ],
        stops=[
            ("BHNS-A", [("s1", "Unrelated stop")]),
            (
                "BHNS-B",
                [("s2", "Coulounieix-Chamiers"), ("s3", "Boulazac Isle Manoire")],
            ),
        ],
    )
    connection = duckdb.connect()
    opening = OpeningRow(
        "NAQ-03",
        "Péribus (Grand Périgueux)",
        "bhns",
        "BHNS Est-Ouest",
        "Coulounieix-Chamiers",
        "Boulazac Isle Manoire",
    )
    proposals = propose_route_matches(connection, root, [opening])

    assert proposals[0].match_confidence == "stop-confirmed"
    assert proposals[0].candidate_route_ids == ("BHNS-B",)
    assert "stop names alone" in proposals[0].notes


def test_stop_name_fallback_refuses_to_guess_between_two_matching_routes(
    tmp_path,
) -> None:
    # Both section_from and section_to are each served by stops of more
    # than one route of the family, so the fallback must not guess --
    # the row stays "none"/unresolved, to be logged, not applied.
    root = tmp_path / "gtfs"
    _write_gtfs(
        root,
        routes=[
            ("BUS-1", "1", "Corridor one", "3"),
            ("BUS-2", "2", "Corridor two", "3"),
        ],
        stops=[
            ("BUS-1", [("s1", "Viry-Chatillon"), ("s2", "Corbeil-Essonnes")]),
            ("BUS-2", [("s3", "Viry-Chatillon"), ("s4", "Corbeil-Essonnes")]),
        ],
    )
    connection = duckdb.connect()
    opening = OpeningRow(
        "IDF-17",
        "Keolis Tisse (IDFM)",
        "bhns",
        "Tzen 4",
        "Viry-Chatillon",
        "Corbeil-Essonnes",
    )
    proposals = propose_route_matches(connection, root, [opening])

    assert proposals[0].match_confidence == "none"
    assert proposals[0].candidate_route_ids == ()


def test_stop_name_fallback_also_resolves_an_ambiguous_name_match(
    tmp_path,
) -> None:
    # The fallback applies after the ordinary name-based pipeline leaves a
    # row "ambiguous" too, not only "none": within the name-matched pool
    # alone, Tzen1 also matches one hint (any-hint narrowing keeps both,
    # "ambiguous"), but only Tzen4 calls at *both* named stops, which the
    # whole-family, every-hint fallback can tell apart.
    root = tmp_path / "gtfs"
    _write_gtfs(
        root,
        routes=[
            ("TZEN1", "Tzen1", "Corridor one", "3"),
            ("TZEN4", "Tzen4", "Corridor four", "3"),
            ("OTHER", "Other", "Unrelated corridor", "3"),
        ],
        stops=[
            ("TZEN1", [("s1", "Viry-Chatillon")]),
            ("TZEN4", [("s2", "Viry-Chatillon"), ("s3", "Corbeil-Essonnes")]),
            ("OTHER", [("s4", "Completely unrelated stop")]),
        ],
    )
    connection = duckdb.connect()
    opening = OpeningRow(
        "IDF-17",
        "Keolis Tisse (IDFM)",
        "bhns",
        "Tzen 4",
        "Viry-Chatillon",
        "Corbeil-Essonnes",
    )
    proposals = propose_route_matches(connection, root, [opening])

    # Name-based matching alone would have left this "ambiguous"
    # (Tzen1/Tzen4 share the "tzen" prefix); the stop-name fallback
    # narrows it to the one route serving both named stops.
    assert proposals[0].match_confidence == "stop-confirmed"
    assert proposals[0].candidate_route_ids == ("TZEN4",)


def test_single_letter_code_matches_numbered_circular_variants_by_prefix(
    tmp_path,
) -> None:
    # "H1"/"H2" (circular directions of Express H) share the code "H" as a
    # prefix; an unrelated route merely containing "h" must not match.
    root = tmp_path / "gtfs"
    _write_gtfs(
        root,
        routes=[
            ("911", "H1", "Bus Express H1", "3"),
            ("912", "H2", "Bus Express H2", "3"),
            ("97", "97", "Night bus 97", "3"),
        ],
        stops=[
            ("911", [("s1", "Cenon Gare")]),
            ("912", [("s2", "Cenon Gare")]),
            ("97", [("s3", "Some stop")]),
        ],
    )
    connection = duckdb.connect()
    opening = OpeningRow("NAQ-11", "TBM", "bhns", "H (Bus Express)", None, None)
    proposals = propose_route_matches(connection, root, [opening])

    # Both circular variants are found via the "H" prefix (and reported,
    # even without a disambiguating hint); the unrelated "97" line never
    # enters the pool at all.
    assert set(proposals[0].candidate_route_ids) == {"911", "912"}


def test_mode_family_filter_excludes_wrong_route_type(tmp_path) -> None:
    root = tmp_path / "gtfs"
    _write_gtfs(
        root,
        routes=[
            ("bus-A", "A", "Bus A", "3"),
            ("tram-A", "A", "Tram A", "0"),
        ],
        stops=[
            ("bus-A", [("s1", "Stop One")]),
            ("tram-A", [("s2", "Stop Two")]),
        ],
    )
    connection = duckdb.connect()
    opening = OpeningRow("NAQ-12", "TBM", "tram", "A", None, None)
    proposals = propose_route_matches(connection, root, [opening])

    assert proposals[0].match_confidence == "exact"
    assert proposals[0].candidate_route_ids == ("tram-A",)


def test_write_mapping_csv_merges_without_discarding_other_networks(
    tmp_path,
) -> None:
    output = tmp_path / "mapping.csv"
    root = tmp_path / "gtfs"
    _write_gtfs(
        root,
        routes=[("59", "A", "Tram A", "0")],
        stops=[("59", [("s1", "Stop One")])],
    )
    connection = duckdb.connect()
    first = propose_route_matches(
        connection, root, [OpeningRow("A-1", "TBM", "tram", "A", None, None)]
    )
    write_mapping_csv(output, first)

    second = propose_route_matches(
        connection, root, [OpeningRow("A-2", "TBM", "tram", "Z", None, None)]
    )
    write_mapping_csv(output, second)

    with output.open(encoding="utf-8", newline="") as stream:
        rows = {row["opening_id"]: row for row in csv.DictReader(stream)}
    assert set(rows) == {"A-1", "A-2"}
    assert rows["A-1"]["match_confidence"] == "exact"
    assert rows["A-2"]["match_confidence"] == "none"


def test_run_mapping_grouped_resolves_each_row_against_its_own_mode(
    tmp_path,
) -> None:
    # The "TER Occitanie (liO)" case: a rail row and a bus row sharing one
    # network must resolve against two different GTFS resources, and
    # neither run may overwrite the other's result for a different row.
    rail_root = tmp_path / "rail_gtfs"
    _write_gtfs(
        rail_root,
        routes=[("TER42", "42", "TER 42", "2")],
        stops=[("TER42", [("s1", "Stop One")])],
    )
    bus_root = tmp_path / "bus_gtfs"
    _write_gtfs(
        bus_root,
        routes=[("coachA", "A", "Coach A", "3")],
        stops=[("coachA", [("s2", "Stop Two")])],
    )
    openings = tmp_path / "openings.csv"
    openings.write_text(
        "id,region,city,network,mode,line_2026,section_from,section_to\n"
        "O1,R,C,liO,rail,42,,\n"
        "O2,R,C,liO,bus,A,,\n",
        encoding="utf-8",
    )
    output = tmp_path / "mapping.csv"

    proposals = run_mapping_grouped(
        openings, "liO", {"rail": rail_root, "bus": bus_root}, output
    )

    by_id = {p.opening_id: p for p in proposals}
    assert by_id["O1"].candidate_route_ids == ("TER42",)
    assert by_id["O1"].match_confidence == "exact"
    assert by_id["O2"].candidate_route_ids == ("coachA",)
    assert by_id["O2"].match_confidence == "exact"


def test_run_mapping_grouped_logs_a_mode_with_no_configured_resource(
    tmp_path,
) -> None:
    rail_root = tmp_path / "rail_gtfs"
    _write_gtfs(
        rail_root,
        routes=[("TER42", "42", "TER 42", "2")],
        stops=[("TER42", [("s1", "Stop One")])],
    )
    openings = tmp_path / "openings.csv"
    openings.write_text(
        "id,region,city,network,mode,line_2026,section_from,section_to\n"
        "O1,R,C,liO,rail,42,,\n"
        "O2,R,C,liO,bus,A,,\n",
        encoding="utf-8",
    )
    output = tmp_path / "mapping.csv"

    proposals = run_mapping_grouped(openings, "liO", {"rail": rail_root}, output)

    by_id = {p.opening_id: p for p in proposals}
    assert by_id["O1"].match_confidence == "exact"
    assert by_id["O2"].match_confidence == "none"
    assert "no configured resource" in by_id["O2"].notes


_OPENINGS_CSV_HEADER = (
    "id,region,city,network,mode,line_2026,change_type,section_from,"
    "section_to,state_2022,state_2024,confidence"
)


def _write_openings_csv(path: Path, rows: list[str]) -> None:
    path.write_text(
        "\n".join([_OPENINGS_CSV_HEADER, *rows]) + "\n", encoding="utf-8"
    )


def _write_mapping_row(
    path: Path,
    opening_id: str,
    match_confidence: str,
    candidate_route_ids: str = "",
) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
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
            ]
        )
        writer.writerow(
            [opening_id, "TBM", "tram", "F", "", "", candidate_route_ids, "",
             match_confidence, "test note"]
        )


def test_apply_openings_matches_applies_exact_high_confidence_rows(
    tmp_path,
) -> None:
    openings = tmp_path / "openings.csv"
    _write_openings_csv(
        openings,
        ["A-1,R,C,TBM,tram,F,extension,X,Y,remove,keep,high"],
    )
    mapping = tmp_path / "mapping.csv"
    _write_mapping_row(mapping, "A-1", "exact", "164")

    result = apply_openings_matches(openings, mapping)

    assert len(result.applied) == 1
    change = result.applied[0]
    assert change.route_id == "164"
    assert change.change_type == "extension"
    assert change.state_2022 == "remove"
    assert change.state_2024 == "keep"
    # extension + remove -> cut, never drop (section 5.6 point 2).
    assert change.instruction_at(date(2022, 1, 1)) == "cut"
    assert result.warnings == ()
    assert result.not_applied_by_design == {}
    assert result.closed_before_2026 == ()


def test_ambiguous_row_is_a_warning_and_low_confidence_row_is_info(
    tmp_path,
) -> None:
    openings = tmp_path / "openings.csv"
    _write_openings_csv(
        openings,
        [
            "A-1,R,C,TBM,bhns,H,new_line,X,Y,remove,remove,medium",
            "A-2,R,C,TBM,tram,Z,new_line,X,Y,remove,remove,low",
        ],
    )
    mapping = tmp_path / "mapping.csv"
    _write_mapping_row(mapping, "A-1", "ambiguous", "911|912")

    result = apply_openings_matches(openings, mapping)

    assert result.applied == ()
    # A-1 carries a real remove instruction (new_line) whose match failed:
    # a genuine gap, logged at WARNING.
    assert len(result.warnings) == 1
    assert "A-1" in result.warnings[0] and "ambiguous" in result.warnings[0]
    # A-2 is excluded by design (low CSV confidence): counted, not warned.
    assert result.not_applied_by_design == {"low_confidence": 1}


def test_apply_openings_matches_uses_configured_confidence_thresholds(
    tmp_path,
) -> None:
    """Changing the configured thresholds changes what is applied.

    No confidence/match_confidence value is hardcoded in
    ``apply_openings_matches`` -- it must be driven entirely by
    ``national_policy.openings_list.include_row_confidence``/
    ``apply_match_confidence`` (``config/gtfs_rebuild.yaml``), exactly as
    read by ``mobgrid.pt.cli`` and rendered by ``report.py``.
    """
    openings = tmp_path / "openings.csv"
    _write_openings_csv(
        openings,
        ["A-1,R,C,TBM,tram,F,extension,X,Y,remove,keep,medium"],
    )
    mapping = tmp_path / "mapping.csv"
    _write_mapping_row(mapping, "A-1", "stop-confirmed", "164")

    # The configured policy today (high/medium, exact/stop-confirmed)
    # applies this medium-confidence, stop-confirmed row.
    default_result = apply_openings_matches(
        openings,
        mapping,
        include_row_confidence=("high", "medium"),
        apply_match_confidence=("exact", "stop-confirmed"),
    )
    assert len(default_result.applied) == 1

    # Tightening the row-confidence threshold to high-only (a config
    # change, not a code change) must reject the same medium-confidence
    # row instead.
    stricter_result = apply_openings_matches(
        openings,
        mapping,
        include_row_confidence=("high",),
        apply_match_confidence=("exact", "stop-confirmed"),
    )
    assert stricter_result.applied == ()
    assert stricter_result.warnings == ()
    assert stricter_result.not_applied_by_design == {"low_confidence": 1}

    # Tightening the match-confidence threshold to exact-only must
    # likewise reject a stop-confirmed match -- a genuine remove
    # instruction that failed to match, so this is a WARNING, not a count.
    exact_only_result = apply_openings_matches(
        openings,
        mapping,
        include_row_confidence=("high", "medium"),
        apply_match_confidence=("exact",),
    )
    assert exact_only_result.applied == ()
    assert len(exact_only_result.warnings) == 1
    assert "match_confidence='stop-confirmed'" in exact_only_result.warnings[0]
    assert exact_only_result.not_applied_by_design == {}


def test_apply_openings_matches_leaves_out_closed_before_2026_rows(
    tmp_path,
) -> None:
    openings = tmp_path / "openings.csv"
    _write_openings_csv(
        openings,
        ["A-1,R,C,TER,rail,67,closure,X,Y,add,add,medium"],
    )
    mapping = tmp_path / "mapping.csv"
    mapping.write_text(
        "opening_id,network,mode,line_2026,section_from,section_to,"
        "candidate_route_ids,candidate_refs,match_confidence,notes\n",
        encoding="utf-8",
    )

    result = apply_openings_matches(openings, mapping)

    assert result.applied == ()
    assert result.warnings == ()
    assert result.not_applied_by_design == {}
    assert len(result.closed_before_2026) == 1
    assert "A-1" in result.closed_before_2026[0]
    assert "closed before 2026" in result.closed_before_2026[0]


def test_apply_openings_matches_counts_rows_with_no_instruction_as_info(
    tmp_path,
) -> None:
    openings = tmp_path / "openings.csv"
    _write_openings_csv(
        openings,
        [
            # restructuring: never gives an instruction, regardless of state.
            "A-1,R,C,TBM,tram,A,restructuring,X,Y,modify,modify,high",
            # new_line but state keep/keep (not yet open): nothing to
            # remove yet, no match attempted.
            "A-2,R,C,TBM,tram,B,new_line,X,Y,keep,keep,high",
        ],
    )
    mapping = tmp_path / "mapping.csv"
    mapping.write_text(
        "opening_id,network,mode,line_2026,section_from,section_to,"
        "candidate_route_ids,candidate_refs,match_confidence,notes\n",
        encoding="utf-8",
    )

    result = apply_openings_matches(openings, mapping)

    assert result.applied == ()
    assert result.warnings == ()
    assert result.not_applied_by_design == {
        "non_instruction_change_type": 1,
        "no_remove_state": 1,
    }


def test_apply_openings_matches_allows_a_multi_route_extension_match(
    tmp_path,
) -> None:
    # The real motivating case: NAQ-02's new_station row matches 8
    # directional/numbered variants of TER 42; every one that calls at
    # the new station is applied, not just the first (section 5.6
    # point 2, 2026-10-16 fix). The mapping CSV is assumed already
    # narrowed by ``propose_route_matches`` to the calling routes only.
    openings = tmp_path / "openings.csv"
    _write_openings_csv(
        openings,
        ["A-1,R,C,TER,rail,42,new_station,X,,remove,keep,high"],
    )
    mapping = tmp_path / "mapping.csv"
    _write_mapping_row(mapping, "A-1", "exact", "421A|421B|421C")

    result = apply_openings_matches(openings, mapping)

    assert result.warnings == ()
    assert {change.route_id for change in result.applied} == {
        "421A", "421B", "421C",
    }
    assert all(
        change.instruction_at(date(2022, 1, 1)) == "new_station"
        for change in result.applied
    )


def test_apply_openings_matches_allows_a_multi_route_new_line_match(tmp_path) -> None:
    # The real motivating case: Bordeaux's circular Bus Express H row
    # (NAQ-11) matches both numbered directions, H1 (911) and H2 (912);
    # dropping both is safe since a new_line instruction needs only route
    # identity, not a single route's stop pattern (section 5.6 point 4).
    openings = tmp_path / "openings.csv"
    _write_openings_csv(
        openings,
        ["A-1,R,C,TBM,bhns,H,new_line,X,Y,remove,remove,medium"],
    )
    mapping = tmp_path / "mapping.csv"
    _write_mapping_row(mapping, "A-1", "exact", "911|912")

    result = apply_openings_matches(openings, mapping)

    assert result.warnings == ()
    assert {change.route_id for change in result.applied} == {"911", "912"}
    assert all(
        change.instruction_at(date(2022, 1, 1)) == "drop"
        for change in result.applied
    )


def test_row_counts_sum_to_total_rows_and_distinguish_route_level_edits(
    tmp_path,
) -> None:
    # 2026-10-16 bookkeeping fix: one row of each of the six categories,
    # plus a multi-route row, so `len(result.applied)` (route-level) and
    # `row_counts()["applied"]` (row-level) differ on purpose.
    openings = tmp_path / "openings.csv"
    _write_openings_csv(
        openings,
        [
            # applied: one row, two routes.
            "A-1,R,C,TBM,bhns,H,new_line,X,Y,remove,remove,medium",
            # remove instruction that fails to match -> warning.
            "A-2,R,C,TBM,tram,Z,new_line,X,Y,remove,remove,high",
            # low confidence -> by design.
            "A-3,R,C,TBM,tram,Z,new_line,X,Y,remove,remove,low",
            # no remove state (planned, not yet open) -> by design.
            "A-4,R,C,TBM,tram,Z,new_line,X,Y,keep,keep,high",
            # non-instruction change_type -> by design.
            "A-5,R,C,TBM,tram,Z,restructuring,X,Y,modify,modify,high",
            # closed before 2026.
            "A-6,R,C,TBM,tram,Z,closure,X,Y,add,add,high",
        ],
    )
    mapping = tmp_path / "mapping.csv"
    _write_mapping_row(mapping, "A-1", "exact", "911|912")

    result = apply_openings_matches(openings, mapping)

    assert len(result.applied) == 2  # route-level: 911 and 912
    assert result.applied_opening_ids == {"A-1"}  # row-level: one row
    assert len(result.warnings) == 1
    assert result.not_applied_by_design == {
        "low_confidence": 1,
        "no_remove_state": 1,
        "non_instruction_change_type": 1,
    }
    assert len(result.closed_before_2026) == 1
    counts = result.row_counts()
    assert counts == {
        "low_confidence": 1,
        "no_remove_state": 1,
        "non_instruction_change_type": 1,
        "applied": 1,
        "remove_not_applied": 1,
        "closed_before_2026": 1,
    }
    assert sum(counts.values()) == 6  # one per CSV row, not 7 (route-level)


def test_real_openings_list_row_counts_reconcile_to_the_total() -> None:
    """Acceptance test on the real committed CSV/mapping/config.

    Every row of the real openings list falls into exactly one of the
    six categories, with no new run needed (2026-10-16 bookkeeping fix):
    this is the check ``apply_openings_matches`` itself performs before
    returning, exercised here against the real committed data.
    """
    config = load_gtfs_rebuild_config(ROOT / "config" / "gtfs_rebuild.yaml")
    openings_list = config.national_policy.openings_list
    openings_csv = ROOT / "config" / "French transit openings 2022 to 2026.csv"
    total_rows = len(load_openings_rows(openings_csv, ""))
    result = apply_openings_matches(
        ROOT / "config" / "French transit openings 2022 to 2026.csv",
        ROOT / "config" / "pt_openings_mapping.csv",
        include_row_confidence=openings_list.include_row_confidence,
        apply_match_confidence=openings_list.apply_match_confidence,
    )
    assert sum(result.row_counts().values()) == total_rows
    # Route-level edits (several per row for a multi-route match) must be
    # at least as many as the rows actually applied, never fewer.
    assert len(result.applied) >= len(result.applied_opening_ids)


def test_bordeaux_real_rows_match_the_documented_outcomes() -> None:
    """Acceptance test on the real committed CSV/mapping (section 5.6 point 4).

    1 Jan 2022: A, C, E kept; F cut at Carrefour des Quatre Chemins
    (NAQ-01); G and H (both numbered directions) dropped. 1 Jan 2024: A,
    C, E kept; F has no active openings-list instruction (falls through
    to the tram automatic rule); G and H dropped. Reads only committed
    config files (the openings CSV and its mapping), never
    ``data/raw``/``data/interim``, so it is fully isolated and
    deterministic.
    """
    result = apply_openings_matches(
        ROOT / "config" / "French transit openings 2022 to 2026.csv",
        ROOT / "config" / "pt_openings_mapping.csv",
    )
    catalogue = PtChangeCatalogue(from_openings=list(result.applied))
    config = load_gtfs_rebuild_config(ROOT / "config" / "gtfs_rebuild.yaml")
    network_resource_ids = build_network_resource_ids(config)
    mode_split_resource_ids = (
        config.national_policy.openings_list.mode_split_network_resource_ids
    )
    network = "TBM (Bordeaux Métropole)"
    resource_id = network_resource_ids[network]
    d2022, d2024 = date(2022, 1, 1), date(2024, 1, 1)
    removed_2022 = {
        route
        for net, route in catalogue.removed_route_keys(
            d2022,
            network_resource_ids=network_resource_ids,
            mode_split_network_resource_ids=mode_split_resource_ids,
        )
        if net == resource_id
    }
    removed_2024 = {
        route
        for net, route in catalogue.removed_route_keys(
            d2024,
            network_resource_ids=network_resource_ids,
            mode_split_network_resource_ids=mode_split_resource_ids,
        )
        if net == resource_id
    }

    for route_id in ("59", "61", "163"):  # A, C, E
        assert route_id not in removed_2022
        assert route_id not in removed_2024

    assert "164" not in removed_2022  # F: cut, never dropped
    assert "164" not in removed_2024

    for route_id in ("901", "911", "912"):  # G, H1, H2
        assert route_id in removed_2022
        assert route_id in removed_2024

    edits_2022 = collect_edit_specs(catalogue, d2022)
    f_edits_2022 = edits_2022.get((network, "164"), [])
    assert len(f_edits_2022) == 1
    assert f_edits_2022[0].kind == "cut"
    assert "Quatre Chemins" in f_edits_2022[0].anchor_from

    edits_2024 = collect_edit_specs(catalogue, d2024)
    assert (network, "164") not in edits_2024


def test_resolve_and_extract_never_attempts_a_network_call(tmp_path) -> None:
    # A clean sweep of this module's own source confirms there is no
    # import of a network client at all; this import-level check is a
    # stronger, static guarantee than any single test run.
    import mobgrid.pt.pt_openings as pt_openings_module

    assert "httpx" not in dir(pt_openings_module)
    assert "requests" not in dir(pt_openings_module)


def test_resolve_and_extract_reads_an_already_downloaded_feed_offline(
    tmp_path,
) -> None:
    root = tmp_path / "gtfs"
    _write_gtfs(
        root.parent / "already_downloaded",
        routes=[("59", "A", "Tram A", "0")],
        stops=[("59", [("s1", "Stop One")])],
    )
    # _write_gtfs writes CSVs, not a zip; build one from them for this test.
    import zipfile

    zip_path = tmp_path / "feed.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        for name in ("routes.txt", "trips.txt", "stop_times.txt", "stops.txt"):
            archive.write(root.parent / "already_downloaded" / name, name)

    inventory = tmp_path / "gtfs_inventory.csv"
    with inventory.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["resource_id", "local_path"])
        writer.writerow(["83024", str(zip_path)])

    table_dir = resolve_and_extract(inventory, 83024, tmp_path / "scratch")
    assert (table_dir / "routes.txt").is_file()


def test_resolve_and_extract_raises_a_clear_error_when_not_downloaded(
    tmp_path,
) -> None:
    inventory = tmp_path / "gtfs_inventory.csv"
    with inventory.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["resource_id", "local_path"])
        writer.writerow(["99999", str(tmp_path / "not_downloaded.zip")])

    try:
        resolve_and_extract(inventory, 99999, tmp_path / "scratch")
    except FileNotFoundError as error:
        assert "not downloaded locally" in str(error)
        assert "never downloads" in str(error)
    else:
        raise AssertionError("expected a FileNotFoundError")

