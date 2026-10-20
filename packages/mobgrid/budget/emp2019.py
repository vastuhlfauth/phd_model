"""EMP 2019 trip-leg reconstruction for section 9.9 (step 11).

Rebuilds each respondent's surveyed day as legs, reusing the section 9
formulas (``mobgrid.energy``) over the public EMP 2019 tables. Section
9.9's re-estimation step 1: "the main mode, the declared duration
(DUREE), the distance (MDISTTOT_fin), the purpose and the companions,
with the weight POND_JOUR"; terminal legs take the defaults of sections
9.4 to 9.7 by density class of the trip ends, and the vehicle leg takes
the rest of the declared duration.

EMP 2019 gives no headway, station-depth or PT access-distance data, so
these (``config.pt_ride.headway_min_am_peak``/``station_height_m``/
``access_walk_m_by_density``) are new, provisional, TODO(confirm) values
in ``config/energy.yaml``, in the spirit of section 9.3's own station
table; everything else (car terminal legs, activity rates, PT ride
crowding) reuses the values already calibrated for step 7.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import duckdb

from mobgrid.energy import legs, walk
from mobgrid.energy.rates import (
    MET_MINUTE_KJ_PER_KG,
    EnergyConfig,
    activity_rate_kj_per_min,
    sedentary_energy_kj,
)

#: Repository root, three levels above this file (packages/mobgrid/budget).
ROOT = Path(__file__).resolve().parents[3]

#: Default location of the EMP 2019 public data archive (`config/sources.yaml`
#: source id `emp2019-data`).
DEFAULT_ZIP_PATH = ROOT / "data" / "raw" / "emp2019" / "emp2019-data.zip"

#: Zip member name -> extracted CSV file name, for the five public tables
#: section 9.9 names (K_DEPLOC, TCM_IND, TCM_IND_KISH, K_INDIVIDU, Q_MENAGE).
ZIP_MEMBERS = {
    "5. k_deploc_public_V4.csv": "k_deploc.csv",
    "k_individu_public_V3.csv": "k_individu.csv",
    "tcm_ind_public_V3.csv": "tcm_ind.csv",
    "tcm_ind_kish_public_V3.csv": "tcm_ind_kish.csv",
    "q_menage_public_V3.csv": "q_menage.csv",
}

#: k_deploc uses a comma-quoted dialect; the other four tables are
#: semicolon-separated, unquoted.
_KDEPLOC_NAME = "k_deploc.csv"

#: Vehicle keys of `config.pt_ride` (`load_factor_max`, `standing_share_am_peak`,
#: `headway_min_am_peak`, `station_height_m`), mapped from EMP's `mtp` main
#: transport-mode code (section 9.9, "the main mode"). `mtp` codes follow
#: `data/raw/emp2019/emp2019-categories.pdf`'s "Moyen de transport" table.
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

#: Distance threshold splitting `train` into `train_short`/`train_long`
#: day-mode groups (section 9.9 point 3).
TRAIN_LONG_THRESHOLD_KM = 80.0

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
#: used by `emp.py`'s report. Cycling energy is time-based (not
#: distance-based) since round 4's fix, so only walk's and car's
#: corrected distances feed the energy formula.
WALK_SPEED_UPPER_KMH = 7.0
CYCLE_SPEED_UPPER_KMH = 35.0
CAR_SPEED_UPPER_KMH = 130.0
_CAR_MODE_GROUPS = (
    "car_driver", "car_passenger_household", "car_passenger_carpool",
)

#: `mode_group = 'other'` day-mode-group contents, stated for the report
#: (section 9.9 point 3, "State in the report what 'other' contains").
OTHER_MODE_DESCRIPTION = (
    "powered two-wheelers under 50cm3 or unspecified (mtp 2.3-2.7), "
    "unspecified 3/4-wheeler (mtp 3.4), taxi/specialised/school transport "
    "(mtp 4.x), plane (mtp 7.x), boat (mtp 8.1), other/unspecified "
    "(mtp 9.1, missing, or the 9999 refusal code)"
)

#: `k_deploc.MOT_SEQ_COMPL`'s own labels ("Motif corrige detaille de la
#: sequence", the chain-level, corrected trip purpose; unlike the raw,
#: trip-level `MMOTIFDES` used by `is_loop_trip` above, it has no
#: "return home"/"return to residence" codes 1.1-1.3, since a return leg
#: is recoded to the purpose of the outward leg it closes). Used by
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
#: `MOT_SEQ_COMPL`) is sport (7.6), a destination-less stroll (7.7, the
#: same purpose as `is_loop_trip`, via the raw `MMOTIFDES` instead) or
#: "going to a place to walk/ride" (7.8, destination exists, but the
#: movement itself is the point) are excluded from every day/energy
#: computation in step 11's report -- the whole report's base scope, not
#: an optional variant.
NEEDS_EXCLUDED_MOTIVE_CODES = (7.6, 7.7, 7.8)

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

#: `tcm_ind_kish_public`'s `SITUA` ("Situation principale vis-a-vis du
#: travail") codes, mapped to section 6.1's five population categories
#: (children 6-17, employed, unemployed, retired, other inactive).
#: Codes 1/2 = employed or paid trainee; 4 = unemployed; 5 = retired;
#: 3/6/7/8 = student/homemaker/other/unspecified inactive, all folded
#: into "other_inactive" (section 6.1: "students aged 18 or more,
#: homemakers, others").
_POPULATION_CATEGORY_BY_SITUA = {
    "1": "employed",
    "2": "employed",
    "3": "other_inactive",
    "4": "unemployed",
    "5": "retired",
    "6": "other_inactive",
    "7": "other_inactive",
    "8": "other_inactive",
}

#: EMP's 4-level `DENSITECOM_ORI`/`DENSITECOM_DES` codes (section 9.9
#: point 3: "the four levels of the INSEE density grid"), in the INSEE
#: grid's own order and names (`emp2019-categories.pdf`, "Degre de
#: densite"): 1 = densely populated, 2 = intermediate density, 3 =
#: sparsely populated ("peu denses"), 4 = very sparsely populated
#: ("tres peu denses").
_DENSITY_LABEL_BY_CODE = {
    1: "dense",
    2: "intermediate",
    3: "sparse",
    4: "very_sparse",
}

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


def _relabel_density(mapping: dict[str, float]) -> dict[str, float]:
    """Re-key a `config.car`/`config.pt_ride` density dict (`dense`,
    `urban`, `suburban`, `rural`) to the INSEE labels of
    `_DENSITY_LABEL_BY_CODE`."""
    return {_DENSITY_KEY_TRANSLATION[key]: value for key, value in mapping.items()}


def extract_tables(
    zip_path: Path = DEFAULT_ZIP_PATH, out_dir: Path | None = None
) -> dict[str, Path]:
    """Extract the five public tables to UTF-8 CSVs, resumable.

    The archive's CSVs are Windows-1252 encoded (French accents), which
    DuckDB's CSV reader does not accept; each file is decoded once and
    re-written as UTF-8 under ``out_dir`` (default
    ``data/interim/emp2019/csv``). Already-extracted files are kept.
    """
    if out_dir is None:
        out_dir = ROOT / "data" / "interim" / "emp2019" / "csv"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    with zipfile.ZipFile(zip_path) as archive:
        for member, dest_name in ZIP_MEMBERS.items():
            dest_path = out_dir / dest_name
            if not dest_path.exists():
                text = archive.read(member).decode("cp1252")
                dest_path.write_text(text, encoding="utf-8")
            paths[dest_name] = dest_path
    return paths


def register_views(con: duckdb.DuckDBPyConnection, csv_paths: dict[str, Path]) -> None:
    """Register the five extracted CSVs as DuckDB views."""
    for name, path in csv_paths.items():
        view_name = name.removesuffix(".csv")
        posix_path = path.as_posix()
        if name == _KDEPLOC_NAME:
            con.sql(
                f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_csv("
                f"'{posix_path}', delim=',', quote='\"', escape='\"', "
                "nullstr='NA', strict_mode=false)"
            )
        else:
            con.sql(
                f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_csv("
                f"'{posix_path}', delim=';', quote='', nullstr='NA', "
                "strict_mode=false)"
            )


def _implied_load_factor(standing_share: float) -> float:
    """Load factor consistent with a standing share (section 9.5).

    Inverts ``legs.pt_standing_share``: LF = 1 / (1 - p_s); mirrors
    ``mobgrid.energy.checks._implied_load_factor``.
    """
    return 1.0 / (1.0 - min(standing_share, 0.999_999))


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
            height_m, "down", config.reference_mass_kg,
            stairs.up_speed_m_per_s, stairs.down_speed_m_per_s,
            stairs.up_efficiency, stairs.down_to_up_energy_ratio,
        )
        up_s, up_e_kj = walk.stair_time_and_energy(
            height_m, "up", config.reference_mass_kg,
            stairs.up_speed_m_per_s, stairs.down_speed_m_per_s,
            stairs.up_efficiency, stairs.down_to_up_energy_ratio,
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
            headway_min * 60.0, cv, waiting.headway_regime_threshold_min * 60.0,
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
            load_factor, pt_ride.load_factor_max[vehicle], pt_ride.r_sit_kj_per_min,
            pt_ride.r_relaxed_kj_per_min, pt_ride.r_restless_kj_per_min,
        )
    return result


def build_trip_legs(
    con: duckdb.DuckDBPyConnection,
    config: EnergyConfig,
    *,
    terminal_scale: float = 1.0,
    bike_p0_override_w: float | None = None,
) -> None:
    """Create the ``trip_legs`` view: one row per EMP 2019 trip, with time
    and energy above rest (both rate sets) by leg (section 9.9, point 1).

    Reuses ``mobgrid.energy``'s public rate/leg formulas wherever a
    parameter is per-vehicle or per-density-class (computed once, in
    Python, over the handful of vehicle/density keys); only the
    arithmetic over the EMP rows themselves (tens of thousands) runs as
    vectorised DuckDB SQL.

    ``terminal_scale`` multiplies every terminal-leg time and energy
    component (walk-to/from-car, parking search, carpool walk/wait, PT
    access walk/wait/level-change, bike get-and-park and stops), with the
    main/ride/drive leg taking the rest of the declared duration (section
    9.9's F8 robustness check, "terminal legs x0.5, x1, x1.5").

    Cycling energy's work term is time-based at a single, population-level
    power, ``bike_p0_override_w`` if given, else ``config.bike.power.p0_w``
    (section 9.7's own force-balance power selection, flat ground, since
    EMP gives no gradient): every pedalled second is charged at this one
    rate, not at each trip's own noisy implied speed. Deriving power
    per-trip instead (speed, hence drag, hence power, is convex; EMP's
    durations are also rounded to 5/15/30/60 min) was found to inflate
    mean cycling energy several-fold above the population rate (section
    9.9, step 11 third round) -- the same Jensen's-inequality bias the
    ratio-of-weighted-sums v0/P0 estimator avoids for calibration, but
    that the energy formula used to reintroduce. ``p0_calibrated_w`` (the
    per-trip implied power) is still exposed, as a diagnostic only, no
    longer used by the energy formula.
    """
    mass = config.reference_mass_kg
    walking = config.walking
    bike_p0_w = (
        bike_p0_override_w if bike_p0_override_w is not None
        else config.bike.power.p0_w
    )
    if bike_p0_w is None:
        raise ValueError(
            "config.bike.power.p0_w is not set and no bike_p0_override_w "
            "was given: cycling energy has no power to use"
        )

    walk_rate_kh = walk.walking_time_and_energy(
        [(walking.v0_kmh * 1000.0 / 60.0, 0.0)], mass, walking.v0_kmh,
        walking.c0_j_per_kg_m["kh"], walking.gradient_polynomial_j_per_kg_m,
    )[1]
    walk_rate_cp = walk.walking_time_and_energy(
        [(walking.v0_kmh * 1000.0 / 60.0, 0.0)], mass, walking.v0_kmh,
        walking.c0_j_per_kg_m["compendium"], walking.gradient_polynomial_j_per_kg_m,
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
    access_walk_min_by_density = _relabel_density({
        density: metres / v0_m_per_s / 60.0
        for density, metres in config.pt_ride.access_walk_m_by_density.items()
    })
    stair_legs = _vehicle_stair_legs(config, (standing_kh, standing_cp))
    wait_minutes = _vehicle_wait_minutes(config)
    ride_rate = _vehicle_ride_rate_kj_per_min(config)

    car = config.car
    bike = config.bike
    stops = bike.stops
    crr = bike.surface_crr["asphalt_concrete_paved_default"]
    bike_total_mass = mass + bike.bike_mass_kg
    walk_to_car_by_density = _relabel_density(car.walk_to_car.apartment_min_by_density)
    parking_search_by_density = _relabel_density(car.parking_search_min_by_density)
    walk_from_car_by_density = _relabel_density(car.walk_from_car_min_by_density)

    # DOUBLE-cast SQL literals of every scalar embedded directly below
    # (see `_dbl`'s docstring for why the cast matters).
    mass_sql = _dbl(mass)
    crr_sql = _dbl(crr)
    rho_air_sql = _dbl(bike.rho_air_kg_per_m3)
    cda_sql = _dbl(bike.cda_m2)
    drivetrain_eff_sql = _dbl(bike.drivetrain_efficiency)
    muscular_eff_sql = _dbl(bike.gross_muscular_efficiency)
    bike_total_mass_sql = _dbl(bike_total_mass)
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
    terminal_scale_sql = _dbl(terminal_scale)
    train_threshold_sql = _dbl(TRAIN_LONG_THRESHOLD_KM)
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

    vehicle_mapping_sql = "CASE mtp\n    " + "\n    ".join(
        f"WHEN {code} THEN '{vehicle}'" for code, vehicle in _VEHICLE_BY_MTP.items()
    ) + "\n    ELSE NULL\nEND"
    population_category_sql = _case_sql(
        "k.SITUA", _POPULATION_CATEGORY_BY_SITUA, default="'unknown'",
        quote_values=True,
    )
    # `_case_sql`'s non-quoted branch wraps every value in `_dbl` (a DOUBLE
    # cast); density labels are strings, so build the CASE directly here.
    density_ori_sql = "CASE d.DENSITECOM_ORI\n    " + "\n    ".join(
        f"WHEN {code} THEN '{label}'" for code, label in _DENSITY_LABEL_BY_CODE.items()
    ) + "\n    ELSE 'intermediate'\nEND"
    density_des_sql = "CASE d.DENSITECOM_DES\n    " + "\n    ".join(
        f"WHEN {code} THEN '{label}'" for code, label in _DENSITY_LABEL_BY_CODE.items()
    ) + "\n    ELSE 'intermediate'\nEND"

    sql = f"""
    CREATE OR REPLACE VIEW trip_legs AS
    WITH joined AS (
        SELECT
            d.IDENT_DEP AS ident_dep,
            d.IDENT_IND AS ident_ind,
            d.IDENT_MEN AS ident_men,
            d.POND_JOUR AS pond_jour,
            d.TYPEJOUR AS typejour,
            d.mobloc AS mobloc,
            d.num_dep AS num_dep,
            d.MORIDOM AS moridom,
            d.DUREE AS duration_min,
            d.MDISTTOT_fin AS distance_km_declared,
            d.MACCOMPM AS maccompm,
            d.MACCOMPHM AS maccomphm,
            -- EMP's own "corrected, detailed motive of the sequence"
            -- (MOT_SEQ_COMPL): unlike the raw, trip-level MMOTIFDES
            -- used by `is_loop_trip` below, this is chain-level and
            -- excludes "return home"/"return to residence" codes
            -- (1.1-1.3), used by `emp._compute_motive_decomposition`
            -- (section 9.9 point 1 follow-up) to find which purposes
            -- dominate a mode's energy, in particular cycling's.
            CASE WHEN d.MOT_SEQ_COMPL = {_dbl(9999.0)} THEN NULL
                ELSE d.MOT_SEQ_COMPL
            END AS motive,
            -- Trips without a real destination (section 9.9's "leisure
            -- loops"): EMP's own purpose code 7.7 "se promener sans
            -- destination precise" (stroll, no specific destination);
            -- code 7.8 ("go to a place for walking") has a destination
            -- and does not count. EMP's public release has no
            -- commune-level origin field (destination only, disclosure
            -- control), so an "origin = destination" geometry check is
            -- not available; this purpose code is EMP's own
            -- operationalisation of the same concept.
            d.MMOTIFDES = {_dbl(7.7)} AS is_loop_trip,
            CASE
                WHEN d.mtp IS NULL OR d.mtp = 9999 THEN 'other'
                WHEN floor(d.mtp) = 1 THEN 'walk'
                WHEN d.mtp IN (2.1, 2.2) THEN 'cycle'
                WHEN d.mtp IN (3.1, 3.3) THEN 'car_driver'
                WHEN d.mtp = 3.2 AND coalesce(d.MACCOMPHM, 0) > 0
                    AND coalesce(d.MACCOMPM, 0) = 0 THEN 'car_passenger_carpool'
                WHEN d.mtp = 3.2 THEN 'car_passenger_household'
                WHEN d.mtp IN (5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7) THEN 'urban_pt'
                WHEN (d.mtp IN (5.8, 5.9) OR floor(d.mtp) = 6)
                    AND d.MDISTTOT_fin < {train_threshold_sql} THEN 'train_short'
                WHEN d.mtp IN (5.8, 5.9) OR floor(d.mtp) = 6 THEN 'train_long'
                ELSE 'other'
            END AS mode_group,
            {vehicle_mapping_sql} AS vehicle,
            -- EMP's 4-level DENSITECOM_ORI/DES (section 9.9 point 3: "the
            -- four levels of the INSEE density grid"), in the INSEE
            -- grid's own names and order; stray/missing codes default to
            -- 'intermediate'.
            {density_ori_sql} AS density_ori,
            {density_des_sql} AS density_des,
            k.AGE AS age,
            k.AGE6 AS age_band,
            -- Section 6.1's five population categories: children under
            -- 18 (6-17 in this travel survey), employed, unemployed,
            -- retired, other inactive (students 18+, homemakers, others).
            CASE
                WHEN k.AGE BETWEEN 6 AND 17 THEN 'children_6_17'
                ELSE {population_category_sql}
            END AS population_category,
            i.pond_indC AS pond_ind
        FROM k_deploc d
        JOIN tcm_ind_kish k ON k.IDENT_IND = d.IDENT_IND
        JOIN k_individu i ON i.IDENT_IND = d.IDENT_IND
    ),
    speed_quality AS (
        SELECT *,
            CASE WHEN duration_min > 0 THEN
                distance_km_declared / (duration_min / 60.0)
            END AS implied_speed_kmh_declared
        FROM joined
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
            -- PARTITION BY, so every row of the walk (resp. car) rows
            -- sees the same one value.
            median(implied_speed_kmh_declared) FILTER (
                WHERE mode_group = 'walk' AND NOT speed_flagged_upper
            ) OVER () AS walk_median_speed_kmh,
            median(implied_speed_kmh_declared) FILTER (
                WHERE mode_group IN ({car_modes_sql}) AND NOT speed_flagged_upper
            ) OVER () AS car_median_speed_kmh
        FROM speed_flagged
    ),
    corrected AS (
        SELECT *,
            -- Correct, don't drop (section 9.9, step 11 round 5):
            -- distance = declared duration x the mode's median speed,
            -- for the trips flagged above the upper speed bound only.
            -- Cycling energy is time-based (round 4), so only walk's and
            -- car's corrected distances matter to the energy formulas
            -- below; bike is flagged (reported) but not corrected.
            CASE
                WHEN mode_group = 'walk' AND speed_flagged_upper
                    THEN duration_min / 60.0 * walk_median_speed_kmh
                WHEN mode_group IN ({car_modes_sql}) AND speed_flagged_upper
                    THEN duration_min / 60.0 * car_median_speed_kmh
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
            -- Bike-only: estimated terminal overhead (get/park, section
            -- 9.7's "about 1 min each"; expected stop delays, section
            -- 9.7's Webster 1958 formula) at the naive (whole-trip)
            -- speed, used to recover ride-only time (section 9.9, step
            -- 1's v0/P0 calibration).
            CASE WHEN mode_group = 'cycle' AND duration_min > 0 THEN
                {terminal_scale_sql} * (
                    {bike_get_park_total_min_sql} * 60.0
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
    ),
    car_terminal AS (
        SELECT *,
            {_case_sql("density_ori", walk_to_car_by_density)} AS walk_to_car_min,
            {_case_sql("density_des", parking_search_by_density)} AS parking_search_min,
            {_case_sql("density_des", walk_from_car_by_density)} AS walk_from_car_min
        FROM bike_power
    ),
    pt_terminal AS (
        SELECT *,
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
        FROM car_terminal
    )
    SELECT
        ident_dep, ident_ind, ident_men, pond_jour, pond_ind, typejour, mobloc,
        num_dep, moridom, mode_group, vehicle, density_ori, density_des,
        age, age_band, population_category, is_loop_trip, motive,
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
                + {standing_kh_sql} * {bike_get_park_total_min_sql}
                    * {terminal_scale_sql}
                + {stops_per_km_sql} * distance_km
                    * 0.5 * {bike_total_mass_sql} * pow(bike_ride_speed_m_per_s, 2)
                    / {muscular_eff_sql} / 1000.0 * {terminal_scale_sql}
            WHEN 'car_driver' THEN
                {walk_rate_kh_sql} * {terminal_scale_sql}
                    * (walk_to_car_min + walk_from_car_min)
                + {driving_kh_sql} * {terminal_scale_sql} * parking_search_min
                + {driving_kh_sql} * greatest(duration_min
                    - {terminal_scale_sql} * (walk_to_car_min
                        + parking_search_min + walk_from_car_min), 0)
            WHEN 'car_passenger_household' THEN
                {walk_rate_kh_sql} * {terminal_scale_sql}
                    * (walk_to_car_min + walk_from_car_min)
                + {sitting_kh_sql} * {terminal_scale_sql} * parking_search_min
                + {sitting_kh_sql} * greatest(duration_min
                    - {terminal_scale_sql} * (walk_to_car_min
                        + parking_search_min + walk_from_car_min), 0)
            WHEN 'car_passenger_carpool' THEN
                {walk_rate_kh_sql} * {terminal_scale_sql}
                    * ({carpool_walk_sql} + walk_from_car_min)
                + {standing_kh_sql} * {terminal_scale_sql} * {carpool_wait_sql}
                + {sitting_kh_sql} * {terminal_scale_sql} * parking_search_min
                + {sitting_kh_sql} * greatest(duration_min
                    - {terminal_scale_sql} * ({carpool_walk_sql}
                        + {carpool_wait_sql} + parking_search_min
                        + walk_from_car_min), 0)
            WHEN 'urban_pt' THEN
                {walk_rate_kh_sql} * {terminal_scale_sql}
                    * (access_walk_ori_min + access_walk_des_min)
                + {standing_kh_sql} * {terminal_scale_sql} * wait_min
                + {terminal_scale_sql} * stairs_energy_kh_kj
                + ride_rate_kj_per_min * greatest(duration_min
                    - {terminal_scale_sql} * (access_walk_ori_min
                        + access_walk_des_min + wait_min + stairs_time_min), 0)
            WHEN 'train_short' THEN
                {walk_rate_kh_sql} * {terminal_scale_sql}
                    * (access_walk_ori_min + access_walk_des_min)
                + {standing_kh_sql} * {terminal_scale_sql} * wait_min
                + {terminal_scale_sql} * stairs_energy_kh_kj
                + ride_rate_kj_per_min * greatest(duration_min
                    - {terminal_scale_sql} * (access_walk_ori_min
                        + access_walk_des_min + wait_min + stairs_time_min), 0)
            WHEN 'train_long' THEN
                {walk_rate_kh_sql} * {terminal_scale_sql}
                    * (access_walk_ori_min + access_walk_des_min)
                + {standing_kh_sql} * {terminal_scale_sql} * wait_min
                + {terminal_scale_sql} * stairs_energy_kh_kj
                + ride_rate_kj_per_min * greatest(duration_min
                    - {terminal_scale_sql} * (access_walk_ori_min
                        + access_walk_des_min + wait_min + stairs_time_min), 0)
            ELSE NULL
        END AS energy_kh_kj,

        CASE mode_group
            WHEN 'walk' THEN {mass_sql} * {c0_cp_sql} * distance_km
            WHEN 'cycle' THEN
                {bike_p0_w_sql}
                    / {muscular_eff_sql} * bike_ride_time_for_energy_s / 1000.0
                + {bike_unloaded_rate_kj_per_min_sql}
                    * bike_ride_time_for_energy_s / 60.0
                + {standing_cp_sql} * {bike_get_park_total_min_sql}
                    * {terminal_scale_sql}
                + {stops_per_km_sql} * distance_km
                    * 0.5 * {bike_total_mass_sql} * pow(bike_ride_speed_m_per_s, 2)
                    / {muscular_eff_sql} / 1000.0 * {terminal_scale_sql}
            WHEN 'car_driver' THEN
                {walk_rate_cp_sql} * {terminal_scale_sql}
                    * (walk_to_car_min + walk_from_car_min)
                + {driving_cp_sql} * {terminal_scale_sql} * parking_search_min
                + {driving_cp_sql} * greatest(duration_min
                    - {terminal_scale_sql} * (walk_to_car_min
                        + parking_search_min + walk_from_car_min), 0)
            WHEN 'car_passenger_household' THEN
                {walk_rate_cp_sql} * {terminal_scale_sql}
                    * (walk_to_car_min + walk_from_car_min)
                + {sitting_cp_sql} * {terminal_scale_sql} * parking_search_min
                + {sitting_cp_sql} * greatest(duration_min
                    - {terminal_scale_sql} * (walk_to_car_min
                        + parking_search_min + walk_from_car_min), 0)
            WHEN 'car_passenger_carpool' THEN
                {walk_rate_cp_sql} * {terminal_scale_sql}
                    * ({carpool_walk_sql} + walk_from_car_min)
                + {standing_cp_sql} * {terminal_scale_sql} * {carpool_wait_sql}
                + {sitting_cp_sql} * {terminal_scale_sql} * parking_search_min
                + {sitting_cp_sql} * greatest(duration_min
                    - {terminal_scale_sql} * ({carpool_walk_sql}
                        + {carpool_wait_sql} + parking_search_min
                        + walk_from_car_min), 0)
            WHEN 'urban_pt' THEN
                {walk_rate_cp_sql} * {terminal_scale_sql}
                    * (access_walk_ori_min + access_walk_des_min)
                + {standing_cp_sql} * {terminal_scale_sql} * wait_min
                + {terminal_scale_sql} * stairs_energy_cp_kj
                + ride_rate_kj_per_min * greatest(duration_min
                    - {terminal_scale_sql} * (access_walk_ori_min
                        + access_walk_des_min + wait_min + stairs_time_min), 0)
            WHEN 'train_short' THEN
                {walk_rate_cp_sql} * {terminal_scale_sql}
                    * (access_walk_ori_min + access_walk_des_min)
                + {standing_cp_sql} * {terminal_scale_sql} * wait_min
                + {terminal_scale_sql} * stairs_energy_cp_kj
                + ride_rate_kj_per_min * greatest(duration_min
                    - {terminal_scale_sql} * (access_walk_ori_min
                        + access_walk_des_min + wait_min + stairs_time_min), 0)
            WHEN 'train_long' THEN
                {walk_rate_cp_sql} * {terminal_scale_sql}
                    * (access_walk_ori_min + access_walk_des_min)
                + {standing_cp_sql} * {terminal_scale_sql} * wait_min
                + {terminal_scale_sql} * stairs_energy_cp_kj
                + ride_rate_kj_per_min * greatest(duration_min
                    - {terminal_scale_sql} * (access_walk_ori_min
                        + access_walk_des_min + wait_min + stairs_time_min), 0)
            ELSE NULL
        END AS energy_cp_kj
    FROM pt_terminal
    """
    con.sql(sql)
