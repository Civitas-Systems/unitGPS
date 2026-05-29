---
type: function
parent: "[[UnitGraph]]"
module: unitgps.engine.graph
file: src/unitgps/engine/graph.py
lines: "30-155"
status: current
generation: Claude
last_updated: 2026-05-20
tags: [engine, graph, filtering, complex]
related:
  - "[[UnitGraph]]"
  - "[[Unit graph]]"
  - "[[Temporal scope]]"
  - "[[Reciprocal edges]]"
  - "[[Ambiguous paths]]"
  - "[[determine_conversion]]"
  - "[[determine_ghg_emissions]]"
---

# UnitGraph.filter_graph

Return a new `MultiDiGraph` containing only the edges that match the caller's filters. This is the single most important function in the engine — pathfinding never runs against the full graph; it always runs against a `filter_graph` output. Every search the user does in the UI calls this with a different `search_parameters` dict.

## Signature

```python
def filter_graph(
    self,
    search_parameters: dict,
    include_emission_factors: bool = False,
) -> nx.MultiDiGraph
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `search_parameters` | `dict` | Column-name → value (or list of values) mapping. A special key `"Data Year"` may instead be a `{'mode': str, 'values': list}` dict. See [[#Special keys in search_parameters]]. |
| `include_emission_factors` | `bool` | When `False` (default), edges whose `Set` contains "emission factor" are stripped out. [[determine_conversion]] passes `False`; [[determine_ghg_emissions]] passes `True`. |

### Special keys in search_parameters

- **`"Data Year"`** — three accepted shapes:
  - Omitted or `None` → mode `'all'`, no temporal filtering.
  - A bare list of years like `[2020, 2022]` → mode `'exact'`.
  - A dict `{'mode': 'recent_global', 'values': []}` → explicit mode. Modes: `all`, `exact`, `range`, `recent_global`, `recent_edge`. See [[Temporal scope]].
- **Any other column name** — single value or list of values. List members are matched with `in`; a single value is matched with `==`.
- **`None` values** are skipped (treated as "no filter on this column").

## Output

A fresh `nx.MultiDiGraph` containing:

- **Every node** from `self.G`, with all attributes preserved. This is intentional — the UI's unit pickers want to show every possible target unit, even ones that have no surviving edges under the current filter.
- **A subset of edges** based on the filter rules below.

The returned graph is independent of `self.G`; mutating it doesn't affect future calls.

## How it works (pseudocode)

```
filtered_G = new empty MultiDiGraph
add every node from self.G to filtered_G (with attributes)

dy_mode, dy_values = parse search_parameters['Data Year']

temp_edges = []          # surviving edges, with their parsed year
global_max_year = -∞

# ─── Pass 1: column + per-edge temporal filtering ───
for each edge (u, v, key, attrs) in self.G:
    if it's an Emission Factor and include_emission_factors is False:
        skip it

    is_unit_conv  = attrs['Set'] in static-conversion sets
    is_chem_prop  = attrs['Set'] == 'Chemical Properties'

    # Column filters
    match = True
    for each (column, value) in search_parameters (except 'Data Year'):
        if value is None: continue
        if is_chem_prop and column is non-chemical: continue   # carve-out
        if attrs[column] not in value (or != value): match = False; break
    if not match and not is_unit_conv:
        skip it                                                # exempt static

    # Per-edge temporal filter (only for 'exact' and 'range' modes)
    edge_year = parse_float(attrs['Data Year'])
    if dy_mode == 'exact' and edge_year not in dy_values and edge_year is not None:
        if not is_unit_conv: skip it
    if dy_mode == 'range' and edge_year is outside [dy_values[0], dy_values[1]]:
        if not is_unit_conv and edge_year is not None: skip it

    if edge_year > global_max_year: global_max_year = edge_year
    temp_edges.append((u, v, key, attrs, edge_year))

# ─── Pass 2: relative-temporal filtering ───
if dy_mode == 'recent_global':
    for each (u, v, key, attrs, ey) in temp_edges:
        if ey == global_max_year or ey is None:
            emit edge
elif dy_mode == 'recent_edge':
    edge_max_years = {}
    for each (u, v, key, attrs, ey) in temp_edges:
        edge_max_years[(u, v)] = max(edge_max_years.get((u,v), -∞), ey if ey is not None else -∞)
    for each (u, v, key, attrs, ey) in temp_edges:
        if ey is None or ey == edge_max_years[(u, v)]:
            emit edge
else:
    emit every temp_edge unchanged

