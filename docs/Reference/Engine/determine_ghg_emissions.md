---
type: function
parent: "[[Unit graph]]"
module: unitgps.engine.emissions
file: src/unitgps/engine/emissions.py
lines: "55-137"
status: current
generation: Claude
last_updated: 2026-05-30
tags: [engine, ghg, gwp]
related:
  - "[[GHG emissions and GWP]]"
  - "[[determine_conversion]]"
  - "[[find_gwp]]"
  - "[[shortest_paths_via_edge_set]]"
  - "[[calculate_conversion_factor]]"
  - "[[UnitGraph.filter_graph]]"
---

# determine_ghg_emissions

Route each greenhouse gas (CO2, CH4, N2O) independently from `source` to `target`, weight each resulting mass by its Global Warming Potential, and sum to a single CO2e total. The high-level GHG entry point — the GHG result panel renders its return value directly.

## Signature

```python
def determine_ghg_emissions(
    graph_engine, search_parameters, source, target, starting_value, gwps_data,
    ghgs=("CO2", "CH4", "N2O"), gwp_report="AR5", gwp_horizon="100", edge_picks=None,
) -> dict
```

## What it does, per gas

For each gas it runs the standard pipeline, but with a **constraint** and a GHG-specific filter key:

```
for ghg in (CO2, CH4, N2O):
    params = search_parameters + {"GHG": ghg}
    F = graph_engine.filter_graph(params, include_emission_factors=True)   # EFs included
    paths = shortest_paths_via_edge_set(F, source, target, _is_emission_factor_edge)
    audit = calculate_conversion_factor(F, edge_tuples(paths), starting_value, edge_picks)
    Mass  = audit[0]["ultimate_value"]
```

Two things are specific to GHG:

1. **EFs are included** (`include_emission_factors=True`) — unit-conversion routing never needs them, GHG always does.
2. **The route must cross a real emission-factor edge.** [[shortest_paths_via_edge_set]] with `_is_emission_factor_edge` enforces this. Without it, a gas could route through pure unit/fuel-mass conversions to the same `kg` node and report a non-emission as if it were one. This is the *"a GHG path must travel through one emission-factor data type"* rule. See [[GHG emissions and GWP]].

## GWP weighting and the total

After all gases are routed, each mass is weighted:

```
for ghg:
    GWP  = find_gwp(gwps_data, ghg, gwp_report, gwp_horizon)   # CO2 -> 1.0
    CO2e = Mass * GWP
    total_co2e += CO2e
```

`gwp_report` / `gwp_horizon` come from the AR + Time-Horizon selectors that sit under the GHG module in the UI. See [[find_gwp]].

## Output

```python
{
  "results": {
    "CO2": {"Mass", "GWP", "CO2e", "Path", "Audit", "Error"},
    "CH4": {...}, "N2O": {...},
  },
  "total_co2e": float,
  "valid_calc": bool,
}
```

- `Audit` is the full per-step audit dict from [[calculate_conversion_factor]] (route, edges, EF value, provenance) — the GHG renderer uses it for the transparent calc table and the provenance expander.
- **`valid_calc`** is `True` only if at least one gas produced a mass AND no gas hit an `AmbiguityError` AND CO2 specifically resolved (CO2 is the dominant term; if it failed the total is meaningless).

## Error handling

Errors are caught **per gas**, not for the whole call: one gas hitting an `AmbiguityError` or routing failure sets that gas's `Error`/`Audit` and leaves the others intact. This is why the panel can show CO2 + N2O while CH4 reads "no path found".

## Rendering

The result feeds [[renderers - emissions]], which now shows the explicit **Mass × GWP = CO2e** table per gas (so the math is visible rather than trusted), a contribution bar, and a collapsed per-gas pathway/provenance section. See [[GHG condensed panel]].

## See also

[[GHG emissions and GWP]] · [[determine_conversion]] · [[find_gwp]] · [[shortest_paths_via_edge_set]] · [[calculate_conversion_factor]] · [[UnitGraph.filter_graph]]
