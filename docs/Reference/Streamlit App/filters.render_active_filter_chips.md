---
type: function
module: streamlit_app.filters
file: apps/streamlit_app/filters.py
status: current
generation: Claude
last_updated: 2026-05-23
tags: [ui, filters, chips]
related:
  - "[[filters]]"
  - "[[filters.render_filter_tabs]]"
  - "[[filters.dynamic_multiselect]]"
---

# filters.render_active_filter_chips

Display-only chip strip summarising every active filter selection. Sits above the filter tab group as a scannable "what's currently narrowing my search" indicator.

## Signature

```python
def render_active_filter_chips(theme: dict) -> None
```

## What it renders

For each known filter key with a non-empty session_state value, one chip:

```
Active filters:  [CHEMICAL TYPE Anthracite]  [AGENCY EPA]  [SCOPE 1]
```

Each chip carries:
- The friendly label (`"Chemical Type"`, not the raw `"Source-Chemical Type"` column name) in small uppercase secondary text
- The selected value in primary text, slightly bold
- A neutral surface background with a 1px theme border

Multi-select selections render as multiple chips (one per selected value).

## How it knows the labels

```python
_FILTER_LABELS: dict[str, str] = {
    "Source-Chemical Category": "Chemical Category",
    "Source-Chemical Type": "Chemical Type",
    "Formula": "Formula",
    "Property": "Property",
    "Process1": "Process 1",
    "Process2": "Process 2",
    "Scope": "Scope",
    "Category": "Category",
    "Region": "Region",
    "Country": "Country",
    "State": "State",
    "Agency": "Agency",
    "Dataset": "Dataset",
    "Data Year": "Data Year",
}
```

`_FILTER_LABELS` maps raw column names (used as session_state keys by [[filters.dynamic_multiselect]]) to human labels. Adding a new filterable column? Add its key/label pair here.

## Display-only

Chips have no remove `×` button. To clear a filter the user opens the corresponding tab in the filter UI and unticks the value. This was a deliberate scope cut — fully interactive chips with click-to-remove require a per-chip Streamlit widget which gets clunky at scale. The chip strip's job is *visibility*, not editing.

A future enhancement could add interactive chips when Streamlit gets cheaper inline button-in-text widgets.

## See also

[[filters]] · [[filters.render_filter_tabs]] · [[filters.dynamic_multiselect]]
