---
type: function
parent: "[[formatting]]"
module: streamlit_app.formatting
file: apps/streamlit_app/formatting.py
lines: "68-76"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, formatting, latex, escaping]
related:
  - "[[formatting]]"
  - "`formatting.build_math_latex` *(removed)*"
---

# formatting.sanitize_latex

Escape a unit name so KaTeX renders it correctly. The catch: KaTeX chokes on caret-containing strings inside `\text{}` blocks (so `\text{ft^3}` crashes); the fix is to split on `^` and emit the exponent outside the `\text` block.

## Signature

```python
def sanitize_latex(s: str) -> str
```

## Inputs / Outputs

| Input | Output | Why |
|-------|--------|-----|
| `"kg"` | `"\\text{kg}"` | Plain text wrap |
| `"ft^3"` | `"\\text{ft}^{3}"` | Split exponent out so KaTeX doesn't choke |
| `"BTU"` | `"\\text{BTU}"` | Plain |
| `"mmBTU"` | `"\\text{mmBTU}"` | Plain |

## How it works

```python
def sanitize_latex(s):
    if '^' in s:
        base, exp = s.split('^', 1)
        return f'\\text{{{base}}}^{{{exp}}}'
    return f'\\text{{{s}}}'
```

`s.split('^', 1)` splits on the FIRST `^` only — defensive in case a unit ever contains multiple carets (it doesn't today, but the limit-1 split is the right behavior anyway).

## Why this exists

The Data Library has units like `ft^3` (cubic feet), `m^2` (square meters), `mol^-1` (per mole). Rendering them in a LaTeX equation as `\text{ft^3}` causes KaTeX to render literal text or throw. Splitting the caret out produces `\text{ft}^{3}` which KaTeX renders as `ft³` — exactly what's wanted.

## Edge cases

- **`^^`** (literal double caret) — never appears in real units; would produce `\text{}^{^...}` which is odd LaTeX but doesn't crash.
- **Unicode in unit names** (e.g. `°C`) — passes through unchanged. KaTeX renders it correctly via Unicode passthrough.

## Usage

```python
# Inside build_math_latex:
s_unit = sanitize_latex(source_unit)
t_unit = sanitize_latex(target_unit)
latex_str = f'{start_num} \\, {s_unit} \\times ...'
```

## See also

[[formatting]] · `formatting.build_math_latex` *(removed)*
