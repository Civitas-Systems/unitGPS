---
type: module
module: streamlit_app.themes
file: apps/streamlit_app/themes.py
status: current
generation: Claude
last_updated: 2026-05-23
tags: [streamlit, ui, theming, css]
related:
  - "[[themes.get_theme]]"
  - "[[themes.inject_css]]"
  - "[[app]]"
  - "[[state]]"
---

# themes (module overview)

The active theme dict + the giant CSS-in-Python injector that recolors Streamlit's default look. Imported by [[app]] on every rerun.

## Public API

| Symbol | Type | Purpose |
|--------|------|---------|
| `THEMES` | `dict[str, dict]` | 13 theme dicts, keyed by display name. |
| `DEFAULT_THEME` | `str` | `"Obsidian"` — used when session_state doesn't carry one. |
| [[themes.get_theme]] | function | Look up a theme by name, fall back to default if unknown. |
| [[themes.inject_css]] | function | Emit the full themed `<style>` block via `st.markdown`. |

## The 13 themes

Original nine plus four light/dark variants for the themes that make sense to invert.

| Name | Mode | Background | Primary |
|------|------|------------|---------|
| `Obsidian` (default) | dark | `#18181B` near-black | `#8B5CF6` violet |
| `Obsidian Light` | light | `#FAFAF7` warm-white | `#6D28D9` deep purple |
| `Material Design (M3)` | light | `#F3EDF7` lavender | `#6750A4` purple |
| `Material Design (M3) Dark` | dark | `#141218` (M3 dark surface) | `#D0BCFF` lilac |
| `Neo-Brutalism` | mode-locked | `#FACC15` yellow | `#FF90E8` hot pink |
| `Glassmorphism` | mode-locked | gradient | `#FFFFFF` white |
| `Cyberpunk` | mode-locked | `#0B0F19` near-black | `#00FFCC` cyan |
| `Earthy Zen` | light | `#F9F6F0` cream | `#78866B` sage |
| `Earthy Zen Dark` | dark | `#1F1D18` bark | `#A3B099` muted sage |
| `Ultra-Minimalist` | light | `#FFFFFF` pure white | `#000000` pure black |
| `Ultra-Minimalist Dark` | dark | `#000000` pure black | `#FFFFFF` pure white |
| `Retro OS` | mode-locked | `#008080` Win95 teal | `#000080` navy |
| `Bloomberg Terminal` | mode-locked | `#000000` pure black | `#FF9900` amber |

Mode-locked themes (Neo-Brutalism, Glassmorphism, Cyberpunk, Retro OS, Bloomberg) don't get light/dark variants because their identity *is* the specific mode — inverting them would create a different theme, not a variant.

## Theme dict schema

Every theme has these keys (one entry per theme):

| Key | Purpose |
|-----|---------|
| `bg` | Page background. May be a hex, an `rgba(...)`, or a `linear-gradient(...)`. |
| `surface` | Card backgrounds. Should contrast cleanly with `text`. |
| `primary` | Main accent — buttons, links, the metric-value text. |
| `text_on_primary` | Foreground color when text sits on a `primary` fill. |
| `text` | Body text. Must hit AA contrast against `bg` (4.5:1+). |
| `secondary` | Muted text — labels, captions, attribution lines. |
| `border` | Card and divider borders. Bumped from theme defaults to ≥AA·LG (3:1) for visibility. |
| `danger` | Red-ish — emission badges, error states. |
| `success` | Green-ish — chemical-property badges. |
| `font` | Body font-family string. |
| `radius` | Card corner radius. |
| `shadow` | Drop shadow on raised surfaces. |
| `input_radius` | Form-input corner radius. |
| `button_transform` | `text-transform` for buttons. |
| `tab_radius` | Tab-header corner radius. |
| `border_width` | Default border thickness in px. |
| `input_bg` | Input field background. |
| `backdrop` | (Glassmorphism only) backdrop-filter value for frosted glass. |

## WCAG contrast audit

All 13 themes pass the audit script (see `Pass 3.1`). Snapshot of the worst-case ratios:

| Theme | text/bg | secondary/bg | text/surface | border/bg |
|-------|---------|--------------|--------------|-----------|
| Obsidian | 14.3 AAA | 6.9 AA | 13.5 AAA | 2.3 (subtle) |
| Material Design (M3) | 14.9 AAA | 8.1 AAA | 17.1 AAA | 1.4 (subtle) |
| Glassmorphism | 3.9 AA·LG | 3.5 AA·LG | **21.0** | 3.9 |
| Bloomberg Terminal | 9.8 AAA | 15.3 AAA | 9.8 AAA | 2.4 |
| Obsidian Light | 16.9 AAA | 7.4 AA | 17.7 AAA | 1.4 |
| Earthy Zen Dark | 13.0 AAA | 7.1 AA | 11.8 AAA | 1.8 |
| Ultra-Minimalist Dark | 21.0 AAA | 7.4 AA | 21.0 AAA | 1.7 |

Subtle borders (1.4–2.3) are intentional on the minimalist themes — louder borders would compete with the typography. The audit script flags anything below 3:1 for inspection but doesn't force a fix.

## The big CSS injector

[[themes.inject_css]] is a single ~400-line f-string built fresh per call from the active theme dict. Theme switching = inject_css re-runs on the next rerun with a different theme. No caching, no FOUC.

Critical rules (all use the `[data-testid="stMainBlockContainer"][data-testid="stMainBlockContainer"]` doubled-attribute trick so they win against Streamlit's emotion-generated CSS — see [[../../architecture#Streamlit-1.57-CSS-specificity|architecture]]):

- **Width cap** — `max-width: min(1040px, 94vw)` so content sits in a centered column regardless of viewport width
- **Compact labels** — Streamlit's default 1.6rem H3 → 1.05rem 500-weight
- **Filter dropdown cap** — `max-width: 360px` inside `[data-testid="stTabs"]` so Process 1 / Process 2 don't spread edge-to-edge
- **Subtle dividers** — `<hr>` opacity 0.5, border 0.5px so section separators read as quiet
- **Sidebar hidden** — `.stSidebar { display: none; }` (we use centered layout)

See [[themes.inject_css]] for the full rule set.

## See also

[[themes.get_theme]] · [[themes.inject_css]] · [[app]] · [[state]]
