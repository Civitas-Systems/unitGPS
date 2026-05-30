---
type: function
parent: "[[Unit graph]]"
module: unitgps.engine.pathfinding
file: src/unitgps/engine/pathfinding.py
lines: "64-86"
status: current
generation: Claude
last_updated: 2026-05-30
tags: [engine, pathfinding, graph]
related:
  - "[[identify_conversion_path]]"
  - "[[shortest_paths_via_edge_set]]"
  - "[[Shortest paths]]"
  - "[[Pathway-scoped filters]]"
---

# shortest_path_edges

Return the **set of `(u, v)` node pairs that lie on at least one shortest path** from `source` to `target`. Unlike [[identify_conversion_path]] (which returns whole node paths), this returns just the union of edges that any shortest path could use — handy when you care about reachability/membership rather than enumerating routes.

## Signature

```python
def shortest_path_edges(G, source, target) -> set[tuple[str, str]]
```

## How it works

Two breadth-first passes, then a membership test:

```
dist_from = BFS distances from source        (single_source_shortest_path_length)
dist_to   = BFS distances to target          (same, on G.reverse())
total     = dist_from[target]                # length of a shortest path

edge (u, v) is on SOME shortest path  iff
    dist_from[u] + 1 + dist_to[v] == total
```

An edge is "on a shortest path" exactly when going `source → u`, crossing `u→v`, then `v → target` costs no more than the shortest path overall. Parallel `MultiDiGraph` edges collapse automatically because the result is a set of node pairs.

## Output

- A `set` of `(u, v)` tuples. Empty if `source`/`target` is missing or there's no path.

## Why it exists

Cheap (`O(V + E)`) reachability primitive. It underpins the dimension-level reachability used by [[Pathway-scoped filters]] (which scopes filter *options* to the source→target pathway) and is a building block alongside [[shortest_paths_via_edge_set]].

## Edge cases

- Missing node → `set()`.
- `target` unreachable from `source` → `set()` (the `target not in dist_from` guard).

## See also

[[identify_conversion_path]] · [[shortest_paths_via_edge_set]] · [[Shortest paths]] · [[Pathway-scoped filters]]
