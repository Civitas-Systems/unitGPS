---
type: module
module: streamlit_app.export
file: apps/streamlit_app/export.py
status: current
generation: Claude
last_updated: 2026-05-23
tags: [ui, export, serialization]
related:
  - "[[Portable results]]"
  - "[[renderers - conversion]]"
  - "[[renderers - emissions]]"
---

# export

JSON + Markdown serialization for Conversion and GHG results. Pure functions — no Streamlit dependency, fully testable.

## Public API

| Symbol | Purpose |
|--------|---------|
| `audit_to_json(result, source_unit, target_unit, starting_value, *, kind, extras=None) -> str` | Render an audit dict as a JSON string. `kind` is `"conversion"` or `"ghg"`. |
| `audit_to_markdown(result, source_unit, target_unit, starting_value, *, kind, extras=None) -> str` | Render the same audit as a human-readable Markdown report. |

Both helpers accept an optional `extras: dict` that gets folded into the output as a context section — used by the GHG export to record the active `gwp_report` and `gwp_horizon`.

## JSON envelope

```json
{
  "schema": "unitgps-audit/v1",
  "kind": "conversion",
  "generated_at": "2026-05-23T14:30:00Z",
  "source_unit": "J",
  "target_unit": "kg",
  "starting_value": 1.0,
  "conversion_factor": 9.83e-08,
  "ultimate_value": 9.83e-08,
  "route": ["J", "mmBTU", "kg"],
  "is_ambiguous": false,
  "audit_steps": [
    {
      "step_num": 1,
      "source": "J",
      "target": "mmBTU",
      "chosen_edge_idx": 0,
      "edges": [
        {"key": 0, "value": 9.48e-10, "set": "Unit Conversion",
         "parameters": {}, "source": {}}
      ]
    },
    ...
  ]
}
```

GHG envelopes have `per_gas: {CO2: {...}, CH4: {...}, N2O: {...}}` instead of the flat conversion fields, with each gas carrying `mass`, `gwp`, `co2e`, `error`, and its own `audit_steps`.

## Markdown structure

Conversion report:
- `# UnitGPS conversion audit` heading
- `## Result` — multiplier, route, ambiguity flag
- `## Audit` — per-step sub-section with multiplier, set, classification, chemical, attribution

GHG report:
- `# UnitGPS GHG emissions audit`
- `## Total` — total CO₂e with input
- `## Per-gas breakdown` — Markdown table with Mass / GWP / CO₂e / %
- `## Per-gas audit steps` — one sub-section per gas

## Why decoupled from Streamlit

- Smoke tests run without a Streamlit runtime
- The same serializers can power an HTMX or CLI variant
- File-name convention (`unitgps_conversion_J_to_kg_p1.json` etc.) lives in the renderer that calls download_button, not in the serializer

## See also

[[Portable results]] · [[renderers - conversion]] · [[renderers - emissions]]
