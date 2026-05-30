---
type: reference
status: current
generation: Claude
last_updated: 2026-05-30
tags: [faq, help, glossary]
---

# FAQ

- **What does UnitGPS do?** Converts between units and computes greenhouse-gas emissions
  over a curated data library, with a full audit trail for every result.
- **What's a GWP?** Global Warming Potential — how much a gas warms relative to CO₂ over a
  time horizon (e.g. CH₄ = 28× over 100 yr, AR5). Used to put each gas on a common scale.
- **What's CO₂e?** CO₂-equivalent — every gas expressed as Mass × GWP, then summed.
- **Where does the data come from?** Curated from authoritative sources: EPA GHG Emission
  Factors Hub & eGRID, IPCC AR4–AR6 GWPs, NIST/SI conversions. See [[References]].
- **Why must a GHG path cross an emission factor?** So the number is a *real* emission,
  not a unit conversion that happens to land on a mass unit. See [[GHG emissions and GWP]].
- **What's an "ambiguous" path?** When multiple sources provide parallel edges; the engine
  flags it and lets you pick which to use. See [[Ambiguous paths]].
- **How accurate is it?** Validated to match NIST / IPCC / EPA values exactly; round-trips
  within 0.1%. See [[QA_NOTES]].
- **What are Scopes 1/2/3?** GHG Protocol categories (direct / purchased energy / value
  chain). Filterable under Process.
- **Can I trust a specific number?** Every result shows its derivation and source — open
  the per-gas provenance to see the exact emission factor, agency, and dates.
- **What can't it do (yet)?** Affine conversions (temperature offsets) and uncertainty
  ranges — by design / roadmap. See [[METHODOLOGY]] §10 and [[Roadmap to world-class]].
