"""Smoke tests for ``unitgps.engine.graph``."""

from __future__ import annotations


def test_graph_builds(graph) -> None:
    """The full graph has a substantial number of nodes and edges."""
    assert len(graph.G.nodes) > 50
    assert len(graph.G.edges) > 1000


def test_common_units_are_nodes(graph) -> None:
    for unit in ["J", "kJ", "kg", "g", "BTU", "Cal"]:
        assert graph.G.has_node(unit), f"missing expected node: {unit}"


def test_filter_keeps_unit_conversions(graph, empty_search_params) -> None:
    """With no filters and EFs excluded, unit conversion edges remain."""
    F = graph.filter_graph(empty_search_params, include_emission_factors=False)
    sets_seen = {d.get("Set") for _, _, d in F.edges(data=True)}
    assert "Unit Conversion" in sets_seen
    assert "Magnitude Adjustment" in sets_seen


def test_filter_excludes_emission_factors_by_default(graph, empty_search_params) -> None:
    F = graph.filter_graph(empty_search_params, include_emission_factors=False)
    sets_seen = {d.get("Set") for _, _, d in F.edges(data=True)}
    assert "Emission Factors" not in sets_seen


def test_filter_includes_emission_factors_when_requested(graph, empty_search_params) -> None:
    F = graph.filter_graph(empty_search_params, include_emission_factors=True)
    sets_seen = {d.get("Set") for _, _, d in F.edges(data=True)}
    assert "Emission Factors" in sets_seen


def test_get_nodes_by_dimension(graph) -> None:
    weights = graph.get_nodes_by_dimension("Weight")
    assert "kg" in weights
    assert "g" in weights
