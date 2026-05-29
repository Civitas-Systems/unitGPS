# Building a standalone UnitGPS.exe

How to produce a portable Windows executable of the Streamlit app that you can
copy to any Windows machine — **no Python install required on the target**.

## TL;DR — three steps

From a PowerShell or cmd window in the project root:

```bat
scripts\build_exe.bat
```

That's it. After ~3–5 minutes:

```
v0.5-Claude\dist\UnitGPS\
├── UnitGPS.exe          ← double-click this
├── _internal\           ← bundled Python + libs + assets
└── ...
```

To distribute:

1. **Right-click the `dist\UnitGPS` folder → Send to → Compressed (zipped) folder.**
2. Send the resulting `UnitGPS.zip` to whoever needs it.
3. On the target machine: unzip, open the `UnitGPS` folder, double-click `UnitGPS.exe`. A browser window opens at `http://localhost:8501` after ~3 seconds.

## What gets built

`build_exe.bat` produces **onedir** mode by default — a folder containing
`UnitGPS.exe` plus everything it needs in `_internal\`. The folder is
~300–400 MB.

To also produce a **single-file** `.exe` (one literal file, no folder), run:

```bat
scripts\build_exe.bat --onefile
```

You'll get `dist\UnitGPS_onefile.exe` in addition to the onedir build.

### Onedir vs onefile trade-offs

| Aspect | Onedir (default) | Onefile |
|--------|------------------|---------|
| Distribution unit | A folder (zip it to share) | A single `.exe` |
| Cold start | ~2–3 sec | ~8–15 sec (extracts to %TEMP% each launch) |
| Disk usage on target | ~300 MB folder | ~300 MB .exe + ~300 MB in %TEMP% per launch |
| Antivirus heuristics | Folder of files = boring | Single self-extracting binary = sometimes flagged |
| Recommended for | Daily use, internal sharing | Email attachment, one-off demo |

**Most users want onedir.** The single-file build is convenient for
specific scenarios but you pay a real cold-start penalty every launch.

## Inside the build

The build script (`scripts\build_exe.bat`) does five things:

1. **Ensures the dev venv exists** with all UI deps. Reuses the same
   import-check logic as `apps\streamlit_app\run.bat` — won't reinstall
   unnecessarily.
2. **Adds PyInstaller** to the venv if not already there. Kept out of
   `requirements\streamlit.txt` so the runtime venv stays lean.
3. **Locates Streamlit's package directory.** PyInstaller can find Python
   modules via imports, but Streamlit ships HTML/JS/font assets as *loose
   files* that need explicit `--add-data` paths.
4. **Cleans previous build artifacts** (`build\`, `dist\`, `UnitGPS.spec`)
   so each run starts from a known state.
5. **Runs PyInstaller** with the entrypoint `apps\streamlit_app\_launcher.py`
   and the flag soup needed for Streamlit + matplotlib + plotly + networkx
   to all import correctly inside the bundled binary.

### The launcher entrypoint

`apps\streamlit_app\_launcher.py` is the only thing PyInstaller sees as
a "main" — it figures out where the bundle was extracted, sets up
`sys.path`, configures Streamlit's environment, programmatically invokes
`streamlit.web.cli.main()` pointed at the bundled `app.py`, and spins a
background thread to open the user's browser after ~2 seconds.

The launcher works identically in dev mode (`python _launcher.py`) and
bundled mode (sys.frozen detection switches the bundle-root computation).

## Known Streamlit + PyInstaller gotchas

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'streamlit.runtime.scriptrunner.magic_funcs'` | PyInstaller missed a dynamic import | Already included as `--hidden-import`. If it shows up for a different module, add the same flag. |
| App launches but white page in browser | Streamlit's static assets not bundled | `--add-data "%STREAMLIT_PKG%\static;streamlit\static"` (already in the build script). |
| Windows Defender flags the exe | Self-extracting binaries trigger heuristics on first-build, fresh-from-pyinstaller exes | Either (a) sign the binary with a code-signing certificate, (b) add an exclusion locally, (c) use onedir mode (less likely to be flagged). |
| `matplotlib.colors` ImportError at runtime | `--collect-all matplotlib` was skipped | Already in the build script. |
| Engine errors about missing `data/Data Library, ...xlsx` | The `data/` folder wasn't bundled | `--add-data "data;data"` (already in the build script). |

## Updating the exe

After any code change, just re-run `scripts\build_exe.bat`. PyInstaller
will produce a fresh `dist\UnitGPS\`. Zip and redistribute.

## Cross-platform note

This build is **Windows-only**. PyInstaller produces native binaries for
the OS it runs on — to produce a Mac or Linux build, you'd need to run
`build_exe.bat`'s equivalent shell script on that target OS. We haven't
written those yet; the project's only deployment target so far is Windows.
