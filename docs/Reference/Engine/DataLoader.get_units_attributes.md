---
type: function
parent: "[[DataLoader]]"
module: unitgps.engine.data
file: src/unitgps/engine/data.py
lines: "40-75"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [engine, data-loading, node-attributes]
related:
  - "[[DataLoader]]"
  - "[[UnitGraph]]"
  - "[[Unit graph]]"
  - "[[Glossary#Dimension]]"
---

# DataLoader.get_units_attributes

Build the `{unit_name: {Unit Dimension, Unit System, Color}}` dict that [[UnitGraph]] uses to decorate every node. Called once during engine setup, never during a query.

## Signature

```python
def get_units_attributes(self, df: pd.DataFrame) -> dict
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `df` | `pd.DataFrame` | The combined Data Library DataFrame (post-reciprocals). Must have `Numerator`, `Numerator Dimension`, `Numerator System`, `Denominator`, `Denominator Dimension`, `Denominator System` columns. |

Typically passed the output of [[DataLoader.load_data_library]].

## Output

A `dict` mapping each unit name to a sub-dict of metadata:

```python
{
    'J':     {'Unit Dimension': 'Energy',    'Unit System': 'SI',       'Color': 'pink'},
    'kg':    {'Unit Dimension': 'Weight',    'Unit System': 'SI',       'Color': 'purple'},
    'mmBTU': {'Unit Dimension': 'Energy',    'Unit System': 'imperial', 'Color': 'pink'},
    ...
}
```

For the canonical Data Library file this dict has roughly 200 entries. [[UnitGraph]] uses these as node attributes; the Streamlit UI uses them for dimension grouping in the source/target selectors.

## How it works (pseudocode)

```
1. Project two slices of df:
   - units_num: (Numerator, Numerator Dimension, Numerator System) columns,
     renamed to (Unit, Dimension, System)
   - units_den: same projection on the Denominator side
2. Concat them, drop duplicates, drop rows with null Unit
3. For each remaining row:
   - Look up the color for its Dimension in DIMENSION_COLORS
   - Build {'Unit Dimension', 'Unit System', 'Color'} dict
4. Return as a dict keyed by Unit name
```

## Line-by-line

```python
units_num = df[['Numerator', 'Numerator Dimension', 'Numerator System']].rename(
    columns={
        'Numerator': 'Unit',
        'Numerator Dimension': 'Dimension',
        'Numerator System': 'System',
    }
)
units_den = df[['Denominator', 'Denominator Dimension', 'Denominator System']].rename(
    columns={
        'Denominator': 'Unit',
        'Denominator Dimension': 'Dimension',
        'Denominator System': 'System',
    }
)
units_all = pd.concat([units_num, units_den]).drop_duplicates().dropna(subset=['Unit'])
```

A unit is something that appears as either a numerator OR a denominator. Collecting both sides ensures we don't miss units that only show up in one position.

```python
dimension_colors = {
    'Time': 'black',  'Area': 'blue',     'Length': 'green',
    'Energy': 'pink', 'Volume': 'orange', 'Weight': 'purple',
    'Power': 'brown', 'Logistics': 'cyan',
}
```

Inline color map. Unknown dimensions fall through to `'grey'` below. These colors are intended for future graph visualization — the Streamlit UI doesn't currently render the unit graph, but the data is ready when it does.

```python
attr_dict = {}
for _, row in units_all.iterrows():
    dim = row['Dimension']
    sys_name = row['System']
    color = dimension_colors.get(dim, 'grey')
    attr_dict[row['Unit']] = {
        'Unit Dimension': dim,
        'Unit System': sys_name,
        'Color': color,
    }
return attr_dict
```

`iterrows()` is slow for big DataFrames but units_all is only ~200 rows, so it's fine. If the source data grows by orders of magnitude, switch to a vectorized construction via `to_dict('records')`.

## Edge cases

- **A unit with conflicting dimensions on numerator vs. denominator sides.** Last-write-wins (whichever row pandas iterates last wins). In practice this doesn't happen in the canonical data — a unit always has the same dimension.
- **A unit appearing only in the GWP rows.** Not affected — GWP rows have GHG abbreviations like `CO2` as numerators and `CO2` as denominators (the ratio is unitless), so they don't introduce new graph nodes.
- **Unknown dimensions** silently get `'grey'`. Loud failure here would surface upstream data issues; current behavior masks them.

## Usage

```python
node_attrs = loader.get_units_attributes(df)
print(node_attrs['kWh'])
# {'Unit Dimension': 'Energy', 'Unit System': 'SI', 'Color': 'pink'}

# Passed straight into UnitGraph:
graph = UnitGraph(df, node_attrs)
```

## See also

[[DataLoader]] · [[UnitGraph]] · [[Unit graph]] · [[Glossary#Dimension]]
