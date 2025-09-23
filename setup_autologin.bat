@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_PATH=%SCRIPT_DIR%campnet_autologin.py"
set "RUN_KEY=HKCU\Software\Microsoft\Windows\CurrentVersion\Run"
set "RUN_VALUE=CampnetAutoLogin"

if not exist "%SCRIPT_PATH%" (
    echo [campnet-autologin] campnet_autologin.py not found next to this script.
    exit /b 1
)

if /I "%~1"=="--remove" (
    reg delete "%RUN_KEY%" /v "%RUN_VALUE%" /f >nul 2>&1
    if errorlevel 1 (
        echo [campnet-autologin] Autostart entry not found in registry.
    ) else (
        echo [campnet-autologin] Autostart entry removed from registry.
    )
    exit /b 0
)

call :find_python || exit /b 1

set "RUN_CMD=\"%PYTHON_CMD%\" \"%SCRIPT_PATH%\""
reg add "%RUN_KEY%" /v "%RUN_VALUE%" /t REG_SZ /d "%RUN_CMD%" /f >nul 2>&1
if errorlevel 1 (
    echo [campnet-autologin] Failed to register startup entry. Try running as the logged-in user.
) else (
    echo [campnet-autologin] Startup entry written to registry.
)

start "" "%PYTHON_CMD%" "%SCRIPT_PATH%"
if errorlevel 1 (
    echo [campnet-autologin] Warning: could not start watcher immediately; it will still launch on next sign-in.
    exit /b 0
)

echo [campnet-autologin] campnet_autologin.py running via %PY_LABEL%.
if /I "%PY_LABEL%"=="python" (
    echo [campnet-autologin] (A console window may remain open.)
)
exit /b 0

:find_python
for /f "delims=" %%I in ('where pythonw.exe 2^>nul') do (
    set "PYTHON_CMD=%%I"
    set "PY_LABEL=pythonw"
    goto fp_done
)

for /f "delims=" %%I in ('where python.exe 2^>nul') do (
    set "PYTHON_CMD=%%I"
    set "PY_LABEL=python"
    goto fp_done
)

echo [campnet-autologin] Python executable not found on PATH.
exit /b 1

:fp_done
exit /b 0
