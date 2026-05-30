---
type: function
parent: "[[filters]]"
module: streamlit_app.filters
file: apps/streamlit_app/filters.py
status: current
generation: Claude
last_updated: 2026-05-30
tags: [streamlit, filters, reachability]
related: ["[[Pathway-scoped filters]]", "[[shortest_path_edges]]"]
---

# filters.dimension_reach

`(reachable_from_source, can_reach_target)` dimension sets on the dimension-reduced graph
(`dimension_digraph` + `networkx.descendants` / `ancestors`). Each is `None` when its
dimension is unset (no constraint), else a set including the dimension itself.

```python
def dimension_reach(graph_df, node_attrs, source_dim, target_dim) -> tuple[set|None, set|None]
```

Powers the **Source/Target dimension & unit pickers**: the target only offers dimensions
a source can reach (Area → Area only; Energy → Weight when an emission-factor path is in
the active modules), and under GHG (target = Weight) the source narrows to dimensions
that reach Weight. Computed on the active-module frame so enabling/disabling modules
changes reachability. See [[Pathway-scoped filters]].
