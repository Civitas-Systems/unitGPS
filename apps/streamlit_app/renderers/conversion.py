"""Render the Conversions result panel."""

from __future__ import annotations

import logging

import streamlit as st

from unitgps.engine import determine_conversion, format_sig_figs

from ..export import audit_to_json, audit_to_markdown
from ..formatting import format_audit_date, normalize_param_value
from ..network_viz import render_network_figure, render_network_plotly
from .stepper import render_hero_stepper

logger = logging.getLogger(__name__)

# Audit columns we group as "Source" (provenance/attribution).
SOURCE_KEYS = ("Agency", "Dataset", "Data Year", "Version", "Updated", "Release Date")

# Sets that are static infrastructure — never have parameters or source.
STATIC_SETS = {"Unit Conversion", "Unit Conversions", "Magnitude Adjustment"}


def _chosen_edge(step: dict) -> dict:
    """Return the parallel edge actually used in the calculation.

    Honors the user's edge pick (``chosen_edge_idx``) so on-screen cards match
    both the computed result and the Markdown export. Falls back to the first
    edge (the engine default) when the index is missing or out of range.
    """
    edges = step.get("edges") or []
    if not edges:
        return {}
    idx = step.get("chosen_edge_idx", 0)
    if not isinstance(idx, int) or idx < 0 or idx >= len(edges):
        idx = 0
    return edges[idx]


# --- Step-type styling ------------------------------------------------------ #
# Unit Conversion + Magnitude Adjustment share one visual treatment because
# they're both static infrastructure (the user's words). Chemical Properties
# and Emission Factors each get their own.

def _set_style(set_name: str, theme: dict) -> dict:
    """Return {color, icon, group_label} for a Set name."""
    sn = (set_name or "").strip()
    if sn in STATIC_SETS:
        return {
            "color": theme.get("secondary", "#888"),
            "icon": "🔧",
            "group": "Static conversion",
        }
    if sn == "Chemical Properties":
        return {
            "color": theme.get("success", "#10b981"),
            "icon": "🧪",
            "group": "Chemical property",
        }
    if "emission" in sn.lower():
        return {
            "color": theme.get("danger", "#ef4444"),
            "icon": "🌫",
            "group": "Emission factor",
        }
    return {
        "color": theme.get("primary", "#8B5CF6"),
        "icon": "•",
        "group": sn or "Edge",
    }


def _split_audit_params(
    params: dict, sources: dict
) -> tuple[list[tuple[str, str]], list[tuple[str, str, str | None]]]:
    """Bucket an edge's params into (classification_rows, chemical_rows).

    - classification_rows: list[(label, value)] for non-chemical, non-source params
    - chemical_rows: list[(label, std_value, src_value_or_None)]
      paired by encounter order so ``Chemical1`` lines up with the first ``Source-…``
      key, ``Chemical2`` with the second, etc. ``src_value`` is set to None when
      identical to the standardized value, so the subtitle stays silent.
    """
    classification: list[tuple[str, str]] = []
    chemical_std: list[tuple[str, str]] = []
    chemical_src_values: list[str] = []

    for k, v in params.items():
        if k in SOURCE_KEYS:
            continue  # attribution line owns these
        if v is None or v == "":
            continue
        if k.startswith("Source-") or k.startswith("Source "):
            chemical_src_values.append(normalize_param_value(v))
        elif "Chemical" in k:
            chemical_std.append((k, normalize_param_value(v)))
        else:
            classification.append((k, normalize_param_value(v)))

    chemical_rows: list[tuple[str, str, str | None]] = []
    for i, (label, std_v) in enumerate(chemical_std):
        src_v = chemical_src_values[i] if i < len(chemical_src_values) else None
        if src_v == std_v:
            src_v = None
        chemical_rows.append((label, std_v, src_v))

    return classification, chemical_rows


