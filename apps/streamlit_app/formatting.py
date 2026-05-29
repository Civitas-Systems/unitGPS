"""Pure formatting helpers — no Streamlit dependency.

Date normalization (YYYY-MMM-DD), parameter value tidying, and number
formatters for both HTML (with Unicode superscripts) and LaTeX. Used by
the audit-card renderers and the GHG-derivation expander.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, List

from unitgps.engine import format_sig_figs

# --------------------------------------------------------------------------- #
# Audit-card formatters                                                        #
# --------------------------------------------------------------------------- #

_MONTH_ABBR = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)

_DATE_PARSE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
)


def format_audit_date(value: Any) -> str:
    """Render a date as ``YYYY-MMM-DD`` (e.g. ``2025-Aug-22``).

    Accepts datetime / date objects, ISO-ish strings, and a couple of common
    US/EU date variants. If parsing fails, the original string is returned
    so we never blank out a value just because the formatter is strict.
    """
    if value is None or value == "":
        return ""
    if isinstance(value, datetime):
        d: date = value.date()
    elif isinstance(value, date):
        d = value
    else:
        s = str(value).strip()
        d = None  # type: ignore[assignment]
        for fmt in _DATE_PARSE_FORMATS:
            try:
                d = datetime.strptime(s, fmt).date()
                break
            except ValueError:
                continue
        if d is None:
            return s  # unparseable — return as-is rather than blanking
    return f"{d.year:04d}-{_MONTH_ABBR[d.month - 1]}-{d.day:02d}"


def normalize_param_value(value: Any) -> str:
    """Tidy a parameter value for display.

    - ``1.0`` / ``"1.0"`` -> ``"1"`` (integer-valued floats lose the .0)
    - ``1.5`` -> ``"1.5"``
    - non-numeric strings pass through trimmed
    - ``None`` / empty -> ``""``
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else f"{value:g}"
    s = str(value).strip()
    if not s:
        return ""
    # Try numeric coercion so "1.0" -> "1" without losing "Scope 1.0" etc.
    try:
        f = float(s)
        # Only collapse if the whole string is exactly the number
        if str(f) == s or f"{f:g}" == s:
            return str(int(f)) if f.is_integer() else f"{f:g}"
    except ValueError:
        pass
    return s


# --------------------------------------------------------------------------- #
# Number formatters                                                            #
# --------------------------------------------------------------------------- #


def format_html_num(val) -> str:
    """Format a float for HTML display with Unicode superscript exponents."""
    if val is None:
        return "N/A"
    if val == 0:
        return "0"
    abs_val = abs(val)
    if 1e-5 <= abs_val < 1e6:
        s = f"{val:.6f}"
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        if not s or s == "0" or s == "-0":
            s = f"{val:.5g}"
        return s
    s = f"{val:.4e}"
    base, exp = s.split("e")
    base = base.rstrip("0").rstrip(".") if "." in base else base
    exp_int = int(exp)
    superscripts = {
        "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
        "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
        "-": "⁻", "+": "⁺",
    }
    exp_str = "".join(superscripts.get(c, c) for c in str(exp_int))
    return f"{base} × 10{exp_str}"


def format_latex_num(val) -> str:
    """Format a float for LaTeX rendering — `\\times 10^{n}` for very small/large."""
    if val is None:
        return ""
    if val == 0:
        return "0"
    abs_val = abs(val)
    if 1e-5 <= abs_val < 1e6:
        s = f"{val:.6f}"
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        if not s or s == "0" or s == "-0":
            s = f"{val:.5g}"
        return s
    val_str = f"{val:.2e}"   # 3 sig figs in scientific notation
    base, exp = val_str.lower().split("e")
    base = base.rstrip("0").rstrip(".") if "." in base else base
    return f"{base} \\times 10^{{{int(exp)}}}"


def sanitize_latex(s: str) -> str:
    """Escape a unit name so KaTeX can render it."""
    if "^" in s:
        base, exp = s.split("^", 1)
        return f"\\text{{{base}}}^{{{exp}}}"
    return f"\\text{{{s}}}"
