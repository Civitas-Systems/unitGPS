---
type: changelog
status: current
generation: Claude
last_updated: 2026-05-30
tags: [changelog, history, passes]
---

# CHANGELOG

A pass-by-pass record of what changed during the v0.5-Claude generation. Newest first.

## Pass 11 — Hardening, accessibility & deploy prep (2026-05-30)

- **11.1 Readable network-path labels.** The network view's path node labels were a hard-coded light grey (invisible on light themes); they now use the active theme's text colour so the units (e.g. `mmBTU -> ton -> g -> kg`) are legible on any theme and cross-reference against the step list. The static (matplotlib) render also stopped labelling *every* node — only the highlighted path + dimension names are labelled, so the path isn't buried. See [[Network visualization]], [[network_viz]].
- **11.2 Reachability-scoped Source/Target pickers.** (See Pass 10.7 / [[Pathway-scoped filters]].)
- **11.3 Accessibility.** Keyboard focus ring (`:focus-visible`), `prefers-reduced-motion` support, descriptive captions (alt-text) under the network charts, and an accessible, downloadable `st.dataframe` twin of the GHG calc table.
- **11.4 Deploy prep + dependency fixes.** Added a root `requirements.txt` and `.streamlit/config.toml`; declared **matplotlib** (used by the Static render but previously undeclared) and bumped the Streamlit floor to `>=1.40` (for `st.segmented_control`). New beginner guide `DEPLOYMENT.md`; README stats refreshed.
- **11.5 Repo hygiene + CI.** Added `.gitattributes` (line-ending normalization — kills the recurring `.spec` CRLF churn) and a GitHub Actions workflow running the engine test suite on every push. Three new tests pin the single-rule `filter_graph` behaviour. **47 tests pass.**

## Pass 10 — Finalization: card UI + transparent GHG (2026-05-30)

