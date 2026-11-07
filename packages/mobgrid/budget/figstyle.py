"""Shared styles and data export for the step 11/12 budget figures."""

from __future__ import annotations

import csv
import re
import warnings
from pathlib import Path
from typing import Any

import numpy as np
from matplotlib.colors import to_hex

SURVEY_COLOURS = {"ENTD 2008": "#2a78d6", "EMP 2019": "#eb6834"}
HISTORICAL_COLOUR = "#52514e"
TEXT_COLOUR = "#0b0b0b"
SECONDARY_TEXT_COLOUR = "#52514e"
GRID_COLOUR = "#e4e3de"
BACKGROUND_COLOUR = "#ffffff"

POPULATION_ORDER = (
    "Children 6–17",
    "Employed",
    "Unemployed",
    "Retired",
    "Other inactive",
    "All",
)
DENSITY_ORDER = ("Dense", "Intermediate", "Sparse", "Very sparse")
INCOME_ORDER = ("Q1", "Q2", "Q3", "Q4", "Q5", "Unknown")
MODE_ORDER = (
    "Walking only",
    "Cycle",
    "Car driver",
    "Car passenger (household)",
    "Car passenger (carpool)",
    "Urban PT",
    "Train",
    "Multimodal",
    "Other",
)
DISTANCE_ORDER = (
    "0-1 km",
    "1-2 km",
    "2-5 km",
    "5-10 km",
    "10-20 km",
    "20-40 km",
    "40-80 km",
    ">=80 km",
    "Unknown distance",
)
SCOPE_ORDER = ("Reference", "One switch", "Two switches", "Three switches")
_PLAIN_LABELS = {
    "children_6_17": "Children 6–17",
    "employed": "Employed",
    "unemployed": "Unemployed",
    "retired": "Retired",
    "other_inactive": "Other inactive",
    "dense": "Dense",
    "intermediate": "Intermediate",
    "sparse": "Sparse",
    "very_sparse": "Very sparse",
    "q1": "Q1",
    "q2": "Q2",
    "q3": "Q3",
    "q4": "Q4",
    "q5": "Q5",
    "walking_only": "Walking only",
    "cycle": "Cycle",
    "car_driver": "Car driver",
    "car_passenger_household": "Car passenger (household)",
    "car_passenger_carpool": "Car passenger (carpool)",
    "urban_pt": "Urban PT",
    "train": "Train",
    "multimodal": "Multimodal",
    "other": "Other",
    "unknown distance": "Unknown distance",
}

# A given quantity always uses the same range, even when it appears in a
# different report or panel. Ranges are deliberately broad enough for the
# full survey samples; outliers are warned about before the axis is clipped.
QUANTITY_RANGES = {
    "time": (0.0, 180.0),
    "trips": (0.0, 20.0),
    "energy": (0.0, 1500.0),
    "minutes per trip": (0.0, 180.0),
    "speed": (0.0, 120.0),
    "share": (0.0, 100.0),
}

CSV_COLUMNS = (
    "figure",
    "panel",
    "scope",
    "survey",
    "group",
    "subgroup",
    "quantity",
    "unit",
    "days",
    "basis",
    "n",
    "mean",
    "ci_low",
    "ci_high",
    "median",
    "p25",
    "p75",
    "ratio",
    "ratio_ci_low",
    "ratio_ci_high",
)

_CONTEXT: dict[str, str] = {
    "scope": "Reference",
    "survey": "",
    "days": "7-day",
    "basis": "per day with trips",
    "section": "section 9.9",
    "replicates": "200",
}


def set_context(
    *,
    scope: str,
    survey: str,
    days: str,
    basis: str = "per day with trips",
    section: str = "section 9.9",
    replicates: int = 200,
) -> None:
    """Set report metadata used in every subsequent figure sidecar."""
    _CONTEXT.update(
        scope=scope,
        survey=survey,
        days=days,
        basis=basis,
        section=section,
        replicates=str(replicates),
    )


def annotate_ratio(
    ax: Any, x: float, y: float, ratio: tuple[float, float, float]
) -> None:
    """Annotate a survey ratio while retaining full precision for its CSV."""
    point, low, high = ratio
    text = ax.text(
        x,
        y,
        f"×{point:.3f} [{low:.3f}, {high:.3f}]",
        ha="center",
        va="bottom",
        fontsize=8,
    )
    setattr(text, "_figure_ratio_values", ratio)


