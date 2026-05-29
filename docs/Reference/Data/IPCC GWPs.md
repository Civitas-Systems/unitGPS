---
type: data
file: data/IPCC GWPs AR4-AR6.xlsx
sheet: Data
rows: 1209
columns_post_load: 4
status: current
generation: Claude
last_updated: 2026-05-21
tags: [data, schema, gwp, ipcc]
related:
  - "[[DataLoader.load_gwps]]"
  - "[[find_gwp]]"
  - "[[GHG emissions and GWP]]"
---

# IPCC GWPs (data file)

The canonical Global Warming Potential lookup. Used by [[find_gwp]] to weight each GHG mass into total CO₂e.

## File

- **Path:** `v0.5-Claude/data/IPCC GWPs AR4-AR6.xlsx`
- **Sheets:** `About` (descriptive, ignored) + `Data` (the actual table)
- **Rows on Data sheet:** 1,209
- **Columns (raw):** `Indicator`, `Long Chemical Name`, `GHG`, `GWP`

## Loaded shape (after `load_gwps`)

After [[DataLoader.load_gwps]] runs, the DataFrame has 4 columns:

| Column | Type | Example values |
|--------|------|----------------|
| `GHG` | str | `CO2`, `CH4`, `N2O`, `SF6`, `HFC-134a`, ... |
| `GWP` | float | `1.0`, `28.0`, `265.0`, ... |
| `Assessment Report` | str | `AR4`, `AR5`, `AR6` |
| `Time Horizon` | str | `20`, `100`, `500` |

The original `Indicator` column ships as `"AR5-100"` style strings; the loader splits on the dash. The `Long Chemical Name` column is dropped (redundant with `GHG`).

## Coverage

- **3 Assessment Reports:** AR4 (2007), AR5 (2014), AR6 (2021).
- **3 Time Horizons per AR:** 20-year, 100-year, 500-year.
- **~130 distinct GHGs per (AR × horizon)** — yields ~1,200 rows total.

## Reference values (common cases)

### CO₂, CH₄, N₂O — 100-year horizon

| Gas | AR4 | AR5 | AR6 |
|-----|-----|-----|-----|
| CO₂ | 1 | 1 | 1 |
| CH₄ | 25 | 28 | 27.9 |
| N₂O | 298 | 265 | 273 |

CO₂ is always exactly 1 by definition.

### CH₄ across all horizons (AR5)

| Horizon | GWP | Why it varies |
|---------|-----|--------------|
| 20 yr | 84 | Methane is intense short-term but decays in atmosphere |
| 100 yr | 28 | Standard reporting horizon for most regulators |
| 500 yr | 7 | Long-tail integration reduces methane's relative contribution |

The choice of horizon materially changes the math — see [[GHG emissions and GWP#GWP picking]].

### Fluorinated gases (selected, AR5/100)

| Gas | GWP | Notes |
|-----|-----|-------|
| SF₆ | 23,500 | Used in electrical switchgear |
| HFC-134a | 1,300 | Common refrigerant |
| HFC-23 | 12,400 | Industrial byproduct |
| NF₃ | 16,100 | Semiconductor manufacturing |

These get returned by [[find_gwp]] if requested but aren't routed by default — [[determine_ghg_emissions]] defaults to `('CO2', 'CH4', 'N2O')`.

## Today's usage by the engine

The engine uses ONLY:
- `AR5` / `100` (the hard-coded defaults in [[determine_ghg_emissions]])
- `CO2`, `CH4`, `N2O` (the default GHG list)

So out of ~1,200 rows, only 3 are routinely queried (one per default gas). The rest are loaded but unused — kept available for future UI selectors.

## Format quirks

- **`Time Horizon` is a string, not int.** Both the source xlsx and the post-load DataFrame keep it as a string. Callers must pass `'100'` not `100` to [[find_gwp]].
- **`Indicator` is normalized at load.** If a future GWP file ships pre-split, [[DataLoader.load_gwps]]'s `if '-' in str(gwps_data['Indicator'].iloc[0])` guard skips the split.

## See also

[[DataLoader.load_gwps]] · [[find_gwp]] · [[GHG emissions and GWP]] · [[determine_ghg_emissions]]
