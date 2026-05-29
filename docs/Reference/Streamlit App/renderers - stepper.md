---
type: module
module: streamlit_app.renderers.stepper
file: apps/streamlit_app/renderers/stepper.py
status: current
generation: Claude
last_updated: 2026-05-23
tags: [ui, renderer, stepper, pathway, visualization]
related:
  - "[[renderers - conversion]]"
  - "[[renderers - emissions]]"
  - "[[Hero pathway stepper]]"
---

# renderers - stepper

The hero pathway stepper module. Pure HTML/CSS generator — no Streamlit dependency, fully unit-testable. Renders an audit path as a subway-map visualization with color-coded edges per Set kind.

## Module shape

```python
"""Hero pathway visual stepper."""

# Public:
def render_hero_stepper(
    audit_steps: List[dict],
    dim_lookup: Callable[[str], str],
    theme: dict,
    label: str = "Pathway",
) -> str

# Private helpers:
def _classify_set(set_name: str) -> str            # static/chemical/emission/other
def _set_color(set_kind: str, theme: dict) -> str   # theme color for the kind
def _set_short_label(set_kind: str, set_name: str) -> str  # short edge badge label
def _node_html(unit: str, dim: str, theme: dict) -> str    # one unit-node card
def _edge_html(value: float, set_name: str, theme: dict) -> str  # one labeled edge
```

## render_hero_stepper

| Param | Type | Description |
|-------|------|-------------|
| `audit_steps` | `list[dict]` | Per-step audit output from [[calculate_conversion_factor]]. Each step's `source`/`target`/`edges[0].value`/`edges[0].set` is read. |
| `dim_lookup` | `Callable[[str], str]` | Unit-name → dimension-string resolver. Caller supplies a closure over `graph_engine.G.nodes[u]["Unit Dimension"]`. |
| `theme` | `dict` | Active theme dict. The `bg`, `surface`, `border`, `text`, `secondary`, `primary`, `success`, `danger` keys are read. |
| `label` | `str` | The small uppercase heading rendered above the stepper. Defaults to `"Pathway"`. The GHG per-gas section overrides this with e.g. `"CO2 pathway"`. |

Returns the full HTML string. Caller does `st.markdown(html, unsafe_allow_html=True)`.

## How sets map to colors

```python
def _classify_set(set_name: str) -> str:
    if set_name in ("Unit Conversion", "Unit Conversions", "Magnitude Adjustment"):
        return "static"
    if set_name == "Chemical Properties":
        return "chemical"
    if "emission" in set_name.lower():
        return "emission"
    return "other"
```

Then `_set_color()` resolves to `theme['secondary']` / `theme['success']` / `theme['danger']` / `theme['primary']` respectively. Consistent palette ensures the stepper recolors automatically with theme changes — no hardcoded hex.

## Layout choices

- `display: flex; align-items: stretch` on the container — node and edge children fill the same height
- Unit nodes are `flex: 0 0 auto; min-width: 78px` so they never collapse
- Edges are `flex: 1 1 0; min-width: 110px` so they expand to fill space proportionally
- Edge content uses `position: relative; z-index: 1` with `background: {theme['bg']}` to "punch through" the colored line behind it
- Container has `overflow-x: auto` so long paths scroll horizontally rather than wrap

## Why decoupled from Streamlit

Returns a string instead of calling `st.markdown()` directly so:
- Smoke tests can run without a Streamlit runtime
- The output can be inspected and asserted in pytest
- The same generator could feed an HTMX or static export variant later

## See also

[[renderers - conversion]] · [[renderers - emissions]] · [[Hero pathway stepper]]
