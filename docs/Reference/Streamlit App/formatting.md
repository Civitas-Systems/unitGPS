---
type: module
module: streamlit_app.formatting
file: apps/streamlit_app/formatting.py
lines: "1-163"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, formatting, latex, graphviz]
related:
  - "[[formatting.format_html_num]]"
  - "[[formatting.format_latex_num]]"
  - "[[formatting.sanitize_latex]]"
  - "`formatting.build_math_latex` *(removed)*"
  - "`formatting.draw_path_graph` *(removed)*"
  - "[[format_sig_figs]]"
---

# formatting (module overview)

Pure formatting helpers — **no Streamlit dependency.** Used by both [[renderers - conversion]] and [[renderers - emissions]] to format numbers, build LaTeX equations, and render Graphviz pathway diagrams.

## Public API

| Symbol | Type | Purpose |
|--------|------|---------|
| [[formatting.format_html_num]] | function | Format a float for HTML with Unicode superscript exponents. |
| [[formatting.format_latex_num]] | function | Format a float for LaTeX with `\times 10^{n}` for small/large. |
| [[formatting.sanitize_latex]] | function | Escape a unit name like `ft^3` for KaTeX. |
| `formatting.build_math_latex` *(removed)* | function | Build the aligned multi-step conversion equation. |
| `formatting.draw_path_graph` *(removed)* | function | Build the Graphviz DOT source for the pathway diagram. Supports a `label_mode` parameter (`both` / `set_only` / `value_only`) so callers can tune what shows on each edge. |

## Why a separate module?

Two reasons:

1. **Reusable across renderers.** Both Conversions and GHG Emissions panels need the same LaTeX/HTML formatters and the same Graphviz drawer. Extracting them avoids copy-paste.
2. **No Streamlit means testable.** These functions can be unit-tested without spinning up a Streamlit context — useful for catching LaTeX-escape bugs early.

## What the three "format" functions return

| Function | Input | Output style | Example |
|----------|-------|--------------|---------|
| [[format_sig_figs]] (engine) | float | Plain string | `'1.235e+03'` |
| [[formatting.format_html_num]] | float | Plain or Unicode superscript | `'1.235 × 10³'` |
| [[formatting.format_latex_num]] | float | LaTeX | `'1.235 \\times 10^{3}'` |

The three formatters trade off "compactness vs. context" — Conversions inner card uses HTML; the LaTeX equation uses LaTeX; the engine itself uses sig-figs plain.

## See also

[[formatting.format_html_num]] · [[formatting.format_latex_num]] · [[formatting.sanitize_latex]] · `formatting.build_math_latex` *(removed)* · `formatting.draw_path_graph` *(removed)* · [[format_sig_figs]]
