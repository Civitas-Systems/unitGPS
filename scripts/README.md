# scripts/

Project-wide maintenance scripts only — anything that's NOT specific to one UI variant.

Per-variant launchers live alongside their code:

| To launch | Run |
|-----------|-----|
| Streamlit app | `apps\streamlit_app\run.bat` |
| (future) React app | `apps\react_app\run.bat` |
| (future) HTMX app | `apps\htmx_app\run.bat` |
| (future) Desktop app | `apps\desktop_app\run.bat` |

## What belongs here

Cross-cutting things that operate on the whole project:

- `update_data.bat` — refresh canonical xlsx files from upstream sources
- `run_tests.bat` — convenience wrapper around `pytest`
- `build_docs.bat` — if we ever generate static docs from the Obsidian markdown
- `lint.bat` — run `ruff` / `mypy` across everything

Nothing here yet — this folder is reserved for the above as they get written.
