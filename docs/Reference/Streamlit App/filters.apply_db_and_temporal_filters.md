---
type: function
parent: "[[filters]]"
module: streamlit_app.filters
file: apps/streamlit_app/filters.py
lines: "52-112"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, filtering, pandas]
related:
  - "[[filters]]"
  - "[[UnitGraph.filter_graph]]"
  - "[[Temporal scope]]"
  - "[[app]]"
---

# filters.apply_db_and_temporal_filters

Apply column + Data Year filters to a pandas DataFrame, mirroring the rules in [[UnitGraph.filter_graph]]. Used for computing live counts and available unit lists before the engine even runs.

## Signature

```python
def apply_db_and_temporal_filters(
    df: pd.DataFrame,
    search_params: dict,
    mode: str,
    start_yr: int | None = None,
    end_yr: int | None = None,
    dy_vals: Iterable | None = None,
    exempt_static_conversions: bool = True,
) -> pd.DataFrame
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `df` | DataFrame | Source rows. Typically `combined_data` or a `Set`-filtered subset. |
| `search_params` | dict | `{column_name: list_of_values}`. Empty/None values are skipped. |
| `mode` | str | One of `"All Years"`, `"Specific Years"`, `"Range"`, `"Most Recent Global"`, `"Most Recent per Path"` (UI labels). |
| `start_yr`, `end_yr` | int | For `"Range"` mode, inclusive bounds. |
| `dy_vals` | iterable | For `"Specific Years"` mode, the list of selected years. |
| `exempt_static_conversions` | bool | When True (default), Unit Conversions + Magnitude Adjustments bypass all filters. |

## Output

A new `pd.DataFrame` containing the surviving rows. The original `df` is not modified.

## Three rule layers (same as the engine)

```
1. Column filters
   For each (column, values) in search_params:
       Build a mask that's True if:
         - The row is a Unit Conversion / Magnitude Adjustment AND exempt_static_conversions, OR
         - The row is a Chemical Property AND column is non-chemical (carve-out), OR
         - The row's column value is in the values list
       AND the running mask with this one.

2. Temporal filter
   Build a temp-exempt mask (True for static conversions iff exempting).
   If mode == 'Specific Years':
       keep rows where temp_exempt OR Data Year is NaN OR Data Year in dy_vals
   elif mode == 'Range':
       keep rows where temp_exempt OR Data Year is NaN OR start_yr <= Data Year <= end_yr
   else:
       no temporal filter

3. Return df[final_mask]
```

This mirrors the engine's [[UnitGraph.filter_graph]] rules but expressed as pandas mask operations instead of NetworkX edge iteration.

## Why "exempt_static_conversions" defaults to True

Because static conversions (Unit Conversion, Magnitude Adjustment) don't have meaningful Data Years or Agency/Country/etc. attributes. Filtering them out would amputate the conversion graph's "skeleton" of identity relationships that everything else builds on.

Setting it to False is rarely useful — only when computing counts of *how many static conversions would also match a given filter*, which the UI currently doesn't do.

## Not handled here

This function doesn't implement the `recent_global` / `recent_edge` modes. Those require a two-pass approach (scan all rows, then pick the right vintage per pair), which is duplicated work on the pandas side — the UI doesn't currently show counts based on those modes. If counts matter for those modes, add a second-pass implementation; otherwise the current UI just shows the count for the equivalent "All Years" filter.

## Usage

```python
# Compute the row count for the GHG Emissions module
temp = apply_db_and_temporal_filters(combined_data, search_params, mode, start_yr, end_yr, dy_vals)
ghg_count = len(temp[temp['Set'] == 'Emission Factors'])

# Derive available units from the surviving rows
df_for_units = apply_db_and_temporal_filters(df_for_units, ...)
available_units = sorted(
    set(df_for_units['Numerator'].dropna()).union(set(df_for_units['Denominator'].dropna()))
)
```

## See also

[[filters]] · [[UnitGraph.filter_graph]] · [[Temporal scope]] · [[app]]