def plot_quartiles(
    ax: Any,
    x: Any,
    p25: Any,
    median: Any,
    p75: Any,
    *,
    color: Any,
    label: str | None = None,
    marker: str = "D",
    size: float = 18,
    zorder: int = 3,
) -> Any:
    """Draw a weighted interquartile bar and median marker, retaining values
    for the figure CSV."""
    x_values = np.asarray(x, dtype=float)
    quantiles = np.column_stack(
        [np.asarray(values, dtype=float) for values in (p25, median, p75)]
    )
    valid = np.isfinite(quantiles).all(axis=1)
    ax.vlines(
        x_values[valid],
        quantiles[valid, 0],
        quantiles[valid, 2],
        color=color,
        linewidth=1.2,
        zorder=zorder - 1,
    )
    points = ax.scatter(
        x_values,
        quantiles[:, 1],
        marker=marker,
        color=color,
        s=size,
        zorder=zorder,
        label=label,
    )
    setattr(points, "_figure_quantile_values", quantiles)
    return points


def _quantity_range(label: str) -> tuple[float, float] | None:
    text = label.casefold()
    if "%" in text or "share" in text:
        return QUANTITY_RANGES["share"]
    for quantity, limits in QUANTITY_RANGES.items():
        if quantity in text or (
            quantity == "energy" and ("kj" in text or "energy" in text)
        ):
            return limits
    return None


def _axis_values(ax: Any) -> list[float]:
    values: list[float] = []
    for patch in ax.patches:
        if patch.get_visible():
            bottom = float(patch.get_y())
            values.extend((bottom, bottom + float(patch.get_height())))
    for line in ax.lines:
        if line.get_visible():
            values.extend(
                float(value) for value in line.get_ydata() if np.isfinite(value)
            )
    for collection in ax.collections:
        get_offsets = getattr(collection, "get_offsets", None)
        if get_offsets is not None:
            offsets = np.asarray(get_offsets())
            if offsets.size:
                values.extend(
                    float(value) for value in offsets[:, 1] if np.isfinite(value)
                )
    return values


