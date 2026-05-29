---
type: function
module: unitgps.engine.pathfinding
file: src/unitgps/engine/pathfinding.py
lines: "24-46"
status: current
generation: Claude
last_invariant: 2026-05-21
last_updated: 2026-05-21
tags: [engine, pathfinding]
related:
  - "[[convert_path_to_edge_tuples]]"
  - "[[UnitGraph.filter_graph]]"
  - "[[Shortest paths]]"
  - "[[Ambiguous paths]]"
  - "[[determine_conversion]]"
---

# identify_conversion_path

Find every shortest path between a source node and a target node in a (typically filtered) graph. The thin wrapper around `networkx.all_shortest_paths` that handles missing nodes gracefully.

## Signature

```python
def identify_conversion_path(G: nx.MultiDiGraph, source: str, target: str) -> List[NodePath]

NodePath = List[str]
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `G` | `nx.MultiDiGraph` | The graph to search. Almost always the output of [[UnitGraph.filter_graph]], not the full graph. |
| `source` | `str` | Source node name (e.g. `'mmBTU'`). |
| `target` | `str` | Target node name (e.g. `'kg'`). |

## Output

A `list[list[str]]` — one inner list per shortest path, each inner list being the sequence of node names from source to target. Always returns a list (possibly empty); never returns `None`.

```python
[['mmBTU', 'kg']]                          # one direct edge
[['mmBTU', 'BTU', 'J', 'kJ']]              # multi-hop, single path
[['A', 'B', 'C'], ['A', 'D', 'C']]         # two paths tied for shortest
[]                                          # no path, or node missing
```

## How it works (pseudocode)

```
1. If source or target isn't in G, log and return [].
2. If no path exists (nx.has_path is False), log and return [].
3. Otherwise return list(nx.all_shortest_paths(G, source, target)).
```

## Line-by-line

```python
if not (G.has_node(source) and G.has_node(target)):
    logger.debug("identify_conversion_path: missing node — source=%r target=%r", source, target)
    return []
```

The missing-node guard is necessary because `nx.has_path` raises `NodeNotFound` if either endpoint isn't in the graph. By short-circuiting we get a uniform "no path" return value regardless of whether the failure is "nodes exist but unconnected" or "nodes don't exist."

> **Cleanup note.** The original Antigravity version did NOT have this guard — it called `nx.has_path` directly and crashed on missing nodes. Adding the guard was part of the Claude port.

```python
if nx.has_path(G, source, target):
    paths = list(nx.all_shortest_paths(G, source, target))
    logger.debug("identify_conversion_path: %d shortest path(s) from %r to %r", len(paths), source, target)
    return paths
```

`all_shortest_paths` is a generator; `list(...)` realizes it. For a typical 1–3 hop conversion in the unit graph, the number of paths is small (1–10). Pathologically wide graphs could return thousands, but the UI caps display at `max_paths` (default 5).

```python
logger.debug("identify_conversion_path: no path %r → %r in graph of %d nodes", source, target, len(G.nodes))
return []
```

Final fallback — nodes exist but are unconnected in the current filter view.

## Why "shortest"?

See [[Shortest paths]] for the design rationale. TL;DR: fewest edges = least opportunity for compounding rounding error or accumulated ambiguity.

## Why "all"?

There's no principled way to rank tied shortest paths without more information. Returning all of them lets the UI either show them all (`max_paths='All'`) or pick a default and let the user narrow filters to disambiguate.

## Failure modes

- **Missing node** → `[]` (logged at DEBUG).
- **No path in filtered subgraph** → `[]` (logged at DEBUG).
- **Cyclic edges of length 0** — not possible in a unit graph (no self-loops in the source data).

## Usage

```python
from unitgps.engine import identify_conversion_path, UnitGraph

F = graph.filter_graph({...})
paths = identify_conversion_path(F, 'mmBTU', 'kg')

if not paths:
    print('No path found.')
else:
    print(f'{len(paths)} path(s) found:')
    for p in paths:
        print(' -> '.join(p))
```

Typically you don't call this directly — [[determine_conversion]] and [[determine_ghg_emissions]] chain it with `filter_graph` and `calculate_conversion_factor` for you.

## Cleanup history

The Antigravity version of this function wrote diagnostic info to a hard-coded file path (`C:\Users\davel\.gemini\antigravity\brain\<uuid>\scratch\debug_pathfinding.txt`). The Claude port replaced those with `logger.debug()` calls so the diagnostics still exist but go through the standard logging system and don't break when run on any machine other than the original.

## See also

[[convert_path_to_edge_tuples]] · [[UnitGraph.filter_graph]] · [[Shortest paths]] · [[Ambiguous paths]] · [[calculate_conversion_factor]]
