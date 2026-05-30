---
type: function
module: streamlit_app.renderers.emissions
file: apps/streamlit_app/renderers/emissions.py
lines: "1-261"
status: current
generation: Claude
last_updated: 2026-05-22
tags: [streamlit, renderer, emissions, ui-rendering]
related:
  - "[[app]]"
  - "[[renderers - conversion]]"
  - "[[determine_ghg_emissions]]"
  - "[[find_gwp]]"
  - "[[formatting.format_html_num]]"
  - "[[formatting.format_latex_num]]"
  - "[[formatting.sanitize_latex]]"
  - "`formatting.draw_path_graph` *(removed)*"
  - "[[GHG emissions and GWP]]"
---

# renderers/emissions.py — render_emissions_panel

Render the entire GHG Emissions result panel — header with active IPCC AR/horizon subtitle, total CO₂e metric, plugged-in LaTeX equation, per-gas summary table (with Mass + GWP + CO₂e columns) side-by-side with a donut chart of CO₂e contributions, and the conversion-pathway diagram. Single function module; this is its docs.

## Signature

```python
def render_emissions_panel(
    graph_engine,
    search_params: dict,
    source_unit: str,
    target_unit: str,
    gwps_data,
    theme: dict,
    sync_done: bool,
    gwp_report: str = "AR5",
    gwp_horizon: str = "100",
) -> None
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `graph_engine` | `UnitGraph` | Engine wrapper. |
| `search_params` | dict | From [[filters.build_search_params]]. |
| `source_unit` | str | E.g. `'mmBTU'`. |
| `target_unit` | str | E.g. `'kg'` (must be Weight). |
| `gwps_data` | DataFrame | From [[DataLoader.load_gwps]]. |
| `theme` | dict | Active theme. |
| `sync_done` | bool | Returned by [[renderers - conversion]] — whether the bidirectional input sync has already run. |
| `gwp_report`, `gwp_horizon` | str | IPCC Assessment Report (`AR4` / `AR5` / `AR6`) and time horizon (`20` / `100` / `500` years). Pulled from `st.session_state` via the selectors in [[app]]. |

## Output

None. Side effect: emits the entire Emissions result panel into the current Streamlit container.

## What gets rendered

```
🌍 GHG Emissions   IPCC AR5 · 100-year     ← active GWP assumption is visible
┌──────────────────────────────────────────────────────────┐
│ Total Carbon Footprint                                   │
│ 104.42 kg CO₂e                                           │
│                                                          │
│ Total CO₂e = CO₂ + (CH₄×GWP) + (N₂O×GWP)                 │ ← plugged-in LaTeX
│           = 103.69 + (0.011 × 28) + (0.0016 × 265)       │
│           = 104.42 kg CO₂e                               │
│                                                          │
│ ┌──── Table (3 cols) ────┐  ┌──── Donut (2 cols) ──┐     │
│ │ GHG │ Mass │ GWP │ CO₂e│  │      ╭───╮            │     │
│ │ CO₂ │103.7 │ 1   │103.7│  │     │ 104  │           │     │
│ │ CH₄ │0.011 │ 28  │0.31 │  │     │ kg CO₂e│         │     │
│ │ N₂O │0.0016│ 265 │0.42 │  │      ╰───╯            │     │
│ └────────────────────────┘  └─────────────────────┘     │
│ ─────────────────                                        │
│ Conversion Pathway                                       │
│ ┌────────┐  ┌──────┐  ┌────────┐                         │
│ │ mmBTU  │->│ ...  │->│   kg   │                         │
│ └────────┘  └──────┘  └────────┘                         │
└──────────────────────────────────────────────────────────┘
```

## High-level flow

```
1. Render header "🌍 GHG Emissions   IPCC <AR> · <horizon>-year"
   ← the subtitle makes the GWP assumption auditable from a screenshot.

2. If sync_done is False, do a base calc + update session_state per calc_direction.

3. Call determine_ghg_emissions with starting_value = session_state.start_val.

4. If valid_calc: render Total CO2e metric + plugged-in LaTeX equation.
   Else: "⚠️ Global calculation incomplete" warning.

5. Build the per-gas HTML table — 4 columns: GHG / Mass / GWP / CO2e.
   - Mass column shows raw emissions BEFORE GWP weighting (user-requested,
     critical for audit because anyone reading the result can see how much
     of each gas is being emitted, not just the CO2e total).