def _apply_style(fig: Any, *, survey: str | None) -> None:
    fig.set_facecolor(BACKGROUND_COLOUR)
    width, height = fig.get_size_inches()
    if width != 7.0:
        fig.set_size_inches(7.0, height * 7.0 / width, forward=True)

    survey_colour = SURVEY_COLOURS.get(survey or "")
    for ax in fig.axes:
        ax.set_facecolor(BACKGROUND_COLOUR)
        x_labels = [
            _PLAIN_LABELS.get(label.get_text(), label.get_text())
            for label in ax.get_xticklabels()
        ]
        y_labels = [
            _PLAIN_LABELS.get(label.get_text(), label.get_text())
            for label in ax.get_yticklabels()
        ]
        if x_labels:
            ax.set_xticks(ax.get_xticks(), labels=x_labels)
        if y_labels:
            ax.set_yticks(ax.get_yticks(), labels=y_labels)
        ax.tick_params(colors=TEXT_COLOUR, labelsize=8)
        ax.xaxis.label.set_color(TEXT_COLOUR)
        ax.yaxis.label.set_color(TEXT_COLOUR)
        ax.title.set_color(TEXT_COLOUR)
        ax.grid(True, color=GRID_COLOUR, linewidth=0.6, alpha=0.8)
        ax.set_axisbelow(True)
        for text in [*ax.texts, *ax.get_xticklabels(), *ax.get_yticklabels()]:
            text.set_color(TEXT_COLOUR)
            text.set_fontsize(max(8.0, text.get_fontsize()))
        legend = ax.get_legend()
        if legend is not None:
            for text in legend.get_texts():
                text.set_fontsize(max(8.0, text.get_fontsize()))
                text.set_color(TEXT_COLOUR)

        limits = _quantity_range(ax.get_ylabel())
        if limits is not None:
            values = _axis_values(ax)
            if values and (min(values) < limits[0] or max(values) > limits[1]):
                warnings.warn(
                    f"Figure value outside configured {ax.get_ylabel()!r} "
                    f"range {limits}: [{min(values)}, {max(values)}]",
                    RuntimeWarning,
                    stacklevel=2,
                )
            ax.set_ylim(*limits)

        bars = [
            patch
            for patch in ax.patches
            if patch.get_visible() and np.isfinite(patch.get_height())
        ]
        small_n_texts = []
        for text in ax.texts:
            match = re.search(r"\bn\s*=\s*(\d+)\b", text.get_text())
            if match and int(match.group(1)) < 50:
                small_n_texts.append((text, int(match.group(1))))
        for patch in bars:
            center = float(patch.get_x() + patch.get_width() / 2)
            for text, n in small_n_texts:
                if abs(float(text.get_position()[0]) - center) <= 0.35:
                    patch.set_visible(False)
                    setattr(text, "_figure_n_value", n)
                    text.set_text("n < 50")
                    text.set_color(SECONDARY_TEXT_COLOUR)
                    break
        visible_bars = [patch for patch in bars if patch.get_visible()]
        labeled_indexes = set(range(len(visible_bars)))
        if len(visible_bars) > 24:
            heights = [
                float(patch.get_y() + patch.get_height()) for patch in visible_bars
            ]
            labeled_indexes = {int(np.argmin(heights)), int(np.argmax(heights))}
            labeled_indexes.update(
                i
                for i, patch in enumerate(visible_bars)
                if _nearest_group(ax, float(patch.get_x() + patch.get_width() / 2))
                == "All"
            )
        existing_text_positions = [
            (float(text.get_position()[0]), float(text.get_position()[1]))
            for text in ax.texts
        ]
        for index, patch in enumerate(visible_bars):
            if index not in labeled_indexes:
                continue
            x = float(patch.get_x() + patch.get_width() / 2)
            y = float(patch.get_y() + patch.get_height())
            if any(
                np.isclose(x, text_x, atol=0.04) and np.isclose(y, text_y, atol=0.5)
                for text_x, text_y in existing_text_positions
            ):
                continue
            ax.annotate(
                f"{y:.1f}",
                (x, y),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                color=TEXT_COLOUR,
            )
            existing_text_positions.append((x, y))

        for line in ax.lines:
            if line.get_marker() in ("None", "", None):
                continue
            x_values = np.asarray(line.get_xdata(), dtype=float)
            y_values = np.asarray(line.get_ydata(), dtype=float)
            if len(x_values) != len(y_values) or len(x_values) < 2:
                continue
            valid = np.isfinite(x_values) & np.isfinite(y_values)
            indexes = np.flatnonzero(valid)
            if len(indexes) > 24:
                visible_values = y_values[indexes]
                selected = {
                    indexes[int(np.argmin(visible_values))],
                    indexes[int(np.argmax(visible_values))],
                }
                selected.update(
                    index
                    for index in indexes
                    if _nearest_group(ax, float(x_values[index])) == "All"
                )
            else:
                selected = set(indexes)
            for index in selected:
                x, y = float(x_values[index]), float(y_values[index])
                if any(
                    np.isclose(x, text_x, atol=0.04) and np.isclose(y, text_y, atol=0.5)
                    for text_x, text_y in existing_text_positions
                ):
                    continue
                ax.annotate(
                    f"{y:.1f}",
                    (x, y),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    color=TEXT_COLOUR,
                )
                existing_text_positions.append((x, y))

        for collection in ax.collections:
            paths = getattr(collection, "get_paths", lambda: [])()
            if paths and any(len(path.vertices) == 5 for path in paths):
                edge_colours = collection.get_edgecolors()
                if not len(edge_colours):
                    edge_colours = collection.get_facecolors()
                collection.set_facecolor(BACKGROUND_COLOUR)
                edge_colour = (
                    survey_colour
                    if survey_colour is not None
                    else edge_colours
                    if len(edge_colours)
                    else SECONDARY_TEXT_COLOUR
                )
                collection.set_edgecolor(edge_colour)
                offsets = np.asarray(collection.get_offsets())
                if offsets.ndim == 2 and offsets.shape[1] == 2:
                    for x, y in offsets:
                        if np.isfinite(x) and np.isfinite(y):
                            ax.annotate(
                                f"{y:.1f}",
                                (float(x), float(y)),
                                xytext=(0, -9),
                                textcoords="offset points",
                                ha="center",
                                va="top",
                                fontsize=8,
                                color=SECONDARY_TEXT_COLOUR,
                            )

        if survey_colour is not None:
            for patch in ax.patches:
                patch.set_facecolor(survey_colour)
            for line in ax.lines:
                line.set_color(survey_colour)

    for text in fig.texts:
        text.set_color(TEXT_COLOUR)
        text.set_fontsize(max(8.0, text.get_fontsize()))


def _nearest_group(ax: Any, x: float) -> str:
    ticks = np.asarray(ax.get_xticks(), dtype=float)
    labels = [label.get_text() for label in ax.get_xticklabels()]
    if not len(ticks):
        return ""
    index = int(np.argmin(np.abs(ticks - x)))
    if index < len(labels) and np.isclose(ticks[index], x, atol=0.5):
        return labels[index]
    return f"{x:g}"