def _build_attribution(sources: dict, params: dict) -> str:
    """Build the bottom attribution line.

    Falls back to ``params`` when a provenance field isn't in ``sources``,
    matching the legacy behaviour where some edges only carry these in params.
    Dates are normalized to YYYY-MMM-DD.
    """
    def get(key: str):
        val = sources.get(key)
        if val:
            return val
        return params.get(key)

    agency = get("Agency")
    dataset = get("Dataset")
    version = get("Version") or get("Data Year")
    released = get("Release Date")
    updated = get("Updated")

    parts: list[str] = []
    if agency:
        parts.append(f"<b>{agency}</b>")
    if dataset:
        if version:
            parts.append(f"{dataset} v{normalize_param_value(version)}")
        else:
            parts.append(str(dataset))
    elif version:
        parts.append(f"v{normalize_param_value(version)}")
    if released:
        parts.append(f"Released {format_audit_date(released)}")
    if updated:
        parts.append(f"Updated {format_audit_date(updated)}")

    return " · ".join(parts)


def _grouped_section_html(
    label: str,
    rows: list[tuple[str, str]],
    theme: dict,
) -> str:
    """Render a labeled section of simple key/value rows (classification group)."""
    if not rows:
        return ""
    header = (
        f"<div style='font-size:0.7rem; color:{theme['secondary']} !important; "
        f"text-transform:uppercase; letter-spacing:0.5px; font-weight:600; "
        f"margin: 0 0 4px 0;'>{label}</div>"
    )
    body = "<table style='border-collapse:collapse; margin: 0 0 12px 0;'><tbody>"
    for k, v in rows:
        body += (
            f"<tr>"
            f"<td style='padding: 3px 18px 3px 0; color:{theme['secondary']} !important; "
            f"font-size:0.85rem; vertical-align: top; white-space: nowrap;'>{k}</td>"
            f"<td style='padding: 3px 0; color:{theme['text']} !important; "
            f"font-size:0.85rem;'>{v}</td>"
            f"</tr>"
        )
    body += "</tbody></table>"
    return header + body


def _chemical_section_html(
    rows: list[tuple[str, str, str | None]],
    theme: dict,
) -> str:
    """Render the chemical group with standardized name + optional source subtitle."""
    if not rows:
        return ""
    header = (
        f"<div style='font-size:0.7rem; color:{theme['secondary']} !important; "
        f"text-transform:uppercase; letter-spacing:0.5px; font-weight:600; "
        f"margin: 0 0 4px 0;'>Chemical</div>"
    )
    body = "<table style='border-collapse:collapse; margin: 0 0 12px 0;'><tbody>"
    for label, std_v, src_v in rows:
        if src_v:
            val_html = (
                f"{std_v}"
                f"<div style='font-size:0.72rem; color:{theme['secondary']} !important; "
                f"font-style: italic; margin-top: 1px; opacity: 0.85;'>"
                f"source: {src_v}</div>"
            )
        else:
            val_html = std_v
        body += (
            f"<tr>"
            f"<td style='padding: 3px 18px 3px 0; color:{theme['secondary']} !important; "
            f"font-size:0.85rem; vertical-align: top; white-space: nowrap;'>{label}</td>"
            f"<td style='padding: 3px 0; color:{theme['text']} !important; "
            f"font-size:0.85rem;'>{val_html}</td>"
            f"</tr>"
        )
    body += "</tbody></table>"
    return header + body


def _attribution_footer_html(attribution: str, theme: dict) -> str:
    """Render the elegant single-line attribution footer."""
    if not attribution:
        return ""
    return (
        f"<div style='display: flex; align-items: center; gap: 8px; "
        f"padding: 8px 0 4px 0; margin-top: 6px; "
        f"border-top: 1px solid {theme['border']}; "
        f"color:{theme['secondary']} !important; font-size:0.8rem; "
        f"flex-wrap: wrap;'>"
        f"<span style='font-size:0.85rem; opacity: 0.7;'>🏛</span>"
        f"<span>{attribution}</span>"
        f"</div>"
    )


