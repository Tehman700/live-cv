@echo off
:: Registers the CV watcher to start automatically at Windows login.
:: Run this file ONCE as Administrator.

set SCRIPT="%~dp0watch.py"
set PYTHONW=pythonw.exe
set TASKNAME=CV Auto-Deploy Watcher

echo Registering CV watcher to start at login...

schtasks /create ^
  /tn "%TASKNAME%" ^
  /tr "%PYTHONW% %SCRIPT%" ^
  /sc ONLOGON ^
  /rl HIGHEST ^
  /f

if %errorlevel% == 0 (
    echo.
    echo Done! The watcher will now start automatically every time you log in.
    echo It runs silently in the background — check watcher.log to see its activity.
    echo.
    echo To start it right now without restarting, run:
    echo   pythonw "%~dp0watch.py"
    echo.
) else (
    echo.
    echo Failed to register. Try right-clicking this file and choosing "Run as Administrator".
)

pause
