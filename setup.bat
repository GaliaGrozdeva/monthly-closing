@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3.13 -m venv .venv
    if errorlevel 1 goto fail
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
".venv\Scripts\python.exe" manage.py migrate
if errorlevel 1 goto fail
".venv\Scripts\python.exe" manage.py check
if errorlevel 1 goto fail
echo Setup completed. Run start.bat to open the application.
pause
exit /b 0
:fail
echo Setup failed. Read the error above. Python 3.13 must be installed.
pause
exit /b 1
