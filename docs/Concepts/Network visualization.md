---
type: concept
status: current
generation: Claude
last_updated: 2026-05-24
tags: [concept, ui, visualization, network, matplotlib]
related:
  - "[[network_viz]]"
  - "[[Unit graph]]"
  - "[[Hero pathway stepper]]"
---

# Network visualization

A matplotlib + NetworkX rendering of the *entire conversion graph* with the active calculation's path highlighted. Complements the hero pathway stepper — the stepper shows the path you ran; this shows that path *in the context of every other conversion the engine could have done*.

## The visual

```
                    [Time]
                       •
                    s s s s
   [Length]   [Area]      [Logistics]
       •         •              •
    s s s s s s s s s s     s s s s s
                                
  [Energy] ====highlighted====> [Weight]   ← your path overlaid
    pink                       purple
    s s s s s                  s s s s
                                
            [Volume]
               •
            s s s s

            [Power]
               •
            s s s s
```

Each Dimension (Energy, Weight, Time, etc.) is a cluster centered on a fixed 2D position with its own color. Inside each cluster, a per-dimension spring layout arranges the units. Edges are drawn dimmed; the active path is overlaid in bold color on top.

## Why it's useful

The hero stepper answers *"how did my conversion get from A to B?"* The network view answers *"how does my conversion sit in the broader graph?"* Two distinct questions:

| Question | Best view |
|----------|-----------|
| What was the multiplication chain for **this** calc? | Hero stepper |
| What other routes might exist if I changed filters? | Network view |
| Is this conversion typical or unusual for my data? | Network view |
| What's the topology of the data library? | Network view (no highlights) |

## Layout philosophy: dimensional anchoring

Default 2D positions per dimension:

| Dimension | Position | Color |
|-----------|----------|-------|
| Time | (-2.5, 5.0) | dark gray |
| Area | (2.5, 5.0) | blue |
| Length | (0.0, 2.5) | green |
| Energy | (-3.5, 0.0) | pink |
| Volume | (3.5, 0.0) | orange |
| Weight | (0.0, -3.5) | purple |
| Power | (-5.0, -5.0) | brown |
| Logistics | (5.0, -5.0) | cyan |

Each Dimension's nodes get a spring layout *within* the dimension subgraph, centered at the fixed position. Result: clusters stay in roughly the same place across calls, so the user builds visual familiarity with where each dimension lives. Edges between dimensions show as the connective tissue.

## Highlight semantics

When ``highlight_paths`` is passed, the function:

1. Computes the set of *active nodes* (every unit on a highlighted path)
2. Renders the background (dimmed) layer: all edges + labels for non-active nodes
3. Stacks each path as a colored overlay (Path 1 thinnest on top, Path N thickest on bottom — so simultaneously-highlighted paths are all visible)
4. Re-draws active nodes prominently (bold labels, larger size) so the path stands out

For GHG emissions, three paths overlay simultaneously with consistent gas-accent colors (CO₂ violet, CH₄ green, N₂O red).

## Where it lives in the UI

- **Conversions panel** — one "🌐 Show network view" expander per path tab (default closed). Shows that path highlighted on the full graph.
- **GHG Emissions panel** — one "🌐 Show GHG network view" expander at the bottom of the panel. Shows all three gas paths overlaid.

Default-closed because the figure is expensive (full graph render at 11x11in) — only the user explicitly requesting it pays that cost.

## Performance

`compute_styled_graph_and_layout(graph_engine)` is wrapped in `st.cache_resource` so the expensive spring-around-fixed-dimension computation runs *once per session*. Subsequent renders only redraw the figure, not recompute the layout.

## Origin

Ported from `v0.4-Antigravity/03-network.ipynb` (the original notebook by the project author). The notebook had three `visualize_*` functions; this port unifies them as a single `render_network_figure` taking optional `highlight_paths` and `path_colors`. See [[network_viz]].

## See also

[[network_viz]] · [[Unit graph]] · [[Hero pathway stepper]]

## Updated 2026-05-30
Rendered two ways via the Output-options "Network render" toggle: **Interactive** (Plotly,
`render_network_plotly` — hover/zoom/pan) and **Static** (matplotlib). Path node labels
are theme-aware (legible on light themes); only the highlighted path + dimension names are
labelled, so the path isn't buried. An experimental pathway Sankey was tried and removed
(uniform-width links carried no quantity). See [[network_viz]].
