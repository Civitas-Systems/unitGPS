"""Smoke tests for ``unitgps.engine.calculate``."""

from __future__ import annotations

import math

from unitgps.engine import (
    calculate_conversion_factor,
    convert_path_to_edge_tuples,
    format_sig_figs,
    identify_conversion_path,
    is_valid_parameter,
)


def test_format_sig_figs_basic() -> None:
    assert format_sig_figs(0) == "0"
    # Default 4 sig figs
    assert format_sig_figs(1234.5678).startswith("1235")
    # Tiny number → scientific notation
    assert "e" in format_sig_figs(0.0000123)
    # Huge number → scientific notation
    assert "e" in format_sig_figs(1.23e8)


def test_is_valid_parameter() -> None:
    assert is_valid_parameter("foo")
    assert is_valid_parameter(42)
    assert not is_valid_parameter(None)
    assert not is_valid_parameter("")
    assert not is_valid_parameter("   ")
    assert not is_valid_parameter("nan")
    assert not is_valid_parameter(float("nan"))


def test_kj_to_j_factor_is_1000(graph, empty_search_params) -> None:
    """1 kJ should equal 1000 J — the simplest non-trivial conversion."""
    F = graph.filter_graph(empty_search_params, include_emission_factors=False)
    paths = identify_conversion_path(F, "kJ", "J")
    edges = convert_path_to_edge_tuples(paths)
    results = calculate_conversion_factor(F, edges, starting_value=1.0)
    assert results, "expected at least one calculation result"
    assert math.isclose(results[0]["conversion_factor"], 1000.0, rel_tol=1e-9)
    assert math.isclose(results[0]["ultimate_value"], 1000.0, rel_tol=1e-9)


def test_btu_to_j_factor(graph, empty_search_params) -> None:
    """1 BTU ≈ 1055.06 J (per the data library's Unit Conversion entry)."""
    F = graph.filter_graph(empty_search_params, include_emission_factors=False)
    paths = identify_conversion_path(F, "BTU", "J")
    edges = convert_path_to_edge_tuples(paths)
    results = calculate_conversion_factor(F, edges, starting_value=1.0)
    assert results
    # Match to ~5 sig figs — the engine should pick the direct edge
    assert math.isclose(results[0]["conversion_factor"], 1055.06, rel_tol=1e-4)


def test_round_trip_is_identity(graph, empty_search_params) -> None:
    """J → kJ → J should land back at the starting value."""
    F = graph.filter_graph(empty_search_params, include_emission_factors=False)
    forward = calculate_conversion_factor(
        F, convert_path_to_edge_tuples(identify_conversion_path(F, "J", "kJ")), 1.0
    )
    backward = calculate_conversion_factor(
        F,
        convert_path_to_edge_tuples(identify_conversion_path(F, "kJ", "J")),
        forward[0]["ultimate_value"],
    )
    assert math.isclose(backward[0]["ultimate_value"], 1.0, rel_tol=1e-9)


def test_audit_steps_structure(graph, empty_search_params) -> None:
    """Every audit step exposes source/target and at least one edge dict."""
    F = graph.filter_graph(empty_search_params, include_emission_factors=False)
    results = calculate_conversion_factor(
        F,
        convert_path_to_edge_tuples(identify_conversion_path(F, "J", "kJ")),
        1.0,
    )
    audit = results[0]["audit_steps"]
    for step in audit:
        assert "source" in step and "target" in step
        assert step["edges"], "every step should have at least one edge"
        assert "value" in step["edges"][0]


# --------------------------------------------------------------------------- #
# edge_picks parameter — user override for parallel edge selection             #
# --------------------------------------------------------------------------- #


def _two_edge_graph():
    """Build a minimal graph A→B with two parallel edges (values 2 and 10)."""
    import networkx as nx

    G = nx.MultiDiGraph()
    G.add_edge("A", "B", key="alpha", Value=2, Set="EF")
    G.add_edge("A", "B", key="beta", Value=10, Set="EF")
    return G


def test_edge_picks_default_uses_first_edge() -> None:
    """No edge_picks means legacy behaviour — primary value is from edge 0."""
    G = _two_edge_graph()
    out = calculate_conversion_factor(G, [("A", "B")], starting_value=1.0)
    assert out[0]["conversion_factor"] == 2
    assert out[0]["audit_steps"][0]["chosen_edge_idx"] == 0


