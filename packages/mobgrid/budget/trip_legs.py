"""Shared trip-leg energy computation for section 9.9's re-estimation
(step 11), survey-agnostic.

``build_trip_legs`` reads the ``trips_norm`` view -- one row per trip,
with the columns of ``docs/data/entd2008.md``'s "Columns of the
normalised trip view, by survey" table -- and creates the ``trip_legs``
view: mode/vehicle classification, density resolution (the INSEE grid or
the section 9.9 urban-unit-status x residence-size proxy), the
data-quality speed correction, and the section 9 leg/energy formulas.
Each survey (``mobgrid.budget.emp2019``, ``mobgrid.budget.entd2008``)
builds its own ``trips_norm`` from its own raw tables; everything from
``trips_norm`` onward is this one shared module, so the energy model
cannot silently differ between surveys.
"""

from __future__ import annotations

import duckdb

from mobgrid.energy import legs, walk
from mobgrid.energy.bike import solve_bike_speed_m_per_s
from mobgrid.energy.rates import (
    MET_MINUTE_KJ_PER_KG,
    EnergyConfig,
    activity_rate_kj_per_min,
    sedentary_energy_kj,
)

#: Vehicle keys of `config.pt_ride` (`load_factor_max`, `standing_share_am_peak`,
#: `headway_min_am_peak`, `station_height_m`), mapped from the harmonised
#: (EMP 2019-coded) main transport-mode code `mtp` that every survey's
#: `trips_norm` exposes (section 9.9, "the main mode"; `mtp` codes follow
#: `data/raw/emp2019/emp2019-categories.pdf`'s "Moyen de transport" table).
#: `mtp` code 5.10 ("autres transports urbains/regionaux sans precision")
#: has no separate entry: as a float it equals 5.1, so DuckDB cannot tell
#: the two apart either; both fall in "urban_bus" regardless.
_VEHICLE_BY_MTP = {
    5.1: "urban_bus",  # autobus urbain, trolleybus
    5.2: "urban_bus",  # navette fluviale (closest proxy)
    5.3: "interurban_coach",  # autocar de ligne
    5.4: "interurban_coach",  # autre autocar
    5.5: "ter",  # autocar TER
    5.6: "tram",
    5.7: "metro",  # metro, VAL, funiculaire
    5.8: "rer_suburban",  # RER, SNCF banlieue
    5.9: "ter",
    6.1: "tgv_long_distance_coach",
    6.2: "tgv_long_distance_coach",
    6.3: "intercites",
    6.4: "intercites",
    6.5: "intercites",
}

#: CV default key (`config.waiting.cv_defaults`) by vehicle, by right of way:
#: reserved-track rail (metro/RER/TER/long-distance), tram on reserved
#: track, or bus/coach in mixed traffic (section 9.4).
_CV_KEY_BY_VEHICLE = {
    "metro": "metro_rail",
    "rer_suburban": "metro_rail",
    "ter": "metro_rail",
    "intercites": "metro_rail",
    "tgv_long_distance_coach": "metro_rail",
    "tram": "tram_reserved_track",
    "urban_bus": "bus_mixed_traffic",
    "interurban_coach": "bus_mixed_traffic",
}

#: Minimum ride-only time, seconds, below which the bike get-park/stops
#: adjustment is considered unreliable (section 9.9's P0 calibration):
#: fixed overheads cannot credibly exceed almost all of a very short
#: trip's declared duration. The stricter of this absolute floor and
#: `_BIKE_MIN_RIDE_FRACTION` of the declared duration applies.
_BIKE_MIN_RIDE_TIME_S = 60.0

#: Minimum share of the declared duration that must remain as ride time
#: for the get-park/stops adjustment to be considered reliable.
_BIKE_MIN_RIDE_FRACTION = 0.5

#: Plausibility cap, km/h, on the adjusted ride speed (section 9.9's P0
#: calibration): above this, a trip's declared distance/duration/stop
#: count combination is not credible even though it passed the ride-time
#: checks above (occasional, very short, very long-looking bike trips);
#: it falls back to the naive whole-duration speed, like the ride-time
#: checks above.
_BIKE_MAX_PLAUSIBLE_SPEED_KMH = 45.0

#: Door-to-door implied speed upper bounds, km/h, by mode (a separate
#: data-quality check: unlike the bike P0 calibration guards above, this
#: flags individual trips for distance correction, not a quantity
#: derived from them). Only an upper bound: declared durations are
#: self-reported and often rounded to 5/15/30/60 min, so a trip can look
#: implausibly fast purely from rounding; the lower end is left alone
#: (round 4's two-sided filter dropped whole days -- round 5 corrects
#: the implausible trips instead, so stricter lower-bound flagging would
#: just replace more declared values with the sample median). Public:
#: used by `emp.py`'s report. Cycling energy's main work term is
#: time-based (not distance-based) since round 4's fix, but its "stops"
#: sub-term still multiplies by distance and by the distance-derived
#: ride speed squared (section 9.7), so a flagged bike trip's distance
#: is corrected too, like walk and car (round 9, after an ENTD 2008
#: outlier -- a declared 376 km/65 min cycling leg -- inflated one day
#: to ~1.3M kJ through this term).
WALK_SPEED_UPPER_KMH = 7.0
CYCLE_SPEED_UPPER_KMH = 35.0
CAR_SPEED_UPPER_KMH = 130.0
_CAR_MODE_GROUPS = (
    "car_driver",
    "car_passenger_household",
    "car_passenger_carpool",
)

#: `terminal_legs` variants of `build_trip_legs` (section 9.9, 27 October
#: 2026 decision: "the survey reconstruction takes its terminal legs from
#: the declared values"). ``'declared'`` (the new default): each trip's
#: own declared walking minutes (`MTEMPSMAP`/`V2_MTEMPSMAP`) replace the
#: walks to and from the car, the carpool walk to the meeting point, the
#: PT access walks and the bike get/park time; the declared waiting
#: minutes (`MTPSATTENT`/`V2_MTPSATTENT`) replace the PT/train wait;
#: missing declared values (0.3% to 3% of trips, by mode) fall back to
#: the section 9.4-9.7 defaults. ``'declared_plus1'``: the same, plus
#: 1 minute of walking for car (both passenger types too), bike and
#: urban PT trips -- not train -- "for unreported short walks"
#: (`_DECLARED_PLUS1_MODES`). ``'defaults'``: the former section 9.4-9.7
#: density-class defaults throughout, the only variant ``terminal_scale``
#: still sweeps (its old x0.5/x1.5 robustness role).
TERMINAL_LEGS_VARIANTS = ("declared", "declared_plus1", "defaults")