def _render_edge_picker(step: dict, path_idx: int, theme: dict) -> None:
    """Render a sticky picker for an ambiguous step (>1 parallel edges).

    Persists the user's pick in ``st.session_state["_edge_picks"]`` keyed by
    ``(source, target)``. The dict is read by ``app.py`` and forwarded to the
    engine on the next calc, so the chosen edge becomes the primary on rerun.
    """
    edges = step.get("edges") or []
    if len(edges) <= 1:
        return

    u = step["source"]
    v = step["target"]
    current_idx = step.get("chosen_edge_idx", 0)

    # Build short, scannable labels for each alternative.
    options: list[str] = []
    for i, e in enumerate(edges):
        val_str = format_sig_figs(e.get("value", 1.0), 5)
        srcs = e.get("source", {}) or {}
        params = e.get("parameters", {}) or {}
        agency = srcs.get("Agency") or "?"
        year = (
            srcs.get("Data Year")
            or srcs.get("Version")
            or params.get("Data Year")
            or params.get("Version")
        )
        ctx_bits = []
        for k in ("Category", "Asset"):
            v_val = normalize_param_value(params.get(k, ""))
            if v_val:
                ctx_bits.append(v_val)
        chem = (
            normalize_param_value(params.get("Chemical2", ""))
            or normalize_param_value(params.get("Chemical1", ""))
        )
        if chem:
            ctx_bits.append(chem)
        year_suffix = f" ({year})" if year else ""
        ctx_suffix = f" · {' · '.join(ctx_bits)}" if ctx_bits else ""
        options.append(f"× {val_str} · {agency}{year_suffix}{ctx_suffix}")

    # Build a short identifier for the current selection — agency + year + chemical
    # so the user sees what they have *without* opening the picker. Falls back to
    # "#K of N" only when the chosen edge has no useful identifying metadata.
    cur_edge = edges[current_idx]
    cur_srcs = cur_edge.get("source", {}) or {}
    cur_params = cur_edge.get("parameters", {}) or {}
    cur_bits: list[str] = []
    cur_agency = cur_srcs.get("Agency")
    if cur_agency:
        cur_bits.append(str(cur_agency))
    cur_year = (
        cur_srcs.get("Data Year")
        or cur_srcs.get("Version")
        or cur_params.get("Data Year")
        or cur_params.get("Version")
    )
    if cur_year:
        cur_bits.append(str(cur_year))
    cur_chem = (
        normalize_param_value(cur_params.get("Chemical2", ""))
        or normalize_param_value(cur_params.get("Chemical1", ""))
    )
    if cur_chem:
        cur_bits.append(cur_chem)
    cur_summary = " · ".join(cur_bits) if cur_bits else f"#{current_idx + 1} of {len(edges)}"
    label = (
        f"⚡ {len(edges)} alternatives — using: {cur_summary}"
    )
    # Unique key per path so the same (u, v) edge in multiple paths gets its own
    # widget instance. They all read/write the shared _edge_picks dict.
    radio_key = f"_pick_{u}__{v}__p{path_idx}__s{step.get('step_num', 0)}"

    with st.expander(label, expanded=False):
        chosen_idx = st.radio(
            f"Choose edge for {u} → {v}",
            options=list(range(len(edges))),
            format_func=lambda i: options[i],
            index=current_idx,
            key=radio_key,
            label_visibility="collapsed",
        )
        picks = st.session_state.setdefault("_edge_picks", {})
        if picks.get((u, v)) != chosen_idx:
            picks[(u, v)] = chosen_idx
            st.rerun()
        elif chosen_idx != 0 and (u, v) not in picks:
            # First-time selection that's non-default — record it.
            picks[(u, v)] = chosen_idx
            st.rerun()

        if (u, v) in picks:
            col_reset, _spacer = st.columns([1, 4])
            with col_reset:
                if st.button("Reset to default", key=f"_pick_reset_{radio_key}"):
                    picks.pop((u, v), None)
                    # Also clear the widget's own state so radio resets visually
                    st.session_state.pop(radio_key, None)
                    st.rerun()


