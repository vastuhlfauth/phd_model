import pytest


def test_projects_census_growth_over_a_shorter_interval() -> None:
    from landgrid.origins.temporal import projected_growth_factor

    factor = projected_growth_factor(
        90, 120, observed_years=6, projected_years=2
    )
    assert factor == pytest.approx((4 / 3) ** (1 / 3))


@pytest.mark.parametrize(
    ("start", "end"),
    [(0, 10), (-1, 10), (10, -1), (float("nan"), 10)],
)
def test_rejects_invalid_growth_inputs(start: float, end: float) -> None:
    from landgrid.origins.temporal import projected_growth_factor

    with pytest.raises(ValueError, match="growth"):
        projected_growth_factor(start, end, observed_years=6, projected_years=2)


def test_rescales_age_margins_to_grown_individual_total() -> None:
    from landgrid.origins.temporal import rescale_age_margins

    adjusted, adjustment = rescale_age_margins(
        {"child": 20.0, "adult": 30.0}, individual_total=60.0
    )
    assert adjusted == {"child": 24.0, "adult": 36.0}
    assert adjustment == pytest.approx(1.2)


def test_rejects_positive_individuals_without_age_support() -> None:
    from landgrid.origins.temporal import rescale_age_margins

    with pytest.raises(ValueError, match="age margin"):
        rescale_age_margins({"child": 0.0, "adult": 0.0}, individual_total=1.0)
