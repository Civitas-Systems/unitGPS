---
type: module
module: streamlit_app.state
file: apps/streamlit_app/state.py
lines: "1-95"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, state, session]
related:
  - "[[state.init_session_state]]"
  - "[[state.on_start_change]]"
  - "[[state.on_final_change]]"
  - "[[state.make_sync_callbacks]]"
  - "[[app]]"
---

# state (module overview)

Owns Streamlit's `st.session_state` defaults and the bi-directional sync callbacks. Imported by [[app]] on every rerun.

## Public API

| Symbol | Type | Purpose |
|--------|------|---------|
| `_DEFAULTS` | `dict` (module-private) | Initial values for every key the app uses across reruns. |
| [[state.init_session_state]] | function | Idempotent — apply defaults for any key not yet in session_state. |
| [[state.on_start_change]] | function | Callback: user edited Starting Value → set calc_direction = 'forward'. |
| [[state.on_final_change]] | function | Callback: user edited Final Value → set calc_direction = 'backward'. |
| [[state.make_sync_callbacks]] | function | Factory: build the four dimension↔unit sync callbacks bound to `node_attrs`. |

## The `_DEFAULTS` dict

```python
_DEFAULTS = {
    'theme': 'Obsidian',
    'start_val': 1.0,
    'final_val': 0.0,
    'calc_direction': 'forward',
    'source_dim': 'Energy',
    'source_unit_sb': 'J',
    'target_dim': 'Weight',
    'target_unit_sb': 'kg',
    'dy_mode': 'All Years',
    'dy_mode_radio': 'All Years',
    'Data Year': [],
    'run_clicked': False,
    'max_paths': 5,
    'gwp_report': 'AR5',     # IPCC Assessment Report — user-switchable
    'gwp_horizon': '100',    # Time horizon in years — user-switchable
}
```

The starting page has the user converting 1 J → kg (an emission-factor query). Edit `_DEFAULTS` to change the first-impression UI.

## Why a separate module?

Three reasons:

1. **Cross-cutting state lives here.** Without this module, defaults would either be scattered through `app.py` or hidden inside callback functions — both make it harder to scan "what session_state keys exist?"
2. **Callbacks need closure over node_attrs.** The sync functions need to know each unit's dimension. Passing `node_attrs` to each callback explicitly via `make_sync_callbacks` keeps the callbacks pure and the dependency obvious.
3. **Testability.** Pure functions in a separate module are unit-testable without spinning up Streamlit. (No tests exist yet but the structure supports them.)

## Cross-rerun state model

Streamlit re-runs the entire script on every interaction. Anything that needs to survive a rerun lives in `st.session_state`. Anything ephemeral lives in local variables that get rebuilt each rerun.

Examples:
- **In session_state:** user's theme choice, source/target unit, current numeric inputs, which paths to show.
- **Not in session_state:** `graph_engine` (in `@st.cache_resource` instead), `combined_data` (also cached), `active_sets` (recomputed from checkboxes each rerun).

## See also

[[state.init_session_state]] · [[state.on_start_change]] · [[state.on_final_change]] · [[state.make_sync_callbacks]] · [[app]]
