---
type: function
parent: "[[formatting]]"
module: streamlit_app.formatting
file: apps/streamlit_app/formatting.py
lines: "47-65"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, formatting, latex]
related:
  - "[[formatting]]"
  - "[[formatting.format_html_num]]"
  - "`formatting.build_math_latex` *(removed)*"
---

# formatting.format_latex_num

Format a float as a LaTeX-safe number string, using `\times 10^{n}` notation for very small or very large values.

## Signature

```python
def format_latex_num(val) -> str
```

## Inputs / Outputs

| Input | Output |
|-------|--------|
| `None` | `""` |
| `0` | `"0"` |
| `1e-5 ≤ |val| < 1e6` | Plain decimal e.g. `"1234.5"` |
| Outside | LaTeX scientific e.g. `"1.234 \\times 10^{8}"` |

## How it works

```python
def format_latex_num(val):
    if val is None:
        return ''
    if val == 0:
        return '0'
    abs_val = abs(val)
    if 1e-5 <= abs_val < 1e6:
        s = f'{val:.6f}'
        if '.' in s:
            s = s.rstrip('0').rstrip('.')
        if not s or s == '0' or s == '-0':
            s = f'{val:.5g}'
        return s
    val_str = f'{val:.4e}'
    base, exp = val_str.lower().split('e')
    base = base.rstrip('0').rstrip('.') if '.' in base else base
    return f'{base} \\times 10^{{{int(exp)}}}'
```

The plain-decimal branch is identical to [[formatting.format_html_num]]. The scientific branch differs only in the output style — `\times 10^{8}` for LaTeX vs. `× 10⁸` Unicode for HTML.

## Why a separate function from format_html_num?

LaTeX rendering (via Streamlit's `st.latex` → KaTeX) needs the `\times` macro and `^{...}` syntax. HTML rendering benefits from Unicode superscripts. Same logic, different output dialects.

## Usage

```python
# Inside renderers/emissions.py, building the GHG LaTeX equation:
co2_m = format_latex_num(res['results']['CO2']['Mass'])
ch4_m = format_latex_num(res['results']['CH4']['Mass'])
latex_eq = f"... &= {co2_m} + ({ch4_m} \\times {ch4_g}) + ..."
```

## See also

[[formatting]] · [[formatting.format_html_num]] · `formatting.build_math_latex` *(removed)*
