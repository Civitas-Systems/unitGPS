---
type: concept
status: current
generation: Claude
last_updated: 2026-05-20
tags: [concept, edge-case, ux]
related:
  - [[Unit graph]]
  - [[calculate_conversion_factor]]
  - [[AmbiguityError]]
---

# Ambiguous paths

A path step is *ambiguous* when the [[Unit graph]] has more than one parallel edge connecting the same `(source, target)` pair. The conversion can still be computed — the engine just has to pick one of the parallel values — but the result is no longer uniquely determined by the filters.

## Why this happens

Three common causes:

1. **Multiple agencies publish the same EF.** EPA and DESNZ both report kg CO₂ per mmBTU of bituminous coal. Different values, both valid.
2. **Multiple fuel sub-types share a category.** When the filter is "Source-Chemical Category = Coal" without further specification, the graph still has separate edges for Anthracite, Bituminous, Sub-bituminous, and Lignite — all from `kg per mmBTU`.
3. **Multiple Data Year vintages.** Without a temporal filter, an EF revised yearly contributes several parallel edges, one per vintage.

## How the engine handles it today

In [[calculate_conversion_factor]]:

```python
for step in path:
    edges_at_step = G[u][v]            # all parallel edges
    if len(edges_at_step) > 1:
        path_ambiguity = True          # mark path
    primary_val = first(edges_at_step) # silently pick the first
    path_values.append(primary_val)
```

The audit report's `is_ambiguous` field is set to `True` and `ambiguous_details` lists exactly which steps had multiple edges. The Conversions panel in the Streamlit app shows an amber warning:

> ⚠️ **Ambiguous Pathway**: This conversion path has multiple parallel edges (e.g. multiple fuels). Only the first option was used. To get a more specific conversion, narrow down your filters (e.g. Chemical Type).

There's also an [[AmbiguityError]] exception class reserved for callers who want strict mode (raise instead of warn), but the engine doesn't raise it today — the warn-and-continue behavior was a deliberate Antigravity-era choice.

## How users resolve it today

- Narrow the **Source-Chemical Type** filter (Anthracite vs. Bituminous vs. Sub-bituminous).
- Narrow the **Agency** filter (EPA vs. DESNZ).
- Switch the **Temporal Scope** to "Most Recent per Path" or "Specific Years" to collapse vintage ambiguity.

## How users should resolve it (planned)

The flagged improvement is to let users **explicitly choose** which parallel edge to use, presented inline in the result panel. Something like:

```
Step 2: mmBTU → kg
  ○ Anthracite (EPA, 2023, 103.69 kg/mmBTU)
  ○ Bituminous (EPA, 2023, 93.28 kg/mmBTU)
  ○ Sub-bituminous (EPA, 2023, 97.17 kg/mmBTU)
```

…with a default of "compute one result per option and show all of them stacked." See [[architecture#4. Differences from Antigravity]].

## Edge cases worth knowing

- **All ambiguous edges have identical Value.** Algorithmically still ambiguous, but the result happens to be deterministic. Engine still flags it.
- **GHG emissions paths cross-product the ambiguity.** Each gas (CO₂/CH₄/N₂O) routes independently. If CO₂'s path is unambiguous but CH₄'s is ambiguous, the total CO₂e inherits CH₄'s ambiguity. See [[determine_ghg_emissions]].

## See also

[[Unit graph]] · [[calculate_conversion_factor]] · [[AmbiguityError]] · [[determine_ghg_emissions]]
