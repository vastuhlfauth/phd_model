import numpy as np
import pytest
from mobgrid.energy.bike import (
    bike_ride_energy_kj,
    climbing_work_j_per_kg,
    drag_work_j,
    ride_speed_and_power,
    rolling_work_j_per_kg,
)
from mobgrid.energy.rates import load_energy_config
from mobgrid.osm.bike_speed_table import BikeSpeedTable
from mobgrid.osm.config import load_network_config


@pytest.mark.parametrize("surface", [
    "asphalt_concrete_paved_default",
    "concrete_plates_lanes",
    "paving_stones",
    "compacted",
    "fine_gravel",
    "sett_cobblestone",
    "gravel_unpaved_ground_dirt_earth",
    "grass_sand",
])
@pytest.mark.parametrize("cap_kmh", [10.0, 20.0, 25.0, 30.0])
def test_table_matches_scalar_solver_across_grade_transitions(surface, cap_kmh):
    energy = load_energy_config("config/energy.yaml")
    network = load_network_config("config/network.yaml")
    grid = network.bike_speed_table
    crr = energy.bike.surface_crr[surface]
    table = BikeSpeedTable(energy, grid, crr, cap_kmh)
    grades = np.linspace(grid.grade_min, grid.grade_max, 1601)
    speeds, powers = table.lookup(grades)
    bike = energy.bike
    power = bike.power
    expected = np.array([
        ride_speed_and_power(
            float(grade), power.p0_w, power.k, power.p_max_w,
            energy.reference_mass_kg + bike.bike_mass_kg, crr,
            bike.cda_m2, bike.rho_air_kg_per_m3, bike.drivetrain_efficiency,
            power.v_max_descent_kmh / 3.6, cap_kmh / 3.6,
        )
        for grade in grades
    ])
    assert np.max(np.abs(speeds - expected[:, 0]) * 3.6) <= grid.speed_tolerance_kmh
    positive = (expected[:, 0] > 0) & (expected[:, 1] > 0)
    def ride_energy(grade, speed):
        return bike_ride_energy_kj(
            rolling_work_j_per_kg(1000, grade, crr),
            climbing_work_j_per_kg(1000, grade), 0,
            drag_work_j(1000, speed, bike.rho_air_kg_per_m3, bike.cda_m2),
            energy.reference_mass_kg + bike.bike_mass_kg,
            bike.gross_muscular_efficiency,
            rider_mass_kg=energy.reference_mass_kg,
            pedalled_time_s=1000 / speed,
            unloaded_net_met_per_min=bike.pedalling_unloaded_net_met,
        )

    energy_per_km = [
        ride_energy(float(grade), float(speed))
        for grade, speed in zip(grades[positive], speeds[positive], strict=True)
    ]
    scalar_energy_per_km = [
        ride_energy(float(grade), float(speed))
        for grade, speed in zip(
            grades[positive], expected[positive, 0], strict=True
        )
    ]
    assert np.all(powers[positive] > 0)
    assert energy_per_km == pytest.approx(
        scalar_energy_per_km, rel=grid.energy_relative_tolerance
    )


def test_lookup_handles_grades_outside_the_grid_and_rejects_nonfinite_values():
    energy = load_energy_config("config/energy.yaml")
    grid = load_network_config("config/network.yaml").bike_speed_table
    table = BikeSpeedTable(energy, grid, 0.006, 30.0)
    grades = np.array([-0.3, 0.3])
    speeds, _ = table.lookup(grades)
    bike = energy.bike
    power = bike.power
    expected = [
        ride_speed_and_power(
            float(grade), power.p0_w, power.k, power.p_max_w,
            energy.reference_mass_kg + bike.bike_mass_kg, 0.006,
            bike.cda_m2, bike.rho_air_kg_per_m3, bike.drivetrain_efficiency,
            power.v_max_descent_kmh / 3.6, 30 / 3.6,
        )[0]
        for grade in grades
    ]
    assert speeds == pytest.approx(expected)
    with pytest.raises(ValueError, match="grade"):
        table.lookup(np.array([np.nan]))
