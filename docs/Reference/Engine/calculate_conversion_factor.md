---
type: function
module: unitgps.engine.calculate
file: src/unitgps/engine/calculate.py
lines: "49-178"
status: current
generation: Claude
last_updated: 2026-05-23
tags: [engine, calculation, audit]
related:
  - "[[identify_conversion_path]]"
  - "[[convert_path_to_edge_tuples]]"
  - "[[UnitGraph.filter_graph]]"
  - "[[Ambiguous paths]]"
  - "[[AmbiguityError]]"
  - "[[is_valid_parameter]]"
  - "[[determine_conversion]]"
---

# calculate_conversion_factor

Multiply edge values along a path; return one structured "audit report" dict per path. This is the engine's reporting layer — it doesn't just produce a number, it produces the full provenance breakdown that drives the UI's LaTeX equation, Graphviz pathway, and audit-detail expander.

## Signature

```python
def calculate_conversion_factor(
    G: nx.MultiDiGraph,
    shortest_paths_edges: Sequence,
    starting_value: float = 1.0,
    edge_picks: Dict[Tuple[str, str], int] | None = None,
) -> List[Dict[str, Any]]
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `G` | `nx.MultiDiGraph` | The (typically filtered) graph the path came from. Used to look up edge attributes. |
| `shortest_paths_edges` | `list` | Either a single path `[(u1,v1), (u2,v2), ...]` or a list of such paths. Typically the output of [[convert_path_to_edge_tuples]]. |
| `starting_value` | `float` | The numeric input. Multiplied by the conversion factor to produce `ultimate_value`. Defaults to 1.0. |
| `edge_picks` | `dict \| None` | Per-edge user picks for ambiguous steps: `{(source, target): edge_index}`. When present, overrides the default "pick edge 0" behaviour for the listed edges. Defaults to `None` (legacy behaviour). |

## Output

A `list[dict]`, one entry per path. Each dict (an "audit report") has this shape:

```python
{
    'route': ['mmBTU', 'BTU', 'kg'],           # full node sequence
    'starting_value': 1.0,                     # input
    'conversion_factor': 103.69,               # product of edge values
    'ultimate_value': 103.69,                  # starting × factor
    'audit_steps': [
        {
            'step_num': 1,
            'source': 'mmBTU',
            'target': 'BTU',
            'edges': [
                {
                    'key': 0,                   # MultiDiGraph edge key
                    'value': 1000000.0,
                    'set': 'Magnitude Adjustment',
                    'parameters': {...},        # general edge attrs
                    'source': {...},            # Agency, Dataset, Version, ...
                },
                # ... more entries if parallel edges exist
            ],
            'chosen_edge_idx': 0,           # which edge index was used as primary
        },
        # ... more steps
    ],
    'is_ambiguous': False,                      # True iff any step had >1 edge
    'ambiguous_details': [],                    # the subset of audit_steps that were ambiguous
}
```

The double-list structure (`audit_steps[i]['edges']`) is what lets the UI show "step 2 had 3 parallel options, here they are."

## How it works (pseudocode)

```
if no input paths: return None

# Normalize input shape — accept single path or list of paths
if input is a single path: wrap in [path]

results = []
for each path:
    route = sequence of nodes implied by the edge tuples
    path_values = []          # edge values to multiply
    audit_steps = []          # rich per-step breakdown
    path_ambiguous = False

    for each (u, v) edge in path:
        edges_at_step = G[u][v]    # all parallel edges in this MultiDiGraph slot
        if len(edges_at_step) > 1:
            path_ambiguous = True

        # Build the audit step's edge list
        step_edges = []
        for key, edge_data in edges_at_step.items():
            split edge_data into:
              - source_keys (Agency, Dataset, Version, Updated, ...)
              - general_params (everything else not in exclude_keys)
            keep only is_valid_parameter() entries
            append {key, value, set, parameters, source}

        audit_steps.append({step_num, source=u, target=v, edges=step_edges})

        # The actual math uses just the FIRST edge's value
        path_values.append(edges_at_step[first_key].Value)

    conversion_factor = product(path_values)
    ultimate_value    = starting_value * conversion_factor

    results.append({
        route, starting_value, conversion_factor, ultimate_value,
        audit_steps, is_ambiguous=path_ambiguous,
        ambiguous_details = audit_steps where len(edges) > 1,
    })

return results
```

## Key implementation details

### Input shape normalization

```python
paths_to_process = list(shortest_paths_edges)
if shortest_paths_edges and isinstance(shortest_paths_edges[0], tuple):
    paths_to_process = [list(shortest_paths_edges)]
