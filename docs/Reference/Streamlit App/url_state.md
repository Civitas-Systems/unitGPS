---
type: module
module: streamlit_app.url_state
file: apps/streamlit_app/url_state.py
status: current
generation: Claude
last_updated: 2026-05-23
tags: [ui, url-state, persistence, bookmarks]
related:
  - "[[Portable results]]"
  - "[[app]]"
  - "[[state]]"
---

# url_state

Round-trips the user's configuration through `st.query_params`. Bookmarks survive across sessions, scenarios are shareable as URLs.

## Public API

| Symbol | Purpose |
|--------|---------|
| `URL_SAFE_KEYS` | Tuple of single-value session_state keys to round-trip (theme, units, modules, GWP, etc.) |
| `FILTER_KEYS` | Tuple of list-valued filter column names (encoded as comma-separated under `f_<key>`) |
| `hydrate_from_query_params(query_params=None) -> int` | URL → session_state. Called early in `app.py`. Returns count of keys hydrated. |
| `sync_to_query_params(query_params=None) -> int` | session_state → URL. Called late in `app.py`. Returns count of keys written. |
| `build_shareable_link(base_url="") -> str` | Build a complete shareable URL from current session_state without touching `st.query_params`. Used by the "🔗 Share / bookmark" popover. |

## Encoding rules

- **Defaults are stripped.** `cb_mod_*` checkboxes default to `True`; only modules turned *off* serialize. Keeps URLs short for the common case.
- **Filters encode under `f_<safe_key>`.** `Source-Chemical Type` becomes `f_source_chemical_type`. Multi-select values join with commas.
- **Numbers parse defensively.** `start_val` tries float, `max_paths` handles int-or-"All", year inputs try int. Bad values are silently skipped rather than crash.
- **Lists deserialize via `split(",")`.** Empty string → empty list.
- **What's NOT in the URL:** `_edge_picks` (per-result, not configuration), `start_yr_input`/`end_yr_input` defaults, numeric results (recomputed on URL load).

## Hydration vs init_session_state ordering

```python
# In app.py:
hydrate_from_query_params()  # First — URL takes precedence if present
init_session_state()         # Second — fills in defaults for missing keys
```

Order matters: `init_session_state` only writes keys that don't exist. If a URL set them, defaults are skipped. This means a clean visit (no URL params) gets defaults; a bookmark visit gets the bookmarked state.

## Sync timing

`sync_to_query_params()` runs at the *end* of `app.py` after every widget has rendered and session_state is stable. The URL bar updates after each interaction — bookmark anywhere, restore anywhere.

## Testability

Both entry points accept a `query_params` argument so tests can pass a plain dict and verify round-trip behaviour without a Streamlit runtime. See the smoke test in this module's docstring.

## See also

[[Portable results]] · [[app]] · [[state]]
