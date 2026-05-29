---
type: test
file: tests/
status: current
generation: Claude
last_updated: 2026-05-21
tests_total: 30
tests_passing: 30
runtime_seconds: 2.21
tags: [tests, pytest, smoke]
related:
  - "[[DataLoader]]"
  - "[[UnitGraph]]"
  - "[[identify_conversion_path]]"
  - "[[calculate_conversion_factor]]"
  - "[[determine_ghg_emissions]]"
  - "[[Reciprocal edges]]"
  - "[[GHG emissions and GWP]]"
---

# Test suite

30 tests covering all 5 engine modules. Real smoke tests against the canonical data files — no mocking. Run in ~2 seconds.

## How to run

```bat
cd v0.5-Claude
pytest
```

Pytest auto-discovers `tests/`. The `pyproject.toml` config sets `testpaths = ['tests']`.

If you hit "FUSE-mounted OneDrive path" issues during teardown, use the workaround from the engine port:

```bash
cd /tmp
python -m pytest /path/to/v0.5-Claude/tests/ -p no:cacheprovider --rootdir=/path/to/v0.5-Claude
```

## conftest.py — shared fixtures

| Fixture | Scope | Returns |
|---------|-------|---------|
| `data_paths` | session | `{'data_library': '...', 'gwp_file': '...'}` |
| `loader` | session | `DataLoader` instance |
| `combined_data` | session | DataFrame post-reciprocal-synthesis |
| `node_attrs` | session | `{unit: {...}}` |
| `gwps` | session | GWP DataFrame |
| `graph` | session | `UnitGraph` instance |
| `empty_search_params` | function | `{'Data Year': {'mode': 'all', 'values': []}}` |

`session` scope means the graph is built once for the whole test run (which takes most of the 2-second runtime). Per-test fixtures are cheap.

## test_data.py — 6 tests

Tests for [[DataLoader]] and its three methods.

| Test | What it asserts |
|------|-----------------|
| `test_data_library_loads` | Required columns present; >3,635 rows after reciprocals. |
| `test_reciprocal_synthesized_for_known_row` | For Anthracite/mmBTU CO2 (forward = 103.69), reciprocal row exists with Value ≈ 1/103.69. |
| `test_no_null_values` | All `Value` cells are non-null after load. |
| `test_static_conversions_not_duplicated` | Exactly 294 Unit Conversion rows (the raw count — proves they're not reciprocated). |
| `test_unit_attributes` | `J` is Energy, `kg` is Weight, `kJ` is Energy. |
| `test_gwps_split_indicator` | After load: `Assessment Report`, `Time Horizon` columns exist; `Indicator` is gone; CO₂/AR5/100 returns GWP = 1.0. |

## test_graph.py — 6 tests

Tests for [[UnitGraph]] and [[UnitGraph.filter_graph]].

| Test | What it asserts |
|------|-----------------|
| `test_graph_builds` | >50 nodes, >1000 edges in the full graph. |
| `test_common_units_are_nodes` | `J`, `kJ`, `kg`, `g`, `BTU`, `Cal` all exist. |
| `test_filter_keeps_unit_conversions` | Filtered graph includes Unit Conversion and Magnitude Adjustment edges by default. |
| `test_filter_excludes_emission_factors_by_default` | Filtered graph excludes Emission Factor edges when `include_emission_factors=False`. |
| `test_filter_includes_emission_factors_when_requested` | Including EFs when `include_emission_factors=True`. |
| `test_get_nodes_by_dimension` | `Weight` dimension includes `kg` and `g`. |

## test_pathfinding.py — 5 tests

Tests for [[identify_conversion_path]] and [[convert_path_to_edge_tuples]].

| Test | What it asserts |
|------|-----------------|
| `test_finds_direct_path` | `kJ → J` returns at least one path; all paths start with `kJ` and end with `J`. |
| `test_missing_node_returns_empty` | Asking for a non-existent source unit returns `[]` (not a crash). |
| `test_convert_path_to_edge_tuples_single` | `['A', 'B', 'C']` → `[[('A', 'B'), ('B', 'C')]]`. |
| `test_convert_path_to_edge_tuples_multi` | `[['A', 'B'], ['A', 'C', 'D']]` → expected pair of edge lists. |
| `test_convert_empty_path` | Empty input → empty output. |

## test_calculate.py — 6 tests

Tests for [[calculate_conversion_factor]] and the utility functions [[format_sig_figs]] / [[is_valid_parameter]].

| Test | What it asserts |
|------|-----------------|
| `test_format_sig_figs_basic` | `format_sig_figs(0)` is `"0"`; `1234.5678` starts with `"1235"`; tiny/huge values use scientific notation. |
| `test_is_valid_parameter` | `None`, empty, whitespace, and `"nan"` all return `False`; real values return `True`. |
| `test_kj_to_j_factor_is_1000` | `1 kJ → J` gives `conversion_factor` and `ultimate_value` both ≈ 1000. |
| `test_btu_to_j_factor` | `1 BTU → J` gives `conversion_factor` ≈ 1055.06 (1e-4 tolerance). |
| `test_round_trip_is_identity` | `J → kJ → J` round-trip returns exactly 1.0 (float-epsilon tolerance). |
| `test_audit_steps_structure` | Every audit step has source, target, and at least one edge dict with a value. |

The round-trip test is the load-bearing one — it proves that [[Reciprocal edges|reciprocal synthesis]] is mathematically consistent.

## test_emissions.py — 7 tests

Tests for [[find_gwp]], [[determine_conversion]], [[determine_ghg_emissions]].

| Test | What it asserts |
|------|-----------------|
| `test_find_gwp_co2_is_1` | CO2/AR5/100 = 1.0 exactly. |
| `test_find_gwp_ch4_ar5_100` | CH4/AR5/100 = 28.0 exactly. |
| `test_find_gwp_n2o_ar5_100` | N2O/AR5/100 = 265.0 exactly. |
| `test_find_gwp_unknown_returns_none` | Unknown gas → `None`. |
| `test_determine_conversion_kj_to_j` | High-level wrapper: kJ → J with factor 1000.0. |
| `test_determine_conversion_no_path` | Unknown target unit → `status: 'error'`. |
| `test_determine_ghg_emissions_runs` | End-to-end mmBTU → kg with Anthracite filter: `valid_calc=True`, CO2 mass in 50–200 kg range. |

The last test is the only one that exercises the full filter → path → calculate → GWP-weight pipeline.

## What's NOT tested

| Concern | Why not (yet) |
|---------|---------------|
| Streamlit UI | Bare-mode import smoke-tested manually; full UI testing needs Selenium or similar. |
| Per-theme CSS injection | Pure visual; needs screenshot tests. |
| Ambiguity warning | Engine doesn't raise [[AmbiguityError]] today; reactivate when strict mode lands. |
| Performance benchmarks | Engine is fast enough that there's no benchmark threshold to defend. |
| Property-based tests (round-trip for many random units) | Single round-trip test today covers the core invariant. |

## Adding a test

1. Pick the right `test_*.py` file (matches the engine module being tested).
2. Use the appropriate fixture from `conftest.py` (`graph`, `combined_data`, etc.).
3. Assert on real values from the canonical data file — magic numbers are fine if they're traceable to a Data Library row.
4. Run `pytest -v` to verify.

## See also

[[architecture]] · [[DataLoader]] · [[UnitGraph]] · [[identify_conversion_path]] · [[calculate_conversion_factor]] · [[determine_ghg_emissions]] · [[Reciprocal edges]]
