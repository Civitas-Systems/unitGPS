---
type: changelog
status: current
generation: Claude
last_updated: 2026-05-25
tags: [changelog, history, passes]
---

# CHANGELOG

A pass-by-pass record of what changed during the v0.5-Claude generation. Newest first.

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
