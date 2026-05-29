---
type: class
module: unitgps.engine.graph
file: src/unitgps/engine/graph.py
lines: "16-165"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [engine, graph, class]
related:
  - "[[UnitGraph.filter_graph]]"
  - "[[UnitGraph.get_nodes_by_dimension]]"
  - "[[Unit graph]]"
  - "[[DataLoader]]"
  - "[[identify_conversion_path]]"
---

# UnitGraph

Wraps a `networkx.MultiDiGraph` of unit-to-unit conversions and provides the two engine entry points the rest of the code uses: [[UnitGraph.filter_graph|filter_graph]] for subgraph queries and [[UnitGraph.get_nodes_by_dimension|get_nodes_by_dimension]] for UI dimension grouping.

Conceptually this is the [[Unit graph]] made concrete in code.

## Construction

```python
def __init__(self, data: pd.DataFrame, node_attributes: dict) -> None:
    self.G = nx.from_pandas_edgelist(
        data,
        source='Denominator',
        target='Numerator',
        edge_attr=True,
        create_using=nx.MultiDiGraph,
    )
    nx.set_node_attributes(self.G, node_attributes)
```

| Param | Type | Description |
|-------|------|-------------|
| `data` | `pd.DataFrame` | Combined data, typically the output of [[DataLoader.load_data_library]] (with reciprocals already synthesized). |
| `node_attributes` | `dict` | `{unit: {Unit Dimension, Unit System, Color}}`, typically from [[DataLoader.get_units_attributes]]. |

### Why `Denominator → Numerator` direction?

Because *units cancel out*. If you start with `mmBTU` and traverse an edge whose label is `kg / mmBTU`, you end at `kg`. So the source side of the edge is the denominator and the target side is the numerator. This convention is the reason [[DataLoader.load_data_library|reciprocal synthesis]] swaps the two columns.

### Why `MultiDiGraph`?

- **Directed** because conversion edges are not symmetric — `kg → g` (×1000) is a different edge from `g → kg` (×0.001). Both useful, both stored separately.
- **Multi** because multiple parallel edges between the same `(source, target)` are normal — different agencies, different vintages, different fuel sub-types. See [[Ambiguous paths]].

### What's stored

- Every row of `data` becomes one edge. All 38 columns of the row are attached as edge attributes (via `edge_attr=True`).
- Every unit found in `node_attributes` is set as a node attribute.

After construction, `self.G` has ~200 nodes and ~6,000 edges for the canonical Data Library.

## Methods

| Method | Purpose |
|--------|---------|
| [[UnitGraph.filter_graph]] | Return a filtered subgraph honoring search parameters + temporal mode. The primary engine entry point. |
| [[UnitGraph.get_nodes_by_dimension]] | List all node names whose `Unit Dimension` attribute matches a given value. Used by the UI's dimension picker. |

## Lifecycle

A `UnitGraph` is built once per engine session and cached:

```python
@st.cache_resource(show_spinner='Loading Engine...')
def load_engine():
    loader = DataLoader(...)
    df = loader.load_data_library()
    node_attrs = loader.get_units_attributes(df)
    gwps = loader.load_gwps()
    return UnitGraph(df, node_attrs), gwps, df, node_attrs
```

The full graph is never mutated after construction. `filter_graph` returns a fresh subgraph on every call; pathfinding runs against the subgraph.

## Typical query sequence

```python
graph = UnitGraph(df, node_attrs)                                    # build once

F = graph.filter_graph(search_params, include_emission_factors=True) # per query
paths = identify_conversion_path(F, source='mmBTU', target='kg')     # per query
edges = convert_path_to_edge_tuples(paths)                           # per query
results = calculate_conversion_factor(F, edges, starting_value=1.0)  # per query
```

The wrappers [[determine_conversion]] and [[determine_ghg_emissions]] bundle these four steps so callers don't have to chain them by hand.

## See also

[[UnitGraph.filter_graph]] · [[UnitGraph.get_nodes_by_dimension]] · [[Unit graph]] · [[DataLoader]] · [[identify_conversion_path]]
