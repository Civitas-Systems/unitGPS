"""Validation against authoritative external reference values.

Unlike the smoke tests (which check internal consistency), these assert the
engine reproduces *published* constants — NIST/SI unit conversions and the IPCC
AR4/AR5/AR6 100-year Global Warming Potentials. A failure here means the data or
engine diverged from an authoritative source: a substantive finding, not a
flaky test. All values confirmed matching on 2026-05-30.

References:
- NIST SP 811 (SI units); IT BTU = 1055.05585 J (rounded 1055.06).
- IPCC AR4 (2007) Table 2.14; AR5 (2013) Table 8.7; AR6 (2021) Table 7.15.
  (AR6 CH4 has fossil 29.8 / non-fossil 27.0 variants; the dataset stores 27.9.)
"""

from __future__ import annotations

import math

import pytest

from unitgps.engine import determine_conversion, find_gwp


# (source, target, expected factor for 1 source unit, reference note)
CONVERSIONS = [
    ("kJ", "J", 1000.0, "SI exact"),
    ("kg", "g", 1000.0, "SI exact"),
    ("BTU", "J", 1055.06, "NIST IT BTU"),
    ("mmBTU", "J", 1.05506e9, "1e6 IT BTU"),
    ("kWh", "J", 3.6e6, "SI exact"),
    ("hr", "s", 3600.0, "SI exact"),
    ("L", "m^3", 0.001, "SI exact"),
]


@pytest.mark.parametrize("source,target,expected,ref", CONVERSIONS)
def test_conversion_matches_reference(graph, empty_search_params, source, target, expected, ref) -> None:
    result = determine_conversion(graph, empty_search_params, source, target, 1.0)
    assert result["status"] == "success", f"no path {source} -> {target}"
    factor = result["data"][0]["conversion_factor"]
    assert math.isclose(factor, expected, rel_tol=1e-4), (
        f"1 {source} -> {target}: engine {factor:g} != reference {expected:g} ({ref})"
    )


# (gas, assessment report, expected 100-year GWP)
GWPS = [
    ("CO2", "AR4", 1.0), ("CH4", "AR4", 25.0), ("N2O", "AR4", 298.0),
    ("CO2", "AR5", 1.0), ("CH4", "AR5", 28.0), ("N2O", "AR5", 265.0),
    ("CO2", "AR6", 1.0), ("CH4", "AR6", 27.9), ("N2O", "AR6", 273.0),
]


@pytest.mark.parametrize("gas,report,expected", GWPS)
def test_gwp_matches_ipcc(gwps, gas, report, expected) -> None:
    value = find_gwp(gwps, gas, report, "100")
    assert value is not None, f"missing GWP {gas} {report} 100yr"
    assert math.isclose(value, expected, rel_tol=1e-3), (
        f"{report} {gas} 100yr: data {value} != IPCC {expected}"
    )


def test_anthracite_emission_factor_matches_epa(graph, gwps) -> None:
    """EPA GHG Emission Factors Hub — anthracite coal, stationary combustion:
    103.69 kg CO2, 11 g CH4 (0.011 kg), 1.6 g N2O (0.0016 kg) per mmBTU."""
    from unitgps.engine import determine_ghg_emissions

    params = {"Data Year": {"mode": "all", "values": []}, "Source-Chemical Type": ["Anthracite"]}
    r = determine_ghg_emissions(graph, params, "mmBTU", "kg", 1.0, gwps)
    assert math.isclose(r["results"]["CO2"]["Mass"], 103.69, rel_tol=1e-3), "CO2 EF != EPA 103.69"
    assert math.isclose(r["results"]["CH4"]["Mass"], 0.011, rel_tol=1e-2), "CH4 EF != EPA 11 g"
    assert math.isclose(r["results"]["N2O"]["Mass"], 0.0016, rel_tol=1e-2), "N2O EF != EPA 1.6 g"


ROUNDTRIP_UNITS = ["J", "kJ", "BTU", "kWh", "Cal", "mmBTU", "kg", "g", "L", "m^3"]


def test_round_trip_consistency(graph, empty_search_params) -> None:
    """A->B->A returns the original within 0.1% for connected units. The engine
    multiplies stored factors exactly; the residual is source-constant rounding
    across unit families (see QA_NOTES F2). This locks in the 0.1% bound so a
    larger regression would fail."""
    import itertools

    for u, v in itertools.combinations(ROUNDTRIP_UNITS, 2):
        r1 = determine_conversion(graph, empty_search_params, u, v, 1.0)
        r2 = determine_conversion(graph, empty_search_params, v, u, 1.0)
        if r1["status"] != "success" or r2["status"] != "success":
            continue
        f1 = r1["data"][0]["conversion_factor"]
        f2 = r2["data"][0]["conversion_factor"]
        assert math.isclose(f1 * f2, 1.0, rel_tol=1e-3), f"{u}<->{v} round-trip = {f1*f2:g}"