def _year_series(ax: Any, x: float) -> str:
    if "vs" not in _CONTEXT["survey"].casefold():
        return ""
    ticks = np.asarray(ax.get_xticks(), dtype=float)
    if not len(ticks):
        return ""
    tick = float(ticks[np.argmin(np.abs(ticks - x))])
    if np.isclose(tick, x, atol=0.04):
        return ""
    return "2008" if x < tick else "2019"


def _rows_from_figure(fig: Any, path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    figure_name = path.stem
    for panel_index, ax in enumerate(fig.axes, start=1):
        panel = ax.get_title() or f"Panel {panel_index}"
        quantity = ax.get_ylabel() or ax.get_title() or "Value"
        unit_match = re.search(
            r"(?<![A-Za-z])(kJ|minutes|min|km/h|W|%)(?![A-Za-z])",
            ax.get_ylabel(),
            re.IGNORECASE,
        )
        unit = unit_match.group(1) if unit_match else ""
        by_group: dict[tuple[str, str], dict[str, Any]] = {}

        def row_for(group: str, subgroup: str) -> dict[str, Any]:
            key = (group, subgroup)
            if key not in by_group:
                by_group[key] = {
                    "figure": figure_name,
                    "panel": panel,
                    "scope": _CONTEXT["scope"],
                    "survey": _CONTEXT["survey"],
                    "group": group,
                    "subgroup": subgroup,
                    "quantity": quantity,
                    "unit": unit,
                    "days": _CONTEXT["days"],
                    "basis": _panel_basis(ax, panel, _CONTEXT["basis"]),
                    "n": "",
                    "mean": "",
                    "ci_low": "",
                    "ci_high": "",
                    "median": "",
                    "p25": "",
                    "p75": "",
                    "ratio": "",
                    "ratio_ci_low": "",
                    "ratio_ci_high": "",
                }
            return by_group[key]

        for patch in ax.patches:
            if not patch.get_visible() or not hasattr(patch, "get_height"):
                continue
            x = float(patch.get_x() + patch.get_width() / 2)
            group = _nearest_group(ax, x)
            label = getattr(patch, "get_label", lambda: "")()
            subgroup = "" if not label or label.startswith("_") else label
            colour = to_hex(patch.get_facecolor())
            if colour == SURVEY_COLOURS["ENTD 2008"]:
                subgroup = "2008"
            elif colour == SURVEY_COLOURS["EMP 2019"]:
                subgroup = "2019"
            row = row_for(group, subgroup)
            value = float(patch.get_y() + patch.get_height())
            if np.isfinite(value):
                row["mean"] = value

        for line in ax.lines:
            x_data = np.asarray(line.get_xdata(), dtype=float)
            y_data = np.asarray(line.get_ydata(), dtype=float)
            if (
                len(x_data) == 1
                and len(y_data) == 1
                and line.get_marker()
                not in (
                    "None",
                    "",
                    None,
                )
            ):
                group = _nearest_group(ax, float(x_data[0]))
                label = line.get_label()
                if "median" in label.casefold() or line.get_marker() == "D":
                    row_for(group, "")["median"] = float(y_data[0])
                else:
                    row_for(group, label if not label.startswith("_") else "")[
                        "mean"
                    ] = float(y_data[0])
            elif len(y_data) >= 2 and np.allclose(y_data, y_data[0]):
                label = line.get_label()
                if line.get_linestyle() in ("--", "-.", ":") and not label.startswith(
                    "_"
                ):
                    group = "All"
                    row_for(group, label)["mean"] = float(y_data[0])
            elif len(x_data) == len(y_data) and len(y_data) > 1:
                label = line.get_label()
                if label.startswith("_"):
                    continue
                for x_value, y_value in zip(x_data, y_data, strict=True):
                    if np.isfinite(x_value) and np.isfinite(y_value):
                        row_for(f"{x_value:.6g}", label)["mean"] = float(y_value)

        for collection in ax.collections:
            get_offsets = getattr(collection, "get_offsets", None)
            if get_offsets is None:
                continue
            offsets = np.asarray(get_offsets())
            paths = getattr(collection, "get_paths", lambda: [])()
            if offsets.ndim != 2 or offsets.shape[1] != 2 or not paths:
                continue
            if not any(len(path.vertices) == 5 for path in paths):
                continue
            quantiles = getattr(collection, "_figure_quantile_values", None)
            for index, (x_value, y_value) in enumerate(offsets):
                if np.isfinite(x_value) and np.isfinite(y_value):
                    group = _nearest_group(ax, float(x_value))
                    row = row_for(group, _year_series(ax, float(x_value)))
                    row["median"] = float(y_value)
                    if quantiles is not None:
                        row["p25"] = float(quantiles[index, 0])
                        row["p75"] = float(quantiles[index, 2])

        for container in ax.containers:
            parts = getattr(container, "lines", None)
            if not parts or len(parts) < 3:
                continue
            bar_line_collections = parts[2]
            if not bar_line_collections:
                continue
            for collection in bar_line_collections:
                for segment in collection.get_segments():
                    points = np.asarray(segment)
                    if points.shape != (2, 2) or not np.isclose(
                        points[0, 0], points[1, 0]
                    ):
                        continue
                    group = _nearest_group(ax, float(points[0, 0]))
                    label = container.get_label()
                    row = row_for(group, label if label in ("2008", "2019") else "")
                    row["ci_low"] = float(np.min(points[:, 1]))
                    row["ci_high"] = float(np.max(points[:, 1]))

        for text in ax.texts:
            match = re.search(r"\bn\s*=\s*(\d+)\b", text.get_text())
            sample_size = getattr(text, "_figure_n_value", None)
            if match or sample_size is not None:
                x_position = float(text.get_position()[0])
                group = _nearest_group(ax, x_position)
                n = int(sample_size if sample_size is not None else match.group(1))
                row_for(group, "")["n"] = n
                year = _year_series(ax, x_position)
                if year:
                    row_for(group, year)["n"] = n
            ratio_match = re.search(
                r"×([\d.]+)\s+\[([\d.]+),\s*([\d.]+)\]", text.get_text()
            )
            if ratio_match:
                row = row_for(
                    _nearest_group(ax, float(text.get_position()[0])), "2019/2008"
                )
                values = getattr(
                    text,
                    "_figure_ratio_values",
                    tuple(float(ratio_match.group(i)) for i in (1, 2, 3)),
                )
                row["ratio"], row["ratio_ci_low"], row["ratio_ci_high"] = values

        for image in ax.images:
            values = np.asarray(image.get_array())
            if values.ndim != 2:
                continue
            x_labels = [label.get_text() for label in ax.get_xticklabels()]
            y_labels = [label.get_text() for label in ax.get_yticklabels()]
            for y_index, row_label in enumerate(y_labels):
                for x_index, col_label in enumerate(x_labels):
                    if y_index >= values.shape[0] or x_index >= values.shape[1]:
                        continue
                    value = float(values[y_index, x_index])
                    record = row_for(row_label, col_label)
                    if np.isfinite(value):
                        record["mean"] = value

        for group in {key[0] for key in by_group}:
            sizes = [
                record["n"]
                for (row_group, _), record in by_group.items()
                if row_group == group and record["n"] != ""
            ]
            if sizes:
                for (row_group, _), record in by_group.items():
                    if row_group == group and record["n"] == "":
                        record["n"] = max(sizes)
        rows.extend(by_group.values())
    return rows


def _panel_basis(ax: Any, panel: str, default: str) -> str:
    description = f"{panel} {ax.get_ylabel()}".casefold()
    if "per person" in description:
        return "per person"
    if "per trip" in description or "one-way trip" in description:
        return "per trip"
    return default


def save_figure(
    fig: Any,
    path: Path,
    *,
    survey: str | None = None,
    rows: list[dict[str, Any]] | None = None,
) -> Path:
    """Save a 7-inch, 200-dpi PNG and a same-stem CSV of plotted values."""
    _apply_style(fig, survey=survey or _CONTEXT["survey"])
    fig.text(
        0.5,
        0.955,
        " · ".join(
            value
            for value in (
                _CONTEXT["scope"],
                _CONTEXT["days"],
                _CONTEXT["basis"],
                _CONTEXT["survey"],
            )
            if value
        ),
        ha="center",
        va="top",
        fontsize=8,
        color=SECONDARY_TEXT_COLOUR,
    )
    fig.text(
        0.5,
        0.012,
        "Mean and 95% CI (household bootstrap, "
        f"{_CONTEXT['replicates']} replicates); ◇ median; bar = quartiles; "
        f"{_CONTEXT['section']}",
        ha="center",
        va="bottom",
        fontsize=8,
        color=SECONDARY_TEXT_COLOUR,
    )
    fig.tight_layout(rect=(0.0, 0.04, 1.0, 0.91))
    fig.savefig(path, dpi=200, facecolor=BACKGROUND_COLOUR)
    data_path = path.with_suffix(".csv")
    output_rows = _rows_from_figure(fig, path) if rows is None else rows
    with data_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in output_rows:
            writer.writerow({column: row.get(column, "") for column in CSV_COLUMNS})
    return path
