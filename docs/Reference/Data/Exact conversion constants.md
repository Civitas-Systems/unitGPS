---
type: reference
status: current
generation: Claude
last_updated: 2026-05-30
tags: [reference, data, precision, constants]
---

# Exact conversion constants (precision reference)

UnitGPS validates to <0.1% ([[QA_NOTES]] F2), which is expected and healthy — real
conversion/fuel factors differ slightly by source. If you want **bit-exact** constants,
they belong in the **data source / pipeline** (the engine multiplies whatever the data
stores; precision lives in the data, not the code). This page lists the authoritative
values so the pipeline can standardise on them. The one genuine decision is **which BTU
definition** to use — that's yours.

## Energy

| Quantity | In data | Exact authoritative | Notes / source |
|----------|---------|---------------------|----------------|
| BTU → J  | 1055.06 | **1055.05585** (IT) · 1054.350 (thermochemical) · 1055.87 (BTU₃₉°F) | NIST SP 811. The stored 1055.06 ≈ IT BTU rounded. **Choose one definition and apply consistently.** |
| cal → J  | 4.184   | **4.184** (thermochemical, exact by definition) · 4.1868 (IT) · 4.1855 (15 °C) | thermochemical calorie is exact |
| kWh → J  | 3.6×10⁶ | **3 600 000** (exact) | SI (1 Wh = 3600 J) |
| eV → J   | —       | 1.602176634×10⁻¹⁹ (exact, 2019 SI) | if ever added |

## Length / mass / volume (international definitions, all exact)

| Quantity | Exact authoritative | Source |
|----------|---------------------|--------|
| in → m   | 0.0254              | international inch |
| ft → m   | 0.3048              | international foot |
| mi → m   | 1609.344            | international mile |
| lb → kg  | 0.45359237          | international avoirdupois pound |
| oz → kg  | 0.028349523125      | = lb/16 |
| gal (US) → m³ | 0.003785411784  | US liquid gallon (231 in³) |
| L → m³   | 0.001               | exact |

## GWPs

Already match IPCC exactly for AR4/AR5/AR6 (CO₂ 1; CH₄ 25/28/27.9; N₂O 298/265/273),
**except** the AR6 CH₄ = 27.9 choice — see [[QA_NOTES]] F1 (IPCC AR6 gives 29.8 fossil /
27.0 non-fossil).

## Recommendation

Apply exact constants at the **data-source/pipeline** level, not a one-off xlsx edit
(the pipeline would overwrite it). Standardise the BTU definition first; the rest are
unambiguous. Net numerical change is <0.1%, but it makes every value citation-exact —
which is the right bar for academic use.

References: NIST Special Publication 811 (2008 ed.); BIPM SI Brochure (9th ed., 2019).
