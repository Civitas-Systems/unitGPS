---
type: glossary
status: current
generation: Claude
last_updated: 2026-05-25
tags: [glossary, vocabulary]
---

# Glossary

Every domain term used in this vault, defined once. When you cite a term elsewhere, link here with `[[Glossary#Term]]`.

## A

### Ambiguity
A path step has more than one parallel edge connecting the same `(source, target)` pair. The engine defaults to picking edge 0 and flags the path with `is_ambiguous=True`; the user can override per step via [[Glossary#edge_picks|edge_picks]]. See [[Ambiguous paths]] · [[Edge picks for ambiguous paths]].

### Attribution footer
The single elegant line at the bottom of every (non-static) audit card that reads `🏛 EPA · GHG EF Hub v2025 · Released 2025-Jan-25 · Updated 2025-Aug-22`. Built by `_build_attribution` from the edge's `source` dict (with fallback to `parameters`). Dates always render YYYY-MMM-DD. See [[Audit card hybrid layout]].

### Audit card hybrid layout
The current step-card design: colored Set-type header bar + grouped two-column body (Classification + Chemical) + attribution footer. Called "hybrid" because it combines option B's structured key/value with option A's elegant attribution line. See [[Audit card hybrid layout]].

### Audit report
The dict structure returned by [[calculate_conversion_factor]] for each path: `{route, starting_value, conversion_factor, ultimate_value, audit_steps, is_ambiguous, ambiguous_details}`. Each step in `audit_steps` carries [[Glossary#chosen_edge_idx|chosen_edge_idx]] indicating which parallel edge supplied the multiplier.

### Assessment Report (AR)
An IPCC report cycle. The GWP file has GWPs for AR4 (2007), AR5 (2014), and AR6 (2021). See [[GHG emissions and GWP]].

## B

### Bookmark URL
A URL that encodes the user's current configuration via `st.query_params`. Opening it restores Source/Target units, modules, filters, theme, and GWP settings. Produced by the "🔗 Share / bookmark" popover. See [[Portable results]].

## C

### chosen_edge_idx
The 0-based index on each audit step telling the renderer which parallel edge was used as the primary value. Defaults to 0; overridden via [[Glossary#edge_picks|edge_picks]]. Surfaced in the [[Glossary#Edge picker|edge picker]] UI. See [[calculate_conversion_factor]].

### CO₂e — Carbon dioxide equivalent
Mass of CO₂ that would have the same global warming impact as some mixture of GHGs. Computed as `Σ (mass_i × GWP_i)`. See [[GHG emissions and GWP]].

### Chemical Properties
A `Set` value in the Data Library. Edges that encode intrinsic chemical attributes (e.g. density, heating value) used as conversion stepping-stones. Subject to chemical-only filters; see [[UnitGraph.filter_graph]].

## D

### Data Library
The main xlsx file at `Claude/data/Data Library, 2025-10-18, 1960-2023.xlsx`. 3,635 rows × 40 columns. Source of truth for every conversion edge. See [[Data Library schema]].

### Data Year
The vintage year of an emission factor or property. Critical because emission factors are revised annually. See [[Temporal scope]].

### Dimension
The physical quantity a unit measures (Energy, Length, Mass/Weight, Volume, Power, Time, Area, Logistics). Stored on each node in the [[Unit graph]] as `Unit Dimension`.

### Dimension centroid
The fixed 2D anchor position for a Dimension's cluster in the [[Network visualization]]. Each Dimension has a `Default Position` like Energy=(-3.5, 0.0) or Weight=(0.0, -3.5). Per-dimension spring layout arranges nodes around the centroid. See [[network_viz]].

### Dominant gas marker
The gold ★ rendered next to the per-gas card with the largest CO₂e contribution. Computed dynamically as `max(("CO2","CH4","N2O"), key=lambda g: results[g]["CO2e"] or 0)`. See [[GHG condensed panel]].

### Doubled-attribute trick
The CSS specificity pattern `[data-testid="X"][data-testid="X"]` that boosts a rule's specificity to (0,2,0) so it beats emotion-generated single-attribute rules. Used in [[themes.inject_css]] for the width cap. Without this trick the `max-width` on `stMainBlockContainer` was silently lost in Streamlit 1.57.

## E

### Edge
A conversion in the unit graph: `(denominator_unit, numerator_unit)` plus a `Value` and metadata. Multiple parallel edges between the same nodes are common.

### Edge picker
The inline `st.expander` rendered on every ambiguous step card (`⚡ N alternatives — using: EPA · 2025 · Anthracite`). Inside, an `st.radio` lets the user pick a different parallel edge. The pick persists in `st.session_state["_edge_picks"]` and feeds back into the next engine call. See [[Edge picks for ambiguous paths]].

### edge_picks
The `dict[tuple[str,str], int]` parameter on [[calculate_conversion_factor]] (and forwarded by [[determine_conversion]] / [[determine_ghg_emissions]]). Maps `(source, target)` → edge index for ambiguous steps. Out-of-bounds or negative indices clamp defensively. Default `None` preserves legacy "pick edge 0" behaviour. See [[Edge picks for ambiguous paths]].

### Emission Factor
A `Set` value. Mass of GHG emitted per unit of activity (e.g. kg CO₂ per mmBTU of coal). Not present in the graph by default — `include_emission_factors=True` on [[UnitGraph.filter_graph]] turns them on.

### Export (JSON / Markdown)
Two serializers in [[export|export.py]] that turn a Conversions or GHG result into a lossless JSON audit (`schema: unitgps-audit/v1`) or a human-readable Markdown report. Surfaced as `⬇ JSON audit` / `⬇ Markdown report` download buttons on each result panel. See [[Portable results]].

### eGRID
EPA's Emissions & Generation Resource Integrated Database. A regional electricity-grid identifier appearing as a filter column.

## G

### GHG — Greenhouse gas
A gas that traps heat. UnitGPS routes CO₂, CH₄, and N₂O by default; the GWP file covers ~400 species across AR4–AR6.

### GHG condensed panel
The 3-block GHG result layout (total CO₂e headline + horizontal stacked bar + 3 compact per-gas cards). Replaces the old 5-block layout (total + LaTeX + table + donut + 3 sections). LaTeX derivation tucked behind "Show derivation" expander. See [[GHG condensed panel]].

### GWP — Global Warming Potential
The relative warming a gas causes compared to CO₂ over a chosen time horizon (20, 100, or 500 years). CO₂ has GWP = 1 by definition. See [[find_gwp]].

## H

### Hero pathway stepper
The horizontal subway-map visualization at the top of the Conversions result panel. Unit nodes are cards with symbol + dimension subtitle; edges show multiplier + Set-colored badge (gray static / green chemical / red emission). Pure HTML/CSS — lives in `renderers/stepper.py`. See [[Hero pathway stepper]] · [[renderers - stepper]].

### Horizontal stacked bar
The CO₂e contribution visualization in the GHG panel — a horizontal bar split into colored segments per gas, proportional to share. Replaces the donut chart, which was unreadable when CO₂ dominates at 99%+. Tiny segments enforce `min-width: 14px` so they stay visible. See [[GHG condensed panel]].

### Hydration (URL state)
Reading the URL's query params at app startup and populating `st.session_state` from them, before any widget renders. Lets a bookmark URL restore the user's full configuration on reload. See [[url_state]].

## M

### Magnitude Adjustment
A `Set` value covering metric-prefix scaling (kJ ↔ J = 1000, kg ↔ g = 1000, etc.). Treated as static infrastructure — always retained by filtering. See [[Temporal scope]].

### MultiDiGraph
NetworkX's directed graph that allows multiple parallel edges between the same pair of nodes. The natural data structure for UnitGPS because the same conversion often has multiple sources. See [[Unit graph]].

## N

### Master layout
The `{node: (x, y)}` dict mapping every unit to its 2D position in the [[Network visualization]]. Computed once per session by `compute_styled_graph_and_layout` via spring-around-fixed-dimensions, cached via `st.cache_resource`. Subsequent renders reuse the cached layout.

### Network view
The matplotlib + NetworkX rendering of the full conversion graph with the active path(s) highlighted. Available via "🌐 Show network view" expander on the Conversions panel and "🌐 Show GHG network view" on the GHG panel. See [[Network visualization]] · [[network_viz]].

### Node
A unit in the graph (`"kg"`, `"J"`, `"mmBTU"`, etc.). Attributes: `Unit Dimension`, `Unit System`, `Color`.

### Numerator / Denominator
Every Data Library row reads as `Value × (Denominator → Numerator)`. So a row with `Numerator=kg, Denominator=mmBTU, Value=103.69` says *one mmBTU yields 103.69 kg* of the substance described by the rest of the row.

## P

### Path comparison table
The small summary table rendered above the path tabs when more than one valid path exists. Columns: Route, Multiplier, Steps, Set-kind breakdown. The ⚡ marker flags ambiguous paths. Helps the user pick which tab to inspect. See [[renderers - conversion]].

### Portable results
The export + URL-state combination that takes a calculation out of the running app. JSON for archival, Markdown for human consumption, URL for repeat / share. See [[Portable results]].

## R

### Reciprocal edge
The mathematical inverse of a conversion edge. The engine synthesizes these for emission factors and chemical properties (so the graph is bidirectional) but NOT for unit conversions (which are already bidirectional in the source data). See [[Reciprocal edges]].

## S

### Set
The category column on each Data Library row. Values: `Unit Conversion`, `Magnitude Adjustment`, `Emission Factors`, `Chemical Properties`, `Global Warming Potentials`. Drives filtering behavior in [[UnitGraph.filter_graph]].

### Shortest path
The minimum-edge path between two nodes in the unit graph. Found via `networkx.all_shortest_paths`. See [[Shortest paths]].

### Source-vs-standardized chemical
The convention where each chemical row in the audit card shows the standardized name as the primary value (e.g. `Coal and Coke`) and the original source-dataset string (e.g. `Source-Chemical Category`) as an italic subtitle — but only when the two strings differ. Identical pairs render silent so the audit stays uncluttered. See [[Audit card hybrid layout]].

### Source-Chemical Type / Category
Filter columns identifying *what* an emission factor is for (e.g. Anthracite, Bituminous, Natural Gas). Important: these only apply to Chemical-property edges; non-chemical edges ignore them.

### Static step
An audit step whose Set is `Unit Conversion`, `Unit Conversions`, or `Magnitude Adjustment`. Renders header-only — no body — because there are no parameters or external source to attribute. See [[Audit card hybrid layout]].

## T

### Time Horizon
The GWP integration window: 20, 100, or 500 years. Different time horizons give different GWPs for the same gas (CH₄ is 84 over 20 years, 28 over 100, 7 over 500 — methane is more potent short-term).

## U

### Unit Conversion
A `Set` value covering static unit-to-unit conversions (BTU ↔ J, ft ↔ m, etc.). Treated as static infrastructure — never filtered out, never reciprocated (already bidirectional in source).

### UnitGraph
The wrapper class around the `networkx.MultiDiGraph`. See [[UnitGraph]].

## W

### WCAG contrast
Web Content Accessibility Guidelines luminance-ratio thresholds. AA normal text = 4.5:1; AA large text / UI elements = 3:1; AAA normal text = 7:1. The theme audit (Pass 3.1) checks every theme's text/bg, secondary/bg, text/surface, and border/bg pairs against these. See [[themes]].
