---
type: concept
status: current
generation: Claude
last_updated: 2026-05-23
tags: [concept, ui, audit, design]
related:
  - "[[renderers - conversion]]"
  - "[[calculate_conversion_factor]]"
---

# Audit card hybrid layout (B + A)

How each step in a Conversions audit gets rendered: a colored Set-type header bar, then a two-column body (Classification + Chemical) with an elegant attribution footer line at the bottom.

## Anatomy

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 2/4   mmBTU → ton  ·  × 0.039857  ·  🧪 Chemical Properties │  ← header (green left border)
├─────────────────────────────────────────────────────────────────┤
│ Classification              Chemical                              │
│   Scope        1              Chemical1   Coal and Coke           │
│   Category     Stationary…    Chemical2   Anthracite              │
│   Asset        Building                                            │
│   Property     Heat Content                                        │
│                                                                    │
│   🏛 EPA · GHG EF Hub v2025 · Released 2025-Jan-25 · Updated 2025-Aug-22 │  ← attribution
└─────────────────────────────────────────────────────────────────┘
```

## The "hybrid" name

Three layout options were on the table:

| Option | Style | Best for |
|--------|-------|----------|
| A | Chip strip (all params as colored pills) | 3–4 short facts |
| B | Two-column key/value (labels + values) | Many varied-length params |
| C | Hero identity + collapsible detail | Casual viewers only |

The shipped design is "B with A's footer": **B's structure** (labeled rows in two columns) plus **A's attribution footer** (one elegant line with agency + dataset + dates). The right column ("Source" in pure-B) was killed because its data is short — folding it into a horizontal footer line saves a whole column of vertical space and removes the dead-air problem.

## Two-column conditional grid

```python
if classification_rows and chemical_rows:
    body_inner = (
        f"<div style='display: grid; grid-template-columns: 1fr 1fr; "
        f"gap: 24px; align-items: start;'>"
        f"<div>{classification_html}</div>"
        f"<div>{chemical_html}</div>"
        f"</div>"
    )
else:
    body_inner = f"{classification_html}{chemical_html}"
```

When both sections have content → 1fr 1fr split. When only one side has data → single column so the empty side doesn't waste space.

## Source-vs-standardized chemical handling

Each chemical row can show two strings:

```
Chemical1   Biomass Fuels — Liquid       ← standardized name (primary)
            source: Biomass Fuels - Liquid  ← original source-dataset string (italic subtitle)
```

The italic `source: …` subtitle appears **only when the source string differs from the standardized name**. Identical pairs render silent — no noise when the two strings happen to match.

## Static-step exception

Steps where Set is `Unit Conversion`, `Unit Conversions`, or `Magnitude Adjustment` get **no body at all** — the header bar carries the whole step (set name + multiplier are already in the header). The shell exception preserves consistent visual rhythm across the audit stack while not adding empty bodies for static steps that have no params or source.

## Implementation

[[renderers - conversion|conversion.py]] holds the helpers:
- `_split_audit_params(params, sources)` — buckets params into Classification / Chemical (with source-pair detection)
- `_build_attribution(sources, params)` — single elegant attribution string
- `_grouped_section_html(...)` / `_chemical_section_html(...)` / `_attribution_footer_html(...)` — render each piece
- `_render_step_card(step, theme, step_num, total_steps, path_idx)` — orchestrator

## See also

[[renderers - conversion]] · [[calculate_conversion_factor]]
