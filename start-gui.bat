@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-gui.ps1"
set "launch_exit=%ERRORLEVEL%"
if not "%launch_exit%"=="0" (
    echo.
    echo Outbreak Web Bridge could not start. Review the error above.
    pause
)
exit /b %launch_exit%
