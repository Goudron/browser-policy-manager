@echo off
setlocal
net session >nul 2>&1
if not "%errorlevel%"=="0" (
  echo bpm-migrate must be run from an elevated Administrator prompt. 1>&2
  exit /b 5
)
call "%~dp0bpm-env.cmd"
pushd "%~dp0"
"%~dp0venv\Scripts\python.exe" -m alembic -c "%~dp0alembic.ini" upgrade head
set "BPM_MIGRATE_RESULT=%errorlevel%"
popd
exit /b %BPM_MIGRATE_RESULT%
