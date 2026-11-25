"""Preallocated destination products for bounded searches (section 10.2)."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
from numba import njit


class SearchProducts:
    """Reusable outputs indexed by node, counted type, nearest type and bin.

    Costs are seconds, metres and kJ. O-D and nearest arrays are valid only up
    to their counts; curves contain non-cumulative opportunity counts.
    """

    def __init__(
        self,
        od_flags: npt.NDArray[np.bool_],
        counts: np.ndarray,
        nearest_flags: npt.NDArray[np.bool_],
        required: np.ndarray,
        *,
        nearest_extra: int,
        bin_widths: tuple[float, float, float],
        bin_counts: tuple[int, int, int],
    ) -> None:
        od_flags = np.asarray(od_flags)
        counts = np.asarray(counts)
        nearest_flags = np.asarray(nearest_flags)
        required = np.asarray(required)
        if (
            od_flags.ndim != 1
            or od_flags.dtype != np.bool_
            or counts.ndim != 2
            or counts.shape[0] != len(od_flags)
            or not np.issubdtype(counts.dtype, np.number)
            or not np.isfinite(counts).all()
            or np.any(counts < 0)
            or nearest_flags.ndim != 2
            or nearest_flags.shape[0] != len(od_flags)
            or nearest_flags.dtype != np.bool_
            or required.shape != (nearest_flags.shape[1],)
            or not np.issubdtype(required.dtype, np.integer)
            or np.any(required < 0)
            or not isinstance(nearest_extra, int)
            or nearest_extra < 0
            or len(bin_widths) != 3
            or any(not np.isfinite(value) or value <= 0 for value in bin_widths)
            or len(bin_counts) != 3
            or any(not isinstance(value, int) or value <= 0 for value in bin_counts)
        ):
            raise ValueError("invalid destination flags, counts, limits or bins")
        n = len(od_flags)
        self.od_flags = od_flags
        self.counts = counts.astype(np.float64, copy=False)
        self.nearest_flags = nearest_flags
        self.nearest_limits = required.astype(np.int64) + nearest_extra
        self.bin_widths = np.asarray(bin_widths, dtype=np.float64)
        self.od_nodes = np.empty(n, dtype=np.int32)
        self.od_costs = np.empty((n, 3), dtype=np.float64)
        self._od_count = np.zeros(1, dtype=np.int64)
        self.curves = tuple(
            np.zeros((counts.shape[1], bins), dtype=np.float64) for bins in bin_counts
        )
        maximum = int(self.nearest_limits.max(initial=0))
        self.nearest_nodes = np.empty((len(required), maximum), dtype=np.int32)
        self.nearest_costs = np.empty((len(required), maximum, 3), dtype=np.float64)
        self.nearest_counts = np.zeros(len(required), dtype=np.int64)
        self._overflow = np.zeros(1, dtype=np.int8)
        self.arrays = (
            self.od_flags,
            self.counts,
            self.nearest_flags,
            self.nearest_limits,
            self.bin_widths,
            self.od_nodes,
            self.od_costs,
            self._od_count,
            self.curves[0],
            self.curves[1],
            self.curves[2],
            self.nearest_nodes,
            self.nearest_costs,
            self.nearest_counts,
            self._overflow,
        )

    @property
    def od_count(self) -> int:
        return int(self._od_count[0])

    def reset(self) -> None:
        """Clear product counts and bins before a search."""
        self._od_count.fill(0)
        self.nearest_counts.fill(0)
        self._overflow.fill(0)
        for curve in self.curves:
            curve.fill(0)


@njit(cache=True)
def record_settled(node, time_s, distance_m, energy_kj, arrays):
    """Update all flagged products when a destination settles."""
    (
        od_flags,
        counts,
        nearest_flags,
        limits,
        widths,
        od_nodes,
        od_costs,
        od_count,
        time_curve,
        distance_curve,
        energy_curve,
        nearest_nodes,
        nearest_costs,
        nearest_counts,
        overflow,
    ) = arrays
    if od_flags[node]:
        position = od_count[0]
        od_nodes[position] = node
        od_costs[position, 0] = time_s
        od_costs[position, 1] = distance_m
        od_costs[position, 2] = energy_kj
        od_count[0] += 1
    for kind in range(counts.shape[1]):
        value = counts[node, kind]
        if value == 0:
            continue
        time_bin = int(np.floor(time_s / widths[0]))
        distance_bin = int(np.floor(distance_m / widths[1]))
        energy_bin = int(np.floor(energy_kj / widths[2]))
        if (
            time_bin < 0
            or time_bin >= time_curve.shape[1]
            or distance_bin < 0
            or distance_bin >= distance_curve.shape[1]
            or energy_bin < 0
            or energy_bin >= energy_curve.shape[1]
        ):
            overflow[0] = 1
        else:
            time_curve[kind, time_bin] += value
            distance_curve[kind, distance_bin] += value
            energy_curve[kind, energy_bin] += value
    for kind in range(nearest_flags.shape[1]):
        position = nearest_counts[kind]
        if nearest_flags[node, kind] and position < limits[kind]:
            nearest_nodes[kind, position] = node
            nearest_costs[kind, position, 0] = time_s
            nearest_costs[kind, position, 1] = distance_m
            nearest_costs[kind, position, 2] = energy_kj
            nearest_counts[kind] += 1
