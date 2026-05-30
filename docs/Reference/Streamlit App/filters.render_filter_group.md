---
type: function
parent: "[[filters]]"
module: streamlit_app.filters
file: apps/streamlit_app/filters.py
status: current
generation: Claude
last_updated: 2026-05-30
tags: [streamlit, filters]
related: ["[[filters.get_active_filter_groups]]", "[[filters.dynamic_multiselect]]"]
---

# filters.render_filter_group

Render one filter category's widgets, full width. Replaced the per-tab bodies of the old
`render_filter_tabs` when the filter UI moved to an inline segmented control.

```python
def render_filter_group(g_name, df_for_units, theme) -> None
```

- **Resources** — Chemical Category / Type / Formula / Property
- **Process** — Process 1/2, Scope (1/2/3 checkboxes), Category
- **Location** — Country, eGRID Region
- **Data Source** — Agency, Dataset

The app renders the selected group visibly and the others inside a `display:none`
container so multiselect state persists across switches (mirrors how `st.tabs` kept every
panel mounted). The legacy `render_filter_tabs` remains for compatibility.
