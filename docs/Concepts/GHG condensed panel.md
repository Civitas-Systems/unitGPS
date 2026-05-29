---
type: concept
status: current
generation: Claude
last_updated: 2026-05-23
tags: [concept, ui, ghg, design]
related:
  - "[[renderers - emissions]]"
  - "[[determine_ghg_emissions]]"
  - "[[Hero pathway stepper]]"
---

# GHG condensed panel

How the GHG Emissions result panel went from five stacked blocks to three.

## Before vs after

| Block | Before | After |
|-------|--------|-------|
| Total CO₂e headline | ✓ | ✓ |
| LaTeX derivation equation | always visible | tucked behind "Show derivation" `st.expander` (default closed) |
| Per-gas table (Mass / GWP / CO₂e) | standalone table block with own white background | **gone** — fields folded into each gas card |
| Donut chart | always visible | **gone** — replaced with horizontal stacked bar |
| Per-gas pathway + step cards | three full sections (hero stepper + step cards repeated per gas) | three one-row compact cards with route summary + EF context + provenance |

Five visual blocks → three (total + bar / cards / disclosed equation). Vertical height roughly cut in half.

## Why the donut had to go

Donut charts fail when one slice eats >90% of the circle. Combustion emissions are CO₂-dominant (typically 99%+); the donut showed a near-complete purple ring with two slivers too small to see, communicating less information than a one-line "CO₂ 99.3%" caption would.

A horizontal stacked bar (`_render_horizontal_stacked_bar` in [[renderers - emissions]]) keeps proportional widths but enforces a `min-width: 14px` per segment, so the tiny CH₄ and N₂O slivers stay visible even when their percentages are sub-1%. Inline labels appear when the segment is wide enough (≥12%); a legend below carries the precise percentages always.

## Why the table folded into cards

The standalone GHG table duplicated information that the per-gas cards were about to show again. Each card now carries a thin metrics row at the top of its right column:

```
Mass  9.83×10⁻⁸ kg  ·  GWP  1  ·  CO₂e  9.83×10⁻⁸ kg
```

So the table block can disappear entirely. Saves ~150px of vertical space and removes the white-table-on-page contrast distraction.

## Dominant ★ marker

The card with the highest CO₂e contribution (computed as `max(("CO2","CH4","N2O"), key=lambda g: results[g]["CO2e"] or 0)`) gets a gold ★ before its gas badge. Visual reinforcement of the data story: "this is the gas that matters here."

## Static-step footnote

A typical CH₄ path looks like `J → Wh → MWh → kg` — three steps: unit conversion, magnitude adjustment, emission factor. Showing all three as full step cards across all three gases is redundant noise. The compact card collapses static steps into a tiny footnote: `J → Wh → MWh → kg (+ 1 unit conv, 1 magnitude)`. The emission-factor step is the interesting one; the EF line and provenance carry its details.

## See also

[[renderers - emissions]] · [[determine_ghg_emissions]] · [[Hero pathway stepper]] · [[Audit card hybrid layout]]
