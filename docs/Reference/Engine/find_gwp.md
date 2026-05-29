---
type: function
module: unitgps.engine.emissions
file: src/unitgps/engine/emissions.py
lines: "19-43"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [engine, gwp, lookup]
related:
  - "[[DataLoader.load_gwps]]"
  - "[[determine_ghg_emissions]]"
  - "[[GHG emissions and GWP]]"
  - "[[IPCC GWPs]]"
---

# find_gwp

Look up a Global Warming Potential value for one gas at one IPCC report × time horizon combination. Pure DataFrame query — no graph traversal, no math beyond returning the looked-up number.

## Signature

```python
def find_gwp(
    gwps_data: pd.DataFrame,
    ghg: str,
    assessment_report: str = 'AR5',
    time_horizon: str = '100',
) -> float | None
```

## Inputs

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `gwps_data` | `pd.DataFrame` | — | The GWP table from [[DataLoader.load_gwps]]. Must have `GHG`, `Assessment Report`, `Time Horizon`, `GWP` columns. |
| `ghg` | `str` | — | The greenhouse gas (`'CO2'`, `'CH4'`, `'N2O'`, etc.). Case-sensitive. |
| `assessment_report` | `str` | `'AR5'` | IPCC report cycle (`'AR4'`, `'AR5'`, `'AR6'`). |
| `time_horizon` | `str` | `'100'` | Years (`'20'`, `'100'`, `'500'`). Note: string, not int. |

## Output

A `float` with the GWP value, or `None` if no row matches the filter.

| Result | Meaning |
|--------|---------|
| `1.0` | CO₂ (always, by definition — also returned as fallback if CO₂ row is missing) |
| `28.0` | CH₄ at AR5, 100-year |
| `265.0` | N₂O at AR5, 100-year |
| `None` | No matching row (unknown gas, unknown AR, unknown horizon) |

See [[GHG emissions and GWP#GWP picking]] for a reference table of common values.

## How it works (pseudocode)

```
try:
    row = gwps_data where GHG matches AND Assessment Report matches AND Time Horizon matches
    if row is empty:
        if ghg == 'CO2': return 1.0   # CO2 is the reference gas
        return None
    return float(row.GWP.values[0])
except any exception:
    return None
```

## Line-by-line

```python
try:
    gwp_row = gwps_data.loc[
        (gwps_data['GHG'] == ghg)
        & (gwps_data['Assessment Report'] == assessment_report)
        & (gwps_data['Time Horizon'] == time_horizon)
    ]
```

Boolean-mask filtering. The three conditions are ANDed; the row count is normally 0 or 1.

```python
    if gwp_row.empty:
        if ghg == 'CO2': return 1.0
        return None
```

The CO₂ fallback exists because CO₂ has GWP = 1 by definition (it's the reference). The fallback covers the unlikely case where someone's GWP file doesn't ship a row for CO₂.

```python
    return float(gwp_row['GWP'].values[0])
```

`.values[0]` grabs the first (only) match. The `float()` cast normalizes whatever pandas returned (could be `numpy.float64` or similar) into a plain Python float.

```python
except Exception:
    return None
```

Belt-and-braces fallback. Catches malformed `gwps_data` (missing columns, weird types, etc.) and turns them into a clean `None` return instead of crashing the caller. This is one of the few places in the engine that swallows exceptions broadly.

## Why are AR and horizon strings, not ints?

Because [[DataLoader.load_gwps]] reads them as strings — they're split out of an `Indicator` column that starts as text (`"AR5-100"`). Keeping them as strings end-to-end avoids any cast mismatch. The downside is that calling `find_gwp(gwps, 'CH4', 'AR5', 100)` (int 100) returns `None` because `'100' != 100`.

## Edge cases

- **Empty `gwps_data`** → empty row → returns `None` (or `1.0` for CO₂).
- **Multiple rows for the same `(GHG, AR, horizon)`** → `.values[0]` takes the first one. Doesn't happen with the canonical file.
- **Wrong column names in `gwps_data`** → caught by the broad `except Exception` → `None`.

## Usage

```python
gwps = loader.load_gwps()
print(find_gwp(gwps, 'CH4'))                           # 28.0 (AR5 / 100 defaults)
print(find_gwp(gwps, 'CH4', 'AR6', '20'))              # ~82
print(find_gwp(gwps, 'N2O', 'AR5'))                    # 265.0
print(find_gwp(gwps, 'SF6'))                           # 23500.0
print(find_gwp(gwps, 'UNKNOWN_GAS'))                   # None
print(find_gwp(gwps, 'CO2'))                           # 1.0
```

[[determine_ghg_emissions]] calls this once per gas to weight each gas's mass into total CO₂e.

## See also

[[DataLoader.load_gwps]] · [[determine_ghg_emissions]] · [[GHG emissions and GWP]] · [[IPCC GWPs]]
