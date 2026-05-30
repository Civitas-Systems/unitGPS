---
type: function
parent: "[[Unit graph]]"
module: unitgps.engine.pathfinding
file: src/unitgps/engine/pathfinding.py
lines: "89-128"
status: current
generation: Claude
last_updated: 2026-05-30
tags: [engine, pathfinding, graph, ghg]
related:
  - "[[identify_conversion_path]]"
  - "[[shortest_path_edges]]"
  - "[[determine_ghg_emissions]]"
  - "[[GHG emissions and GWP]]"
---

# shortest_paths_via_edge_set

Return the shortest `source → target` node paths that **traverse at least one edge accepted by a predicate**. This is a *constrained* shortest path: of all routes, keep only the shortest ones that are forced through a particular kind of edge.

## Signature

```python
def shortest_paths_via_edge_set(G, source, target, edge_filter) -> list[list[str]]
```

| Param | Type | Description |
|-------|------|-------------|
| `edge_filter` | `callable(u, v, data) -> bool` | Returns `True` for edges the path *must* be able to cross. |

## Why it exists — the GHG correctness rule

A GHG route is only meaningful if it passes through a **real emission-factor edge**. Without this constraint, the graph could route, say, `mmBTU → … → kg` through pure unit/fuel-mass conversions that happen to land on the same `kg` target node — producing a number that is *not* an emission. [[determine_ghg_emissions]] therefore calls this with `edge_filter = _is_emission_factor_edge`, guaranteeing every gas's mass is computed across an actual EF. See [[GHG emissions and GWP]].

## How it works (pseudocode)

```
dist_s = BFS distances from source
dist_t = BFS distances to target (on G.reverse())

best = inf; pivots = []
for each edge (u, v, data):
    if not edge_filter(u, v, data): continue
    if u reachable from source and v reaches target:
        total = dist_s[u] + 1 + dist_t[v]            # shortest path forced through (u,v)
        keep the minimal total; collect all pivot edges that tie at it

if no qualifying edge: return []

for each minimal pivot (a, b):
    full = shortest_path(source, a) + shortest_path(b, target)
    add full (deduped)
return paths
```

It finds the cheapest way to be *forced through* a qualifying edge, then reconstructs the actual node path(s) for each tied pivot. Cost: two BFS passes plus one path reconstruction per minimal pivot.

## Output

- A `list` of node paths (each a `list[str]`). Empty if a node is missing or no qualifying path exists — which the GHG panel surfaces as "no path found" for that gas.

## Edge cases

- Several pivot edges can tie at the minimal length → multiple paths returned (deduped by node sequence).
- A gas with no EF in the filtered graph → `[]` → that gas shows "no path found" while others may still compute.

## See also

[[identify_conversion_path]] · [[shortest_path_edges]] · [[determine_ghg_emissions]] · [[GHG emissions and GWP]]
