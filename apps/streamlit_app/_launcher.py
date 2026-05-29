"""PyInstaller entrypoint for UnitGPS.

When you build with ``pyinstaller _launcher.py``, this module becomes the
top of the bundle. Its only job: configure Streamlit and hand off to its
CLI, pointing at the bundled ``apps/streamlit_app/app.py``.

Why this exists (rather than running ``streamlit run`` directly):
PyInstaller-frozen binaries don't have a ``streamlit`` console script on
the PATH. They have *this* script as the entrypoint. We invoke Streamlit
programmatically via ``streamlit.web.cli.main()``, which accepts a
synthetic ``sys.argv`` that mimics what the user would have typed.

Two runtime modes:
- **frozen** (built exe) — ``sys._MEIPASS`` is the extracted bundle root.
  cwd gets set there so all the bundled assets (apps/, src/, data/,
  streamlit/static) are at known relative paths.
- **dev** (running ``python _launcher.py`` from source) — bundle root is
  the project root, computed via parent traversal.

Browser open: bundled apps run "headless" from Streamlit's perspective
(no auto-tab-open from the CLI), so we spin a small background thread to
open ``http://localhost:8501`` once the server should be up. Belt-and-
suspenders — if Streamlit's own browser hint also fires, the browser
just gets focused twice, no harm.
"""

from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path


_STREAMLIT_PORT = 8501


def _bundle_root() -> Path:
    """Return the directory PyInstaller extracted us into, or the dev project root."""
    if getattr(sys, "frozen", False):
        # PyInstaller sets sys._MEIPASS to the extraction directory at runtime.
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # Dev mode: this file lives at v0.5-Claude/apps/streamlit_app/_launcher.py
    # — bundle root is two parents up.
    return Path(__file__).resolve().parent.parent.parent


def _open_browser_when_ready() -> None:
    """Open the user's default browser to the Streamlit URL after a short delay."""
    # ~2s is usually enough for Streamlit's tornado server to start accepting
    # connections. If the URL isn't ready yet the browser will retry with a
    # brief "site can't be reached" flash. Acceptable trade for not polling.
    time.sleep(2.0)
    try:
        webbrowser.open(f"http://localhost:{_STREAMLIT_PORT}")
    except Exception:  # noqa: BLE001 — never break startup over a browser-open hiccup
        pass


def main() -> int:
    root = _bundle_root()

    # Ensure the bundled ``src/`` is importable so ``unitgps`` resolves the
    # same way it does in dev (where it's installed editable via ``pip -e .``).
    src_dir = root / "src"
    if src_dir.exists() and str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    app_path = root / "apps" / "streamlit_app" / "app.py"
    if not app_path.exists():
        print(f"FATAL: app.py not found at {app_path}", file=sys.stderr)
        print(f"  bundle root: {root}", file=sys.stderr)
        print(f"  contents:    {[p.name for p in root.iterdir()] if root.exists() else '(missing)'}", file=sys.stderr)
        return 1

    # Streamlit honours these env vars over CLI flags in some versions, so we
    # set both. Headless = "don't auto-open browser" (we do it ourselves).
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("STREAMLIT_SERVER_PORT", str(_STREAMLIT_PORT))

    # Background-open the browser ~2s in. Daemon so it doesn't keep the
    # process alive after the streamlit server exits.
    threading.Thread(target=_open_browser_when_ready, daemon=True).start()

    # Build a synthetic argv exactly as if the user had typed:
    #   streamlit run apps/streamlit_app/app.py --server.headless=true ...
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        f"--server.port={_STREAMLIT_PORT}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",
    ]

    # Import streamlit.web.cli lazily so this module loads even if streamlit
    # isn't present (matches the same pattern we use for matplotlib in
    # network_viz).
    try:
        from streamlit.web import cli as stcli
    except ImportError as exc:
        print(f"FATAL: streamlit unavailable in this build: {exc}", file=sys.stderr)
        return 1

    return stcli.main()  # streamlit.web.cli.main returns an exit code


if __name__ == "__main__":
    sys.exit(main())
