"""Smoke tests for ``unitgps.engine.pathfinding``."""

from __future__ import annotations

from unitgps.engine import convert_path_to_edge_tuples, identify_conversion_path


def test_finds_direct_path(graph, empty_search_params) -> None:
    """kJ → J is a single direct magnitude-adjustment hop."""
    F = graph.filter_graph(empty_search_params, include_emission_factors=False)
    paths = identify_conversion_path(F, "kJ", "J")
    assert paths, "expected at least one path from kJ to J"
    assert all(p[0] == "kJ" and p[-1] == "J" for p in paths)


def test_missing_node_returns_empty(graph) -> None:
    paths = identify_conversion_path(graph.G, "definitely_not_a_unit", "J")
    assert paths == []


def test_convert_path_to_edge_tuples_single() -> None:
    result = convert_path_to_edge_tuples(["A", "B", "C"])
    assert result == [[("A", "B"), ("B", "C")]]


def test_convert_path_to_edge_tuples_multi() -> None:
    result = convert_path_to_edge_tuples([["A", "B"], ["A", "C", "D"]])
    assert result == [[("A", "B")], [("A", "C"), ("C", "D")]]


def test_convert_empty_path() -> None:
    assert convert_path_to_edge_tuples([]) == []
