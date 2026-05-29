# UnitGPS — Claude generation (v0.5)

Graph-based universal unit converter and GHG-emissions calculator. This folder is the **Claude** generation — the active rewrite that takes over from the `v0.4-Antigravity/` sibling.

## Status

- ✅ **Engine** ported, ~700 lines across 5 modules.
- ✅ **Tests** — 30 pytest smoke tests passing in ~2s.
- ✅ **Streamlit UI** ported, ~1,900 lines decomposed across 7 modules (down from a 1,290-line monolith).
- ✅ **Documentation** — 53 Obsidian-formatted pages covering every function. See [`docs/_MOC.md`](docs/_MOC.md).

See [`docs/architecture.md`](docs/architecture.md) for the design rationale and remaining cleanup checklist.

## Layout

```
v0.5-Claude/
├── data/                   Canonical xlsx files (self-contained copy)
├── src/unitgps/engine/     Shared engine — used by every UI variant
├── apps/
│   ├── streamlit_app/      First UI target — clean port of Antigravity's app.py
│   │   ├── app.py + 6 supporting modules
│   │   └── run.bat         ← launcher (handles venv + install + launch)
│   ├── react_app/          Planned: FastAPI backend + React frontend
│   ├── htmx_app/           Planned: lightweight web variant
│   └── desktop_app/        Planned: standalone .exe (pywebview or PyQt)
├── tests/                  pytest smoke tests for the engine (5 files, 30 tests)
├── requirements/           Per-variant dependency lists
├── scripts/                Project-wide maintenance scripts (NOT per-variant launchers)
└── docs/                   Concept + reference docs (Obsidian vault)
```

## Run the Streamlit app

```bat
apps\streamlit_app\run.bat
```

That's it. The launcher:

1. Creates `.venv/` at the project root if missing.
2. Detects a stale venv (e.g. after the folder is renamed) and rebuilds it.
3. Installs `requirements/streamlit.txt` + `pip install -e .` into the venv on first run.
4. Launches `streamlit run apps/streamlit_app/app.py`.

First run takes 30–60 seconds for the install; subsequent runs start immediately.

## Run the tests

```bat
cd v0.5-Claude
.venv\Scripts\python.exe -m pytest
```

(Or, equivalently, with the venv activated: `pytest`.)

## Isolation from older generations

This folder is fully self-contained:

- Own `.venv` next to this README — not shared with `v0.4-Antigravity/` or any of `00-Legacy Versions/`.
- Own copies of the data xlsx files under `data/`.
- No imports, links, or path references to sibling generations.

To compare behavior side-by-side, run each generation from its own folder.

## Adding a UI variant

Each variant gets its own folder under `apps/` with its own `run.bat`:

| Variant | Folder | Launcher |
|---------|--------|----------|
| Streamlit | `apps/streamlit_app/` | `apps\streamlit_app\run.bat` |
| React (planned) | `apps/react_app/` | `apps\react_app\run.bat` |
| HTMX (planned) | `apps/htmx_app/` | `apps\htmx_app\run.bat` |
| Desktop (planned) | `apps/desktop_app/` | `apps\desktop_app\run.bat` |

All variants share the same `src/unitgps/engine/` package. See [`apps/README.md`](apps/README.md) for the per-variant roadmap.
