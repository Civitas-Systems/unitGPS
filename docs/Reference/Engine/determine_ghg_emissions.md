---
type: function
module: unitgps.engine.emissions
file: src/unitgps/engine/emissions.py
lines: "46-124"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [engine, wrapper, ghg, emissions]
related:
  - "[[determine_conversion]]"
  - "[[UnitGraph.filter_graph]]"
  - "[[find_gwp]]"
  - "[[GHG emissions and GWP]]"
  - "[[Ambiguous paths]]"
  - "[[AmbiguityError]]"
---

# determine_ghg_emissions

Compute total CO₂-equivalent emissions for a source activity. Routes each GHG (default: CO₂ + CH₄ + N₂O) independently through the [[Unit graph]], weights each gas's mass by its [[find_gwp|GWP]], and sums to a single total. The convenience function the Streamlit GHG Emissions panel calls.

## Signature

```python
def determine_ghg_emissions(
    graph_engine,
    search_parameters: dict,
    source: str,
    target: str,
    starting_value: float,
    gwps_data: pd.DataFrame,
    ghgs: Sequence[str] = ('CO2', 'CH4', 'N2O'),
    gwp_report: str = 'AR5',
    gwp_horizon: str = '100',
    edge_picks: dict | None = None,
) -> dict
```

### `edge_picks` parameter

Forwarded verbatim to [[calculate_conversion_factor]] for every gas's path. Same `(source, target)` → edge index dict shape. Useful when multiple gases share a static unit-conversion prefix that has parallel edges. Default `None`.

## Inputs

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `graph_engine` | `UnitGraph` | — | The full graph wrapper. Filtering happens internally per-gas. |
| `search_parameters` | `dict` | — | Column filters + temporal mode. Each gas gets a fresh copy with `GHG` added. |
| `source` | `str` | — | Source unit (e.g. `'mmBTU'`). |
| `target` | `str` | — | Target unit, must be a Weight unit (`'kg'`, `'tonne'`, etc.). |
| `starting_value` | `float` | — | Activity quantity. |
| `gwps_data` | `pd.DataFrame` | — | GWP table from [[DataLoader.load_gwps]]. |
| `ghgs` | `Sequence[str]` | `('CO2', 'CH4', 'N2O')` | Which gases to route. Add fluorinated gases here to include them. |
| `gwp_report` | `str` | `'AR5'` | IPCC assessment report. |
| `gwp_horizon` | `str` | `'100'` | Time horizon in years (`'20'`, `'100'`, `'500'`). |

## Output

```python
{
    'results': {
        'CO2': {
            'Mass': 103.69,                    # ultimate_value from calculation
            'GWP': 1.0,                        # from find_gwp
            'CO2e': 103.69,                    # Mass * GWP
            'Path': [['mmBTU', 'kg']],         # node paths from identify_conversion_path
            'Audit': {                         # full audit report from calculate_conversion_factor
                'route': [...],
                'conversion_factor': ...,
                'audit_steps': [...],
                'is_ambiguous': ...,
                ...
            },
            'Error': None,                     # or 'AmbiguityError' or str(exception)
        },
        'CH4': { ... },
        'N2O': { ... },
    },
    'total_co2e': 105.13,                      # sum of CO2e across all gases
    'valid_calc': True,                        # see "Valid calc semantics" below
}
```

Per-gas error isolation — one gas failing doesn't break the others. The UI renders even partial results.

## How it works (pseudocode)

```
total_co2e = 0
results = {}

for ghg in ghgs:                                                # CO2, CH4, N2O
    params_for_ghg = search_parameters + {'GHG': ghg}

    try:
        F     = graph_engine.filter_graph(params_for_ghg, include_emission_factors=True)
        paths = identify_conversion_path(F, source, target)
        audit = calculate_conversion_factor(F, convert_path_to_edge_tuples(paths), starting_value)
        if audit:
            mass  = audit[0]['ultimate_value']
            results[ghg] = {'Mass': mass, 'Audit': audit[0], 'Path': paths, 'Error': None, ...}
    except AmbiguityError as e:
        results[ghg] = {..., 'Error': 'AmbiguityError', 'Audit': e.args[0]}
    except Exception as e:
        results[ghg] = {..., 'Error': str(e)}

# Second pass: look up GWPs and sum
for ghg in ghgs:
    gwp = find_gwp(gwps_data, ghg, gwp_report, gwp_horizon)
    results[ghg]['GWP'] = gwp
    if results[ghg]['Mass'] is not None and gwp is not None:
        results[ghg]['CO2e'] = results[ghg]['Mass'] * gwp
        total_co2e += results[ghg]['CO2e']

valid = (any mass != None) and (no AmbiguityError) and (CO2.Mass != None)

return {'results': results, 'total_co2e': total_co2e, 'valid_calc': valid}
```

