# Deploying UnitGPS to Streamlit Community Cloud

A step-by-step guide to putting the app online for free. No server admin required —
Streamlit Community Cloud builds and hosts directly from your GitHub repo.

## What you get

A public URL like `https://unitgps.streamlit.app` that runs `apps/streamlit_app/app.py`,
rebuilds automatically every time you push to `main`, and costs nothing on the
Community tier.

## Before you start — the repo is already deploy-ready

These were prepared so the deploy "just works":

- **`requirements.txt`** at the repo root lists the runtime dependencies (Streamlit,
  pandas, networkx, plotly, matplotlib, openpyxl, pyarrow). Streamlit Cloud installs
  from this automatically.
- **Data files are committed** under `data/` and loaded by a `__file__`-relative path,
  so the cloud container finds them with no configuration.
- **No secrets or environment variables are needed** — the app reads only the bundled
  xlsx files.
- **`.streamlit/config.toml`** sets the initial dark theme so there's no flash on load.
- The app **bootstraps its own import path** (`src/` and `apps/` are added to
  `sys.path` at startup), so the package does not need to be pip-installed.

## Steps

1. **Make the GitHub repo public.**
   On `https://github.com/DaveLZelinka/UnitGPS` → **Settings** → scroll to
   **Danger Zone** → **Change repository visibility** → **Make public** → confirm.
   (Community Cloud's free tier requires a public repo.)

2. **Make sure `main` is fully pushed.**
   In your terminal:
   ```
   cd "D:\OneDrive\Civitas Systems\Projects\SustBrain\UnitGPS\v0.5-Claude"
   git push
   ```
   (If the `.git/objects … (y/n)` prompt appears, type `n`.)

3. **Sign in to Streamlit Community Cloud.**
   Go to `https://share.streamlit.io` and **Sign in with GitHub**. Authorize it to
   see your repositories when prompted.

4. **Create the app.**
   Click **Create app** (or **New app**) → **Deploy a public app from GitHub**, then set:
   - **Repository:** `DaveLZelinka/UnitGPS`
   - **Branch:** `main`
   - **Main file path:** `apps/streamlit_app/app.py`
   - **App URL:** pick your subdomain (e.g. `unitgps`).

5. **Click Deploy.**
   The first build takes a few minutes while it installs the dependencies. When it
   finishes you'll land on the live app.

## Updating the live app

Just push to `main` — Community Cloud detects the push and redeploys automatically:
```
git add -A
git commit -m "your change"
git push
```
No redeploy button needed.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `ModuleNotFoundError: No module named 'X'` | `X` is missing from `requirements.txt`. Add it, commit, push. |
| `FileNotFoundError` for a `.xlsx` | The data file wasn't committed. Confirm `data/*.xlsx` shows in the GitHub repo. |
| App boots then shows a blank theme | The native theme loaded before the app's CSS — harmless, it resolves on the first interaction. |
| "Oh no. Error running app." | Open **Manage app → Logs** (bottom-right of the live app) to see the Python traceback. |
| Slow first load | Cold start + the one-time graph build (~3,600 edges). Subsequent loads are cached and fast. |
| App "goes to sleep" | Community-tier apps sleep after inactivity; the first visitor wakes it in a few seconds. |

## Resource notes

The free tier provides ~1 GB RAM. UnitGPS loads a ~330 KB data file and builds an
in-memory graph of a few thousand edges (cached once per session via
`@st.cache_resource`), so it sits comfortably within the limit.

## Custom domain (optional, later)

Community Cloud serves from `*.streamlit.app`. For a custom domain you'd move to a
host that supports it (e.g. a small container on Render/Railway/Fly.io running
`streamlit run apps/streamlit_app/app.py`). Not needed to go live.
