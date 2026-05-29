"""Conversion-factor calculation and structured audit reporting.

Each call returns a list of "AuditReport" dicts (one per shortest path) so
the UI can render the math, the pathway diagram, and the per-step source
attribution without doing any further engine work.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Sequence, Tuple

import networkx as nx


class AmbiguityError(Exception):
    """Raised when a conversion path has multiple unresolved parallel edges.

    Currently the calculator silently picks the first parallel edge and flags
    the result as ``is_ambiguous`` — this exception type is reserved for
    callers that want to opt into strict mode in the future.
    """


def format_sig_figs(value, sig_figs: int = 4) -> str:
    """Format a float with the given significant-figure count."""
    if value == 0:
        return "0"
    abs_val = abs(value)
    if abs_val < 1e-3 or abs_val >= 1e5:
        return f"{value:.{sig_figs - 1}e}"
    return f"{value:.{sig_figs}g}"


def is_valid_parameter(value) -> bool:
    """Return True if ``value`` is a non-empty, non-NaN parameter worth showing."""
    if value is None:
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    if isinstance(value, str):
        if not value.strip():
            return False
        if value.lower() == "nan":
            return False
    return True


def calculate_conversion_factor(
    G: nx.MultiDiGraph,
    shortest_paths_edges: Sequence,
    starting_value: float = 1.0,
    edge_picks: Dict[Tuple[str, str], int] | None = None,
) -> List[Dict[str, Any]]:
    """Multiply edge values along a path; return a list of AuditReport dicts.

    Each AuditReport contains:
      - ``route``: the full node sequence as a list
      - ``starting_value``: input value
      - ``conversion_factor``: product of all edge values along the path
      - ``ultimate_value``: ``starting_value * conversion_factor``
      - ``audit_steps``: per-step source/target/edge metadata
      - ``is_ambiguous``: True if any step had >1 parallel edge
      - ``ambiguous_details``: the subset of audit_steps that were ambiguous

    When parallel edges exist at a step, the engine picks edge 0 by default,
    flagging the path as ambiguous. Callers can override per-edge picks via
    ``edge_picks``: a dict mapping ``(source, target)`` -> edge index (0-based,
    referring to the order edges appear in ``G[u][v]``). Each audit step
    carries a ``chosen_edge_idx`` field so downstream renderers know which
    parallel option was used.
    """
    if not shortest_paths_edges:
        return None

    # Allow either a single path (list[tuple]) or many paths (list[list[tuple]])
    paths_to_process: List[List[Tuple[str, str]]] = list(shortest_paths_edges)
    if shortest_paths_edges and isinstance(shortest_paths_edges[0], tuple):
        paths_to_process = [list(shortest_paths_edges)]

    results: List[Dict[str, Any]] = []

    for path_edges in paths_to_process:
        if not path_edges:
            continue

        full_route = [path_edges[0][0]] + [edge[1] for edge in path_edges]

        path_values: List[float] = []
        audit_steps: List[Dict[str, Any]] = []
        path_ambiguity = False
        ambiguous_details: List[Dict[str, Any]] = []

        for step_num, (u, v) in enumerate(path_edges, 1):
            edges_at_step = G[u][v]
            edge_count = len(edges_at_step)
            step_values: List[float] = []

            if edge_count > 1:
                path_ambiguity = True

            step_details: Dict[str, Any] = {
                "step_num": step_num,
                "source": u,
                "target": v,
                "edges": [],
            }

            for k, edge_data in edges_at_step.items():
                val = edge_data.get("Value", 1.0)
                step_values.append(val)

                source_keys = [
                    "Agency",
                    "Dataset",
                    "Release Date",
                    "Version",
                    "Location in File",
                    "Updated",
                ]
                exclude_keys = {
                    "Value",
                    "Conversion",
                    "Operation",
                    "Source",
                    "Reference",
                    "Numerator",
                    "Denominator",
                    "Color",
                    "Weight",
                    "Numerator System",
                    "Denominator System",
                    "Numerator Dimension",
                    "Denominator Dimension",
                    "Set",
                    "System",
                }
                exclude_keys.update(source_keys)

                source_params = {
                    k: edge_data[k]
                    for k in source_keys
                    if k in edge_data and is_valid_parameter(edge_data[k])
                }
                general_params = {
                    kk: vv
                    for kk, vv in edge_data.items()
                    if kk not in exclude_keys and is_valid_parameter(vv)
                }

                step_details["edges"].append(
                    {
                        "key": k,
                        "value": val,
                        "set": edge_data.get("Set", edge_data.get("System")),
                        "parameters": general_params,
                        "source": source_params,
                    }
                )

            # Determine which parallel edge to use as the primary value.
            # Defaults to 0 (preserves legacy behaviour). edge_picks lets the
            # UI surface and persist a user choice for ambiguous steps.
            pick_idx = 0
            if edge_picks and (u, v) in edge_picks:
                requested = edge_picks[(u, v)]
                # Clamp defensively — a stale pick from a previous calc could
                # reference an index that no longer exists after filter changes.
                pick_idx = max(0, min(int(requested), edge_count - 1))
            step_details["chosen_edge_idx"] = pick_idx

            audit_steps.append(step_details)
            if edge_count > 1:
                ambiguous_details.append(step_details)

            primary_val = step_values[pick_idx]
            path_values.append(primary_val)

        conversion_factor = math.prod(path_values)
        ultimate_value = starting_value * conversion_factor

        results.append(
            {
                "route": full_route,
                "starting_value": starting_value,
                "conversion_factor": conversion_factor,
                "ultimate_value": ultimate_value,
                "audit_steps": audit_steps,
                "is_ambiguous": path_ambiguity,
                "ambiguous_details": ambiguous_details,
            }
        )

    return results
