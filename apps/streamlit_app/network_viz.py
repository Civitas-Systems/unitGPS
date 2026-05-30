"""Network visualization for the conversion graph.

Ports the original v0.4-Antigravity ``03-network.ipynb`` visualization
toolkit: spring-around-fixed-dimension layout (each Dimension clustered
around a fixed centroid on the plane), edge color blending, parallel-edge
flattening, and the per-path / per-emissions highlight overlays.

Key differences from the notebook port:

- No mutation of the engine's graph. Every visualization clones into a local
  ``MultiDiGraph`` that carries Position/Color attributes for layout, leaving
  ``graph_engine.G`` clean.
- No global variables. The DIMENSIONS / PATH_STYLE_CONFIG dicts are module
  constants; everything else is parameter-passed.
- Layout is cached via ``st.cache_resource`` keyed by the loaded engine, so
  the expensive spring computation runs once per session.
- Figures default to 12×12in (the notebook used 24×24in, which is unusable
  inside a Streamlit panel).

Returns matplotlib Figure objects so callers can pass directly to st.pyplot.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import numpy as np
import streamlit as st

# matplotlib is imported lazily inside the rendering functions so this module
# can load even when matplotlib isn't installed. Callers (the result-panel
# renderers) wrap render calls in try/except and surface ImportError as a
# graceful "Network view unavailable" warning, rather than crashing the app.
try:
    import matplotlib.colors as mcolors
    import matplotlib.pyplot as plt
    _MATPLOTLIB_AVAILABLE = True
except ImportError:  # pragma: no cover
    mcolors = None  # type: ignore[assignment]
    plt = None      # type: ignore[assignment]
    _MATPLOTLIB_AVAILABLE = False


def _require_matplotlib() -> None:
    """Raise a clear ImportError when matplotlib is missing."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "matplotlib is required for network_viz rendering. "
            "Install via: pip install matplotlib>=3.7 "
            "(or re-run apps/streamlit_app/run.bat which now pulls it in via requirements/streamlit.txt)."
        )


# --------------------------------------------------------------------------- #
# Configuration                                                                 #
# --------------------------------------------------------------------------- #

# Fixed centroid positions on the 2D plane per Dimension, with a recognizable
# color so dimensional clusters stay visually distinct.
DIMENSIONS: Dict[str, Dict[str, Any]] = {
    "Time":      {"Color": "#222222", "Default Position": (-2.5,  5.0)},
    "Area":      {"Color": "#1F77B4", "Default Position": ( 2.5,  5.0)},
    "Length":    {"Color": "#2CA02C", "Default Position": ( 0.0,  2.5)},
    "Energy":    {"Color": "#E377C2", "Default Position": (-3.5,  0.0)},
    "Volume":    {"Color": "#FF7F0E", "Default Position": ( 3.5,  0.0)},
    "Weight":    {"Color": "#9467BD", "Default Position": ( 0.0, -3.5)},
    "Power":     {"Color": "#8C564B", "Default Position": (-5.0, -5.0)},
    "Logistics": {"Color": "#17BECF", "Default Position": ( 5.0, -5.0)},
}

PATH_STYLE_CONFIG: Dict[str, Dict[str, Any]] = {
    "Path 1":  {"Color": "#1F77B4"},   # blue
    "Path 2":  {"Color": "#2CA02C"},   # green
    "Path 3":  {"Color": "#D62728"},   # red
    "Path 4":  {"Color": "#FF7F0E"},   # orange
    "Path 5":  {"Color": "#9467BD"},   # purple
    "Path 6":  {"Color": "#8C564B"},   # brown
    "Path 7":  {"Color": "#E377C2"},   # hotpink
    "Path 8":  {"Color": "#BCBD22"},   # olive
    "Path 9":  {"Color": "#17BECF"},   # cyan
    "Path 10": {"Color": "#7F7F7F"},   # gray
    "Background": {
        "Node Color": "#CCCCCC", "Node Size": 100, "Node Alpha": 0.15,
        "Edge Color": "#CCCCCC", "Edge Width": 0.5, "Edge Alpha": 0.20,
        "Label Size": 10, "Label Alpha": 0.20,
    },
    "Active": {
        "Node Size": 300, "Node Alpha": 1.0, "Node Border Width": 2.0,
        "Label Size": 14, "Label Weight": "bold",
        "Halo Color": "white", "Halo Width": 3,
    },
    "Line": {
        "Base Width": 3.0, "Width Step": 2.5,  # stacked-path width increment
        "Alpha": 0.9, "Arrow Size": 25,
    },
}

