---
type: reference
status: current
generation: Claude
last_updated: 2026-05-30
tags: [abstract, academic, paper]
---

# Abstract & paper outline

For if UnitGPS is ever written up or presented. Draft — Dave to refine.

## Abstract

UnitGPS is a graph-based system for universal unit conversion and greenhouse-gas (GHG)
emissions accounting with end-to-end auditability. Units are modelled as nodes and
conversions as directed edges of a multigraph; a conversion is evaluated as the product
of edge values along a shortest path. GHG emissions are computed by routing each gas
(CO₂, CH₄, N₂O) independently through a *required* emission-factor edge and weighting the
resulting mass by its IPCC Global Warming Potential for a chosen assessment report and
time horizon, summed to a total CO₂-equivalent. A single admission rule governs
data filtering, and filter options are scoped to the dimensional pathway between source
and target. Every result exposes a complete provenance trail to its source rows. The
implementation reproduces NIST, IPCC (AR4–AR6), and U.S. EPA reference values exactly and
round-trips conversions to within 0.1%, with the validation suite enforced in continuous
integration.

## Outline

1. **Introduction** — the problem (heterogeneous units + traceable emissions), motivation, contributions.
2. **Related work** — manual emission factors, online calculators, LCA/footprint tools.
3. **Methods** — graph model, conversion algorithm, GHG accounting, filtering & scoping (see [[METHODOLOGY]]).
4. **Implementation** — pandas + networkx engine, Streamlit UI, reproducibility & CI.
5. **Validation** — reproduction of NIST/IPCC/EPA constants; round-trip consistency (see [[QA_NOTES]]).
6. **Limitations & future work** — uncertainty propagation, principled ambiguity resolution, affine conversions, scaling (see [[Roadmap to world-class]], [[Performance and scaling]]).
7. **Conclusion.**

References: [[References]].
