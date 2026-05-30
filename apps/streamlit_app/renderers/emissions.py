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
import pandas as pd

from unitgps.engine import determine_ghg_emissions, format_sig_figs

from ..export import audit_to_json, audit_to_markdown
from ..network_viz import ghg_palette, render_network_figure, render_network_plotly
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


def _render_ghg_bar_plotly(
    per_gas: dict, total_co2e: float, gas_colors: dict, theme: dict, target_unit: str
) -> None:
    """Interactive Plotly version of the stacked bar: hover a segment for the
    exact CO2e and share. Falls back to the static bar if plotly is missing."""
    if not total_co2e:
        return
    try:
        import plotly.graph_objects as go
    except ImportError:  # pragma: no cover
        _render_horizontal_stacked_bar(per_gas, total_co2e, gas_colors, theme)
        return

    fig = go.Figure()
    legend_parts = []
    total_w = 0.0
    for ghg in ("CO2", "CH4", "N2O"):
        co2e = per_gas.get(ghg, {}).get("CO2e") or 0
        pct = (co2e / total_co2e * 100) if total_co2e else 0
        w = max(pct, 0.6)  # floor so tiny gases stay a visible sliver
        total_w += w
        fig.add_trace(go.Bar(
            x=[w], y=["CO2e"], orientation="h", name=ghg,
            marker=dict(color=gas_colors[ghg]),
            customdata=[[co2e, pct]],
            hovertemplate=(
                "<b>" + ghg + "</b><br>%{customdata[0]:.4g} " + target_unit
                + " CO2e<br>%{customdata[1]:.2f}% of total<extra></extra>"),
        ))
        legend_parts.append(
            f"<span style='display:inline-flex;align-items:center;gap:6px;'>"
            f"<span style='display:inline-block;width:10px;height:10px;border-radius:2px;"
            f"background:{gas_colors[ghg]};'></span>"
            f"<span style='color:{theme['text']} !important;font-weight:500;'>{ghg}</span>"
            f"<span style='color:{theme['secondary']} !important;'>{pct:.2f}%</span></span>")
    fig.update_layout(
        barmode="stack", height=64, margin=dict(l=2, r=2, t=2, b=2),
        xaxis=dict(visible=False, range=[0, total_w]),
        yaxis=dict(visible=False), showlegend=False, bargap=0.1,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        f"<div style='display:flex;gap:18px;flex-wrap:wrap;font-size:0.78rem;"
        f"color:{theme['secondary']} !important;margin:-6px 0 14px 0;'>"
        f"{''.join(legend_parts)}</div>",
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


def _render_ghg_calc_table(
    per_gas: dict, total_co2e: float, gas_colors: dict, target_unit: str, theme: dict
) -> None:
    """One aligned table that makes the math explicit and the gases comparable.

    Each row reads as the equation it is -- ``Mass x GWP = CO2e`` -- with a share
    bar, so the user can *see* the calculation and the differences between gases
    instead of having to trust three separate numbers.
    """
    sub, tx, bd = theme["secondary"], theme["text"], theme["border"]
    u = target_unit
    label_of = {"CO2": "CO\u2082", "CH4": "CH\u2084", "N2O": "N\u2082O"}

    def num(content, *, strong=False, color=None):
        sty = (f"padding:7px 8px; text-align:right; white-space:nowrap; "
               f"font-family:monospace; color:{color or tx} !important;"
               + ("font-weight:700;" if strong else ""))
        return f"<td style='{sty}'>{content}</td>"

    def op(sym):
        return (f"<td style='padding:7px 3px; text-align:center; "
                f"color:{sub} !important;'>{sym}</td>")

    head = (
        f"<tr style='font-size:0.64rem; text-transform:uppercase; letter-spacing:0.5px; "
        f"color:{sub} !important;'>"
        f"<th style='text-align:left; padding:4px 8px;'>Gas</th>"
        f"<th style='text-align:right; padding:4px 8px;'>Mass</th><th></th>"
        f"<th style='text-align:right; padding:4px 8px;'>GWP</th><th></th>"
        f"<th style='text-align:right; padding:4px 8px;'>CO\u2082e</th>"
        f"<th style='text-align:left; padding:4px 14px;'>Share</th></tr>"
    )

    body = ""
    for ghg in ("CO2", "CH4", "N2O"):
        d = per_gas.get(ghg, {}) or {}
        mass, gwp, co2e = d.get("Mass"), d.get("GWP"), d.get("CO2e")
        color = gas_colors.get(ghg, sub)
        badge = (
            f"<span style='display:inline-flex; align-items:center; gap:7px;'>"
            f"<span style='width:10px; height:10px; border-radius:2px; "
            f"background:{color}; display:inline-block;'></span>"
            f"<span style='color:{tx} !important; font-weight:600;'>{label_of[ghg]}</span></span>"
        )
        if mass is None or co2e is None:
            body += (
                f"<tr style='border-top:1px solid {bd};'>"
                f"<td style='padding:7px 8px;'>{badge}</td>"
                f"<td colspan='6' style='padding:7px 8px; color:{sub} !important; "
                f"font-size:0.78rem;'>no path found</td></tr>"
            )
            continue
        pct = (co2e / total_co2e * 100) if total_co2e else 0.0
        gwp_s = (str(int(gwp)) if (gwp is not None and float(gwp).is_integer())
                 else (f"{gwp:g}" if gwp is not None else "\u2014"))
        barw = max(pct, 0.8)
        share = (
            f"<div style='display:flex; align-items:center; gap:8px;'>"
            f"<div style='height:7px; width:96px; background:{bd}; border-radius:4px; "
            f"overflow:hidden;'><div style='height:100%; width:{barw:.1f}%; "
            f"background:{color};'></div></div>"
            f"<span style='font-size:0.74rem; color:{tx} !important; "
            f"min-width:40px;'>{pct:.1f}%</span></div>"
        )
        body += (
            f"<tr style='border-top:1px solid {bd}; font-size:0.82rem;'>"
            f"<td style='padding:7px 8px;'>{badge}</td>"
            f"{num(f'{format_sig_figs(mass, 4)} {u}')}{op('×')}{num(gwp_s)}"
            f"{op('=')}{num(f'{format_sig_figs(co2e, 4)} {u}', strong=True, color=color)}"
            f"<td style='padding:7px 14px;'>{share}</td></tr>"
        )

    total_row = (
        f"<tr style='border-top:2px solid {bd};'>"
        f"<td style='padding:8px 8px; color:{sub} !important; font-size:0.7rem; "
        f"text-transform:uppercase; letter-spacing:0.5px; font-weight:600;'>Total</td>"
        f"<td colspan='4'></td>"
        f"<td style='padding:8px 8px; text-align:right; font-family:monospace; "
        f"font-weight:700; color:{tx} !important; white-space:nowrap;'>"
        f"{format_sig_figs(total_co2e, 4)} {u}</td>"
        f"<td style='padding:8px 14px; color:{sub} !important; font-size:0.72rem;'>"
        f"CO\u2082e</td></tr>"
    )

    st.markdown(
        f"<table style='width:100%; border-collapse:collapse; margin:4px 0 8px 0;'>"
        f"{head}{body}{total_row}</table>",
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

            # CO2/CH4/N2O accents — one palette drives the bar, cards and network.
            # Honors the Output-options "Colour-blind-safe" toggle.
            gas_colors = ghg_palette(st.session_state.get("cb_safe", False))

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

            # ── Stacked bar — interactive (Plotly) or static (HTML) per toggle ──
            if st.session_state.get("viz_mode", "Interactive") == "Interactive":
                _render_ghg_bar_plotly(res["results"], total_co2e, gas_colors, theme, target_unit)
            else:
                _render_horizontal_stacked_bar(res["results"], total_co2e, gas_colors, theme)

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

            # ── Transparent calculation: Mass × GWP = CO₂e, gases side by side ──
            st.markdown(
                f"<div style='font-size:0.7rem; color:{theme['secondary']} !important; "
                f"text-transform:uppercase; letter-spacing:0.5px; font-weight:600; "
                f"margin: 14px 0 4px 0;'>How the total is built — Mass × GWP = CO₂e</div>",
                unsafe_allow_html=True,
            )
            _render_ghg_calc_table(res["results"], total_co2e, gas_colors, target_unit, theme)

            # Accessible twin of the table above: st.dataframe is keyboard-
            # navigable, screen-reader friendly, and has a built-in CSV download.
            _label = {"CO2": "CO\u2082", "CH4": "CH\u2084", "N2O": "N\u2082O"}
            _rows = []
            for _g in ("CO2", "CH4", "N2O"):
                _d = res["results"].get(_g, {}) or {}
                _co2e = _d.get("CO2e")
                _rows.append({
                    "Gas": _label[_g],
                    f"Mass ({target_unit})": _d.get("Mass"),
                    "GWP": _d.get("GWP"),
                    f"CO\u2082e ({target_unit})": _co2e,
                    "Share %": round(_co2e / total_co2e * 100, 2) if (total_co2e and _co2e) else 0.0,
                })
            with st.expander("Data table (screen-reader friendly \u00b7 downloadable)", expanded=False):
                st.dataframe(pd.DataFrame(_rows), use_container_width=True, hide_index=True)

            # ── Per-gas pathway & provenance (where each Mass comes from) ──
            dominant_ghg = max(
                ("CO2", "CH4", "N2O"),
                key=lambda g: (res["results"].get(g, {}).get("CO2e") or 0),
            )
            with st.expander("Per-gas pathway & provenance", expanded=False):
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
                    ghg_path_colors.append(gas_colors.get(ghg, theme.get("primary", "#888")))
            if ghg_paths:
                _viz_mode = st.session_state.get("viz_mode", "Interactive")
                with st.expander("🌐 Show GHG network view", expanded=False):
                    st.caption(
                        "The full conversion graph with each greenhouse gas's "
                        "pathway highlighted in its colour (CO\u2082, CH\u2084, N\u2082O)."
                    )
                    try:
                        if _viz_mode == "Interactive":
                            st.plotly_chart(
                                render_network_plotly(graph_engine, highlight_paths=ghg_paths,
                                                      path_colors=ghg_path_colors, label_color=theme["text"]),
                                use_container_width=True)
                        else:
                            import matplotlib.pyplot as plt
                            fig = render_network_figure(
                                graph_engine, highlight_paths=ghg_paths,
                                path_colors=ghg_path_colors, figsize=(11, 11), label_color=theme["text"],
                            )
                            st.pyplot(fig, use_container_width=True)
                            plt.close(fig)
                    except Exception as exc:  # noqa: BLE001
                        st.warning(f"Diagram unavailable: {exc}")