# GHG-specific palette so CO2/CH4/N2O get consistent colors matching the rest
# of the app's accent system.
GHG_PATH_COLORS: Dict[str, str] = {
    "CO2": "#8B5CF6",  # violet — matches theme primary
    "CH4": "#10b981",  # green  — matches theme success
    "N2O": "#ef4444",  # red    — matches theme danger
}


# --------------------------------------------------------------------------- #
# Layout (spring-around-fixed-dimensions)                                       #
# --------------------------------------------------------------------------- #


def _blend_colors(c1: str, c2: str) -> str:
    """Average two colors and return the result as hex. Defensive on bad input."""
    try:
        r1, g1, b1 = mcolors.to_rgb(c1)
        r2, g2, b2 = mcolors.to_rgb(c2)
        return mcolors.to_hex(((r1 + r2) / 2, (g1 + g2) / 2, (b1 + b2) / 2))
    except (ValueError, TypeError):
        return "#888888"


def _spring_around_fixed_dimensions(
    G: nx.MultiDiGraph,
    *,
    scale: float = 1.5,
    cluster_radius: float = 1.0,
    k: float = 0.72,
    iterations: int = 100,
    seed: int = 42,
) -> Dict[Any, Tuple[float, float]]:
    """Per-dimension spring layout, each cluster centered at its fixed default.

    Returns ``{node: (x, y)}``. Deterministic when ``seed`` is fixed.
    """
    node_positions: Dict[Any, Tuple[float, float]] = {}
    for dim, d_data in DIMENSIONS.items():
        nodes_in_dim = [
            n for n, attr in G.nodes(data=True)
            if attr.get("Unit Dimension") == dim
        ]
        if not nodes_in_dim:
            continue
        subgraph = G.subgraph(nodes_in_dim)
        cx, cy = d_data["Default Position"]
        center = (cx * cluster_radius, cy * cluster_radius)
        sub_pos = nx.spring_layout(
            subgraph,
            center=center,
            scale=scale,
            k=k,
            iterations=iterations,
            seed=seed,
        )
        node_positions.update(sub_pos)
    return node_positions


def _build_styled_graph(graph_engine) -> Tuple[nx.MultiDiGraph, Dict[Any, Tuple[float, float]]]:
    """Build a styled copy of the engine's graph plus its layout.

    The copy carries 'Color' + 'Position' on nodes and 'Color' + 'Weight' on
    edges. The engine's original graph is untouched.
    """
    base = graph_engine.G
    G = nx.MultiDiGraph()
    G.add_nodes_from(base.nodes(data=True))
    G.add_edges_from(base.edges(keys=True, data=True))

    layout = _spring_around_fixed_dimensions(G)

    # Stamp node Color + Position
    for n, data in G.nodes(data=True):
        dim = data.get("Unit Dimension")
        data["Color"] = DIMENSIONS.get(dim, {}).get("Color", "#888888")
        data["Position"] = layout.get(n, (0.0, 0.0))

    # Stamp edge Color (blend of endpoint colors) + Weight
    for u, v, k_edge, d in G.edges(keys=True, data=True):
        d["Color"] = _blend_colors(
            G.nodes[u].get("Color", "#888888"),
            G.nodes[v].get("Color", "#888888"),
        )
        if d.get("Set") in ("Unit Conversion", "Unit Conversions"):
            d["Weight"] = 10
        elif d.get("Set") == "Magnitude Adjustment":
            d["Weight"] = 4
        else:
            d["Weight"] = 1

    return G, layout


