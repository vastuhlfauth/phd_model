"""Interpolated bike speeds for directional edge segments (section 9.7)."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from mobgrid.energy.bike import ride_speed_and_power
from mobgrid.energy.rates import GRAVITY_M_S2, EnergyConfig
from mobgrid.osm.config import BikeSpeedTableConfig

FloatArray = npt.NDArray[np.float64]


class BikeSpeedTable:
    """Speed table for one rolling resistance and class cap (section 9.7)."""

    def __init__(
        self,
        energy: EnergyConfig,
        grid: BikeSpeedTableConfig,
        rolling_resistance: float,
        cap_kmh: float,
    ) -> None:
        power = energy.bike.power
        if any(value is None for value in (
            power.p0_w, power.k, power.p_max_w, power.v_max_descent_kmh
        )):
            raise ValueError("bike power parameters must be configured")
        if grid.grade_min >= grid.grade_max or rolling_resistance <= 0 or cap_kmh <= 0:
            raise ValueError("invalid speed table bounds, surface or cap")
        self.energy = energy
        self.grid = grid
        self.rolling_resistance = rolling_resistance
        self.paved_rolling_resistance = energy.bike.surface_crr[
            "asphalt_concrete_paved_default"
        ]
        self.cap_kmh = cap_kmh
        self.p0 = float(power.p0_w)
        self.k = float(power.k)
        self.p_max = float(power.p_max_w)
        self.descent_cap = float(power.v_max_descent_kmh) / 3.6
        count = round((grid.grade_max - grid.grade_min) / grid.grade_step)
        if count < 1 or not np.isclose(
            count * grid.grade_step, grid.grade_max - grid.grade_min
        ):
            raise ValueError("bike grade grid bounds must align with its step")
        self.grades = np.linspace(grid.grade_min, grid.grade_max, count + 1)
        bike = energy.bike
        self.speeds = np.array([
            ride_speed_and_power(
                float(grade), self.p0, self.k, self.p_max,
                energy.reference_mass_kg + bike.bike_mass_kg,
                rolling_resistance, bike.cda_m2, bike.rho_air_kg_per_m3,
                bike.drivetrain_efficiency, self.descent_cap, cap_kmh / 3.6,
                paved_rolling_resistance=self.paved_rolling_resistance,
            )[0]
            for grade in self.grades
        ])

    def lookup(self, grades: FloatArray) -> tuple[FloatArray, FloatArray]:
        """Return speed (m/s) and rider power (W) for signed grades (9.7)."""
        grades = np.asarray(grades, dtype=np.float64)
        if not np.isfinite(grades).all():
            raise ValueError("bike grade must be finite")
        bike = self.energy.bike
        weight = (
            (self.energy.reference_mass_kg + bike.bike_mass_kg) * GRAVITY_M_S2
            * (self.rolling_resistance + grades) / np.sqrt(1 + grades**2)
        )
        drag = 0.5 * bike.rho_air_kg_per_m3 * bike.cda_m2
        felt_grades = grades + (
            self.rolling_resistance - self.paved_rolling_resistance
        )
        selected_power = np.clip(self.p0 * (1 + self.k * felt_grades), 0, self.p_max)
        target = selected_power * bike.drivetrain_efficiency
        # A fixed coarse grid straddles cap/coasting kinks. Refine its
        # interpolated estimate with vectorised, bracketed force balance.
        estimate = np.interp(grades, self.grades, self.speeds)
        low = np.sqrt(np.maximum(-weight / (3 * drag), 0))
        high = np.cbrt(target / drag) + np.sqrt(np.maximum(-weight / drag, 0))
        value = np.clip(estimate, low, high)
        for _ in range(np.finfo(np.float64).nmant):
            residual = value * (weight + drag * value**2) - target
            low = np.where(residual < 0, value, low)
            high = np.where(residual >= 0, value, high)
            value = (low + high) / 2
        coast = np.sqrt(np.maximum(-weight / drag, 0))
        speed = np.where(selected_power > 0, value, coast)
        cap = np.where(
            grades < 0, min(self.descent_cap, self.cap_kmh / 3.6),
            self.cap_kmh / 3.6,
        )
        capped = speed > cap
        speed = np.minimum(speed, cap)
        capped_power = np.maximum(
            speed * (weight + drag * speed**2) / bike.drivetrain_efficiency, 0
        )
        return speed, np.where(capped, capped_power, selected_power)