6. Build a donut chart (px.pie with hole=0.55) of per-gas CO2e contributions,
   with the total CO2e shown in the hole. Same color map as the table badges.

7. Render table (cols=3) and donut (cols=2) side-by-side in st.columns([3, 2]).

8. Render the Conversion Pathway diagram below, always visible (full width).
```

## Key design choices

### Header subtitle showing IPCC AR + horizon

```python
st.markdown(
    f"<h3 style='color: {theme['danger']} !important; margin-bottom: 0;'>🌍 GHG Emissions "
    f"<span style='font-size:0.6em; color:{theme['secondary']} !important; "
    f"font-weight:normal; vertical-align:middle;'>"
    f"IPCC {gwp_report} · {gwp_horizon}-year</span></h3>",
    ...
)
```

The IPCC report and horizon are USER-SWITCHABLE via selectboxes in [[app]] — defaults are AR5/100 but the user can pick AR4/AR5/AR6 × 20/100/500. Putting the active values in the header means anyone screenshotting the result can see which assumption produced it.

### Mass column in the table

```python
mass_val = details["Mass"]
mass_str = f"<b>{format_html_num(mass_val)}</b> {target_unit}"
```

Mass is the routed-but-not-yet-GWP-weighted result for each gas (from [[determine_ghg_emissions]]'s `results[ghg]['Mass']`). Showing it next to GWP and CO₂e makes the math obvious: `Mass × GWP = CO₂e`. Previously the panel showed only CO₂e, hiding the per-gas physical quantities.

### Donut instead of stacked bar

```python
fig = px.pie(df_chart, values="CO2e", names="GHG", color="GHG",
             hole=0.55, color_discrete_map=gas_colors)
fig.add_annotation(
    text=f"<b>{format_sig_figs(total_co2e, 4)}</b><br><span>{target_unit} CO₂e</span>",
    x=0.5, y=0.5, showarrow=False,
)
```

A pie/donut of 3 slices is much cleaner than a 3-color stacked bar of one category. The donut hole carries the total CO₂e — same data the metric card shows, reinforced visually.

### Table + donut side-by-side

```python
col_table, col_chart = st.columns([3, 2])
```

The table is information-dense; the donut is the visual summary. Placing them side-by-side lets the eye flow from row → slice. The 3:2 column ratio gives the table breathing room while keeping the donut readable.

### Per-gas color map

```python
gas_colors = {
    "CO2": theme["primary"],
    "CH4": theme["success"],
    "N2O": theme["danger"],
}
```

Same colors used in the table badges, the donut slices, and the Conversion Pathway diagram below. Reinforces "purple = CO₂, green = CH₄, red = N₂O" throughout the panel.

## Plugged-in LaTeX equation

The equation isn't a generic template — it shows the actual numbers being plugged in across 4 lines:

```latex
\begin{aligned}
Total CO₂e &= CO₂ + (CH₄ × GWP) + (N₂O × GWP)
           &= 103.69 + (0.011 × 28) + (0.0016 × 265)   [kg]
           &= 103.69 + 0.308 + 0.424   [kg CO₂e]
           &= 104.42   [kg CO₂e]
\end{aligned}
```

This is what makes the GHG panel auditable — every number is shown with its lineage.

## Logging

```python
logger.debug("GHG call source=%r target=%r start=%r valid=%s", ...)
```

Replaces Antigravity-era hard-coded debug-file writes — gone for good.

## See also

[[app]] · [[renderers - conversion]] · [[determine_ghg_emissions]] · [[find_gwp]] · [[formatting.format_html_num]] · [[formatting.format_latex_num]] · [[formatting.sanitize_latex]] · `formatting.draw_path_graph` *(removed)* · [[GHG emissions and GWP]]

## Updated 2026-05-30
The GHG panel now leads with a transparent **Mass × GWP = CO₂e** table
(`_render_ghg_calc_table`) — explicit per-gas math, comparable, with share bars and a
total. The dense per-gas cards moved into a collapsed "Per-gas pathway & provenance"
expander; an accessible/downloadable `st.dataframe` twin and a chart caption were added;
the redundant LaTeX "Show derivation" expander was removed. See [[GHG condensed panel]],
[[CHANGELOG]] 10.3 / 11.3 / 12.5.