@st.cache_resource(show_spinner=False)
def compute_styled_graph_and_layout(_graph_engine):
    """Cached entry-point. The underscore prefix on ``_graph_engine`` tells
    Streamlit not to hash it (graph engines are heavy and ID-equality is fine
    since they're created once per session via ``@st.cache_resource``)."""
    return _build_styled_graph(_graph_engine)


# --------------------------------------------------------------------------- #
# Flatten parallel edges (one summary edge per Set group)                       #
# --------------------------------------------------------------------------- #


def _flatten_graph(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Collapse parallel edges per Set group, keeping one summary per group."""
    flat = nx.MultiDiGraph()
    flat.add_nodes_from(G.nodes(data=True))
    for u, v in set((u, v) for u, v, _ in G.edges(keys=True)):
        groups: Dict[str, List[dict]] = {}
        for k_edge, attrs in G.get_edge_data(u, v).items():
            s = attrs.get("Set", "?")
            groups.setdefault(s, []).append(attrs)
        for set_name, attrs_list in groups.items():
            base = attrs_list[0].copy()
            count = len(attrs_list)
            conv = base.get("Conversion", "")
            base["label"] = f"{conv} [{set_name}]" + (f" ×{count}" if count > 1 else "")
            flat.add_edge(u, v, key=set_name, **base)
    return flat


# --------------------------------------------------------------------------- #
# Rendering                                                                     #
# --------------------------------------------------------------------------- #


def _draw_background_layer(flat: nx.MultiDiGraph, layout: dict, bg: dict, active_nodes: set) -> None:
    """Draw dimmed background edges + labels for nodes NOT on a highlighted path."""
    nx.draw_networkx_edges(
        flat, layout,
        edge_color=bg["Edge Color"],
        width=bg["Edge Width"],
        arrows=True, arrowstyle="-|>", arrowsize=10,
        alpha=bg["Edge Alpha"],
    )
    bg_nodes = [n for n in flat.nodes() if n not in active_nodes]
    nx.draw_networkx_labels(
        flat, layout,
        labels={n: n for n in bg_nodes},
        font_family="sans-serif",
        font_size=bg["Label Size"],
        alpha=bg["Label Alpha"],
    )


def _draw_highlighted_paths(
    flat: nx.MultiDiGraph, layout: dict, paths: List[List[str]],
    colors: Optional[List[str]] = None,
) -> None:
    """Draw each path as a colored, stacked-width overlay."""
    cfg_line = PATH_STYLE_CONFIG["Line"]
    # Reverse order so Path 1 ends up on top (drawn last)
    for i in range(len(paths) - 1, -1, -1):
        path = paths[i]
        if not path or len(path) < 2:
            continue
        if colors and i < len(colors):
            color = colors[i]
        else:
            color = PATH_STYLE_CONFIG.get(f"Path {i + 1}", {"Color": "#444444"})["Color"]
        width = cfg_line["Base Width"] + (i * cfg_line["Width Step"])
        path_edges = list(zip(path, path[1:]))
        sub = nx.DiGraph()
        sub.add_edges_from(path_edges)
        nx.draw_networkx_edges(
            sub, layout,
            edgelist=path_edges,
            width=width, edge_color=color,
            arrows=True, arrowstyle="-|>",
            arrowsize=cfg_line["Arrow Size"],
            alpha=cfg_line["Alpha"],
        )


def _draw_active_nodes(flat: nx.MultiDiGraph, layout: dict, active_nodes: set) -> None:
    """Draw highlighted nodes + bold labels on top of everything else."""
    if not active_nodes:
        return
    cfg = PATH_STYLE_CONFIG["Active"]
    nodelist = list(active_nodes)
    node_colors = [flat.nodes[n].get("Color", "#CCCCCC") for n in nodelist]
    nx.draw_networkx_nodes(
        flat, layout,
        nodelist=nodelist,
        node_color=node_colors,
        node_size=cfg["Node Size"],
        alpha=cfg["Node Alpha"],
        edgecolors="black",
        linewidths=cfg["Node Border Width"],
    )
    nx.draw_networkx_labels(
        flat, layout,
        labels={n: n for n in nodelist},
        font_family="sans-serif",
        font_size=cfg["Label Size"],
        font_weight=cfg["Label Weight"],
    )


def _draw_dimension_centroids(layout: dict, flat: nx.MultiDiGraph) -> None:
    """Label each dimension's region with its name in dimension color."""
    # Compute actual centroid per dimension from node positions
    by_dim: Dict[str, List[Tuple[float, float]]] = {}
    for n, data in flat.nodes(data=True):
        dim = data.get("Unit Dimension")
        if dim and n in layout:
            by_dim.setdefault(dim, []).append(layout[n])
    for dim, positions in by_dim.items():
        if not positions:
            continue
        xs, ys = zip(*positions)
        cx, cy = float(np.mean(xs)), float(np.mean(ys))
        color = DIMENSIONS.get(dim, {}).get("Color", "#888888")
        plt.text(
            cx, cy + 0.9, dim,
            fontsize=14, fontweight="bold",
            color=color, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color, lw=1, alpha=0.85),
        )


