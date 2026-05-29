# UnitGPS UI variants

Each subfolder is one user-facing build of UnitGPS. They all import from
`src/unitgps/engine` — the engine is the single source of truth for
data loading, graph construction, pathfinding, and emissions math.

| Variant         | Stack                       | Status        | Purpose |
|-----------------|-----------------------------|---------------|---------|
| `streamlit_app` | Streamlit + Plotly          | First target  | Clean port of Antigravity's app.py, decomposed into modules |
| `react_app`     | FastAPI + React (Vite)      | Placeholder   | Modern web stack — engine exposed as REST API, custom frontend |
| `htmx_app`      | FastAPI + HTMX + Jinja      | Placeholder   | Lightweight server-rendered web variant |
| `desktop_app`   | pywebview (or PyQt)         | Placeholder   | Standalone .exe — wraps the web UI in a native window |

## Adding a new variant

1. Create a sibling folder under `apps/`.
2. Add a `README.md` describing the stack and how to run it.
3. Add the dependencies to `requirements/<variant>.txt`.
4. Import only from `unitgps.engine` — never duplicate engine logic.
