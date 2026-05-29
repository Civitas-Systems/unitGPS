@echo off
REM Launch the Streamlit variant of UnitGPS.
REM
REM Health-check strategy: if the venv's python can `import unitgps`, the venv
REM is good — launch immediately. Only set up / rebuild if that fails. Avoids
REM the OneDrive reparse-point path-mismatch issue that an earlier sys.prefix
REM check ran into.

setlocal
REM This script lives at <PROJECT_ROOT>\apps\streamlit_app\run.bat
pushd "%~dp0\..\.."

set "PROJECT_ROOT=%CD%"
set "VENV_DIR=%PROJECT_ROOT%\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "VENV_STREAMLIT=%VENV_DIR%\Scripts\streamlit.exe"

REM ---------------------------------------------------------------
REM Step 1: Fast path — venv exists AND all required modules import.
REM
REM We check every top-level UI dependency so that adding a new module to
REM requirements\streamlit.txt actually triggers a reinstall on next launch
REM (rather than silently leaving the venv stale). If any one of these
REM imports fails, we fall through to the install step below.
REM ---------------------------------------------------------------
if exist "%VENV_PY%" (
    "%VENV_PY%" -c "import unitgps, streamlit, pandas, networkx, matplotlib, plotly, openpyxl" >nul 2>&1
    if not errorlevel 1 goto :LAUNCH
)

REM ---------------------------------------------------------------
REM Step 2: Need setup. Create venv if it doesn't have a python.exe.
REM ---------------------------------------------------------------
if not exist "%VENV_PY%" (
    if exist "%VENV_DIR%" (
        echo [setup] Removing incomplete .venv ...
        rmdir /s /q "%VENV_DIR%"
    )
    echo [setup] Creating virtual environment in .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [setup] ERROR: failed to create venv. Is Python on your PATH?
        popd
        exit /b 1
    )
)

REM ---------------------------------------------------------------
REM Step 3: Install dependencies into the venv
REM ---------------------------------------------------------------
echo [setup] Installing UnitGPS engine and Streamlit dependencies ...
"%VENV_PY%" -m pip install --upgrade pip --quiet --no-warn-script-location
"%VENV_PY%" -m pip install -r requirements\streamlit.txt --quiet --no-warn-script-location
"%VENV_PY%" -m pip install -e . --quiet --no-warn-script-location

REM ---------------------------------------------------------------
REM Step 4: Verify install. If it failed, the existing venv may be
REM unusable (e.g. stale paths inside it). Wipe and try once more.
REM ---------------------------------------------------------------
"%VENV_PY%" -c "import unitgps, streamlit, pandas, networkx, matplotlib, plotly, openpyxl" >nul 2>&1
if errorlevel 1 (
    echo [setup] Install didn't take in existing .venv — rebuilding from scratch ...
    rmdir /s /q "%VENV_DIR%"
    python -m venv .venv
    if errorlevel 1 (
        echo [setup] ERROR: failed to rebuild venv.
        popd
        exit /b 1
    )
    "%VENV_PY%" -m pip install --upgrade pip --quiet --no-warn-script-location
    "%VENV_PY%" -m pip install -r requirements\streamlit.txt --quiet --no-warn-script-location
    "%VENV_PY%" -m pip install -e . --quiet --no-warn-script-location

    "%VENV_PY%" -c "import unitgps, streamlit, pandas, networkx, matplotlib, plotly, openpyxl" >nul 2>&1
    if errorlevel 1 (
        echo [setup] ERROR: required modules still not importable after rebuild.
        popd
        exit /b 1
    )
)

:LAUNCH
echo Starting UnitGPS Streamlit ...
"%VENV_STREAMLIT%" run apps\streamlit_app\app.py

popd
endlocal
