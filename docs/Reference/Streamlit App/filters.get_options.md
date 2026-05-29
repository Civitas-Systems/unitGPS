---
type: function
parent: "[[filters]]"
module: streamlit_app.filters
file: apps/streamlit_app/filters.py
lines: "135-144"
status: current
generation: Claude
last_invariant: 2026-05-21
last_updated: 2026-05-21
tags: [streamlit, filtering, ui-helper]
related:
  - "[[filters]]"
  - "[[filters.get_filtered_df]]"
  - "[[filters.dynamic_multiselect]]"
---

# filters.get_options

Return the sorted, deduplicated list of string options for a multiselect, given the current state of every other filter.

## Signature

```python
def get_options(df_for_units: pd.DataFrame, col: str) -> list[str]
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `df_for_units` | DataFrame | Base DataFrame already filtered by Set + temporal mode. |
| `col` | str | Column to compute options for. |

## Output

A sorted `list[str]` of distinct, non-empty values. Empty if `col` isn't a column in `df_for_units` or has no valid values.

## How it works

```python
def get_options(df_for_units, col):
    filtered = get_filtered_df(df_for_units, exclude_col=col)
    if col not in filtered.columns:
        return []
    vals = filtered[col].dropna().unique()
    if col in ['Scope', 'Data Year']:
        str_vals = {str(int(v)) for v in vals if str(v).replace('.0', '').isdigit()}
    else:
        str_vals = {str(v).strip() for v in vals}
    return sorted([v for v in str_vals if v])
```

## Special handling for numeric columns

```python
if col in ['Scope', 'Data Year']:
    str_vals = {str(int(v)) for v in vals if str(v).replace('.0','').isdigit()}
```

Scope (`1`, `2`, `3`) and Data Year (`2020`, `2021`, ...) are stored as floats in the source (pandas coerces). The cast to `int` then `str` produces clean `"1"`, `"2020"` displays instead of `"1.0"`, `"2020.0"`.

The `.replace('.0','').isdigit()` filter screens out genuinely non-numeric junk that might have crept in.

## Why sorted?

Dropdowns are easier to scan when alphabetized (for strings) or numerically ordered (for cast-to-string numbers — `"2020", "2021", "2022"` sorts correctly lexicographically because they're zero-padded fixed-width).

## Usage

```python
# Inside dynamic_multiselect, before rendering the widget:
options = get_options(df_for_units, 'Country')
# → ['Australia', 'Brazil', 'Germany', 'USA', ...]
```

## See also

[[filters]] · [[filters.get_filtered_df]] · [[filters.dynamic_multiselect]]
