"""Database-filter UI + the temporal/db filtering helper."""

from __future__ import annotations

from typing import Iterable, List

import networkx as nx
import pandas as pd
import streamlit as st


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
    """Apply database column + temporal (Data Year) filters to a DataFrame.

    Infrastructure rows (unit conversions, magnitude adjustments) always pass -
    they have no provenance and are needed to chain multi-step paths. Every
    other row must match each selected filter; a blank scope value excludes it
    (picking an electricity-only column like eGRID drops fuel rows). Data Year
    treats a blank year as a wildcard. ``exempt_static_conversions`` is retained
    for call-site compatibility.
    """
    infra = df["Set"].isin(["Unit Conversion", "Magnitude Adjustment", "Unit Conversions"])
    ok = pd.Series(True, index=df.index)
    for col, search_val in search_params.items():
        if not search_val or col not in df.columns:
            continue
        ok = ok & df[col].isin(search_val)
    if "Data Year" in df.columns:
        has_no_year = df["Data Year"].isna()
        if mode == "Specific Years" and dy_vals:
            yrs = [float(v) for v in dy_vals]
            ok = ok & (has_no_year | df["Data Year"].isin(yrs))
        elif mode == "Range" and start_yr is not None and end_yr is not None:
            ok = ok & (has_no_year | ((df["Data Year"] >= start_yr) & (df["Data Year"] <= end_yr)))
    return df[infra | ok]


def _dimension_reach(graph_df, node_attrs, source_dim, target_dim):
    """``(fwd, rev)``: dimensions reachable FROM ``source_dim`` and dimensions
    that can REACH ``target_dim``, on the dimension-reduced graph (units
    collapsed to their Unit Dimension, parallel edges merged). ``None`` when
    there is no source->target dimensional path.
    """
    dim_of = lambda u: node_attrs.get(u, {}).get("Unit Dimension")
    g = nx.DiGraph()
    for a, b in graph_df[["Denominator", "Numerator"]].dropna().itertuples(index=False, name=None):
        da, db = dim_of(a), dim_of(b)
        if da and db:
            g.add_edge(da, db)
    if source_dim not in g or target_dim not in g:
        return None
    fwd = set(nx.single_source_shortest_path_length(g, source_dim))
    if target_dim not in fwd:
        return None
    rev = set(nx.single_source_shortest_path_length(g.reverse(copy=False), target_dim))
    return fwd, rev


def apply_pathway_scope(
    df_to_scope: pd.DataFrame,
    graph_df: pd.DataFrame,
    source_unit: str | None,
    target_unit: str | None,
    node_attrs: dict,
) -> pd.DataFrame:
    """Narrow ``df_to_scope`` to rows on the source->target *dimensional* pathway.

    Scoping is by **dimension**, not by individual unit: keep a row
    (Denominator->Numerator edge) when its source dimension is reachable from
    the source unit's dimension AND its target dimension can reach the target
    unit's dimension. So every unit of an on-pathway dimension is offered — an
    electricity (MWh) emission factor stays available when the source is J,
    because both are Energy and J can reach any energy unit. Falls back to the
    full frame when source/target are unset, identical, dimensionless, or
    unreachable, so the panel never blanks by surprise.
    """
    dim_of = lambda u: node_attrs.get(u, {}).get("Unit Dimension")
    if not source_unit or not target_unit or source_unit == target_unit:
        return df_to_scope
    sdim, tdim = dim_of(source_unit), dim_of(target_unit)
    if not sdim or not tdim:
        return df_to_scope
    reach = _dimension_reach(graph_df, node_attrs, sdim, tdim)
    if reach is None:
        return df_to_scope
    fwd, rev = reach
    keep = [
        (dim_of(a) in fwd and dim_of(b) in rev)
        for a, b in zip(df_to_scope["Denominator"], df_to_scope["Numerator"])
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


def dimension_digraph(graph_df: pd.DataFrame, node_attrs: dict) -> "nx.DiGraph":
    """Dimension-reduced DiGraph: nodes are Unit Dimensions, with an edge
    ``dim(a) -> dim(b)`` whenever any unit edge ``a -> b`` crosses those two
    dimensions. Reachability on this tiny graph answers "which dimensions can a
    given dimension reach" in O(dims), independent of the ~5k unit edges.
    """
    dim_of = lambda u: node_attrs.get(u, {}).get("Unit Dimension")
    g = nx.DiGraph()
    for a, b in graph_df[["Denominator", "Numerator"]].dropna().itertuples(index=False, name=None):
        da, db = dim_of(a), dim_of(b)
        if da and db:
            g.add_edge(da, db)
    return g


def dimension_reach(graph_df: pd.DataFrame, node_attrs: dict, source_dim, target_dim):
    """``(reachable_from_source, can_reach_target)`` dimension sets on the
    dimension-reduced graph. Each is ``None`` when its dimension is unset (= no
    constraint), else a set that always includes the dimension itself.

    Used to scope the Source/Target dimension pickers so you can only pick a
    target a source can actually reach (Area reaches only Area; Energy reaches
    Weight when an emission-factor path is in the active modules).
    """
    g = dimension_digraph(graph_df, node_attrs)
    from_src = None
    if source_dim:
        from_src = {source_dim} | (nx.descendants(g, source_dim) if source_dim in g else set())
    to_tgt = None
    if target_dim:
        to_tgt = {target_dim} | (nx.ancestors(g, target_dim) if target_dim in g else set())
    return from_src, to_tgt


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
# Filter group rendering                                                       #
# --------------------------------------------------------------------------- #


def get_active_filter_groups(df_for_units: pd.DataFrame, do_ghg: bool = False) -> list[str]:
    """Names of filter groups that currently have options (Process kept when do_ghg)."""
    names: list[str] = []
    for g_name, g_cols in FILTER_GROUPS.items():
        has_options = any(len(get_options(df_for_units, col)) > 0 for col in g_cols)
        if has_options or (g_name == "Process" and do_ghg):
            names.append(g_name)
    return names


def render_filter_group(g_name: str, df_for_units: pd.DataFrame, theme: dict) -> None:
    """Render one filter group's widgets, full width."""
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
            st.session_state["Scope"] = [int(s) for s in st.session_state["Scope_raw"]]
        with e2:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            dynamic_multiselect("Category", "Category", df_for_units)

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


def render_filter_tabs(df_for_units: pd.DataFrame, theme: dict, do_ghg: bool = False) -> None:
    """Legacy tabbed view (kept for compatibility; the app now uses an inline selector)."""
    names = get_active_filter_groups(df_for_units, do_ghg)
    if not names:
        st.info("No database filters apply to the selected Source and Target units.")
        return
    tabs = st.tabs(names)
    for idx, g_name in enumerate(names):
        with tabs[idx]:
            render_filter_group(g_name, df_for_units, theme)


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
