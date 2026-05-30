"""Database-filter UI + the temporal/db filtering helper."""

from __future__ import annotations

from typing import Iterable, List

import networkx as nx
import pandas as pd
import streamlit as st

from unitgps.engine import shortest_path_edges

# --------------------------------------------------------------------------- #
# Constants                                                                    #
# --------------------------------------------------------------------------- #

COLS_TO_EXTRACT: List[str] = [
    "Source-Chemical Category",
    "Source-Chemical Type",
    "Property",
    "Formula",
    "Process1",
    "Process2",
    "Scope",
    "Category",
    "Country",
    "eGRID",
    "Agency",
    "Dataset",
]

FILTER_GROUPS: dict[str, list[str]] = {
    "Resources": ["Source-Chemical Category", "Formula", "Source-Chemical Type", "Property"],
    "Process": ["Process1", "Process2", "Scope", "Category"],
    "Location": ["Country", "eGRID"],
    "Data Source": ["Agency", "Dataset"],
}


# --------------------------------------------------------------------------- #
# Pandas-side filtering                                                        #
# --------------------------------------------------------------------------- #


def apply_db_and_temporal_filters(
    df: pd.DataFrame,
    search_params: dict,
    mode: str,
    start_yr: int | None = None,
    end_yr: int | None = None,
    dy_vals: Iterable | None = None,
    exempt_static_conversions: bool = True,
) -> pd.DataFrame:
    """Apply database column filters + temporal (Data Year) filters to a DataFrame."""
    is_unit_conv = df["Set"].isin(["Unit Conversion", "Magnitude Adjustment", "Unit Conversions"])
    is_chem_prop = df["Set"] == "Chemical Properties"

    mask = pd.Series(True, index=df.index)

    for col, search_val in search_params.items():
        if not search_val:
            continue

        if exempt_static_conversions:
            cond_unit_conv = is_unit_conv
        else:
            cond_unit_conv = is_unit_conv & df[col].isin(search_val)

        if col not in [
            "Source-Chemical Category",
            "Source-Chemical Type",
            "Chemical1",
            "Chemical2",
            "Property",
        ]:
            cond_chem_prop = is_chem_prop
        else:
            cond_chem_prop = is_chem_prop & df[col].isin(search_val)

        cond_others = (~is_unit_conv) & (~is_chem_prop) & df[col].isin(search_val)
        mask = mask & (cond_unit_conv | cond_chem_prop | cond_others)

    has_no_year = df["Data Year"].isna()

    cond_temp_exempt = is_unit_conv if exempt_static_conversions else pd.Series(False, index=df.index)

    if mode == "Specific Years" and dy_vals:
        float_years = [float(v) for v in dy_vals]
        mask = mask & (cond_temp_exempt | has_no_year | df["Data Year"].isin(float_years))
    elif mode == "Range" and start_yr is not None and end_yr is not None:
        mask = mask & (
            cond_temp_exempt
            | has_no_year
            | ((df["Data Year"] >= start_yr) & (df["Data Year"] <= end_yr))
        )

    return df[mask]


def _reduced_pathway_graph(df: pd.DataFrame) -> "nx.DiGraph":
    """Simple DiGraph of Denominator->Numerator unit pairs (parallel edges
    merged) — small enough that shortest-path reachability is two cheap BFS."""
    g = nx.DiGraph()
    pairs = df[["Denominator", "Numerator"]].dropna()
    g.add_edges_from(set(map(tuple, pairs.itertuples(index=False, name=None))))
    return g