## Per-gas independent routing

This is the function's central design choice. Each gas takes a **different path** through the graph because the `GHG` filter changes which emission factor edges are visible:

```python
current_params = search_parameters.copy()
current_params['GHG'] = ghg                  # ← critical
F = graph_engine.filter_graph(current_params, include_emission_factors=True)
```

There's no "gas-agnostic mmBTU → kg" path. CO₂'s path uses CO₂ emission factor edges; CH₄'s path uses CH₄ emission factor edges; etc. See [[GHG emissions and GWP#Why per-gas routing matters]] for the reasoning.

## Valid calc semantics

`valid_calc` is `True` only when all of:

1. **At least one gas** produced a Mass. (Otherwise the total is 0.0 and meaningless.)
2. **No gas** raised an [[AmbiguityError]]. (Unreachable today; reserved for future strict mode.)
3. **CO₂ specifically** produced a Mass. (CO₂ is the load-bearing component; if it failed, the total is suspect.)

When `valid_calc=False`, the UI shows "Global calculation incomplete" but still renders the per-gas table — partial info is better than no info.

## Why initialize the dict before the try?

```python
for ghg in ghgs:
    emissions_results[ghg] = {'Mass': None, 'GWP': None, 'CO2e': None,
                              'Path': None, 'Audit': None, 'Error': None}
    ...
    try:
        ...
    except ...:
        emissions_results[ghg]['Error'] = ...
```

Every gas gets a "skeleton" entry before any computation. If the try block crashes early, the dict still has the expected keys so downstream code doesn't `KeyError`.

## GWP lookup happens AFTER all routing

```python
for ghg in ghgs:                           # routing loop
    ... compute mass ...

for ghg in ghgs:                           # second pass: GWPs + CO2e
    emissions_results[ghg]['GWP'] = find_gwp(...)
    if mass is not None and GWP is not None:
        emissions_results[ghg]['CO2e'] = mass * GWP
        total_co2e += val
```

Two separate passes. The split isn't required (could be one pass) but it cleanly separates "did we route through the graph?" from "did we find a GWP for this gas?".

## Edge cases

- **target_unit isn't a Weight unit** → emission factor paths won't exist → all gases get `Mass = None` → `valid_calc = False`. UI defends against this by locking the target dimension to Weight when GHG module is active.
- **Custom `ghgs` tuple** — `determine_ghg_emissions(..., ghgs=('CO2', 'CH4', 'N2O', 'SF6'))` adds SF₆ to the total. `valid_calc` still keys off CO₂ specifically.
- **GWP for an obscure gas** missing → `CO2e` stays `None` for that gas; total just doesn't include it.

## Usage

```python
gwps = loader.load_gwps()

result = determine_ghg_emissions(
    graph_engine=graph,
    search_parameters={
        'Source-Chemical Type': ['Anthracite'],
        'Data Year': {'mode': 'all', 'values': []},
    },
    source='mmBTU',
    target='kg',
    starting_value=1.0,
    gwps_data=gwps,
)

if result['valid_calc']:
    print(f"Total: {result['total_co2e']:.2f} kg CO2e")
    for ghg, details in result['results'].items():
        print(f"  {ghg}: {details['Mass']:.4f} kg × GWP={details['GWP']} = {details['CO2e']:.4f}")
```

The Streamlit GHG Emissions panel does this, then renders the per-gas table + LaTeX equation + stacked Plotly bar chart + Graphviz pathway.

## Cleanup items

- **`gwp_report` and `gwp_horizon` are hard-coded** to AR5/100 in callers today. Should be user-selectable in the UI. Tracked in [[architecture#4. Differences from Antigravity]].

## See also

[[determine_conversion]] · [[UnitGraph.filter_graph]] · [[find_gwp]] · [[GHG emissions and GWP]] · [[Ambiguous paths]] · [[AmbiguityError]] · [[Temporal scope]]
