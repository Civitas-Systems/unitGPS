---
type: concept
status: current
generation: Claude
last_updated: 2026-05-23
tags: [concept, ambiguity, edge-picks, ui, engine]
related:
  - "[[Ambiguous paths]]"
  - "[[calculate_conversion_factor]]"
  - "[[determine_conversion]]"
  - "[[determine_ghg_emissions]]"
  - "[[renderers - conversion]]"
---

# Edge picks for ambiguous paths

How a user's choice of "use this specific emission factor, not the default one" flows from a click in the UI all the way down to the engine's multiplication chain.

## The problem

When the graph has multiple parallel edges between the same two nodes — typically because two agencies publish different emission factors for the same fuel — the calculator has to pick one. The default ([[Ambiguous paths|legacy behaviour]]) is "pick edge 0, flag the path as ambiguous, let the user narrow filters." That's fine when filtering uniquely resolves the conflict; it's a dead end when the user genuinely wants to compare alternatives.

## The shape of a "pick"

A pick is an entry in the dict `edge_picks: {(source, target): edge_index}`. The engine reads it inside [[calculate_conversion_factor]]:

```python
pick_idx = 0
if edge_picks and (u, v) in edge_picks:
    requested = edge_picks[(u, v)]
    pick_idx = max(0, min(int(requested), edge_count - 1))  # defensive clamp
step_details["chosen_edge_idx"] = pick_idx
primary_val = step_values[pick_idx]
```

Three properties matter:

| Property | What it means |
|----------|--------------|
| **Per-edge, not per-path** | A pick is keyed by `(source, target)`. If two different paths share that edge, both use the same pick — there's only one truth for which alternative the user prefers. |
| **Sticky** | Picks live in `st.session_state["_edge_picks"]` so they survive reruns. Changing modules or filters doesn't wipe them. |
| **Defensive** | Out-of-bounds or negative indices clamp silently. A stale pick from a previous filter state can't crash the engine. |

## Flow end-to-end

1. **User clicks**. In the audit step card, an `st.expander("⚡ N alternatives — currently using #K")` opens to an `st.radio` of the available edges. Each option shows the multiplier + agency + context.
2. **Pick persists.** The picker's `on_change` writes `st.session_state["_edge_picks"][(u, v)] = chosen_idx` and `st.rerun()`s.
3. **Renderer reads the dict.** `render_conversion_panel` and `render_emissions_panel` pull `st.session_state["_edge_picks"]` and forward it to [[determine_conversion]] / [[determine_ghg_emissions]].
4. **Engine applies the pick.** [[calculate_conversion_factor]] uses `edge_picks.get((u, v), 0)` to choose `step_values[pick_idx]`. The audit carries `chosen_edge_idx` so the UI can echo back which option was used.
5. **Renderer surfaces state.** The picker label updates from "#K" to "#K+1" so the user sees their choice took effect; the calculated output reflects the new edge value.

## Why this matters

Without per-edge picks, the only way to disambiguate was to add more filter selections until exactly one row survived. That's painful when:
- The user wants to *compare* EPA vs IPCC for the same fuel (they want both alternatives visible)
- The conflict is on a single step in a multi-step path (overfiltering kills unrelated valid edges)
- The "right" answer is context-dependent (compliance reporting wants one source, audit modelling wants another)

Edge picks let you keep all alternatives in the graph and choose per step.

## See also

[[Ambiguous paths]] · [[calculate_conversion_factor]] · [[determine_conversion]] · [[determine_ghg_emissions]] · [[renderers - conversion]]
