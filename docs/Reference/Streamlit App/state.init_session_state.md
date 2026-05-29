---
type: function
parent: "[[state]]"
module: streamlit_app.state
file: apps/streamlit_app/state.py
lines: "38-42"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, state, initialization]
related:
  - "[[state]]"
  - "[[app]]"
---

# state.init_session_state

Populate any missing `_DEFAULTS` keys into `st.session_state`. Idempotent — safe to call on every rerun.

## Signature

```python
def init_session_state() -> None
```

## Implementation

```python
def init_session_state() -> None:
    for k, v in _DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v
```

## Why "if not in" instead of unconditional assignment

Because Streamlit widgets read their value from `session_state` AND write back to it on change. Unconditionally assigning would clobber the user's last selection on every rerun.

The pattern: defaults seed the state only when there's nothing there yet; the user's interactions update it; future reruns see the updated value.

## Idempotence

```python
init_session_state()                 # first rerun: seeds 13 keys
st.session_state['theme'] = 'Cyberpunk'   # user picks Cyberpunk
init_session_state()                 # next rerun: noops, theme stays Cyberpunk
```

## When to call

Once per rerun, near the top of [[app]], after `st.set_page_config`. Calling it later still works — but widgets rendered before the call would see missing keys and error.

## Usage

```python
# In app.py
from streamlit_app.state import init_session_state

st.set_page_config(...)
init_session_state()
theme = get_theme(st.session_state['theme'])
inject_css(theme)
```

## See also

[[state]] · [[app]]
