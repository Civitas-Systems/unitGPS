---
type: module
module: streamlit_app.filters
file: apps/streamlit_app/filters.py
lines: "1-292"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, filtering, ui]
related:
  - "[[filters.apply_db_and_temporal_filters]]"
  - "[[filters.get_filtered_df]]"
  - "[[filters.get_options]]"
  - "[[filters.dynamic_multiselect]]"
  - "[[filters.get_units_for_dim]]"
  - "[[filters.render_filter_tabs]]"
  - "[[filters.build_search_params]]"
  - "[[UnitGraph.filter_graph]]"
  - "[[Temporal scope]]"
---

# filters (module overview)

Two responsibilities bundled in one module:

1. **Pandas-side filtering** — compute live module counts and available unit lists before the actual graph filter runs. Mirrors [[UnitGraph.filter_graph]]'s rules.
2. **UI rendering** for the dynamic Database Filters tab group (Resources / Process / Location / Data Source) and the final search-params builder handed to the engine.

## Public API

| Symbol | Type | Purpose |
|--------|------|---------|
| `COLS_TO_EXTRACT` | `list[str]` | The 12 column names the UI exposes as filters. |
| `FILTER_GROUPS` | `dict[str, list[str]]` | Maps tab labels → column lists. Determines tab grouping. |
| [[filters.apply_db_and_temporal_filters]] | function | Apply column + Data Year filters to a DataFrame. The pandas-side counterpart of `filter_graph`. |
| [[filters.get_filtered_df]] | function | DataFrame view honoring all filters except one (for "other filters" multiselect logic). |
| [[filters.get_options]] | function | Available string options for a multiselect, given other active filters. |
| [[filters.dynamic_multiselect]] | function | Streamlit multiselect with live option count + placeholder. |
| [[filters.get_units_for_dim]] | function | Units belonging to a given dimension (or any if None). |
| [[filters.render_filter_tabs]] | function | Render the four-tab Database Filters UI. |
| [[filters.build_search_params]] | function | Build the search_params dict the engine expects. |

## Constants

```python
COLS_TO_EXTRACT = [
    'Source-Chemical Category', 'Source-Chemical Type',
    'Property', 'Formula',
    'Process1', 'Process2', 'Scope', 'Category',
    'Country', 'eGRID',
    'Agency', 'Dataset',
]

FILTER_GROUPS = {
    'Resources':   ['Source-Chemical Category', 'Formula', 'Source-Chemical Type', 'Property'],
    'Process':     ['Process1', 'Process2', 'Scope', 'Category'],
    'Location':    ['Country', 'eGRID'],
    'Data Source': ['Agency', 'Dataset'],
}
```

`COLS_TO_EXTRACT` is the canonical list of filter columns; both pandas and engine sides iterate it. `FILTER_GROUPS` decides which tab each column appears under in the UI.

## Why duplicate filter logic from the engine?

Live module counts and available-unit dropdowns need to know "what would the filtered data look like" *before* the user clicks Calculate and before any pathfinding runs. The cheapest way is to mirror [[UnitGraph.filter_graph]]'s rules on pandas — at the cost of two sources of truth.

This duplication is on the cleanup list — see [[architecture#4. Differences from Antigravity]].

## See also

[[filters.apply_db_and_temporal_filters]] · [[filters.render_filter_tabs]] · [[filters.build_search_params]] · [[UnitGraph.filter_graph]] · [[Temporal scope]]
