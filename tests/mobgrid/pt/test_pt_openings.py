"""Tests for the PT-openings-to-GTFS-route proposal tool (2026-10-15)."""

from __future__ import annotations

from pathlib import Path

import duckdb
from mobgrid.pt.pt_openings import (
    OpeningRow,
    load_openings_rows,
    normalise_line_name,
    propose_route_matches,
    write_mapping_csv,
)


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

    import csv

    with output.open(encoding="utf-8", newline="") as stream:
        rows = {row["opening_id"]: row for row in csv.DictReader(stream)}
    assert set(rows) == {"A-1", "A-2"}
    assert rows["A-1"]["match_confidence"] == "exact"
    assert rows["A-2"]["match_confidence"] == "none"
