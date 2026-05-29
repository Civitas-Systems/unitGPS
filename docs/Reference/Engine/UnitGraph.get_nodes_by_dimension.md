---
type: function
parent: "[[UnitGraph]]"
module: unitgps.engine.graph
file: src/unitgps/engine/graph.py
lines: "164-165"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [engine, graph, ui-helper]
related:
  - "[[UnitGraph]]"
  - "[[DataLoader.get_units_attributes]]"
  - "[[Glossary#Dimension]]"
---

# UnitGraph.get_nodes_by_dimension

Return every node name whose `Unit Dimension` attribute matches a given value. Two-line helper used by the UI's dimension-based unit pickers.

## Signature

```python
def get_nodes_by_dimension(self, dimension: str) -> List[str]
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `dimension` | `str` | One of the Dimension values (`'Energy'`, `'Weight'`, `'Length'`, `'Volume'`, `'Time'`, `'Power'`, `'Area'`, `'Logistics'`). |

## Output

A `list[str]` of node names. Order is whatever `self.G.nodes(data=True)` yields — currently insertion order from when [[UnitGraph#Construction]] built the graph.

## How it works

```python
return [n for n, attr in self.G.nodes(data=True) if attr.get('Unit Dimension') == dimension]
```

Single list comprehension. `nodes(data=True)` yields `(node_name, attribute_dict)` tuples; the filter keeps only nodes whose `Unit Dimension` attribute matches.

## Edge cases

- **Dimension name doesn't exist in the graph** → returns `[]`.
- **A node without a `Unit Dimension` attribute** → falls through to `None != dimension`, so it's excluded. Defensive default behavior.
- **Whitespace mismatch** — `'energy'` (lowercase) returns `[]` because the comparison is exact. The UI populates this from the same `node_attrs` dict, so casing is always consistent in practice.

## Usage

```python
graph.get_nodes_by_dimension('Energy')
# ['J', 'kJ', 'MJ', 'GJ', 'BTU', 'mmBTU', 'Cal', 'kWh', 'MWh', 'GWh', 'therm', ...]

graph.get_nodes_by_dimension('Weight')
# ['g', 'kg', 'tonne', 'lb', 'oz', 'kt', 'Mt', 'Gt', 'ton (US)', 'ton (UK)', ...]
```

In the Streamlit UI, the Source Unit dropdown is populated by calling this method (indirectly via `get_units_for_dim_local`) whenever the user changes the Source Dimension.

## Why not `filter_graph`?

[[UnitGraph.filter_graph]] is for *edge* filtering; this is for *node* enumeration. The UI needs the latter to populate unit pickers regardless of what edges currently survive any filter.

## See also

[[UnitGraph]] · [[DataLoader.get_units_attributes]] · [[Glossary#Dimension]]
