# Contributing / developer guide

## Setup
```bat
apps\streamlit_app\run.bat
```
The launcher creates `.venv`, installs deps, and runs the app. To work on the engine
alone you only need `pandas`, `networkx`, `openpyxl`, `pyarrow`.

## Run the tests
```bat
.venv\Scripts\python.exe -m pytest          REM or: PYTHONPATH=src pytest -q
```
68 tests: engine smoke tests + external validation (`tests/test_validation.py`, which
checks the engine against NIST/IPCC/EPA reference values). CI runs them on every push.

## Layout
- `src/unitgps/engine/` — UI-agnostic engine (pandas + networkx only). The source of truth.
- `apps/streamlit_app/` — the Streamlit UI (decomposed into app/filters/themes/renderers/...).
- `data/` — the canonical data library + IPCC GWPs (committed, loaded by a portable path).
- `docs/` — Obsidian vault: start at `docs/_MOC.md`; methods in `METHODOLOGY.md`.

## Conventions
- The engine never imports Streamlit. Keep computation in `src/`, presentation in `apps/`.
- The filter rule lives in **two** places that must agree: `UnitGraph.filter_graph`
  (engine) and `filters.apply_db_and_temporal_filters` (app, for live counts). Change both.
- After editing engine code, do a **full** Streamlit restart (the `@st.cache_resource`
  graph survives a rerun) and clear local `__pycache__` if you see a phantom ImportError.
- Data values are sourced/curated, not authored here — see `docs/QA_NOTES.md` before
  changing any number, and prefer fixing values at the data-source/pipeline level.

## Before committing
- `pytest` green; for engine changes, confirm `tests/test_validation.py` still passes.
- See `DEPLOYMENT.md` to ship to Streamlit Community Cloud.
