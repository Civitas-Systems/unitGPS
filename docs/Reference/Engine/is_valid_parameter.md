---
type: function
module: unitgps.engine.calculate
file: src/unitgps/engine/calculate.py
lines: "35-46"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [engine, validation, utility]
related:
  - "[[format_sig_figs]]"
  - "[[calculate_conversion_factor]]"
---

# is_valid_parameter

Return `True` if a value is "real enough" to show in an audit report. Filters out `None`, NaN, empty strings, whitespace strings, and the literal string `"nan"`. Used by [[calculate_conversion_factor]] to decide which edge attributes are worth including in the audit.

## Signature

```python
def is_valid_parameter(value) -> bool
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `value` | Any | Cell value from a DataFrame edge attribute. |

## Output

`True` if the value should be shown, `False` if it should be filtered out.

| Input | Returns |
|-------|---------|
| `None` | `False` |
| `float('nan')` | `False` |
| `''`, `'   '` | `False` |
| `'nan'`, `'NaN'`, `'NAN'` | `False` |
| `0`, `0.0` | `True` (zero is a real value) |
| `'foo'`, `42`, `3.14` | `True` |

## How it works

```python
def is_valid_parameter(value):
    if value is None:
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    if isinstance(value, str):
        if not value.strip():
            return False
        if value.lower() == 'nan':
            return False
    return True
```

Three guards, in order:
1. **`None`** — explicit early return.
2. **Float NaN** — `math.isnan` to catch real NaN values (which `pd.read_excel` produces for empty cells).
3. **String checks** — empty, whitespace-only, or literal `"nan"` (case-insensitive). Pandas sometimes stringifies NaN before it reaches us.

## Why the string `"nan"` check?

Because pandas occasionally yields the literal string `"nan"` instead of a float NaN, especially after a column that mixes strings and floats gets read. Without this guard, "nan" would slip through and show up in audit reports as if it were a legitimate parameter value.

## Why is `0` valid?

A Data Year of `0` is unusual but not invalid (it could legitimately mean year 0 CE if anyone ever needed it). More importantly, an emission factor `Value` of exactly 0 is meaningful (means "this fuel emits zero of this gas"). The function only filters values that represent *missing-ness*, not zeros.

## Usage

```python
# Inside calculate_conversion_factor, when building audit step details:
source_params = {
    k: edge_data[k]
    for k in source_keys
    if k in edge_data and is_valid_parameter(edge_data[k])
}
```

This is the typical pattern: dict-comprehension filter on column values to decide what's worth including.

## Examples

```python
is_valid_parameter(None)              # False
is_valid_parameter(float('nan'))      # False
is_valid_parameter('')                # False
is_valid_parameter('   ')             # False
is_valid_parameter('nan')             # False
is_valid_parameter('NaN')             # False (case-insensitive)
is_valid_parameter(0)                 # True  (zero is real)
is_valid_parameter(0.0)               # True
is_valid_parameter('EPA')             # True
is_valid_parameter(2023)              # True
```

## See also

[[format_sig_figs]] · [[calculate_conversion_factor]]
