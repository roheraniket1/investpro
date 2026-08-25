@echo off
title Kotak Neo Live Market Server Pro
color 0A

echo ============================================================
echo    Kotak Neo Live Market Server Pro
echo    Starting Server...
echo ============================================================
echo.

cd /d "%~dp0"

:: Use venv Python directly
set PYTHON=%~dp0venv\Scripts\python.exe

if not exist "%PYTHON%" (
    echo [!] Virtual environment not found!
    echo [!] Please create one first: python -m venv venv
    pause
    exit /b 1
)

echo [*] Using Python: %PYTHON%
echo.
echo ============================================================
echo    Server starting on http://localhost:8787
echo    Dashboard: http://localhost:8787
echo    Press Ctrl+C to stop
echo ============================================================
echo.

:: Open browser after 3 seconds
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8787"

:: Start the server
"%PYTHON%" server.py

:: If server stops, keep window open
echo.
echo [!] Server stopped. Press any key to exit...
pause >nul
