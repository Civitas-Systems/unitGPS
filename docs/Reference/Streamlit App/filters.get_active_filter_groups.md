---
type: function
parent: "[[filters]]"
module: streamlit_app.filters
file: apps/streamlit_app/filters.py
status: current
generation: Claude
last_updated: 2026-05-30
tags: [streamlit, filters]
related: ["[[filters.render_filter_group]]", "[[Pathway-scoped filters]]"]
---

# filters.get_active_filter_groups

Return the names of the filter categories (`Resources`, `Process`, `Location`,
`Data Source`) that currently have any options for the scoped frame. `Process` is kept
when `do_ghg=True` even with no options. Drives the inline segmented selector in the
Database Filters toolbar (replaced the old `st.tabs`).

```python
def get_active_filter_groups(df_for_units, do_ghg=False) -> list[str]
```

Each group maps to columns via `FILTER_GROUPS`; a group is "active" if any of its columns
has options ([[filters.get_options]]). See [[filters.render_filter_group]] for rendering.
