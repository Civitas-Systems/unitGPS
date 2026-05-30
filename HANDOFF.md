# HANDOFF — current state (2026-05-30)

The app is **validated, documented, and deploy-ready**. 68 tests pass.

## What it is
Graph-based unit converter + GHG-emissions calculator. Engine = pandas + networkx
(`src/unitgps/engine/`); UI = Streamlit (`apps/streamlit_app/`); data committed under
`data/`. Start reading at `docs/_MOC.md`; methods in `docs/METHODOLOGY.md`.

## Verify
```
PYTHONPATH=src python -m pytest -q        # expect 68 passed
```
`tests/test_validation.py` checks the engine against NIST / IPCC / EPA reference values.

## Current state
- **Engine**: validated to reproduce NIST conversions, IPCC AR4/5/6 GWPs, EPA EF exactly;
  round-trips < 0.1%. One filter rule (infra-always / blank-excludes / blank-year-wildcard).
- **UI**: card layout, inline segmented filter toolbar, transparent Mass × GWP = CO₂e
  table, theme-aware network labels, accessibility pass, 13 themes (contrast-fixed).
- **Docs**: METHODOLOGY, QA_NOTES (+ findings), Roadmap to world-class, Performance and
  scaling, References, FAQ, Scenarios, Tutorial, Diagrams, CHANGELOG (through Pass 12).
- **Deploy**: `requirements.txt`, `.streamlit/config.toml`, `DEPLOYMENT.md`, CI workflow.

## Open items — need Dave / an awake design session
- **F1** (`docs/QA_NOTES.md`): data's AR6 CH₄ GWP-100 = 27.9 vs IPCC 29.8 (fossil)/27.0 (non-fossil).
- **BTU definition** choice (`docs/Reference/Data/Exact conversion constants.md`).
- **Engine upgrades** (`docs/Roadmap to world-class.md`): uncertainty propagation; principled ambiguity policy.
- **Scale** (`docs/Concepts/Performance and scaling.md`): Parquet (free) → precompute edge metadata → vectorise (pandas/Polars) → DuckDB → native.
- **git**: push pending commits; `git commit-graph write` heals the corrupted commit-graph.

## Gotchas (also in agent memory)
- OneDrive: write files via bash heredocs (Write/Edit can truncate); clear local
  `__pycache__` after engine edits; `git config gc.auto 0`; sandbox git is unreliable —
  commit natively on Windows.
- Engine edits need a **full** Streamlit restart (`@st.cache_resource` caches the graph).