```

If the first element is a tuple, it's a single path; wrap it. Otherwise it's already a list of paths. This is the symmetric counterpart of [[convert_path_to_edge_tuples]]'s output-shape uniformization.

### Edge-attribute categorization

```python
source_keys = ['Agency', 'Dataset', 'Release Date', 'Version', 'Location in File', 'Updated']
exclude_keys = {
    'Value', 'Conversion', 'Operation', 'Source', 'Reference',
    'Numerator', 'Denominator', 'Color', 'Weight',
    'Numerator System', 'Denominator System',
    'Numerator Dimension', 'Denominator Dimension',
    'Set', 'System',
}
exclude_keys.update(source_keys)

source_params = {k: edge_data[k] for k in source_keys if k in edge_data and is_valid_parameter(edge_data[k])}
general_params = {kk: vv for kk, vv in edge_data.items() if kk not in exclude_keys and is_valid_parameter(vv)}
```

Three categories of edge attributes:

| Category | Examples | Where it ends up |
|----------|----------|------------------|
| **Source** | `Agency`, `Dataset`, `Version`, `Updated` | Audit `source` block — provenance/attribution |
| **General** | `GHG`, `Source-Chemical Type`, `Country`, `Data Year` | Audit `parameters` block — what the edge represents |
| **Excluded** | `Value`, `Numerator`, `Denominator`, `Color` | Filtered out — either already shown elsewhere (Value), structural (Numerator/Denominator), or not user-facing (Color) |

[[is_valid_parameter]] runs on each value to drop empty/NaN entries.

### Picking which parallel edge contributes to the result

When a step has multiple parallel edges, the calculator defaults to picking edge 0 — whatever order `nx.MultiDiGraph[u][v].items()` returns, typically insertion order. The path is still flagged with `is_ambiguous=True` so the UI can surface that alternatives exist.

`edge_picks` lets the UI persist a user's per-edge choice. When provided, the engine uses `edge_picks.get((u, v), 0)` to determine the primary edge for each step:

```python
pick_idx = 0
if edge_picks and (u, v) in edge_picks:
    requested = edge_picks[(u, v)]
    # Clamp defensively — a stale pick from a previous calc could reference
    # an index that no longer exists after filter changes.
    pick_idx = max(0, min(int(requested), edge_count - 1))
step_details["chosen_edge_idx"] = pick_idx

primary_val = step_values[pick_idx]
```

The chosen index is also written back to each step as `chosen_edge_idx` so renderers know which edge was used (and which alternatives are available). See [[Edge picks for ambiguous paths]] for the full UI integration story.

A future strict mode would raise [[AmbiguityError]] when `edge_picks` doesn't resolve an ambiguous step.

## Edge cases

- **Empty input** → returns `None` (not `[]`). Slightly inconsistent with [[identify_conversion_path]]'s `[]`-returning convention; preserved for backward compatibility.
- **Single-node path** (`[]` edges) → `conversion_factor = math.prod([]) = 1.0`, `ultimate_value = starting_value`. Treated as identity conversion.
- **An edge with `Value` not in attrs** → `edge_data.get('Value', 1.0)` falls back to 1.0. Defensive default; shouldn't happen with real data.
- **All steps unambiguous** → `is_ambiguous=False`, `ambiguous_details=[]`. UI suppresses the amber warning.

## Performance

- One pass over each path. For typical 1–3 hop paths with 1–5 parallel edges per step, completes in microseconds.
- Builds a fresh `step_details` dict per call — no caching. Fine because callers don't reuse results across runs.

## Usage

Almost always invoked indirectly through [[determine_conversion]]:

```python
res = determine_conversion(graph, search_params, source='mmBTU', target='kg', starting_value=1.0)
if res['status'] == 'success':
    for audit in res['data']:
        print(f"{audit['conversion_factor']} via {audit['route']}")
```

Direct invocation pattern:

```python
F = graph.filter_graph(search_params)
paths = identify_conversion_path(F, source, target)
edges = convert_path_to_edge_tuples(paths)
results = calculate_conversion_factor(F, edges, starting_value=42.0)
```

With explicit edge picks for an ambiguous path:

```python
# User picked the second parallel edge for the (mmBTU, ton) step
results = calculate_conversion_factor(
    F, edges, starting_value=42.0,
    edge_picks={("mmBTU", "ton"): 1},
)
assert results[0]["audit_steps"][0]["chosen_edge_idx"] == 1
```

## See also

[[identify_conversion_path]] · [[convert_path_to_edge_tuples]] · [[UnitGraph.filter_graph]] · [[Ambiguous paths]] · [[Edge picks for ambiguous paths]] · [[AmbiguityError]] · [[is_valid_parameter]] · [[determine_conversion]]
