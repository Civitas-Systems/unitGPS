---
type: reference
status: current
generation: Claude
last_updated: 2026-05-30
tags: [examples, scenarios]
---

# Scenario gallery

Configurations UnitGPS handles — each is just a choice of source, target, modules, and
filters.

| # | Goal | Source → Target | Key settings |
|---|------|-----------------|--------------|
| 1 | Fuel combustion footprint | `mmBTU` anthracite → `kg` | GHG on; Chemical Type = Anthracite. See [[Tutorial — worked example]]. |
| 2 | Purchased electricity | `MWh` → `kg` | GHG on; Location → eGRID region (regional grid factor) |
| 3 | Fuel energy ↔ mass | `mmBTU` → `kg` | Fuel Properties on (heat content) |
| 4 | Pure unit conversion | `GJ` → `kWh`, `ton` → `kg` | GHG off; just Unit Conversions |
| 5 | Most-recent data only | any | Temporal Scope → Most Recent per Path |
| 6 | Compare GWP vintages | same fuel | switch Assessment Report AR4 / AR5 / AR6 |
| 7 | Specific agency / year | any | Data Source → Agency; Temporal Scope → Specific Years |

Each result is exportable (JSON audit / Markdown) and bookmarkable (Share link).
