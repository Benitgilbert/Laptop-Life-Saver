@echo off
setlocal enabledelayedexpansion
echo Starting Laptop Life-Saver Agent...

:: Ensure we are in the script directory
cd /d "%~dp0"

:: Check for virtual environment without complex IF blocks
if not exist .venv\Scripts\python.exe goto :no_venv

:: Run the agent
.venv\Scripts\python.exe -m agent.agent
pause
exit /b

:no_venv
echo Error: Virtual environment (.venv) not found.
echo Please create it first using: python -m venv .venv
pause
exit /b
