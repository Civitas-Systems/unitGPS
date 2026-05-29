---
type: function
parent: "[[themes]]"
module: streamlit_app.themes
file: apps/streamlit_app/themes.py
lines: "113-483"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, theming, css]
related:
  - "[[themes]]"
  - "[[themes.get_theme]]"
  - "[[app]]"
---

# themes.inject_css

Build the giant themed `<style>` block from a theme dict and emit it via `st.markdown`. Called once per rerun by [[app]] right after the theme is resolved.

## Signature

```python
def inject_css(theme: dict) -> None
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `theme` | `dict` | One of the entries in `THEMES`, typically obtained via [[themes.get_theme]]. |

## Output

None. Side effect: emits a `<style>...</style>` block into the page head via `st.markdown(unsafe_allow_html=True)`.

## What gets styled

This is roughly 370 lines of CSS inside a Python f-string. It restyles:

| Element | Selector | What changes |
|---------|----------|--------------|
| Page background | `.stApp` | bg color, text color, font family |
| Container cards | `[data-testid="stVerticalBlockBorderWrapper"]` | bg, border, radius, shadow, backdrop |
| Buttons | `.stButton > button` | bg, text color, border, radius, transform |
| Inputs | `div[data-baseweb="select"] > div` etc. | bg, border, radius |
| Dropdown menus | `html body [data-baseweb="popover"]` | popover bg, item bg, hover state |
| Tabs | `.stTabs [data-baseweb="tab-list"]` | sticky positioning, bg, radius |
| Number-input steppers | `[data-testid="stNumberInputStepUp/Down"]` | hidden by default, shown only on year-range inputs |
| Headers | `h1..h5, p, span, div` | text color (forced via `!important`) |
| Custom classes | `.metric-value`, `.metric-label`, `.audit-step`, `.badge`, `.ghg-summary-table`, `.ghg-badge-*` | Set per theme |

## How it works

```python
def inject_css(theme: dict) -> None:
    th = theme
    bg_prop = 'background' if 'gradient' in th['bg'] else 'background-color'
    text_on_primary = th.get('text_on_primary', '#FFFFFF')

    st.markdown(f"""
<style>
    .stApp {{
        {bg_prop}: {th['bg']};
        color: {th['text']};
        font-family: {th['font']};
    }}
    ...
""", unsafe_allow_html=True)
```

Key implementation points:

1. **`bg` may be a CSS gradient.** The Glassmorphism theme uses `linear-gradient(...)`; that needs CSS `background` (not `background-color`). The check sniffs the theme value for the substring `gradient`.
2. **`text_on_primary` defaults to white.** Themes that don't define it (in case a new theme is added without it) fall through to white.
3. **f-string with `{{` and `}}`** — Python f-strings escape literal braces by doubling them. The CSS has tons of braces; every one is doubled.

## Why `!important` everywhere?

Streamlit's own component styles use `!important`, so anything we inject without `!important` would be overridden by Streamlit's defaults. We're in a CSS specificity arms race we'd lose without it.

## Performance

Runs on every rerun, but the CSS is ~15KB of text — negligible. The browser parses the same CSS afresh every time, but at this size it's microseconds. No caching needed.

## Why one big function instead of per-element helpers?

Tried both during the port. The single-function approach won because:

- The CSS is heavily interleaved with f-string interpolation. Splitting it across functions means passing the theme dict around constantly.
- Streamlit applies the *whole* stylesheet in one shot; injecting many small `<style>` blocks doesn't help anything.
- Easier to scan the full styling rules in one place when debugging visual issues.

## Caveats

- **`!important` makes overrides hard.** If you want to style something differently on one page, you need higher specificity AND `!important`.
- **Selectors are fragile to Streamlit updates.** A future Streamlit release that renames `data-testid` attributes would silently break theming. Mitigation: pin Streamlit version in `requirements/streamlit.txt`.
- **Browser dev tools are essential.** When tweaking CSS, inspect-element on the rendered page to see what selector to target.

## See also

[[themes]] · [[themes.get_theme]] · [[app]]
