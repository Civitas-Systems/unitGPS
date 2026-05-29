---
type: function
module: unitgps.engine.pathfinding
file: src/unitgps/engine/pathfinding.py
lines: "49-61"
status: current
generation: Claude
last_updated: 2026-05-21
tags: [engine, pathfinding, utility]
related:
  - "[[identify_conversion_path]]"
  - "[[calculate_conversion_factor]]"
---

# convert_path_to_edge_tuples

Turn node lists into `(source, target)` edge tuples. A pure data-structure adapter — no graph traversal, no I/O. Sits between [[identify_conversion_path]] (which returns node sequences) and [[calculate_conversion_factor]] (which wants edge tuples).

## Signature

```python
def convert_path_to_edge_tuples(
    path_nodes: Union[NodePath, Sequence[NodePath]],
) -> List[List[EdgeTuple]]

NodePath = List[str]
EdgeTuple = Tuple[str, str]
```

## Inputs

Accepts either shape:

| Shape | Example | Treated as |
|-------|---------|------------|
| Single path | `['A', 'B', 'C']` | One path |
| List of paths | `[['A', 'B'], ['A', 'C', 'D']]` | Multiple paths |

The two shapes match the two ways callers commonly have data: a single path from `nx.shortest_path` or many from [[identify_conversion_path]].

## Output

Always a `list[list[tuple]]` — one outer list per input path, each inner list containing sequential `(u, v)` edges.

```python
convert_path_to_edge_tuples(['A', 'B', 'C'])
# → [[('A', 'B'), ('B', 'C')]]

convert_path_to_edge_tuples([['A', 'B'], ['A', 'C', 'D']])
# → [[('A', 'B')], [('A', 'C'), ('C', 'D')]]

convert_path_to_edge_tuples([])
# → []
```

The outer wrapping is uniform so [[calculate_conversion_factor]] can always iterate over paths the same way.

## How it works (pseudocode)

```
1. If input is empty, return [].
2. If the first element is a list, treat input as a list of paths;
   zip each path with its tail (path, path[1:]) into edge tuples.
3. Otherwise treat input as a single path; zip it into edge tuples
   and wrap in an outer list.
```

## Line-by-line

```python
if not path_nodes:
    return []
```

Empty input → empty output. Handles the [[identify_conversion_path|no-path-found]] case naturally.

```python
if isinstance(path_nodes[0], list):
    return [list(zip(p, p[1:])) for p in path_nodes]
```

List-of-paths case. `zip(p, p[1:])` is the standard Python trick for "pair each element with the next" — for `p = ['A', 'B', 'C']` this gives `[('A', 'B'), ('B', 'C')]`. The outer comprehension applies it per path.

```python
return [list(zip(path_nodes, path_nodes[1:]))]
```

Single-path case. Same zip trick, wrapped in an extra `[...]` so the output shape matches the list-of-paths branch.

## Edge cases

- **Single-node "path"** like `['A']` → `[[]]` (a list containing one empty edge list). Treated as zero-edge path; [[calculate_conversion_factor]] would compute a conversion factor of 1.0 (empty product).
- **Mixed input** — a list with first element a list but later elements strings → undefined; assumed list-of-paths and would crash on later iterations. No defense; not a real-world input.

## Usage

```python
from unitgps.engine import identify_conversion_path, convert_path_to_edge_tuples

paths = identify_conversion_path(F, 'mmBTU', 'kg')
# [['mmBTU', 'BTU', 'kg']]

edges = convert_path_to_edge_tuples(paths)
# [[('mmBTU', 'BTU'), ('BTU', 'kg')]]

# Now ready to pass to calculate_conversion_factor
```

## See also

[[identify_conversion_path]] · [[calculate_conversion_factor]]
