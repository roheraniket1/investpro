@echo off
title Uninstall Kotak Neo Auto-Startup
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\KotakNeoLiveServerPro.vbs"

if exist "%SHORTCUT%" (
    del /f /q "%SHORTCUT%"
    echo Auto-Startup removed successfully.
) else (
    echo Auto-Startup shortcut was not installed.
)
pause