def render_network_figure(
    graph_engine,
    highlight_paths: Optional[List[List[str]]] = None,
    path_colors: Optional[List[str]] = None,
    *,
    figsize: Tuple[float, float] = (12, 12),
    show_dimension_labels: bool = True,
):
    """Render the full conversion network with optional highlighted paths.

    ``highlight_paths`` is a list of paths; each path is a list of node names.
    ``path_colors`` overrides the default per-path palette (used for GHG to
    color CO2/CH4/N2O consistently with the rest of the app).

    Raises ``ImportError`` if matplotlib is not installed — callers are
    expected to wrap this in try/except (the renderers in
    ``streamlit_app/renderers/`` already do).
    """
    _require_matplotlib()
    G, layout = compute_styled_graph_and_layout(graph_engine)
    flat = _flatten_graph(G)

    fig = plt.figure(figsize=figsize, dpi=110)
    bg = PATH_STYLE_CONFIG["Background"]

    paths = highlight_paths or []
    active_nodes: set = set()
    for p in paths:
        if p:
            active_nodes.update(p)

    _draw_background_layer(flat, layout, bg, active_nodes)
    _draw_highlighted_paths(flat, layout, paths, colors=path_colors)
    _draw_active_nodes(flat, layout, active_nodes)
    if show_dimension_labels:
        _draw_dimension_centroids(layout, flat)

    plt.axis("off")
    plt.tight_layout()
    return fig


