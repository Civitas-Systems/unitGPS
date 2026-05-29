---
type: concept
status: current
generation: Claude
last_updated: 2026-05-23
tags: [concept, ui, pathway, visualization]
related:
  - "[[renderers - stepper]]"
  - "[[renderers - conversion]]"
  - "[[renderers - emissions]]"
  - "[[Unit graph]]"
---

# Hero pathway stepper

A subway-map style visualization that renders any audit path as a horizontal sequence of unit-node cards connected by color-coded edge labels. Replaces the older flat `J → mmBTU → kg` text breadcrumb.

## Anatomy

```
┌──────┐  × 9.48e-10        ┌────────┐  × 0.0399       ┌─────┐
│  J   │────────────────────│ mmBTU  │─────────────────│ ton │  ...
│Energy│  🔧 Unit conv      │ Energy │  🧪 Chemical    │Wt   │
└──────┘                    └────────┘                 └─────┘
```

- **Unit nodes** are cards: monospace symbol on top, dimension subtitle (uppercase, secondary color) beneath.
- **Edges** are colored lines with a "punch-through" label pill in the panel background showing multiplier + set badge.
- **Color encodes Set kind**:

| Set kind | Color (uses theme key) | Icon |
|----------|-----------------------|------|
| Unit Conversion / Magnitude Adjustment | `theme['secondary']` (gray) | 🔧 |
| Chemical Properties | `theme['success']` (green) | 🧪 |
| Emission Factor | `theme['danger']` (red) | 🌫 |
| Other | `theme['primary']` (purple) | • |

Colors are looked up in the active theme dict so the stepper recolors with theme changes.

## Why this layout

Three problems with the legacy text breadcrumb:

1. **Step kinds invisible.** A long chain looked the same whether it was 3 unit conversions or 3 emission factors. The colored edges make the kind read at a glance.
2. **Multiplier and Set both hidden.** Reading the breadcrumb told you the route but not the math or attribution — those lived in nested expanders.
3. **No spatial sense of "how far".** Five steps stacked vertically as text felt linear-and-tall; horizontal flow with proportional spacing feels like a journey.

## Implementation

Lives in [[renderers - stepper|stepper.py]] as a pure HTML/CSS generator — no Streamlit dependency. The caller (Conversions panel, GHG per-gas section) does `st.markdown(html, unsafe_allow_html=True)`. The function takes a `dim_lookup` callable so it can resolve unit dimensions without coupling to the graph engine type.

Key sizing choices:
- `min-width: 78px` per unit node so symbols never clip
- `min-width: 110px` per edge so multiplier + badge fits
- `overflow-x: auto` on the container so long paths scroll horizontally rather than wrap

## Where it appears

- **Conversions panel** — once per path (or once per tab when multiple paths exist)
- **GHG Emissions panel** — *not* in the new condensed layout. The per-gas summary cards have a one-line route string instead; the hero stepper would be too much repetition across CO₂/CH₄/N₂O.

## See also

[[renderers - stepper]] · [[renderers - conversion]] · [[renderers - emissions]] · [[Unit graph]]
