---
type: concept
status: current
generation: Claude
last_updated: 2026-05-20
tags: [concept, ghg, emissions, gwp]
related:
  - [[determine_ghg_emissions]]
  - [[find_gwp]]
  - [[IPCC GWPs]]
  - [[Unit graph]]
---

# GHG emissions and GWP

GHG calculation is just unit conversion with extra steps. UnitGPS computes the emissions for an activity by routing each greenhouse gas independently through the [[Unit graph]] and then weighting each mass by its Global Warming Potential to get a total CO₂-equivalent.

## The math

For an activity producing masses $m_{CO_2}, m_{CH_4}, m_{N_2O}$:

$$\text{Total CO}_2\text{e} = m_{CO_2} \cdot 1 + m_{CH_4} \cdot \text{GWP}_{CH_4} + m_{N_2O} \cdot \text{GWP}_{N_2O}$$

CO₂ has GWP = 1 by definition (it's the reference gas). Methane and nitrous oxide get multipliers from whichever IPCC Assessment Report and time horizon the caller picked.

## The algorithm

[[determine_ghg_emissions]] does this per call:

```
for ghg in ['CO2', 'CH4', 'N2O']:
    params_with_ghg = search_params + {'GHG': ghg}
    F = filter_graph(params_with_ghg, include_emission_factors=True)
    path = identify_conversion_path(F, source, target)
    mass = calculate_conversion_factor(F, path, starting_value)

    gwp = find_gwp(gwps_data, ghg, report, horizon)
    co2e_per_gas = mass * gwp
    total_co2e += co2e_per_gas
```

Each gas takes a **separately filtered subgraph** because the `GHG` filter changes which emission factor edges are available — there is no path "from mmBTU to kg" that's gas-agnostic; you need to know whether you're looking at CO₂ emission factors or CH₄ emission factors.

## Why per-gas routing matters

A coal burn produces all three gases simultaneously, but each has its own path through the graph:

- **CO₂**: 1 mmBTU Anthracite → 103.69 kg CO₂  (high-mass, high-confidence)
- **CH₄**: 1 mmBTU Anthracite → 0.011 kg CH₄  (low-mass, important due to high GWP)
- **N₂O**: 1 mmBTU Anthracite → 0.0016 kg N₂O  (tiny-mass, important due to very high GWP)

If any single gas's path can't be resolved (filters too narrow, missing data), that gas contributes nothing to the total. The audit report flags this per-gas via `results[ghg]['Error']`.

## GWP picking

[[find_gwp]] is the lookup. Its signature is `find_gwp(gwps_data, ghg, assessment_report='AR5', time_horizon='100')`. The defaults match what most US/EU regulators currently require, but the IPCC ships:

| AR | Year | CO₂ | CH₄ (100yr) | N₂O (100yr) |
|----|------|-----|-------------|-------------|
| AR4 | 2007 | 1 | 25 | 298 |
| AR5 | 2014 | 1 | 28 | 265 |
| AR6 | 2021 | 1 | 27.9 | 273 |

Each report also has 20-year and 500-year horizons. **Same gas, different multiplier** — methane is ~84 over 20 years but only ~7 over 500 years, because methane decays in the atmosphere on a ~12-year timescale.

For this reason: which AR / horizon the user picks materially changes the answer. The Streamlit UI exposes both as live selectors next to the GHG module toggle (AR4/AR5/AR6 × 20/100/500 yr); the active values surface as a subtitle on the GHG Emissions panel header. Defaults are AR5 / 100 yr to match most US/EU regulators.

## "Valid calc" semantics

`determine_ghg_emissions` returns `valid_calc=True` only when:

1. **At least one gas** produced a mass result (had a viable path).
2. **No gas** raised an [[AmbiguityError]] (today this is unreachable since the engine doesn't raise; reserved for future strict mode).
3. **CO₂ specifically** produced a result. CO₂ is the load-bearing component for most activities; if you can't compute CO₂, the total is suspicious.

If any of those fail, the UI shows "Global calculation incomplete" but still renders the per-gas table so the user can see which gases did compute.

## See also

[[determine_ghg_emissions]] · [[find_gwp]] · [[IPCC GWPs]] · [[UnitGraph.filter_graph]] · [[Ambiguous paths]]
