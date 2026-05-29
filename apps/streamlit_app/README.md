# Streamlit variant

First UI build for the Claude generation. This is a clean port of the
Antigravity-era `apps/streamlit_app/app.py` (1,290 lines, all in one file),
decomposed into modules and stripped of Gemini-specific debug paths.

## Modules (planned)

| File                   | Responsibility |
|------------------------|----------------|
| `app.py`               | Thin entry point — page config, theme load, layout assembly |
| `themes.py`            | The 9-theme dict and CSS injection helpers |
| `state.py`             | `st.session_state` defaults + bi-directional sync callbacks |
| `filters.py`           | Database-filter UI + the `apply_db_and_temporal_filters` helper |
| `renderers/conversion.py` | Conversions results panel — LaTeX, Graphviz, audit |
| `renderers/emissions.py`  | GHG Emissions panel — table, stacked bar, pathway |

## Run

```bat
apps\streamlit_app\run.bat
```

`run.bat` auto-creates and maintains its own `.venv` at the project root, detects stale venvs (e.g. after the project folder is renamed), and installs Streamlit dependencies on first launch.
