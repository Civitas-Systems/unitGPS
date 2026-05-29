"""Hero pathway visual stepper.

Renders an audit path as a horizontal subway-map: unit nodes (cards with
symbol + dimension subtitle) connected by color-coded edges (multiplier +
set badge centered on the line). Replaces the flat 'J → mmBTU → kg' text
breadcrumb in both the Conversions panel and the GHG per-gas sections.

Pure HTML/CSS — returns a string that the caller wraps with
``st.markdown(..., unsafe_allow_html=True)``. Decoupled from Streamlit so it
stays testable.
"""

from __future__ import annotations

from typing import Callable, List

from unitgps.engine import format_sig_figs


# Step-type colors are looked up in the theme dict so they match the rest of
# the audit UI (left-border accents, badges, attribution).
_SET_ICON = {
    "static": "🔧",
    "chemical": "🧪",
    "emission": "🌫",
    "other": "•",
}


def _classify_set(set_name: str) -> str:
    """Bucket a set name into one of: static / chemical / emission / other."""
    sn = (set_name or "").strip()
    if sn in ("Unit Conversion", "Unit Conversions", "Magnitude Adjustment"):
        return "static"
    if sn == "Chemical Properties":
        return "chemical"
    if "emission" in sn.lower():
        return "emission"
    return "other"


def _set_color(set_kind: str, theme: dict) -> str:
    return {
        "static": theme.get("secondary", "#888"),
        "chemical": theme.get("success", "#10b981"),
        "emission": theme.get("danger", "#ef4444"),
        "other": theme.get("primary", "#8B5CF6"),
    }[set_kind]


def _set_short_label(set_kind: str, set_name: str) -> str:
    """Short label for the edge badge — keeps the stepper compact."""
    return {
        "static": "Unit conv" if set_name != "Magnitude Adjustment" else "Magnitude",
        "chemical": "Chemical",
        "emission": "Emission",
        "other": (set_name or "")[:12],
    }[set_kind]


def _node_html(unit: str, dim: str, theme: dict) -> str:
    """One unit node card: symbol on top, dimension subtitle beneath."""
    dim_html = (
        f"<div style='font-size: 0.65rem; color:{theme.get('secondary', '#888')} !important; "
        f"text-transform: uppercase; letter-spacing: 0.4px; margin-top: 2px;'>{dim}</div>"
        if dim
        else ""
    )
    return (
        f"<div style='flex: 0 0 auto; min-width: 78px; max-width: 140px; "
        f"padding: 10px 12px; background: {theme.get('surface', '#f5f5f5')}; "
        f"border: 1px solid {theme.get('border', '#ddd')}; border-radius: 8px; "
        f"text-align: center; display: flex; flex-direction: column; "
        f"justify-content: center; align-items: center;'>"
        f"<div style='font-family: monospace; font-size: 0.95rem; font-weight: 600; "
        f"color: {theme.get('text', '#222')} !important;'>{unit}</div>"
        f"{dim_html}"
        f"</div>"
    )


def _edge_html(value: float, set_name: str, theme: dict) -> str:
    """One labeled edge: multiplier + set badge centered on a colored line."""
    kind = _classify_set(set_name)
    color = _set_color(kind, theme)
    icon = _SET_ICON[kind]
    short = _set_short_label(kind, set_name)
    bg = theme.get("bg", "#fff")

    return (
        f"<div style='flex: 1 1 0; min-width: 110px; display: flex; "
        f"flex-direction: column; align-items: center; justify-content: center; "
        f"padding: 0 4px; position: relative; min-height: 64px;'>"
        # The line behind the label
        f"<div style='position: absolute; top: 50%; left: 0; right: 0; "
        f"height: 2px; transform: translateY(-50%); background: {color}; "
        f"opacity: 0.55;'></div>"
        # The label sits on top of the line, with the panel bg punching through
        f"<div style='position: relative; z-index: 1; background: {bg}; "
        f"padding: 2px 8px; display: flex; flex-direction: column; "
        f"align-items: center; gap: 2px; border-radius: 4px;'>"
        f"<span style='font-family: monospace; font-size: 0.78rem; "
        f"font-weight: 600; color: {color} !important;'>× {format_sig_figs(value, 4)}</span>"
        f"<span style='font-size: 0.7rem; color: {color} !important; "
        f"display: inline-flex; align-items: center; gap: 3px;'>"
        f"{icon} {short}</span>"
        f"</div>"
        f"</div>"
    )


def render_hero_stepper(
    audit_steps: List[dict],
    dim_lookup: Callable[[str], str],
    theme: dict,
    label: str = "Pathway",
) -> str:
    """Return the full HTML for the hero pathway stepper.

    ``audit_steps`` is the engine's per-path audit list. ``dim_lookup`` is a
    callable mapping a unit name to its dimension string (e.g.
    ``lambda u: graph_engine.G.nodes[u].get("Unit Dimension", "")``).
    """
    if not audit_steps:
        return ""

    secondary = theme.get("secondary", "#888")
    surface_bg = theme.get("bg", "#fff")
    border = theme.get("border", "#ddd")

    # nodes = source of first step, then target of every step
    nodes = [audit_steps[0]["source"]] + [s["target"] for s in audit_steps]

    parts: List[str] = []

    # Tiny header above the stepper to match the rest of the UI's section labels.
    parts.append(
        f"<div style='font-size: 0.7rem; color: {secondary} !important; "
        f"text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; "
        f"margin: 14px 0 6px 0;'>{label}</div>"
    )

    # The stepper itself — horizontal flex, scrolls if path is long.
    parts.append(
        f"<div style='display: flex; align-items: stretch; gap: 0; "
        f"padding: 14px 10px; background: {surface_bg}; "
        f"border: 1px solid {border}; border-radius: 10px; "
        f"overflow-x: auto; margin-bottom: 8px;'>"
    )

    # Interleave nodes and edges: N[0], E[0], N[1], E[1], ..., N[last]
    for i, node in enumerate(nodes):
        dim = dim_lookup(node) if dim_lookup else ""
        parts.append(_node_html(node, dim or "", theme))
        if i < len(audit_steps):
            step = audit_steps[i]
            edge = step["edges"][0]
            parts.append(_edge_html(edge["value"], edge.get("set", ""), theme))

    parts.append("</div>")
    return "".join(parts)
