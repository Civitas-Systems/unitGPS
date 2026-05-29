---
type: function
parent: "[[themes]]"
module: streamlit_app.themes
file: apps/streamlit_app/themes.py
lines: "108-110"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, theming]
related:
  - "[[themes]]"
  - "[[themes.inject_css]]"
---

# themes.get_theme

Return the named theme dict, falling back to the default if the name is unknown. Defensive lookup so a stale `session_state.theme` value can't crash the page.

## Signature

```python
def get_theme(name: str) -> dict
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `name` | `str` | Theme name (e.g. `'Obsidian'`, `'Cyberpunk'`). Case-sensitive. |

## Output

The theme dict. Always returns a valid theme — falls back to `THEMES[DEFAULT_THEME]` if `name` isn't in `THEMES`.

## Implementation

```python
def get_theme(name: str) -> dict:
    return THEMES.get(name, THEMES[DEFAULT_THEME])
```

Single line. `dict.get(key, default)` is the standard Python idiom for "lookup with fallback."

## When the fallback fires

- User picks a theme, you later remove that theme from `THEMES`. Their stored `session_state.theme` is now invalid → fallback to default.
- Migration — older sessions might have theme names that have since been renamed.
- Bad config in some upstream code that pre-populates session state with a typo.

## Usage

```python
# In app.py
theme = get_theme(st.session_state['theme'])
inject_css(theme)
```

## See also

[[themes]] · [[themes.inject_css]]
