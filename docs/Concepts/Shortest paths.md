---
type: concept
status: current
generation: Claude
last_updated: 2026-05-20
tags: [concept, pathfinding, networkx]
related:
  - [[Unit graph]]
  - [[identify_conversion_path]]
  - [[calculate_conversion_factor]]
  - [[Ambiguous paths]]
---

# Shortest paths

A conversion in UnitGPS is the multiplication of edge values along the shortest path from source unit to target unit. **"Shortest" means fewest edges**, not lowest weight — every edge counts the same.

## The implementation

```python
nx.all_shortest_paths(G, source, target)
```

`all_shortest_paths` returns *every* path that ties for shortest length. Two important consequences:

1. **Multiple results are normal.** If there are five different 3-hop routes from mmBTU to kg CO₂e (one per agency, say), all five come back.
2. **They're not ranked.** The order networkx returns them in is implementation-dependent. The UI shows the first N up to `max_paths`; if the user wants a specific path, they need to narrow filters.

## Why fewest edges, not lowest weight?

Edge weights in UnitGPS are conversion factors (multiplicative). Asking for "lowest weight" would translate to "smallest product of factors" which is meaningless — the product depends on whether you're going from a small unit to a large one or vice versa, not on path quality.

Path *length* is the right minimization target because every extra hop is an opportunity to compound rounding error or introduce ambiguity. Fewer hops = a more direct, more trustworthy conversion.

## Multi-source ranking

When there are multiple shortest paths and the user wants exactly one, the current strategy is:

1. **Apply more filters** — narrow Agency, Data Year, etc. until only one path remains.
2. **Read the audit** — if multiple paths come back, the [[calculate_conversion_factor|audit report]] lets the user pick by inspecting which agencies / vintages each path uses.

A planned improvement is letting the user explicitly choose which path / which parallel edge to use; tracked in [[architecture#4. Differences from Antigravity]].

## Failure mode: no path

When source and target aren't connected in the filtered graph, [[identify_conversion_path]] returns `[]`. Common causes:

- **Filters too narrow** — e.g. asking for `mmBTU → kg` with `Source-Chemical Type=Anthracite` AND `Data Year=2008` when the EPA Anthracite EF has no 2008 vintage.
- **Physically impossible** — `kg of Anthracite → liters of gasoline` is a nonsensical unit conversion. The graph correctly reports no path.
- **Missing reciprocal** — for a Set the engine doesn't reciprocate (Unit Conversion, Magnitude Adjustment), the source data must include the direction you're asking about.

## See also

[[Unit graph]] · [[identify_conversion_path]] · [[calculate_conversion_factor]] · [[Ambiguous paths]]
