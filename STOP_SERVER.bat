@echo off
title Stop Kotak Neo Server & Tunnel
echo Stopping all Kotak Neo server and tunnel processes...

taskkill /F /IM cloudflared.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8787 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo Server stopped cleanly.
pause
