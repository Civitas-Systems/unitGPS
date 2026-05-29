# React variant (placeholder)

Planned: FastAPI backend exposing the engine as a JSON API, with a React +
Vite frontend in a sibling `frontend/` folder.

Not yet scaffolded. When started, structure will be roughly:

```
react_app/
├── backend/
│   ├── main.py          FastAPI app
│   ├── routers/         /convert, /emissions, /metadata
│   └── models.py        pydantic schemas
└── frontend/
    ├── package.json
    ├── src/
    └── vite.config.ts
```