#: Mode groups that get `'declared_plus1'`'s extra minute of walking
#: (car, both passenger types, bike, urban PT; not train, per the 27
#: October 2026 decision).
_DECLARED_PLUS1_MODES = (
    "car_driver",
    "car_passenger_household",
    "car_passenger_carpool",
    "cycle",
    "urban_pt",
)

#: `mode_group = 'other'` day-mode-group contents, stated for the report
#: (section 9.9 point 3, "State in the report what 'other' contains").
OTHER_MODE_DESCRIPTION = (
    "powered two-wheelers under 50cm3 or unspecified (mtp 2.3-2.7), "
    "unspecified 3/4-wheeler (mtp 3.4), taxi/specialised/school transport "
    "(mtp 4.x), plane (mtp 7.x), boat (mtp 8.1), other/unspecified "
    "(mtp 9.1, missing, or the 9999 refusal code)"
)

#: `MOT_SEQ_COMPL`'s own labels ("Motif corrige detaille de la sequence",
#: the chain-level, corrected trip purpose; unlike the raw, trip-level
#: `MMOTIFDES`/is_loop_trip, it has no "return home"/"return to
#: residence" codes 1.1-1.3, since a return leg is recoded to the
#: purpose of the outward leg it closes). Shared across surveys: ENTD
#: 2008's `V2_MMOTIFDES`/`V2_MMOTIFORI` are converted to these same
#: codes (`docs/data/entd2008.md`). Used by
#: `emp._compute_motive_decomposition` (section 9.9 point 1 follow-up,
#: "decompose energy per motive"), labels from
#: `data/raw/emp2019/emp2019-categories.pdf`'s "Motif" table.
MOTIVE_LABEL_BY_CODE = {
    1.1: "return home",
    1.2: "return to occasional residence",
    1.3: "return to parents'/friends' home",
    1.4: "study (school/university)",
    1.5: "young-child childcare drop-off",
    2.1: "shopping, mall/large store",
    2.2: "shopping, local store",
    3.1: "medical/personal care",
    4.1: "administrative errand",
    4.12: "waste disposal site",
    5.1: "visit family",
    5.2: "visit friends",
    6.1: "accompany to station/airport",
    6.2: "accompany elsewhere",
    6.3: "pick up from station/airport",
    6.4: "pick up elsewhere",
    7.1: "association/religious/meeting",
    7.2: "leisure centre/amusement park/fair",
    7.3: "eat/drink out",
    7.4: "visit monument/historic site",
    7.5: "cultural/sports show, conference",
    7.6: "sport",
    7.7: "stroll, no specific destination",
    7.8: "go to a place for walking",
    8.1: "holiday, away from second home",
    8.2: "go to second home",
    8.3: "go to occasional residence",
    8.4: "other personal reason",
    9.1: "work, fixed usual workplace",
    9.2: "work, outside fixed workplace",
    9.3: "training/conference/exhibition",
    9.4: "professional rounds/patient visits",
    9.5: "other professional reason",
}

#: Section 9.9's scope (2026-10-20 project decision): the re-estimation
#: is about commuting and travel for needs fulfilment, not recreational
#: movement for its own sake. Trips whose corrected motive (`motive`,
#: `MOT_SEQ_COMPL`, or ENTD 2008's converted equivalent) is sport (7.6),
#: a destination-less stroll (7.7, the same purpose as `is_loop_trip`),
#: "going to a place to walk/ride" (7.8, destination exists, but the
#: movement itself is the point), or any top-level motive group 8
#: purpose (8.1-8.4: holidays, second/occasional residence, other
#: private reasons -- none of them a needs-fulfilment destination) are
#: excluded from every day/energy computation in step 11's report -- the
#: whole report's base scope, not an optional variant.
NEEDS_EXCLUDED_MOTIVE_CODES = (7.6, 7.7, 7.8, 8.1, 8.2, 8.3, 8.4)

#: SQL fragment for ``day_summary``'s candidate-trip filter (and any
#: other per-leg query that must match its scope): keeps a trip unless
#: its corrected motive is one of `NEEDS_EXCLUDED_MOTIVE_CODES`; a
#: missing/refused motive (``motive IS NULL``) is kept, not excluded (we
#: cannot tell whether it was needs-based).
NEEDS_ONLY_WHERE_SQL = (
    "(motive IS NULL OR motive NOT IN ("
    + ", ".join(f"{code:g}" for code in NEEDS_EXCLUDED_MOTIVE_CODES)
    + "))"
)

#: Top-level (integer) motive group labels, `emp2019-categories.pdf`'s
#: "Motif" table section headers, used by the all-modes "energy by
#: motive" figure (one stacked bar per mode, 9 segments instead of
#: `MOTIVE_LABEL_BY_CODE`'s ~30 sub-codes).
TOP_LEVEL_MOTIVE_LABEL_BY_CODE = {
    1.0: "return home/study/childcare",
    2.0: "shopping",
    3.0: "medical/personal care",
    4.0: "administrative errand",
    5.0: "visits",
    6.0: "accompany/pick up",
    7.0: "leisure",
    8.0: "holidays/second home",
    9.0: "professional",
}

#: The INSEE 4-level density grid's own names and order (section 9.9
#: point 3), shared by the grid (EMP 2019's `DENSITECOM_ORI`/`_DES`) and
#: the urban-unit-status x residence-size proxy of section 9.9's "Change
#: between 2008 and 2019" (both surveys, used in both when
#: ``density_source='proxy'``).
DENSITY_LABELS = ("dense", "intermediate", "sparse", "very_sparse")

#: `config.car`/`config.pt_ride`'s existing density-class keys (chosen for
#: step 7) translated to the INSEE names above, so every density-keyed
#: default (car terminal legs, PT access walk) can be looked up by the
#: same label used for grouping and reporting.
_DENSITY_KEY_TRANSLATION = {
    "dense": "dense",
    "urban": "intermediate",
    "suburban": "sparse",
    "rural": "very_sparse",
}

