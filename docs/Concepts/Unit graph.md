---
type: concept
status: current
generation: Claude
last_updated: 2026-05-20
tags: [concept, graph, foundational]
related:
  - [[Reciprocal edges]]
  - [[Shortest paths]]
  - [[Ambiguous paths]]
  - [[UnitGraph]]
---

# Unit graph

The central abstraction in UnitGPS. **Units are nodes; conversions are directed edges.** Computing a conversion is finding a path of edges from the source unit to the target unit and multiplying the edge values together.

## Why a graph?

A spreadsheet of conversions answers "given A, what is B?" only when there is a direct row for A→B. A graph answers it for *any reachable B*, even if the route passes through three intermediate units. This is what makes UnitGPS qualitatively different from a hard-coded converter:

| Question | Spreadsheet | UnitGPS graph |
|----------|-------------|---------------|
| 1 BTU → J? | Direct lookup | 1-hop path |
| 1 BTU → cal? | Two lookups | 2-hop path (no direct row needed) |
| 1 mmBTU of Anthracite → kg CO₂e? | No row | Multi-hop path through magnitude + emission factor + GWP |
| 100 gal of Diesel → kg CO₂e in Oregon, 2023? | Many lookups, manual chain | Single shortest-path query |

The cost is that we have to think about graph properties (reachability, parallel edges, filter-induced disconnections) instead of just "is the row there?".

## The data structure

UnitGPS uses `networkx.MultiDiGraph`:

- **Directed** because *kg per gram* and *gram per kg* are different edges, both useful.
- **Multi** because two agencies often publish different values for the same conversion (e.g. two EFs for "kg CO₂ per mmBTU Anthracite"). Both edges live in the graph; whichever survives filtering is used. See [[Ambiguous paths]].

```
            ┌──────────────────────────────────┐
            │ MultiDiGraph                     │
            │                                  │
            │  J ──×1000──> kJ                 │
            │  J <──×0.001── kJ                │
            │                                  │
            │  mmBTU ─×103.69(EPA)─> kg(CO₂)   │
            │  mmBTU ─×95.52(EPA, mix)─> kg    │  ← parallel edges
            │  mmBTU ─×0.009644──> kg          │  ← reciprocal (see below)
            │                                  │
            └──────────────────────────────────┘
```

## Node and edge data

**Nodes** have these attributes (set by [[DataLoader.get_units_attributes]]):

| Attribute | Example | Used for |
|-----------|---------|----------|
| `Unit Dimension` | `Energy`, `Weight` | UI grouping; dimension-locked target |
| `Unit System` | `SI`, `imperial` | UI filtering |
| `Color` | `pink` (Energy) | Graph visualization (planned) |

**Edges** carry the full Data Library row as edge attributes. Every column from the xlsx — `Value`, `Set`, `Agency`, `Dataset`, `Data Year`, `Source-Chemical Type`, `GHG`, etc. — is preserved so filters can reach into them. See [[Data Library schema]].

## Construction

`Denominator` is the source node, `Numerator` is the target. This is the inverse of how you might write a fraction (`kg/mmBTU` → `mmBTU → kg`) but it follows the principle that *units cancel out*: starting with mmBTU and multiplying by `kg/mmBTU` gives kg.

```python
G = nx.from_pandas_edgelist(
    data,
    source='Denominator',
    target='Numerator',
    edge_attr=True,                # carry every column as edge data
    create_using=nx.MultiDiGraph,
)
```

See [[UnitGraph]] for the wrapper class.

## Five kinds of edges

The `Set` column tags each edge by what kind of conversion it is. Each kind has different filtering rules:

| Set | Count (raw) | Filtering rule |
|-----|-------------|----------------|
| `Unit Conversion` | 294 | Always kept. Never reciprocated (already bidirectional in source). |
| `Magnitude Adjustment` | 192 | Always kept. Never reciprocated. |
| `Emission Factors` | 3,024 | Excluded by default; opt in via `include_emission_factors=True`. Reciprocated. |
| `Chemical Properties` | 63 | Always kept, but ignore non-chemical filters. Reciprocated. |
| `Global Warming Potentials` | 62 | Unused in the graph (GWPs come from the separate IPCC file). |

After reciprocal synthesis, the combined row count grows from 3,635 to 6,056. See [[Reciprocal edges]] for why and which kinds get reciprocated.

## What "filter" means

The graph is never modified after construction. Every query first calls [[UnitGraph.filter_graph]] which returns a **new subgraph** containing only the edges that match the user's filters. Pathfinding then runs against the subgraph, not the full graph. This is what lets the UI offer Agency / Country / Data Year filters without rebuilding anything.

## Failure modes

- **No path exists in the filtered subgraph.** Either the source/target aren't connected (e.g. asking for `kg of Anthracite` → `gallons of diesel` makes no physical sense) or the filters eliminated every route. [[identify_conversion_path]] returns `[]`.
- **Multiple shortest paths.** All are returned. The UI shows the top N (capped by Max Paths).
- **Parallel edges on a path step.** Engine picks the first edge, flags `is_ambiguous=True`. See [[Ambiguous paths]].

## See also

[[UnitGraph]] · [[UnitGraph.filter_graph]] · [[Reciprocal edges]] · [[Shortest paths]] · [[Data Library schema]]
