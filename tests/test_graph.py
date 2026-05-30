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


# --- The single filter rule (2026-05-30 rewrite): infrastructure always passes;
#     every other edge strictly matches each filter (blank EXCLUDES); a blank
#     Data Year is a wildcard. ---

INFRA_SETS = ("Unit Conversion", "Unit Conversions", "Magnitude Adjustment")


def test_filter_graph_infrastructure_always_passes(graph, empty_search_params) -> None:
    """A filter matching no provenance still keeps infrastructure edges, and ONLY
    those — no emission-factor/chemical edge sneaks past a non-matching filter."""
    params = dict(empty_search_params)
    params["Agency"] = ["NO_SUCH_AGENCY_XYZ"]
    F = graph.filter_graph(params, include_emission_factors=True)
    sets_seen = {d.get("Set") for _, _, d in F.edges(data=True)}
    assert sets_seen & set(INFRA_SETS), "infrastructure was dropped"
    non_infra = [d for _, _, d in F.edges(data=True) if d.get("Set") not in INFRA_SETS]
    assert non_infra == [], "a provenance edge wrongly survived a non-matching Agency filter"


def test_filter_graph_blank_value_excludes(graph, empty_search_params) -> None:
    """Strict match: a provenance edge that is blank in the filtered column is
    excluded (the old Chemical-Properties carve-out is gone)."""
    params = dict(empty_search_params)
    params["Source-Chemical Type"] = ["Anthracite"]
    F = graph.filter_graph(params, include_emission_factors=True)
    for _, _, d in F.edges(data=True):
        if d.get("Set") in INFRA_SETS:
            continue  # infrastructure is exempt
        val = d.get("Source-Chemical Type")
        assert val is not None and str(val).strip() != "", "a blank-valued edge slipped a strict filter"


def test_filter_graph_blank_year_is_wildcard(graph) -> None:
    """An edge with no Data Year survives an exact-year filter, so infrastructure
    (which carries no year) is never dropped by a temporal filter."""
    params = {"Data Year": {"mode": "exact", "values": [1901]}}  # matches no real vintage
    F = graph.filter_graph(params, include_emission_factors=False)
    sets_seen = {d.get("Set") for _, _, d in F.edges(data=True)}
    assert "Unit Conversion" in sets_seen, "blank-year infrastructure was dropped by a year filter"


def test_filter_recent_global_mode(graph) -> None:
    F = graph.filter_graph({"Data Year": {"mode": "recent_global", "values": []}},
                           include_emission_factors=True)
    assert F.number_of_edges() > 0


def test_filter_recent_edge_mode(graph) -> None:
    F = graph.filter_graph({"Data Year": {"mode": "recent_edge", "values": []}},
                           include_emission_factors=True)
    assert F.number_of_edges() > 0


def test_filter_range_mode(graph) -> None:
    F = graph.filter_graph({"Data Year": {"mode": "range", "values": [2010.0, 2024.0]}},
                           include_emission_factors=True)
    assert F.number_of_edges() > 0
    # infrastructure (no Data Year) survives a range filter as a wildcard
    sets = {d.get("Set") for _, _, d in F.edges(data=True)}
    assert "Unit Conversion" in sets
