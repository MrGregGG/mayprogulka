@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 goto failed
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed

".venv\Scripts\python.exe" manage.py migrate
if errorlevel 1 goto failed

".venv\Scripts\python.exe" manage.py load_demo_data
if errorlevel 1 goto failed

echo.
echo Setup completed successfully.
echo Next step: run create_admin_windows.bat
echo Then start the project with run_windows.bat
pause
exit /b 0

:failed
echo.
echo Setup failed. Check the error messages above.
pause
exit /b 1
