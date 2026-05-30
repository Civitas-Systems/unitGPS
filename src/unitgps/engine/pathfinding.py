"""Shortest-path discovery between units.

Cleanup vs. Antigravity: the two hard-coded debug file writes to
``C:\\Users\\davel\\.gemini\\antigravity\\brain\\...\\scratch\\*.txt`` are
gone. Diagnostics now go through the stdlib ``logging`` module — callers
that want to see them can configure their own handler.
"""

from __future__ import annotations

import logging
from typing import List, Sequence, Tuple, Union

import networkx as nx

logger = logging.getLogger(__name__)

NodePath = List[str]
EdgeTuple = Tuple[str, str]


def identify_conversion_path(G: nx.MultiDiGraph, source: str, target: str) -> List[NodePath]:
    """Find all shortest paths between a source and a target node.

    Returns an empty list if either node is missing or no path exists.
    """
    if not (G.has_node(source) and G.has_node(target)):
        logger.debug("identify_conversion_path: missing node — source=%r target=%r", source, target)
        return []

    if nx.has_path(G, source, target):
        paths = list(nx.all_shortest_paths(G, source, target))
        logger.debug(
            "identify_conversion_path: %d shortest path(s) from %r to %r", len(paths), source, target
        )
        return paths

    logger.debug(
        "identify_conversion_path: no path %r → %r in graph of %d nodes",
        source,
        target,
        len(G.nodes),
    )
    return []


def convert_path_to_edge_tuples(
    path_nodes: Union[NodePath, Sequence[NodePath]],
) -> List[List[EdgeTuple]]:
    """Convert a list of nodes (or list-of-lists) into sequential edge tuples.

    A single path ``['A', 'B', 'C']`` returns ``[[('A','B'), ('B','C')]]`` —
    always wrapped one level deep so callers can iterate uniformly.
    """
    if not path_nodes:
        return []

    if isinstance(path_nodes[0], list):
        return [list(zip(p, p[1:])) for p in path_nodes]

    return [list(zip(path_nodes, path_nodes[1:]))]


def shortest_path_edges(G, source, target):
    """Return the set of ``(u, v)`` edges that lie on SOME shortest path from
    ``source`` to ``target``.

    Two BFS passes (forward distances from ``source``, reverse distances to
    ``target``): an edge ``(u, v)`` is on a shortest path iff
    ``dist(source, u) + 1 + dist(v, target) == dist(source, target)``. Cheap —
    O(V + E) — and works on any directed graph; parallel edges collapse since
    the result is a set of node pairs. Empty set if a node is missing or there
    is no path.
    """
    if not (G.has_node(source) and G.has_node(target)):
        return set()
    dist_from = nx.single_source_shortest_path_length(G, source)
    if target not in dist_from:
        return set()
    dist_to = nx.single_source_shortest_path_length(G.reverse(copy=False), target)
    total = dist_from[target]
    return {
        (u, v)
        for u, v in G.edges()
        if u in dist_from and v in dist_to and dist_from[u] + 1 + dist_to[v] == total
    }
