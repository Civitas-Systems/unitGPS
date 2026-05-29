---
type: concept
status: current
generation: Claude
last_updated: 2026-05-20
tags: [concept, filtering, temporal]
related:
  - [[UnitGraph.filter_graph]]
  - [[filters]]
  - [[Unit graph]]
---

# Temporal scope

Emission factors are revised every year. The `Data Year` filter — exposed in the Streamlit UI as the **Temporal Scope** radio — controls which vintage of each edge is allowed into the filtered subgraph. Five modes are supported.

## The five modes

| UI label | Engine `mode` value | Behavior |
|----------|--------------------|----------|
| All Years | `all` | No temporal filtering. Every vintage of every edge is eligible — usually causes [[Ambiguous paths]]. |
| Specific Years | `exact` | Only edges whose `Data Year` is in the user-selected list survive. |
| Range | `range` | Only edges whose `Data Year` falls within `[start_yr, end_yr]`. |
| Most Recent Global | `recent_global` | First pass finds the single newest year present anywhere in the surviving edge set; second pass keeps only edges from that year. |
| Most Recent per Path | `recent_edge` | First pass finds the newest year per `(source, target)` pair; second pass keeps only the latest edge per pair. |

## Static-conversion exemption

Unit Conversions and Magnitude Adjustments don't have meaningful Data Years (a BTU has been a BTU since 1824). They're **always retained** regardless of which temporal mode is active — that's the `exempt_static_conversions=True` path in [[filters.apply_db_and_temporal_filters]] and the parallel branch in [[UnitGraph.filter_graph]].

## The two-pass design

`recent_global` and `recent_edge` can't be done in one pass because the answer depends on values you haven't seen yet. So [[UnitGraph.filter_graph]] does:

```
Pass 1:
    for each edge in the full graph:
        decide if it survives the column filters
        if yes, remember it AND track the global max year
Pass 2:
    apply the temporal-mode-specific rule to the remembered edges
    emit the survivors to the output graph
```

`all`, `exact`, and `range` collapse into a single pass because their rule is per-edge.

## Edges with no Data Year

Some rows have `Data Year = NaN`:

- All Unit Conversions and Magnitude Adjustments (no vintage applies).
- Some Chemical Properties.
- Older emission factor rows from datasets that didn't track vintage.

These **always survive** the temporal filter regardless of mode. The reasoning is that a NaN year is a statement of "this value isn't time-varying," not "we don't know when it's from."

## Interaction with Range mode

Range mode (`recent_edge` and `range`) gets one important detail wrong if you're not careful: it's `[start, end]` inclusive, not Python's half-open `[start, end)`. So `Range 2020 to 2023` matches Data Years 2020, 2021, 2022, AND 2023.

The Streamlit UI defaults to `[max_db_year - 4, max_db_year]` (a five-year window ending at the most recent vintage in the data).

## See also

[[UnitGraph.filter_graph]] · [[filters]] · [[Ambiguous paths]] · [[Data Library schema]]
