---
type: moc
status: current
generation: Claude
last_updated: 2026-05-25
tags: [moc, index, home]
---

# UnitGPS — Map of Content

Home page for the UnitGPS documentation vault. Every other page in `docs/` is linked from here. Treat this as the starting view in Obsidian.

> **Scope.** This vault documents the **Claude generation** of UnitGPS — the codebase under `D:\OneDrive\Civitas Systems\Projects\SustBrain\UnitGPS\v0.5-Claude\`. Older generations are archived under `00-Legacy Versions/` and `v0.4-Antigravity/`; the documentation pattern is designed to extend to them when/if they're formalized. See [[architecture#6. Build order]].

## How this vault is organized

- **[[#Concepts]]** — version-agnostic ideas. These are the load-bearing abstractions; read these first if you're new.
- **[[#Reference — Engine]]** — code-level walkthrough of every engine function. One page per function.
- **[[#Reference — Streamlit App]]** — code-level walkthrough of every UI module/function.
- **[[#Reference — Data]]** — schema documentation for the xlsx files.
- **[[#Tests]]** — what each test asserts and why.
- **[[Glossary]]** — every term used in this vault, defined once.

Design-intent ("why we built it this way", not function-level) lives at [[architecture]]. Pass-by-pass history lives at [[CHANGELOG]].

## Concepts (12 pages)

Abstractions you'd need to understand even if you reimplemented UnitGPS in another language.

- [[Unit graph]] — units as nodes, conversions as directed edges
- [[Reciprocal edges]] — why we synthesize inverse edges for emission factors but not unit conversions
- [[Shortest paths]] — how `networkx.all_shortest_paths` gives us conversion routes
- [[Ambiguous paths]] — what parallel edges mean and how the engine currently handles them
- [[Edge picks for ambiguous paths]] — end-to-end story of how a user's pick flows from UI to engine
- [[Temporal scope]] — the five Data Year filter modes (all, exact, range, recent_global, recent_edge)
- [[GHG emissions and GWP]] — routing CO₂/CH₄/N₂O independently and summing to CO₂e
- [[Hero pathway stepper]] — the subway-map design for visualising audit paths
- [[Audit card hybrid layout]] — Classification + Chemical + Attribution layout for step cards
- [[GHG condensed panel]] — how the GHG result panel went from 5 blocks to 3
- [[Portable results]] — export (JSON / Markdown) + bookmark URLs
- [[Network visualization]] — the full conversion graph with the active path overlaid

## Reference — Engine (16 pages)

`src/unitgps/engine/` — UI-agnostic computational core. Imports only pandas + networkx.

### `data.py`
- [[DataLoader]] — class overview
- [[DataLoader.load_data_library]]
- [[DataLoader.get_units_attributes]]
- [[DataLoader.load_gwps]]

### `graph.py`
- [[UnitGraph]] — class overview
- [[UnitGraph.filter_graph]] — the most complex engine function
- [[UnitGraph.get_nodes_by_dimension]]

### `pathfinding.py`
- [[identify_conversion_path]]
- [[convert_path_to_edge_tuples]]

### `calculate.py`
- [[AmbiguityError]] — reserved-but-unraised exception class
- [[format_sig_figs]]
- [[is_valid_parameter]]
- [[calculate_conversion_factor]] — audit report builder (now supports `edge_picks`)

### `emissions.py`
- [[find_gwp]]
- [[determine_conversion]] — wrapper for unit conversions (now supports `edge_picks`)
- [[determine_ghg_emissions]] — wrapper for CO₂e computation (now supports `edge_picks`)

## Reference — Streamlit App (30 pages)

`apps/streamlit_app/` — the user-facing UI, decomposed across themed modules. All UI rendering, none of it touches the engine internals.

### `app.py`
- [[app]] — the thin orchestrator script

### `themes.py`
- [[themes]] — module overview + the 13 theme dicts
- [[themes.get_theme]]
- [[themes.inject_css]]

### `state.py`
- [[state]] — module overview + `_DEFAULTS` (including `_edge_picks`)
- [[state.init_session_state]]
- [[state.on_start_change]]
- [[state.on_final_change]]
- [[state.make_sync_callbacks]]

### `filters.py`
- [[filters]] — module overview + `COLS_TO_EXTRACT` + `FILTER_GROUPS`
- [[filters.apply_db_and_temporal_filters]] — pandas mirror of `UnitGraph.filter_graph`
- [[filters.get_filtered_df]]
- [[filters.get_options]]
- [[filters.dynamic_multiselect]] — now auto-hides empty filters
- [[filters.get_units_for_dim]]
- [[filters.render_filter_tabs]]
- [[filters.render_active_filter_chips]] *(new)* — display-only chip strip of active filter selections
- [[filters.build_search_params]]

### `formatting.py`
- [[formatting]] — module overview
- [[formatting.format_html_num]]
- [[formatting.format_latex_num]]
- [[formatting.sanitize_latex]]
- [[formatting.format_audit_date]] *(new)* — YYYY-MMM-DD renderer
- [[formatting.normalize_param_value]] *(new)* — tidy numeric param strings

### `export.py`
- [[export]] *(new)* — JSON audit + Markdown report serializers

### `network_viz.py`
- [[network_viz]] *(new)* — matplotlib + NetworkX rendering of the full conversion graph, ported from v0.4-Antigravity

### `url_state.py`
- [[url_state]] *(new)* — URL ↔ session_state round-trip for bookmarkable configuration

### `renderers/`
- [[renderers - conversion]] — the Conversions result panel (now with hero stepper, two-col audit body, per-step edge picker, path tabs + comparison table)
- [[renderers - emissions]] — the GHG Emissions result panel (now condensed: total + horizontal bar + 3 compact cards + collapsed LaTeX derivation)
- [[renderers - stepper]] *(new)* — pure HTML/CSS hero pathway stepper

## Reference — Data (2 pages)

- [[Data Library schema]] — every column in the 3,635-row xlsx documented
- [[IPCC GWPs]] — sheet structure + `Indicator` splitting + GWP reference values

## Tests (1 page)

- [[Test suite]] — all 38 tests organized by module, what each asserts (was 30; 8 new tests for `edge_picks`)

## Page-status legend

Properties on each page use the `status` field with these values:

- `current` — accurate as of `last_updated`
- `draft` — being written, may be incomplete
- `stale` — known to be out of sync with code (fix or delete)
- `planned` — placeholder, no real content yet

## Vault inventory

| Section | Page count |
|---------|-----------|
| MOC + Glossary | 2 |
| Concepts | 12 |
| Reference — Engine | 16 |
| Reference — Streamlit App | 30 |
| Reference — Data | 2 |
| Tests | 1 |
| `architecture.md` (design doc) | 1 |
| **Total** | **65** |

## What changed in the v0.5-Claude rewrite

For readers coming from the [[../v0.4-Antigravity|v0.4-Antigravity]] generation, the docs marked *(new)* above reflect modules added in this rewrite:

- **stepper.py** — extracted hero pathway visualization into its own pure HTML/CSS module
- **formatting.format_audit_date / normalize_param_value** — shared formatters for audit cards
- **filters.render_active_filter_chips** — display-only summary of current filter selections
- **edge_picks** parameter on `calculate_conversion_factor` / `determine_conversion` / `determine_ghg_emissions` — sticky user choice for ambiguous parallel edges

The rewrite also collapsed the GHG panel from 5 stacked blocks (total + equation + table + donut + 3 per-gas sections) to 3 (total + horizontal stacked bar + 3 compact gas cards), and switched the audit body to a two-column Classification + Chemical layout with a single elegant attribution footer.

## 2026-05-30 additions & changes

**New top-level docs**
- [[METHODOLOGY]] — rigorous methods writeup: graph model, conversion math, GHG accounting, data sources, validation, **assumptions & limitations**.
- [[Roadmap to world-class]] — the engine-level gaps (uncertainty propagation, principled ambiguity policy, data-quality metadata) for a future awake design pass.
- [[QA_NOTES]] — how answers are validated (internal + independent external checks) and findings. **See finding F1: AR6 CH4 = 27.9 vs IPCC 29.8/27.0.**
- `DEPLOYMENT.md` (repo root) — Streamlit Community Cloud deploy guide.

**New reference / concept pages**
- [[Pathway-scoped filters]], [[shortest_path_edges]], [[shortest_paths_via_edge_set]].

**Changed (see [[CHANGELOG]] Passes 8–11)**
- The experimental pathway **Sankey was removed**; pages mentioning `render_pathway_sankey` are superseded. Network labels are now theme-aware.
- Filter **tabs → inline segmented control** (`render_filter_group`, `get_active_filter_groups`).
- One filter rule (infra-always / blank-excludes / blank-year-wildcard) replaced the old multi-rule logic in [[UnitGraph.filter_graph]].
- GHG result panel: transparent **Mass × GWP = CO₂e** table; LaTeX derivation removed as redundant.
