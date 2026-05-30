"""Render the GHG Emissions result panel.

Condensed layout:
- Total CO2e headline
- Horizontal stacked bar (replaces the donut — far more readable when one gas
  dominates the result, which is the typical case for combustion sources)
- Optional "Show derivation" expander containing the LaTeX equation
- Three per-gas compact summary cards, each carrying:
    * gas badge + contribution % + ★ marker on the dominant contributor
    * Mass / GWP / CO2e metric row (folds in the old standalone table)
    * Route string with static-step footnote
    * Emission-factor multiplier + context (Stationary Combustion · Anthracite …)
    * Provenance attribution line (Agency · Dataset · Released … · Updated …)
"""

from __future__ import annotations

import logging

import streamlit as st

from unitgps.engine import determine_ghg_emissions, format_sig_figs

from ..export import audit_to_json, audit_to_markdown
from ..network_viz import GHG_PATH_COLORS, render_network_figure, render_network_plotly
from ..formatting import format_html_num, format_latex_num, normalize_param_value, sanitize_latex
from .conversion import (
    STATIC_SETS,
    _build_attribution,
    _chosen_edge,
    _render_panel_header,
)

logger = logging.getLogger(__name__)

GAS_LATEX = {
    "CO2": r"\text{CO}_2",
    "CH4": r"\text{CH}_4",
    "N2O": r"\text{N}_2\text{O}",
}


def _gwp_text(val) -> str:
    """Render a GWP value cleanly for inclusion in LaTeX — integer if it is one."""
    if val is None:
        return r"\text{N/A}"
    if float(val).is_integer():
        return str(int(val))
    return f"{val:g}"


# --------------------------------------------------------------------------- #
# Horizontal stacked bar — replaces the donut                                  #
# --------------------------------------------------------------------------- #


