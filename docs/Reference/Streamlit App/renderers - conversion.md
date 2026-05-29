---
type: function
module: streamlit_app.renderers.conversion
file: apps/streamlit_app/renderers/conversion.py
lines: "1-227"
status: current
generation: Claude
last_updated: 2026-05-22
tags: [streamlit, renderer, conversion, ui-rendering]
related:
  - "[[app]]"
  - "[[renderers - emissions]]"
  - "[[determine_conversion]]"
  - "`formatting.build_math_latex` *(removed)*"
  - "`formatting.draw_path_graph` *(removed)*"
  - "[[state.on_start_change]]"
  - "[[Ambiguous paths]]"
---

# renderers/conversion.py — render_conversion_panel

Render the entire Conversions result panel — header, output metric card, side-by-side Pathway + Math views, and the per-step audit expander showing source provenance. Single function module.

## Signature

```python
def render_conversion_panel(
    graph_engine,
    search_params: dict,
    source_unit: str,
    target_unit: str,
    theme: dict,
) -> bool
```

## Output

A `bool` — `True` if the calculation succeeded AND the renderer updated `session_state.start_val` or `final_val` via [[Ambiguous paths|calc_direction]] logic. The caller passes this as `sync_done` to [[renderers - emissions|render_emissions_panel]] so the GHG panel doesn't repeat the sync.

## What gets rendered (per result path)

```
🔄 Conversions
  Found N path(s). Displaying top M.

  ── Path 1 ──────────────────────────────────────
  ┌─────────────────────────────────────────────────┐
  │ Output                                          │
  │ 1000 J  (calculated multiplier: ×1000)          │
  │                                                 │
  │ ┌──── Pathway ─────┐  ┌──── Math ────────────┐  │
  │ │                  │  │                      │  │
  │ │ kJ ─[Magnitude]─ │  │ 1 kJ × (1000 J/kJ)  │  │
  │ │     → J          │  │  = 1000 J            │  │
  │ │                  │  │                      │  │
  │ └──────────────────┘  └──────────────────────┘  │
  │                                                 │
  │ ▸ Audit Details — sources & provenance          │
  │   Step 1: kJ ➔ J · Multiplier: ×1000 · Set: …   │
  │     Parameters chips: GHG, Chemical Type, …     │
  │     Source chips: Agency, Dataset, Year, …      │
  └─────────────────────────────────────────────────┘
```

## Design — three views that each earn their place

| View | Shows | Doesn't show (lives elsewhere) |
|------|-------|--------------------------------|
| **Output metric** | The answer, big | The chain of factors |
| **Pathway** (Graphviz, left half) | Topology — which units, which `[Set]` at each step | The numeric value of each step (deliberately stripped) |
| **Math** (LaTeX, right half) | The multiplication chain with values | What kind of edge each factor came from |
| **Audit expander** | Per-step Agency / Dataset / Year / Version + Parameters | The numeric output (already shown above) |

The Pathway and Math used to duplicate each other — both showed the conversion factor. Now Pathway uses `label_mode="set_only"` (see `formatting.draw_path_graph` *(removed)*) so it only labels each edge with the `[Set]` name, while the LaTeX shows the actual numbers. They become complementary.

## High-level flow

```
1. Header + path count.
2. For each surviving path (up to max_paths):
   a. Output metric card (value + unit + multiplier + ambiguity warning if any)
   b. Side-by-side st.columns([1, 1]):
        LEFT — Graphviz pathway with label_mode='set_only'
        RIGHT — LaTeX equation from build_math_latex
   c. Audit expander showing per-step Sources & Parameters as chips
3. Return sync_done = True iff calc succeeded.
```

## Key implementation choices

### Pathway / Math side-by-side

```python
col_path, col_math = st.columns([1, 1])
with col_path:
    st.markdown("<div class='small-caps'>Pathway</div>", ...)
    st.graphviz_chart(draw_path_graph(audit_steps, theme, primary, label_mode="set_only"))
with col_math:
    st.markdown("<div class='small-caps'>Math</div>", ...)
    st.latex(build_math_latex(...))
```

50/50 column split. Streamlit reflows on narrow viewports; on standard desktop both views fit comfortably.

### `label_mode="set_only"` to deduplicate

```python
draw_path_graph(audit_steps, theme, theme["primary"], label_mode="set_only")
```

With this mode the Graphviz edge labels show only `[Magnitude Adjustment]` (or whatever Set is at that step) — no `× 1000` prefix. The LaTeX panel next to it shows the actual numbers. Each view contributes information the other doesn't.

### Enhanced audit expander

```python
# Per-step:
#   - The basic "source ➔ target | Multiplier | Set" line (unchanged)
#   - Chip row: Parameters (GHG, Chemical Type, Country, etc.)
#   - Chip row: Source (Agency, Dataset, Data Year, Version, Updated)
```

Each chip is small, rounded, and labeled. Parameters chips have lighter backgrounds; source chips use the surface color. Makes the per-step provenance scannable instead of buried in a flat string.

The chip data comes from the audit step's `edge['parameters']` and `edge['source']` dicts that [[calculate_conversion_factor]] populates. Previously visible only by inspecting the engine output programmatically; now shown inline.

### Forward / backward calc direction

```python
if st.session_state['calc_direction'] == 'forward':
    st.session_state['final_val'] = st.session_state['start_val'] * factor
else:
    st.session_state['start_val'] = st.session_state['final_val'] / factor if factor else 0.0
```

Two-way input handling — same as before. See [[state.on_start_change]] / [[state.on_final_change]].

### Ambiguity warning

```python
if data.get("is_ambiguous"):
    ambiguity_warn = "<div ...>⚠️ <b>Ambiguous Pathway</b>: ...</div>"
```

Amber border + amber text. Hex value `#ffcc00` hard-coded so amber looks like amber across every theme.

## Logging

```python
logger.debug("Conversion call source=%r target=%r status=%s", ...)
```

Replaces Antigravity-era hard-coded `C:\Users\davel\.gemini\...` debug-file writes — gone for good.

## See also

[[app]] · [[renderers - emissions]] · [[determine_conversion]] · `formatting.build_math_latex` *(removed)* · `formatting.draw_path_graph` *(removed)* · [[state.on_start_change]] · [[Ambiguous paths]] · [[calculate_conversion_factor]]
