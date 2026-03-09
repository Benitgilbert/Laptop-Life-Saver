@echo off
setlocal enabledelayedexpansion
echo Starting Laptop Life-Saver Agent...

:: Ensure we are in the script directory
cd /d "%~dp0"

:: Check for virtual environment without complex IF blocks
if not exist .venv\Scripts\python.exe goto :no_venv

:: Run the agent in background mode (no window)
start /b "" .venv\Scripts\pythonw.exe -m agent.agent
echo Agent started in background. Check the system tray icon.
timeout /t 3
exit /b

:no_venv
echo Error: Virtual environment (.venv) not found.
echo Please create it first using: python -m venv .venv
pause
exit /b
