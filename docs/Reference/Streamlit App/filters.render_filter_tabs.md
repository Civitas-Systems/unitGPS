---
type: function
parent: "[[filters]]"
module: streamlit_app.filters
file: apps/streamlit_app/filters.py
lines: "175-247"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, filtering, ui-rendering]
related:
  - "[[filters]]"
  - "[[filters.dynamic_multiselect]]"
  - "[[filters.get_options]]"
  - "[[app]]"
---

# filters.render_filter_tabs

Render the four-tab Database Filters group (Resources / Process / Location / Data Source). Only tabs whose columns have at least one option get rendered — empty tabs are hidden.

## Signature

```python
def render_filter_tabs(df_for_units: pd.DataFrame, theme: dict) -> None
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `df_for_units` | DataFrame | Source data for computing option lists. |
| `theme` | dict | Current theme (used only for the SCOPE label color). |

## Output

None. Side effect: emits the tabs widget and its contents into the current Streamlit container.

## What gets rendered

| Tab | Columns | Layout |
|-----|---------|--------|
| **Resources** | Chemical Category, Formula, Chemical Type, Property | 2×2 grid of multiselects |
| **Process** | Process 1, Process 2, Scope (1/2/3), Category | 2 multiselects on top, Scope checkboxes + Category multiselect below |
| **Location** | Country, eGRID Region | Side-by-side multiselects |
| **Data Source** | Agency, Dataset | Side-by-side multiselects |

## Dynamic tab visibility

```python
active_groups = []
for g_name, g_cols in FILTER_GROUPS.items():
    if any(len(get_options(df_for_units, col)) > 0 for col in g_cols):
        active_groups.append((g_name, g_cols))

if not active_groups:
    st.info('No database filters apply to the selected Source and Target units.')
    return

tabs = st.tabs([g[0] for g in active_groups])
```

A tab is only shown if at least one column in its group has at least one available option. If the user has filtered down to where no group qualifies, an info banner is shown instead.

This dynamic behavior is what makes the UI feel responsive — when you pick a Source unit that's only used in a few EFs, irrelevant filter tabs disappear.

## Scope checkboxes

Scope (1, 2, 3 emissions per the GHG Protocol) is rendered as three small checkboxes instead of a multiselect — three values are few enough that checkboxes are faster than a dropdown.

```python
raw = st.session_state.get('Scope_raw', [])
s_c1 = scope_cols[0].checkbox('1', value=('1' in raw)) if '1' in available_scopes else False
s_c2 = scope_cols[1].checkbox('2', value=('2' in raw)) if '2' in available_scopes else False
s_c3 = scope_cols[2].checkbox('3', value=('3' in raw)) if '3' in available_scopes else False

st.session_state['Scope_raw'] = [s for s, b in [('1', s_c1), ('2', s_c2), ('3', s_c3)] if b]
st.session_state['Scope'] = st.session_state['Scope_raw']
```

Two session_state slots: `Scope_raw` (mirror used by checkboxes) and `Scope` (read by the engine). They're kept identical.

## Side effects on session_state

- `Scope_raw`, `Scope` set by the Scope checkbox handling.
- Every other column's value set by its [[filters.dynamic_multiselect]] (via the `key=col_name` argument).

## Usage

```python
# In app.py inside the Database Filters container:
render_filter_tabs(df_for_units, theme)
```

## See also

[[filters]] · [[filters.dynamic_multiselect]] · [[filters.get_options]] · [[app]]
