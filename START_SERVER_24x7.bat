@echo off
title Kotak Neo Live Market Server Pro - 24x7 Auto-Healing Service
cd /d "%~dp0"

if not exist "data" mkdir data

:LOOP
echo [%date% %time%] Starting Kotak Neo Server... >> data\server_service.log
"%~dp0venv\Scripts\python.exe" server.py >> data\server_service.log 2>&1

echo [%date% %time%] Server process stopped. Auto-restarting in 3 seconds... >> data\server_service.log
timeout /t 3 /nobreak >nul
goto LOOP
