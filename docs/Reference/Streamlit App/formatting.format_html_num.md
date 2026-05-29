---
type: function
parent: "[[formatting]]"
module: streamlit_app.formatting
file: apps/streamlit_app/formatting.py
lines: "20-44"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, formatting, html]
related:
  - "[[formatting]]"
  - "[[formatting.format_latex_num]]"
  - "[[format_sig_figs]]"
---

# formatting.format_html_num

Format a float for HTML display using Unicode superscript characters for the exponent (so HTML doesn't need a `<sup>` tag).

## Signature

```python
def format_html_num(val) -> str
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `val` | float or None | Number to format. None → `"N/A"`. |

## Output

A `str` formatted in one of three ways:

| Input range | Output style | Example |
|-------------|--------------|---------|
| `None` | `"N/A"` | — |
| `val == 0` | `"0"` | — |
| `1e-5 ≤ |val| < 1e6` | Plain decimal, trailing zeros stripped | `format_html_num(1234.5)` → `"1234.5"` |
| Outside that range | `<base> × 10<superscript>` | `format_html_num(1.23e8)` → `"1.23 × 10⁸"` |

The Unicode superscript map handles digits 0-9 plus the minus sign.

## How it works

```python
def format_html_num(val):
    if val is None:
        return 'N/A'
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
    s = f'{val:.4e}'
    base, exp = s.split('e')
    base = base.rstrip('0').rstrip('.') if '.' in base else base
    exp_int = int(exp)
    superscripts = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
                    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
                    '-': '⁻', '+': '⁺'}
    exp_str = ''.join(superscripts.get(c, c) for c in str(exp_int))
    return f'{base} × 10{exp_str}'
```

The plain-decimal branch strips trailing zeros AND trailing decimal points (so `1234.500` becomes `1234.5` not `1234.5.`). The fallback to `:.5g` handles edge cases where stripping leaves an empty string.

## Why Unicode superscript instead of `<sup>`?

HTML rendering in Streamlit's `st.markdown` is fine but adds visual weight (and depends on `unsafe_allow_html=True`). Unicode superscripts render the same way in monospace contexts and don't require HTML at all. They also work in non-HTML contexts (terminal copies, Markdown viewers).

## Edge cases

- **Very tiny values** like `1e-10` → scientific notation (`"1 × 10⁻¹⁰"`).
- **NaN** — would slip past the None check and the math comparison; result is `'nan'` (lowercase) from f-string formatting. Not specifically handled.

## Usage

```python
# Inside renderers/emissions.py, for the GHG summary table:
co2e_str = f'<b>{format_html_num(co2e_val)}</b> {target_unit} CO₂e'
```

## See also

[[formatting]] · [[formatting.format_latex_num]] · [[format_sig_figs]]