#: Residence urban-unit size bands of section 9.9's density proxy table
#: (`TUU2017_RES`/`TU99`/`V2_TUU...` codes 0-8): 0 rural, 1-3 small urban
#: units (together "rural or under 20,000"), 4-6 "20,000 to 199,999", 7-8
#: "200,000 or more, Paris".
_TUU_RES_SMALL_CODES = ("0", "1", "2", "3")
_TUU_RES_MEDIUM_CODES = ("4", "5", "6")
_TUU_RES_LARGE_CODES = ("7", "8")


def relabel_density(mapping: dict[str, float]) -> dict[str, float]:
    """Re-key a `config.car`/`config.pt_ride` density dict (`dense`,
    `urban`, `suburban`, `rural`) to the INSEE labels of
    `DENSITY_LABELS`."""
    return {_DENSITY_KEY_TRANSLATION[key]: value for key, value in mapping.items()}


def _dbl(value: float) -> str:
    """A numeric literal explicitly cast to DOUBLE.

    DuckDB infers a narrow DECIMAL type for literals with many decimal
    digits (e.g. a repeating-fraction Python float); an explicit cast
    keeps every rate/leg constant a DOUBLE, avoiding overflow once CASE
    branches with different literal precisions are combined in the same
    arithmetic expression.
    """
    return f"({value!r}::DOUBLE)"


def _case_sql(
    column_sql: str, mapping: dict, default: str = "NULL", quote_values: bool = False
) -> str:
    """A SQL CASE expression mapping ``column_sql``'s string key to a value.

    Numeric values (minutes, kJ) are emitted as DOUBLE literals;
    ``quote_values`` emits each value as a quoted string literal instead
    (used for the age-activity group labels).
    """
    value_sql = (lambda v: f"'{v}'") if quote_values else _dbl
    branches = "\n    ".join(
        f"WHEN '{key}' THEN {value_sql(value)}" for key, value in mapping.items()
    )
    return f"CASE {column_sql}\n    {branches}\n    ELSE {default}\nEND"


def density_proxy_case_sql(uu_status_col: str, tuu_res_col: str) -> str:
    """Section 9.9's density proxy ("trip-end urban-unit status x
    residence size class"), used in both surveys when
    ``density_source='proxy'`` (always, for ENTD 2008, which has no
    density grid): a trip end in the city centre ('C') of a large
    residence urban unit (200,000+/Paris) is 'dense'; a rural trip end
    ('R', "hors unite urbaine") is always 'very_sparse'; an isolated town
    ('I') is always 'sparse'; everything else follows the table of
    section 9.9's "Change between 2008 and 2019". A missing/unrecognised
    status or size code (``NULL``, the disclosure-masked EMP 2019 codes
    '8'/'9') falls back to 'intermediate', as the grid's own stray codes
    do.
    """
    small = ", ".join(f"'{c}'" for c in _TUU_RES_SMALL_CODES)
    medium = ", ".join(f"'{c}'" for c in _TUU_RES_MEDIUM_CODES)
    large = ", ".join(f"'{c}'" for c in _TUU_RES_LARGE_CODES)
    return f"""
    CASE
        WHEN {uu_status_col} = 'C' AND {tuu_res_col} IN ({large}) THEN 'dense'
        WHEN {uu_status_col} = 'C' AND {tuu_res_col} IN ({medium}) THEN 'intermediate'
        WHEN {uu_status_col} = 'C' AND {tuu_res_col} IN ({small}) THEN 'sparse'
        WHEN {uu_status_col} = 'B' AND {tuu_res_col} IN ({large}) THEN 'intermediate'
        WHEN {uu_status_col} = 'B' AND {tuu_res_col} IN ({medium}) THEN 'intermediate'
        WHEN {uu_status_col} = 'B' AND {tuu_res_col} IN ({small}) THEN 'sparse'
        WHEN {uu_status_col} = 'I' THEN 'sparse'
        WHEN {uu_status_col} = 'R' THEN 'very_sparse'
        ELSE 'intermediate'
    END
    """


def _implied_load_factor(standing_share: float) -> float:
    """Load factor consistent with a standing share (section 9.5).

    Inverts ``legs.pt_standing_share``: LF = 1 / (1 - p_s); mirrors
    ``mobgrid.energy.checks._implied_load_factor``.
    """
    return 1.0 / (1.0 - min(standing_share, 0.999_999))


def _vehicle_stair_legs(
    config: EnergyConfig, rate_set_kh_cp: tuple[float, float]
) -> dict[str, tuple[float, float, float]]:
    """Per vehicle: (stairs_time_min, stairs_energy_kh_kj, stairs_energy_cp_kj).

    Section 9.3: a round trip's two level changes (entering, leaving),
    both of ``config.pt_ride.station_height_m[vehicle]``; above the
    escalator threshold, both legs are at the standing-relaxed rate
    instead of the stairs formula (section 9.3, "Escalators and lifts are
    taken at the standing rate").
    """
    standing_relaxed_kh, standing_relaxed_cp = rate_set_kh_cp
    stairs = config.stairs
    result: dict[str, tuple[float, float, float]] = {}
    for vehicle, height_m in config.pt_ride.station_height_m.items():
        down_s, down_e_kj = walk.stair_time_and_energy(
            height_m,
            "down",
            config.reference_mass_kg,
            stairs.up_speed_m_per_s,
            stairs.down_speed_m_per_s,
            stairs.up_efficiency,
            stairs.down_to_up_energy_ratio,
        )
        up_s, up_e_kj = walk.stair_time_and_energy(
            height_m,
            "up",
            config.reference_mass_kg,
            stairs.up_speed_m_per_s,
            stairs.down_speed_m_per_s,
            stairs.up_efficiency,
            stairs.down_to_up_energy_ratio,
        )
        time_min = (down_s + up_s) / 60.0
        if height_m > stairs.escalator_depth_threshold_m:
            energy_kh = sedentary_energy_kj(standing_relaxed_kh, down_s + up_s)
            energy_cp = sedentary_energy_kj(standing_relaxed_cp, down_s + up_s)
        else:
            energy_kh = energy_cp = down_e_kj + up_e_kj
        result[vehicle] = (time_min, energy_kh, energy_cp)
    return result


