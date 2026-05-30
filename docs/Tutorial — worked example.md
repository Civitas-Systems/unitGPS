---
type: tutorial
status: current
generation: Claude
last_updated: 2026-05-30
tags: [tutorial, example, ghg]
---

# Tutorial — a worked example

Convert **1 mmBTU of anthracite coal → kg CO₂e**, end to end, with the real numbers the
engine produces. This is the fastest way to understand what UnitGPS does and how to read
a result. Concepts: [[GHG emissions and GWP]], [[determine_ghg_emissions]].

## Set it up

| Control | Value |
|--------|-------|
| Source | `1` `mmBTU` (Energy) |
| Target | `kg` (Weight) |
| Modules | GHG Emissions on |
| Database Filters → Resources | Chemical Type = **Anthracite** |
| GHG weighting | AR5 · 100-year |

Press **Calculate**.

## What you get

**Total carbon footprint = 104.42 kg CO₂e.** It is built like this — and the app shows
exactly this table:

| Gas | Mass (per mmBTU) | × GWP (AR5/100) | = CO₂e | Share |
|-----|------------------|-----------------|--------|-------|
| CO₂ | 103.69 kg | × 1   | 103.69 kg | 99.3% |
| CH₄ | 0.011 kg (11 g) | × 28  | 0.308 kg | 0.3% |
| N₂O | 0.0016 kg (1.6 g) | × 265 | 0.424 kg | 0.4% |
| **Total** | | | **104.42 kg CO₂e** | |

## How to read it

- **Each gas is routed independently** from mmBTU to kg, and the route is *required* to
  cross a real emission-factor edge — so the mass is a genuine emission, not a unit trick.
- **Mass × GWP = CO₂e.** The GWP comes from the IPCC report and horizon you chose (AR5,
  100-yr: CH₄ = 28, N₂O = 265, CO₂ = 1 by definition).
- **CO₂ dominates** (~99%) — typical of combustion. The transparent table makes the
  trace gases visible even though they're tiny.
- **Provenance:** the per-gas expander shows the emission factor came from the EPA GHG
  Emission Factors Hub, with its release/updated dates and scope — every number is
  traceable.

## Verify it yourself

These are externally validated (`tests/test_validation.py`): the anthracite factors are
the EPA published values (103.69 kg CO₂, 11 g CH₄, 1.6 g N₂O per mmBTU) and the GWPs are
the IPCC AR5 values. See [[QA_NOTES]].

## Try next

- Switch the **Assessment Report** to AR6 and watch CH₄'s contribution change.
- Change **Source** to `GJ` or `kWh` — the engine re-routes automatically.
- Convert **purchased electricity** (`MWh` → `kg`) and pick an **eGRID region** under
  Location to use a regional grid factor.
