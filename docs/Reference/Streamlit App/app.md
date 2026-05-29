---
type: script
module: streamlit_app.app
file: apps/streamlit_app/app.py
lines: "1-495"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, ui, orchestrator]
related:
  - "[[themes]]"
  - "[[state]]"
  - "[[filters]]"
  - "[[formatting]]"
  - "[[renderers - conversion]]"
  - "[[renderers - emissions]]"
  - "[[DataLoader]]"
  - "[[UnitGraph]]"
  - "[[determine_conversion]]"
  - "[[determine_ghg_emissions]]"
---

# app.py (Streamlit orchestrator)

The entry point Streamlit runs. **Not a function — a top-to-bottom script that executes from line 1 every time the user interacts with anything.** That's how Streamlit works: every widget change re-runs the whole script.

The page is deliberately thin (~495 lines, most of which is widget assembly) because the heavy lifting is delegated to the dedicated modules: [[themes]] handles styling, [[state]] handles session defaults and callbacks, [[filters]] handles the database-filter UI and pandas-side filtering, [[renderers - conversion]] and [[renderers - emissions]] render the two result panels.

## How to run

```bat
apps\streamlit_app\run.bat
```

Or manually:

```bat
.venv\Scripts\activate
streamlit run apps\streamlit_app\app.py
```

## What happens on each rerun

```
1. Path bootstrap — add src/ and apps/ to sys.path if not installed
2. st.set_page_config(title, layout, icon, sidebar)
3. init_session_state()                  ← apply defaults for first-run keys
4. theme = get_theme(session_state.theme)
5. inject_css(theme)                     ← emit the giant <style> block

6. load_engine()  (cached)               ← DataLoader → UnitGraph, ~3s first time, 0s thereafter

7. Read module checkboxes from session_state. Compute active_sets.

8. df_for_units = combined_data filtered by active_sets
   df_for_units = apply_db_and_temporal_filters(df_for_units, ...)
   ← used for live module counts and available unit lists

9. Derive available_units + available_dims from df_for_units

10. Force target_dim='Weight' if GHG module is on

10b. If GHG module is active: render IPCC AR + Time Horizon selectboxes
     (state keys: gwp_report, gwp_horizon).

11. Render layout:
    a. Header (title + theme picker)
    b. Source/Target unit pickers (with sync callbacks)
    c. Module toggle checkboxes (with live counts)
    d. Temporal Scope radio (+ year inputs if Specific/Range)
    e. Database Filters tabs + Calculate button + Max Paths

12. Build search_params dict via build_search_params()

13. If user clicked Calculate AND source/target are valid:
    - Determine which result panels to show (conv, ghg, both)
    - Render the panels via render_conversion_panel / render_emissions_panel
    - Each panel renders full-width and stacked vertically (NOT side-by-side)
      so long equations and audit tables can never be horizontally cut off

14. Render the two-way Starting/Final number inputs (LAST — so the renderers
    above could have updated start_val/final_val via the calc_direction logic)
```

## Path bootstrap

```python
APP_DIR     = Path(__file__).resolve().parent
CLAUDE_ROOT = APP_DIR.parents[1]
SRC_DIR     = CLAUDE_ROOT / 'src'
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

APPS_DIR = APP_DIR.parent
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))
```

Two sys.path additions:

1. **`src/`** so `from unitgps.engine import ...` works even without `pip install -e .`. (Preferred install path: `pip install -e .` so this hack is unnecessary.)
2. **`apps/`** so `from streamlit_app.filters import ...` works when Streamlit launches `app.py` as a top-level script (which puts `apps/streamlit_app/` on sys.path but not `apps/`).

## Engine loading (cached)

```python
@st.cache_resource(show_spinner='Loading Engine...')
def load_engine():
    loader = DataLoader(str(DATA_LIBRARY), str(GWP_FILE))
    combined_data = loader.load_data_library()
    ...
    node_attrs = loader.get_units_attributes(combined_data)
    gwps = loader.load_gwps()
    graph_engine = UnitGraph(combined_data, node_attrs)
    return graph_engine, gwps, combined_data, node_attrs
```

`@st.cache_resource` is the heavy-object cache; the engine is built once and reused across reruns and sessions until the process restarts. Without this, the xlsx would be re-read on every widget change.

The function also propagates `Source-Chemical Category` from `Source-Chemical Type` for rows where the Category is null — a data-cleanup step that lives in the loader rather than the data file so the xlsx stays untouched.

## Layout — the rendering order matters

### Two-way inputs rendered LAST

```python
# Step 11: source/target unit pickers
with col_src:
    ...
    with s1:
        start_val_container = st.container()   # ← reserve the slot

# Step 13: render result panels (may update session_state.final_val)

# Step 14: actually render the number inputs INTO the reserved slots
with start_val_container:
    st.number_input('Starting Value', step=None, key='start_val', on_change=on_start_change)
```

The trick: `st.container()` reserves a slot in the layout, but the actual `st.number_input` widget is rendered later. By the time we render the input, the result panels have already run and (if calculation succeeded) updated `session_state.start_val` or `final_val` via the calc_direction logic. So the number inputs display the *post-calculation* values.

If we rendered them inline before the result panels, the displayed values would be one rerun behind.

### Module count uses an unfiltered-by-modules df

```python
# Counts use DB+temporal filters but ignore the module-checkbox state itself
temp_df = apply_db_and_temporal_filters(combined_data, search_params_raw, mode, ...)
conv_count = len(temp_df[temp_df['Set'].isin(['Unit Conversion', 'Unit Conversions'])])
```

The counts shown next to each module checkbox (e.g. "🌍 GHG Emissions (3024)") need to be independent of whether that checkbox is currently checked — otherwise unchecking GHG would zero out its own count. We filter by DB+temporal filters only, then count per Set.

## Cleanup items

- **`get_units_for_dim_local` is duplicated** in app.py — same function as `get_units_for_dim` in [[filters]]. Should be removed from app.py and imported from filters.
- **Hard-coded year-dropdown range** — `range(max_db_yr, min_db_yr - 1, -1)` should move to a helper in [[filters]].
- **Path bootstrap is gnarly.** If we commit to `pip install -e .` as the install method (which `run.bat` does), the sys.path additions become dead code.

## See also

[[themes]] · [[state]] · [[filters]] · [[renderers - conversion]] · [[ren