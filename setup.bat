@echo off
echo ============================================================
echo  Instagram Content System - Setup
echo ============================================================
echo.

:: Locate Python — check PATH first, then known install location
set PYTHON=python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    set PYTHON=C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe
    "%PYTHON%" --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo [!] Python not found in PATH. Installing via winget...
        winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
        set PYTHON=C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe
    )
)

:: Show version
%PYTHON% --version
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python not found. Please install manually:
    echo   1. Go to https://www.python.org/downloads/
    echo   2. Download Python 3.12 for Windows
    echo   3. Run installer - CHECK "Add Python to PATH"
    echo   4. Run setup.bat again
    pause
    exit /b 1
)

echo.
echo [*] Installing Python packages...
%PYTHON% -m pip install --upgrade pip -q --no-warn-script-location
%PYTHON% -m pip install anthropic Pillow -q --no-warn-script-location

echo.
echo [OK] Packages installed.
echo.

:: Validate API key
cd /d "%~dp0"
%PYTHON% -c "import json; cfg=json.load(open('config.json')); k=cfg.get('anthropic_api_key','').strip(); print('[OK] API key found.' if k else '[!] Add your Anthropic API key to config.json')"

echo.
echo ============================================================
echo  Setup complete!
echo.
echo  HOW TO RUN:
echo    %PYTHON% generate.py
echo.
echo  NEXT STEPS:
echo    1. Add your Anthropic API key to config.json
echo    2. Add your Instagram handle to config.json
echo    3. Open vault.md and add your downloads
echo    4. Run the command above
echo ============================================================
echo.

:: Save the python path for run.bat
echo @echo off > run.bat
echo cd /d "%%~dp0" >> run.bat
echo %PYTHON% generate.py %%* >> run.bat

echo [OK] Created run.bat — double-click it to start generating content.
echo.
pause
