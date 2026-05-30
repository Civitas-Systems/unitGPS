"""Unit graph construction and filtering.

The graph treats units as nodes and conversions as directed edges. A
``MultiDiGraph`` is used because multiple parallel edges between the same
pair of units are common (e.g. several agencies' emission factors for the
same fuel→CO2 relationship).

Ported from Antigravity/engine/core.py (renamed for clarity — the file is
specifically about the unit graph, not "core" in any deeper sense).
"""

from __future__ import annotations

from typing import List

import networkx as nx
import pandas as pd


class UnitGraph:
    """Wraps a ``networkx.MultiDiGraph`` of unit-to-unit conversions."""

    def __init__(self, data: pd.DataFrame, node_attributes: dict) -> None:
        self.G = nx.from_pandas_edgelist(
            data,
            source="Denominator",
            target="Numerator",
            edge_attr=True,
            create_using=nx.MultiDiGraph,
        )
        nx.set_node_attributes(self.G, node_attributes)

    def filter_graph(
        self,
        search_parameters: dict,
        include_emission_factors: bool = False,
    ) -> nx.MultiDiGraph:
        """Return a filtered subgraph based on search parameters.

        Infrastructure (Unit Conversions, Magnitude Adjustments) always passes -
        it has no provenance and is needed to chain any multi-step path. Every
        other row must match each selected filter; a blank scope value is
        excluded (so an electricity-only column like eGRID drops fuel rows).
        Data Year treats a blank year as a wildcard.

        ``search_parameters['Data Year']`` may be:
          - a list (treated as ``mode='exact'``);
          - a dict ``{'mode': str, 'values': list}`` where mode is one of
            ``'all'``, ``'exact'``, ``'range'``, ``'recent_global'``,
            ``'recent_edge'``.
        """
        filtered_G = nx.MultiDiGraph()
        filtered_G.add_nodes_from(self.G.nodes(data=True))

        dy_param = search_parameters.get("Data Year")
        dy_mode = "all"
        dy_values: list = []
        if isinstance(dy_param, dict):
            dy_mode = dy_param.get("mode", "all")
            dy_values = dy_param.get("values", [])
        elif isinstance(dy_param, list):
            dy_mode = "exact"
            dy_values = dy_param

        temp_edges = []
        global_max_year = -float("inf")

        for u, v, key, attributes in self.G.edges(keys=True, data=True):
            row_set_raw = attributes.get("Set", attributes.get("System", ""))
            row_set_clean = str(row_set_raw).strip().lower()
            is_emission_factor = "emission factor" in row_set_clean

            if not include_emission_factors and is_emission_factor:
                continue

            # Infrastructure always passes; every other row must match each
            # selected filter. A blank scope value therefore EXCLUDES the row
            # (e.g. picking an eGRID region drops fuel rows, which are blank in
            # the eGRID column). Data Year is handled below and still wildcards
            # a blank year.
            is_infrastructure = attributes.get("Set") in (
                "Unit Conversion",
                "Magnitude Adjustment",
                "Unit Conversions",
            )
            match_found = True
            if not is_infrastructure:
                for param, search_val in search_parameters.items():
                    if param == "Data Year" or search_val is None:
                        continue
                    data_val = attributes.get(param)
                    if isinstance(search_val, list):
                        if data_val not in search_val:
                            match_found = False
                            break
                    elif search_val != data_val:
                        match_found = False
                        break

            if not match_found:
                continue

            # Data Year - a blank year is a wildcard, same as above.
            edge_year = attributes.get("Data Year")
            try:
                edge_year_val = (
                    float(edge_year)
                    if pd.notnull(edge_year) and str(edge_year).strip() != ""
                    else None
                )
            except (ValueError, TypeError):
                edge_year_val = None

            if dy_mode == "exact" and dy_values:
                if edge_year_val is not None and edge_year_val not in dy_values:
                    continue
            elif dy_mode == "range" and len(dy_values) == 2:
                if edge_year_val is not None and not (
                    dy_values[0] <= edge_year_val <= dy_values[1]
                ):
                    continue

            if edge_year_val is not None and edge_year_val > global_max_year:
                global_max_year = edge_year_val

            temp_edges.append((u, v, key, attributes, edge_year_val))

        # Second pass: relative Data Year modes
        if dy_mode == "recent_global" and global_max_year != -float("inf"):
            for u, v, key, attr, ey_val in temp_edges:
                if ey_val == global_max_year or ey_val is None:
                    filtered_G.add_edge(u, v, key=key, **attr)
        elif dy_mode == "recent_edge":
            edge_max_years: dict = {}
            for u, v, key, attr, ey_val in temp_edges:
                if ey_val is not None:
                    current_max = edge_max_years.get((u, v), -float("inf"))
                    if ey_val > current_max:
                        edge_max_years[(u, v)] = ey_val

            for u, v, key, attr, ey_val in temp_edges:
                if ey_val is None or ey_val == edge_max_years.get((u, v)):
                    filtered_G.add_edge(u, v, key=key, **attr)
        else:
            for u, v, key, attr, ey_val in temp_edges:
                filtered_G.add_edge(u, v, key=key, **attr)

        return filtered_G

    def get_nodes_by_dimension(self, dimension: str) -> List[str]:
        """Return all node names whose ``Unit Dimension`` attribute matches."""
        return [n for n, attr in self.G.nodes(data=True) if attr.get("Unit Dimension") == dimension]
