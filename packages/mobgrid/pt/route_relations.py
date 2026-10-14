"""Name-first OSM relation matching for rebuilding historical GTFS routes."""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Literal

TransportMode = Literal["bus", "tram", "metro", "rail", "ferry"]
MatchPass = Literal["name", "geometry"] | None
RouteOutcome = Literal[
    "kept", "kept-renamed", "cut", "dropped", "not-testable"
]
_FIXED_MODES = frozenset(("tram", "metro", "rail"))


@dataclass(frozen=True)
class OSMWay:
    """One relation-member way in EPSG:3035 metres."""

    points: tuple[tuple[float, float], ...]
    railway: str | None = None
    highway: str | None = None
    construction: str | None = None
    lifecycle: bool = False


@dataclass(frozen=True)
class OSMRelation:
    """The matching fields and spatial members of one OSM route relation."""

    relation_id: int
    ref: str | None
    name: str | None
    network: str | None
    operator: str | None
    mode: TransportMode
    stops: tuple[tuple[float, float], ...]
    ways: tuple[OSMWay, ...]
    bbox: tuple[float, float, float, float] | None = field(
        init=False, repr=False
    )

    def __post_init__(self) -> None:
        points = [point for way in self.ways for point in way.points]
        bbox = (
            (
                min(point[0] for point in points),
                min(point[1] for point in points),
                max(point[0] for point in points),
                max(point[1] for point in points),
            )
            if points
            else None
        )
        object.__setattr__(self, "bbox", bbox)


@dataclass(frozen=True)
class RoutePattern:
    """One GTFS route pattern on the configured reference date."""

    pattern_id: str
    route_id: str
    short_name: str | None
    long_name: str | None
    mode: TransportMode
    agency_name: str | None
    trip_count: int
    stops: tuple[tuple[float, float], ...]
    is_bhns: bool = False


@dataclass(frozen=True)
class RelationMatch:
    """Selected relation set and matching evidence for one main pattern."""

    pass_name: MatchPass
    relation_ids: tuple[int, ...]
    relation_refs: tuple[str, ...]
    covered_share: float


@dataclass(frozen=True)
class RouteResult:
    """Spatial verification result for one route's main pattern."""

    route_id: str
    outcome: RouteOutcome
    match_pass: MatchPass
    relation_ids: tuple[int, ...]
    relation_refs: tuple[str, ...]
    n: int
    covered: int
    covered_share: float
    start_index: int
    end_index: int


def _normalise_text(value: str | None) -> str:
    if not value:
        return ""
    ascii_value = unicodedata.normalize("NFKD", value).encode(
        "ascii", "ignore"
    ).decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_value.casefold())


def normalise_ref(value: str | None) -> str:
    """Normalise a line ref, including common T/M/L and ``Ligne`` prefixes."""
    text = unicodedata.normalize("NFKD", value or "").encode(
        "ascii", "ignore"
    ).decode("ascii")
    text = re.sub(r"^\s*(?:ligne|line)\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*[tml]\s*[-.:]?\s*(?=[a-z0-9])", "", text, flags=re.I)
    return re.sub(r"[^a-z0-9]+", "", text.casefold())


_BHNS_KEYWORDS = ("express", "bhns", "liane", "chronobus")


def classify_bhns(
    short_name: str | None,
    long_name: str | None,
    description: str | None = None,
) -> bool:
    """Identify BHNS/express bus routes from their name or description.

    Matches ``Express``, ``BHNS``, ``Lianes``/``Liane`` and ``Chronobus``
    (case- and diacritics-insensitive) in the short name, long name or GTFS
    ``route_desc``; these routes are verified like trams (section 5.6 point
    2 of the 2026-10-14 decision), not with the plain bus kept/dropped rule.
    """
    haystack = _normalise_text(
        " ".join(value for value in (short_name, long_name, description) if value)
    )
    return any(keyword in haystack for keyword in _BHNS_KEYWORDS)


