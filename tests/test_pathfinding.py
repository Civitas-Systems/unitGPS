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


def test_shortest_path_edges_picks_shortcut() -> None:
    """Edges on the unique shortest path are returned; longer detours excluded."""
    import networkx as nx
    from unitgps.engine import shortest_path_edges

    G = nx.DiGraph()
    G.add_edge("A", "B"); G.add_edge("B", "C"); G.add_edge("A", "C"); G.add_edge("C", "D")
    # A->C->D (len 2) beats A->B->C->D (len 3)
    assert shortest_path_edges(G, "A", "D") == {("A", "C"), ("C", "D")}


def test_shortest_path_edges_parallel_branches() -> None:
    """Two equal-length shortest paths both contribute their edges."""
    import networkx as nx
    from unitgps.engine import shortest_path_edges

    G = nx.DiGraph()
    G.add_edge("S", "X"); G.add_edge("X", "T"); G.add_edge("S", "Y"); G.add_edge("Y", "T")
    assert shortest_path_edges(G, "S", "T") == {("S", "X"), ("X", "T"), ("S", "Y"), ("Y", "T")}


def test_shortest_path_edges_no_path_or_missing() -> None:
    import networkx as nx
    from unitgps.engine import shortest_path_edges

    G = nx.DiGraph(); G.add_edge("A", "B"); G.add_node("Z")
    assert shortest_path_edges(G, "A", "Z") == set()
    assert shortest_path_edges(G, "missing", "B") == set()
