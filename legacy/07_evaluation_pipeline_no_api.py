#!/usr/bin/env python3
"""Run Phase 7 evaluation pipeline without Google API calls.

This wrapper enforces `--skip-api` and forwards all other CLI options to:
`codes/07_evaluation_pipeline.py`.

Examples:
  python codes/07_evaluation_pipeline_no_api.py
  python codes/07_evaluation_pipeline_no_api.py --sample-per-mode 200 --departure-times 07:00 08:20
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
PHASE7_SCRIPT = ROOT_DIR / "codes" / "07_evaluation_pipeline.py"


def _parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description="Run Phase 7 without Google API")
    parser.add_argument(
        "--python-bin",
        type=str,
        default=sys.executable,
        help="Python executable used to run 07_evaluation_pipeline.py",
    )
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="Also skip plot generation (forwarded to Phase 7)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Forward resume behavior for API mode (kept for compatibility)",
    )
    args, passthrough = parser.parse_known_args()
    return args, passthrough


def main() -> None:
    args, passthrough = _parse_args()

    if not PHASE7_SCRIPT.exists():
        raise FileNotFoundError(f"Missing script: {PHASE7_SCRIPT}")

    cmd = [args.python_bin, str(PHASE7_SCRIPT), "--skip-api"]
    if args.skip_plots:
        cmd.append("--skip-plots")
    if args.resume:
        cmd.append("--resume")
    cmd.extend(passthrough)

    completed = subprocess.run(cmd, cwd=str(ROOT_DIR), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
