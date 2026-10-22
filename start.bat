@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo First run setup.bat to create this project's virtual environment.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" manage.py migrate --noinput
if errorlevel 1 (
    pause
    exit /b 1
)
echo Open http://127.0.0.1:8000/ in your browser.
echo Keep this window open. Press Ctrl+C to stop the server.
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000 --noreload
pause
