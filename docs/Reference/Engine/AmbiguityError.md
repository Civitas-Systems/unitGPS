---
type: exception
module: unitgps.engine.calculate
file: src/unitgps/engine/calculate.py
lines: "16-23"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [engine, exception, ambiguity]
related:
  - "[[Ambiguous paths]]"
  - "[[calculate_conversion_factor]]"
  - "[[determine_conversion]]"
  - "[[determine_ghg_emissions]]"
---

# AmbiguityError

A custom exception class reserved for strict-mode ambiguity handling. **Not currently raised by the engine** — kept in the public API for future use.

## Definition

```python
class AmbiguityError(Exception):
    """Raised when a conversion path has multiple unresolved parallel edges."""
```

Subclass of `Exception`, no extra methods. Standard try/except handling.

## Why it exists but isn't raised

Antigravity originally planned to raise this whenever a path step had multiple parallel edges (see [[Ambiguous paths]]). The behavior was changed before the Antigravity → Claude port to "silently use the first edge and flag `is_ambiguous=True` in the audit." The exception class survived the change because:

1. The public API exports it (caller code may still reference it).
2. [[determine_conversion]] and [[determine_ghg_emissions]] still have `except AmbiguityError` branches, so if a future caller raises it from a hook, those wrappers handle it cleanly.
3. A "strict mode" flag could legitimately reactivate raising in the future.

## What the engine does instead

In [[calculate_conversion_factor]]:

```python
if edge_count > 1:
    path_ambiguity = True       # mark the path, don't raise

primary_val = step_values[0]    # use the first parallel edge's value
path_values.append(primary_val)
```

And in [[determine_conversion]] / [[determine_ghg_emissions]]:

```python
try:
    ...
except AmbiguityError as e:
    return {'status': 'ambiguity_error', 'data': e.args[0]}
```

The except branch is dead code today, but it's the right shape for the future.

## Reactivation path

If you ever want strict mode:

```python
# In calculate_conversion_factor, after the loop:
if path_ambiguity and strict:
    raise AmbiguityError(ambiguous_details)
```

…and add a `strict: bool = False` parameter. The wrappers already handle the exception.

## See also

[[Ambiguous paths]] · [[calculate_conversion_factor]] · [[determine_conversion]] · [[determine_ghg_emissions]]
