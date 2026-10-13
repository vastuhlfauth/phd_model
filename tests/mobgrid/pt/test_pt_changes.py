"""PT change catalogue acceptance tests (section 11.4)."""

from datetime import date
from pathlib import Path

from mobgrid.pt.pt_changes import load_pt_changes

ROOT = Path(__file__).resolve().parents[3]


def test_only_confirmed_changes_are_subtracted_from_past_state() -> None:
    catalogue = load_pt_changes(ROOT / "config" / "pt_changes.yaml")
    route_ids = {
        route_id
        for change in catalogue.changes_after(date(2024, 1, 1))
        for route_id in change.route_ids
    }
    assert route_ids == {"901", "911", "912", "A"}
    assert not catalogue.candidates
