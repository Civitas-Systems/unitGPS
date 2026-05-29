"""Result serialization for export.

Two output formats:

- :func:`audit_to_json` — full structured JSON of a Conversion or GHG result.
  Lossless, includes every audit step, every parallel-edge alternative, every
  source attribution. Suitable for archival, downstream tooling, audit logs.

- :func:`audit_to_markdown` — human-readable Markdown audit report. Renders
  the route, the chosen edge per step, the source attribution, and the totals.
  Suitable for pasting into a doc, email, or compliance write-up.

Both helpers operate on the audit dicts returned by ``determine_conversion``
and ``determine_ghg_emissions`` — no Streamlit dependency, fully testable.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from unitgps.engine import format_sig_figs

from .formatting import format_audit_date, normalize_param_value


# --------------------------------------------------------------------------- #
# JSON serialization                                                           #
# --------------------------------------------------------------------------- #


def _clean_step(step: dict) -> dict:
    """Strip non-JSON-serializable fields and normalize floats."""
    edges_out: list[dict] = []
    for edge in step.get("edges", []) or []:
        edges_out.append({
            "key": edge.get("key"),
            "value": edge.get("value"),
            "set": edge.get("set"),
            "parameters": edge.get("parameters", {}) or {},
            "source": edge.get("source", {}) or {},
        })
    return {
        "step_num": step.get("step_num"),
        "source": step.get("source"),
        "target": step.get("target"),
        "chosen_edge_idx": step.get("chosen_edge_idx", 0),
        "edges": edges_out,
    }


def audit_to_json(
    result: dict,
    source_unit: str,
    target_unit: str,
    starting_value: float,
    *,
    kind: str = "conversion",
    extras: dict | None = None,
) -> str:
    """Render a result dict as a JSON string.

    ``kind`` is either ``"conversion"`` (audit dict from determine_conversion)
    or ``"ghg"`` (full GHG result from determine_ghg_emissions).
    """
    envelope: dict[str, Any] = {
        "schema": "unitgps-audit/v1",
        "kind": kind,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source_unit": source_unit,
        "target_unit": target_unit,
        "starting_value": starting_value,
    }
    if extras:
        envelope["context"] = extras

    if kind == "conversion":
        envelope["conversion_factor"] = result.get("conversion_factor")
        envelope["ultimate_value"] = result.get("ultimate_value")
        envelope["route"] = result.get("route")
        envelope["is_ambiguous"] = result.get("is_ambiguous", False)
        envelope["audit_steps"] = [_clean_step(s) for s in result.get("audit_steps", []) or []]
    elif kind == "ghg":
        envelope["total_co2e"] = result.get("total_co2e")
        envelope["valid_calc"] = result.get("valid_calc", False)
        per_gas: dict[str, Any] = {}
        for ghg, details in (result.get("results") or {}).items():
            audit = details.get("Audit") or {}
            per_gas[ghg] = {
                "mass": details.get("Mass"),
                "gwp": details.get("GWP"),
                "co2e": details.get("CO2e"),
                "error": details.get("Error"),
                "audit_steps": [_clean_step(s) for s in audit.get("audit_steps", []) or []],
            }
        envelope["per_gas"] = per_gas
    else:
        raise ValueError(f"Unknown kind: {kind!r} (expected 'conversion' or 'ghg')")

    return json.dumps(envelope, indent=2, default=str)


# --------------------------------------------------------------------------- #
# Markdown report                                                              #
# --------------------------------------------------------------------------- #


def _md_attribution(sources: dict, params: dict) -> str:
    """Build a single inline attribution line for a Markdown step."""
    def get(k: str):
        v = (sources or {}).get(k)
        if v:
            return v
        return (params or {}).get(k)

    agency = get("Agency")
    dataset = get("Dataset")
    version = get("Version") or get("Data Year")
    released = get("Release Date")
    updated = get("Updated")

    parts: list[str] = []
    if agency:
        parts.append(f"**{agency}**")
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
    return " · ".join(parts) if parts else "—"


def _md_step(step: dict) -> list[str]:
    """Render one step as Markdown bullet block. Returns list of lines."""
    chosen = step.get("chosen_edge_idx", 0)
    edges = step.get("edges") or []
    edge = edges[chosen] if edges else {}
    val = edge.get("value", 1.0)
    set_name = edge.get("set", "?")
    n_alts = len(edges)
    alt_note = f" *(picked #{chosen + 1} of {n_alts})*" if n_alts > 1 else ""

    lines = [
        f"### Step {step.get('step_num')}: `{step.get('source')}` → `{step.get('target')}`",
        "",
        f"- **Multiplier:** `× {format_sig_figs(val, 6)}`",
        f"- **Set:** {set_name}{alt_note}",
    ]

    params = edge.get("parameters") or {}
    sources = edge.get("source") or {}
    # Classification + chemical params (skip source-keys; they're in attribution)
    SOURCE_KEYS = {"Agency", "Dataset", "Data Year", "Version", "Updated", "Release Date"}
    classification = []
    chemical = []
    src_chemical = []
    for k, v in params.items():
        if k in SOURCE_KEYS or v is None or v == "":
            continue
        if k.startswith("Source-") or k.startswith("Source "):
            src_chemical.append((k, normalize_param_value(v)))
        elif "Chemical" in k:
            chemical.append((k, normalize_param_value(v)))
        else:
            classification.append((k, normalize_param_value(v)))

    if classification:
        lines.append("- **Classification:** " + ", ".join(f"{k}=`{v}`" for k, v in classification))
    if chemical:
        # Pair with source-chemical when they differ
        src_dict = dict(src_chemical)
        items = []
        for i, (k, v) in enumerate(chemical):
            # Try to find a paired src key by encounter order
            src_v = list(src_dict.values())[i] if i < len(src_dict) else None
            if src_v and src_v != v:
                items.append(f"{k}=`{v}` *(source: `{src_v}`)*")
            else:
                items.append(f"{k}=`{v}`")
        lines.append("- **Chemical:** " + ", ".join(items))
    attr = _md_attribution(sources, params)
    if attr and attr != "—":
        lines.append(f"- **Attribution:** {attr}")
    lines.append("")
    return lines


def audit_to_markdown(
    result: dict,
    source_unit: str,
    target_unit: str,
    starting_value: float,
    *,
    kind: str = "conversion",
    extras: dict | None = None,
) -> str:
    """Render a result as a Markdown audit report.

    Suitable for pasting into a doc / email / audit log without modification.
    """
    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    lines: list[str] = []

    if kind == "conversion":
        factor = result.get("conversion_factor", 1.0)
        ultimate = result.get("ultimate_value", starting_value * factor)
        route = result.get("route") or []
        route_str = " → ".join(f"`{u}`" for u in route)
        lines += [
            f"# UnitGPS conversion audit",
            "",
            f"*Generated {timestamp}*",
            "",
            f"## Result",
            "",
            f"**{format_sig_figs(starting_value, 6)} {source_unit}** → "
            f"**{format_sig_figs(ultimate, 6)} {target_unit}**",
            "",
            f"- Multiplier: `× {format_sig_figs(factor, 6)}`",
            f"- Route: {route_str}",
            f"- Ambiguous path: {'yes' if result.get('is_ambiguous') else 'no'}",
            "",
            "## Audit",
            "",
        ]
        for step in result.get("audit_steps") or []:
            lines += _md_step(step)
    elif kind == "ghg":
        total = result.get("total_co2e", 0.0)
        per_gas = result.get("results") or {}
        lines += [
            f"# UnitGPS GHG emissions audit",
            "",
            f"*Generated {timestamp}*",
            "",
            f"## Total",
            "",
            f"**{format_sig_figs(total, 6)} {target_unit} CO₂e** from "
            f"{format_sig_figs(starting_value, 6)} {source_unit}",
            "",
            "## Per-gas breakdown",
            "",
            "| GHG | Mass | GWP | CO₂e | % of total |",
            "|-----|------|-----|------|-----------|",
        ]
        for ghg, details in per_gas.items():
            mass = details.get("Mass")
            gwp = details.get("GWP")
            co2e = details.get("CO2e")
            pct = (co2e / total * 100) if (total and co2e) else 0
            mass_s = format_sig_figs(mass, 5) if mass is not None else "—"
            gwp_s = str(int(gwp)) if (gwp is not None and float(gwp).is_integer()) else (f"{gwp:g}" if gwp is not None else "—")
            co2e_s = format_sig_figs(co2e, 5) if co2e is not None else "—"
            lines.append(
                f"| {ghg} | {mass_s} {target_unit} | {gwp_s} | {co2e_s} {target_unit} | {pct:.2f}% |"
            )
        lines += ["", "## Per-gas audit steps", ""]
        for ghg, details in per_gas.items():
            audit = details.get("Audit") or {}
            steps = audit.get("audit_steps") or []
            if not steps:
                lines.append(f"### {ghg} — no path")
                lines.append("")
                continue
            lines.append(f"### {ghg} pathway")
            lines.append("")
            for step in steps:
                lines += _md_step(step)
    else:
        raise ValueError(f"Unknown kind: {kind!r} (expected 'conversion' or 'ghg')")

    if extras:
        lines += [
            "## Context",
            "",
        ]
        for k, v in extras.items():
            lines.append(f"- **{k}:** `{v}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
