---
type: methodology
status: current
generation: Claude
last_updated: 2026-05-30
tags: [methodology, engine, ghg, reference]
---

# UnitGPS — Methodology

A rigorous account of *how* UnitGPS converts units and computes greenhouse-gas
emissions, the assumptions it makes, the data it relies on, and the limits of the
model. Written to be read by someone evaluating the tool's scientific validity.
Design rationale lives in [[architecture]]; pass history in [[CHANGELOG]].

## 1. Problem statement

Given a curated data library of unit conversions, fuel/material properties, and
greenhouse-gas emission factors, compute (a) the conversion factor between any two
units reachable through the library, and (b) the greenhouse-gas emissions of an
energy/material quantity — with every result fully auditable back to its source rows.

## 2. The graph model

Units are **nodes**; conversions are **directed edges** in a `networkx.MultiDiGraph`
(`Denominator → Numerator`). A multigraph is required because multiple *parallel*
edges between the same pair of units are common (e.g. several agencies' emission
factors for the same fuel→CO₂ relationship). Each edge carries its full provenance
(agency, dataset, year, scope, chemical, etc.) as attributes; each node carries its
`Unit Dimension`, `Unit System`, and a display colour. See [[Unit graph]].

**Reciprocal synthesis.** For every non-infrastructure row (emission factors,
chemical properties) the inverse edge is synthesised (`Value → 1/Value`) so the graph
is naturally bidirectional for those measurements; rows with `Value == 0` are dropped
first to avoid a divide-by-zero that would corrupt the graph. Static unit conversions
already exist in both directions in the source data and are not inverted. See
[[Reciprocal edges]].

## 3. Filtering — one rule

Pathfinding never runs on the full graph; it runs on a filtered subgraph
([[UnitGraph.filter_graph]]). The admission rule is singular:

1. **Infrastructure always passes** — `Unit Conversion`, `Unit Conversions`,
   `Magnitude Adjustment`. These have no provenance and are the connective tissue
   every multi-step path needs.
2. **Every other edge must strictly match each selected filter**, where a **blank
   value excludes** the edge. This is what makes provenance filters *partition* the
   data (choosing an eGRID region drops fuel rows, which are blank in that column).
3. **Data Year** treats a blank year as a wildcard; modes are `all`, `exact`,
   `range`, `recent_global`, `recent_edge`. See [[Temporal scope]].

Separately, the UI scopes the *available* Source/Target dimensions/units and filter
options to those reachable on the source→target **dimensional** pathway. See
[[Pathway-scoped filters]].

## 4. Conversion algorithm

```
filter_graph(params)                       -> subgraph F
identify_conversion_path(F, source, target) -> all shortest node paths   (networkx)
calculate_conversion_factor(F, paths, v0)   -> audited results
```

The conversion factor of a path is the **product of the edge `Value`s** along it
(`math.prod`); the result is `v0 × factor`. Each step records its source/target unit,
the chosen edge, that edge's value, and full provenance — so the displayed
multiplication chain *is* the audit trail. See [[calculate_conversion_factor]].

## 5. Ambiguity

When a step has parallel edges, the engine uses edge index 0 by default and flags the
path `is_ambiguous`. The UI can override per `(source, target)` via `edge_picks`, and
each step reports which parallel option was used. The default "first edge" choice is a
known limitation (§10).

## 6. Greenhouse-gas accounting

Each gas (CO₂, CH₄, N₂O) is routed **independently** with emission factors included:

```
for gas in (CO2, CH4, N2O):
    F     = filter_graph(params + {GHG: gas}, include_emission_factors=True)
    path  = shortest path source->target that TRAVERSES a real emission-factor edge
    Mass  = product of edge values along that path
    GWP   = IPCC GWP(gas, assessment_report, time_horizon)     # CO2 = 1 by definition
    CO2e  = Mass * GWP
Total CO2e = sum of per-gas CO2e
```

The **must-traverse-an-emission-factor** constraint
([[shortest_paths_via_edge_set]]) is essential: without it a gas could route through
pure unit/fuel-mass conversions to the same mass node and report a non-emission as an
emission. GWPs are selectable by IPCC Assessment Report (AR4/AR5/AR6) and time horizon
(20/100/500 yr). See [[GHG emissions and GWP]], [[determine_ghg_emissions]].

## 7. Data sources & provenance

- **Data Library** (`data/Data Library, 2025-10-18, 1960-2023.xlsx`) — the curated
  aggregation of unit conversions, magnitude adjustments, fuel/material properties,
  and emission factors, spanning data years 1960–2023.
- **Emission factors** — EPA GHG Emission Factors Hub (the in-app audit cites e.g.
  "GHG EF Hub v2025"), with eGRID regional factors for purchased electricity.
- **Global Warming Potentials** (`data/IPCC GWPs AR4-AR6.xlsx`) — IPCC Fourth (2007),
  Fifth (2013) and Sixth (2021) Assessment Reports.

Every emission-factor result in the UI surfaces its agency, dataset, release/updated
dates, scope, and chemical context. See [[Reference/Data/Data Library schema]].

## 8. Validation

The engine reproduces authoritative external constants exactly (`tests/test_validation.py`):

- **Unit conversions** vs NIST/SI: BTU→J = 1055.06, kWh→J = 3.6×10⁶, kJ→J = 1000,
  kg→g = 1000, hr→s = 3600, L→m³ = 0.001.
- **IPCC 100-yr GWPs**: AR4 (CH₄ 25, N₂O 298), AR5 (CH₄ 28, N₂O 265),
  AR6 (CH₄ 27.9, N₂O 273), CO₂ = 1 throughout.

63 automated tests run on every push (GitHub Actions). See [[Test suite]].

## 9. Reproducibility

Pure `pandas` + `networkx`; deterministic given the data. Dependencies pinned in
`requirements.txt`; data committed in-repo and loaded by a portable, `__file__`-relative
path; CI enforces the test suite. Deployable to Streamlit Community Cloud (`DEPLOYMENT.md`).

## 10. Assumptions & limitations

Stated honestly, because knowing the boundary is part of using a tool correctly:

- **Multiplicative only.** The model multiplies edge values, so it handles
  multiplicative conversions but **not affine** ones (e.g. °C↔°F, which need an offset).
  This is a deliberate scope choice — temperature is not in the dimension set.
- **Ambiguity default.** Parallel edges resolve to "first edge" unless overridden;
  this is not yet a principled data-quality ranking (recency / agency authority /
  geographic-temporal representativeness). *Roadmap item.*
- **No uncertainty propagation.** Results are point estimates; published emission-factor
  and conversion uncertainties are not carried through the chain. *Roadmap item.*
- **Path selection.** All shortest paths are returned; the headline answer depends on
  the path ordering and the `max paths` setting.
- **AR6 CH₄** is stored as 27.9; IPCC AR6 also lists fossil (29.8) and non-fossil (27.0)
  variants.

See the companion [[Roadmap to world-class]] for how the *Roadmap item* gaps would be
closed.

## 11. References

- NIST Special Publication 811 — *Guide for the Use of the International System of Units*.
- IPCC AR4 (2007) Ch. 2; AR5 (2013) Ch. 8; AR6 (2021) Ch. 7 — Global Warming Potentials.
- U.S. EPA — *GHG Emission Factors Hub*; *eGRID* (Emissions & Generation Resource Integrated Database).