def apply_pathway_scope(
    df_to_scope: pd.DataFrame,
    graph_df: pd.DataFrame,
    source_unit: str | None,
    target_unit: str | None,
) -> pd.DataFrame:
    """Narrow ``df_to_scope`` to rows that are edges on a SHORTEST source->target
    conversion path, so the filter panel only offers pathway-relevant values
    (an electricity MWh->kg pathway hides coal/fuel chemical types).

    The reachability graph is built from ``graph_df`` (module-filtered data,
    independent of the user's db-filter picks) so selecting a filter can't break
    reachability. Falls back to ``df_to_scope`` unchanged when source/target are
    unset, identical, missing, or unreachable, so the panel never blanks by
    surprise.
    """
    if not source_unit or not target_unit or source_unit == target_unit:
        return df_to_scope
    edges = shortest_path_edges(_reduced_pathway_graph(graph_df), source_unit, target_unit)
    if not edges:
        return df_to_scope
    keep = [
        (d, n) in edges
        for d, n in zip(df_to_scope["Denominator"], df_to_scope["Numerator"])
    ]
    return df_to_scope[keep]


# --------------------------------------------------------------------------- #
# UI helpers                                                                   #
# --------------------------------------------------------------------------- #


def get_filtered_df(df_for_units: pd.DataFrame, exclude_col: str | None = None) -> pd.DataFrame:
    temp = df_for_units.copy()
    for col in COLS_TO_EXTRACT:
        if col == exclude_col:
            continue
        val = st.session_state.get(col, [])
        if val:
            temp = temp[temp[col].isin(val)]
    return temp


def get_options(df_for_units: pd.DataFrame, col: str) -> list[str]:
    filtered = get_filtered_df(df_for_units, exclude_col=col)
    if col not in filtered.columns:
        return []
    vals = filtered[col].dropna().unique()
    if col in ["Scope", "Data Year"]:
        # Keep only integer-valued entries, formatted without a trailing .0
        # (e.g. 2020.0 -> "2020"). Coerce numerically rather than string-munging
        # so a value like "1.05" is skipped, not silently corrupted into "15"
        # (and never fed to int() as a non-integer string, which would crash).
        str_vals = set()
        for v in vals:
            try:
                f = float(v)
            except (TypeError, ValueError):
                continue
            if f.is_integer():
                str_vals.add(str(int(f)))
    else:
        str_vals = {str(v).strip() for v in vals}
    return sorted([v for v in str_vals if v])


def dynamic_multiselect(label: str, col_name: str, df_for_units: pd.DataFrame, **kwargs):
    options = get_options(df_for_units, col_name)
    # Auto-hide filters with no options (e.g. Formula(0) when no rows have a formula).
    if not options:
        # Clear any stale session_state for this filter so a previous selection
        # doesn't ghost-filter after the column drops to zero options.
        st.session_state.pop(col_name, None)
        return None
    placeholder = f"e.g. {options[0]}" if options else "No options"
    display_label = f"{label} ({len(options)})"
    return st.multiselect(
        display_label, options=options, key=col_name, placeholder=placeholder, **kwargs
    )


def get_units_for_dim(
    dim: str | None,
    available_units: list[str],
    available_dims: list[str],
    node_attrs: dict,
) -> list[str]:
    if dim:
        valid = [u for u, attr in node_attrs.items() if attr.get("Unit Dimension") == dim]
        return sorted(valid) if valid else available_units

    valid_set = set(available_units)
    for u, attr in node_attrs.items():
        if attr.get("Unit Dimension") in available_dims:
            valid_set.add(u)
    return sorted(valid_set)


# --------------------------------------------------------------------------- #
# Active-filter chip strip (display-only summary of current selections)        #
# --------------------------------------------------------------------------- #

# Display labels for the chip strip — friendlier than raw column names.
_FILTER_LABELS: dict[str, str] = {
    "Source-Chemical Category": "Chemical Category",
    "Source-Chemical Type": "Chemical Type",
    "Formula": "Formula",
    "Property": "Property",
    "Process1": "Process 1",
    "Process2": "Process 2",
    "Scope": "Scope",
    "Category": "Category",
    "Region": "Region",
    "Country": "Country",
    "State": "State",
    "Agency": "Agency",
    "Dataset": "Dataset",
    "Data Year": "Data Year",
}


