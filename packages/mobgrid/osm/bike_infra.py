"""Directional cycling infrastructure classification for section 8.1."""

from __future__ import annotations

import re
from collections.abc import Mapping

from mobgrid.osm.config import NetworkConfig

_SIDE_TAG = re.compile(r"^cycleway:(left|right)(?::.*)?$")


def parse_maxspeed_kmh(
    value: str | None, config: NetworkConfig
) -> float | None:
    """Parse one OSM maxspeed value to km/h; symbolic unknowns stay null."""
    if value is None:
        return None
    text = value.strip().casefold()
    tokens = {
        key.casefold(): speed for key, speed in config.maxspeed_tokens_kmh.items()
    }
    if text in tokens:
        return tokens[text]
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(mph|km/?h)?", text)
    if match is None:
        return None
    speed = float(match.group(1))
    return speed * config.mph_to_kmh if match.group(2) == "mph" else speed


def maxspeed_sql(tags_expression: str, config: NetworkConfig) -> str:
    """Build a DuckDB SQL expression matching ``parse_maxspeed_kmh``."""
    speed = f"lower(trim({tags_expression}['maxspeed']))"
    symbolic = " ".join(
        f"WHEN {speed} = '{key.casefold()}' THEN {value}"
        for key, value in config.maxspeed_tokens_kmh.items()
        if value is not None
    )
    numeric = (
        "regexp_full_match("
        f"{speed}, '^[[:space:]]*[0-9]+([.][0-9]+)?[[:space:]]*"
        "(mph|km/?h)?[[:space:]]*$')"
    )
    number = (
        f"try_cast(regexp_extract({speed}, "
        "'^[[:space:]]*([0-9]+([.][0-9]+)?)[[:space:]]*"
        "(mph|km/?h)?[[:space:]]*$', 1) AS DOUBLE)"
    )
    return (
        f"CASE {symbolic} WHEN {numeric} THEN {number} * "
        f"CASE WHEN ends_with({speed}, 'mph') THEN {config.mph_to_kmh} "
        "ELSE 1 END ELSE NULL END"
    )


def _side_applies(key: str, forward: bool) -> bool:
    match = _SIDE_TAG.fullmatch(key)
    if match is None:
        return True
    expected_side = "right" if forward else "left"
    return match.group(1) == expected_side


def _rule_sql(
    rule: str,
    *,
    tags_expression: str,
    forward_expression: str,
    bike_access_expression: str,
    config: NetworkConfig,
) -> str:
    if rule == "other_bike_accessible_roads":
        return bike_access_expression
    if rule == "busway+cycling_access":
        candidates = []
        for key in ("busway", "busway:left", "busway:right", "busway:both"):
            if not _side_applies(key, True):
                direction = f"NOT ({forward_expression})"
            elif not _side_applies(key, False):
                direction = forward_expression
            else:
                direction = "TRUE"
            values = ", ".join(f"'{value}'" for value in config.busway_values)
            candidates.append(
                f"({direction} AND lower({tags_expression}['{key}']) "
                f"IN ({values}))"
            )
        return (
            f"({bike_access_expression} AND ("
            + " OR ".join(candidates)
            + "))"
        )
    if rule.startswith("maxspeed<="):
        limit = float(rule.split("<=", 1)[1])
        return f"({maxspeed_sql(tags_expression, config)} <= {limit})"

    conditions = []
    for condition in rule.split("+"):
        key, expected = condition.split("=", 1)
        if key.endswith(":left"):
            direction = f"NOT ({forward_expression})"
        elif key.endswith(":right"):
            direction = forward_expression
        else:
            direction = "TRUE"
        conditions.append(
            f"({direction} AND lower({tags_expression}['{key}']) "
            f"= '{expected.casefold()}')"
        )
    return "(" + " AND ".join(conditions) + ")"


def bike_infrastructure_sql(
    tags_expression: str,
    forward_expression: str,
    bike_access_expression: str,
    config: NetworkConfig,
) -> str:
    """Build a vectorized SQL expression for one directed edge's bike class."""
    priority = (
        "separated_track_path",
        "painted_lane",
        "bus_lane",
        "low_speed",
        "mixed_traffic",
    )
    cases = []
    for bike_class in priority:
        rules = [
            _rule_sql(
                rule,
                tags_expression=tags_expression,
                forward_expression=forward_expression,
                bike_access_expression=bike_access_expression,
                config=config,
            )
            for rule in config.bike_classes[bike_class]
        ]
        if rules:
            cases.append(f"WHEN {' OR '.join(rules)} THEN '{bike_class}'")
    return (
        f"CASE WHEN NOT ({bike_access_expression}) THEN NULL "
        + " ".join(cases)
        + " ELSE 'mixed_traffic' END"
        )


def _matches_rule(
    rule: str,
    tags: Mapping[str, str | None],
    *,
    forward: bool,
    bike_access: bool,
    config: NetworkConfig,
) -> bool:
    if rule == "other_bike_accessible_roads":
        return bike_access
    if rule == "busway+cycling_access":
        return bike_access and any(
            (tags.get(key) or "").casefold() in config.busway_values
            for key in ("busway", "busway:left", "busway:right", "busway:both")
        )
    if rule.startswith("maxspeed<="):
        limit = float(rule.split("<=", 1)[1])
        speed = parse_maxspeed_kmh(tags.get("maxspeed"), config)
        return speed is not None and speed <= limit

    for condition in rule.split("+"):
        key, expected = condition.split("=", 1)
        if not _side_applies(key, forward):
            return False
        if (tags.get(key) or "").casefold() != expected.casefold():
            return False
    return True


def classify_bike_infrastructure(
    tags: Mapping[str, str | None],
    *,
    forward: bool,
    bike_access: bool,
    config: NetworkConfig,
) -> str | None:
    """Return one section 8.1 bike class for a directed edge, or ``None``.

    Left/right cycleway tags apply to the way's corresponding travel
    direction: right for the forward direction, left for the reverse.
    """
    if not bike_access:
        return None
    priority = (
        "separated_track_path",
        "painted_lane",
        "bus_lane",
        "low_speed",
        "mixed_traffic",
    )
    for bike_class in priority:
        if any(
            _matches_rule(
                rule,
                tags,
                forward=forward,
                bike_access=bike_access,
                config=config,
            )
            for rule in config.bike_classes[bike_class]
        ):
            return bike_class
    return "mixed_traffic"