def test_edge_picks_selects_specified_edge() -> None:
    """Explicit pick uses the requested parallel edge."""
    G = _two_edge_graph()
    out = calculate_conversion_factor(
        G, [("A", "B")], starting_value=1.0, edge_picks={("A", "B"): 1}
    )
    assert out[0]["conversion_factor"] == 10
    assert out[0]["audit_steps"][0]["chosen_edge_idx"] == 1


def test_edge_picks_clamps_out_of_bounds() -> None:
    """Indices beyond the available edges clamp to the last edge, not crash."""
    G = _two_edge_graph()
    out = calculate_conversion_factor(
        G, [("A", "B")], starting_value=1.0, edge_picks={("A", "B"): 99}
    )
    # 2 edges, indices 0..1 — 99 clamps to 1
    assert out[0]["conversion_factor"] == 10
    assert out[0]["audit_steps"][0]["chosen_edge_idx"] == 1


def test_edge_picks_clamps_negative() -> None:
    """Negative indices clamp to 0 (defensive against stale UI state)."""
    G = _two_edge_graph()
    out = calculate_conversion_factor(
        G, [("A", "B")], starting_value=1.0, edge_picks={("A", "B"): -5}
    )
    assert out[0]["conversion_factor"] == 2
    assert out[0]["audit_steps"][0]["chosen_edge_idx"] == 0


def test_edge_picks_ignores_unrelated_edges() -> None:
    """A pick for an edge not on the path is silently ignored."""
    G = _two_edge_graph()
    out = calculate_conversion_factor(
        G, [("A", "B")], starting_value=1.0, edge_picks={("Z", "Q"): 7}
    )
    assert out[0]["conversion_factor"] == 2
    assert out[0]["audit_steps"][0]["chosen_edge_idx"] == 0


def test_edge_picks_per_step_on_multi_step_path() -> None:
    """Each step in a multi-step path can have its own pick."""
    import networkx as nx

    G = nx.MultiDiGraph()
    # A -> B has two parallel edges, B -> C has two parallel edges
    G.add_edge("A", "B", key="a1", Value=2, Set="EF")
    G.add_edge("A", "B", key="a2", Value=5, Set="EF")
    G.add_edge("B", "C", key="b1", Value=3, Set="EF")
    G.add_edge("B", "C", key="b2", Value=7, Set="EF")

    # Default — both step 0 picks
    out = calculate_conversion_factor(G, [("A", "B"), ("B", "C")], starting_value=1.0)
    assert out[0]["conversion_factor"] == 2 * 3  # 6

    # Pick second alternative for A->B only — first for B->C still defaults to 0
    out = calculate_conversion_factor(
        G, [("A", "B"), ("B", "C")], starting_value=1.0,
        edge_picks={("A", "B"): 1},
    )
    assert out[0]["conversion_factor"] == 5 * 3  # 15

    # Pick second for both — uses both upper alternatives
    out = calculate_conversion_factor(
        G, [("A", "B"), ("B", "C")], starting_value=1.0,
        edge_picks={("A", "B"): 1, ("B", "C"): 1},
    )
    assert out[0]["conversion_factor"] == 5 * 7  # 35
    assert out[0]["audit_steps"][0]["chosen_edge_idx"] == 1
    assert out[0]["audit_steps"][1]["chosen_edge_idx"] == 1


def test_edge_picks_is_ambiguous_flag_still_set() -> None:
    """Even with an explicit pick, the path is still flagged as ambiguous so
    the UI can surface that alternatives exist."""
    G = _two_edge_graph()
    out = calculate_conversion_factor(
        G, [("A", "B")], starting_value=1.0, edge_picks={("A", "B"): 1}
    )
    assert out[0]["is_ambiguous"] is True
    assert len(out[0]["ambiguous_details"]) == 1


def test_edge_picks_threaded_through_determine_conversion(graph, empty_search_params) -> None:
    """determine_conversion forwards edge_picks to the calculator."""
    from unitgps.engine import determine_conversion

    # Without edge_picks — should still succeed
    res = determine_conversion(graph, empty_search_params, "kJ", "J", 1.0)
    assert res["status"] == "success"
    legacy_factor = res["data"][0]["conversion_factor"]

    # With an irrelevant edge_picks (no ambiguity on this path) — same result
    res2 = determine_conversion(
        graph, empty_search_params, "kJ", "J", 1.0, edge_picks={("kJ", "J"): 0}
    )
    assert res2["status"] == "success"
    assert res2["data"][0]["conversion_factor"] == legacy_factor
