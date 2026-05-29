"""UnitGPS — Streamlit UI (Claude generation).

Thin entry point. Responsibilities:
1. Page config + theme injection
2. Load the engine (cached) from Claude/data/
3. Assemble the layout — defers to themes/state/filters/renderers modules

Run from the project root with:
    streamlit run apps/streamlit_app/app.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

# --------------------------------------------------------------------------- #
# Path bootstrap                                                               #
# --------------------------------------------------------------------------- #
APP_DIR = Path(__file__).resolve().parent
CLAUDE_ROOT = APP_DIR.parents[1]
SRC_DIR = CLAUDE_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

APPS_DIR = APP_DIR.parent
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

from unitgps.engine import DataLoader, UnitGraph  # noqa: E402

from streamlit_app.filters import (  # noqa: E402
    COLS_TO_EXTRACT,
    apply_db_and_temporal_filters,
    build_search_params,
    get_options,
    render_active_filter_chips,
    render_filter_tabs,
)
from streamlit_app.renderers.conversion import render_conversion_panel  # noqa: E402
from streamlit_app.renderers.emissions import render_emissions_panel  # noqa: E402
from streamlit_app.state import (  # noqa: E402
    init_session_state,
    make_sync_callbacks,
    on_final_change,
    on_start_change,
)
from streamlit_app.themes import THEMES, get_theme, inject_css  # noqa: E402
from streamlit_app.url_state import (  # noqa: E402
    build_shareable_link,
    hydrate_from_query_params,
    sync_to_query_params,
)

logger = logging.getLogger("unitgps.streamlit")

# --------------------------------------------------------------------------- #
# Page config + theme                                                          #
# --------------------------------------------------------------------------- #

st.set_page_config(
    page_title="UnitGPS",
    # Centered (not wide) so Streamlit's own CSS caps the content area; we
    # expand the cap to our preferred 1040px via inject_css in themes.py.
    layout="centered",
    page_icon="🧭",
    initial_sidebar_state="collapsed",
)

hydrate_from_query_params()
init_session_state()
theme = get_theme(st.session_state["theme"])
inject_css(theme)

# --------------------------------------------------------------------------- #
# Engine loading (cached across reruns)                                        #
# --------------------------------------------------------------------------- #

DATA_DIR = CLAUDE_ROOT / "data"
DATA_LIBRARY = DATA_DIR / "Data Library, 2025-10-18, 1960-2023.xlsx"
GWP_FILE = DATA_DIR / "IPCC GWPs AR4-AR6.xlsx"


@st.cache_resource(show_spinner="Loading Engine...")
def load_engine():
    loader = DataLoader(str(DATA_LIBRARY), str(GWP_FILE))
    combined_data = loader.load_data_library()

    if (
        "Source-Chemical Category" in combined_data.columns
        and "Source-Chemical Type" in combined_data.columns
    ):
        type_to_cat = (
            combined_data.dropna(subset=["Source-Chemical Category"])
            .set_index("Source-Chemical Type")["Source-Chemical Category"]
            .to_dict()
        )
        mask = (
            combined_data["Source-Chemical Category"].isnull()
            & combined_data["Source-Chemical Type"].isin(type_to_cat)
        )
        combined_data.loc[mask, "Source-Chemical Category"] = combined_data["Source-Chemical Type"].map(
            type_to_cat
        )

    node_attrs = loader.get_units_attributes(combined_data)
    gwps = loader.load_gwps()
    graph_engine = UnitGraph(combined_data, node_attrs)

    return graph_engine, gwps, combined_data, node_attrs


try:
    graph_engine, gwps_data, combined_data, node_attrs = load_engine()
except Exception as e:  # noqa: BLE001
    st.error(f"Failed to load data engine: {e}")
    st.stop()

sync_callbacks = make_sync_callbacks(node_attrs)

# --------------------------------------------------------------------------- #
# Module toggles + filter pre-computation                                      #
# --------------------------------------------------------------------------- #

do_conv = st.session_state.get("cb_mod_conv", True)
do_mag = st.session_state.get("cb_mod_mag", True)
do_fuel = st.session_state.get("cb_mod_fuel", True)
do_ghg = st.session_state.get("cb_mod_ghg", True)

active_sets: list[str] = []
if do_conv:
    active_sets.extend(["Unit Conversion", "Unit Conversions"])
if do_ghg:
    active_sets.append("Emission Factors")
if do_fuel:
    active_sets.append("Chemical Properties")
if do_mag:
    active_sets.append("Magnitude Adjustment")

df_for_units = (
    combined_data[combined_data["Set"].isin(active_sets)] if active_sets else combined_data.iloc[0:0]
)

search_params_raw: dict = {}
for col in COLS_TO_EXTRACT:
    val = st.session_state.get(col, [])
    if val:
        search_params_raw[col] = val

mode = st.session_state.get("dy_mode", "All Years")
dy_vals = st.session_state.get("Data Year", [])
start_yr = st.session_state.get("start_yr_input", 2010)
end_yr = st.session_state.get("end_yr_input", 2024)

df_for_units = apply_db_and_temporal_filters(
    df_for_units, search_params_raw, mode, start_yr, end_yr, dy_vals, exempt_static_conversions=True
)

available_units = sorted(
    set(df_for_units["Numerator"].dropna()).union(set(df_for_units["Denominator"].dropna()))
)
available_dims_set: set = set()
for u in available_units:
    dim = node_attrs.get(u, {}).get("Unit Dimension")
    if dim:
        available_dims_set.add(dim)
available_dims = sorted(available_dims_set)

if not available_dims:
    available_units = sorted(
        set(combined_data["Numerator"].dropna()).union(set(combined_data["Denominator"].dropna()))
    )
    available_dims_set = set()
    for u in available_units:
        dim = node_attrs.get(u, {}).get("Unit Dimension")
        if dim:
            available_dims_set.add(dim)
    available_dims = sorted(available_dims_set)

if do_ghg:
    if st.session_state.get("target_dim") != "Weight":
        st.session_state["target_dim"] = "Weight"
    tgt_unit = st.session_state.get("target_unit_sb")
    if tgt_unit:
        if node_attrs.get(tgt_unit, {}).get("Unit Dimension") != "Weight":
            st.session_state["target_unit_sb"] = None


def get_units_for_dim_local(dim):
    if dim:
        valid = [u for u, attr in node_attrs.items() if attr.get("Unit Dimension") == dim]
        return sorted(valid) if valid else available_units
    valid_set = set(available_units)
    for u, attr in node_attrs.items():
        if attr.get("Unit Dimension") in available_dims:
            valid_set.add(u)
    return sorted(valid_set)


# --------------------------------------------------------------------------- #
# Header + Theme picker                                                        #
# --------------------------------------------------------------------------- #

# vertical_alignment="center" lines all three controls up on a common
# baseline regardless of their intrinsic heights (the title is a heading,
# Share is a button, Theme is a selectbox — they're all different sizes).
h_title, h_link, h_theme = st.columns([4, 2, 2.2], vertical_alignment="center")
with h_title:
    # Use a flex container so the title can size itself and we keep its
    # vertical center aligned with the row. Bumped weight + font-size for
    # readability; the primary color stays for the brand.
    st.markdown(
        f"<div style='display: flex; align-items: center; gap: 8px; "
        f"font-size: 1.45rem; font-weight: 600; "
        f"color: {theme['primary']} !important; line-height: 1;'>"
        f"<span>🧭</span><span>UnitGPS Workspace</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
with h_link:
    # Share-link popover. use_container_width keeps the button height
    # consistent with the selectbox so they line up cleanly.
    with st.popover("🔗 Share link", use_container_width=True):
        link = build_shareable_link()
        st.caption(
            "Copy this link to bookmark or share the current configuration "
            "(source/target/units/modules/filters/theme). Reopening it restores "
            "the same state — handy for repeat calculations or sending a "
            "specific scenario to a colleague."
        )
        st.code(link or "?", language="text")
with h_theme:
    # label_visibility="collapsed" hides the "UI Theme" label so the
    # selectbox's input sits at the same baseline as the title text and
    # Share button. The label was making this column ~22px taller and
    # visibly out of alignment with the rest of the row.
    st.selectbox(
        "UI Theme",
        options=list(THEMES.keys()),
        key="theme",
        label_visibility="collapsed",
    )

# --------------------------------------------------------------------------- #
# Source / Target setup                                                        #
# --------------------------------------------------------------------------- #

col_src, col_arr, col_tgt = st.columns([1, 0.1, 1])

with col_src:
    with st.container(border=True):
        st.markdown(
            f"<h4 style='color: {theme['primary']} !important; margin-top: 0; margin-bottom: 10px;'>"
            "Source</h4>",
            unsafe_allow_html=True,
        )
        s1, s2, s3 = st.columns([2, 3, 3])
        with s3:
            if st.session_state.get("source_dim") not in available_dims:
                st.session_state["source_dim"] = None
            source_dim = st.selectbox(
                f"Dimension ({len(available_dims)})",
                options=available_dims,
                key="source_dim",
                placeholder="All Dimensions",
                on_change=sync_callbacks["source_unit"],
            )
        with s2:
            s_opts = get_units_for_dim_local(source_dim)
            if st.session_state.get("source_unit_sb") not in s_opts:
                st.session_state["source_unit_sb"] = None
            source_unit = st.selectbox(
                f"Unit ({len(s_opts)})",
                options=s_opts,
                key="source_unit_sb",
                placeholder="Select Unit",
                on_change=sync_callbacks["source_dim"],
            )
        with s1:
            start_val_container = st.container()

with col_arr:
    st.markdown(
        f"<div style='text-align: center; font-size: 28px; color: {theme['secondary']} !important; "
        "margin-top: 55px;'>➔</div>",
        unsafe_allow_html=True,
    )

with col_tgt:
    with st.container(border=True):
        st.markdown(
            f"<h4 style='color: {theme['primary']} !important; margin-top: 0; margin-bottom: 10px;'>"
            "Target</h4>",
            unsafe_allow_html=True,
        )
        t1, t2, t3 = st.columns([2, 3, 3])
        with t3:
            t_dim_opts = ["Weight"] if do_ghg else available_dims
            if st.session_state.get("target_dim") not in t_dim_opts:
                st.session_state["target_dim"] = "Weight" if do_ghg else None
            target_dim = st.selectbox(
                f"Dimension ({len(t_dim_opts)})",
                options=t_dim_opts,
                key="target_dim",
                placeholder="All Dimensions",
                on_change=sync_callbacks["target_unit"],
                disabled=do_ghg,
            )
        with t2:
            if do_ghg:
                t_opts = [u for u in available_units if node_attrs.get(u, {}).get("Unit Dimension") == "Weight"]
                if not t_opts:
                    t_opts = [u for u, attr in node_attrs.items() if attr.get("Unit Dimension") == "Weight"]
            else:
                t_opts = get_units_for_dim_local(target_dim)
            if st.session_state.get("target_unit_sb") not in t_opts:
                st.session_state["target_unit_sb"] = None
            target_unit = st.selectbox(
                f"Unit ({len(t_opts)})",
                options=t_opts,
                key="target_unit_sb",
                placeholder="Select Unit",
                on_change=sync_callbacks["target_dim"],
            )
        with t1:
            final_val_container = st.container()

# --------------------------------------------------------------------------- #
# Module toggles (with live counts)                                            #
# --------------------------------------------------------------------------- #

temp_df = apply_db_and_temporal_filters(
    combined_data, search_params_raw, mode, start_yr, end_yr, dy_vals
)
conv_count = len(temp_df[temp_df["Set"].isin(["Unit Conversion", "Unit Conversions"])])
mag_count = len(temp_df[temp_df["Set"] == "Magnitude Adjustment"])
fuel_count = len(temp_df[temp_df["Set"] == "Chemical Properties"])
ghg_count = len(temp_df[temp_df["Set"] == "Emission Factors"])

st.markdown("<h3 style='margin-top: 5px; margin-bottom: 5px;'>Modules</h3>", unsafe_allow_html=True)
m_cols = st.columns([2.2, 2.2, 2.2, 2.2, 1.2])
with m_cols[0]:
    st.markdown("<div class='modules-container-flag'></div>", unsafe_allow_html=True)
    st.checkbox(f"🔄 Unit Conversions ({conv_count})", value=st.session_state.get("cb_mod_conv", True), key="cb_mod_conv")
with m_cols[1]:
    st.checkbox(f"📐 Magnitude Adjustments ({mag_count})", value=st.session_state.get("cb_mod_mag", True), key="cb_mod_mag")
with m_cols[2]:
    st.checkbox(f"⛽ Fuel Properties ({fuel_count})", value=st.session_state.get("cb_mod_fuel", True), key="cb_mod_fuel")
with m_cols[3]:
    st.checkbox(f"🌍 GHG Emissions ({ghg_count})", value=st.session_state.get("cb_mod_ghg", True), key="cb_mod_ghg")

# --------------------------------------------------------------------------- #
# Filter session_state defaults                                                #
# --------------------------------------------------------------------------- #
for col in COLS_TO_EXTRACT:
    if col not in st.session_state:
        st.session_state[col] = []

# --------------------------------------------------------------------------- #
# Temporal scope                                                               #
# --------------------------------------------------------------------------- #

st.markdown("<h3 style='margin-top: 15px; margin-bottom: 5px;'>Temporal Scope</h3>", unsafe_allow_html=True)

mode_temp = st.session_state.get("dy_mode_radio", "All Years")
if mode_temp == "Specific Years":
    col_radio, col_input = st.columns([7.5, 1.5])
elif mode_temp == "Range":
    col_radio, col_input = st.columns([7.0, 2.0])
else:
    col_radio, col_input = st.columns([7.5, 1.5])

with col_radio:
    mode = st.radio(
        "Temporal Scope",
        ["All Years", "Most Recent Global", "Most Recent per Path", "Specific Years", "Range"],
        horizontal=True,
        label_visibility="collapsed",
        key="dy_mode_radio",
    )
    st.session_state["dy_mode"] = mode

dy_values: list = []
dy_mode_engine = "all"

with col_input:
    if mode == "Specific Years":
        year_opts = get_options(df_for_units, "Data Year")
        st.session_state["Data Year"] = st.multiselect(
            "Select Exact Years",
            options=year_opts,
            placeholder=f"{len(year_opts)} options",
            label_visibility="collapsed",
        )
        dy_values = [float(v) for v in st.session_state["Data Year"]]
        dy_mode_engine = "exact"
    elif mode == "Range":
        r1, r2 = st.columns(2)
        max_db_yr = int(combined_data["Data Year"].dropna().max()) if "Data Year" in combined_data else 2024
        min_db_yr = int(combined_data["Data Year"].dropna().min()) if "Data Year" in combined_data else 1960
        all_years = list(range(max_db_yr, min_db_yr - 1, -1))

        default_start = max_db_yr - 4
        default_end = max_db_yr
        idx_start = all_years.index(default_start) if default_start in all_years else len(all_years) - 1
        idx_end = all_years.index(default_end) if default_end in all_years else 0

        # Set session_state defaults BEFORE the widgets render so we can
        # safely drop the conflicting index= argument.
        if st.session_state.get("start_yr_input") not in all_years:
            st.session_state["start_yr_input"] = all_years[idx_start]
        if st.session_state.get("end_yr_input") not in all_years:
            st.session_state["end_yr_input"] = all_years[idx_end]
        with r1:
            start_yr = st.selectbox("From", options=all_years, key="start_yr_input", label_visibility="collapsed")
        with r2:
            end_yr = st.selectbox("To", options=all_years, key="end_yr_input", label_visibility="collapsed")

        dy_values = [float(start_yr), float(end_yr)]
        dy_mode_engine = "range"
    else:
        if mode == "Most Recent Global":
            dy_mode_engine = "recent_global"
        elif mode == "Most Recent per Path":
            dy_mode_engine = "recent_edge"

# --------------------------------------------------------------------------- #
# Database filters tab group + Calculate button                                #
# --------------------------------------------------------------------------- #

with st.container():
    st.markdown('<div class="db-filters-anchor"></div>', unsafe_allow_html=True)
    title_col, calc_c1, calc_c2, calc_c3 = st.columns(
        [4.6, 0.7, 1.0, 1.3], vertical_alignment="bottom"
    )
    with title_col:
        st.markdown("<h3 style='margin-top:0px; margin-bottom:5px;'>Database Filters</h3>", unsafe_allow_html=True)
    with calc_c1:
        st.markdown(
            "<div style='text-align: right; margin-bottom: 12px;'>"
            "<span class='calc-btn-anchor'>MAX PATHS</span></div>",
            unsafe_allow_html=True,
        )
    with calc_c2:
        st.selectbox(
            "Max Paths",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 25, 50, 75, 100, "All"],
            key="max_paths",
            label_visibility="collapsed",
        )
    with calc_c3:
        run_btn = st.button("Calculate", type="primary", key="calc_btn_main", use_container_width=True)

    if run_btn:
        st.session_state["run_clicked"] = True

    # Display-only summary of every active filter selection — sits above the
    # filter tabs as a scannable reminder of what's currently narrowing the search.
    render_active_filter_chips(theme)

    render_filter_tabs(df_for_units, theme, do_ghg=do_ghg)

# --------------------------------------------------------------------------- #
# Build search_params for the engine                                           #
# --------------------------------------------------------------------------- #

search_params = build_search_params(active_sets, dy_mode_engine, dy_values)

# --------------------------------------------------------------------------- #
# Run + render results                                                         #
# --------------------------------------------------------------------------- #

if not source_unit or not target_unit:
    st.session_state["run_clicked"] = False

if st.session_state.get("run_clicked", False):
    if not source_unit or not target_unit:
        st.warning("Please select valid source and target units.")
    elif not active_sets:
        st.warning("Please select at least one module to perform calculations.")
    else:
        st.markdown(f"<hr style='border-color: {theme['border']};'>", unsafe_allow_html=True)

        op_modes: list[str] = []
        if do_conv or do_mag or do_fuel:
            op_modes.append("conv")
        target_is_weight = (
            target_unit is not None
            and node_attrs.get(target_unit, {}).get("Unit Dimension") == "Weight"
        )
        if do_ghg and target_is_weight:
            op_modes.append("ghg")

        sync_done = False

        # Result panels render full-width and stacked vertically.
        if "conv" in op_modes:
            sync_done = render_conversion_panel(
                graph_engine, search_params, source_unit, target_unit, theme
            )

        if "ghg" in op_modes:
            render_emissions_panel(
                graph_engine, search_params, source_unit, target_unit,
                gwps_data, theme, sync_done,
                gwp_report=st.session_state.get("gwp_report", "AR5"),
                gwp_horizon=st.session_state.get("gwp_horizon", "100"),
            )

# --------------------------------------------------------------------------- #
# Two-way numeric inputs (rendered last so the result calc can update them)   #
# --------------------------------------------------------------------------- #

with start_val_container:
    st.number_input("Starting Value", step=None, key="start_val", on_change=on_start_change)

with final_val_container:
    st.number_input("Final Value", step=None, key="final_val", on_change=on_final_change)


# --------------------------------------------------------------------------- #
# URL state sync — mirror live session_state into st.query_params so the URL  #
# bar reflects the current configuration and is shareable.                    #
# --------------------------------------------------------------------------- #
sync_to_query_params()
