---
type: concept
status: current
generation: Claude
last_updated: 2026-05-30
tags: [concept, performance, scaling, engine]
related:
  - "[[UnitGraph.filter_graph]]"
  - "[[DataLoader.load_data_library]]"
  - "[[architecture]]"
---

# Performance and scaling

How UnitGPS behaves as the data library grows toward millions of rows, where it
breaks, and what to do about it. Measured 2026-05-30 on the current library.

## Current benchmarks (6,049 edges, 147 units)

| Operation | Time | Frequency |
|-----------|------|-----------|
| Load data (xlsx) | ~844 ms | once per session (cached via `@st.cache_resource`) |
| Build graph (networkx) | ~35 ms | once per session |
| `filter_graph` | ~31 ms | **every interaction** |
| One conversion | ~7 ms | per result |
| GHG (3 gases) | ~31 ms | per GHG result |

## Where it breaks at scale (≈1,000× → ~6M edges)

- **xlsx load** ~844 ms × 1000 ≈ **14 min** cold start. Dominated by the Excel parser.
- **`filter_graph`** ~31 ms × 1000 ≈ **~30 s per click** — it Python-loops every edge and,
  per edge, re-derives the `Set` string (`str().strip().lower()`) and parses `Data Year`.
  This is the scaling wall, because it runs on every UI interaction.
- **networkx memory** — a MultiDiGraph costs a few hundred bytes/edge; millions of edges
  is GBs of RAM.

## Easy win available NOW (zero code change)

**Store the data library as Parquet.** `DataLoader.load_data_library` already branches on
`.parquet` and reads it with `pd.read_parquet` — 10–50× faster than xlsx and far smaller
on disk. When your pipeline lands, write Parquet (keep xlsx for human editing if you
like). This removes the cold-start problem entirely.

## Applied now

- **Active-filter hoist in `filter_graph`** — the per-edge loop no longer re-scans ~20
  mostly-null search keys; behaviour-identical (verified by the full suite). Helps a
  *filtered* query at scale; negligible on small/unfiltered ones.

## For the awake / scale session (each behaviour-preserving, but medium effort)

1. **Precompute per-edge metadata at build time.** Store `is_emission_factor` (bool) and
   the parsed numeric `Data Year` as edge attributes once in `UnitGraph.__init__`, so
   `filter_graph` stops re-deriving them per edge per call. Pure speedup, low risk.
2. **Vectorise `filter_graph` in pandas.** Filter the source DataFrame with boolean masks
   (C-speed) and build the subgraph from the surviving rows, instead of Python-looping
   networkx edges. This is the real fix — turns ~30 ms into ~ms and scales to millions.
   The same one-rule logic already exists in pandas as
   [[filters.apply_db_and_temporal_filters]], so the two could converge on one
   vectorised implementation.
3. **Lighter graph backend** (only at true millions). Evaluate `scipy.sparse` adjacency or
   `igraph` if networkx RAM/iteration becomes the limit. Bigger change — defer until the
   data actually demands it.

## Guidance

Do (1) and the Parquet switch first; they're low-risk and high-leverage. (2) is the
durable scaling fix and should be done when the data starts growing. (3) only if needed.
None of this is required for the current app to work well.

## Longer-horizon / exploratory (ideas to weigh later — not now)

These trade more engineering, or a new language, for speed. Revisit only when the data
genuinely demands it; exhaust the cheap wins (Parquet, precompute edge metadata,
vectorise the filter) first.

- **Polars instead of pandas** (data + filter layer). Polars (Rust core, multi-threaded,
  lazy, columnar) is commonly several-to-10× faster than pandas on large frames with
  lower memory. The data load and a vectorised `filter_graph` are the natural adoption
  points; the API is close enough to be a contained swap. Strong candidate at millions
  of rows.
- **DuckDB over the data library.** Query the library as SQL over Parquet (vectorised,
  out-of-core) to filter/aggregate millions of rows *before* they become graph edges.
  Pairs naturally with Polars.
- **Faster graph backend** — `igraph` or `graph-tool` (C/C++ cores) in place of networkx
  for build + shortest paths at scale (networkx is pure-Python and RAM-heavy). Bigger
  change; only if the graph itself becomes the limit.
- **Native hot path** — push the per-edge filter / path math into **Rust (PyO3)** or
  **Julia** (`juliacall`), or a small Julia/Rust service, with Python as the
  orchestration layer. Highest ceiling, highest integration cost — most justified if
  heavy numerical work lands (e.g. Monte-Carlo **uncertainty propagation**, large batch
  jobs).
- **Caching / materialised views** — memoise common filtered subgraphs and conversion
  results keyed on the filter signature, so repeated queries skip recomputation.

Rough order of adoption by cost/benefit: Parquet → precompute edge metadata → vectorise
(pandas or **Polars**) → DuckDB pre-filter → graph backend → native (Rust/Julia).