- **10.1 Group delineation + section headers.** `st.container(border=True)` panels now read as real cards (surface fill + theme-appropriate elevation that survives light themes, where surface ≈ background). Section headers (Source / Target / Modules / Temporal Scope / Output options / Database Filters) gained a bolder, larger style with a primary accent bar and a hairline rule. Targeting note: the bordered container carries no inline `border` style, so cards are matched via a `.ug-card-head` marker + `:has()`. See [[themes]].
- **10.2 Inline Database Filters toolbar.** Replaced the filter **tabs** with an inline `st.segmented_control` in the header row — `Database Filters · [Resources][Process][Location][Data Source] · Calculate` on one line, chosen category's filters full-width below. Refactor in `filters.py`: `render_filter_tabs` split into [[filters.get_active_filter_groups]] + [[filters.render_filter_group]]; the non-selected groups still mount inside a `display:none` container so multiselect state persists across category switches.
- **10.3 Transparent GHG calculation.** New `_render_ghg_calc_table` shows each gas as the equation it is — **Mass × GWP = CO₂e** — aligned side-by-side with share bars and a total, so the footprint is visible rather than trusted. The dense per-gas pathway/provenance cards moved into a collapsed expander. See [[GHG condensed panel]], [[renderers - emissions]].
- **10.4 Sankey dropped.** The experimental pathway Sankey (added in Pass 9) drew every link at uniform width, so it carried no quantity — removed entirely (the Diagram radio, both renderers' branches, and `render_pathway_sankey`/`_hex_to_rgba` in `network_viz.py`). Output options is now just Max paths · Network render (Interactive/Static) · Colour-blind-safe.
- **10.5 Theme contrast pass.** Objective WCAG audit of all 13 themes. Fixed the unreadable Share-link **popover** button (black-on-dark ~1.2:1 → themed outline), darkened Earthy Zen's terracotta labels (3.3 → ~4.8:1), gave Neo-Brutalism a dark section accent (pink was 1.3:1 on yellow). Max-paths dropdown width capped.
- **10.7 Reachability-scoped Source/Target pickers.** The Source/Target dimension *and* unit dropdowns now use the same dimension-reachability scoping as the Database Filters (`dimension_reach` in `filters.py`): the target only offers dimensions/units a source can reach (Area -> Area only); under GHG (target = Weight) the source only offers dimensions that can reach Weight. See [[Pathway-scoped filters]].
- **10.6 Zero-value guard.** A `0` starting value now shows a hint instead of silently emitting all-zero results. Layout: tightened the Temporal↔Output column spacing. 44/44 tests pass.

## Pass 9 — Interactive output visualization (2026-05-29)

- **9.1 Plotly network.** Added `render_network_plotly` — hover/zoom/pan version of the network view with per-dimension "region bubble" shapes. A **Network render: Interactive / Static** toggle (`viz_mode`) picks Plotly vs the matplotlib image.
- **9.2 Colour-blind-safe GHG palette.** `ghg_palette(colorblind)` + a Colour-blind-safe toggle swap the green/red gas pair for blue/orange/purple. One palette drives the bar, table and network overlay.
- **9.3 Interactive GHG bar.** `_render_ghg_bar_plotly` complements the static HTML stacked bar. (An experimental pathway Sankey was also added here and later removed — see Pass 10.4.)

## Pass 8 — Engine + filter-logic overhaul (2026-05-29)

- **8.1 One filter rule.** Rewrote [[UnitGraph.filter_graph]] (and its pandas mirror [[filters.apply_db_and_temporal_filters]]) to a single rule: **infrastructure (Unit Conversions / Magnitude Adjustments) always passes; every other edge must strictly match each selected filter, where a blank value EXCLUDES; Data Year treats a blank year as a wildcard.** Replaced the old per-rule Unit-Conversion exemption + Chemical-Properties carve-out. Fixes electricity pathways offering Anthracite, eGRID not partitioning out fuels, etc.
- **8.2 Pathway-scoped filter options.** New `apply_pathway_scope` + `_dimension_reach` scope the filter *dropdowns* to the source→target **dimensional** pathway (keep every unit of any reachable dimension, not just units with a literal edge). See [[Pathway-scoped filters]].
- **8.3 GHG must traverse an emission factor.** New [[shortest_paths_via_edge_set]] (+ [[shortest_path_edges]]) constrains GHG routes through a real EF edge via `_is_emission_factor_edge`, so a gas can't report a non-emission unit conversion. [[determine_ghg_emissions]] updated.
- **8.4 Robustness + layout.** `calculate_conversion_factor` returns `[]` (not `None`) on empty input; `data.py` drops zero-value rows before reciprocal inversion. Controls moved to a 3-column layout (Modules | Temporal Scope | Output options); AR Report + Time Horizon relocated under the GHG module; module/GHG toggles gate their outputs.

## Pass 7 — Network visualization (2026-05-25)

- **7.1 Port network_viz module.** Ported the v0.4-Antigravity `03-network.ipynb` visualization toolkit into `apps/streamlit_app/network_viz.py` — DIMENSIONS config, PATH_STYLE_CONFIG, GHG_PATH_COLORS, spring-around-fixed-dimension layout, parallel-edge flattening, three-layer (background / paths / active nodes) rendering. Single unified `render_network_figure(graph_engine, highlight_paths=None, path_colors=None)` replaces the original's three `visualize_*` functions. Layout cached via `st.cache_resource` so spring computation runs once per session. Engine graph never mutated — work happens on a styled clone.
- **7.2 Integrate into Conversions panel.** "🌐 Show network view" expander on each path tab (default closed). Shows the path highlighted in the Path 1 color against the full graph background.
- **7.3 Integrate into GHG Emissions panel.** "🌐 Show GHG network view" expander after the per-gas cards. Overlays all three gas paths with CO₂ violet, CH₄ green, N₂O red — accent-consistent with the bar and cards above.
- **7.4 Verify + docs.** New concept page `Network visualization.md` (philosophy, layout, three-layer rendering, origin). New reference page `network_viz.md`. 3 new Glossary entries: Dimension centroid, Master layout, Network view. MOC + CHANGELOG updated. 38/38 tests still pass; all 10 UI modules import.

## Pass 6 — Portable results (2026-05-24)

- **6.1 Export buttons.** Added `⬇ JSON audit` and `⬇ Markdown report` download buttons on both Conversions and GHG panels. New `streamlit_app/export.py` module with `audit_to_json` and `audit_to_markdown` — pure functions, no Streamlit dependency. JSON envelope uses `schema: unitgps-audit/v1`. Markdown is paste-ready into any doc.
- **6.2 URL state persistence.** New `streamlit_app/url_state.py` module with `hydrate_from_query_params` (URL → session_state, called early) and `sync_to_query_params` (session_state → URL, called late). 18 single-value keys + 14 filter columns round-trip. Default-True checkboxes strip from URL to keep bookmarks short. New `🔗 Share / bookmark` popover in the title row shows the live URL.
- **6.3 Verify + docs.** Round-trip smoke test passes; 38/38 engine tests still green. New concept page `Portable results.md`. New reference pages `export.md`, `url_state.md`. 4 new Glossary entries: Bookmark URL, Export, Hydration, Portable results. MOC and CHANGELOG updated.

## Pass 5 — "Make it perfect" polish (2026-05-23)

- **5.1 Dead code removal.** Stripped `formatting.draw_path_graph` (Graphviz pathway, replaced by hero stepper), `formatting.build_math_latex` (replaced by inline LaTeX in the GHG derivation expander), `_route_breadcrumb`, `_kv_table`, `_section_label` from `conversion.py` — all unreferenced. Removed corresponding doc pages. Net: −5 functions, −2 doc pages, ~5.5KB of source.
- **5.2 Edge picker label.** Was `⚡ 3 alternatives — currently using #2`. Now `⚡ 3 alternatives — using: EPA · 2025 · Anthracite`. The user sees what they have without opening the picker.
- **5.3 Glossary refresh.** Added 14 new entries: Attribution footer, Audit card hybrid layout, chosen_edge_idx, Dominant gas marker, Doubled-attribute trick, Edge picker, edge_picks, GHG condensed panel, Hero pathway stepper, Horizontal stacked bar, Path comparison table, Source-vs-standardized chemical, Static step, WCAG contrast.
- **5.4 Architecture refresh + this CHANGELOG.** Updated `architecture.md` to mark Pass 2 items as done, document Streamlit 1.57 CSS specificity, GHG bar-vs-donut reasoning, edge-pick semantics, static-step shell decision, theme mode-locking.

## Pass 4 — Documentation refresh (2026-05-23)

- **4.1 New reference docs.** Created `renderers - stepper.md`, `formatting.format_audit_date.md`, `formatting.normalize_param_value.md`, `filters.render_active_filter_chips.md`.
- **4.2 Existing doc updates.** Updated `calculate_conversion_factor.md`, `determine_conversion.md`, `determine_ghg_emissions.md` for `edge_picks` parameter. Rewrote `themes.md` for 13 themes + new CSS.
- **4.3 New concept pages.** `Edge picks for ambiguous paths.md`, `Hero pathway stepper.md`, `Audit card hybrid layout.md`, `GHG condensed panel.md`.
- **4.4 MOC + frontmatter.** Updated `_MOC.md` with all new pages, "What changed" callout, accurate inventory. Verified all wiki-links resolve.

## Pass 3 — Themes (2026-05-23)

- **3.1 Contrast audit.** Wrote a WCAG luminance-ratio checker for every theme's text/bg, secondary/bg, text/surface, border/bg pairs. Fixed Glassmorphism's invisible text (surface 1.0:1 → 21:1 by darkening to rgba(0,0,0,0.35)). Bumped near-invisible borders on Obsidian, M3, Earthy Zen, Ultra-Minimalist, Bloomberg.
- **3.2 Light/dark variants.** Added Obsidian Light, Material Design (M3) Dark, Earthy Zen Dark, Ultra-Minimalist Dark. Mode-locked themes (Neo-Brutalism, Glassmorphism, Cyberpunk, Retro OS, Bloomberg) kept single-mode. Total themes: 9 → 13.

## Pass 2 — Path control (2026-05-23)

- **2.1 Engine: `edge_picks` param.** Added `edge_picks: dict[tuple[str,str], int] | None = None` to `calculate_conversion_factor`. Defensive clamp on out-of-bounds. Writes `chosen_edge_idx` to each step.
- **2.2 Engine wrappers.** Threaded `edge_picks` through `determine_conversion` and `determine_ghg_emissions`.
- **2.3 Engine tests.** Added 8 tests covering default, explicit pick, out-of-bounds clamp, negative clamp, unrelated-edges ignored, per-step picks on multi-step paths, ambiguity-flag preservation, and wrapper forwarding. 30 → 38 tests.
- **2.5 Path comparison table.** Above the tabs when N > 1: Route, Multiplier, Steps, Set kinds, ⚡ marker for ambiguous.
- **2.6 Tabs for multi-path.** `st.tabs(["Path 1 ⚡", "Path 2", ...])` instead of vertical stacking.
- **2.7 Sticky ambiguous-edge picker.** Inline expander on each ambiguous step. Pick persists in `st.session_state["_edge_picks"]` and survives reruns.
- **2.9 Verify.** End-to-end smoke test with multi-step ambiguous path. 38/38 tests pass.

## Pass 1.6 — CSS specificity bug fix (2026-05-23)

- Width cap rule was being silently ignored on Streamlit 1.57. Root cause: `.main .block-container` was the legacy selector; 1.57 uses `[data-testid="stMainBlockContainer"]`. Switched `layout="wide"` → `"centered"` so Streamlit's own CSS caps naturally, plus added the doubled-attribute trick (`[data-testid="X"][data-testid="X"]`) for specificity override. Content finally sits in a centered 1040px column on wide monitors.

## Pass 1.5 — Visual cleanup (2026-05-22 → 2026-05-23)

- **1.5.1** Shared formatters: `format_audit_date` (YYYY-MMM-DD), `normalize_param_value` (Scope 1.0 → Scope 1).
- **1.5.2** Audit card redesign — hybrid B+A layout: grouped Classification + Chemical key/values with source-vs-standardized subtitles + single attribution footer line.
- **1.5.3** Container max-width + removed redundant `st.container(border=True)` boxes + subtle dividers between panels.
- **1.5.4** Active-filter chip strip above filter tabs. Auto-hide empty filters (Formula(0)).
- **1.5.5** Moved filter UI to collapsible left sidebar — *reverted* after user feedback that the sidebar pattern hurt rather than helped.
- **1.5.6** Compact widget label CSS.
- **1.5.7** Verify.
- **1.5.8** Tightened top input section (Source/Target/Modules/Temporal Scope column ratios).
- **1.5.9** Hero pathway visual stepper (`render_hero_stepper` in new `stepper.py`). Replaces the flat text breadcrumb in both Conversions and GHG panels.
- **1.5.10** Consistent step card shell — initially with one-line static body, later simplified to header-only after user feedback.
- **1.5.11** Per-gas compact summary cards (Option B from a side-by-side comparison).
- **1.5.12** GHG condensed panel — bar over donut, table folded into cards, equation behind disclosure, dominant ★ marker.
- **1.5.13** Tight Ribbon top-section layout — *reverted* after wide-monitor issue revealed the underlying width-cap bug (later fixed in Pass 1.6).

## Pass 1 — Initial polish (2026-05-21 → 2026-05-22)

- **1.1** LaTeX equation: drop `m_` prefix (use plain `CO₂`, `CH₄`, `N₂O`).
- **1.2** Dropdowns sized to content (no full-row stretch).
- **1.3** Skip "no parameters" message for static steps.
- **1.4** Step-type visual differentiation via colored left border on step cards (gray/green/red).
- **1.5** Collapsible Conversions + GHG result panels.
- **1.6** Verify.

## Initial build (2026-05-20 → 2026-05-21)

- Scaffold folder structure under `v0.5-Claude/`.
- Port engine modules (data, graph, pathfinding, calculate, emissions) with Gemini debug paths removed.
- 30-test pytest suite covering all 5 engine modules.
- Streamlit app decomposed into themes / state / filters / formatting / renderers / app orchestrator.
- 53-page Obsidian documentation vault.

## Pre-Claude generations (archived)

- **v0.4-Antigravity** — Google Antigravity build. Single 1,290-line app.py, hard-coded debug paths to `C:\Users\davel\.gemini\antigravity\brain\…`. Functional but unmaintainable.
- **v0.2.2025.01.15** and earlier — under `00-Legacy Versions/`. Not actively maintained.