return filtered_G
```

## The three rule layers

Three orthogonal rule sets stack on top of each other:

1. **Set-based admission** (immediate skip):
   - Emission Factors are skipped unless `include_emission_factors=True`.
2. **Column filters** (per-edge):
   - Each non-None entry in `search_parameters` must match the edge's attribute value.
   - Two carve-outs:
     - **Unit Conversion / Magnitude Adjustment edges bypass column filters entirely.** They're treated as static infrastructure — they exist independent of agency/year/etc. and should remain reachable.
     - **Chemical Properties edges ignore non-chemical filter columns.** A density edge between `kg` and `L` is relevant whether or not the user filtered by `Agency`.
3. **Temporal filters** (per-edge for `exact`/`range`, two-pass for `recent_*`):
   - Edges with no Data Year always survive (interpreted as "not time-varying").
   - Static conversions always survive (same exemption as column filters).
   - For `recent_global` and `recent_edge`, a second pass is required because the answer depends on the global or per-pair maximum year.

The interactions matter: a Chemical Properties edge with `Data Year = NaN` will survive any combination of Agency + Year filters because both layers have carve-outs that catch it.

## Line-by-line — the column-filter loop

This is the part most likely to confuse on first read. Annotated:

```python
match_found = True
for param, search_val in search_parameters.items():
    if param == 'Data Year' or search_val is None:
        continue                                          # handled separately / no-op

    if is_chemical_property and param not in [
        'Source-Chemical Category', 'Source-Chemical Type',
        'Chemical1', 'Chemical2', 'Property'
    ]:
        continue                                          # the carve-out

    data_val = attributes.get(param)
    if isinstance(search_val, list):
        if data_val not in search_val:
            match_found = False
            break
    else:
        if search_val != data_val:
            match_found = False
            break

if not match_found and not is_unit_conversion:
    continue                                              # the static-conversion exemption
```

The two `continue`s are doing very different things:

- The inner `continue` (mid-loop) says "this filter doesn't apply to this edge type — keep checking the others."
- The outer `continue` (after loop) says "this edge failed at least one filter and isn't a static conversion — skip it entirely."

The static-conversion exemption is *after* the loop, not inside it, because we don't want to short-circuit and miss the chance for the loop to find a real mismatch. Static conversions still go through the loop; their results are ignored.

## Edge cases worth knowing

- **Empty filter dict** → returns a graph with every edge that's eligible by Set (drops EFs by default; keeps everything else).
- **Filter that matches no edges** → returns a graph with all nodes but only Unit Conversion + Magnitude Adjustment edges (those survive every filter).
- **Data Year as a string** vs. number — `pd.notnull` plus the `float()` cast handles both. `'2023'`, `2023`, `2023.0` all resolve to `2023.0`.
- **`recent_global` with no surviving timed edges** — `global_max_year` stays at `-∞`, the `if dy_mode == 'recent_global' and global_max_year != -inf` guard catches this and falls through to the "emit everything" branch, so the call doesn't accidentally return an empty graph.

## Usage

```python
# All EPA emission factors from 2023, plus all unit conversions
F = graph.filter_graph(
    {
        'Agency': ['EPA'],
        'Data Year': {'mode': 'exact', 'values': [2023]},
    },
    include_emission_factors=True,
)

# Most recent vintage per (source, target) pair, anthracite only
F = graph.filter_graph(
    {
        'Source-Chemical Type': ['Anthracite'],
        'Data Year': {'mode': 'recent_edge', 'values': []},
    },
    include_emission_factors=True,
)

# Pure unit-conversion graph — no EFs, no temporal restriction
F = graph.filter_graph({'Data Year': {'mode': 'all', 'values': []}})
```

## Performance notes

- Single pass over `self.G.edges()` plus an optional second pass — both `O(E)`. For E ≈ 5,500 this completes in single-digit milliseconds.
- The graph is rebuilt from scratch on every call. There's no memoization. Streamlit's `@st.cache_resource` caches the *engine* (the full graph and the `UnitGraph` wrapper), but not the filter output — fine because filter parameters change with every UI interaction.

## Cleanup items

- Same filter rules are encoded twice: here AND in [[filters|apply_db_and_temporal_filters]] in the Streamlit app, which computes live row counts before pathfinding. Both files need to be kept in sync by hand. Tracked in [[architecture#4. Differences from Antigravity]].
- The `is_chemical_property and param not in [...]` check uses a literal list inline. Extract to a module-level `CHEMICAL_FILTER_COLUMNS` constant so the rule is named.

## See also

[[UnitGraph]] · [[Unit graph]] · [[Temporal scope]] · [[Reciprocal edges]] · [[Ambiguous paths]] · [[determine_conversion]] · [[determine_ghg_emissions]]
