---
type: class
module: unitgps.engine.data
file: src/unitgps/engine/data.py
lines: "11-121"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [engine, data-loading, class]
related:
  - "[[DataLoader.load_data_library]]"
  - "[[DataLoader.get_units_attributes]]"
  - "[[DataLoader.load_gwps]]"
  - "[[UnitGraph]]"
  - "[[Data Library schema]]"
  - "[[IPCC GWPs]]"
---

# DataLoader

The entry point for getting data from disk into the engine. Holds the two xlsx paths and exposes three methods that produce ready-to-use DataFrames for downstream graph construction.

## Why a class?

The class wraps the two file paths so callers don't have to pass them on every method call. Aside from path storage, the methods are functional — no mutable state, no side effects beyond reading files.

## Construction

```python
def __init__(self, data_library_path: str, gwp_file_path: str) -> None:
    self.data_library_path = data_library_path
    self.gwp_file_path = gwp_file_path
```

Pure attribute storage; no I/O. The xlsx files are not opened until you call a method.

| Param | Type | Description |
|-------|------|-------------|
| `data_library_path` | `str` | Path to `Data Library, <date>, <range>.xlsx` (or `.parquet`). |
| `gwp_file_path` | `str` | Path to `IPCC GWPs AR4-AR6.xlsx`. |

## Methods

| Method | Purpose | Output shape |
|--------|---------|--------------|
| [[DataLoader.load_data_library]] | Load + clean + synthesize reciprocals | `pd.DataFrame` ~6,000 × 38 |
| [[DataLoader.get_units_attributes]] | Per-unit metadata (dimension, system, color) | `dict[str, dict]` |
| [[DataLoader.load_gwps]] | Load IPCC GWPs, split Indicator column | `pd.DataFrame` ~1,200 × 4 |

## Typical usage

```python
from unitgps.engine import DataLoader, UnitGraph

loader = DataLoader(
    data_library_path='data/Data Library, 2025-10-18, 1960-2023.xlsx',
    gwp_file_path='data/IPCC GWPs AR4-AR6.xlsx',
)
df = loader.load_data_library()
node_attrs = loader.get_units_attributes(df)
gwps = loader.load_gwps()

graph = UnitGraph(df, node_attrs)
# graph is now ready for filter_graph() + pathfinding + calculate
```

This is exactly the sequence that `apps/streamlit_app/app.py:load_engine()` performs inside Streamlit's `@st.cache_resource` so the engine builds once per session.

## Design notes

- **No caching at this layer.** Each method call re-reads the xlsx. Caching is the caller's job (Streamlit does it with `@st.cache_resource`; tests do it with a session-scoped pytest fixture).
- **Returns DataFrames, not the graph.** The class deliberately stops short of building the [[UnitGraph]] — separation of concerns means you can swap in a different graph type without touching the loader.
- **No validation.** A malformed xlsx will surface as a pandas error rather than a friendly engine message. Cleanup item: explicit schema check in [[architecture#4. Differences from Antigravity]].

## See also

[[DataLoader.load_data_library]] · [[DataLoader.get_units_attributes]] · [[DataLoader.load_gwps]] · [[UnitGraph]] · [[Data Library schema]]
