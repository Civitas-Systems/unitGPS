"""Smoke tests for ``unitgps.engine.data``."""

from __future__ import annotations

import math


def test_data_library_loads(combined_data) -> None:
    """The xlsx loads and expected columns are present."""
    expected = {"Value", "Conversion", "Set", "Numerator", "Denominator"}
    assert expected.issubset(set(combined_data.columns))
    # The raw file is 3,635 rows; with reciprocals it must be larger.
    assert len(combined_data) > 3635


def test_reciprocal_synthesized_for_known_row(combined_data) -> None:
    """For a specific known emission factor, its mathematical inverse must
    also appear in the combined DataFrame with Value ≈ 1/original."""
    ef = combined_data[combined_data["Set"] == "Emission Factors"]
    # Forward row: 1 mmBTU of Anthracite coal → 103.69 kg CO2
    fwd = ef[
        (ef["Numerator"] == "kg")
        & (ef["Denominator"] == "mmBTU")
        & (ef["GHG"] == "CO2")
        & (ef["Source-Chemical Type"] == "Anthracite")
    ]
    assert len(fwd) == 1, "expected exactly one forward Anthracite/mmBTU/CO2 row"
    forward_value = float(fwd["Value"].iloc[0])

    # Reciprocal row: 1 kg CO2 → 1/103.69 mmBTU of Anthracite
    rev = ef[
        (ef["Numerator"] == "mmBTU")
        & (ef["Denominator"] == "kg")
        & (ef["GHG"] == "CO2")
        & (ef["Source-Chemical Type"] == "Anthracite")
    ]
    assert len(rev) == 1, "reciprocal row was not synthesized"
    assert math.isclose(float(rev["Value"].iloc[0]), 1.0 / forward_value, rel_tol=1e-9)


def test_no_null_values(combined_data) -> None:
    """``load_data_library`` drops null Values."""
    assert combined_data["Value"].notna().all()


def test_static_conversions_not_duplicated(combined_data) -> None:
    """Unit Conversions are already bidirectional in the source — they should
    NOT be reciprocated again (otherwise we'd get duplicate edges)."""
    # The raw file has 294 Unit Conversion rows.
    uc = combined_data[combined_data["Set"] == "Unit Conversion"]
    assert len(uc) == 294


def test_unit_attributes(node_attrs) -> None:
    """Common units should be classified into the expected dimensions."""
    assert node_attrs["J"]["Unit Dimension"] == "Energy"
    assert node_attrs["kg"]["Unit Dimension"] == "Weight"
    assert node_attrs["kJ"]["Unit Dimension"] == "Energy"


def test_gwps_split_indicator(gwps) -> None:
    """``load_gwps`` splits ``Indicator='AR5-100'`` into separate columns."""
    assert "Assessment Report" in gwps.columns
    assert "Time Horizon" in gwps.columns
    assert "Indicator" not in gwps.columns
    # Known reference values
    co2_ar5_100 = gwps[
        (gwps["GHG"] == "CO2")
        & (gwps["Assessment Report"] == "AR5")
        & (gwps["Time Horizon"] == "100")
    ]
    assert len(co2_ar5_100) == 1
    assert float(co2_ar5_100["GWP"].iloc[0]) == 1.0
