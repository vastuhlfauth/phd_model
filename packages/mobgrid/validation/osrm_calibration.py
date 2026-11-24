"""Bounded car calibration against OSRM log time ratios (section 8.1)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path

import duckdb
import numpy as np
import numpy.typing as npt
import pyarrow as pa
from numba import njit
from pydantic import BaseModel, ConfigDict, Field, model_validator

from mobgrid.graph.csr import CSRGraph
from mobgrid.graph.dijkstra import SearchWorkspace, search
from mobgrid.osm.config import load_network_config

FloatArray = npt.NDArray[np.float64]
CONTROL_NAMES = (
    "signal_s",
    "stop_s",
    "give_way_s",
    "mini_roundabout_s",
    "at_to_node_s",
    "crossing_s",
)


class RoadGroup(BaseModel):
    """Road classes sharing bounds for their individual speed factors."""

    model_config = ConfigDict(extra="forbid")
    highways: tuple[str, ...]
    bounds: tuple[float, float]


class CalibrationSettings(BaseModel):
    """Car fit bounds and numerical controls, in seconds where applicable."""

    model_config = ConfigDict(extra="forbid")
    network_config: Path
    seed: int = Field(ge=0)
    training_fraction: float = Field(gt=0, lt=1)
    uncertainty_fraction: float = Field(gt=0, le=1)
    max_iterations: int = Field(gt=0)
    tolerance: float = Field(gt=0, allow_inf_nan=False)
    max_backtracks: int = Field(gt=0)
    arc_time_tolerance_s: float = Field(gt=0, allow_inf_nan=False)
    road_groups: dict[str, RoadGroup]
    fixed_highways: tuple[str, ...]
    control_bounds_s: dict[str, tuple[float, float]]

    @model_validator(mode="after")
    def check_bounds(self) -> CalibrationSettings:
        if not self.road_groups or set(self.control_bounds_s) != set(CONTROL_NAMES):
            raise ValueError("car road groups and all control bounds are required")
        classes = list(self.fixed_highways)
        if not classes:
            raise ValueError("fixed road classes are required")
        for group in self.road_groups.values():
            if (
                not group.highways
                or not all(np.isfinite(group.bounds))
                or not 0 < group.bounds[0] < group.bounds[1]
            ):
                raise ValueError("invalid road factor bounds")
            classes.extend(group.highways)
        if len(set(classes)) != len(classes):
            raise ValueError("road classes must belong to exactly one group")
        for bounds in self.control_bounds_s.values():
            if not all(np.isfinite(bounds)) or not 0 <= bounds[0] < bounds[1]:
                raise ValueError("invalid control-delay bounds")
        return self


@dataclass(frozen=True)
class CalibrationFit:
    """Fitted parameters, uncertainty and provisional-value constraints."""

    values: FloatArray
    standard_errors: FloatArray
    correlations: FloatArray
    fixed: npt.NDArray[np.bool_]
    fixed_standard_errors: FloatArray


def factor_highways(settings: CalibrationSettings) -> tuple[str, ...]:
    """Return fitted highway classes in stable configuration order."""
    return tuple(
        highway for group in settings.road_groups.values() for highway in group.highways
    )


def arc_features(
    graph: CSRGraph,
    edges_path: Path,
    costs_path: Path,
    settings: CalibrationSettings,
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray, list[str]]:
    """Recover per-arc cruising seconds by class and directional control counts."""
    if graph.mode != "car" or not len(graph.indices):
        raise ValueError("calibration requires a nonempty car graph")
    network = load_network_config(settings.network_config).car_speed
    highway_names = factor_highways(settings)
    names = list(highway_names) + list(CONTROL_NAMES)
    factors = network.realism_factor_by_highway
    initial_factors = []
    lower = []
    upper = []
    for group in settings.road_groups.values():
        for highway in group.highways:
            initial_factors.append(factors.get(highway, factors["default"]))
            lower.append(group.bounds[0])
            upper.append(group.bounds[1])
    if any(
        factors.get(name, factors["default"]) != 1 for name in settings.fixed_highways
    ):
        raise ValueError("fixed road classes must have provisional factor 1")
    delays = np.asarray([getattr(network.delays, name) for name in CONTROL_NAMES])
    for name in CONTROL_NAMES:
        bounds = settings.control_bounds_s[name]
        lower.append(bounds[0])
        upper.append(bounds[1])
    initial = np.asarray([*initial_factors, *delays], dtype=float)
    lower_array, upper_array = np.asarray(lower), np.asarray(upper)
    if np.any(initial < lower_array) or np.any(initial > upper_array):
        raise ValueError("provisional car parameters are outside calibration bounds")
    if (
        len(graph.member_offsets) != len(graph.indices) + 1
        or graph.member_offsets[0] != 0
        or graph.member_offsets[-1] != len(graph.member_edge_rows)
        or np.any(np.diff(graph.member_offsets) <= 0)
    ):
        raise ValueError("car graph has invalid original-edge membership")
    with duckdb.connect() as connection:
        connection.register(
            "_car_members",
            pa.table(
                {
                    "position": np.arange(len(graph.member_edge_rows), dtype=np.int64),
                    "edge_row": graph.member_edge_rows,
                }
            ),
        )
        table = connection.execute(
            """
            WITH edges AS (
              SELECT *, row_number() OVER () - 1 AS edge_row FROM read_parquet(?)
            )
            SELECT e.mode, e.from_node_id, e.to_node_id, lower(e.highway) AS highway,
              c.car_time_s, coalesce(e.signal_count, 0) AS signals,
              coalesce(e.stop_count, 0) AS stops,
              coalesce(e.give_way_count, 0) AS give_ways,
              coalesce(e.mini_roundabout_count, 0) AS mini_roundabouts,
              CASE WHEN e.to_degree >= ? THEN 1 ELSE 0 END AS junctions,
              coalesce(e.crossing_count, 0) AS crossings
            FROM _car_members m LEFT JOIN edges e ON m.edge_row = e.edge_row
            LEFT JOIN read_parquet(?) c ON e.edge_key = c.edge_key
            ORDER BY m.position
            """,
            [str(edges_path), network.delays.degree_threshold, str(costs_path)],
        ).to_arrow_table()
    required = ("mode", "from_node_id", "to_node_id", "highway", "car_time_s")
    if table.num_rows != len(graph.member_edge_rows) or any(
        table.column(name).null_count for name in required
    ):
        raise ValueError("car graph member edges or costs are missing or duplicated")
    modes = np.asarray(table.column("mode").to_pylist())
    if np.any(modes != "car"):
        raise ValueError("car graph refers to non-car edges")
    starts = graph.member_offsets[:-1]
    source_nodes = np.repeat(graph.node_ids, np.diff(graph.indptr))
    from_ids = np.asarray(table.column("from_node_id").to_numpy())
    to_ids = np.asarray(table.column("to_node_id").to_numpy())
    if not np.array_equal(from_ids[starts], source_nodes) or not np.array_equal(
        to_ids[graph.member_offsets[1:] - 1], graph.node_ids[graph.indices]
    ):
        raise ValueError("car graph member endpoints disagree with edge table")
    continuation = np.ones(len(from_ids), dtype=bool)
    continuation[starts] = False
    if not np.array_equal(
        from_ids[1:][continuation[1:]], to_ids[:-1][continuation[1:]]
    ):
        raise ValueError("car graph member paths are not continuous")
    times = np.asarray(table.column("car_time_s").to_numpy(), dtype=np.float64)
    controls = np.column_stack(
        [
            table.column(name).to_numpy()
            for name in (
                "signals",
                "stops",
                "give_ways",
                "mini_roundabouts",
                "junctions",
                "crossings",
            )
        ]
    ).astype(float)
    if not np.isfinite(times).all() or np.any(times < 0) or np.any(controls < 0):
        raise ValueError("invalid original car times or control counts")
    cruising = times - controls @ delays
    if np.any(cruising < 0):
        raise ValueError(
            "car costs are inconsistent with configured provisional delays"
        )
    highways = np.asarray(table.column("highway").to_pylist())
    features = np.zeros((len(graph.indices), 1 + len(names)), dtype=np.float64)
    covered = np.zeros(len(times), dtype=bool)
    for index, highway in enumerate(highway_names):
        mask = highways == highway
        features[:, 1 + index] = np.add.reduceat(
            np.where(mask, cruising * initial_factors[index], 0), starts
        )
        covered |= mask
    fixed_mask = np.isin(highways, settings.fixed_highways)
    features[:, 0] = np.add.reduceat(np.where(fixed_mask, cruising, 0), starts)
    covered |= fixed_mask
    if not covered.all():
        raise ValueError(
            f"unconfigured car highway classes: {np.unique(highways[~covered])}"
        )
    features[:, 1 + len(highway_names) :] = np.add.reduceat(controls, starts, axis=0)
    if np.any(
        np.abs(
            adjusted_weights(features, initial, len(highway_names))
            - graph.weights["time_s"]
        )
        > settings.arc_time_tolerance_s
    ):
        raise ValueError("car graph times disagree with original edges and costs")
    return features, initial, lower_array, upper_array, names


def adjusted_weights(
    features: FloatArray, values: FloatArray, groups: int
) -> FloatArray:
    """Calculate arc or path seconds from cruise coefficients and control counts."""
    return (
        features[:, 0]
        + (features[:, 1 : 1 + groups] / values[:groups]).sum(axis=1)
        + features[:, 1 + groups :] @ values[groups:]
    )


@njit(cache=True)
def _trace(destination, origin, parent_nodes, parent_edges):
    path = np.empty(len(parent_nodes), dtype=np.int32)
    size = 0
    node = destination
    while node != origin:
        if node < 0 or parent_nodes[node] < 0 or size >= len(path):
            raise ValueError("invalid Dial predecessor chain")
        path[size] = parent_edges[node]
        size += 1
        node = parent_nodes[node]
    return path[:size][::-1].copy()


def trace_routes(
    graph: CSRGraph,
    features: FloatArray,
    pairs: list[dict],
    cutoff_s: float,
    resolution_s: float,
) -> list[dict]:
    """Trace Dial paths and aggregate arc features; times are seconds."""
    workspace = SearchWorkspace(
        graph, ("distance_m",), max_dial_ticks=int(np.ceil(cutoff_s / resolution_s))
    )
    rows = []
    for pair in pairs:
        ids = np.asarray([pair["origin_node_id"], pair["destination_node_id"]])
        indices = np.searchsorted(graph.node_ids, ids)
        if np.any(indices >= len(graph.node_ids)) or not np.array_equal(
            graph.node_ids[indices], ids
        ):
            raise ValueError("calibration pair node is absent from graph")
        origin, destination = indices
        result = search(
            graph,
            workspace,
            np.asarray([origin]),
            np.asarray([0.0]),
            cutoff_s,
            queue="dial",
            resolution_s=resolution_s,
        )
        if workspace.settled_stamps[destination] != result.generation:
            rows.append({"pair_id": pair["pair_id"], "path": None})
            continue
        path = _trace(
            destination, origin, workspace.predecessor_node, workspace.predecessor_edge
        )
        rows.append(
            {
                "pair_id": pair["pair_id"],
                "path": path,
                "features": features[path].sum(axis=0),
                "time_s": float(workspace.times[destination] * result.scale),
                "distance_m": float(workspace.secondary[destination, 0]),
            }
        )
    return rows


def _cached_paths(
    graph: CSRGraph,
    features: FloatArray,
    pairs: list[dict],
    cutoff_s: float,
    resolution_s: float,
    checkpoint: Path | None,
) -> list[dict]:
    if checkpoint is None:
        return trace_routes(graph, features, pairs, cutoff_s, resolution_s)
    if checkpoint.exists():
        rows = json.loads(checkpoint.read_text(encoding="utf-8"))
        if [row["pair_id"] for row in rows] != [pair["pair_id"] for pair in pairs]:
            raise ValueError(f"invalid calibration checkpoint: {checkpoint}")
        for row in rows:
            if row["path"] is not None:
                row["path"] = np.asarray(row["path"], dtype=np.int32)
                row["features"] = np.asarray(row["features"], dtype=np.float64)
                if (
                    row["features"].shape != (features.shape[1],)
                    or np.any(row["path"] < 0)
                    or np.any(row["path"] >= len(graph.indices))
                ):
                    raise ValueError(f"invalid calibration checkpoint: {checkpoint}")
        return rows
    rows = trace_routes(graph, features, pairs, cutoff_s, resolution_s)
    serializable = [
        {
            key: value.tolist() if isinstance(value, np.ndarray) else value
            for key, value in row.items()
        }
        for row in rows
    ]
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    temporary = checkpoint.with_suffix(".tmp")
    temporary.write_text(json.dumps(serializable), encoding="utf-8")
    temporary.replace(checkpoint)
    return rows


def calibrate_car(
    graph: CSRGraph,
    features: FloatArray,
    pairs: list[dict],
    observed: FloatArray,
    provisional: FloatArray,
    lower: FloatArray,
    upper: FloatArray,
    settings: CalibrationSettings,
    *,
    cutoff_s: float,
    resolution_s: float,
    checkpoint_directory: Path | None = None,
    checkpoint_key: str | None = None,
) -> dict:
    """Fit on provisional paths, reroute once, then refit those fixed paths."""
    observed = np.asarray(observed, dtype=np.float64)
    if len(pairs) != len(observed) or len(pairs) < 2:
        raise ValueError("car calibration needs matched training and holdout pairs")
    groups = len(factor_highways(settings))
    train_count = int(len(pairs) * settings.training_fraction)
    if train_count <= 0 or train_count >= len(pairs):
        raise ValueError("training split must leave both training and holdout pairs")
    permutation = np.random.default_rng(settings.seed).permutation(len(pairs))
    training = permutation[:train_count]
    holdout = permutation[train_count:]
    if (checkpoint_directory is None) != (checkpoint_key is None):
        raise ValueError(
            "calibration checkpoint directory and key must be supplied together"
        )
    initial_checkpoint = (
        checkpoint_directory / f"{checkpoint_key}_provisional.json"
        if checkpoint_directory is not None
        else None
    )
    first_paths = _cached_paths(
        graph, features, pairs, cutoff_s, resolution_s, initial_checkpoint
    )
    if any(row["path"] is None for row in first_paths):
        raise ValueError("car calibration pairs exceed the provisional Dial cutoff")

    def fit(
        paths: list[dict], previous: CalibrationFit | None = None
    ) -> CalibrationFit:
        design = np.stack([paths[index]["features"] for index in training])
        return fit_log_time_ratios(
            design[:, 1 : 1 + groups],
            design[:, 1 + groups :],
            design[:, 0],
            observed[training],
            lower,
            upper,
            provisional,
            uncertainty_fraction=settings.uncertainty_fraction,
            max_iterations=settings.max_iterations,
            tolerance=settings.tolerance,
            max_backtracks=settings.max_backtracks,
            fixed_at_provisional=previous.fixed if previous is not None else None,
            fixed_standard_errors=(
                previous.fixed_standard_errors if previous is not None else None
            ),
        )

    first_fit = fit(first_paths)
    first_weights = adjusted_weights(features, first_fit.values, groups).astype(
        np.float32
    )
    if np.any(~np.isfinite(first_weights)) or np.any(first_weights < 0):
        raise ValueError("first fit produced invalid car arc times")
    rerouted_graph = replace(graph, weights={**graph.weights, "time_s": first_weights})
    factor_key = hashlib.sha256(
        str(checkpoint_key).encode() + first_weights.tobytes()
    ).hexdigest()
    rerouted_checkpoint = (
        checkpoint_directory / f"{factor_key}.json"
        if checkpoint_directory is not None
        else None
    )
    rerouted_paths = _cached_paths(
        rerouted_graph, features, pairs, cutoff_s, resolution_s, rerouted_checkpoint
    )
    if any(row["path"] is None for row in rerouted_paths):
        raise ValueError("car calibration pairs exceed the fitted Dial cutoff")
    refit = fit(rerouted_paths, first_fit)
    refit_weights = adjusted_weights(features, refit.values, groups).astype(np.float32)
    if np.any(~np.isfinite(refit_weights)) or np.any(refit_weights < 0):
        raise ValueError("refit produced invalid car arc times")
    ticks = np.rint(refit_weights.astype(np.float64) / resolution_s)
    changed = [
        not np.array_equal(before["path"], after["path"])
        for before, after in zip(first_paths, rerouted_paths, strict=True)
    ]
    holdout_rows = []
    for index in holdout:
        before, after = first_paths[index], rerouted_paths[index]
        holdout_rows.append(
            {
                "pair_id": pairs[index]["pair_id"],
                "provisional_time_s": before["time_s"],
                "provisional_distance_m": before["distance_m"],
                "first_time_s": after["time_s"],
                "first_distance_m": after["distance_m"],
                "refit_time_s": float(ticks[after["path"]].sum() * resolution_s),
                "refit_distance_m": after["distance_m"],
                "path_changed": changed[index],
            }
        )
    return {
        "first_fit": first_fit,
        "refit": refit,
        "training_count": len(training),
        "holdout": holdout_rows,
        "changed_share": float(np.mean(changed)),
    }


def _residual_jacobian(
    cruise: FloatArray,
    controls: FloatArray,
    fixed_time: FloatArray,
    observed: FloatArray,
    values: FloatArray,
) -> tuple[FloatArray, FloatArray]:
    factors = values[: cruise.shape[1]]
    predicted = fixed_time + (cruise / factors).sum(axis=1)
    predicted += controls @ values[cruise.shape[1] :]
    if np.any(predicted <= 0) or not np.isfinite(predicted).all():
        raise ValueError("calibration predicted non-positive or non-finite times")
    residual = np.log(predicted / observed)
    jacobian = np.column_stack((-cruise / factors**2, controls)) / predicted[:, None]
    return residual, jacobian


def _optimise(
    cruise: FloatArray,
    controls: FloatArray,
    fixed_time: FloatArray,
    observed: FloatArray,
    lower: FloatArray,
    upper: FloatArray,
    values: FloatArray,
    fixed: npt.NDArray[np.bool_],
    max_iterations: int,
    tolerance: float,
    max_backtracks: int,
) -> FloatArray:
    scale = upper - lower
    x = (values - lower) / scale
    active = ~fixed
    if not active.any():
        return values
    for _ in range(max_iterations):
        values = lower + x * scale
        residual, jacobian = _residual_jacobian(
            cruise, controls, fixed_time, observed, values
        )
        jacobian = jacobian[:, active] * scale[active]
        gradient = jacobian.T @ residual
        xa = x[active]
        projected = xa - np.clip(xa - gradient, 0, 1)
        if np.max(np.abs(projected)) <= tolerance:
            return values
        step = np.zeros(len(xa))
        free = np.ones(len(xa), dtype=bool)
        for _ in range(len(xa)):
            adjusted = -residual - jacobian[:, ~free] @ step[~free]
            step[free] = np.linalg.lstsq(jacobian[:, free], adjusted, rcond=None)[0]
            proposed = xa + step
            violation = np.maximum(-proposed, proposed - 1)
            violation[~free] = -np.inf
            worst = int(np.argmax(violation))
            if violation[worst] <= 0:
                break
            step[worst] = np.clip(proposed[worst], 0, 1) - xa[worst]
            free[worst] = False
            if not free.any():
                break
        direction = step
        if gradient @ direction >= 0:
            direction = -projected
        objective = float(residual @ residual)
        accepted = False
        for iteration in range(max_backtracks):
            trial = x.copy()
            trial[active] = np.clip(xa + direction * (0.5**iteration), 0, 1)
            trial_residual, _ = _residual_jacobian(
                cruise, controls, fixed_time, observed, lower + trial * scale
            )
            if float(trial_residual @ trial_residual) < objective:
                x = trial
                accepted = True
                break
        if not accepted:
            raise RuntimeError("bounded calibration stalled before convergence")
    raise RuntimeError("bounded calibration exceeded its iteration limit")


def _uncertainty(
    residual: FloatArray,
    jacobian: FloatArray,
    fixed: npt.NDArray[np.bool_],
) -> tuple[FloatArray, FloatArray]:
    count = len(fixed)
    errors = np.full(count, np.nan)
    correlations = np.full((count, count), np.nan)
    active = np.flatnonzero(~fixed)
    if not len(active):
        return errors, correlations
    j = jacobian[:, active]
    _, singular, vt = np.linalg.svd(j, full_matrices=j.shape[0] < j.shape[1])
    threshold = singular[0] * max(j.shape) * np.finfo(float).eps if len(singular) else 0
    rank = int(np.sum(singular > threshold))
    variance = (
        float(residual @ residual / (len(residual) - rank))
        if len(residual) > rank
        else np.inf
    )
    if rank:
        directions = vt[:rank].T
        covariance = (directions / singular[:rank] ** 2) @ directions.T
        diagonal = np.diag(covariance)
        with np.errstate(divide="ignore", invalid="ignore"):
            correlation = covariance / np.sqrt(np.outer(diagonal, diagonal))
        correlations[np.ix_(active, active)] = correlation
        errors[active] = np.sqrt(diagonal * variance)
    else:
        errors[active] = np.inf
    if rank < len(active):
        null_directions = vt[rank:]
        unidentified = np.any(
            np.abs(null_directions) > np.sqrt(np.finfo(float).eps), axis=0
        )
        errors[active[unidentified]] = np.inf
        correlations[active[unidentified], :] = np.nan
        correlations[:, active[unidentified]] = np.nan
    return errors, correlations


def fit_log_time_ratios(
    cruise: FloatArray,
    controls: FloatArray,
    fixed_time: FloatArray,
    observed: FloatArray,
    lower: FloatArray,
    upper: FloatArray,
    provisional: FloatArray,
    *,
    uncertainty_fraction: float,
    max_iterations: int,
    tolerance: float,
    max_backtracks: int,
    fixed_at_provisional: npt.NDArray[np.bool_] | None = None,
    fixed_standard_errors: FloatArray | None = None,
) -> CalibrationFit:
    """Fit class speed factors and control seconds with uncertainty-based fixing."""
    cruise, controls, fixed_time, observed, lower, upper, provisional = (
        np.asarray(value, dtype=np.float64)
        for value in (cruise, controls, fixed_time, observed, lower, upper, provisional)
    )
    if (
        cruise.ndim != 2
        or controls.ndim != 2
        or fixed_time.ndim != 1
        or observed.shape != fixed_time.shape
        or cruise.shape[0] != len(observed)
        or controls.shape[0] != len(observed)
        or not len(observed)
        or lower.shape != (cruise.shape[1] + controls.shape[1],)
        or upper.shape != lower.shape
        or provisional.shape != lower.shape
        or any(
            not np.isfinite(a).all()
            for a in (cruise, controls, fixed_time, observed, lower, upper, provisional)
        )
        or np.any(cruise < 0)
        or np.any(controls < 0)
        or np.any(fixed_time < 0)
        or np.any(observed <= 0)
        or np.any(lower[: cruise.shape[1]] <= 0)
        or np.any(lower >= upper)
        or np.any(provisional < lower)
        or np.any(provisional > upper)
        or not 0 < uncertainty_fraction <= 1
        or max_iterations <= 0
        or tolerance <= 0
        or max_backtracks <= 0
    ):
        raise ValueError("invalid bounded calibration inputs")
    if (fixed_at_provisional is None) != (fixed_standard_errors is None):
        raise ValueError(
            "fixed parameters and their original errors must be supplied together"
        )
    values = provisional.copy()
    if fixed_at_provisional is None:
        fixed = np.zeros(len(values), dtype=bool)
        fixed_errors = np.full(len(values), np.nan)
    else:
        fixed = np.asarray(fixed_at_provisional)
        fixed_errors = np.asarray(fixed_standard_errors, dtype=np.float64)
        if (
            fixed.dtype != np.bool_
            or fixed.shape != values.shape
            or fixed_errors.shape != values.shape
            or np.any(np.isnan(fixed_errors[fixed]))
            or np.any(fixed_errors[fixed] < 0)
        ):
            raise ValueError("invalid previously fixed parameters or errors")
        fixed = fixed.copy()
        fixed_errors = fixed_errors.copy()
    while True:
        values = _optimise(
            cruise,
            controls,
            fixed_time,
            observed,
            lower,
            upper,
            values,
            fixed,
            max_iterations,
            tolerance,
            max_backtracks,
        )
        residual, jacobian = _residual_jacobian(
            cruise, controls, fixed_time, observed, values
        )
        errors, correlations = _uncertainty(residual, jacobian, fixed)
        ratio = errors / (upper - lower)
        ratio[fixed] = -np.inf
        index = int(np.argmax(ratio))
        if ratio[index] <= uncertainty_fraction:
            return CalibrationFit(values, errors, correlations, fixed, fixed_errors)
        fixed[index] = True
        fixed_errors[index] = errors[index]
        values[index] = provisional[index]
