---
type: roadmap
status: current
generation: Claude
last_updated: 2026-05-30
tags: [roadmap, engine, design]
---

# Roadmap to world-class (engine-level)

The *scaffolding* gaps (documentation, external validation, provenance,
reproducibility, CI) are done or in progress and are low-risk. What remains to move
the **engine** itself from "good" to "world-class" is a short list of genuine design
decisions on Dave's foundation — to be done together, awake, because each touches the
data schema or the scientific model.

## 1. Uncertainty propagation (highest value)
Emission factors and many conversions are published with uncertainty (± ranges, data
quality tiers; cf. IPCC and the GHG Protocol). The engine currently returns point
estimates. World-class accounting carries uncertainty through the multiplicative
chain — analytically (relative-error addition in quadrature) or by Monte Carlo — so a
result reads "104 ± X kg CO2e."
Touches: data schema (uncertainty columns), `calculate_conversion_factor` (propagate),
UI (display ranges). Reversible, additive if uncertainty is optional per edge.

## 2. Principled ambiguity resolution
Parallel edges currently resolve to "first edge" (`is_ambiguous` flagged, `edge_picks`
override). "First" is not scientifically defensible. Replace it with a documented,
deterministic ranking policy — by data recency, agency authority, and
geographic/temporal representativeness — and/or surface the full alternative set with
those attributes for the user to choose.
Touches: `calculate_conversion_factor` default selection, data-quality metadata (below).

## 3. Data-quality / representativeness metadata
Authoritative EF databases tag each factor with a data-quality tier and
geographic/temporal representativeness. Carrying these as edge attributes would let the
engine (a) rank ambiguous edges (item 2) and (b) report fitness-for-purpose.
Touches: data schema, surfaced in the audit.

## 4. Scope note — affine conversions
The multiplicative model cannot represent affine conversions (temperature offsets,
e.g. degC<->degF). This is currently out of scope (no Temperature dimension). Adding it
would require a non-multiplicative edge type (scale + offset) and a path evaluator that
composes affine maps. Document as an explicit boundary unless/until needed.

## Sequencing
1 then 2+3 together (they share the data-quality metadata), 4 only if temperature
enters scope. None should be done autonomously — they are foundation decisions.