def _point_segment_distance(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    px, py = point
    ax, ay = start
    bx, by = end
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _point_way_distance(point: tuple[float, float], way: OSMWay) -> float:
    if not way.points:
        return math.inf
    if len(way.points) == 1:
        return math.dist(point, way.points[0])
    return min(
        _point_segment_distance(point, start, end)
        for start, end in zip(way.points, way.points[1:])
    )


def _way_in_service(way: OSMWay, mode: TransportMode) -> bool:
    if mode not in _FIXED_MODES:
        return True
    if way.lifecycle or way.construction:
        return False
    allowed = {
        "tram": {"tram", "light_rail"},
        "metro": {"subway"},
        "rail": {"rail"},
    }[mode]
    return way.railway in allowed


def _coverage_flags(
    pattern: RoutePattern, relations: tuple[OSMRelation, ...], r_m: float
) -> tuple[bool, ...]:
    ways = tuple(
        way
        for relation in relations
        for way in relation.ways
        if _way_in_service(way, pattern.mode)
    )
    member_stops = (
        ()
        if pattern.mode in _FIXED_MODES
        else tuple(stop for relation in relations for stop in relation.stops)
    )
    return tuple(
        any(_point_way_distance(stop, way) <= r_m for way in ways)
        or any(math.dist(stop, member_stop) <= r_m for member_stop in member_stops)
        for stop in pattern.stops
    )


def _share(flags: tuple[bool, ...]) -> float:
    return sum(flags) / len(flags) if flags else 0.0


def _relation_is_local(pattern: RoutePattern, relation: OSMRelation) -> bool:
    if relation.bbox is None:
        return False
    min_x, min_y, max_x, max_y = relation.bbox
    if not any(
        min_x - 1_000 <= x <= max_x + 1_000
        and min_y - 1_000 <= y <= max_y + 1_000
        for x, y in pattern.stops
    ):
        return False
    return any(
        _point_way_distance(stop, way) <= 1_000
        for stop in pattern.stops
        for way in relation.ways
    )


def _affiliation_score(pattern: RoutePattern, relation: OSMRelation) -> int:
    agency = _normalise_text(pattern.agency_name)
    if not agency:
        return 0
    return max(
        int(bool(value) and (value in agency or agency in value))
        for value in (
            _normalise_text(relation.network),
            _normalise_text(relation.operator),
        )
    )


def _name_matches(pattern: RoutePattern, relation: OSMRelation) -> bool:
    short_name = normalise_ref(pattern.short_name)
    ref = normalise_ref(relation.ref)
    long_name = _normalise_text(pattern.long_name)
    relation_name = _normalise_text(relation.name)
    return bool(
        (short_name and ref and short_name == ref)
        or (long_name and relation_name and long_name == relation_name)
    )


def match_route(
    pattern: RoutePattern,
    relations: list[OSMRelation],
    *,
    r_m: float,
    geometry_share: float,
) -> RelationMatch:
    """Match one main pattern by name, then by covered-stop geometry."""
    candidates = [
        relation
        for relation in relations
        if relation.mode == pattern.mode and _relation_is_local(pattern, relation)
    ]
    named = [relation for relation in candidates if _name_matches(pattern, relation)]
    if named:
        best_affiliation = max(
            _affiliation_score(pattern, relation) for relation in named
        )
        selected = tuple(
            relation
            for relation in named
            if _affiliation_score(pattern, relation) == best_affiliation
        )
        return _make_match(pattern, selected, "name", r_m)

    shares = [
        (_share(_coverage_flags(pattern, (relation,), r_m)), relation)
        for relation in candidates
    ]
    eligible = [
        (share, relation)
        for share, relation in shares
        if share >= geometry_share
    ]
    if not eligible:
        return RelationMatch(None, (), (), 0.0)
    best_share = max(share for share, _ in eligible)
    selected = tuple(
        relation for share, relation in eligible if math.isclose(share, best_share)
    )
    return _make_match(pattern, selected, "geometry", r_m)


def _make_match(
    pattern: RoutePattern,
    relations: tuple[OSMRelation, ...],
    pass_name: Literal["name", "geometry"],
    r_m: float,
) -> RelationMatch:
    flags = _coverage_flags(pattern, relations, r_m)
    return RelationMatch(
        pass_name,
        tuple(sorted(relation.relation_id for relation in relations)),
        tuple(sorted({relation.ref for relation in relations if relation.ref})),
        _share(flags),
    )


def evaluate_route(
    pattern: RoutePattern,
    relations: tuple[OSMRelation, ...],
    *,
    match_pass: MatchPass,
    r_m: float,
    k: int,
    theta: float,
    fallback_stops: tuple[tuple[float, float], ...] = (),
) -> RouteResult:
    """Verify one main pattern, cutting fixed-guideway ends before theta."""
    flags = _coverage_flags(pattern, relations, r_m)
    if not relations and pattern.mode in _FIXED_MODES and fallback_stops:
        flags = tuple(
            any(math.dist(stop, fallback) <= r_m for fallback in fallback_stops)
            for stop in pattern.stops
        )
    n = len(flags)
    relation_ids = tuple(sorted(relation.relation_id for relation in relations))
    refs = tuple(sorted({relation.ref for relation in relations if relation.ref}))
    if pattern.mode not in _FIXED_MODES:
        share = _share(flags)
        outcome: RouteOutcome = (
            ("kept-renamed" if match_pass == "geometry" else "kept")
            if n and share >= theta
            else "dropped"
        )
        return RouteResult(
            pattern.route_id,
            outcome,
            match_pass,
            relation_ids,
            refs,
            n,
            sum(flags),
            share,
            0,
            max(n - 1, 0),
        )

    leading = 0
    while leading < n and not flags[leading]:
        leading += 1
    trailing = 0
    while trailing < n and not flags[n - trailing - 1]:
        trailing += 1
    start = leading if leading >= k else 0
    end = n - trailing - 1 if trailing >= k else n - 1
    remaining = flags[start : end + 1] if start <= end else ()
    share = _share(remaining)
    if len(remaining) < 2 or share < theta:
        outcome = "dropped"
    elif start or end != n - 1:
        outcome = "cut"
    elif match_pass == "geometry":
        outcome = "kept-renamed"
    else:
        outcome = "kept"
    return RouteResult(
        pattern.route_id,
        outcome,
        match_pass,
        relation_ids,
        refs,
        len(remaining),
        sum(remaining),
        share,
        start,
        max(end, 0),
    )


def qualify_fallback_stops(
    stops: tuple[tuple[float, float], ...],
    mode: TransportMode,
    relations: list[OSMRelation],
    r_m: float,
) -> tuple[tuple[float, float], ...]:
    """Keep fallback stops beside an in-service relation way of the same mode."""
    ways = tuple(
        way
        for relation in relations
        if relation.mode == mode
        for way in relation.ways
        if _way_in_service(way, mode)
    )
    if not ways:
        return ()
    cells: dict[tuple[int, int], list[OSMWay]] = {}
    cell_size = max(r_m, 1.0)
    for way in ways:
        if not way.points:
            continue
        min_x = min(point[0] for point in way.points) - r_m
        max_x = max(point[0] for point in way.points) + r_m
        min_y = min(point[1] for point in way.points) - r_m
        max_y = max(point[1] for point in way.points) + r_m
        for ix in range(
            math.floor(min_x / cell_size),
            math.floor(max_x / cell_size) + 1,
        ):
            for iy in range(
                math.floor(min_y / cell_size), math.floor(max_y / cell_size) + 1
            ):
                cells.setdefault((ix, iy), []).append(way)
    return tuple(
        stop
        for stop in stops
        if any(
            _point_way_distance(stop, way) <= r_m
            for way in cells.get(
                (
                    math.floor(stop[0] / cell_size),
                    math.floor(stop[1] / cell_size),
                ),
                (),
            )
        )
    )


def choose_main_patterns(patterns: list[RoutePattern]) -> dict[str, RoutePattern]:
    """Choose the most-travelled reference-date pattern of every GTFS route."""
    selected: dict[str, RoutePattern] = {}
    for pattern in patterns:
        current = selected.get(pattern.route_id)
        if current is None or (-pattern.trip_count, pattern.pattern_id) < (
            -current.trip_count,
            current.pattern_id,
        ):
            selected[pattern.route_id] = pattern
    return selected


def classify_network(matched_routes: int, total_routes: int) -> str:
    """Return testability under the 50% relation-coverage rule."""
    if total_routes <= 0 or matched_routes * 2 < total_routes:
        return "not-testable"
    return "testable"
