@echo off
REM Skrypt uruchamiający Smart Home Server na Windows
REM Użycie: run_server.bat [--debug] [--port NUMER_PORTU]

echo === Smart Home Server - Windows ===
echo Uruchamianie serwera...

REM Sprawdź czy środowisko wirtualne istnieje
if exist ".venv\Scripts\python.exe" (
    echo Używam środowiska wirtualnego
    .venv\Scripts\python.exe run_server.py %*
) else (
    echo Używam systemowego Python
    python run_server.py %*
)

pause
