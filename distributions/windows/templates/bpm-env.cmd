@echo off
set "BPM_CONFIG=%ProgramData%\Browser Policy Manager\bpm.env"
if not exist "%BPM_CONFIG%" exit /b 0
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /R /V "^[;#]" "%BPM_CONFIG%"`) do set "%%A=%%B"
