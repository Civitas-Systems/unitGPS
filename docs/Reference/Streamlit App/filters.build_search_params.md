---
type: function
parent: "[[filters]]"
module: streamlit_app.filters
file: apps/streamlit_app/filters.py
lines: "254-291"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, filtering, engine-bridge]
related:
  - "[[filters]]"
  - "[[UnitGraph.filter_graph]]"
  - "[[determine_conversion]]"
  - "[[determine_ghg_emissions]]"
---

# filters.build_search_params

Assemble the `search_params` dict the engine expects, pulling values from session_state. Last call before [[determine_conversion]] or [[determine_ghg_emissions]].

## Signature

```python
def build_search_params(
    active_sets: list[str],
    dy_mode_engine: str,
    dy_values: list[float],
) -> dict
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `active_sets` | `list[str]` | Sets to include in pathfinding — based on module checkboxes. |
| `dy_mode_engine` | `str` | One of `"all"`, `"exact"`, `"range"`, `"recent_global"`, `"recent_edge"`. |
| `dy_values` | `list[float]` | Year values appropriate to the mode. |

The rest of the search params (column filters) come from `session_state[col]` for each column in `COLS_TO_EXTRACT`.

## Output

A dict shaped exactly as [[UnitGraph.filter_graph]] expects:

```python
{
    'Set': ['Unit Conversion', 'Emission Factors', ...] or None,
    'Data Year': {'mode': 'all'|'exact'|..., 'values': [...]},
    'Source-Chemical Category': [...] or None,
    'Source-Chemical Type': [...] or None,
    'Agency': [...] or None,
    # ... + 20 more keys, mostly None
    # Many keys are deliberately included as None so the engine sees
    # them as "no filter here" rather than KeyError.
}
```

## Implementation

```python
def build_search_params(active_sets, dy_mode_engine, dy_values):
    search_params = {
        'Set': active_sets if active_sets else None,
        'Numerator Dimension': None, 'Numerator System': None,
        'Denominator Dimension': None, 'Denominator System': None,
        'Asset': None, 'Mode': None,
        'Vehicle1': None, 'Vehicle2': None,
        'Source-Vehicle Category': None, 'Source-Vehicle Type': None,
        'Source-Process Type': None,
        'Chemical1': None, 'Chemical2': None,
        'Source-Material Type': None,
        'IPCC Report': None, 'GHG': None,
        'Location in File': None, 'Release Date': None, 'Updated': None,
        'Data Year': {'mode': dy_mode_engine, 'values': dy_values},
    }
    for col in COLS_TO_EXTRACT:
        val = st.session_state.get(col, [])
        search_params[col] = val if val else None
    return search_params
```

The dict starts with explicit None for every engine-recognized key (so the engine never sees an unexpected absent key), then overrides with whatever session_state provides for the user-exposed filter columns.

## Why explicit Nones?

The engine's [[UnitGraph.filter_graph]] iterates `search_parameters.items()`. Any key with value None is skipped. Listing every possible filter column up front makes it obvious which columns the engine knows how to filter on — and prevents silent typos (a `'Agencyy'` key would never apply but also never error).

## Why `'Set'` is special

`active_sets` comes from the module checkboxes (Unit Conversions / Magnitude / Fuel / GHG), not from a Database Filter widget. It's bundled into `search_params` so the engine treats it uniformly with other column filters.

## Usage

```python
search_params = build_search_params(active_sets, dy_mode_engine, dy_values)
result = determine_conversion(graph_engine, search_params, source_unit, target_unit, 1.0)
```

## See also

[[filters]] · [[UnitGraph.filter_graph]] · [[determine_conversion]] · [[determine_ghg_emissions]]
