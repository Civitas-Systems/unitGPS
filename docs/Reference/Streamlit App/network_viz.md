---
type: module
module: streamlit_app.network_viz
file: apps/streamlit_app/network_viz.py
status: current
generation: Claude
last_updated: 2026-05-24
tags: [ui, visualization, network, matplotlib, port]
related:
  - "[[Network visualization]]"
  - "[[renderers - conversion]]"
  - "[[renderers - emissions]]"
---

# network_viz

Matplotlib + NetworkX rendering of the full conversion graph with optional highlighted paths. Ported from `v0.4-Antigravity/03-network.ipynb`.

## Public API

| Symbol | Purpose |
|--------|---------|
| `DIMENSIONS` | Dict of `{dimension: {Color, Default Position}}` — fixed 2D anchor per Dimension. |
| `PATH_STYLE_CONFIG` | Per-path color palette + Background/Active/Line style sections. |
| `GHG_PATH_COLORS` | `{CO2: violet, CH4: green, N2O: red}` — consistent with the rest of the app's accents. |
| `compute_styled_graph_and_layout(_graph_engine)` | Cached: returns `(styled_graph, layout)`. The underscore on `_graph_engine` tells Streamlit not to hash it. |
| `render_network_figure(graph_engine, highlight_paths=None, path_colors=None, *, figsize=(12,12), show_dimension_labels=True)` | Returns a matplotlib `Figure`. Caller passes to `st.pyplot`. |

## Layout: spring-around-fixed-dimensions

Each Dimension's nodes are extracted into a subgraph; `nx.spring_layout` runs on that subgraph centered at the Dimension's fixed position. Result: dimensional clusters stay in stable positions across sessions while internal arrangement reflects connectivity.

Parameters (module-private constants):
- `scale=1.5` — node spread within each cluster
- `cluster_radius=1.0` — multiplier on dimension centroids (separation between clusters)
- `k=0.72` — optimal node distance in spring layout
- `iterations=100` — spring iterations
- `seed=42` — deterministic so layouts don't shuffle between calls

## Three-layer rendering

| Layer | Drawn | Purpose |
|-------|-------|---------|
| Background | Dimmed edges + labels (only non-active nodes) | Show the graph topology without competing with the highlight |
| Highlighted paths | One colored line per path, stacked widths (thicker → further index) | Stack so multiple simultaneous paths all visible |
| Active nodes | Bold larger nodes + labels (only on highlighted paths) | Make the path's endpoints + intermediates stand out |

Optional fourth layer: `show_dimension_labels=True` adds a centroid label per Dimension cluster in its color.

## No mutation of engine graph

The engine's `graph_engine.G` is **not** mutated. `_build_styled_graph` clones into a new `MultiDiGraph` and stamps `Position` + `Color` attributes on the clone, leaving the engine's graph untouched.

## Flatten step

`_flatten_graph(G)` collapses parallel edges per Set group into one summary edge with a label like `kg per lb [Unit Conversion] ×3`. Without this, repeated edges would visually clutter the render.

## Color blending

`_blend_colors(c1, c2)` averages two colors and returns hex. Used for edge coloring — the engine's edges inherit a blend of their source and target node colors so an edge between Energy (pink) and Weight (purple) shows in the mix. Defensive against bad input (falls back to gray).

## Origin

The original notebook had three functions: `visualize_network`, `visualize_path`, `visualize_emissions`. This port unifies them via a single `render_network_figure` with `highlight_paths` + `path_colors` parameters. The path-stacking + dimming logic carries through verbatim from the original `path_style_config`.

## See also

[[Network visualization]] · [[renderers - conversion]] · [[renderers - emissions]]

## Updated 2026-05-30
`render_pathway_sankey` / `_hex_to_rgba` were **removed** (the Sankey was dropped). Current
functions: `render_network_figure` (matplotlib, static) and `render_network_plotly`
(interactive). Both accept `label_color` so the highlighted-path unit labels use the
active theme's text colour (legible on light themes); the static render no longer labels
*every* node — only the path + dimension names. See [[Network visualization]], [[CHANGELOG]] 10.4 / 11.1.
