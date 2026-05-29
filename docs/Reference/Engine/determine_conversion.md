---
type: function
module: unitgps.engine.emissions
file: src/unitgps/engine/emissions.py
lines: "126-156"
status: current
generation: Claude
last_updated: 2026-05-23
tags: [engine, wrapper, conversion]
related:
  - "[[UnitGraph.filter_graph]]"
  - "[[identify_conversion_path]]"
  - "[[convert_path_to_edge_tuples]]"
  - "[[calculate_conversion_factor]]"
  - "[[determine_ghg_emissions]]"
  - "[[AmbiguityError]]"
---

# determine_conversion

High-level wrapper for non-emission conversions. Chains filter → pathfind → calculate, wraps the result in a status dict the UI can render directly. The convenience function the Streamlit Conversions panel calls.

## Signature

```python
def determine_conversion(
    graph_engine,
    search_parameters: dict,
    source: str,
    target: str,
    starting_value: float,
    edge_picks: dict | None = None,
) -> dict
```

### `edge_picks` parameter

Forwarded verbatim to [[calculate_conversion_factor]]. A dict mapping `(source, target)` → edge index for ambiguous steps. When provided, the engine uses the requested edge instead of the default 0. Indices are clamped defensively. Default `None` preserves the legacy first-edge behaviour.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `graph_engine` | `UnitGraph` | The full graph wrapper, NOT a pre-filtered subgraph. Filtering happens inside. |
| `search_parameters` | `dict` | Column filters + `Data Year` mode. See [[UnitGraph.filter_graph#Inputs]]. |
| `source` | `str` | Source unit name. |
| `target` | `str` | Target unit name. |
| `starting_value` | `float` | The input quantity. Multiplied through to produce `ultimate_value`. |

Note: emission factors are **excluded** from the filter — this is the conversion-only path. For GHG emissions use [[determine_ghg_emissions]].

## Output

One of three status dicts:

```python
# Success
{
    'status': 'success',
    'data': [
        {  # one audit report per shortest path — see calculate_conversion_factor
            'route': [...],
            'conversion_factor': ...,
            'ultimate_value': ...,
            'audit_steps': [...],
            'is_ambiguous': ...,
            ...
        },
        ...
    ],
}

# Ambiguity error (only reachable if AmbiguityError is raised — currently never)
{
    'status': 'ambiguity_error',
    'data': <whatever the exception's first arg was>,
}

# Any other error (no path, missing nodes, unexpected exception)
{
    'status': 'error',
    'message': '<error description>',
}
```

The dict shape is meant to be ready-to-render — the Conversions panel switches on `status` and calls a different renderer per branch.

## How it works (pseudocode)

```
1. Filter the graph (EFs excluded).
2. Find all shortest paths source → target in the filtered graph.
3. Convert node paths to edge tuples.
4. Calculate the conversion factor + audit reports.
5. If we got results, return status=success with the audit list.
   If pathfinding came back empty, return status=error with "No path found".
   If AmbiguityError was raised, return status=ambiguity_error.
   Any other exception: return status=error with the string message.
```

## Line-by-line

```python
current_params = search_parameters.copy()
```

Shallow copy. Today the function doesn't mutate `current_params`, but the copy is defensive against a future change that adds a `current_params['something'] = ...`.

```python
try:
    F = graph_engine.filter_graph(current_params, include_emission_factors=False)
```

The critical difference from [[determine_ghg_emissions]] — `include_emission_factors=False`. Emission factors are not part of unit conversions.

```python
    shortest_paths_nodes = identify_conversion_path(F, source, target)

    calc_results = calculate_conversion_factor(
        F,
        convert_path_to_edge_tuples(shortest_paths_nodes),
        starting_value,
    )
```

The three-step pipeline. Each function is independently testable; this is just the convenience composition.

```python
    if calc_results:
        return {'status': 'success', 'data': calc_results}
    return {'status': 'error', 'message': 'No path found'}
```

Empty result list means the path-find returned no paths. (Pathfinding returns `[]` for both "missing node" and "no connection"; the user sees the same message either way.)

```python
except AmbiguityError as e:
    return {'status': 'ambiguity_error', 'data': e.args[0] if e.args else None}
except Exception as e:
    return {'status': 'error', 'message': str(e)}
```

The [[AmbiguityError]] branch is reserved-but-unreachable today (see that page). The bare `Exception` catch turns any unexpected error (missing column in `gwps_data`, malformed `search_parameters`, etc.) into a UI-friendly error message instead of a stack trace.

## Edge cases

- **Source unit not in graph** → pathfinding returns `[]` → `status='error'` with "No path found".
- **No filters narrow enough to make a path** → same outcome.
- **Bidirectional paths exist** — both forward and reverse will be among the shortest paths. The UI shows up to `max_paths`.

## Usage

```python
result = determine_conversion(
    graph_engine,
    search_parameters={'Data Year': {'mode': 'all', 'values': []}},
    source='kJ',
    target='J',
    starting_value=1.0,
)

if result['status'] == 'success':
    audits = result['data']
    print(f"{len(audits)} path(s) found")
    print(f"First path: {audits[0]['conversion_factor']}× via {audits[0]['route']}")
elif result['status'] == 'ambiguity_error':
    print('Ambiguity:', result['data'])
else:
    print('Error:', result['message'])
```

The Streamlit Conversions panel does exactly this and then renders the audit list with LaTeX equations + Graphviz diagrams.

## See also

[[UnitGraph.filter_graph]] · [[identify_conversion_path]] · [[convert_path_to_edge_tuples]] · [[calculate_conversion_factor]] · [[determine_ghg_emissions]] · [[AmbiguityError]]
