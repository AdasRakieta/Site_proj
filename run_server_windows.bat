@echo off
REM Run SmartHome app with Waitress (Windows)
REM Usage: double-click or run from cmd

REM Activate venv if exists
IF EXIST .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Install waitress if not present
pip show waitress >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Installing waitress...
    pip install waitress
)

REM Run the server
python -m waitress --port=5001 app_db:main
