@echo off
title Install Kotak Neo Auto-Startup
cd /d "%~dp0"

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT=%STARTUP_FOLDER%\KotakNeoLiveServerPro.vbs"

echo Creating Auto-Startup shortcut in Windows Startup folder...
copy /Y "%~dp0START_SERVER_SILENT.vbs" "%SHORTCUT%" >nul

if exist "%SHORTCUT%" (
    echo.
    echo ================================================================
    echo  SUCCESS: Kotak Neo Pro is now configured to RUN ALWAYS!
    echo ================================================================
    echo  The server will now automatically start in the background
    echo  every time your computer boots or logs in.
    echo ================================================================
) else (
    echo ERROR: Could not create startup shortcut.
)
echo.
pause
