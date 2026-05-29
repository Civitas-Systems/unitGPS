---
type: concept
status: current
generation: Claude
last_updated: 2026-05-20
tags: [concept, data-loading, graph]
related:
  - [[Unit graph]]
  - [[DataLoader.load_data_library]]
  - [[Data Library schema]]
---

# Reciprocal edges

To make pathfinding work in both directions, the engine **synthesizes reciprocal (inverse) edges** for some kinds of Data Library rows during load. Without this step, you could compute *1 mmBTU Anthracite → 103.69 kg CO₂* but not *1 kg CO₂ → ? mmBTU Anthracite*, because the source data only ships the forward direction.

## The synthesis rule

```
For each row where Set ∉ {'Unit Conversion', 'Magnitude Adjustment'}:
    new_row = swap(Numerator, Denominator)
    new_row.Value = 1 / row.Value
    append new_row to the combined DataFrame
```

So a row reading:

| Numerator | Denominator | Value | Set | GHG | Source-Chemical Type |
|-----------|-------------|-------|-----|-----|----------------------|
| kg | mmBTU | 103.69 | Emission Factors | CO₂ | Anthracite |

becomes two rows in the combined DataFrame:

| Numerator | Denominator | Value | Set | GHG | Source-Chemical Type |
|-----------|-------------|-------|-----|-----|----------------------|
| kg | mmBTU | 103.69 | Emission Factors | CO₂ | Anthracite |
| mmBTU | kg | 0.009644 | Emission Factors | CO₂ | Anthracite |

All other columns (`Agency`, `Dataset`, `Data Year`, etc.) are copied over unchanged — so a filter that selects "EPA, 2023, Anthracite" still matches both the forward and reverse edge.

Implementation: see [[DataLoader.load_data_library]].

## Why exclude Unit Conversion and Magnitude Adjustment?

Because the source data **already ships both directions** for those Sets. The Data Library has six rows for J ↔ kJ ↔ MJ ↔ J in both directions, six for kg ↔ g, and so on. Synthesizing reciprocals on top would create duplicate parallel edges — and duplicate edges mean every conversion through them looks [[Ambiguous paths|ambiguous]] for no good reason.

Concretely, you'd see this:

```
Before synthesis:    1 kJ → J  =  1000      (one edge)
After (correct):     1 kJ → J  =  1000      (one edge, original)
After (incorrect):   1 kJ → J  =  1000      (original)
                  +  1 kJ → J  =  1000      (synthesized reciprocal of "J per kJ = 0.001")
                  → ambiguous!
```

By excluding Unit Conversions and Magnitude Adjustments from synthesis, the engine keeps these "infrastructure" edges crisp and unambiguous.

## Why include the other Sets?

**Emission Factors** ship as `kg of GHG per mmBTU of fuel`. The reverse direction (`mmBTU of fuel per kg of GHG`) is a legitimate query — for example, "how much coal would I need to burn to produce 1 ton of CO₂?". Without the reciprocal edge, that path doesn't exist.

**Chemical Properties** are similar — density rows like `kg per L` need to be reversible to support `L per kg`.

**Global Warming Potentials** rows are present in the Data Library but the engine doesn't use them (GWPs come from the separate IPCC file). They get reciprocated by the rule above but don't end up in the graph.

## What's stored vs. what's the truth

A subtle property: the reciprocal edge's `Value` is the exact reciprocal of the forward edge. So a forward Value of `103.69` produces a reverse Value of `0.009644017...`. The reciprocal is mathematically guaranteed to satisfy `forward × reverse = 1.0` — there's no rounding error introduced by the synthesis step itself, only by whatever precision the original Value was stored at.

This is why the round-trip test in [[Test suite]] passes exactly:

```python
1.0 (J) → kJ → J = 1.0   # exactly, modulo float epsilon
```

## See also

[[Unit graph]] · [[DataLoader.load_data_library]] · [[Ambiguous paths]] · [[Data Library schema]]
