---
type: function
parent: "[[state]]"
module: streamlit_app.state
file: apps/streamlit_app/state.py
lines: "50-52"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, state, callback]
related:
  - "[[state]]"
  - "[[state.on_final_change]]"
  - "[[renderers - conversion]]"
  - "[[renderers - emissions]]"
---

# state.on_start_change

Streamlit `on_change` callback for the "Starting Value" number input. Sets `calc_direction = 'forward'`. Called automatically by Streamlit when the user edits the input.

## Signature

```python
def on_start_change() -> None
```

## Implementation

```python
def on_start_change() -> None:
    st.session_state['calc_direction'] = 'forward'
```

## What 'forward' means

When the calc runs (after a result panel renders), it has to decide whether to update `final_val` from `start_val × factor` or `start_val` from `final_val / factor`. The `calc_direction` field tracks which input the user touched most recently:

- `'forward'` → user edited `start_val` → compute `final_val = start_val × conversion_factor`
- `'backward'` → user edited `final_val` → compute `start_val = final_val / conversion_factor`

The renderers ([[renderers - conversion]], [[renderers - emissions]]) read `calc_direction` and update the appropriate side after each calculation. This is the bidirectional-input behavior — you can edit either Starting or Final and the other side back-solves.

## Sibling

[[state.on_final_change]] does the mirror for the Final Value input.

## Why a callback instead of inline check?

Callbacks fire synchronously the moment Streamlit detects a widget change, BEFORE the rerun. By the time the script runs again, `calc_direction` is already set correctly, and the renderers can trust it without inspecting which value changed.

The alternative (compare new vs. old values in the renderers) would require holding the previous values in session_state too — more state, more bugs.

## See also

[[state]] · [[state.on_final_change]] · [[renderers - conversion]] · [[renderers - emissions]]
