import zipfile
from io import BytesIO

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


def test_derives_approved_census_age_bands() -> None:
    from landgrid.origins.temporal import derive_age_measures

    derived = derive_age_measures({
        "under_15": 100.0,
        "age_6_10": 20.0,
        "age_11_14": 30.0,
        "age_15_17": 15.0,
        "age_18_24": 40.0,
        "age_25_39": 50.0,
        "age_40_54": 60.0,
        "age_55_64": 70.0,
        "age_65_79": 80.0,
        "age_80p": 90.0,
    })
    assert derived["age_0_5"] == 50.0
    assert derived["age_11_17"] == 45.0
    assert derived["age_18_24"] == 40.0
    assert derived["age_25_39"] == 50.0


def test_growth_factors_use_age_and_denominator_fallbacks() -> None:
    from landgrid.origins.temporal import calculate_growth_factors

    growth, fallbacks = calculate_growth_factors(
        {"individuals": 100.0, "households": 40.0, "age_0_5": 0.0},
        {"individuals": 110.0, "households": 50.0, "age_0_5": 8.0},
        variables=("ind", "ind_0_3", "log_soc", "ind_snv"),
        measure_by_variable={
            "ind": "individuals",
            "ind_0_3": "age_0_5",
            "log_soc": None,
            "ind_snv": None,
        },
        denominator_by_variable={
            "ind": "households",
            "ind_0_3": "individuals",
            "log_soc": "households",
            "ind_snv": "individuals",
        },
        observed_years=2,
        projected_years=2,
    )
    assert growth == pytest.approx({
        "ind": 1.1,
        "ind_0_3": 1.1,
        "log_soc": 1.25,
        "ind_snv": 1.1,
    })
    assert fallbacks == {"age_to_individual": 1, "denominator": 2}


def test_individual_growth_uses_ff_fallback_when_census_base_is_zero() -> None:
    from landgrid.origins.temporal import calculate_growth_factors

    growth, fallbacks = calculate_growth_factors(
        {"individuals": 0.0, "households": 10.0},
        {"individuals": 5.0, "households": 12.0},
        variables=("ind",),
        measure_by_variable={"ind": "individuals"},
        denominator_by_variable={"ind": "households"},
        observed_years=6,
        projected_years=2,
        fallback_individual_growth=1.03,
    )
    assert growth == {"ind": 1.03}
    assert fallbacks == {"individual_from_ff": 1}


def test_loads_year_specific_edges_from_cog_workbook(tmp_path) -> None:
    from landgrid.origins.temporal import load_cog_passage_edges

    workbook = BytesIO()
    with zipfile.ZipFile(workbook, "w") as archive:
        archive.writestr(
            "xl/workbook.xml",
            '<workbook xmlns="http://schemas.openxmlformats.org/'
            'spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships"><sheets><sheet name="COM" '
            'sheetId="1" r:id="rId1"/></sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/'
            'package/2006/relationships"><Relationship Id="rId1" '
            'Target="worksheets/sheet1.xml"/></Relationships>',
        )
        archive.writestr(
            "xl/sharedStrings.xml",
            '<sst xmlns="http://schemas.openxmlformats.org/'
            'spreadsheetml/2006/main"><si><t>NIVGEO</t></si>'
            '<si><t>CODGEO_2019</t></si><si><t>CODGEO_2021</t></si>'
            '<si><t>COM</t></si><si><t>01001</t></si><si><t>01002</t></si>'
            '<si><t>01003</t></si></sst>',
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            '<worksheet xmlns="http://schemas.openxmlformats.org/'
            'spreadsheetml/2006/main"><sheetData>'
            '<row r="6"><c r="A6" t="s"><v>0</v></c>'
            '<c r="B6" t="s"><v>1</v></c>'
            '<c r="C6" t="s"><v>2</v></c></row>'
            '<row r="7"><c r="A7" t="s"><v>3</v></c>'
            '<c r="B7" t="s"><v>4</v></c>'
            '<c r="C7" t="s"><v>4</v></c></row>'
            '<row r="8"><c r="A8" t="s"><v>3</v></c>'
            '<c r="B8" t="s"><v>5</v></c>'
            '<c r="C8" t="s"><v>6</v></c></row>'
            '<row r="9"><c r="A9" t="s"><v>3</v></c>'
            '<c r="B9" t="s"><v>5</v></c>'
            '<c r="C9" t="s"><v>4</v></c></row>'
            '</sheetData></worksheet>',
        )
    outer_path = tmp_path / "passage.zip"
    with zipfile.ZipFile(outer_path, "w") as outer:
        outer.writestr("passage.xlsx", workbook.getvalue())

    assert load_cog_passage_edges(
        outer_path, source_year=2019, target_year=2021
    ) == (("01001", "01001"), ("01002", "01001"), ("01002", "01003"))


def test_builds_stable_units_for_merges_splits_and_chains() -> None:
    from landgrid.origins.temporal import build_stable_growth_units

    units = build_stable_growth_units((
        ("old_a", "new_a"),
        ("old_b", "new_a"),
        ("old_c", "new_c1"),
        ("old_c", "new_c2"),
        ("old_chain", "bridge"),
        ("bridge", "new_chain"),
        ("old_d", "new_d"),
    ))
    assert units.code_to_unit["old_a"] == "new_a"
    assert units.code_to_unit["old_b"] == "new_a"
    assert units.code_to_unit["old_c"] == "new_c1|new_c2"
    assert units.code_to_unit["old_chain"] == "bridge|new_chain"
    assert units.code_to_unit["bridge"] == "bridge|new_chain"
    assert units.combined_units == {
        "new_a", "new_c1|new_c2", "bridge|new_chain",
    }
