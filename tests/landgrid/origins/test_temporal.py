import duckdb
import pyarrow as pa
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


def test_allocates_grown_commune_totals_and_reconciles_age_margins() -> None:
    from landgrid.origins.temporal import allocate_commune_controls

    base = pa.Table.from_pylist([
        {
            "commune_code": "a", "ind": 10.0, "age_child": 3.0,
            "age_adult": 3.0, "men": 5.0,
        },
        {
            "commune_code": "b", "ind": 20.0, "age_child": 10.0,
            "age_adult": 10.0, "men": 12.0,
        },
    ])
    growth = pa.Table.from_pylist([
        {
            "commune_code": "a", "ind": 2.0, "age_child": 1.0,
            "age_adult": 3.0, "men": 1.2,
        },
        {
            "commune_code": "b", "ind": 1.0, "age_child": 1.0,
            "age_adult": 1.0, "men": 1.0,
        },
    ])
    weights = pa.Table.from_pylist([
        {
            "cell_id": 1, "commune_code": "a", "ind": 1.0,
            "age_child": 1.0, "age_adult": 1.0, "men": 1.0,
        },
        {
            "cell_id": 2, "commune_code": "a", "ind": 3.0,
            "age_child": 3.0, "age_adult": 1.0, "men": 3.0,
        },
        {
            "cell_id": 2, "commune_code": "b", "ind": 1.0,
            "age_child": 1.0, "age_adult": 1.0, "men": 1.0,
        },
    ])
    with duckdb.connect() as connection:
        connection.register("base_controls", base)
        connection.register("growth_factors", growth)
        connection.register("target_weights", weights)
        report = allocate_commune_controls(
            connection,
            base_relation="base_controls",
            growth_relation="growth_factors",
            weights_relation="target_weights",
            variables=("ind", "age_child", "age_adult", "men"),
            age_variables=("age_child", "age_adult"),
        )
        allocated = connection.execute(
            """
            SELECT commune_code, sum(ind) AS ind,
                sum(age_child) AS age_child, sum(age_adult) AS age_adult,
                sum(men) AS men
            FROM _temporal_allocated
            GROUP BY commune_code ORDER BY commune_code
            """
        ).to_arrow_table().to_pylist()
        cells = connection.execute(
            "SELECT cell_id, ind FROM _temporal_target_cells ORDER BY cell_id"
        ).to_arrow_table().to_pylist()

    assert allocated == [
        {
            "commune_code": "a", "ind": 20.0, "age_child": 5.0,
            "age_adult": 15.0, "men": 6.0,
        },
        {
            "commune_code": "b", "ind": 20.0, "age_child": 10.0,
            "age_adult": 10.0, "men": 12.0,
        },
    ]
    assert cells == [{"cell_id": 1, "ind": 5.0}, {"cell_id": 2, "ind": 35.0}]
    assert report["age_adjusted_communes"] == 1
    assert report["age_adjustment_min"] == 1.0
    assert report["age_adjustment_max"] == pytest.approx(20 / 12)


def test_commune_allocation_rejects_positive_totals_without_target_weights() -> None:
    from landgrid.origins.temporal import allocate_commune_controls

    with duckdb.connect() as connection:
        connection.register(
            "base_controls",
            pa.Table.from_pylist([{"commune_code": "a", "ind": 1.0}]),
        )
        connection.register(
            "growth_factors",
            pa.Table.from_pylist([{"commune_code": "a", "ind": 1.0}]),
        )
        connection.register(
            "target_weights",
            pa.Table.from_pylist([{"cell_id": 1, "commune_code": "a", "ind": 0.0}]),
        )
        with pytest.raises(ValueError, match="zero target weights"):
            allocate_commune_controls(
                connection,
                base_relation="base_controls",
                growth_relation="growth_factors",
                weights_relation="target_weights",
                variables=("ind",),
                age_variables=(),
            )
