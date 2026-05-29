---
type: function
parent: "[[DataLoader]]"
module: unitgps.engine.data
file: src/unitgps/engine/data.py
lines: "77-95"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [engine, data-loading, gwp]
related:
  - "[[DataLoader]]"
  - "[[find_gwp]]"
  - "[[GHG emissions and GWP]]"
  - "[[IPCC GWPs]]"
---

# DataLoader.load_gwps

Load the IPCC GWP xlsx and split its `Indicator` column into separate `Assessment Report` and `Time Horizon` columns. The output is the lookup table [[find_gwp]] queries every time it needs a GWP value.

## Signature

```python
def load_gwps(self) -> pd.DataFrame
```

No explicit parameters — reads `self.gwp_file_path`.

## Inputs

| Source | Type | Description |
|--------|------|-------------|
| `self.gwp_file_path` | `str` | Path to `IPCC GWPs AR4-AR6.xlsx`. |

The xlsx has two sheets — `About` (a description, ignored) and `Data` (the actual table, ~1,209 rows). This function reads only the `Data` sheet.

## Output

A `pd.DataFrame` with columns:

| Column | Type | Example |
|--------|------|---------|
| `GHG` | str | `CO2`, `CH4`, `N2O`, `SF6`, ... |
| `GWP` | float | `1.0`, `28.0`, `265.0`, ... |
| `Assessment Report` | str | `AR4`, `AR5`, `AR6` |
| `Time Horizon` | str | `20`, `100`, `500` |

The source xlsx ships these as a single `Indicator` column like `"AR5-100"`; this function splits on the dash. The `Long Chemical Name` column is dropped because it's redundant with `GHG`.

For the canonical AR4–AR6 file: 3 reports × 3 horizons × ~130 gases = ~1,200 rows.

## How it works (pseudocode)

```
1. Read the 'Data' sheet of the GWP xlsx.
2. If Indicator looks like 'AR5-100':
   - Split it on '-' into two new columns: Assessment Report, Time Horizon
   - Drop the Indicator column and the Long Chemical Name column
3. Return the modified DataFrame.
```

## Line-by-line

```python
gwps_data = pd.read_excel(self.gwp_file_path, sheet_name='Data')
```

Explicit `sheet_name='Data'` — unlike [[DataLoader.load_data_library]], which relies on the file having only one sheet, this call has to skip the `About` sheet.

```python
if 'Indicator' in gwps_data.columns and '-' in str(gwps_data['Indicator'].iloc[0]):
    gwps_data[['Assessment Report', 'Time Horizon']] = gwps_data['Indicator'].str.split('-', expand=True)
    gwps_data = gwps_data.drop(columns=['Indicator', 'Long Chemical Name'], errors='ignore')
```

The guard handles two formats — newer files that ship pre-split, and the canonical file that uses the combined `Indicator` form. Checking the first row's content is a heuristic; if the first row happens to lack a dash but later rows have one, this would silently skip the split. In practice the file is uniform.

`str.split('-', expand=True)` returns a two-column DataFrame which gets multi-assigned to two new columns in one statement.

`errors='ignore'` on the drop allows the same code to work with files that don't ship `Long Chemical Name`.

```python
return gwps_data
```

## Edge cases

- **Indicator format like `"AR5-100yr"`** — split-on-dash would give `Time Horizon='100yr'` not `'100'`. Then [[find_gwp]] queries like `time_horizon='100'` would miss. Current canonical file uses plain numerics; format changes would need code update.
- **Empty Data sheet** — returns an empty DataFrame with the right columns. [[find_gwp]] gracefully returns `None` for missing lookups.
- **Multiple GWP entries for the same (GHG, AR, horizon)** — [[find_gwp]] takes `.values[0]`, so the first match wins. Not an issue with the canonical file.

## Usage

```python
gwps = loader.load_gwps()

# Direct lookup pattern (or use find_gwp() wrapper)
ch4_ar5_100 = gwps[
    (gwps['GHG'] == 'CH4')
    & (gwps['Assessment Report'] == 'AR5')
    & (gwps['Time Horizon'] == '100')
]
print(float(ch4_ar5_100['GWP'].iloc[0]))   # 28.0
```

In practice you don't query this DataFrame directly — [[find_gwp]] is the proper accessor and handles the error cases.

## See also

[[DataLoader]] · [[find_gwp]] · [[GHG emissions and GWP]] · [[IPCC GWPs]]
