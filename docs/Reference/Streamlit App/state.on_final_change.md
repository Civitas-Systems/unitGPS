---
type: function
parent: "[[state]]"
module: streamlit_app.state
file: apps/streamlit_app/state.py
lines: "55-57"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, state, callback]
related:
  - "[[state]]"
  - "[[state.on_start_change]]"
---

# state.on_final_change

Streamlit `on_change` callback for the "Final Value" number input. Sets `calc_direction = 'backward'`.

## Signature

```python
def on_final_change() -> None
```

## Implementation

```python
def on_final_change() -> None:
    st.session_state['calc_direction'] = 'backward'
```

## What this enables

User types in `Final Value = 1000` then re-runs:

```
1. on_final_change fires → calc_direction = 'backward'
2. Script reruns
3. Calculate runs → conversion_factor computed
4. Renderer sees calc_direction == 'backward', solves:
       start_val = final_val / conversion_factor
                 = 1000 / 1000       (for 1 kJ → J)
                 = 1.0
5. Starting Value number_input rerenders with the back-solved value
```

This is what makes the two-way input feel like algebraic substitution — edit either side and the other side updates.

## Mirror of

[[state.on_start_change]] for the forward direction.

## See also

[[state]] · [[state.on_start_change]]
