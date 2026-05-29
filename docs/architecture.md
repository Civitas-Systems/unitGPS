---
type: architecture
status: current
generation: Claude
last_updated: 2026-05-23
tags: [architecture, design, history]
---

# UnitGPS Claude — architecture

Living design doc. Updated as decisions land.

## 1. Goals

1. A clean, isolated successor to the Antigravity generation, with
   the same conversion + emissions semantics but cleaner code.
2. A single shared engine that powers multiple UI variants
   (Streamlit first, then React, HTMX, and a standalone desktop build).
3. A real test suite, so future refactors are safe.

## 2. Engine — public API

The engine lives in `src/unitgps/engine/` and is the only Python the UI
variants import. Public symbols (re-exported from
`unitgps.engine.__init__`):

| Symbol | Module | Description |
|--------|--------|-------------|
| `DataLoader` | `data` | Load xlsx, drop nulls, synthesize reciprocal edges |
| `UnitGraph` | `graph` | `MultiDiGraph` wrapper with `filter_graph()` |
| `identify_conversion_path` | `pathfinding` | All shortest paths source→target |
| `convert_path_to_edge_tuples` | `pathfinding` | Nodes → `(u, v)` edges |
| `calculate_conversion_factor` | `calculate` | Multiply edge values, build audit |
| `format_sig_figs`, `is_valid_parameter`, `AmbiguityError` | `calculate` | Utilities |
| `find_gwp` | `emissions` | GWP lookup by GHG / AR / horizon |
| `determine_conversion` | `emissions` | High-level wrapper |
| `determine_ghg_emissions` | `emissions` | Routes CO₂ + CH₄ + N₂O, sums CO₂e |

Module boundary discipline: nothing in `engine/` may import from `apps/`,
`streamlit`, `fastapi`, or any UI framework. Engine functions return data
structures, never widgets.

## 3. UI variants

| Variant | Status | Stack | Folder |
|---------|--------|-------|--------|
| Streamlit | First target | Streamlit + Plotly | `apps/streamlit_app/` |
| React | Planned | FastAPI + React + Vite | `apps/react_app/` |
| HTMX | Planned | FastAPI + Jinja2 + HTMX | `apps/htmx_app/` |
| Desktop | Planned | pywebview (option A) or PyQt6 (option B) | `apps/desktop_app/` |

Each variant maintains its own README inside its folder.

## 4. Differences from Antigravity (cleanup list)

These are the rough edges from the Antigravity generation that this rewrite
addresses. Tracked here as a checklist so nothing slips.

- [x] Remove hard-coded debug paths to `C:\Users\davel\.gemini\antigravity\brain\...`
      (in `pathfinding.py` and `app.py`). Replaced with stdlib `logging`. **Done in both engine and Streamlit UI.**
- [x] Decompose the 1,290-line `app.py` into themes / state / filters / renderers / formatting (Streamlit port done).
- [ ] Make `apply_db_and_temporal_filters` (UI) and `UnitGraph.filter_graph`
      (engine) share a single source of truth — likely by exposing a pure-pandas
      filtering helper from the engine that the UI also calls for live counts.
