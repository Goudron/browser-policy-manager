@echo off
setlocal
call "%~dp0bpm-env.cmd"
if /I "%~1"=="serve" (
  shift
  "%~dp0venv\Scripts\python.exe" -m uvicorn app.main:app --host "%BPM_HOST%" --port "%BPM_PORT%" %*
  exit /b %errorlevel%
)
if /I "%~1"=="migrate" (
  call "%~dp0bpm-migrate.cmd"
  exit /b %errorlevel%
)
if /I "%~1"=="version" (
  "%~dp0venv\Scripts\python.exe" -I -c "from importlib.metadata import version; print(version('browser-policy-manager'))"
  exit /b %errorlevel%
)
echo Usage: bpm {serve^|migrate^|version} 1>&2
exit /b 64
