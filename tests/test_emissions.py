"""Smoke tests for ``unitgps.engine.emissions``."""

from __future__ import annotations

import math

from unitgps.engine import determine_conversion, determine_ghg_emissions, find_gwp


def test_find_gwp_co2_is_1(gwps) -> None:
    assert find_gwp(gwps, "CO2", "AR5", "100") == 1.0


def test_find_gwp_ch4_ar5_100(gwps) -> None:
    """AR5/100yr CH4 GWP = 28."""
    assert find_gwp(gwps, "CH4", "AR5", "100") == 28.0


def test_find_gwp_n2o_ar5_100(gwps) -> None:
    """AR5/100yr N2O GWP = 265."""
    assert find_gwp(gwps, "N2O", "AR5", "100") == 265.0


def test_find_gwp_unknown_returns_none(gwps) -> None:
    assert find_gwp(gwps, "NOT_A_GAS", "AR5", "100") is None


def test_determine_conversion_kj_to_j(graph, empty_search_params) -> None:
    """High-level wrapper: 1 kJ → J should return success with factor=1000."""
    result = determine_conversion(graph, empty_search_params, "kJ", "J", 1.0)
    assert result["status"] == "success"
    assert result["data"]
    assert math.isclose(result["data"][0]["conversion_factor"], 1000.0, rel_tol=1e-9)


def test_determine_conversion_no_path(graph, empty_search_params) -> None:
    """Two unrelated units with no path → status=error."""
    # 'fake_unit' isn't in the graph, so this will error out.
    result = determine_conversion(graph, empty_search_params, "kg", "fake_unit_xyz", 1.0)
    assert result["status"] == "error"


def test_determine_ghg_emissions_runs(graph, gwps, empty_search_params) -> None:
    """End-to-end: routing CO2/CH4/N2O for a coal-energy input should succeed."""
    # Pick Anthracite coal emission factors → mmBTU input → kg output
    params = dict(empty_search_params)
    params["Source-Chemical Type"] = ["Anthracite"]
    result = determine_ghg_emissions(graph, params, "mmBTU", "kg", 1.0, gwps)

    assert result["valid_calc"], f"calculation failed: {result['results']}"
    # CO2 emissions for Anthracite per mmBTU is ~103.69 kg per EPA
    co2 = result["results"]["CO2"]
    assert co2["Mass"] is not None
    assert co2["Mass"] > 50  # sanity floor
    assert co2["Mass"] < 200  # sanity ceiling
    # Total CO2e should be greater than CO2 alone (CH4 and N2O add a bit)
    assert result["total_co2e"] >= co2["Mass"]
