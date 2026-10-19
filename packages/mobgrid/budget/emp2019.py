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

#: `tcm_ind_kish_public`'s `SITUA` ("Situation principale vis-a-vis du
#: travail") codes, mapped to section 9.9 point 3's age-activity groups.
#: Codes 1/2 = employed or paid trainee; 3 = student; 4 = unemployed;
#: 5 = retired; 6/7/8 = homemaker/other/unspecified inactive.
_ACTIVITY_BY_SITUA = {
    "1": "employed",
    "2": "employed",
    "3": "student",
    "4": "unemployed",
    "5": "retired",
    "6": "other_inactive",
    "7": "other_inactive",
    "8": "other_inactive",
}


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


def build_trip_legs(con: duckdb.DuckDBPyConnection, config: EnergyConfig) -> None:
    """Create the ``trip_legs`` view: one row per EMP 2019 trip, with time
    and energy above rest (both rate sets) by leg (section 9.9, point 1).

    Reuses ``mobgrid.energy``'s public rate/leg formulas wherever a
    parameter is per-vehicle or per-density-class (computed once, in
    Python, over the handful of vehicle/density keys); only the
    arithmetic over the EMP rows themselves (tens of thousands) runs as
    vectorised DuckDB SQL.
    """
    mass = config.reference_mass_kg
    walking = config.walking

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
    access_walk_min_by_density = {
        density: metres / v0_m_per_s / 60.0
        for density, metres in config.pt_ride.access_walk_m_by_density.items()
    }
    stair_legs = _vehicle_stair_legs(config, (standing_kh, standing_cp))
    wait_minutes = _vehicle_wait_minutes(config)
    ride_rate = _vehicle_ride_rate_kj_per_min(config)

    car = config.car
    bike = config.bike
    crr = bike.surface_crr["asphalt_concrete_paved_default"]

    # DOUBLE-cast SQL literals of every scalar embedded directly below
    # (see `_dbl`'s docstring for why the cast matters).
    mass_sql = _dbl(mass)
    crr_sql = _dbl(crr)
    rho_air_sql = _dbl(bike.rho_air_kg_per_m3)
    cda_sql = _dbl(bike.cda_m2)
    drivetrain_eff_sql = _dbl(bike.drivetrain_efficiency)
    muscular_eff_sql = _dbl(bike.gross_muscular_efficiency)
    c0_kh_sql = _dbl(config.walking.c0_j_per_kg_m["kh"])
    c0_cp_sql = _dbl(config.walking.c0_j_per_kg_m["compendium"])
    walk_rate_kh_sql, walk_rate_cp_sql = _dbl(walk_rate_kh), _dbl(walk_rate_cp)
    standing_kh_sql, standing_cp_sql = _dbl(standing_kh), _dbl(standing_cp)
    sitting_kh_sql, sitting_cp_sql = _dbl(sitting_kh), _dbl(sitting_cp)
    driving_kh_sql, driving_cp_sql = _dbl(driving_kh), _dbl(driving_cp)
    carpool_walk_sql = _dbl(car.carpool_passenger.walk_to_meeting_point_min)
    carpool_wait_sql = _dbl(car.carpool_passenger.wait_standing_min)

    vehicle_mapping_sql = "CASE mtp\n    " + "\n    ".join(
        f"WHEN {code} THEN '{vehicle}'" for code, vehicle in _VEHICLE_BY_MTP.items()
    ) + "\n    ELSE NULL\nEND"
    activity_group_sql = _case_sql(
        "k.SITUA", _ACTIVITY_BY_SITUA, default="'unknown'", quote_values=True
    )

    sql = f"""
    CREATE OR REPLACE VIEW trip_legs AS
    WITH joined AS (
        SELECT
            d.IDENT_DEP AS ident_dep,
            d.IDENT_IND AS ident_ind,
            d.IDENT_MEN AS ident_men,
            d.POND_JOUR AS pond_jour,
            d.TYPEJOUR AS typejour,
            d.num_dep AS num_dep,
            d.MORIDOM AS moridom,
            d.DUREE AS duration_min,
            d.MDISTTOT_fin AS distance_km,
            d.MACCOMPM AS maccompm,
            d.MACCOMPHM AS maccomphm,
            CASE
                WHEN d.mtp IS NULL OR d.mtp = 9999 THEN 'other'
                WHEN floor(d.mtp) = 1 THEN 'walk'
                WHEN d.mtp IN (2.1, 2.2) THEN 'cycle'
                WHEN d.mtp IN (3.1, 3.3) THEN 'car_driver'
                WHEN d.mtp = 3.2 AND coalesce(d.MACCOMPHM, 0) > 0
                    AND coalesce(d.MACCOMPM, 0) = 0 THEN 'car_passenger_carpool'
                WHEN d.mtp = 3.2 THEN 'car_passenger_household'
                WHEN d.mtp IN (5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7) THEN 'urban_pt'
                WHEN d.mtp IN (5.8, 5.9) OR floor(d.mtp) = 6 THEN 'train'
                ELSE 'other'
            END AS mode_group,
            {vehicle_mapping_sql} AS vehicle,
            -- EMP's 4-level DENSITECOM_ORI/DES (section 9.9 point 3: "the
            -- four levels of the INSEE density grid"): 1 = densely
            -- populated communes ... 4 = very low density; stray/missing
            -- codes default to 'urban'.
            CASE d.DENSITECOM_ORI WHEN 1 THEN 'dense' WHEN 2 THEN 'urban'
                WHEN 3 THEN 'suburban' WHEN 4 THEN 'rural'
                ELSE 'urban' END AS density_ori,
            CASE d.DENSITECOM_DES WHEN 1 THEN 'dense' WHEN 2 THEN 'urban'
                WHEN 3 THEN 'suburban' WHEN 4 THEN 'rural'
                ELSE 'urban' END AS density_des,
            k.AGE AS age,
            k.AGE6 AS age_band,
            CASE
                WHEN k.AGE BETWEEN 6 AND 17 THEN 'children_6_17'
                ELSE {activity_group_sql}
            END AS age_activity_group,
            i.pond_indC AS pond_ind
        FROM k_deploc d
        JOIN tcm_ind_kish k ON k.IDENT_IND = d.IDENT_IND
        JOIN k_individu i ON i.IDENT_IND = d.IDENT_IND
    ),
    walk_cycle AS (
        SELECT *,
            CASE WHEN duration_min > 0 THEN distance_km / (duration_min / 60.0) END
                AS implied_speed_kmh,
            CASE WHEN mode_group = 'cycle' AND duration_min > 0 THEN
                (distance_km * 1000.0 / (duration_min * 60.0))
                * ({mass_sql} * 9.81 * {crr_sql}
                    + 0.5 * {rho_air_sql} * {cda_sql}
                      * pow(distance_km * 1000.0 / (duration_min * 60.0), 2))
                / {drivetrain_eff_sql}
            END AS p0_calibrated_w
        FROM joined
    ),
    car_terminal AS (
        SELECT *,
            {_case_sql("density_ori", car.walk_to_car.apartment_min_by_density)}
                AS walk_to_car_min,
            {_case_sql("density_des", car.parking_search_min_by_density)}
                AS parking_search_min,
            {_case_sql("density_des", car.walk_from_car_min_by_density)}
                AS walk_from_car_min
        FROM walk_cycle
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
        ident_dep, ident_ind, ident_men, pond_jour, pond_ind, typejour,
        num_dep, moridom, mode_group, vehicle, density_ori, density_des,
        age, age_band, age_activity_group,
        duration_min, distance_km, implied_speed_kmh, p0_calibrated_w,

        CASE mode_group
            WHEN 'walk' THEN {mass_sql} * {c0_kh_sql} * distance_km
            WHEN 'cycle' THEN p0_calibrated_w / {muscular_eff_sql}
                * duration_min * 60.0 / 1000.0
            WHEN 'car_driver' THEN
                {walk_rate_kh_sql} * (walk_to_car_min + walk_from_car_min)
                + {driving_kh_sql} * parking_search_min
                + {driving_kh_sql} * greatest(duration_min - walk_to_car_min
                    - parking_search_min - walk_from_car_min, 0)
            WHEN 'car_passenger_household' THEN
                {walk_rate_kh_sql} * (walk_to_car_min + walk_from_car_min)
                + {sitting_kh_sql} * parking_search_min
                + {sitting_kh_sql} * greatest(duration_min - walk_to_car_min
                    - parking_search_min - walk_from_car_min, 0)
            WHEN 'car_passenger_carpool' THEN
                {walk_rate_kh_sql} * ({carpool_walk_sql} + walk_from_car_min)
                + {standing_kh_sql} * {carpool_wait_sql}
                + {sitting_kh_sql} * parking_search_min
                + {sitting_kh_sql} * greatest(duration_min
                    - {carpool_walk_sql} - {carpool_wait_sql}
                    - parking_search_min - walk_from_car_min, 0)
            WHEN 'urban_pt' THEN
                {walk_rate_kh_sql} * (access_walk_ori_min + access_walk_des_min)
                + {standing_kh_sql} * wait_min + stairs_energy_kh_kj
                + ride_rate_kj_per_min * greatest(duration_min
                    - access_walk_ori_min - access_walk_des_min
                    - wait_min - stairs_time_min, 0)
            WHEN 'train' THEN
                {walk_rate_kh_sql} * (access_walk_ori_min + access_walk_des_min)
                + {standing_kh_sql} * wait_min + stairs_energy_kh_kj
                + ride_rate_kj_per_min * greatest(duration_min
                    - access_walk_ori_min - access_walk_des_min
                    - wait_min - stairs_time_min, 0)
            ELSE NULL
        END AS energy_kh_kj,

        CASE mode_group
            WHEN 'walk' THEN {mass_sql} * {c0_cp_sql} * distance_km
            WHEN 'cycle' THEN p0_calibrated_w / {muscular_eff_sql}
                * duration_min * 60.0 / 1000.0
            WHEN 'car_driver' THEN
                {walk_rate_cp_sql} * (walk_to_car_min + walk_from_car_min)
                + {driving_cp_sql} * parking_search_min
                + {driving_cp_sql} * greatest(duration_min - walk_to_car_min
                    - parking_search_min - walk_from_car_min, 0)
            WHEN 'car_passenger_household' THEN
                {walk_rate_cp_sql} * (walk_to_car_min + walk_from_car_min)
                + {sitting_cp_sql} * parking_search_min
                + {sitting_cp_sql} * greatest(duration_min - walk_to_car_min
                    - parking_search_min - walk_from_car_min, 0)
            WHEN 'car_passenger_carpool' THEN
                {walk_rate_cp_sql} * ({carpool_walk_sql} + walk_from_car_min)
                + {standing_cp_sql} * {carpool_wait_sql}
                + {sitting_cp_sql} * parking_search_min
                + {sitting_cp_sql} * greatest(duration_min
                    - {carpool_walk_sql} - {carpool_wait_sql}
                    - parking_search_min - walk_from_car_min, 0)
            WHEN 'urban_pt' THEN
                {walk_rate_cp_sql} * (access_walk_ori_min + access_walk_des_min)
                + {standing_cp_sql} * wait_min + stairs_energy_cp_kj
                + ride_rate_kj_per_min * greatest(duration_min
                    - access_walk_ori_min - access_walk_des_min
                    - wait_min - stairs_time_min, 0)
            WHEN 'train' THEN
                {walk_rate_cp_sql} * (access_walk_ori_min + access_walk_des_min)
                + {standing_cp_sql} * wait_min + stairs_energy_cp_kj
                + ride_rate_kj_per_min * greatest(duration_min
                    - access_walk_ori_min - access_walk_des_min
                    - wait_min - stairs_time_min, 0)
            ELSE NULL
        END AS energy_cp_kj
    FROM pt_terminal
    """
    con.sql(sql)
