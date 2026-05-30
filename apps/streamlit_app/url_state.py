"""Round-trip the user's configuration through ``st.query_params``.

Two entry points:

- :func:`hydrate_from_query_params` — called early in ``app.py`` before any
  widgets render. If the page was loaded with a bookmark URL, this populates
  ``st.session_state`` from the URL so widgets render in the bookmarked state.

- :func:`sync_to_query_params` — called late in ``app.py`` after state is
  stable. Mirrors the current ``st.session_state`` into the URL so the
  current URL bar reflects the live configuration and is shareable.

Why this lives in its own module: clean separation between Streamlit state
plumbing and the URL encoding rules. Tested without a Streamlit runtime by
mocking ``st.query_params`` as a plain dict.
"""

from __future__ import annotations

import streamlit as st


# Single-value session_state keys that round-trip cleanly through URL params.
# Each value gets stringified going out and re-parsed coming in.
URL_SAFE_KEYS: tuple[str, ...] = (
    "theme",
    "source_unit_sb", "source_dim",
    "target_unit_sb", "target_dim",
    "start_val",
    "cb_mod_conv", "cb_mod_mag", "cb_mod_fuel", "cb_mod_ghg",
    "dy_mode_radio",
    "gwp_report", "gwp_horizon",
    "max_paths",
    "start_yr_input", "end_yr_input",
)

# List-valued filter columns. Each filter's selection set encodes as a
# comma-separated list under a ``f_<safe_key>`` URL param so the namespace
# stays tidy.
FILTER_KEYS: tuple[str, ...] = (
    "Source-Chemical Category", "Source-Chemical Type",
    "Formula", "Property",
    "Process1", "Process2", "Scope_raw", "Category",
    "Region", "Country", "State",
    "Agency", "Dataset", "Data Year",
)


def _filter_url_key(col: str) -> str:
    """Map a Data Library column name to a URL-safe query-param key."""
    return "f_" + col.lower().replace(" ", "_").replace("-", "_")


def _parse_max_paths(v: str):
    """``max_paths`` is int-or-"All". Parse defensively."""
    if v == "All":
        return "All"
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------------- #
# Hydrate (URL -> session_state)                                                #
# --------------------------------------------------------------------------- #


_HYDRATED_FLAG = "_url_hydrated"


def hydrate_from_query_params(query_params=None) -> int:
    """Populate ``st.session_state`` from the URL. Returns count of keys hydrated.

    Runs **at most once per session** — guarded by ``_url_hydrated`` flag.
    Without this guard, every widget interaction triggers a rerun whose
    hydrate would clobber the user's just-changed selection by re-reading
    the URL (which ``sync_to_query_params`` hasn't yet rewritten for this
    rerun). The flag preserves the bookmark-restore semantic while letting
    subsequent reruns leave session_state alone.

    Skips silently if the page was loaded with no params (so a clean visit
    uses defaults from :mod:`state`).
    """
    if st.session_state.get(_HYDRATED_FLAG):
        return 0
    qp = query_params if query_params is not None else st.query_params
    if not qp:
        st.session_state[_HYDRATED_FLAG] = True
        return 0

    hydrated = 0
    for k in URL_SAFE_KEYS:
        if k not in qp:
            continue
        raw = qp[k]
        if k.startswith("cb_mod_"):
            st.session_state[k] = raw in ("1", "true", "True")
            hydrated += 1
        elif k == "start_val":
            try:
                st.session_state[k] = float(raw)
                hydrated += 1
            except (ValueError, TypeError):
                pass
        elif k == "max_paths":
            parsed = _parse_max_paths(raw)
            if parsed is not None:
                st.session_state[k] = parsed
                hydrated += 1
        elif k in ("start_yr_input", "end_yr_input"):
            try:
                st.session_state[k] = int(raw)
                hydrated += 1
            except (ValueError, TypeError):
                pass
        else:
            st.session_state[k] = raw
            hydrated += 1

    for col in FILTER_KEYS:
        url_key = _filter_url_key(col)
        if url_key in qp:
            raw = qp[url_key]
            st.session_state[col] = raw.split(",") if raw else []
            hydrated += 1

    st.session_state[_HYDRATED_FLAG] = True
    return hydrated


# --------------------------------------------------------------------------- #
# Sync (session_state -> URL)                                                   #
# --------------------------------------------------------------------------- #


def _set_or_pop(qp, key: str, value) -> None:
    """Write ``value`` to ``qp[key]``, or remove the key if value is empty."""
    if value is None or value == "":
        try:
            del qp[key]
        except (KeyError, AttributeError):
            pass
    else:
        qp[key] = value


def sync_to_query_params(query_params=None) -> int:
    """Mirror current session_state into the URL. Returns count of keys written.

    Called after widgets have rendered (every rerun). Empty/default values
    are stripped so the URL stays short. Note: the internal ``_url_hydrated``
    flag is never written — it's a session-lifetime marker, not configuration.
    """
    qp = query_params if query_params is not None else st.query_params
    written = 0
    # Defensive: strip the internal hydration flag if it ever leaks in
    try:
        del qp[_HYDRATED_FLAG]
    except (KeyError, AttributeError):
        pass

    for k in URL_SAFE_KEYS:
        val = st.session_state.get(k)
        if val is None:
            _set_or_pop(qp, k, None)
            continue
        if k.startswith("cb_mod_"):
            # Skip defaults (all checkboxes default to True) to keep URL clean
            if val is True:
                _set_or_pop(qp, k, None)
            else:
                _set_or_pop(qp, k, "0")
                written += 1
        elif isinstance(val, (int, float, str, bool)):
            _set_or_pop(qp, k, str(val))
            written += 1
        else:
            # Unsupported type — skip silently rather than crash
            continue

    for col in FILTER_KEYS:
        url_key = _filter_url_key(col)
        val = st.session_state.get(col)
        if not val:
            _set_or_pop(qp, url_key, None)
        else:
            _set_or_pop(qp, url_key, ",".join(str(v) for v in val))
            written += 1

    return written


def build_shareable_link(base_url: str = "") -> str:
    """Build a shareable URL with current state encoded as query params.

    Side-effect-free relative to ``sync_to_query_params`` — caller chooses
    when to actually mutate ``st.query_params``.
    """
    from urllib.parse import urlencode

    # Build a fresh dict mirroring what sync_to_query_params would write.
    params: dict[str, str] = {}
    for k in URL_SAFE_KEYS:
        val = st.session_state.get(k)
        if val is None:
            continue
        if k.startswith("cb_mod_"):
            if val is False:
                params[k] = "0"
            continue
        if isinstance(val, (int, float, str, bool)):
            params[k] = str(val)

    for col in FILTER_KEYS:
        val = st.session_state.get(col)
        if val:
            params[_filter_url_key(col)] = ",".join(str(v) for v in val)

    qs = urlencode(params)
    return f"{base_url}?{qs}" if qs else base_url