def render_network_plotly(
    graph_engine,
    highlight_paths=None,
    path_colors=None,
    *,
    height: int = 620,
    show_dimension_labels: bool = True,
):
    """Interactive Plotly version of :func:`render_network_figure`.

    Hover any node for its unit + dimension; zoom, pan and drag. Reuses the same
    cached spring layout so it lines up with the static figure. Returns a Plotly
    ``Figure`` for ``st.plotly_chart``. Raises ``ImportError`` if plotly is
    missing (callers wrap this and fall back to the static figure).
    """
    try:
        import plotly.graph_objects as go
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "plotly is required for the interactive network view "
            "(pip install plotly>=5.18, or re-run run.bat)."
        ) from exc

    G, layout = compute_styled_graph_and_layout(graph_engine)
    flat = _flatten_graph(G)

    paths = highlight_paths or []
    active_nodes: set = set()
    for p in paths:
        if p:
            active_nodes.update(p)

    traces = []

    # Background edges (one None-separated trace) + dim nodes.
    bx, by = [], []
    for u, v in set((u, v) for u, v, _ in flat.edges(keys=True)):
        if u in layout and v in layout:
            (x0, y0), (x1, y1) = layout[u], layout[v]
            bx += [x0, x1, None]
            by += [y0, y1, None]
    traces.append(go.Scatter(x=bx, y=by, mode="lines",
                             line=dict(color="#9aa0a6", width=0.6),
                             opacity=0.22, hoverinfo="skip", showlegend=False))

    # Highlighted paths (reverse so Path 1 ends on top).
    for i in range(len(paths) - 1, -1, -1):
        p = paths[i]
        if not p or len(p) < 2:
            continue
        if path_colors and i < len(path_colors):
            color = path_colors[i]
        else:
            color = PATH_STYLE_CONFIG.get(f"Path {i + 1}", {"Color": "#1F77B4"})["Color"]
        width = PATH_STYLE_CONFIG["Line"]["Base Width"] + i * 1.5
        px, py = [], []
        for a, b in zip(p, p[1:]):
            if a in layout and b in layout:
                (x0, y0), (x1, y1) = layout[a], layout[b]
                px += [x0, x1, None]
                py += [y0, y1, None]
        traces.append(go.Scatter(x=px, y=py, mode="lines",
                                 line=dict(color=color, width=width),
                                 opacity=0.9, hoverinfo="skip", showlegend=False))

    bgn = [n for n in flat.nodes() if n not in active_nodes and n in layout]
    traces.append(go.Scatter(
        x=[layout[n][0] for n in bgn], y=[layout[n][1] for n in bgn],
        mode="markers", marker=dict(size=6, color="#aab", opacity=0.35),
        text=[f"{n} | {flat.nodes[n].get('Unit Dimension', '')}" for n in bgn],
        hoverinfo="text", showlegend=False))

    if active_nodes:
        an = [n for n in active_nodes if n in layout]
        traces.append(go.Scatter(
            x=[layout[n][0] for n in an], y=[layout[n][1] for n in an],
            mode="markers+text",
            marker=dict(size=15, color=[flat.nodes[n].get("Color", "#888") for n in an],
                        line=dict(color="white", width=1.5)),
            text=an, textposition="top center", textfont=dict(size=12, color="#e5e7eb"),
            hovertext=[f"{n} | {flat.nodes[n].get('Unit Dimension', '')}" for n in an],
            hoverinfo="text", showlegend=False))

    fig = go.Figure(data=traces)

    # Faint dotted "region" bubble per dimension cluster, so the groups stay
    # delineated even as nodes spring around.
    annotations, shapes = [], []
    by_dim: dict = {}
    for n, data in flat.nodes(data=True):
        dim = data.get("Unit Dimension")
        if dim and n in layout:
            by_dim.setdefault(dim, []).append(layout[n])
    for dim, ps in by_dim.items():
        xs, ys = zip(*ps)
        cx, cy = float(np.mean(xs)), float(np.mean(ys))
        r = max((((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 for x, y in ps), default=0.6) + 0.7
        col = DIMENSIONS.get(dim, {}).get("Color", "#888888")
        shapes.append(dict(
            type="circle", xref="x", yref="y",
            x0=cx - r, y0=cy - r, x1=cx + r, y1=cy + r,
            line=dict(color=col, width=1.2, dash="dot"),
            fillcolor=col, opacity=0.07, layer="below"))
        if show_dimension_labels:
            annotations.append(dict(
                x=cx, y=cy + r - 0.2, text=dim, showarrow=False,
                font=dict(size=13, color=col)))
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=8, b=8),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False, hovermode="closest", dragmode="pan",
        shapes=shapes, annotations=annotations)
    return fig