- [ ] Drop the empty `_source_cache/v0..v3/` placeholders (don't recreate them here).
- [x] Let the user pick which parallel edge to use when an ambiguous path is
      detected. **Done in Pass 2 — `edge_picks` parameter on `calculate_conversion_factor`, threaded through both wrappers, with sticky per-step picker UI in conversion.py. See [[Edge picks for ambiguous paths]].**
- [x] First-class GWP report + horizon selector (AR4/AR5/AR6 × 20/100/500). **Done — live selectors in the UI when GHG module is active; active values surface in the GHG panel header.**
- [ ] Explicit `sheet_name="Sheet1"` in `pd.read_excel` with a clear error if
      the schema changes.
- [x] Real pytest suite — 38 tests passing across 5 engine modules, including round-trip identity, known-value GWP checks, and the full `edge_picks` parameter contract (default, explicit pick, out-of-bounds clamp, per-step picks on multi-step paths).

## 5. Data

Self-contained in `data/`:
- `Data Library, 2025-10-18, 1960-2023.xlsx` — 3,635 rows × 40 cols,
  single `Sheet1`. Set breakdown: Emission Factors 3,024 / Unit Conversion 294
  / Magnitude Adjustment 192 / Chemical Properties 63 / Global Warming
  Potentials 62 (the GWP rows here are unused — the IPCC file is canonical).
- `IPCC GWPs AR4-AR6.xlsx` — `Data` sheet, 1,209 rows; `Indicator` column
  encodes `<AR>-<horizon>` (e.g. `AR5-100`).

When the data files are refreshed, drop the new versions into `data/` and
update the filename references in `engine/data.py` (or, better, parameterize
the loader to take an explicit path).

## 6. Build order + polish history

The initial three-step build:

1. Scaffold + folder structure. ✅
2. Port engine modules with Gemini debug paths removed. Wire up tests. ✅
3. Get the Streamlit app working end-to-end against the new engine. ✅

The polish that followed — each "Pass" tracked in [[CHANGELOG]]:

| Pass | What landed | Result |
|------|-------------|--------|
| 1.1–1.6 | LaTeX cleanup, dropdown sizing, step-type colors, collapsible panels | Cleaner first impression |
| 1.5.1–1.5.13 | Date/numeric formatters, hybrid audit card, container max-width, filter chips, hero stepper, GHG condensed panel, tight ribbon experiment + revert | Major visual overhaul |
| 1.6 | CSS specificity fix for Streamlit 1.57's `stMainBlockContainer` | Width cap actually applies |
| 2.1–2.9 | `edge_picks` parameter end-to-end (engine + wrappers + tests + picker UI + path comparison + tabs) | Ambiguous paths now controllable |
| 3.1–3.2 | WCAG audit + Glassmorphism contrast fix + 4 light/dark variants | 13 themes, all pass contrast |
| 4.1–4.4 | Docs refresh for new modules, concept pages, frontmatter, MOC | 59 docs pages, all wiki-links resolve |
| 5.1–5.4 | Dead-code removal, sharper edge-picker labels, Glossary refresh, this architecture refresh | Polish for "perfect" |

Next planned: stand up an alternative UI variant (React or HTMX) against the same engine for a single-engine multi-frontend comparison.

## 7. Notable decisions (post-rewrite)

### Streamlit 1.57 CSS specificity

Streamlit's main content container in 1.57 uses `[data-testid="stMainBlockContainer"]` (not the legacy `.main .block-container`). Custom CSS that uses single-attribute selectors loses specificity battles against Streamlit's own emotion-generated rules. The fix in [[themes.inject_css]] uses a doubled-attribute trick — `[data-testid="X"][data-testid="X"]` — to push specificity from (0,1,0) to (0,2,0). This combined with `layout="centered"` on `st.set_page_config` makes the 1040px width cap actually hold. See [[Glossary#Doubled-attribute trick]].

### GHG panel — bar over donut

Donut charts fail when one slice dominates. Combustion CO₂e is CO₂-dominant (typically 99%+), so a donut showed one near-complete arc with two invisible slivers. The horizontal stacked bar with `min-width: 14px` per segment keeps tiny CH₄/N₂O slivers readable while still being proportional. See [[GHG condensed panel]].

### Edge picks — per-edge, not per-path

A user's pick for `(mmBTU, ton)` applies to *every* path that uses that edge, not just one path. This matches the user's mental model — "I prefer EPA's emission factor for Anthracite" is a fact about the edge, not the path. Picks live in `st.session_state["_edge_picks"]`, survive reruns and filter changes, clamp defensively against out-of-bounds. See [[Edge picks for ambiguous paths]].

### Static step shell

Static steps (Unit Conversion / Magnitude Adjustment) get header-only cards — no body. Earlier iterations tried a one-line "Static — no parameters" body for visual consistency; the bare header is cleaner and matches what the user pictured. See [[Audit card hybrid layout]].

### Themes are mode-locked or invertible

Themes whose identity *is* the specific palette (Neo-Brutalism's yellow, Glassmorphism's gradient, Cyberpunk's neon, Retro OS's teal, Bloomberg's amber-on-black) don't get light/dark variants. Themes that are essentially "this typography + neutral palette" (Obsidian, Material Design, Earthy Zen, Ultra-Minimalist) get both. See [[themes]].
