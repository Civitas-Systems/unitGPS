---
type: function
parent: "[[filters]]"
module: streamlit_app.filters
file: apps/streamlit_app/filters.py
lines: "147-151"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, filtering, ui-widget]
related:
  - "[[filters]]"
  - "[[filters.get_options]]"
  - "[[filters.render_filter_tabs]]"
---

# filters.dynamic_multiselect

Render a `st.multiselect` widget whose options + placeholder + label reflect the current filter state. Thin wrapper used by [[filters.render_filter_tabs]] for every database-filter dropdown.

## Signature

```python
def dynamic_multiselect(label: str, col_name: str, df_for_units: pd.DataFrame, **kwargs)
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `label` | `str` | Display label, e.g. `"Country"`. |
| `col_name` | `str` | DataFrame column name AND `session_state` key. Same string for both. |
| `df_for_units` | DataFrame | Source data for computing options. |
| `**kwargs` | — | Passed through to `st.multiselect`. |

## Output

Whatever `st.multiselect` returns — the list of currently-selected values. (Usually unused; the value is also written to `st.session_state[col_name]`.)

## Implementation

```python
def dynamic_multiselect(label, col_name, df_for_units, **kwargs):
    options = get_options(df_for_units, col_name)
    placeholder = f"{len(options)} options" if options else "No options"
    display_label = f"{label} ({len(options)})"
    return st.multiselect(
        display_label, options=options, key=col_name, placeholder=placeholder, **kwargs
    )
```

Three things this does for you:

1. **Calls [[filters.get_options]]** to get the live option list given current filters.
2. **Annotates the label** with the option count: `"Country (47)"` so the user knows how many choices are available.
3. **Sets the placeholder** to the option count too: shown when no values are selected yet.

## Why `key=col_name` matters

The `key` parameter tells Streamlit which `session_state` slot to read/write. Setting it to the column name makes the multiselect bidirectional: changing the widget updates `session_state[col_name]`, and other parts of the script can read `session_state[col_name]` to see what's currently selected.

This is also why `COLS_TO_EXTRACT` uses the exact same column names — the same string serves as DataFrame column, session_state key, and widget key.

## Usage

```python
# Inside render_filter_tabs:
dynamic_multiselect("Country", "Country", df_for_units)
dynamic_multiselect("Agency", "Agency", df_for_units)
```

## See also

[[filters]] · [[filters.get_options]] · [[filters.render_filter_tabs]]
