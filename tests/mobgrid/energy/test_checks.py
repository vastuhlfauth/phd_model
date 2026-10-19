"""Smoke test for the step 7 visual/tabular checks CLI (section 9)."""

from pathlib import Path

from mobgrid.energy import checks


def test_checks_command_writes_figures_and_report_with_no_fail(tmp_path: Path) -> None:
    out_dir = tmp_path / "step7_energy"
    exit_code = checks.main(["--out", str(out_dir)])

    assert exit_code == 0

    png_files = sorted(out_dir.glob("*.png"))
    assert len(png_files) == 10

    md_path = out_dir.parent / f"{out_dir.name}_checks.md"
    assert md_path.is_file()
    report = md_path.read_text(encoding="utf-8")
    assert "| Status |" in report
    assert "| FAIL |" not in report
    assert "| PASS |" in report
