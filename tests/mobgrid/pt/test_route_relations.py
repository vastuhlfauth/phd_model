"""Synthetic acceptance tests for relation-based GTFS rebuilding (section 5.6)."""

from mobgrid.pt.route_relations import (
    OSMRelation,
    OSMWay,
    RoutePattern,
    choose_main_patterns,
    classify_network,
    evaluate_route,
    match_route,
    normalise_ref,
    qualify_fallback_stops,
)


def _pattern(
    *,
    route_id: str = "E",
    short_name: str = "E",
    long_name: str = "Gare - Aeroport",
    mode: str = "tram",
    stops: tuple[tuple[float, float], ...] = ((0.0, 0.0), (100.0, 0.0)),
    trip_count: int = 10,
    pattern_id: str = "p",
    agency_name: str = "TBM",
) -> RoutePattern:
    return RoutePattern(
        pattern_id,
        route_id,
        short_name,
        long_name,
        mode,
        agency_name,
        trip_count,
        stops,
    )


def _way(
    *points: tuple[float, float],
    railway: str | None = "tram",
    construction: str | None = None,
) -> OSMWay:
    return OSMWay(points, railway=railway, construction=construction)


def _relation(
    relation_id: int,
    *,
    ref: str | None = "A",
    name: str | None = "Ligne A",
    mode: str = "tram",
    operator: str | None = "TBM",
    ways: tuple[OSMWay, ...] = (_way((-10.0, 0.0), (110.0, 0.0)),),
    stops: tuple[tuple[float, float], ...] = (),
) -> OSMRelation:
    return OSMRelation(
        relation_id, ref, name, None, operator, mode, stops, ways
    )


def test_name_match_normalises_ref_and_requires_local_way() -> None:
    pattern = _pattern(short_name=" Ligne T A ")
    nearby = _relation(1, ref="a")
    remote = _relation(
        2, ref="A", ways=(_way((10_000.0, 0.0), (11_000.0, 0.0)),)
    )
    match = match_route(pattern, [nearby, remote], r_m=25, geometry_share=0.5)
    assert normalise_ref(" Ligne T A ") == "a"
    assert match.pass_name == "name"
    assert match.relation_ids == (1,)


def test_name_tie_uses_network_or_operator() -> None:
    pattern = _pattern(short_name="A", agency_name="TBM")
    wrong = _relation(1, operator="Other")
    right = _relation(2, operator="TBM")
    match = match_route(pattern, [wrong, right], r_m=25, geometry_share=0.5)
    assert match.relation_ids == (2,)


def test_geometry_match_keeps_renamed_routes_on_old_tracks() -> None:
    old_a = _relation(1, ref="A", name="Tram A")
    for route_name in ("E", "F"):
        match = match_route(
            _pattern(short_name=route_name),
            [old_a],
            r_m=25,
            geometry_share=0.7,
        )
        assert match.pass_name == "geometry"
        assert match.relation_ids == (1,)
        assert match.covered_share == 1.0


def test_fixed_guideway_ignores_construction_ways_and_premapped_stops() -> None:
    relation = _relation(
        1,
        stops=((0.0, 0.0), (100.0, 0.0)),
        ways=(
            _way(
                (-10.0, 0.0),
                (110.0, 0.0),
                railway="construction",
                construction="tram",
            ),
        ),
    )
    result = evaluate_route(
        _pattern(), (relation,), match_pass="name", r_m=25, k=2, theta=0.5
    )
    assert result.outcome == "dropped"
    assert result.covered_share == 0.0


def test_fixed_guideway_cuts_ends_before_applying_theta() -> None:
    relation = _relation(
        1,
        ways=(_way((-5.0, 0.0), (105.0, 0.0)),),
    )
    pattern = _pattern(
        stops=(
            (0.0, 0.0),
            (100.0, 0.0),
            (200.0, 0.0),
            (300.0, 0.0),
        )
    )
    result = evaluate_route(
        pattern, (relation,), match_pass="name", r_m=25, k=2, theta=0.8
    )
    assert result.outcome == "cut"
    assert (result.start_index, result.end_index) == (0, 1)
    assert result.covered_share == 1.0


def test_bus_and_ferry_are_never_cut() -> None:
    for mode in ("bus", "ferry"):
        relation = _relation(
            1,
            mode=mode,
            ways=(_way((-5.0, 0.0), (105.0, 0.0), railway=None),),
        )
        pattern = _pattern(
            mode=mode,
            stops=((0.0, 0.0), (100.0, 0.0), (200.0, 0.0)),
        )
        result = evaluate_route(
            pattern, (relation,), match_pass="name", r_m=25, k=1, theta=0.8
        )
        assert result.outcome == "dropped"


def test_main_pattern_uses_most_reference_date_trips() -> None:
    patterns = [
        _pattern(pattern_id="minor", trip_count=2),
        _pattern(pattern_id="main", trip_count=12),
    ]
    assert choose_main_patterns(patterns)["E"].pattern_id == "main"


def test_low_relation_coverage_makes_whole_network_not_testable() -> None:
    assert classify_network(1, 3) == "not-testable"
    assert classify_network(1, 2) == "testable"


def test_fixed_guideway_fallback_requires_in_service_same_mode_track() -> None:
    stops = ((0.0, 0.0),)
    construction = _relation(
        1,
        ways=(_way((-10.0, 0.0), (10.0, 0.0), construction="tram"),),
    )
    assert not qualify_fallback_stops(stops, "tram", [construction], 25)
    service = _relation(2)
    qualified = qualify_fallback_stops(stops, "tram", [service], 25)
    result = evaluate_route(
        _pattern(),
        (),
        match_pass=None,
        r_m=25,
        k=2,
        theta=0.5,
        fallback_stops=qualified,
    )
    assert result.outcome == "kept"