def _vehicle_wait_minutes(config: EnergyConfig) -> dict[str, float]:
    """Per vehicle, the expected wait of section 9.4's frequency formula,
    at the configured representative AM-peak headway and right-of-way CV."""
    waiting = config.waiting
    result: dict[str, float] = {}
    for vehicle, headway_min in config.pt_ride.headway_min_am_peak.items():
        cv_key = _CV_KEY_BY_VEHICLE[vehicle]
        cv = config.waiting.cv_defaults[cv_key]
        wait_s = legs.expected_wait_s(
            headway_min * 60.0,
            cv,
            waiting.headway_regime_threshold_min * 60.0,
            waiting.w_planned_min * 60.0,
        )
        result[vehicle] = wait_s / 60.0
    return result


def _vehicle_ride_rate_kj_per_min(config: EnergyConfig) -> dict[str, float]:
    """Per vehicle, the first-phase PT ride rate of section 9.5 (KH-pinned,
    not switched by rate set: `config.pt_ride`'s own three rates are the
    literal KH figures)."""
    pt_ride = config.pt_ride
    result: dict[str, float] = {}
    for vehicle, standing_share in pt_ride.standing_share_am_peak.items():
        load_factor = _implied_load_factor(standing_share)
        result[vehicle] = legs.pt_ride_rate_kj_per_min(
            load_factor,
            pt_ride.load_factor_max[vehicle],
            pt_ride.r_sit_kj_per_min,
            pt_ride.r_relaxed_kj_per_min,
            pt_ride.r_restless_kj_per_min,
        )
    return result


