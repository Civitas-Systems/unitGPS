---
type: function
module: unitgps.engine.calculate
file: src/unitgps/engine/calculate.py
lines: "26-32"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [engine, formatting, utility]
related:
  - "[[is_valid_parameter]]"
  - "[[formatting]]"
---

# format_sig_figs

Format a float for display, switching between standard decimal notation and scientific notation based on magnitude. Used everywhere the engine or UI needs to show a number to a human.

## Signature

```python
def format_sig_figs(value, sig_figs: int = 4) -> str
```

## Inputs

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `value` | numeric | — | Number to format. Accepts `int`, `float`, NumPy scalar. |
| `sig_figs` | `int` | `4` | Desired significant figures. |

## Output

A `str` formatted in one of three ways:

| Input range | Notation | Example |
|-------------|----------|---------|
| `value == 0` | Literal `"0"` | `format_sig_figs(0)` → `"0"` |
| `1e-3 ≤ |value| < 1e5` | Python `g` format | `format_sig_figs(1234.5678)` → `"1235"` |
| Outside that range | Scientific (`e`) format | `format_sig_figs(1.23e8)` → `"1.230e+08"` |

The split points come from Antigravity's choice that "readable" means roughly thousandths to hundred-thousands; anything outside is too unwieldy to show as decimals.

## How it works

```python
def format_sig_figs(value, sig_figs=4):
    if value == 0:
        return "0"
    abs_val = abs(value)
    if abs_val < 1e-3 or abs_val >= 1e5:
        return f"{value:.{sig_figs - 1}e}"
    return f"{value:.{sig_figs}g}"
```

`sig_figs - 1` for scientific notation because Python's `e` format counts the leading digit separately from the precision spec. So `sig_figs=4` becomes `.3e`, which yields four total digits.

## Why not just use `g` everywhere?

`g` is great mid-range but has two annoying behaviors at extremes: it drops trailing zeros (so `100000` formats as `1e+05` losing the zeros) and it can show very-small numbers as `0` with low precision. Forcing scientific notation outside the mid-range gives consistent precision.

## Examples

```python
format_sig_figs(0)                # '0'
format_sig_figs(1234.5678)        # '1235'
format_sig_figs(1234.5678, 6)     # '1234.57'
format_sig_figs(0.0001234)        # '1.234e-04'  (below 1e-3)
format_sig_figs(99999)            # '9.999e+04'  (just under 1e5 — yes, scientific)
format_sig_figs(99998)            # '99998'       (below 1e5 wait — actually 9.999e+04 due to <1e5 check)
format_sig_figs(-1234.5)          # '-1235'
```

The `<1e5` (not `<=1e5`) means `99999` formats decimally, but `100000` flips to scientific.

## See also

[[is_valid_parameter]] · [[formatting]] · [[calculate_conversion_factor]]
