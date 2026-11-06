"""Described-day scope switches and trip rules, section 9.9."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path

import duckdb


@dataclass(frozen=True)
class Scope:
    """Three independent switches for a described-day survey result."""

    days: str
    purposes: str
    distance: str

    def __post_init__(self) -> None:
        if (
            self.days not in ("round", "alldays")
            or self.purposes not in ("dest", "allpurp")
            or self.distance not in ("local", "daytable")
        ):
            raise ValueError(f"invalid scope: {self.id}")

    @classmethod
    def parse(cls, value: str) -> Scope:
        """Parse a scope id; reject malformed and retired ids."""
        parts = value.split("-")
        if len(parts) != 3:
            raise ValueError(f"invalid scope: {value}")
        return cls(*parts)

    @property
    def id(self) -> str:
        """Return the three-switch scope id."""
        return f"{self.days}-{self.purposes}-{self.distance}"

    @property
    def label(self) -> str:
        """Return the human-readable scope label."""
        day = "Round-trip days" if self.days == "round" else "All days"
        purpose = "destination purposes" if self.purposes == "dest" else "all purposes"
        distance = (
            "local (≤ 80 km)"
            if self.distance == "local"
            else "all trips in the day's trip table (incl. > 80 km)"
        )
        return f"{day} · {purpose} · {distance}"

    @property
    def where_sql(self) -> str:
        """SQL predicate for a row of ``scope_trips``."""
        predicates = []
        if self.days == "round":
            predicates.append("is_round")
        if self.purposes == "dest":
            predicates.append("is_destination")
        if self.distance == "local":
            predicates.append("mobloc = 1")
        return " AND ".join(predicates) if predicates else "TRUE"

    def trip_filter_sql(self, alias: str = "trip_legs") -> str:
        """SQL predicate selecting matching trips from a trip-level table."""
        return (
            "EXISTS (SELECT 1 FROM scope_trips AS scoped_trip "
            f"WHERE scoped_trip.day_id = {alias}.day_id "
            f"AND scoped_trip.num_dep = {alias}.num_dep "
            f"AND ({self.where_sql}))"
        )


def create_scope_views_from_trip_legs(
    con: duckdb.DuckDBPyConnection, *, activity_stay_min: float
) -> None:
    """Create the scope chain from the survey-normalised and energy trip views."""
    con.sql("""
        CREATE OR REPLACE VIEW scope_input AS
        SELECT t.day_id, t.num_dep, n.origin_purpose, n.destination_purpose,
            n.destination_motive, t.motive, t.moridom, t.mode_group, t.mobloc,
            n.departure_time, n.arrival_time
        FROM trip_legs t
        JOIN trips_norm n ON n.ident_dep = t.ident_dep
    """)
    create_scope_views(con, activity_stay_min=activity_stay_min)


def output_dir_for(base_dir: Path, selected_scope: Scope) -> Path:
    """Return the isolated output directory for one ``--scope all`` run."""
    return base_dir.parent / "scopes" / selected_scope.id / base_dir.name


ALL_SCOPES = tuple(
    Scope(*settings)
    for settings in product(
        ("round", "alldays"), ("dest", "allpurp"), ("local", "daytable")
    )
)
REFERENCE_SCOPE = Scope.parse("round-dest-local")
SDES_SCOPE = Scope.parse("alldays-allpurp-local")


def create_scope_views(
    con: duckdb.DuckDBPyConnection, *, activity_stay_min: float
) -> None:
    """Create full-chain day and trip flags for section 9.9.

    ``scope_input`` contains one row per trip, with globally unique ``day_id``
    and ordered ``num_dep``; raw origin/destination purposes are text, and
    ``destination_motive`` and ``motive`` use harmonised numeric codes.
    ``departure_time`` and ``arrival_time`` are SQL TIME values. Stay and
    ``activity_stay_min`` are in minutes. The caller supplies the threshold.
    """
    if not 0 < activity_stay_min < 24 * 60:
        raise ValueError("activity_stay_min must be between zero and one day")
    invalid = con.sql("""
        SELECT count(*) FROM (
            SELECT day_id, num_dep, count(*) AS n FROM scope_input
            GROUP BY day_id, num_dep
            HAVING day_id IS NULL OR num_dep IS NULL OR count(*) > 1
        )
    """).fetchone()[0]
    if invalid:
        raise ValueError("scope_input requires unique, non-null day and trip numbers")

    con.sql("""
        CREATE OR REPLACE VIEW scope_days AS
        WITH endpoints AS (
            SELECT day_id,
                first(nullif(origin_purpose, '') ORDER BY num_dep) AS first_origin,
                first(moridom ORDER BY num_dep) AS first_moridom,
                first(nullif(destination_purpose, '') ORDER BY num_dep DESC)
                    AS last_destination
            FROM scope_input GROUP BY day_id
        )
        SELECT *,
            coalesce(
                CASE WHEN first_origin IS NULL OR first_origin = '9999'
                    THEN first_moridom = 1
                    ELSE first_origin IN ('1.1', '1.2', '1.3')
                END, FALSE
            ) AS starts_at_residence,
            coalesce(last_destination IN ('1.1', '1.2', '1.3'), FALSE)
                AS ends_at_residence,
            starts_at_residence AND ends_at_residence AS is_round
        FROM endpoints
    """)
    con.execute(f"""
        CREATE OR REPLACE VIEW scope_trips AS
        WITH ordered AS (
            SELECT *,
                lead(departure_time) OVER day_order AS next_departure
            FROM scope_input
            WINDOW day_order AS (PARTITION BY day_id ORDER BY num_dep)
        ), stays AS (
            SELECT *,
                CASE WHEN next_departure IS NOT NULL AND arrival_time IS NOT NULL
                    THEN ((date_diff('second', arrival_time, next_departure)
                        + 86400) % 86400) / 60.0
                END AS stay_min
            FROM ordered
        ), activity AS (
            SELECT *,
                coalesce(mode_group IN ('walk', 'cycle') AND (
                    destination_motive IN (7.7, 7.8)
                    OR (destination_motive = 7.6 AND stay_min < {activity_stay_min})
                ), FALSE) AS outward_activity
            FROM stays
        ), propagated AS (
            SELECT *, lag(outward_activity, 1, FALSE) OVER day_order
                AS prior_activity
            FROM activity
            WINDOW day_order AS (PARTITION BY day_id ORDER BY num_dep)
        )
        SELECT p.*, d.starts_at_residence, d.ends_at_residence, d.is_round,
            NOT (
                coalesce(motive IN (8.1, 8.2, 8.3, 8.4), FALSE)
                OR outward_activity
                OR (coalesce(destination_purpose IN ('1.1', '1.2', '1.3'), FALSE)
                    AND prior_activity)
            ) AS is_destination
        FROM propagated p JOIN scope_days d USING (day_id)
    """)