def _render_step_card(step: dict, theme: dict, step_num: int, total_steps: int, path_idx: int = 0) -> None:
    """Render one audit step: colored step header + grouped body + attribution footer."""
    s, t = step["source"], step["target"]
    edge = _chosen_edge(step)
    val = edge.get("value", 1.0)
    set_name = edge.get("set", "—")
    style = _set_style(set_name, theme)
    is_static = (set_name or "").strip() in STATIC_SETS

    params = edge.get("parameters", {}) or {}
    sources = edge.get("source", {}) or {}

    # Step header bar — colored per-Set
    st.markdown(
        f"""
<div style="margin: 12px 0 0 0; padding: 10px 14px; background: {theme['bg']};
            border: 1px solid {theme['border']};
            border-left: 4px solid {style['color']};
            border-radius: 6px;">
  <div style="display:flex; align-items:baseline; gap:12px; flex-wrap:wrap;">
    <span style="color:{theme['secondary']} !important; font-size:0.75rem;
                 text-transform:uppercase; letter-spacing:0.5px;">
      Step {step_num} / {total_steps}
    </span>
    <span style="color:{theme['text']} !important; font-weight:600; font-size:0.95rem;">
      {s} <span style="color:{theme['secondary']} !important;">➔</span> {t}
    </span>
    <span style="color:{theme['secondary']} !important; font-size:0.8rem;">·</span>
    <span style="color:{style['color']} !important; font-family:monospace; font-size:0.85rem;">
      ×{format_sig_figs(val, 5)}
    </span>
    <span style="color:{theme['secondary']} !important; font-size:0.8rem;">·</span>
    <span style="color:{style['color']} !important; font-size:0.8rem;">
      {style['icon']} {set_name}
    </span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Static conversions never have params/source — header bar carries the
    # whole step (set name + multiplier are already in the header).
    if is_static:
        return

    # Ambiguous edges get an inline picker (sticky in session_state).
    _render_edge_picker(step, path_idx, theme)

    classification_rows, chemical_rows = _split_audit_params(params, sources)
    attribution = _build_attribution(sources, params)

    if not classification_rows and not chemical_rows and not attribution:
        st.markdown(
            f"<div style='color:{theme['secondary']} !important; font-size:0.8rem; "
            f"padding: 6px 14px 12px 14px; font-style:italic;'>"
            f"No additional parameters or source attribution.</div>",
            unsafe_allow_html=True,
        )
        return

    classification_html = _grouped_section_html("Classification", classification_rows, theme)
    chemical_html = _chemical_section_html(chemical_rows, theme)
    footer_html = _attribution_footer_html(attribution, theme)

    # Two-column body when both groups have content; single column otherwise.
    if classification_rows and chemical_rows:
        body_inner = (
            f"<div style='display: grid; grid-template-columns: 1fr 1fr; "
            f"gap: 24px; align-items: start;'>"
            f"<div>{classification_html}</div>"
            f"<div>{chemical_html}</div>"
            f"</div>"
        )
    else:
        body_inner = f"{classification_html}{chemical_html}"

    st.markdown(
        f"<div style='padding: 10px 14px 8px 14px;'>"
        f"{body_inner}"
        f"{footer_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_panel_header(theme: dict, title: str, collapsed_key: str, color_key: str = "primary") -> bool:
    """Render a collapsible panel header. Returns True if collapsed."""
    is_collapsed = st.session_state.get(collapsed_key, False)
    col_title, col_btn = st.columns([20, 1])
    with col_title:
        st.markdown(
            f"<h3 style='color: {theme[color_key]} !important; margin-bottom: 0;'>"
            f"{title}</h3>",
            unsafe_allow_html=True,
        )
    with col_btn:
        label = "▸" if is_collapsed else "▾"
        if st.button(label, key=f"{collapsed_key}_btn",
                     help="Collapse" if not is_collapsed else "Expand"):
            st.session_state[collapsed_key] = not is_collapsed
            st.rerun()
    return is_collapsed


def _render_path_comparison_table(paths: list[dict], target_unit: str, theme: dict) -> None:
    """Compact comparison table when multiple paths are returned.

    Columns: # · Multiplier · Steps · Set kinds · Ambiguous?
    Helps the user pick which tab to open without expanding each.
    """
    if not paths:
        return

    rows = []
    for i, data in enumerate(paths):
        steps = data.get("audit_steps") or []
        # Summarise set kinds
        kind_counts = {"static": 0, "chemical": 0, "emission": 0, "other": 0}
        for s in steps:
            sn = (s["edges"][0].get("set", "") or "").strip()
            if sn in STATIC_SETS:
                kind_counts["static"] += 1
            elif sn == "Chemical Properties":
                kind_counts["chemical"] += 1
            elif "emission" in sn.lower():
                kind_counts["emission"] += 1
            else:
                kind_counts["other"] += 1
        kind_bits = []
        if kind_counts["static"]:
            kind_bits.append(f"{kind_counts['static']} static")
        if kind_counts["chemical"]:
            kind_bits.append(f"{kind_counts['chemical']} chem")
        if kind_counts["emission"]:
            kind_bits.append(f"{kind_counts['emission']} EF")
        if kind_counts["other"]:
            kind_bits.append(f"{kind_counts['other']} other")
        kind_summary = " · ".join(kind_bits) if kind_bits else "—"

        factor = data.get("conversion_factor", 1)
        amb_marker = (
            f"<span style='color:#ffcc00 !important;' title='Has ambiguous edges'>⚡</span>"
            if data.get("is_ambiguous") else ""
        )
        rows.append(
            f"<tr>"
            f"<td style='padding:5px 12px 5px 0; color:{theme['secondary']} !important; "
            f"font-size:0.78rem; white-space:nowrap;'>"
            f"<b style='color:{theme['text']} !important;'>Path {i + 1}</b> {amb_marker}</td>"
            f"<td style='padding:5px 12px; color:{theme['primary']} !important; "
            f"font-family:monospace; font-size:0.8rem; text-align:right;'>"
            f"× {format_sig_figs(factor, 5)}</td>"
            f"<td style='padding:5px 12px; color:{theme['text']} !important; "
            f"font-size:0.78rem; text-align:right;'>{len(steps)}</td>"
            f"<td style='padding:5px 0; color:{theme['secondary']} !important; "
            f"font-size:0.78rem;'>{kind_summary}</td>"
            f"</tr>"
        )

    st.markdown(
        f"<div style='font-size:0.7rem; color:{theme['secondary']} !important; "
        f"text-transform:uppercase; letter-spacing:0.5px; font-weight:600; "
        f"margin: 8px 0 4px 0;'>Path comparison</div>"
        f"<table style='border-collapse:collapse; margin: 0 0 12px 0; "
        f"border: 1px solid {theme['border']}; border-radius: 6px; "
        f"overflow: hidden; min-width: 100%;'>"
        f"<thead><tr style='background:{theme['surface']}; "
        f"color:{theme['secondary']} !important; font-size:0.7rem; "
        f"text-transform:uppercase; letter-spacing:0.4px;'>"
        f"<th style='padding:6px 12px 6px 12px; text-align:left;'>Route</th>"
        f"<th style='padding:6px 12px; text-align:right;'>Multiplier</th>"
        f"<th style='padding:6px 12px; text-align:right;'>Steps</th>"
        f"<th style='padding:6px 12px; text-align:left;'>Kinds</th>"
        f"</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        f"</table>",
        unsafe_allow_html=True,
    )


def _render_single_path(
    data: dict,
    p_idx: int,
    source_unit: str,
    target_unit: str,
    starting_value: float,
    dim_lookup,
    theme: dict,
    graph_engine=None,
) -> None:
    """Render one path's output metric + hero stepper + step cards."""
    ambiguity_warn = ""
    if data.get("is_ambiguous"):
        ambiguity_warn = (
            f"<div style='margin-top: 10px; padding: 10px; "
            f"background-color: {theme['surface']}; "
            f"border-left: 4px solid #ffcc00; color: #ffcc00; "
            f"font-size: 0.9rem; border-radius:4px;'>"
            "⚡ <b>Ambiguous pathway</b>: one or more steps have multiple "
            "parallel edges. Use the per-step picker below to choose alternatives, "
            "or narrow filters (Chemical Type, Agency, Data Year) for a unique result."
            "</div>"
        )

    st.markdown(
        f"""
<div>
  <div class="metric-label">Output</div>
  <div class="metric-value">{format_sig_figs(data.get('ultimate_value', 0), 5)}
    <span style="font-size:1.2rem; color:{theme['text']} !important;">{target_unit}</span>
  </div>
  <div style="color: {theme['secondary']} !important; font-size: 0.9rem; margin-top: 5px;">
    Multiplier: <span style="color:{theme['primary']} !important; font-family:monospace;">
    {format_sig_figs(data.get('conversion_factor', 1), 6)}</span>
  </div>
  {ambiguity_warn}
</div>
""",
        unsafe_allow_html=True,
    )

    hero_html = render_hero_stepper(
        data["audit_steps"], dim_lookup, theme, label="Pathway",
    )
    if hero_html:
        st.markdown(hero_html, unsafe_allow_html=True)

    # Export buttons — JSON audit + Markdown report
    json_blob = audit_to_json(
        data, source_unit, target_unit, starting_value, kind="conversion",
    )
    md_blob = audit_to_markdown(
        data, source_unit, target_unit, starting_value, kind="conversion",
    )
    dl_l, dl_r, _dl_sp = st.columns([1, 1, 4])
    with dl_l:
        st.download_button(
            "⬇ JSON audit",
            data=json_blob,
            file_name=f"unitgps_conversion_{source_unit}_to_{target_unit}_p{p_idx + 1}.json",
            mime="application/json",
            key=f"_dl_json_conv_p{p_idx}",
            use_container_width=True,
        )
    with dl_r:
        st.download_button(
            "⬇ Markdown report",
            data=md_blob,
            file_name=f"unitgps_conversion_{source_unit}_to_{target_unit}_p{p_idx + 1}.md",
            mime="text/markdown",
            key=f"_dl_md_conv_p{p_idx}",
            use_container_width=True,
        )

    total_steps = len(data["audit_steps"])
    for i, step in enumerate(data["audit_steps"], start=1):
        _render_step_card(step, theme, i, total_steps, path_idx=p_idx)

    # Network view — full conversion graph with the active path highlighted.
    # Default closed so the panel stays compact; users can open when they want
    # to see the path in the context of the whole unit graph.
    if graph_engine is not None and data.get("route"):
        with st.expander("🌐 Show network view", expanded=False):
            st.caption(
                "The full conversion graph, with this path highlighted in the "
                "Path 1 color. Each dimension (Energy, Weight, Length, etc.) "
                "is a cluster; the path you ran is overlaid in bold."
            )
            _viz_mode = st.session_state.get("viz_mode", "Interactive")
            try:
                if _viz_mode == "Interactive":
                    fig = render_network_plotly(graph_engine, highlight_paths=[data["route"]])
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    import matplotlib.pyplot as plt
                    fig = render_network_figure(
                        graph_engine, highlight_paths=[data["route"]], figsize=(11, 11),
                    )
                    st.pyplot(fig, use_container_width=True)
                    plt.close(fig)
            except Exception as exc:  # noqa: BLE001
                st.warning(f"Network view unavailable: {exc}")


def render_conversion_panel(
    graph_engine,
    search_params: dict,
    source_unit: str,
    target_unit: str,
    theme: dict,
) -> bool:
    """Render the Conversions block. Returns True if a successful calc updated values."""
    sync_done = False

    # Subtle separator between panels — replaces the heavy border on the old container.
    st.markdown(
        f"<hr style='border: none; border-top: 1px solid {theme['border']}; "
        f"margin: 24px 0 12px 0; opacity: 0.6;'>",
        unsafe_allow_html=True,
    )
    with st.container():
        is_collapsed = _render_panel_header(theme, "🔄 Conversions", "conv_collapsed", "primary")
        if is_collapsed:
            return sync_done

        with st.spinner("Processing..."):
            picks = st.session_state.get("_edge_picks") or {}
            res = determine_conversion(
                graph_engine, search_params, source_unit, target_unit, 1.0,
                edge_picks=picks,
            )
            logger.debug(
                "Conversion call source=%r target=%r status=%s",
                source_unit, target_unit, res.get("status"),
            )

            if res["status"] != "success":
                if res["status"] == "ambiguity_error":
                    st.error("⚠️ Ambiguity Error")
                    st.markdown(
                        "Please narrow down Data Year, Agency, or other parameters."
                    )
                else:
                    st.error(res.get("message", "Unknown error"))
                return sync_done

            all_paths = res["data"]
            if isinstance(all_paths, list) and len(all_paths) > 0:
                target_data = all_paths[0]
            elif isinstance(all_paths, dict):
                target_data = all_paths
            else:
                target_data = {"conversion_factor": 1}

            factor = target_data.get("conversion_factor", 1)

            if st.session_state["calc_direction"] == "forward":
                st.session_state["final_val"] = st.session_state["start_val"] * factor
            else:
                st.session_state["start_val"] = (
                    st.session_state["final_val"] / factor if factor else 0.0
                )
            sync_done = True

            max_p_val = st.session_state.get("max_paths", 5)
            max_p = len(all_paths) if max_p_val == "All" else int(max_p_val)

            if isinstance(all_paths, list):
                paths_iter = all_paths[:max_p]
                count_msg = (
                    f"Found {len(all_paths)} valid path(s)."
                    + (f" Displaying top {max_p}." if len(all_paths) > max_p else "")
                )
            else:
                paths_iter = [all_paths]
                count_msg = "Found 1 valid path(s)."

            st.markdown(
                f"<div style='color: {theme['secondary']} !important; "
                f"font-size:0.85rem; margin: 4px 0 12px 0;'>{count_msg}</div>",
                unsafe_allow_html=True,
            )

            # Stamp every path with starting/ultimate values up-front
            for data in paths_iter:
                data["starting_value"] = st.session_state["start_val"]
                data["ultimate_value"] = (
                    st.session_state["start_val"] * data.get("conversion_factor", 1)
                )

            # Path-comparison table (only when N > 1) — at-a-glance summary so
            # the user knows which tab to open.
            if len(paths_iter) > 1:
                _render_path_comparison_table(paths_iter, target_unit, theme)

            def _dim_lookup(u: str) -> str:
                G = getattr(graph_engine, "G", None)
                if G is None or u not in G.nodes:
                    return ""
                return G.nodes[u].get("Unit Dimension", "") or ""

            # Tabs when multiple paths, otherwise render inline.
            if len(paths_iter) > 1:
                tab_labels = []
                for i, data in enumerate(paths_iter):
                    suffix = " ⚡" if data.get("is_ambiguous") else ""
                    tab_labels.append(f"Path {i + 1}{suffix}")
                tabs = st.tabs(tab_labels)
                for p_idx, (tab, data) in enumerate(zip(tabs, paths_iter)):
                    with tab:
                        _render_single_path(data, p_idx, source_unit, target_unit, st.session_state['start_val'], _dim_lookup, theme, graph_engine=graph_engine)
            else:
                _render_single_path(paths_iter[0], 0, source_unit, target_unit, st.session_state['start_val'], _dim_lookup, theme, graph_engine=graph_engine)

    return sync_done
