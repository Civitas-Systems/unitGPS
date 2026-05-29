---
type: handoff
generation: Claude
date: 2026-05-29
purpose: Resume work on UnitGPS v0.5-Claude in a fresh Claude session
---

# UnitGPS v0.5-Claude — handoff

You're picking up an in-flight project. Read this first, then dive in.

## What this is

UnitGPS is a unit-conversion + GHG-emissions calculator that treats units as a directed graph and conversions as edges. Built by Dave Zelinka (`davelzelinka@gmail.com`). Multi-generation rewrite project.

- **v0.4-Antigravity** — prior generation (Google Antigravity). Single 1290-line `app.py`, hard-coded debug paths, functional but unmaintainable.
- **v0.5-Claude** — current generation (this codebase). Cleanly decomposed engine + UI, 38-test suite, 65-page Obsidian docs vault.

Project root: `D:\OneDrive\Civitas Systems\Projects\SustBrain\UnitGPS\v0.5-Claude\`

## Architecture in three sentences

1. **Engine** at `src/unitgps/engine/` — pure pandas + networkx, no Streamlit. Public surface: `DataLoader`, `UnitGraph`, `identify_conversion_path`, `calculate_conversion_factor` (with `edge_picks` parameter), `determine_conversion`, `determine_ghg_emissions`. 38 pytest tests passing.
2. **Streamlit UI** at `apps/streamlit_app/` — decomposed across 10 modules: `app.py` (thin orchestrator), `themes.py` (13 themes with WCAG-verified contrast), `state.py`, `filters.py`, `formatting.py`, `export.py`, `url_state.py`, `network_viz.py`, and `renderers/{conversion,emissions,stepper}.py`. Plus `_launcher.py` for PyInstaller bundling.
3. **Docs** at `docs/` — 65-page Obsidian vault. Concept pages, per-function reference pages, Glossary, MOC, architecture.md, CHANGELOG. All [[wiki-links]] resolve. Open in Obsidian for navigable view.

## Current state — what's already done

Seven completed "passes" of polish. Newest first (full detail in `docs/CHANGELOG.md`):

- **Pass 7 — Network visualization.** Ported the v0.4-Antigravity matplotlib + NetworkX visualization toolkit into `apps/streamlit_app/network_viz.py`. "🌐 Show network view" expanders on both result panels.
- **Pass 6 — Portable results.** JSON + Markdown export buttons (`export.py`), URL state persistence via `st.query_params` (`url_state.py`), "🔗 Share link" popover.
- **Pass 5 — Polish.** Dead-code removal, edge-picker label sharpening (shows "EPA · 2025 · Anthracite" instead of "#2"), Glossary refresh, architecture refresh, CHANGELOG.
- **Pass 4 — Docs.** Concept pages, reference pages, Obsidian frontmatter, MOC update.
- **Pass 3 — Themes.** WCAG audit + 4 light/dark variants added (9 → 13 themes).
- **Pass 2 — Path control.** `edge_picks` parameter end-to-end (engine + wrappers + tests + sticky picker UI + path tabs + comparison table).
- **Pass 1 + 1.5 — Visual overhaul.** Hybrid audit card, hero pathway stepper, GHG condensed panel, CSS-specificity fix for Streamlit 1.57 (the load-bearing fix that made everything start to look right).

## What's in flight RIGHT NOW

**Pass 8 — Standalone PyInstaller .exe.** Goal: produce `dist\UnitGPS\UnitGPS.exe` that runs on any Windows machine with no Python install. Three files exist:

- `apps/streamlit_app/_launcher.py` — PyInstaller entrypoint, handles `sys._MEIPASS` extraction-dir, programmatically invokes `streamlit.web.cli.main()`, opens browser.
- `scripts/build_exe.bat` — one-button build. Just patched a `for /f` bug that broke on OneDrive paths (cmd parses `D:\OneDrive\Civitas Systems\...` poorly inside nested for loops); now constructs streamlit's path directly from venv layout.
- `apps/streamlit_app/BUILD.md` — full build guide with onedir/onefile trade-offs, known Streamlit + PyInstaller gotchas.

**Immediate next step:** Dave runs `scripts\build_exe.bat` from project root. Last attempt failed at the streamlit-path-detection step (fixed now). Expect the build to take 3–5 minutes and produce ~300MB output. May hit additional Streamlit-specific `--hidden-import` issues on first build — those get added to the build script flag soup as they come up.

## Workspace conventions (critical to know)

### OneDrive Write/Edit truncation

**Editing files with the Write or Edit tool sometimes silently truncates the end** when the file is large (>5KB) or the edit grows it by more than ~5 lines. Symptoms: file looks normal, parses fine for a moment, but the tail is missing.

- For substantial edits or new files, use bash heredocs: `cat > "$DEST" <<'EOF'\n...\nEOF`
- After any Write/Edit, verify with `wc -l` + `tail -3` and `py_compile`
- If truncated, recover by appending the missing tail via `cat >> "$DEST"`

This bit me ~6 times during this session. The bash-heredoc-first pattern is much more reliable. See `memory/onedrive_write_truncation.md`.

### Python version

Dave's machine defaults to Python 3.14.4 (he previously had 3.12). Most wheels exist but some packaging tools may complain. The venv lives at `<project_root>\.venv\` and is created by `apps\streamlit_app\run.bat`.

### Bash vs Windows paths

- Working in this sandbox: paths are `/sessions/wonderful-bold-euler/mnt/SustBrain/UnitGPS/v0.5-Claude/...`
- Dave's actual paths: `D:\OneDrive\Civitas Systems\Projects\SustBrain\UnitGPS\v0.5-Claude\...`
- File tools (Read/Write/Edit) use Dave's Windows paths; Bash uses sandbox paths.

### Verification commands

```bash
# Tests (run from /tmp/pytest_workdir to avoid OneDrive lock issues)
mkdir -p /tmp/pytest_workdir && cd /tmp/pytest_workdir
python -m pytest "/sessions/wonderful-bold-euler/mnt/SustBrain/UnitGPS/v0.5-Claude/tests" --rootdir=/tmp/pytest_workdir -q
# Expected: 38 passed

