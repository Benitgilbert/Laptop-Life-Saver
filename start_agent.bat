@echo off
echo Starting Laptop Life-Saver Agent...
:: Determine script directory
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

:: Check for virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo Error: Virtual environment (.venv) not found.
    echo Please create it first using: python -m venv .venv
    pause
    exit /b
)

:: Run the agent as a module
.venv\Scripts\python.exe -m agent.agent
pause
