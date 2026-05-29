---
type: function
parent: "[[filters]]"
module: streamlit_app.filters
file: apps/streamlit_app/filters.py
lines: "154-168"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, filtering, ui-helper]
related:
  - "[[filters]]"
  - "[[DataLoader.get_units_attributes]]"
  - "[[UnitGraph.get_nodes_by_dimension]]"
  - "[[app]]"
---

# filters.get_units_for_dim

Return the list of units that belong to a given dimension, or — if no dimension is specified — every unit available under the current filters.

## Signature

```python
def get_units_for_dim(
    dim: str | None,
    available_units: list[str],
    available_dims: list[str],
    node_attrs: dict,
) -> list[str]
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `dim` | str \| None | Dimension to filter by, or None for "any". |
| `available_units` | `list[str]` | Currently reachable units after filters. |
| `available_dims` | `list[str]` | Currently reachable dimensions. |
| `node_attrs` | `dict` | The `{unit: {Unit Dimension, ...}}` map. |

## Output

A sorted `list[str]` of unit names appropriate for the Unit dropdown.

## Implementation

```python
def get_units_for_dim(dim, available_units, available_dims, node_attrs):
    if dim:
        valid = [u for u, attr in node_attrs.items()
                 if attr.get('Unit Dimension') == dim]
        return sorted(valid) if valid else available_units

    valid_set = set(available_units)
    for u, attr in node_attrs.items():
        if attr.get('Unit Dimension') in available_dims:
            valid_set.add(u)
    return sorted(valid_set)
```

## Two branches

1. **`dim` is set** — return every unit in `node_attrs` whose Dimension matches. Falls back to `available_units` (the filter-restricted set) if no match — which would happen if a Dimension is selected that the current filters exclude.
2. **`dim` is None** — return the union of `available_units` AND any unit whose Dimension is in `available_dims`. This is intentionally permissive: showing all theoretically reachable units when the user hasn't narrowed by Dimension.

## Why two views (this function vs. UnitGraph.get_nodes_by_dimension)

[[UnitGraph.get_nodes_by_dimension]] returns *every* unit of a dimension, regardless of filters. This function returns units that are *appropriate to show in the UI given the current filter context*. The two views serve different purposes — that's why the logic isn't shared.

## Usage

```python
# In the Source Unit selectbox:
s_opts = get_units_for_dim(source_dim, available_units, available_dims, node_attrs)
st.selectbox(f"Unit ({len(s_opts)})", options=s_opts, key='source_unit_sb', ...)
```

Note: today there's also `get_units_for_dim_local` defined inline in [[app]]. Cleanup item is to remove the local copy and import this one consistently.

## See also

[[filters]] · [[DataLoader.get_units_attributes]] · [[UnitGraph.get_nodes_by_dimension]] · [[app]]
