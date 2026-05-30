---
type: concept
status: current
generation: Claude
last_updated: 2026-05-30
tags: [concept, engine, ui, filtering]
related:
  - "[[UnitGraph.filter_graph]]"
  - "[[filters.apply_db_and_temporal_filters]]"
  - "[[shortest_path_edges]]"
  - "[[Unit graph]]"
---

# Pathway-scoped filters

Two different filtering jobs run on every search, and conflating them caused the "electricity pathway still offers Anthracite" class of bug:

1. **Edge admission** — which *edges* survive into the graph pathfinding runs on. This is [[UnitGraph.filter_graph]]'s one rule.
2. **Option scoping** — which *values* appear in the filter dropdowns and module counts, given the chosen Source and Target. This is `apply_pathway_scope`.

This page is about (2).

## The problem it solves

If you're converting `J → kg`, the Database-Filters dropdowns shouldn't offer chemical types, regions, or datasets that can never appear on a `J → kg` route. But scoping by literal *unit* reachability is too strict: an electricity emission factor is `MWh → kg`, and `J` has no direct edge to `MWh` — yet it should still be offered, because `J` is **Energy** and can reach any energy unit, and electricity EFs start from an energy unit.

## The rule: scope by dimension, not unit

`apply_pathway_scope(df, graph_df, source_unit, target_unit, node_attrs)` keeps a row (a `Denominator → Numerator` edge) when:

```
dim(Denominator) is reachable FROM dim(source_unit)
        AND
dim(Numerator)   can REACH dim(target_unit)
```

Reachability is computed once on a **dimension-reduced graph** by `_dimension_reach`: collapse every unit to its `Unit Dimension`, merge parallel edges, then take forward reachability from the source dimension and reverse reachability into the target dimension (two `single_source_shortest_path_length` calls). So *every* unit of an on-pathway dimension is offered — `J` (Energy) keeps the electricity EF because both endpoints are Energy→Weight and the dimensional path exists.

## Why dimension-level is the right grain

| Grain | Behaviour | Verdict |
|-------|-----------|---------|
| Unit-level | Only offer values on a literal `source_unit → target_unit` edge path | Too strict — drops valid EFs whose units differ but dimensions match |
| Dimension-level | Offer values for any reachable *dimension*, all child units | Correct — matches how the data is actually organized |
| Unscoped | Offer everything | Noisy — shows fuels for an electricity conversion |

Dimension-level is the middle ground that matches user intent.

## Interaction with edge admission

These compose. `apply_pathway_scope` narrows the **frame the dropdowns are built from**; [[UnitGraph.filter_graph]] then admits **edges** from the user's actual picks. So eGRID still partitions out fuels (admission rule: a blank eGRID column excludes fuel rows) *and* the eGRID region list only shows regions reachable on the chosen dimensional pathway (scoping). Different jobs, different functions.

## Applied to the Source/Target pickers too

The same dimension-reachability logic scopes the **Source/Target dimension and unit dropdowns** (`dimension_reach` in `filters.py`, called from `app.py`), so you can only choose a target a source can reach:

- Pick **Area** as source and the target offers only Area (Area reaches only Area) — both the dimension list *and* the unit list narrow in lockstep.
- With the **GHG** module on, the target is locked to Weight, so the *source* list narrows to just the dimensions that can reach Weight (Energy, etc. — via emission-factor edges in the active modules).

`dimension_reach` returns `(reachable_from_source, can_reach_target)` from the dimension-reduced graph (`networkx.descendants` / `ancestors`). Reachability is computed on the **active-module** frame (`df_modules`), so enabling/disabling GHG or Fuel modules changes what's reachable — correctly, since EFs only exist when the GHG module is on.

## Graceful fallback

`apply_pathway_scope` returns the **full** frame unchanged when Source/Target are unset, identical, dimensionless, or genuinely unreachable — so the filter panel never blanks out by surprise.

## See also

[[UnitGraph.filter_graph]] · [[filters.apply_db_and_temporal_filters]] · [[shortest_path_edges]] · [[Unit graph]]