def build_trip_legs(
    con: duckdb.DuckDBPyConnection,
    config: EnergyConfig,
    *,
    terminal_scale: float = 1.0,
    bike_p0_override_w: float | None = None,
    density_source: str = "grid",
    terminal_legs: str = "declared",
) -> None:
    """Create the ``trip_legs`` view from ``trips_norm``: one row per
    trip, with time and energy above rest (both rate sets) by leg
    (section 9.9, point 1), shared by every survey.

    Reuses ``mobgrid.energy``'s public rate/leg formulas wherever a
    parameter is per-vehicle or per-density-class (computed once, in
    Python, over the handful of vehicle/density keys); only the
    arithmetic over the trip rows themselves (tens of thousands) runs as
    vectorised DuckDB SQL.

    ``terminal_legs`` (section 9.9, 27 October 2026 decision) selects the
    terminal-leg walking/waiting minutes of every mode but walk itself:
    see ``TERMINAL_LEGS_VARIANTS`` for ``'declared'`` (the default),
    ``'declared_plus1'`` and ``'defaults'``. ``terminal_scale`` multiplies
    every terminal-leg time and energy component (walk-to/from-car,
    parking search, carpool walk/wait, PT access walk/wait/level-change,
    bike get-and-park and stops), with the main/ride/drive leg taking the
    rest of the declared duration; it only has an effect when
    ``terminal_legs='defaults'`` (section 9.9's F8 robustness check,
    "terminal legs x0.5, x1, x1.5" -- the one variant it still sweeps).

    Cycling energy's work term is time-based at a single, population-level
    power, ``bike_p0_override_w`` if given, else ``config.bike.power.p0_w``
    (section 9.7's own force-balance power selection, flat ground, since
    neither survey gives a gradient): every pedalled second is charged at
    this one rate, not at each trip's own noisy implied speed. Deriving
    power per-trip instead (speed, hence drag, hence power, is convex;
    declared durations are also rounded to 5/15/30/60 min) was found to
    inflate mean cycling energy several-fold above the population rate
    (section 9.9, step 11 third round) -- the same Jensen's-inequality
    bias the ratio-of-weighted-sums v0/P0 estimator avoids for
    calibration, but that the energy formula used to reintroduce.
    ``p0_calibrated_w`` (the per-trip implied power) is still exposed, as
    a diagnostic only, no longer used by the energy formula. The "stops"
    sub-term (section 9.7's 2 stops/km, each costing a kinetic-energy
    term) is costed at the same, single flat speed the rider holds at
    this P0 (the inverse force-balance solve, ``bike.
    solve_bike_speed_m_per_s``), not at each trip's own distance/ride-time
    speed, for the same reason (22 October 2026 decision).

    ``density_source`` selects the trip ends' density class: ``'grid'``
    (default) reads ``trips_norm.density_ori_grid``/``density_des_grid``
    (only populated by EMP 2019); ``'proxy'`` computes section 9.9's
    urban-unit-status x residence-size proxy from ``trips_norm``'s
    ``uu_status_ori``/``uu_status_des``/``tuu_res`` instead (the only
    option for ENTD 2008, which has no density grid). Requesting
    ``'grid'`` on a survey that never fills the grid columns raises
    ``ValueError``, rather than silently falling back to 'intermediate'
    for every trip.
    """
    if density_source not in ("grid", "proxy"):
        raise ValueError(f"unknown density_source: {density_source!r}")
    if terminal_legs not in TERMINAL_LEGS_VARIANTS:
        raise ValueError(f"unknown terminal_legs: {terminal_legs!r}")
    if density_source == "grid":
        has_grid = con.sql(
            "SELECT count(*) FROM trips_norm WHERE density_ori_grid IS NOT NULL"
        ).fetchone()[0]
        if has_grid == 0:
            raise ValueError(
                "density_source='grid' was requested, but trips_norm has no "
                "density_ori_grid values (this survey has no density grid: "
                "use density_source='proxy')"
            )

    mass = config.reference_mass_kg
    walking = config.walking
    bike_p0_w = (
        bike_p0_override_w if bike_p0_override_w is not None else config.bike.power.p0_w
    )
    if bike_p0_w is None:
        raise ValueError(
            "config.bike.power.p0_w is not set and no bike_p0_override_w "
            "was given: cycling energy has no power to use"
        )

    walk_rate_kh = walk.walking_time_and_energy(
        [(walking.v0_kmh * 1000.0 / 60.0, 0.0)],
        mass,
        walking.v0_kmh,
        walking.c0_j_per_kg_m["kh"],
        walking.gradient_polynomial_j_per_kg_m,
    )[1]
    walk_rate_cp = walk.walking_time_and_energy(
        [(walking.v0_kmh * 1000.0 / 60.0, 0.0)],
        mass,
        walking.v0_kmh,
        walking.c0_j_per_kg_m["compendium"],
        walking.gradient_polynomial_j_per_kg_m,
    )[1]
    standing_kh = activity_rate_kj_per_min(
        config.activity_rates["standing_relaxed"], "kh", mass
    )
    standing_cp = activity_rate_kj_per_min(
        config.activity_rates["standing_relaxed"], "compendium", mass
    )
    sitting_kh = activity_rate_kj_per_min(
        config.activity_rates["sitting_vehicle"], "kh", mass
    )
    sitting_cp = activity_rate_kj_per_min(
        config.activity_rates["sitting_vehicle"], "compendium", mass
    )
    driving_kh = activity_rate_kj_per_min(
        config.activity_rates["driving_free_flow"], "kh", mass
    )
    driving_cp = activity_rate_kj_per_min(
        config.activity_rates["driving_free_flow"], "compendium", mass
    )

    v0_m_per_s = walking.v0_kmh * 1000.0 / 3600.0
    access_walk_min_by_density = relabel_density(
        {
            density: metres / v0_m_per_s / 60.0
            for density, metres in config.pt_ride.access_walk_m_by_density.items()
        }
    )
    stair_legs = _vehicle_stair_legs(config, (standing_kh, standing_cp))
    wait_minutes = _vehicle_wait_minutes(config)
    ride_rate = _vehicle_ride_rate_kj_per_min(config)

    car = config.car
    bike = config.bike
    stops = bike.stops
    crr = bike.surface_crr["asphalt_concrete_paved_default"]
    bike_total_mass = mass + bike.bike_mass_kg
    # Stops are costed at the flat speed the rider holds at the
    # calibrated P0 (22 October 2026 decision, section 9.9's "Legs
    # without paths"), not at each trip's own (declared-distance/
    # ride-time) speed: that speed is noisy (declared distances and
    # durations), and the stop energy grows with its square, so costing
    # it at each trip's own speed inflated the group mean (the same
    # Jensen's-inequality bias the time-based ride-work term already
    # avoids, section 9.9 point 3). The inverse of the same force-
    # balance equation `daily_energy.calibrate_p0` solves forward
    # (speed -> P0), on the rider's own mass only (not the bike's,
    # matching that calibration's convention), flat ground, no headwind.
    bike_flat_speed_m_per_s = float(
        solve_bike_speed_m_per_s(
            bike_p0_w,
            mass,
            0.0,
            crr,
            bike.cda_m2,
            bike.rho_air_kg_per_m3,
            bike.drivetrain_efficiency,
        )
    )
    walk_to_car_by_density = relabel_density(car.walk_to_car.apartment_min_by_density)
    parking_search_by_density = relabel_density(car.parking_search_min_by_density)
    walk_from_car_by_density = relabel_density(car.walk_from_car_min_by_density)

    # DOUBLE-cast SQL literals of every scalar embedded directly below
    # (see `_dbl`'s docstring for why the cast matters).
    mass_sql = _dbl(mass)
    crr_sql = _dbl(crr)
    rho_air_sql = _dbl(bike.rho_air_kg_per_m3)
    cda_sql = _dbl(bike.cda_m2)
    drivetrain_eff_sql = _dbl(bike.drivetrain_efficiency)
    muscular_eff_sql = _dbl(bike.gross_muscular_efficiency)
    bike_total_mass_sql = _dbl(bike_total_mass)
    bike_flat_speed_m_per_s_sql = _dbl(bike_flat_speed_m_per_s)
    stops_per_km_sql = _dbl(stops.stops_per_km)
    stop_decel_term_sql = _dbl(1.0 / stops.deceleration_m_per_s2)
    stop_accel_term_sql = _dbl(1.0 / stops.acceleration_m_per_s2)
    stop_fixed_wait_s_sql = _dbl(stops.red_time_s**2 / (2.0 * stops.signal_cycle_s))
    bike_get_park_total_min_sql = _dbl(2.0 * bike.get_park_min)
    bike_unloaded_rate_kj_per_min_sql = _dbl(
        bike.pedalling_unloaded_net_met * MET_MINUTE_KJ_PER_KG * mass
    )
    bike_p0_w_sql = _dbl(bike_p0_w)
    c0_kh_sql = _dbl(config.walking.c0_j_per_kg_m["kh"])
    c0_cp_sql = _dbl(config.walking.c0_j_per_kg_m["compendium"])
    walk_rate_kh_sql, walk_rate_cp_sql = _dbl(walk_rate_kh), _dbl(walk_rate_cp)
    standing_kh_sql, standing_cp_sql = _dbl(standing_kh), _dbl(standing_cp)
    sitting_kh_sql, sitting_cp_sql = _dbl(sitting_kh), _dbl(sitting_cp)
    driving_kh_sql, driving_cp_sql = _dbl(driving_kh), _dbl(driving_cp)
    carpool_walk_sql = _dbl(car.carpool_passenger.walk_to_meeting_point_min)
    carpool_wait_sql = _dbl(car.carpool_passenger.wait_standing_min)
    # `terminal_scale` only has an effect under `terminal_legs='defaults'`
    # (its old x0.5/x1/x1.5 robustness-sweep role); a declared quantity
    # (`'declared'`/`'declared_plus1'`) is not scaled.
    effective_terminal_scale = terminal_scale if terminal_legs == "defaults" else 1.0
    terminal_scale_sql = _dbl(effective_terminal_scale)
    car_modes_sql = ", ".join(f"'{m}'" for m in _CAR_MODE_GROUPS)
    # Flags only the upper bound, on the *declared* speed (before any
    # correction): a trip this fast cannot credibly be the mode it is
    # coded as, whatever the declared duration rounding.
    speed_flagged_upper_sql = f"""
        coalesce(
            CASE
                WHEN mode_group = 'walk' THEN
                    implied_speed_kmh_declared > {_dbl(WALK_SPEED_UPPER_KMH)}
                WHEN mode_group = 'cycle' THEN
                    implied_speed_kmh_declared > {_dbl(CYCLE_SPEED_UPPER_KMH)}
                WHEN mode_group IN ({car_modes_sql}) THEN
                    implied_speed_kmh_declared > {_dbl(CAR_SPEED_UPPER_KMH)}
                ELSE FALSE
            END,
            FALSE
        )
    """

    vehicle_mapping_sql = (
        "CASE mtp\n    "
        + "\n    ".join(
            f"WHEN {code} THEN '{vehicle}'" for code, vehicle in _VEHICLE_BY_MTP.items()
        )
        + "\n    ELSE NULL\nEND"
    )

    if density_source == "grid":
        density_ori_sql = "coalesce(density_ori_grid, 'intermediate')"
        density_des_sql = "coalesce(density_des_grid, 'intermediate')"
    else:
        density_ori_sql = density_proxy_case_sql("uu_status_ori", "tuu_res")
        density_des_sql = density_proxy_case_sql("uu_status_des", "tuu_res")

    # `terminal_legs`'s own walk/wait selection (known at build time, not
    # per row: a plain Python branch, like `effective_terminal_scale`
    # above). `used_wait_min` ignores the carpool's own fixed 3-min
    # standing wait (`carpool_wait_sql`, section 9.6): `MTPSATTENT`/
    # `V2_MTPSATTENT` is a PT/train-only question in both surveys
    # (`docs/spec/09_trip_legs_energy.md`, section 9.6), so it has
    # nothing to say about a carpool meeting-point wait.
    plus1_modes_sql = ", ".join(f"'{m}'" for m in _DECLARED_PLUS1_MODES)
    if terminal_legs == "defaults":
        used_walk_min_sql = "default_walk_min"
        used_wait_min_sql = "wait_min"
    elif terminal_legs == "declared":
        used_walk_min_sql = "coalesce(declared_walk_min, default_walk_min)"
        used_wait_min_sql = "coalesce(declared_wait_min, wait_min)"
    else:  # 'declared_plus1'
        used_walk_min_sql = (
            "coalesce(declared_walk_min, default_walk_min) + CASE WHEN "
            f"mode_group IN ({plus1_modes_sql}) THEN 1.0 ELSE 0.0 END"
        )
        used_wait_min_sql = "coalesce(declared_wait_min, wait_min)"

    sql = f"""
    CREATE OR REPLACE VIEW trip_legs AS
    WITH joined AS (
        SELECT
            ident_dep, ident_ind, ident_men, day_id, pond_jour, pond_ind,
            typejour, mobloc, num_dep, moridom, duration_min,
            distance_km_declared, maccompm, maccomphm, mtp,
            motive, is_loop_trip, age, age_band, population_category,
            declared_walk_min, declared_wait_min,
            CASE
                WHEN mtp IS NULL OR mtp = 9999 THEN 'other'
                WHEN floor(mtp) = 1 THEN 'walk'
                WHEN mtp IN (2.1, 2.2) THEN 'cycle'
                WHEN mtp IN (3.1, 3.3) THEN 'car_driver'
                WHEN mtp = 3.2 AND coalesce(maccomphm, 0) > 0
                    AND coalesce(maccompm, 0) = 0 THEN 'car_passenger_carpool'
                WHEN mtp = 3.2 THEN 'car_passenger_household'
                WHEN mtp IN (5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7) THEN 'urban_pt'
                WHEN mtp IN (5.8, 5.9) OR floor(mtp) = 6 THEN 'train'
                ELSE 'other'
            END AS mode_group,
            {vehicle_mapping_sql} AS vehicle,
            ({density_ori_sql}) AS density_ori,
            ({density_des_sql}) AS density_des
        FROM trips_norm
    ),
    -- Terminal-leg defaults (section 9.4-9.7), computed from `density_ori`/
    -- `density_des`/`vehicle` alone: moved ahead of the speed/distance
    -- correction and bike ride-time chain below (unlike the pre-27
    -- October 2026 pipeline, where they came after it) because
    -- `terminal_used`'s `used_walk_min` -- the `'declared'`/
    -- `'declared_plus1'` terminal-leg walk, replacing these defaults --
    -- must be available before `walk_cycle`'s bike ride-time estimate,
    -- which also uses it (the bike's own terminal leg) instead of the
    -- fixed `bike_get_park_total_min_sql`.
    terminal_defaults AS (
        SELECT *,
            {_case_sql("density_ori", walk_to_car_by_density)} AS walk_to_car_min,
            {_case_sql("density_des", parking_search_by_density)} AS parking_search_min,
            {_case_sql("density_des", walk_from_car_by_density)} AS walk_from_car_min,
            {_case_sql("density_ori", access_walk_min_by_density)}
                AS access_walk_ori_min,
            {_case_sql("density_des", access_walk_min_by_density)}
                AS access_walk_des_min,
            {_case_sql("vehicle", {v: t for v, (t, _, _) in stair_legs.items()})}
                AS stairs_time_min,
            {_case_sql("vehicle", {v: e for v, (_, e, _) in stair_legs.items()})}
                AS stairs_energy_kh_kj,
            {_case_sql("vehicle", {v: e for v, (_, _, e) in stair_legs.items()})}
                AS stairs_energy_cp_kj,
            {_case_sql("vehicle", wait_minutes)} AS wait_min,
            {_case_sql("vehicle", ride_rate)} AS ride_rate_kj_per_min
        FROM joined
    ),
    terminal_used AS (
        SELECT *,
            -- Section 9.9's "declared" terminal-leg walk, one combined
            -- minutes figure per mode (no separate to/from-car split in
            -- either survey's `MTEMPSMAP`/`V2_MTEMPSMAP`, "how long did
            -- you walk in total during this trip").
            CASE mode_group
                WHEN 'car_driver' THEN walk_to_car_min + walk_from_car_min
                WHEN 'car_passenger_household' THEN walk_to_car_min + walk_from_car_min
                WHEN 'car_passenger_carpool' THEN
                    {carpool_walk_sql} + walk_from_car_min
                WHEN 'urban_pt' THEN access_walk_ori_min + access_walk_des_min
                WHEN 'train' THEN access_walk_ori_min + access_walk_des_min
                WHEN 'cycle' THEN {bike_get_park_total_min_sql}
                ELSE NULL
            END AS default_walk_min
        FROM terminal_defaults
    ),
    terminal_final AS (
        SELECT *,
            ({used_walk_min_sql}) AS used_walk_min,
            ({used_wait_min_sql}) AS used_wait_min
        FROM terminal_used
    ),
    speed_quality AS (
        SELECT *,
            CASE WHEN duration_min > 0 THEN
                distance_km_declared / (duration_min / 60.0)
            END AS implied_speed_kmh_declared
        FROM terminal_final
    ),
    speed_flagged AS (
        SELECT *,
            ({speed_flagged_upper_sql}) AS speed_flagged_upper
        FROM speed_quality
    ),
    speed_medians AS (
        SELECT *,
            -- One shared median per mode, from the *not*-flagged trips
            -- (section 9.9's data-quality correction): the window has no
            -- PARTITION BY, so every row of the walk (resp. car, cycle)
            -- rows sees the same one value.
            median(implied_speed_kmh_declared) FILTER (
                WHERE mode_group = 'walk' AND NOT speed_flagged_upper
            ) OVER () AS walk_median_speed_kmh,
            median(implied_speed_kmh_declared) FILTER (
                WHERE mode_group IN ({car_modes_sql}) AND NOT speed_flagged_upper
            ) OVER () AS car_median_speed_kmh,
            median(implied_speed_kmh_declared) FILTER (
                WHERE mode_group = 'cycle' AND NOT speed_flagged_upper
            ) OVER () AS cycle_median_speed_kmh
        FROM speed_flagged
    ),
    corrected AS (
        SELECT *,
            -- Correct, don't drop (section 9.9, step 11 round 5):
            -- distance = declared duration x the mode's median speed,
            -- for the trips flagged above the upper speed bound only.
            -- Cycling energy's main work term is time-based (round 4),
            -- but its "stops" sub-term still multiplies by distance_km
            -- and by the (distance-derived) ride speed squared, so an
            -- uncorrected implausible declared distance still reaches
            -- the energy formula through it (round 9: a single ENTD
            -- 2008 day with a declared 376 km/65 min cycling leg, c.
            -- 347 km/h, inflated that one day's energy to ~1.3M kJ and,
            -- through its section 9.9 population weight, the whole
            -- group's and the 2008-2019 comparison's headline means);
            -- cycle is corrected here like walk and car, not left
            -- "flagged but uncorrected".
            CASE
                WHEN mode_group = 'walk' AND speed_flagged_upper
                    THEN duration_min / 60.0 * walk_median_speed_kmh
                WHEN mode_group IN ({car_modes_sql}) AND speed_flagged_upper
                    THEN duration_min / 60.0 * car_median_speed_kmh
                WHEN mode_group = 'cycle' AND speed_flagged_upper
                    THEN duration_min / 60.0 * cycle_median_speed_kmh
                ELSE distance_km_declared
            END AS distance_km
        FROM speed_medians
    ),
    walk_cycle AS (
        SELECT *,
            CASE WHEN duration_min > 0 THEN distance_km / (duration_min / 60.0) END
                AS implied_speed_kmh,
            CASE WHEN mode_group = 'cycle' AND duration_min > 0 THEN
                distance_km * 1000.0 / (duration_min * 60.0)
            END AS bike_naive_speed_m_per_s,
            -- Bike-only: estimated terminal overhead (get/park -- the
            -- mode's own `used_walk_min`, section 9.9's declared-legs
            -- decision of 27 October 2026, replacing the fixed 2-min
            -- default where `terminal_legs` calls for it; expected stop
            -- delays, section 9.7's Webster 1958 formula) at the naive
            -- (whole-trip) speed, used to recover ride-only time
            -- (section 9.9, step 1's v0/P0 calibration).
            CASE WHEN mode_group = 'cycle' AND duration_min > 0 THEN
                {terminal_scale_sql} * (
                    used_walk_min * 60.0
                    + {stops_per_km_sql} * distance_km * (
                        (distance_km * 1000.0 / (duration_min * 60.0))
                        * ({stop_decel_term_sql} + {stop_accel_term_sql})
                        + {stop_fixed_wait_s_sql}
                    )
                )
            END AS bike_terminal_s_estimate
        FROM corrected
    ),
    bike_ride AS (
        SELECT *,
            -- Below `_BIKE_MIN_RIDE_TIME_S`/`_BIKE_MIN_RIDE_FRACTION` of
            -- ride time left, or above `_BIKE_MAX_PLAUSIBLE_SPEED_KMH`
            -- once adjusted, the adjustment is unreliable: fixed
            -- overheads cannot credibly consume almost all of a short
            -- trip, nor can a credible ride speed be this high.
            -- `bike_ride_time_s` is NULL and the energy formula falls
            -- back to the naive, whole-duration speed instead (see
            -- `bike_power` below).
            CASE WHEN bike_terminal_s_estimate IS NOT NULL
                AND duration_min * 60.0 - bike_terminal_s_estimate >= greatest(
                    {_dbl(_BIKE_MIN_RIDE_TIME_S)},
                    {_dbl(_BIKE_MIN_RIDE_FRACTION)} * duration_min * 60.0
                )
                AND distance_km * 3600.0
                    / (duration_min * 60.0 - bike_terminal_s_estimate)
                    <= {_dbl(_BIKE_MAX_PLAUSIBLE_SPEED_KMH)}
            THEN duration_min * 60.0 - bike_terminal_s_estimate
            END AS bike_ride_time_s
        FROM walk_cycle
    ),
    bike_speed AS (
        SELECT *,
            coalesce(
                CASE WHEN bike_ride_time_s IS NOT NULL THEN
                    distance_km * 1000.0 / bike_ride_time_s
                END,
                bike_naive_speed_m_per_s
            ) AS bike_ride_speed_m_per_s
        FROM bike_ride
    ),
    bike_power AS (
        SELECT *,
            -- Per-trip implied power at this trip's own (reliability-
            -- adjusted) ride speed; a diagnostic only, not used by the
            -- energy formula below (which charges every pedalled second
            -- at the single, population-level `bike_p0_w` instead -- see
            -- `build_trip_legs`'s docstring for why).
            CASE WHEN bike_ride_time_s IS NOT NULL THEN
                bike_ride_speed_m_per_s
                * ({mass_sql} * 9.81 * {crr_sql}
                    + 0.5 * {rho_air_sql} * {cda_sql} * pow(bike_ride_speed_m_per_s, 2))
                / {drivetrain_eff_sql}
            END AS p0_calibrated_w,
            coalesce(bike_ride_time_s, duration_min * 60.0)
                AS bike_ride_time_for_energy_s
        FROM bike_speed
    )
    SELECT
        ident_dep, ident_ind, ident_men, day_id, pond_jour, pond_ind, typejour,
        mobloc, num_dep, moridom, mtp, mode_group, vehicle, density_ori, density_des,
        age, age_band, population_category, is_loop_trip, motive,
        declared_walk_min, declared_wait_min,
        -- Modelled terminal-leg minutes (section 9.9, step 1: "compared
        -- with the modelled terminal legs by mode group"): car's
        -- walk-to/from-car, PT/train's access walk at both ends and the
        -- expected wait, plus `used_walk_min`/`used_wait_min`, the
        -- `terminal_legs`-selected values the energy formula below
        -- actually uses (27 October 2026 decision).
        walk_to_car_min, walk_from_car_min,
        access_walk_ori_min, access_walk_des_min, wait_min,
        used_walk_min, used_wait_min,
        duration_min, distance_km, distance_km_declared, implied_speed_kmh,
        implied_speed_kmh_declared, speed_flagged_upper, p0_calibrated_w,
        bike_ride_time_s, bike_ride_time_for_energy_s,

        CASE mode_group
            WHEN 'walk' THEN {mass_sql} * {c0_kh_sql} * distance_km
            WHEN 'cycle' THEN
                {bike_p0_w_sql}
                    / {muscular_eff_sql} * bike_ride_time_for_energy_s / 1000.0
                + {bike_unloaded_rate_kj_per_min_sql}
                    * bike_ride_time_for_energy_s / 60.0
                + {standing_kh_sql} * used_walk_min
                    * {terminal_scale_sql}
                + {stops_per_km_sql} * distance_km
                    * 0.5 * {bike_total_mass_sql}
                    * pow({bike_flat_speed_m_per_s_sql}, 2)
                    / {muscular_eff_sql} / 1000.0 * {terminal_scale_sql}
            WHEN 'car_driver' THEN
                {walk_rate_kh_sql} * {terminal_scale_sql} * used_walk_min
                + {driving_kh_sql} * {terminal_scale_sql} * parking_search_min
                + {driving_kh_sql} * greatest(duration_min
                    - {terminal_scale_sql} * (used_walk_min
                        + parking_search_min), 0)
            WHEN 'car_passenger_household' THEN
                {walk_rate_kh_sql} * {terminal_scale_sql} * used_walk_min
                + {sitting_kh_sql} * {terminal_scale_sql} * parking_search_min
                + {sitting_kh_sql} * greatest(duration_min
                    - {terminal_scale_sql} * (used_walk_min
                        + parking_search_min), 0)
            WHEN 'car_passenger_carpool' THEN
                {walk_rate_kh_sql} * {terminal_scale_sql} * used_walk_min
                + {standing_kh_sql} * {terminal_scale_sql} * {carpool_wait_sql}
                + {sitting_kh_sql} * {terminal_scale_sql} * parking_search_min
                + {sitting_kh_sql} * greatest(duration_min
                    - {terminal_scale_sql} * (used_walk_min
                        + {carpool_wait_sql} + parking_search_min), 0)
            WHEN 'urban_pt' THEN
                {walk_rate_kh_sql} * {terminal_scale_sql} * used_walk_min
                + {standing_kh_sql} * {terminal_scale_sql} * used_wait_min
                + {terminal_scale_sql} * stairs_energy_kh_kj
                + ride_rate_kj_per_min * greatest(duration_min
                    - {terminal_scale_sql} * (used_walk_min
                        + used_wait_min + stairs_time_min), 0)
            WHEN 'train' THEN
                {walk_rate_kh_sql} * {terminal_scale_sql} * used_walk_min
                + {standing_kh_sql} * {terminal_scale_sql} * used_wait_min
                + {terminal_scale_sql} * stairs_energy_kh_kj
                + ride_rate_kj_per_min * greatest(duration_min
                    - {terminal_scale_sql} * (used_walk_min
                        + used_wait_min + stairs_time_min), 0)
            ELSE NULL
        END AS energy_kh_kj,

        CASE mode_group
            WHEN 'walk' THEN {mass_sql} * {c0_cp_sql} * distance_km
            WHEN 'cycle' THEN
                {bike_p0_w_sql}
                    / {muscular_eff_sql} * bike_ride_time_for_energy_s / 1000.0
                + {bike_unloaded_rate_kj_per_min_sql}
                    * bike_ride_time_for_energy_s / 60.0
                + {standing_cp_sql} * used_walk_min
                    * {terminal_scale_sql}
                + {stops_per_km_sql} * distance_km
                    * 0.5 * {bike_total_mass_sql}
                    * pow({bike_flat_speed_m_per_s_sql}, 2)
                    / {muscular_eff_sql} / 1000.0 * {terminal_scale_sql}
            WHEN 'car_driver' THEN
                {walk_rate_cp_sql} * {terminal_scale_sql} * used_walk_min
                + {driving_cp_sql} * {terminal_scale_sql} * parking_search_min
                + {driving_cp_sql} * greatest(duration_min
                    - {terminal_scale_sql} * (used_walk_min
                        + parking_search_min), 0)
            WHEN 'car_passenger_household' THEN
                {walk_rate_cp_sql} * {terminal_scale_sql} * used_walk_min
                + {sitting_cp_sql} * {terminal_scale_sql} * parking_search_min
                + {sitting_cp_sql} * greatest(duration_min
                    - {terminal_scale_sql} * (used_walk_min
                        + parking_search_min), 0)
            WHEN 'car_passenger_carpool' THEN
                {walk_rate_cp_sql} * {terminal_scale_sql} * used_walk_min
                + {standing_cp_sql} * {terminal_scale_sql} * {carpool_wait_sql}
                + {sitting_cp_sql} * {terminal_scale_sql} * parking_search_min
                + {sitting_cp_sql} * greatest(duration_min
                    - {terminal_scale_sql} * (used_walk_min
                        + {carpool_wait_sql} + parking_search_min), 0)
            WHEN 'urban_pt' THEN
                {walk_rate_cp_sql} * {terminal_scale_sql} * used_walk_min
                + {standing_cp_sql} * {terminal_scale_sql} * used_wait_min
                + {terminal_scale_sql} * stairs_energy_cp_kj
                + ride_rate_kj_per_min * greatest(duration_min
                    - {terminal_scale_sql} * (used_walk_min
                        + used_wait_min + stairs_time_min), 0)
            WHEN 'train' THEN
                {walk_rate_cp_sql} * {terminal_scale_sql} * used_walk_min
                + {standing_cp_sql} * {terminal_scale_sql} * used_wait_min
                + {terminal_scale_sql} * stairs_energy_cp_kj
                + ride_rate_kj_per_min * greatest(duration_min
                    - {terminal_scale_sql} * (used_walk_min
                        + used_wait_min + stairs_time_min), 0)
            ELSE NULL
        END AS energy_cp_kj
    FROM bike_power
    """
    con.sql(sql)
