#!/usr/bin/env python3
"""Phase 8: Evaluation analysis and visuals.

Reads Google-vs-model evaluation rows from Phase 7 and produces:
- Row-level comparison table
- Metrics summaries (mode x hour, mode overall)
- Diagnostic summaries by duration and distance bins
- Plots (scatter and residual histograms)
"""

from __future__ import annotations

import argparse
import logging
import math
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parent.parent

DEFAULT_RESULTS_CSV = (
    ROOT_DIR
    / "outputs"
    / "07_evaluation_pipeline_google_subset_pt"
    / "evaluation_google_results_public_transport_exact_conditions.csv"
)
DEFAULT_OUTPUT_DIR = ROOT_DIR / "outputs" / "08_evaluation_visuals_google_subset_pt"
DEFAULT_PLOTS_DIR = ROOT_DIR / "visuals" / "08_evaluation_visuals_google_subset_pt"


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT_DIR / path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 8: evaluate model vs Google results")
    parser.add_argument("--results-csv", type=Path, default=DEFAULT_RESULTS_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--plots-dir", type=Path, default=DEFAULT_PLOTS_DIR)
    parser.add_argument("--status-ok", type=str, default="OK", help="Google status value treated as successful")
    parser.add_argument("--skip-plots", action="store_true")
    return parser.parse_args()


def _normalize_hhmm(value: str) -> str:
    raw = str(value).strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%H:%M")
        except ValueError:
            continue
    if len(raw) >= 5:
        candidate = raw[:5]
        try:
            dt = datetime.strptime(candidate, "%H:%M")
            return dt.strftime("%H:%M")
        except ValueError:
            pass
    return raw


def _safe_div(a: pd.Series | float, b: pd.Series | float) -> pd.Series | float:
    if isinstance(a, pd.Series) or isinstance(b, pd.Series):
        a_s = a if isinstance(a, pd.Series) else pd.Series(a)
        b_s = b if isinstance(b, pd.Series) else pd.Series(b)
        out = a_s / b_s.replace(0, np.nan)
        return out
    if b == 0:
        return float("nan")
    return a / b


def _add_bins(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()

    dur_edges = [-float("inf"), 900, 1800, 2700, 3600, float("inf")]
    dur_labels = ["0-15", "15-30", "30-45", "45-60", "60+"]
    work["model_duration_bin"] = pd.cut(work["model_duration_s"], bins=dur_edges, labels=dur_labels, include_lowest=True)

    dist_edges = [-float("inf"), 2000, 5000, 10000, 20000, float("inf")]
    dist_labels = ["0-2km", "2-5km", "5-10km", "10-20km", "20km+"]
    work["google_distance_bin"] = pd.cut(work["google_distance_m"], bins=dist_edges, labels=dist_labels, include_lowest=True)

    return work


def _prepare_comparison(df: pd.DataFrame, status_ok: str) -> pd.DataFrame:
    work = df.copy()

    if "departure_time_local" in work.columns:
        work["departure_time_local"] = work["departure_time_local"].astype(str).map(_normalize_hhmm)

    numeric_cols = ["model_duration_s", "google_duration_s", "google_distance_m"]
    for col in numeric_cols:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce")

    for required in ["mode", "departure_time_local", "google_status", "model_duration_s", "google_duration_s"]:
        if required not in work.columns:
            raise ValueError(f"Missing required column: {required}")

    work["is_ok"] = work["google_status"].astype(str).str.upper().eq(status_ok.upper())
    work["delta_s"] = work["google_duration_s"] - work["model_duration_s"]
    work["abs_error_s"] = work["delta_s"].abs()

    work["ape"] = _safe_div(work["abs_error_s"], work["google_duration_s"])
    work["ape_pct"] = 100.0 * work["ape"]

    work["signed_pe"] = _safe_div(work["delta_s"], work["google_duration_s"])
    work["signed_pe_pct"] = 100.0 * work["signed_pe"]

    work = _add_bins(work)

    ordered_cols = [
        "request_id",
        "sample_id",
        "mode",
        "departure_date",
        "departure_time_local",
        "origin_id",
        "dest_id",
        "google_status",
        "google_http_status",
        "google_error",
        "is_ok",
        "model_duration_s",
        "google_duration_s",
        "google_distance_m",
        "delta_s",
        "abs_error_s",
        "ape",
        "ape_pct",
        "signed_pe",
        "signed_pe_pct",
        "model_duration_bin",
        "google_distance_bin",
    ]
    cols = [c for c in ordered_cols if c in work.columns]
    return work[cols]


def _metrics_from_group(group: pd.DataFrame) -> pd.Series:
    total_n = len(group)
    ok = group[group["is_ok"] & group["model_duration_s"].notna() & group["google_duration_s"].notna()].copy()
    ok_n = len(ok)

    if ok_n == 0:
        return pd.Series(
            {
                "n_total": total_n,
                "n_ok": 0,
                "n_not_ok": total_n,
                "ok_rate": 0.0,
                "mean_delta_s": np.nan,
                "median_delta_s": np.nan,
                "mae_s": np.nan,
                "rmse_s": np.nan,
                "mape_pct": np.nan,
                "median_ape_pct": np.nan,
                "p90_abs_error_s": np.nan,
                "pearson_r": np.nan,
            }
        )

    delta = ok["delta_s"].astype(float)
    abs_error = ok["abs_error_s"].astype(float)
    ape_pct = ok["ape_pct"].astype(float)

    rmse = float(np.sqrt(np.mean(np.square(delta)))) if len(delta) > 0 else np.nan
    corr = ok["model_duration_s"].corr(ok["google_duration_s"]) if ok_n > 1 else np.nan

    return pd.Series(
        {
            "n_total": total_n,
            "n_ok": ok_n,
            "n_not_ok": total_n - ok_n,
            "ok_rate": ok_n / total_n if total_n > 0 else np.nan,
            "mean_delta_s": float(delta.mean()),
            "median_delta_s": float(delta.median()),
            "mae_s": float(abs_error.mean()),
            "rmse_s": rmse,
            "mape_pct": float(ape_pct.mean(skipna=True)),
            "median_ape_pct": float(ape_pct.median(skipna=True)),
            "p90_abs_error_s": float(abs_error.quantile(0.9)),
            "pearson_r": float(corr) if pd.notna(corr) else np.nan,
        }
    )


def _build_summaries(comp_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    by_mode_hour = (
        comp_df.groupby(["mode", "departure_time_local"], dropna=False)
        .apply(_metrics_from_group)
        .reset_index()
        .sort_values(["mode", "departure_time_local"])
        .reset_index(drop=True)
    )

    by_mode = (
        comp_df.groupby(["mode"], dropna=False)
        .apply(_metrics_from_group)
        .reset_index()
        .sort_values(["mode"])
        .reset_index(drop=True)
    )

    ok_only = comp_df[comp_df["is_ok"]].copy()

    by_duration_bin = (
        ok_only.groupby(["mode", "departure_time_local", "model_duration_bin"], dropna=False)
        .agg(
            n=("request_id", "size"),
            mean_delta_s=("delta_s", "mean"),
            mae_s=("abs_error_s", "mean"),
            rmse_s=("delta_s", lambda x: float(np.sqrt(np.mean(np.square(x)))) if len(x) else np.nan),
            mape_pct=("ape_pct", "mean"),
            p90_abs_error_s=("abs_error_s", lambda x: float(x.quantile(0.9)) if len(x) else np.nan),
        )
        .reset_index()
        .sort_values(["mode", "departure_time_local", "model_duration_bin"])
        .reset_index(drop=True)
    )

    by_distance_bin = (
        ok_only.groupby(["mode", "departure_time_local", "google_distance_bin"], dropna=False)
        .agg(
            n=("request_id", "size"),
            mean_delta_s=("delta_s", "mean"),
            mae_s=("abs_error_s", "mean"),
            rmse_s=("delta_s", lambda x: float(np.sqrt(np.mean(np.square(x)))) if len(x) else np.nan),
            mape_pct=("ape_pct", "mean"),
            p90_abs_error_s=("abs_error_s", lambda x: float(x.quantile(0.9)) if len(x) else np.nan),
        )
        .reset_index()
        .sort_values(["mode", "departure_time_local", "google_distance_bin"])
        .reset_index(drop=True)
    )

    return {
        "summary_mode_hour": by_mode_hour,
        "summary_mode": by_mode,
        "summary_duration_bin": by_duration_bin,
        "summary_distance_bin": by_distance_bin,
    }


def _scatter_plot(group: pd.DataFrame, mode: str, dep_time: str, out_path: Path) -> None:
    x = group["model_duration_s"].astype(float)
    y = group["google_duration_s"].astype(float)
    if len(group) == 0:
        return

    lim = max(float(x.max()), float(y.max()))
    lim = max(lim, 1.0)

    mae = float((y - x).abs().mean())
    bias = float((y - x).mean())

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(x, y, alpha=0.75)
    ax.plot([0, lim], [0, lim], linestyle="--")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Model duration (s)")
    ax.set_ylabel("Google duration (s)")
    ax.set_title(f"{mode} @ {dep_time} (n={len(group)}, MAE={mae:.1f}s, bias={bias:.1f}s)")
    ax.grid(True, alpha=0.25)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _residual_hist(group: pd.DataFrame, mode: str, dep_time: str, out_path: Path) -> None:
    residuals = (group["google_duration_s"] - group["model_duration_s"]).astype(float)
    if len(residuals) == 0:
        return

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(residuals, bins=20, alpha=0.8)
    ax.axvline(0.0, linestyle="--")
    ax.set_xlabel("Residual (Google - model) [s]")
    ax.set_ylabel("Count")
    ax.set_title(f"Residuals: {mode} @ {dep_time}")
    ax.grid(True, alpha=0.2)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_mae_overview(summary_mode_hour: pd.DataFrame, out_path: Path) -> None:
    if summary_mode_hour.empty:
        return

    pivot = summary_mode_hour.pivot(index="mode", columns="departure_time_local", values="mae_s")
    if pivot.empty:
        return

    ax = pivot.plot(kind="bar", figsize=(8, 4))
    ax.set_ylabel("MAE (s)")
    ax.set_title("MAE by mode and departure time")
    ax.grid(True, axis="y", alpha=0.25)
    plt.xticks(rotation=0)

    fig = ax.get_figure()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _write_plots(comp_df: pd.DataFrame, summary_mode_hour: pd.DataFrame, output_dir: Path) -> None:
    ok = comp_df[comp_df["is_ok"] & comp_df["model_duration_s"].notna() & comp_df["google_duration_s"].notna()].copy()
    if ok.empty:
        logger.warning("No OK rows with durations available for plots")
        return

    for (mode, dep_time), group in ok.groupby(["mode", "departure_time_local"]):
        scatter_path = output_dir / "plots" / "scatter" / f"scatter_{mode}_{str(dep_time).replace(':', '')}.png"
        hist_path = output_dir / "plots" / "residual_hist" / f"residual_hist_{mode}_{str(dep_time).replace(':', '')}.png"
        _scatter_plot(group, str(mode), str(dep_time), scatter_path)
        _residual_hist(group, str(mode), str(dep_time), hist_path)

    _plot_mae_overview(summary_mode_hour, output_dir / "plots" / "mae_by_mode_hour.png")


def main() -> None:
    args = _parse_args()

    args.results_csv = _resolve(args.results_csv)
    args.output_dir = _resolve(args.output_dir)
    args.plots_dir = _resolve(args.plots_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.plots_dir.mkdir(parents=True, exist_ok=True)

    if not args.results_csv.exists():
        raise FileNotFoundError(f"Missing results CSV: {args.results_csv}")

    logger.info("Loading Phase 7 results: %s", args.results_csv)
    raw_df = pd.read_csv(args.results_csv)
    if raw_df.empty:
        raise RuntimeError("Results CSV is empty")

    logger.info("Preparing comparison table")
    comp_df = _prepare_comparison(raw_df, status_ok=args.status_ok)

    comparison_path = args.output_dir / "evaluation_comparison.csv"
    comp_df.to_csv(comparison_path, index=False)
    logger.info("Wrote comparison rows: %s (%s rows)", comparison_path, len(comp_df))

    logger.info("Computing summary metrics")
    summaries = _build_summaries(comp_df)

    summary_mode_hour_path = args.output_dir / "evaluation_summary_by_mode_hour.csv"
    summary_mode_path = args.output_dir / "evaluation_summary_by_mode.csv"
    summary_duration_bin_path = args.output_dir / "evaluation_summary_by_duration_bin.csv"
    summary_distance_bin_path = args.output_dir / "evaluation_summary_by_distance_bin.csv"

    summaries["summary_mode_hour"].to_csv(summary_mode_hour_path, index=False)
    summaries["summary_mode"].to_csv(summary_mode_path, index=False)
    summaries["summary_duration_bin"].to_csv(summary_duration_bin_path, index=False)
    summaries["summary_distance_bin"].to_csv(summary_distance_bin_path, index=False)

    logger.info("Wrote summary metrics to %s", args.output_dir)

    if not args.skip_plots:
        logger.info("Generating plots")
        _write_plots(comp_df, summaries["summary_mode_hour"], args.plots_dir)

    logger.info("Phase 8 evaluation analysis completed")


if __name__ == "__main__":
    main()
