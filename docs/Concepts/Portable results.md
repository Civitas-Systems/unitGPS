---
type: concept
status: current
generation: Claude
last_updated: 2026-05-23
tags: [concept, export, url-state, portability]
related:
  - "[[export]]"
  - "[[url_state]]"
  - "[[app]]"
---

# Portable results

How a calculation gets out of the app — for sharing, archival, or resumption.

## Two complementary mechanisms

| Mechanism | Captures | Use case |
|-----------|----------|----------|
| **Export** (`⬇ JSON audit` / `⬇ Markdown report` buttons) | The *output* of a calculation — every audit step, edge value, source attribution, total CO₂e | Paste into a doc, email, audit log; archive for compliance |
| **Bookmark URL** (`🔗 Share / bookmark` popover) | The *configuration* — source/target/units/modules/filters/theme | Repeat the same calculation later; share a scenario with a colleague |

The two are complementary: the URL lets someone re-run your configuration with fresh data; the export lets them see the exact numbers you saw.

## Export format

JSON is lossless — every audit step including all parallel-edge alternatives, every source attribution field, the `chosen_edge_idx` used. The JSON envelope:

```json
{
  "schema": "unitgps-audit/v1",
  "kind": "conversion" | "ghg",
  "generated_at": "2026-05-23T14:30:00Z",
  "source_unit": "J",
  "target_unit": "kg",
  "starting_value": 1.0,
  ...
}
```

Markdown is human-readable — formatted with headers, a result summary, and per-step bullet blocks. The Markdown report for a GHG calculation includes the per-gas summary table directly. Suitable for pasting into Notion / Obsidian / GitHub issues / email.

## URL state encoding

Only ``configuration`` state round-trips through the URL, not transient state like `_edge_picks` (which is per-result and not bookmark-shareable) or numeric results (which the engine recomputes on URL load).

Default values are *stripped* from the URL — a clean visit produces a clean URL. The `cb_mod_*` checkboxes default to `True` for all four modules; only modules turned *off* show up in the URL. This keeps bookmarks short.

Filter selections (multi-select columns like Chemical Type, Agency, etc.) encode as comma-separated values under `f_<column_name>` keys. Example URL for a configured calculation:

```
https://unitgps.app?theme=Obsidian+Light&source_unit_sb=J&target_unit_sb=kg
                  &gwp_report=AR6&gwp_horizon=100
                  &f_source_chemical_type=Anthracite%2CBituminous
                  &f_agency=EPA
```

## Implementation modules

- [[export]] — JSON + Markdown serializers, pure functions, fully testable without a Streamlit runtime
- [[url_state]] — hydrate / sync between `st.query_params` and `st.session_state`, called early/late in `app.py`

## See also

[[export]] · [[url_state]] · [[app]]
