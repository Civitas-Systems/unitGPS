@echo off
REM -----------------------------------------------------------------------
REM build_exe.bat — produce a standalone UnitGPS.exe via PyInstaller.
REM
REM Output:
REM   dist\UnitGPS\UnitGPS.exe           (onedir — faster cold start, ~300MB folder)
REM   dist\UnitGPS_onefile\UnitGPS.exe   (onefile — one .exe, ~300MB, slow cold start)
REM
REM Either output is fully portable: copy/zip and double-click on any
REM Windows machine. The target machine needs NO Python installed.
REM -----------------------------------------------------------------------

setlocal
pushd "%~dp0\.."

set "PROJECT_ROOT=%CD%"
set "VENV_DIR=%PROJECT_ROOT%\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

REM -----------------------------------------------------------------------
REM Step 1: Make sure the dev venv exists and has all UI deps installed.
REM Reuses run.bat's setup logic — if the venv already imports the full
REM UI stack, we skip the install and just add pyinstaller.
REM -----------------------------------------------------------------------
if not exist "%VENV_PY%" (
    echo [build] Creating venv ...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [build] ERROR: failed to create venv. Is Python on your PATH?
        popd & exit /b 1
    )
)

"%VENV_PY%" -c "import unitgps, streamlit, pandas, networkx, matplotlib, plotly, openpyxl" >nul 2>&1
if errorlevel 1 (
    echo [build] Installing UI deps into venv ...
    "%VENV_PY%" -m pip install --upgrade pip --quiet --no-warn-script-location
    "%VENV_PY%" -m pip install -r requirements\streamlit.txt --quiet --no-warn-script-location
    "%VENV_PY%" -m pip install -e . --quiet --no-warn-script-location
)

REM Always ensure pyinstaller is present (it's not in streamlit.txt to
REM keep the runtime venv lean).
"%VENV_PY%" -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [build] Installing PyInstaller ...
    "%VENV_PY%" -m pip install "pyinstaller>=6.0" --quiet --no-warn-script-location
)

REM -----------------------------------------------------------------------
REM Step 2: Locate Streamlit's static-asset directory.
REM
REM Windows venv layout puts every site package at a known path, so we
REM construct it directly rather than asking Python (cmd's `for /f` loop
REM can't reliably parse output of commands with spaces in their args,
REM and OneDrive paths always have spaces).
REM -----------------------------------------------------------------------
set "STREAMLIT_PKG=%VENV_DIR%\Lib\site-packages\streamlit"
if not exist "%STREAMLIT_PKG%\__init__.py" (
    echo [build] ERROR: streamlit not found at %STREAMLIT_PKG%
    echo         The venv might not have UI deps installed. Try deleting
    echo         the .venv folder and re-running scripts\build_exe.bat to
    echo         force a fresh install.
    popd & exit /b 1
)
echo [build] Streamlit package at: %STREAMLIT_PKG%

REM -----------------------------------------------------------------------
REM Step 3: Clean previous build artifacts. Optional — comment out if you
REM want PyInstaller's incremental build cache to speed things up.
REM -----------------------------------------------------------------------
echo [build] Cleaning previous build artifacts ...
if exist "build"             rmdir /s /q "build"
if exist "dist"              rmdir /s /q "dist"
if exist "UnitGPS.spec"      del /q "UnitGPS.spec"

REM -----------------------------------------------------------------------
REM Step 4: Run PyInstaller (onedir mode — preferred default).
REM
REM Why onedir over onefile:
REM   - onefile extracts the entire bundle to %TEMP% on every launch
REM     (~5-10s cold start, doubles disk I/O)
REM   - onedir launches instantly (everything's already extracted)
REM   - You distribute the whole 'UnitGPS' folder either way — zip it
REM     and ship it; the user unzips and double-clicks UnitGPS.exe
REM -----------------------------------------------------------------------
echo [build] Running PyInstaller (onedir mode) ...
"%VENV_PY%" -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --name UnitGPS ^
    --add-data "apps;apps" ^
    --add-data "src;src" ^
    --add-data "data;data" ^
    --add-data "%STREAMLIT_PKG%\static;streamlit\static" ^
    --add-data "%STREAMLIT_PKG%\runtime;streamlit\runtime" ^
    --collect-all streamlit ^
    --collect-all altair ^
    --collect-all matplotlib ^
    --collect-all plotly ^
    --collect-all networkx ^
    --collect-all openpyxl ^
    --collect-all pyarrow ^
    --collect-submodules pandas ^
    --hidden-import streamlit.web.cli ^
    --hidden-import streamlit.runtime.scriptrunner.magic_funcs ^
    --hidden-import streamlit.runtime.caching ^
    apps\streamlit_app\_launcher.py

if errorlevel 1 (
    echo.
    echo [build] ERROR: PyInstaller failed. Common fixes:
    echo   - Missing hidden imports — run again with --debug=imports to find them
    echo   - Streamlit version mismatch — pip install --upgrade streamlit
    echo   - Antivirus blocking — temporarily disable real-time scanning
    popd & exit /b 1
)

echo.
echo [build] SUCCESS. Output: %PROJECT_ROOT%\dist\UnitGPS\UnitGPS.exe
echo.
echo To distribute:
echo   1. ZIP the entire dist\UnitGPS folder
echo   2. Send the .zip to the target machine
echo   3. Recipient unzips and double-clicks UnitGPS.exe
echo.
echo To also build a single-file .exe (slower cold start), run:
echo   build_exe.bat --onefile
echo.

REM -----------------------------------------------------------------------
REM Step 5 (optional): If --onefile flag passed, also produce the
REM single-file variant alongside.
REM -----------------------------------------------------------------------
if "%~1"=="--onefile" (
    echo [build] Also building --onefile variant ...
    "%VENV_PY%" -m PyInstaller ^
        --noconfirm ^
        --onefile ^
        --name UnitGPS_onefile ^
        --add-data "apps;apps" ^
        --add-data "src;src" ^
        --add-data "data;data" ^
        --add-data "%STREAMLIT_PKG%\static;streamlit\static" ^
        --add-data "%STREAMLIT_PKG%\runtime;streamlit\runtime" ^
        --collect-all streamlit ^
        --collect-all altair ^
        --collect-all matplotlib ^
        --collect-all plotly ^
        --collect-all networkx ^
        --collect-all openpyxl ^
        --collect-all pyarrow ^
        --collect-submodules pandas ^
        --hidden-import streamlit.web.cli ^
        --hidden-import streamlit.runtime.scriptrunner.magic_funcs ^
        --hidden-import streamlit.runtime.caching ^
        apps\streamlit_app\_launcher.py
    echo [build] Onefile output: %PROJECT_ROOT%\dist\UnitGPS_onefile.exe
)

popd
endlocal