def _chip_html(label: str, value: str, theme: dict) -> str:
    return (
        f"<span style='display: inline-flex; align-items: center; gap: 6px; "
        f"padding: 3px 10px; background: {theme['surface']}; "
        f"border: 1px solid {theme['border']}; border-radius: 999px; "
        f"font-size: 0.78rem; color: {theme['text']} !important; "
        f"line-height: 1.4;'>"
        f"<span style='color: {theme['secondary']} !important; "
        f"font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.4px;'>"
        f"{label}</span>"
        f"<span style='font-weight: 500;'>{value}</span>"
        f"</span>"
    )


def render_active_filter_chips(theme: dict) -> None:
    """Show a chip strip summarising every active filter selection.

    Display-only — to add/remove filters the user opens the sidebar. The strip
    is always visible in the main column so the current filter state is never
    a mystery, even when the sidebar is collapsed.
    """
    chips: list[str] = []
    for key, label in _FILTER_LABELS.items():
        val = st.session_state.get(key)
        if not val:
            continue
        if isinstance(val, list):
            for v in val:
                chips.append(_chip_html(label, str(v), theme))
        else:
            chips.append(_chip_html(label, str(val), theme))

    if not chips:
        return

    st.markdown(
        f"<div style='display: flex; flex-wrap: wrap; align-items: center; "
        f"gap: 6px; margin: 8px 0 12px 0;'>"
        f"<span style='font-size: 0.7rem; color: {theme['secondary']} !important; "
        f"text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; "
        f"margin-right: 4px;'>Active filters</span>"
        f"{''.join(chips)}"
        f"</div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Tab rendering                                                                #
# --------------------------------------------------------------------------- #


def render_filter_tabs(df_for_units: pd.DataFrame, theme: dict, do_ghg: bool = False) -> None:
    """Render the active Resources/Process/Location/Data Source tabs.

    When ``do_ghg`` is True, the IPCC AR + Time Horizon selectors are rendered
    inside the Process tab (they're effectively process-of-attribution settings
    for GHG accounting). When False, they don't render at all.

    The Process tab is always shown when ``do_ghg=True`` even if no Process
    column has options — otherwise the GWP controls would have nowhere to live.
    """
    active_groups: list[tuple[str, list[str]]] = []
    for g_name, g_cols in FILTER_GROUPS.items():
        has_options = any(len(get_options(df_for_units, col)) > 0 for col in g_cols)
        if has_options or (g_name == "Process" and do_ghg):
            active_groups.append((g_name, g_cols))

    if not active_groups:
        st.info("No database filters apply to the selected Source and Target units.")
        return

    tabs = st.tabs([g[0] for g in active_groups])

    for idx, (g_name, _g_cols) in enumerate(active_groups):
        with tabs[idx]:
            if g_name == "Resources":
                f1, f2 = st.columns(2)
                with f1:
                    dynamic_multiselect("Chemical Category", "Source-Chemical Category", df_for_units)
                    dynamic_multiselect("Formula", "Formula", df_for_units)
                with f2:
                    dynamic_multiselect("Chemical Type", "Source-Chemical Type", df_for_units)
                    dynamic_multiselect("Property", "Property", df_for_units)

            elif g_name == "Process":
                p1, p2 = st.columns(2)
                with p1:
                    dynamic_multiselect("Process 1", "Process1", df_for_units)
                with p2:
                    dynamic_multiselect("Process 2", "Process2", df_for_units)

                e1, e2 = st.columns([1, 2])
                with e1:
                    st.markdown(
                        f"<div style='font-size:0.85rem; color:{theme['secondary']} !important; "
                        f"font-weight:500; margin-bottom:8px; margin-top:8px;'>SCOPE</div>",
                        unsafe_allow_html=True,
                    )
                    scope_cols = st.columns([1, 1, 1])
                    available_scopes = get_options(df_for_units, "Scope")

                    raw = st.session_state.get("Scope_raw", [])
                    s_c1 = scope_cols[0].checkbox("1", value=("1" in raw)) if "1" in available_scopes else False
                    s_c2 = scope_cols[1].checkbox("2", value=("2" in raw)) if "2" in available_scopes else False
                    s_c3 = scope_cols[2].checkbox("3", value=("3" in raw)) if "3" in available_scopes else False

                    st.session_state["Scope_raw"] = [
                        s for s, b in [("1", s_c1), ("2", s_c2), ("3", s_c3)] if b
                    ]
                    # The graph + DataFrame store Scope as numbers (1.0/2.0/3.0)
                    # while the checkboxes yield string labels. Mirror to ints so
                    # list-membership (engine) and DataFrame .isin() comparisons
                    # match the numeric column (1 == 1.0), and chips still show "1"
                    # not "1.0". Without this, picking a Scope dropped every
                    # emission factor (string "1" never equals float 1.0).
                    st.session_state["Scope"] = [
                        int(s) for s in st.session_state["Scope_raw"]
                    ]
                with e2:
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    dynamic_multiselect("Category", "Category", df_for_units)

                # GWP controls live here when GHG module is active.
                if do_ghg:
                    st.markdown(
                        f"<div style='border-top:1px solid {theme['border']}; "
                        f"margin: 14px 0 8px 0; padding-top: 10px;'>"
                        f"<div style='font-size:0.85rem; color:{theme['secondary']} !important; "
                        f"font-weight:500; margin-bottom:6px;'>"
                        "GHG WEIGHTING (IPCC GWP)</div></div>",
                        unsafe_allow_html=True,
                    )
                    # Narrow columns so dropdowns don't stretch full-width.
                    g1, g2, _g_sp = st.columns([1, 1, 3])
                    with g1:
                        st.selectbox(
                            "Assessment Report",
                            options=["AR4", "AR5", "AR6"],
                            key="gwp_report",
                            help=(
                                "Which IPCC Assessment Report's GWP values to use. "
                                "AR4 = 2007, AR5 = 2014, AR6 = 2021. Different reports "
                                "publish different GWPs for the same gases as the science evolves."
                            ),
                        )
                    with g2:
                        st.selectbox(
                            "Time Horizon (yr)",
                            options=["20", "100", "500"],
                            key="gwp_horizon",
                            help=(
                                "Integration window for GWP. Shorter horizons emphasize "
                                "short-lived gases (CH₄ over 20 yr ≈ 84; over 100 yr ≈ 28). "
                                "100-year is the standard regulatory horizon."
                            ),
                        )

            elif g_name == "Location":
                g1, g2 = st.columns(2)
                with g1:
                    dynamic_multiselect("Country", "Country", df_for_units)
                with g2:
                    dynamic_multiselect("eGRID Region", "eGRID", df_for_units)

            elif g_name == "Data Source":
                sm1, sm2 = st.columns(2)
                with sm1:
                    dynamic_multiselect("Agency", "Agency", df_for_units)
                with sm2:
                    dynamic_multiselect("Dataset", "Dataset", df_for_units)


# --------------------------------------------------------------------------- #
# search_params builder                                                        #
# --------------------------------------------------------------------------- #


def build_search_params(
    active_sets: list[str],
    dy_mode_engine: str,
    dy_values: list[float],
) -> dict:
    search_params: dict = {
        "Set": active_sets if active_sets else None,
        "Numerator Dimension": None,
        "Numerator System": None,
        "Denominator Dimension": None,
        "Denominator System": None,
        "Asset": None,
        "Mode": None,
        "Vehicle1": None,
        "Vehicle2": None,
        "Source-Vehicle Category": None,
        "Source-Vehicle Type": None,
        "Source-Process Type": None,
        "Chemical1": None,
        "Chemical2": None,
        "Source-Material Type": None,
        "IPCC Report": None,
        "GHG": None,
        "Location in File": None,
        "Release Date": None,
        "Updated": None,
        "Data Year": {"mode": dy_mode_engine, "values": dy_values},
    }

    for col in COLS_TO_EXTRACT:
        val = st.session_state.get(col, [])
        search_params[col] = val if val else None

    return search_params