# UI module imports (run from project root)
cd /sessions/wonderful-bold-euler/mnt/SustBrain/UnitGPS/v0.5-Claude && find apps src -name __pycache__ -exec rm -rf {} + 2>/dev/null
python -c "
import sys, types
fake_st = types.ModuleType('streamlit')
fake_st.markdown = lambda *a, **k: None
fake_st.session_state = {}
fake_st.query_params = {}
def cache_resource(func=None, **kwargs):
    if func is None: return lambda f: f
    return func
fake_st.cache_resource = cache_resource
sys.modules['streamlit'] = fake_st
sys.path.insert(0, 'src')
sys.path.insert(0, 'apps')
from streamlit_app import network_viz, formatting, themes, state, filters, export, url_state
from streamlit_app.renderers import conversion, emissions, stepper
print('all 10 UI modules import OK')
"
```

## Where to look for full context

- **`docs/CHANGELOG.md`** — pass-by-pass record from initial build through Pass 8. Read this before doing anything new.
- **`docs/architecture.md`** — design decisions + "Notable post-rewrite decisions" section explaining the CSS specificity hack, the GHG bar-vs-donut reasoning, edge-pick semantics, etc.
- **`docs/_MOC.md`** — index of all 65 doc pages. Hit this in Obsidian for navigation.
- **`docs/Glossary.md`** — 50+ defined terms.
- **`docs/Concepts/`** — 12 pages explaining the load-bearing abstractions (Unit graph, Ambiguous paths, Edge picks, Hero pathway stepper, etc.).
- **Auto-memory at** `C:\Users\davel\AppData\Roaming\Claude\local-agent-mode-sessions\.../memory/` — carries between sessions in Cowork mode. Includes notes on OneDrive truncation, venv relocatability, Python 3.12 default, the v4 connector pattern.

## Dave's working style

- Decisive — picks from options quickly, doesn't want long deliberation.
- Visual-first — responds best to mockups + screenshots.
- Iterates fast and reverses cleanly. "Keep improving" / "what's best now" means "pick something high-leverage and go."
- Wants the app to feel "modern, sleek, not weird, not vibe-cody." Tight horizontal layouts. Real typography hierarchy. Visible-but-quiet borders.
- Will revisit polish items as they come up rather than fixing everything in one shot.

## How to resume

1. Run the verification commands above. Confirm 38/38 tests and 10/10 UI imports.
2. Check `docs/CHANGELOG.md` for the latest Pass entries.
3. Ask Dave where to pick up. If he says "continue from where you left off," the answer is **Pass 8 PyInstaller build** — run `scripts\build_exe.bat` on his machine, debug any new hidden-import errors that surface, iterate on the build flags until a working `dist\UnitGPS\UnitGPS.exe` exists.
4. If he points at something specific in the UI as broken or unfinished, prioritize that.

If you need broader context, the system prompt for the current session also includes the auto-memory files (see `memory/MEMORY.md` index). Those carry over automatically in Cowork mode but not in a fresh claude.ai chat.
