@echo off
setlocal
call "%~dp0bpm-env.cmd"
"%~dp0venv\Scripts\python.exe" -m uvicorn app.main:app --host "%BPM_HOST%" --port "%BPM_PORT%"
exit /b %errorlevel%
