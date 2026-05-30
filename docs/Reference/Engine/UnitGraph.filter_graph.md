---
type: function
parent: "[[UnitGraph]]"
module: unitgps.engine.graph
file: src/unitgps/engine/graph.py
lines: "33-148"
status: current
generation: Claude
last_updated: 2026-05-30
tags: [engine, graph, filtering, complex]
related:
  - "[[UnitGraph]]"
  - "[[Unit graph]]"
  - "[[Temporal scope]]"
  - "[[Pathway-scoped filters]]"
  - "[[determine_conversion]]"
  - "[[determine_ghg_emissions]]"
---

# UnitGraph.filter_graph

Return a new `MultiDiGraph` containing only the edges that match the caller's filters. This is the single most important function in the engine — pathfinding never runs against the full graph; it always runs against a `filter_graph` output. Every search the user does in the UI calls this with a different `search_parameters` dict.

> **2026-05-30 rewrite.** The historical "three rule layers" (a Unit-Conversion exemption *and* a separate Chemical-Properties carve-out, applied per filter rule) were replaced by **one** rule. If you read an older copy of this page that talked about a "Chemical Properties carve-out", it no longer exists. See [[CHANGELOG]].

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
| `search_parameters` | `dict` | Column-name → value (or list of values) mapping. The special key `"Data Year"` may instead be a `{'mode': str, 'values': list}` dict. See [[#Special keys]]. |
| `include_emission_factors` | `bool` | When `False` (default), edges whose `Set` contains "emission factor" are stripped. [[determine_conversion]] passes `False`; [[determine_ghg_emissions]] passes `True`. |

### Special keys

- **`"Data Year"`** — three accepted shapes:
  - Omitted / `None` → mode `'all'`, no temporal filtering.
  - A bare list like `[2020, 2022]` → mode `'exact'`.
  - A dict `{'mode': ..., 'values': [...]}`. Modes: `all`, `exact`, `range`, `recent_global`, `recent_edge`. See [[Temporal scope]].
- **Any other column name** — a single value or a list of values. A list matches with `in`; a single value matches with `==`.
- **`None` values** are skipped (no filter on that column).

## Output

A fresh `nx.MultiDiGraph` containing:

- **Every node** from `self.G`, attributes preserved. Intentional — the UI's unit pickers want to show every possible target unit even when it has no surviving edges under the current filter.
- **A subset of edges** per the rules below.

The returned graph is independent of `self.G`; mutating it doesn't affect future calls.

## The one rule

There is exactly **one** admission rule, plus the orthogonal Data-Year handling:

1. **Infrastructure always passes.** An edge whose `Set` is one of `Unit Conversion`, `Unit Conversions`, or `Magnitude Adjustment` is *always* kept. These have no provenance (no agency/year/scope) and are the connective tissue every multi-step path needs.
2. **Every other edge must match each selected filter, strictly.** For each non-`None` entry in `search_parameters` (except `Data Year`), the edge's attribute must equal the value (or be `in` the list). A **blank/missing attribute is a non-match**, so it is excluded. This is what makes provenance filters *partition* the data: pick an eGRID region and fuel rows (blank in the eGRID column) drop out, because electricity and fuel never share a dataset.
3. **Data Year treats a blank year as a wildcard.** An edge with no year survives any temporal filter (it is read as "not time-varying"). `exact`/`range` are applied per edge; `recent_global`/`recent_edge` need a second pass (see below).

The key behavioural difference from the old logic: a blank value now **excludes** under provenance filters (rule 2) but **includes** under Data Year (rule 3). That asymmetry is deliberate — provenance blanks mean "different dataset", a blank year means "timeless".

## How it works (pseudocode)

```
filtered_G = new MultiDiGraph with every node of self.G (attrs preserved)
dy_mode, dy_values = parse search_parameters['Data Year']

temp_edges = []          # surviving edges + parsed year
global_max_year = -inf

# Pass 1 — Set admission + provenance + per-edge temporal
for each edge (u, v, key, attrs) in self.G:
    is_ef = 'emission factor' in attrs['Set'/'System'].lower()
    if is_ef and not include_emission_factors:
        skip

    is_infra = attrs['Set'] in {Unit Conversion, Unit Conversions, Magnitude Adjustment}
    if not is_infra:                         # the one rule
        for (param, value) in search_parameters except Data Year, value not None:
            data_val = attrs.get(param)      # blank -> None -> non-match
            if (value is list and data_val not in value) or (value != data_val):
                skip edge
    # infra falls straight through

    year = parse_float(attrs['Data Year'])   # blank/unparseable -> None (wildcard)
    if dy_mode == 'exact'  and year is not None and year not in dy_values:   skip
    if dy_mode == 'range'  and year is not None and not lo <= year <= hi:    skip

    global_max_year = max(global_max_year, year or -inf)
    temp_edges.append((u, v, key, attrs, year))

# Pass 2 — relative temporal modes
if dy_mode == 'recent_global':   emit edges whose year == global_max_year or is None
elif dy_mode == 'recent_edge':   per (u,v) keep max year; emit that + None-year edges
else:                            emit every temp_edge

return filtered_G
```

## Line-by-line — the admission loop

```python
is_infrastructure = attributes.get("Set") in (
    "Unit Conversion", "Magnitude Adjustment", "Unit Conversions",
)
match_found = True
if not is_infrastructure:                       # infra skips the whole check
    for param, search_val in search_parameters.items():
        if param == "Data Year" or search_val is None:
            continue                            # handled separately / no filter
        data_val = attributes.get(param)        # missing column -> None
        if isinstance(search_val, list):
            if data_val not in search_val:      # blank -> None not in list -> exclude
                match_found = False
                break
        elif search_val != data_val:            # blank -> None != value -> exclude
            match_found = False
            break
if not match_found:
    continue
```

The whole provenance check sits behind `if not is_infrastructure`. There is no per-rule exemption and no column carve-out anymore — infrastructure is decided once, up front, by `Set`.

## Edge cases worth knowing

- **Empty filter dict** → every Set-eligible edge survives (drops EFs by default, keeps everything else).
- **Filter that matches no provenance edges** → graph keeps all nodes but only the infrastructure edges (Unit Conversion / Magnitude Adjustment). Pathfinding may then find no source→target route, which the UI reports as "no path".
- **Data Year as a string vs number** — `pd.notnull` + `float()` cast handles both; `'2023'`, `2023`, `2023.0` all resolve to `2023.0`. Unparseable → `None` → wildcard.
- **`recent_global` with no timed edges** — `global_max_year` stays `-inf`; the `!= -inf` guard falls through to "emit everything", so the call never returns an accidentally empty graph.

## Usage

```python
# All EPA emission factors from 2023, plus all infrastructure edges
F = graph.filter_graph(
    {"Agency": ["EPA"], "Data Year": {"mode": "exact", "values": [2023]}},
    include_emission_factors=True,
)

# Most recent vintage per (source, target) pair, anthracite only
F = graph.filter_graph(
    {"Source-Chemical Type": ["Anthracite"], "Data Year": {"mode": "recent_edge", "values": []}},
    include_emission_factors=True,
)

# Pure unit-conversion graph — no EFs, no temporal restriction
F = graph.filter_graph({"Data Year": {"mode": "all", "values": []}})
```

## Performance

- One pass over `self.G.edges()` plus an optional second pass — both `O(E)`. For E ≈ 5,500 this is single-digit milliseconds.
- Rebuilt from scratch on every call; no memoization. Streamlit's `@st.cache_resource` caches the *engine* (graph + wrapper), not the filter output — correct, since filter parameters change on every UI interaction. (Reminder: engine edits need a **full** Streamlit restart, not just a rerun.)

## Mirrored logic

The same one-rule logic is implemented a second time, in pandas, by [[filters.apply_db_and_temporal_filters]] — the app uses it to compute live module/row counts *before* pathfinding. The two implementations must agree; when you change one, change the other. (This is the now-much-smaller version of the old "kept in sync by hand" cleanup item, since both sides collapsed to a single rule.)

## See also

[[UnitGraph]] · [[Unit graph]] · [[Temporal scope]] · [[Pathway-scoped filters]] · [[determine_conversion]] · [[determine_ghg_emissions]]
