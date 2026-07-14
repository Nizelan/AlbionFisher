@echo off
rem AlbionFisher launcher — double-click to run.
rem Creates the venv and installs dependencies on first run.

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python not found. Install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo First run: creating virtual environment...
    python -m venv .venv || goto :fail
)

".venv\Scripts\python.exe" -c "import PySide6" >nul 2>nul
if errorlevel 1 (
    echo First run: installing dependencies ^(several minutes, torch is large^)...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :fail
)

".venv\Scripts\python.exe" -m albionfisher
exit /b %errorlevel%

:fail
echo.
echo Setup failed — see errors above.
pause
exit /b 1
