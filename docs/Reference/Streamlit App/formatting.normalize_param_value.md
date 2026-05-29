---
type: function
module: streamlit_app.formatting
file: apps/streamlit_app/formatting.py
status: current
generation: Claude
last_updated: 2026-05-23
tags: [ui, formatting, parameters]
related:
  - "[[formatting]]"
  - "[[formatting.format_audit_date]]"
  - "[[Audit card hybrid layout]]"
---

# formatting.normalize_param_value

Tidy a parameter value for display in audit cards. Strips trailing `.0` from integer-valued floats so `Scope 1.0` reads as `Scope 1`, while leaving non-numeric strings (like `"v2.0"`) alone.

## Signature

```python
def normalize_param_value(value: Any) -> str
```

## Behaviour table

| Input | Output | Why |
|-------|--------|-----|
| `1.0` | `"1"` | Integer-valued float, strip `.0` |
| `1.5` | `"1.5"` | Non-integer float, preserve |
| `"1.0"` | `"1"` | Same rule via string parse |
| `"1"` | `"1"` | Already clean |
| `"Building"` | `"Building"` | Non-numeric, pass through |
| `"v2.0"` | `"v2.0"` | Numeric coercion fails on whole string, preserve original |
| `"2025"` | `"2025"` | Integer string, preserve as-is |
| `None` | `""` | Null becomes empty |
| `True` | `"Yes"` | Booleans render human-friendly |
| `False` | `"No"` | |
| `"  trim me  "` | `"trim me"` | Whitespace stripped |

## The coercion trick

```python
try:
    f = float(s)
    # Only collapse if the whole string is exactly the number
    if str(f) == s or f"{f:g}" == s:
        return str(int(f)) if f.is_integer() else f"{f:g}"
except ValueError:
    pass
return s
```

The `str(f) == s or f"{f:g}" == s` guard is what protects `"v2.0"` — `float("v2.0")` raises `ValueError`, and even if it didn't, the round-trip check would fail. Only pure-numeric strings collapse.

## Why this matters

Without normalization:
- Scope rows showed `Scope 1.0` everywhere — the `.0` reads as data noise
- `Data Year 2025.0` looked like a malformed year
- Booleans showed as `True`/`False` instead of `Yes`/`No`

Used throughout `_split_audit_params` and `_build_attribution` so every value rendered in an audit card passes through this cleanup.

## See also

[[formatting]] · [[formatting.format_audit_date]] · [[Audit card hybrid layout]]
