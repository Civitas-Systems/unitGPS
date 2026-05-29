---
type: function
module: streamlit_app.formatting
file: apps/streamlit_app/formatting.py
status: current
generation: Claude
last_updated: 2026-05-23
tags: [ui, formatting, dates]
related:
  - "[[formatting]]"
  - "[[formatting.normalize_param_value]]"
  - "[[Audit card hybrid layout]]"
---

# formatting.format_audit_date

Render a date as `YYYY-MMM-DD` (e.g. `2025-Aug-22`) regardless of input format. The single source of truth for date display anywhere in the audit cards' attribution lines.

## Signature

```python
def format_audit_date(value: Any) -> str
```

## Inputs

Accepts:
- `datetime` / `date` objects
- ISO-ish strings: `"2025-08-22"`, `"2025/08/22"`, `"2025-08-22T14:30:00"`, `"2025-08-22 14:30:00"`
- US/EU date variants: `"08/22/2025"`, `"22/08/2025"`
- `None` or empty string → returns `""`
- Anything unparseable → returns the original string unchanged (graceful degradation, never blanks data)

## Output format

```
{year:04d}-{month_abbr}-{day:02d}
```

Where `month_abbr` is one of `Jan`, `Feb`, `Mar`, `Apr`, `May`, `Jun`, `Jul`, `Aug`, `Sep`, `Oct`, `Nov`, `Dec`.

Examples:
- `format_audit_date("2025-08-22")` → `"2025-Aug-22"`
- `format_audit_date("2025-01-25")` → `"2025-Jan-25"`
- `format_audit_date("08/22/2025")` → `"2025-Aug-22"`
- `format_audit_date(None)` → `""`
- `format_audit_date("not a date")` → `"not a date"`

## Why this format

`YYYY-MMM-DD` was Dave's explicit ask. The three-letter month removes the US/EU ambiguity that pure-numeric `MM/DD/YYYY` vs `DD/MM/YYYY` carries — `Aug` reads correctly to readers anywhere. Year-first sorts lexicographically and makes the four-digit year unmissable.

## See also

[[formatting]] · [[formatting.normalize_param_value]] · [[Audit card hybrid layout]]
