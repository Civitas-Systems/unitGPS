"""Session-state defaults and bi-directional sync callbacks.

Streamlit's session_state is the only place we hold cross-rerun UI state.
``init_session_state`` is idempotent — call it once at the top of the app.
"""

from __future__ import annotations

import streamlit as st

# --------------------------------------------------------------------------- #
# Defaults                                                                     #
# --------------------------------------------------------------------------- #

_DEFAULTS: dict[str, object] = {
    "theme": "Obsidian",
    "start_val": 1.0,
    "final_val": 0.0,
    "calc_direction": "forward",
    "source_dim": "Energy",
    "source_unit_sb": "J",
    "target_dim": "Weight",
    "target_unit_sb": "kg",
    "dy_mode": "All Years",
    "dy_mode_radio": "All Years",
    "Data Year": [],
    "run_clicked": False,
    "max_paths": 5,
    "gwp_report": "AR5",
    "gwp_horizon": "100",
    "conv_collapsed": False,
    "ghg_collapsed": False,
    # Sticky user picks for ambiguous edges: {(source, target): edge_index}
    "_edge_picks": {},
}


def init_session_state() -> None:
    """Populate any missing keys in st.session_state with their defaults."""
    for k, v in _DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


# --------------------------------------------------------------------------- #
# Bi-directional sync callbacks                                                #
# --------------------------------------------------------------------------- #


def on_start_change() -> None:
    """Editing the Starting Value means we calculate forward."""
    st.session_state["calc_direction"] = "forward"


def on_final_change() -> None:
    """Editing the Final Value means we back-solve from the target."""
    st.session_state["calc_direction"] = "backward"


def make_sync_callbacks(node_attrs: dict) -> dict:
    """Build the dimension↔unit sync callbacks bound to the live node_attrs."""

    def sync_source_dim() -> None:
        unit = st.session_state.get("source_unit_sb")
        if unit:
            dim = node_attrs.get(unit, {}).get("Unit Dimension")
            if dim:
                st.session_state["source_dim"] = dim

    def sync_source_unit() -> None:
        dim = st.session_state.get("source_dim")
        unit = st.session_state.get("source_unit_sb")
        if dim and unit:
            if node_attrs.get(unit, {}).get("Unit Dimension") != dim:
                st.session_state["source_unit_sb"] = None

    def sync_target_dim() -> None:
        unit = st.session_state.get("target_unit_sb")
        if unit:
            dim = node_attrs.get(unit, {}).get("Unit Dimension")
            if dim:
                st.session_state["target_dim"] = dim

    def sync_target_unit() -> None:
        dim = st.session_state.get("target_dim")
        unit = st.session_state.get("target_unit_sb")
        if dim and unit:
            if node_attrs.get(unit, {}).get("Unit Dimension") != dim:
                st.session_state["target_unit_sb"] = None

    return {
        "source_dim": sync_source_dim,
        "source_unit": sync_source_unit,
        "target_dim": sync_target_dim,
        "target_unit": sync_target_unit,
    }
