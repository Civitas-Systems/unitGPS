---
type: qa
status: current
generation: Claude
last_updated: 2026-05-30
tags: [qa, validation, findings]
---

# QA & Validation Notes

How answers are checked, and findings from independent verification. QA has two
layers: **internal-data** (does the engine process the data correctly) and
**external validity** (do the data's values match authoritative sources). The
external layer is verified against published primary sources, not just assertion.

## Method

- Engine outputs computed via the real engine (`determine_conversion`, `find_gwp`).
- Reference constants taken from authoritative sources (NIST SI; IPCC AR4/AR5/AR6;
  EPA), and — for load-bearing or nuanced values — confirmed by web search against
  primary documents (IPCC WGI Ch. 7, GHG Protocol/GHGMI tables).
- Encoded as `tests/test_validation.py` (runs in CI). Discrepancies are reported
  here, never silently "fixed" in the data.

## Confirmed (engine reproduces the authority exactly)

- **Unit conversions vs NIST/SI:** BTU→J = 1055.06, kWh→J = 3.6e6, kJ→J = 1000,
  kg→g = 1000, hr→s = 3600, L→m^3 = 0.001.
- **EPA anthracite EF (stationary combustion):** 103.69 kg CO2, 0.011 kg CH4,
  0.0016 kg N2O per mmBTU — engine reproduces EPA GHG EF Hub values exactly.
- **IPCC GWP-100:** AR4 (CH4 25, N2O 298), AR5 (CH4 28, N2O 265), AR6 N2O 273,
  CO2 = 1 throughout. AR4/AR5 are well-established; AR6 N2O web-confirmed.

## Findings (need a human/scientific decision — left for Dave)

### F1 — AR6 CH4 GWP-100 = 27.9 does not match the canonical IPCC AR6 values
The dataset stores **27.9** for AR6 CH4 (100-yr). Independent check of IPCC AR6
WGI Ch. 7 gives **29.8 (fossil)** and **27.0 (non-fossil)** — 27.9 matches neither.
Possible explanations: a blended/generic figure, a no-carbon-cycle-feedback variant,
a draft value, or an error. **Action:** confirm the intended AR6 CH4 value and which
fossil/non-fossil convention the tool should expose (the engine already keys GWPs by
gas/AR/horizon, so a fossil-vs-non-fossil split is possible if desired).
Sources: IPCC AR6 WGI Ch.7 Supplementary Material; GHG Management Institute AR6
methane tables.


### F2 — Round-trips agree to within 0.1% (expected & healthy, not a defect)
A round-trip sweep (A->B->A over 423 connected pairs) finds residuals up to ~0.067%
(BTU<->Cal = 1.00067; Wh-family ~ 0.99996). **Per Dave this is expected and healthy:**
conversion and fuel-property factors legitimately differ slightly by fuel, source, and
rounded physical constants (e.g. BTU 1055.06 vs exact 1055.05585), so a perfect
round-trip to exactly 1 is neither expected nor required. The <0.1% agreement instead
demonstrates strong internal consistency. The engine multiplies stored factors exactly;
the round-trip regression test simply holds the 0.1% bound so a *much* larger drift —
which would indicate a real data problem — gets flagged. Coverage is otherwise clean:
0 isolated units, all 8 dimensions populated. **No action needed.**

## Still to verify (next QA passes)

- eGRID regional electricity factors against the published eGRID release.
- 20-yr and 500-yr GWP horizons.

## Forward — validating the automated data pipeline (world-class, cited)

The data is sourced/curated by Dave; post-launch it will be fed by an automation
workflow that pulls, cleans, and processes into the database. At that point the QA
here becomes the **ingest validation gate**, and the bar is world-class + citable:

1. **Provenance-complete** — every value carries source agency, document, table,
   version/vintage, and URL, so it is individually citable.
2. **Cross-checked at ingest** — incoming values auto-compared to authoritative
   primary sources (IPCC tables, NIST SP 811, EPA GHG EF Hub, eGRID); deviations are
   flagged, not silently accepted (this is exactly how F1 surfaced).
3. **Citation-grade resolution** — each value resolves to a specific citation and
   convention (e.g. *which* IPCC AR6 CH4 variant).
4. **Uncertainty-aware** — capture published uncertainty / data-quality tier.
5. **Change-detected** — diff each pull against the prior; surface value changes for
   human review before they reach the database.
6. **Schema-validated** — types, ranges, unit/dimension consistency, no NaN in
   critical columns.
7. **Reproducible & logged** — every ingest validation run recorded.

`tests/test_validation.py` (engine reproduces NIST/IPCC/EPA exactly) is the seed of
items 2–3; extend it into the pipeline gate when the automation lands.
