---
type: function
parent: "[[DataLoader]]"
module: unitgps.engine.data
file: src/unitgps/engine/data.py
lines: "16-38"
status: current
generation: Claude
last_updated: 2026-05-20
tags: [engine, data-loading, reciprocals]
related:
  - "[[DataLoader]]"
  - "[[Reciprocal edges]]"
  - "[[Data Library schema]]"
  - "[[UnitGraph]]"
---

# DataLoader.load_data_library

Load the main Data Library xlsx, clean it, and synthesize reciprocal edges. This is the function that turns 3,635 raw rows into the ~6,000-row edge list the [[UnitGraph]] gets built from.

## Signature

```python
def load_data_library(self) -> pd.DataFrame
```

No explicit parameters — it reads `self.data_library_path`, set when the [[DataLoader]] was constructed. Output is a single pandas DataFrame containing the original rows plus synthesized reciprocals.

## Inputs

| Source | Type | Description |
|--------|------|-------------|
| `self.data_library_path` | `str` | Filesystem path to the xlsx (or .parquet). Set by `__init__`. Typically `Claude/data/Data Library, 2025-10-18, 1960-2023.xlsx`. |

The xlsx is read with `pd.read_excel` using its default sheet (the file has one sheet named `Sheet1`). If the path ends in `.parquet` it falls back to `pd.read_parquet` for faster reload during development.

## Output

A `pd.DataFrame` with these properties:

- **Rows:** roughly 1.66× the raw row count after reciprocal synthesis. For the canonical 2025-10-18 file: **3,635 raw → 6,056 combined**.
- **Columns:** the original 40 columns minus `Numerator Alias` and `Denominator Alias` (dropped because they're unused downstream) = **38 columns**.
- **No null `Value`:** rows where `Value` was NaN are dropped (those were placeholder rows in the source xlsx).

Every row is one directed edge ready for [[UnitGraph]] construction. See [[Data Library schema]] for column-by-column meaning.

## How it works (pseudocode)

```
1. Read the xlsx (or parquet) at self.data_library_path.
2. Drop the two unused alias columns.
3. Drop any row where Value is null.
4. Select rows whose Set is NOT Unit Conversion, Magnitude Adjustment, or Unit Conversions.
   These are the "reciprocate-me" rows: Emission Factors, Chemical Properties,
   and Global Warming Potentials.
5. Build a column-rename map that swaps every Numerator-* column with its
   Denominator-* counterpart (Numerator Dimension <-> Denominator Dimension,
   Numerator System <-> Denominator System, Numerator <-> Denominator).
6. Apply the rename, regenerate the human-readable Conversion string, and
   invert Value to 1/Value.
7. Concatenate the original DataFrame with the reciprocal DataFrame and reset
   the index.
8. Return the combined DataFrame.
```

The reasoning behind step 4's exclusion list lives in [[Reciprocal edges#Why exclude Unit Conversion and Magnitude Adjustment?]].

## Line-by-line

```python
if self.data_library_path.endswith('.parquet'):
    data = pd.read_parquet(self.data_library_path)
else:
    data = pd.read_excel(self.data_library_path)
```

*Why two readers?* During development it's useful to round-trip the loaded DataFrame through parquet for faster reload. Production always reads the xlsx.

> **Cleanup item.** The xlsx read doesn't pass `sheet_name='Sheet1'` — works today because the file only has one sheet, but fragile if a future revision adds an `About` tab. Tracked in [[architecture#4. Differences from Antigravity]].

```python
data = data.drop(columns=['Numerator Alias', 'Denominator Alias'], errors='ignore')
```

The xlsx ships with `Alias` columns intended for short display names (e.g. `kJ` could have alias `KJ`). They've never been used by the engine. `errors='ignore'` makes this safe if a future file format drops them.

```python
data = data.loc[~data['Value'].isnull()]
```

The xlsx has a handful of placeholder rows with header text in non-Value columns but no numeric Value. Those would crash downstream `1/Value` arithmetic, so they're dropped here.

```python
sets_to_exclude = ['Unit Conversion', 'Magnitude Adjustment', 'Unit Conversions']
reciprocal = data[~data['Set'].isin(sets_to_exclude)].copy()
```

The exclusion list includes both `Unit Conversion` (singular) and `Unit Conversions` (plural) for historical reasons — older Data Library files used the plural form. `.copy()` is needed because the next lines mutate `reciprocal` in place; without it we'd hit pandas' SettingWithCopyWarning.

```python
new_column_names = {}
for col in reciprocal.columns:
    if "Numerator" in col:
        new_column_names[col] = col.replace("Numerator", "Denominator")
    elif "Denominator" in col:
        new_column_names[col] = col.replace("Denominator", "Numerator")
```

Substring-replace, not exact match, so `Numerator Dimension` → `Denominator Dimension`, `Numerator System` → `Denominator System`, and the unprefixed `Numerator` / `Denominator` columns all swap together. The `elif` matters — without it, after `Numerator` had been renamed to `Denominator`, the same iteration would catch the new name and swap it back.

```python
reciprocal = reciprocal.rename(columns=new_column_names)
reciprocal['Conversion'] = reciprocal['Numerator'] + " per " + reciprocal['Denominator']
reciprocal['Value'] = 1 / reciprocal['Value']
```

After the rename, `reciprocal['Numerator']` holds what used to be the denominator and vice versa — that's why the `Conversion` string is rebuilt from scratch. `Value = 1/Value` is the actual reciprocation; all other columns (Agency, Data Year, GHG, Source-Chemical Type, etc.) carry over verbatim so filters work identically on forward and reverse edges.

```python
combined_data = pd.concat([data, reciprocal], ignore_index=True)
return combined_data
```

`ignore_index=True` gives the combined frame a fresh `0..n-1` index. Returned by value — caller (typically the cached engine loader) holds the only reference.

## Edge cases

- **A row whose Value rounds to zero.** `1/0` would raise; pandas leaves it as `inf`. If this happens, the reciprocal edge is mathematically junk. Today there are no such rows in the canonical file; if one ever appears, this would silently produce a broken edge. Worth adding a sanity check.
- **Whitespace-different `Set` values.** A row with `Set = ' Unit Conversion '` (with whitespace) would slip past the exclusion list and get reciprocated, producing duplicate edges. No such rows in the canonical file; not currently defended against.
- **Empty DataFrame after null-drop.** The `pd.concat` step still works (concatenating two empty frames returns an empty frame). The engine would build an empty graph; the UI would show no available units. Loud failure mode rather than silent corruption.

## Usage

```python
from unitgps.engine import DataLoader

loader = DataLoader(
    data_library_path='data/Data Library, 2025-10-18, 1960-2023.xlsx',
    gwp_file_path='data/IPCC GWPs AR4-AR6.xlsx',
)
df = loader.load_data_library()
print(df.shape)              # (6056, 38)
print(df['Set'].value_counts())
# Emission Factors        5330   ← 3024 raw + 2306 reciprocals
# Unit Conversion          294   ← never reciprocated
# Magnitude Adjustment     192   ← never reciprocated
# Chemical Properties      126   ← 63 raw + 63 reciprocals
# Global Warming Potent.   114   ← 62 raw + 52 reciprocals (some rows lacked the prerequisite columns)
```

The combined DataFrame is then passed to [[UnitGraph]] to build the actual graph.

## See also

[[DataLoader]] · [[Reciprocal edges]] · [[Data Library schema]] · [[UnitGraph]] · [[Glossary#Set]]