def _render_horizontal_stacked_bar(
    per_gas: dict, total_co2e: float, gas_colors: dict, theme: dict
) -> None:
    """Render a horizontal stacked bar + legend showing per-gas CO2e contribution.

    Each segment's width is proportional to that gas's share of total CO2e, with
    a small min-width so dominant-by-3-orders-of-magnitude data still shows the
    minor segments as readable slivers.
    """
    if not total_co2e:
        return

    segs = []
    legend_parts = []
    for ghg in ("CO2", "CH4", "N2O"):
        co2e = per_gas.get(ghg, {}).get("CO2e") or 0
        pct = (co2e / total_co2e * 100) if total_co2e else 0
        color = gas_colors[ghg]
        # Inline label only when the segment has enough room for it (~ >= 12%).
        label_html = (
            f"<span style='color:#fff; font-weight:500; "
            f"text-shadow:0 1px 2px rgba(0,0,0,0.35);'>{ghg} · {pct:.1f}%</span>"
            if pct >= 12 else ""
        )
        # Use percentage flex but with a small min-width so tiny slivers stay visible.
        segs.append(
            f"<div style='flex: {max(pct, 0.5)} 1 0; min-width: 14px; "
            f"background: {color}; display: flex; align-items: center; "
            f"padding: 0 10px; font-size: 11px; white-space: nowrap; "
            f"overflow: hidden;'>{label_html}</div>"
        )
        legend_parts.append(
            f"<span style='display:inline-flex; align-items:center; gap:6px;'>"
            f"<span style='display:inline-block; width:10px; height:10px; "
            f"border-radius:2px; background:{color};'></span>"
            f"<span style='color:{theme['text']} !important; font-weight:500;'>{ghg}</span>"
            f"<span style='color:{theme['secondary']} !important;'>{pct:.2f}%</span>"
            f"</span>"
        )

    st.markdown(
        f"<div style='display:flex; height:30px; border-radius:6px; "
        f"overflow:hidden; border:1px solid {theme['border']}; "
        f"margin: 8px 0 8px 0;'>"
        f"{''.join(segs)}"
        f"</div>"
        f"<div style='display:flex; gap:18px; flex-wrap:wrap; "
        f"font-size:0.78rem; color:{theme['secondary']} !important; "
        f"margin-bottom:14px;'>"
        f"{''.join(legend_parts)}"
        f"</div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Per-gas compact card with folded-in metrics                                  #
# --------------------------------------------------------------------------- #


def _render_per_gas_compact_card(
    ghg: str,
    details: dict,
    total_co2e: float,
    target_unit: str,
    accent: str,
    theme: dict,
    is_dominant: bool = False,
) -> None:
    """Render one gas as a single compact summary row (Option B).

    Folds the old standalone GHG table's Mass / GWP / CO2e fields into a quiet
    metric row at the top of the right column, so the table no longer needs
    its own block.
    """
    audit = details.get("Audit") or {}
    steps = audit.get("audit_steps") or []
    err = details.get("Error")
    mass = details.get("Mass")
    gwp = details.get("GWP")
    co2e = details.get("CO2e")

    if not steps:
        msg = "No path found" if err is None else f"Error: {err}"
        st.markdown(
            f"<div style='display:flex; align-items:center; gap:10px; "
            f"padding:8px 14px; background:transparent; "
            f"border:1px solid {theme['border']}; "
            f"border-left:3px solid {accent}; border-radius:6px; "
            f"margin-bottom:6px; font-size:0.8rem;'>"
            f"<span style='display:inline-block; padding:3px 10px; "
            f"background:{accent}22; color:{accent} !important; "
            f"border:1px solid {accent}; border-radius:4px; "
            f"font-weight:600;'>{ghg}</span>"
            f"<span style='color:{theme['secondary']} !important;'>{msg}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        return

    pct = (co2e / total_co2e * 100) if (total_co2e and co2e) else 0.0

    # Route + static-step footnote
    units = [steps[0]["source"]] + [s["target"] for s in steps]
    route = " → ".join(units)
    uc_count = 0
    mag_count = 0
    for s in steps:
        sn = (s["edges"][0].get("set", "") or "").strip()
        if sn in ("Unit Conversion", "Unit Conversions"):
            uc_count += 1
        elif sn == "Magnitude Adjustment":
            mag_count += 1
    foot_parts = []
    if uc_count:
        foot_parts.append(f"{uc_count} unit conv")
    if mag_count:
        foot_parts.append(f"{mag_count} magnitude")
    static_foot = (
        f" <span style='color:{theme['secondary']} !important; opacity:0.7; "
        f"font-size:0.7rem;'>(+ {', '.join(foot_parts)})</span>"
        if foot_parts else ""
    )

    # Find EF step (last non-static)
    ef_step = None
    for s in reversed(steps):
        sn = (s["edges"][0].get("set", "") or "").strip()
        if sn not in STATIC_SETS:
            ef_step = s
            break

    ef_html = ""
    prov_html = ""
    if ef_step:
        edge = _chosen_edge(ef_step)
        ef_val = format_sig_figs(edge["value"], 4)
        params = edge.get("parameters", {}) or {}
        sources = edge.get("source", {}) or {}

        ctx_parts = []
        for key in ("Category", "Asset"):
            v = normalize_param_value(params.get(key, ""))
            if v:
                ctx_parts.append(v)
        chem = (
            normalize_param_value(params.get("Chemical2", ""))
            or normalize_param_value(params.get("Chemical1", ""))
        )
        if chem:
            ctx_parts.append(chem)
        ef_context = " · ".join(ctx_parts)

        ef_html = (
            f"<div style='font-size:0.78rem; color:{theme['text']} !important; "
            f"margin-top:4px;'>"
            f"<span style='color:{theme['secondary']} !important; "
            f"font-size:0.7rem; text-transform:uppercase; letter-spacing:0.4px; "
            f"margin-right:6px;'>EF</span>"
            f"<span style='font-family:monospace; color:{accent} !important; "
            f"font-weight:500;'>×{ef_val}</span>"
            f"<span style='color:{theme['secondary']} !important;'>"
            f" · {ef_step['source']} → {ef_step['target']}"
            f"{(' · ' + ef_context) if ef_context else ''}"
            f"</span>"
            f"</div>"
        )

        attribution = _build_attribution(sources, params)
        if attribution:
            prov_html = (
                f"<div style='font-size:0.72rem; "
                f"color:{theme['secondary']} !important; margin-top:3px;'>"
                f"🏛 {attribution}"
                f"</div>"
            )

    # Folded-in metrics row: Mass / GWP / CO2e
    mass_str = format_html_num(mass) if mass is not None else "—"
    gwp_str = (
        str(int(gwp)) if (gwp is not None and float(gwp).is_integer())
        else (f"{gwp:g}" if gwp is not None else "—")
    )
    co2e_str = format_html_num(co2e) if co2e is not None else "—"

    metric_pill = (
        "background: transparent; color: {tx} !important; "
        "font-family: monospace; font-weight: 500;"
    ).format(tx=theme['text'])
    metric_key = (
        "color: {sc} !important; text-transform: uppercase; letter-spacing: 0.4px; "
        "font-size: 0.65rem; margin-right: 4px;"
    ).format(sc=theme['secondary'])
    metrics_html = (
        f"<div style='display:flex; gap:14px; flex-wrap:wrap; "
        f"font-size:0.75rem; margin-bottom:5px;'>"
        f"<span><span style=\"{metric_key}\">Mass</span>"
        f"<span style=\"{metric_pill}\">{mass_str} {target_unit}</span></span>"
        f"<span><span style=\"{metric_key}\">GWP</span>"
        f"<span style=\"{metric_pill}\">{gwp_str}</span></span>"
        f"<span><span style=\"{metric_key}\">CO₂e</span>"
        f"<span style=\"{metric_pill}\">{co2e_str} {target_unit}</span></span>"
        f"</div>"
    )

    # Left column: gas badge, contribution %, ★ if dominant
    star_html = (
        f"<span style='color: gold; font-size: 0.85rem; margin-right: 4px;' "
        f"title='Dominant contributor'>★</span>"
        if is_dominant else ""
    )
    left_col = (
        f"<div>"
        f"<div style='display:flex; align-items:center;'>"
        f"{star_html}"
        f"<span style='display:inline-block; padding:3px 10px; "
        f"background:{accent}22; color:{accent} !important; "
        f"border:1px solid {accent}; border-radius:4px; "
        f"font-weight:600; font-size:0.85rem;'>{ghg}</span>"
        f"</div>"
        f"<div style='font-size:0.72rem; color:{theme['secondary']} !important; "
        f"margin-top:5px; line-height:1.4;'>"
        f"<b style='color:{accent} !important;'>{pct:.1f}%</b>"
        f"<br><span style='font-size:0.68rem;'>of total CO₂e</span>"
        f"</div>"
        f"</div>"
    )

    st.markdown(
        f"<div style='display:grid; grid-template-columns:130px 1fr; gap:16px; "
        f"padding:10px 14px; background:transparent; "
        f"border:1px solid {theme['border']}; "
        f"border-left:3px solid {accent}; border-radius:6px; "
        f"margin-bottom:8px; align-items:center;'>"
        f"{left_col}"
        f"<div>"
        f"{metrics_html}"
        f"<div style='font-family:monospace; font-size:0.85rem; "
        f"color:{theme['text']} !important;'>{route}{static_foot}</div>"
        f"{ef_html}"
        f"{prov_html}"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Panel orchestrator                                                            #
# --------------------------------------------------------------------------- #


def render_emissions_panel(
    graph_engine,
    search_params: dict,
    source_unit: str,
    target_unit: str,
    gwps_data,
    theme: dict,
    sync_done: bool,
    gwp_report: str = "AR5",
    gwp_horizon: str = "100",
) -> None:
    """Render the GHG Emissions block."""
    # Subtle separator between panels.
    st.markdown(
        f"<hr style='border: none; border-top: 1px solid {theme['border']}; "
        f"margin: 24px 0 12px 0; opacity: 0.6;'>",
        unsafe_allow_html=True,
    )
    with st.container():
        title_html = (
            f"🌍 GHG Emissions "
            f"<span style='font-size:0.6em; color:{theme['secondary']} !important; "
            f"font-weight:normal; vertical-align:middle;'>"
            f"IPCC {gwp_report} · {gwp_horizon}-year</span>"
        )
        is_collapsed = _render_panel_header(theme, title_html, "ghg_collapsed", "danger")
        if is_collapsed:
            return

        with st.spinner("Processing..."):
            if not sync_done:
                picks = st.session_state.get("_edge_picks") or {}
                res_base = determine_ghg_emissions(
                    graph_engine, search_params, source_unit, target_unit, 1.0,
                    gwps_data, gwp_report=gwp_report, gwp_horizon=gwp_horizon,
                    edge_picks=picks,
                )
                if res_base["valid_calc"]:
                    base_co2e = res_base["total_co2e"]
                    if st.session_state["calc_direction"] == "forward":
                        st.session_state["final_val"] = (
                            st.session_state["start_val"] * base_co2e
                        )
                    else:
                        st.session_state["start_val"] = (
                            st.session_state["final_val"] / base_co2e
                            if base_co2e else 0.0
                        )

            picks = st.session_state.get("_edge_picks") or {}
            res = determine_ghg_emissions(
                graph_engine,
                search_params,
                source_unit,
                target_unit,
                st.session_state.start_val,
                gwps_data,
                gwp_report=gwp_report,
                gwp_horizon=gwp_horizon,
                edge_picks=picks,
            )
            logger.debug(
                "GHG call source=%r target=%r start=%r valid=%s",
                source_unit, target_unit, st.session_state.start_val,
                res.get("valid_calc"),
            )

            gas_colors = {
                "CO2": theme["primary"],
                "CH4": theme["success"],
                "N2O": theme["danger"],
            }

            if not res["valid_calc"]:
                st.warning("⚠️ Global calculation incomplete.")
                return

            # ── Total CO2e headline ──
            total_co2e = res["total_co2e"]
            st.markdown(
                f"""
<div>
  <div class="metric-label">Total Carbon Footprint</div>
  <div class="metric-value-danger">{format_sig_figs(total_co2e, 6)}
    <span style="font-size:1.2rem; color:{theme['text']} !important;">{target_unit} CO₂e</span>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

            # ── Horizontal stacked bar + legend (replaces donut) ──
            _render_horizontal_stacked_bar(
                res["results"], total_co2e, gas_colors, theme
            )

            # ── Export buttons — JSON audit + Markdown report ──
            json_blob = audit_to_json(
                res, source_unit, target_unit, st.session_state.start_val,
                kind="ghg",
                extras={"gwp_report": gwp_report, "gwp_horizon": gwp_horizon},
            )
            md_blob = audit_to_markdown(
                res, source_unit, target_unit, st.session_state.start_val,
                kind="ghg",
                extras={"GWP report": gwp_report, "Time horizon (yr)": gwp_horizon},
            )
            dl_l, dl_r, _dl_sp = st.columns([1, 1, 4])
            with dl_l:
                st.download_button(
                    "⬇ JSON audit",
                    data=json_blob,
                    file_name=f"unitgps_ghg_{source_unit}_to_{target_unit}_{gwp_report}_{gwp_horizon}yr.json",
                    mime="application/json",
                    key="_dl_json_ghg",
                    use_container_width=True,
                )
            with dl_r:
                st.download_button(
                    "⬇ Markdown report",
                    data=md_blob,
                    file_name=f"unitgps_ghg_{source_unit}_to_{target_unit}_{gwp_report}_{gwp_horizon}yr.md",
                    mime="text/markdown",
                    key="_dl_md_ghg",
                    use_container_width=True,
                )

            # ── LaTeX derivation (hidden behind expander) ──
            def tex_val(v):
                if v is None:
                    return r"\text{N/A}"
                return format_latex_num(v)

            co2_m = tex_val(res["results"]["CO2"]["Mass"])
            ch4_m = tex_val(res["results"]["CH4"]["Mass"])
            n2o_m = tex_val(res["results"]["N2O"]["Mass"])
            co2_c = tex_val(res["results"]["CO2"]["CO2e"])
            ch4_c = tex_val(res["results"]["CH4"]["CO2e"])
            n2o_c = tex_val(res["results"]["N2O"]["CO2e"])
            tot_c = tex_val(total_co2e)
            ch4_g = _gwp_text(res["results"]["CH4"]["GWP"])
            n2o_g = _gwp_text(res["results"]["N2O"]["GWP"])
            u_tex = sanitize_latex(target_unit)
            co2_t = GAS_LATEX["CO2"]
            ch4_t = GAS_LATEX["CH4"]
            n2o_t = GAS_LATEX["N2O"]

            latex_eq = (
                r"\small"
                r"\begin{aligned}"
                rf"\text{{Total }}{co2_t}\text{{e}} &= "
                rf"{co2_t} + {ch4_t} \cdot \text{{GWP}}_{{{ch4_t}}}"
                rf" + {n2o_t} \cdot \text{{GWP}}_{{{n2o_t}}} \\"
                rf"&= {co2_m} + {ch4_m} \cdot {ch4_g} + {n2o_m} \cdot {n2o_g}"
                rf" \quad \left[ {u_tex} \right] \\"
                rf"&= {co2_c} + {ch4_c} + {n2o_c}"
                rf" \quad \left[ {u_tex}\,{co2_t}\text{{e}} \right] \\"
                rf"&= {tot_c} \quad \left[ {u_tex}\,{co2_t}\text{{e}} \right]"
                r"\end{aligned}"
            )

            with st.expander("Show derivation", expanded=False):
                st.latex(latex_eq)

            # ── Per-gas compact cards (with folded-in Mass/GWP/CO2e) ──
            # Find dominant contributor (max CO2e) for ★ marker.
            dominant_ghg = max(
                ("CO2", "CH4", "N2O"),
                key=lambda g: (res["results"].get(g, {}).get("CO2e") or 0),
            )
            st.markdown(
                f"<div style='font-size:0.7rem; color:{theme['secondary']} !important; "
                f"text-transform:uppercase; letter-spacing:0.5px; font-weight:600; "
                f"margin: 14px 0 8px 0;'>Per-gas pathway & provenance</div>",
                unsafe_allow_html=True,
            )
            for ghg in ("CO2", "CH4", "N2O"):
                _render_per_gas_compact_card(
                    ghg=ghg,
                    details=res["results"][ghg],
                    total_co2e=total_co2e,
                    target_unit=target_unit,
                    accent=gas_colors[ghg],
                    theme=theme,
                    is_dominant=(ghg == dominant_ghg),
                )

            # Network view — full graph with all three gas pathways overlaid
            # in their accent colors. Lets the user see CO2/CH4/N2O routing
            # in the context of the whole conversion universe.
            ghg_paths: list[list[str]] = []
            ghg_path_colors: list[str] = []
            for ghg in ("CO2", "CH4", "N2O"):
                details = res["results"].get(ghg, {})
                path_raw = details.get("Path")
                # path_raw may be: None, a flat list of nodes, or a list of paths
                if not path_raw:
                    continue
                if isinstance(path_raw, list) and path_raw and isinstance(path_raw[0], list):
                    chosen = path_raw[0]
                else:
                    chosen = path_raw
                if chosen and isinstance(chosen, list) and isinstance(chosen[0], str):
                    ghg_paths.append(chosen)
                    ghg_path_colors.append(GHG_PATH_COLORS.get(ghg, theme.get("primary", "#888")))
            if ghg_paths:
                with st.expander("🌐 Show GHG network view", expanded=False):
                    st.caption(
                        "All three gas pathways overlaid on the full conversion "
                        "graph. CO₂ in violet, CH₄ in green, N₂O in red — the "
                        "same accents used in the bar and per-gas cards above."
                    )
                    _viz_mode = st.session_state.get("viz_mode", "Interactive")
                    try:
                        if _viz_mode == "Interactive":
                            fig = render_network_plotly(
                                graph_engine, highlight_paths=ghg_paths, path_colors=ghg_path_colors,
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            import matplotlib.pyplot as plt
                            fig = render_network_figure(
                                graph_engine, highlight_paths=ghg_paths,
                                path_colors=ghg_path_colors, figsize=(11, 11),
                            )
                            st.pyplot(fig, use_container_width=True)
                            plt.close(fig)
                    except Exception as exc:  # noqa: BLE001
                        st.warning(f"Network view unavailable: {exc}")
