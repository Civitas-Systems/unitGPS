---
type: function
parent: "[[filters]]"
module: streamlit_app.filters
file: apps/streamlit_app/filters.py
lines: "121-132"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, filtering, ui-helper]
related:
  - "[[filters]]"
  - "[[filters.get_options]]"
  - "[[filters.dynamic_multiselect]]"
---

# filters.get_filtered_df

Return a DataFrame view honoring every active filter column EXCEPT the named one. Used so a multiselect can offer options that are still valid given the *other* currently-active filters.

## Signature

```python
def get_filtered_df(df_for_units: pd.DataFrame, exclude_col: str | None = None) -> pd.DataFrame
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `df_for_units` | DataFrame | Base DataFrame to filter (already restricted by Set + Data Year). |
| `exclude_col` | str \| None | If set, skip filtering on this column. |

## Output

A `pd.DataFrame` filtered by every column in `COLS_TO_EXTRACT` except `exclude_col`, using whatever values are currently in `st.session_state` for each.

## How it works

```python
def get_filtered_df(df_for_units, exclude_col=None):
    temp = df_for_units.copy()
    for col in COLS_TO_EXTRACT:
        if col == exclude_col:
            continue
        val = st.session_state.get(col, [])
        if val:
            temp = temp[temp[col].isin(val)]
    return temp
```

The defensive `.copy()` prevents pandas' SettingWithCopyWarning on downstream chained operations.

## Why "exclude one column"

The key insight for [[filters.dynamic_multiselect]]: when populating Country's multiselect options, we want options that are still reachable given *all other* active filters — but NOT given Country itself (otherwise the dropdown would only ever show the currently-selected values).

Concretely: if the user picks Agency=EPA and Country=USA, the Country dropdown should still show "USA, UK, Germany, ..." (all countries that have EPA data), not just "USA". The Country filter is excluded when computing Country's options.

## Usage

```python
# Inside get_options(col='Country'):
filtered = get_filtered_df(df_for_units, exclude_col='Country')
# Then collect unique values from filtered['Country']
```

## See also

[[filters]] · [[filters.get_options]] · [[filters.dynamic_multiselect]]
