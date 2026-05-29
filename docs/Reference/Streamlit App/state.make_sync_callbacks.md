---
type: function
parent: "[[state]]"
module: streamlit_app.state
file: apps/streamlit_app/state.py
lines: "60-95"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [streamlit, state, callback, factory]
related:
  - "[[state]]"
  - "[[DataLoader.get_units_attributes]]"
  - "[[app]]"
---

# state.make_sync_callbacks

Factory that builds the four dimension↔unit sync callbacks, each closed over the live `node_attrs` dict. Returns them in a dict ready to wire into widget `on_change=` parameters.

## Signature

```python
def make_sync_callbacks(node_attrs: dict) -> dict
```

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `node_attrs` | `dict` | The `{unit: {Unit Dimension, ...}}` dict from [[DataLoader.get_units_attributes]]. |

## Output

A dict of four callbacks:

```python
{
    'source_dim':  callable,  # → wire to Source Unit's on_change
    'source_unit': callable,  # → wire to Source Dimension's on_change
    'target_dim':  callable,  # → wire to Target Unit's on_change
    'target_unit': callable,  # → wire to Target Dimension's on_change
}
```

Note the **deliberate swap**: `source_dim` (which keeps Dimension in sync after Unit changed) wires to the Unit widget, and `source_unit` (which keeps Unit valid after Dimension changed) wires to the Dimension widget. The callback name describes what it *updates*, not what it *responds to*.

## What each callback does

```python
def sync_source_dim() -> None:
    """Run after Unit changed: update Dimension to match the new Unit."""
    unit = st.session_state.get('source_unit_sb')
    if unit:
        dim = node_attrs.get(unit, {}).get('Unit Dimension')
        if dim:
            st.session_state['source_dim'] = dim

def sync_source_unit() -> None:
    """Run after Dimension changed: clear Unit if it no longer belongs to new Dim."""
    dim = st.session_state.get('source_dim')
    unit = st.session_state.get('source_unit_sb')
    if dim and unit:
        if node_attrs.get(unit, {}).get('Unit Dimension') != dim:
            st.session_state['source_unit_sb'] = None
```

`sync_source_dim` infers Dimension from Unit. `sync_source_unit` invalidates Unit if it doesn't match the new Dimension (so the unit dropdown opens fresh). The Target pair mirrors this exactly.

## Why a factory?

The callbacks need `node_attrs` to look up dimensions, but Streamlit's `on_change` parameter doesn't accept additional args. Three options:

| Approach | Pro | Con |
|----------|-----|-----|
| Module-level globals | Simplest | Couples module to a specific node_attrs instance |
| `functools.partial` | Clean | Many small partials, hard to introspect |
| **Factory + closure** (current) | One factory call, four closures, easy to test by passing a fake `node_attrs` | Slightly more lines |

The factory pattern wins because `node_attrs` only exists after the engine loads, which means callbacks have to be built at runtime, not import time.

## Wiring example

```python
# In app.py after the engine loads:
sync_callbacks = make_sync_callbacks(node_attrs)

# When rendering the Source widgets:
st.selectbox('Dimension', ..., key='source_dim',
             on_change=sync_callbacks['source_unit'])
st.selectbox('Unit',      ..., key='source_unit_sb',
             on_change=sync_callbacks['source_dim'])
```

## Visual outcome

- Pick a Source Unit like `kJ` → Dimension auto-fills to `Energy`.
- Switch Dimension to `Weight` → kJ doesn't belong to Weight → Unit dropdown clears.
- Pick Unit `kg` → Dimension is `Weight`, was already `Weight`, no visible change.

## See also

[[state]] · [[DataLoader.get_units_attributes]] · [[app]]
