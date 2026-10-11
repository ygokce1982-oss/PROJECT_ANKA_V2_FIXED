@echo off
setlocal
set "ANKA_OFFLINE=1"
set "ANKA_DISABLE_LIVE=1"
set "PYTHONUTF8=1"
cd /d "%~dp0"
set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if not exist "%PYTHON%" (
  echo ANKA Finans: Python 3.14 bulunamadi.
  pause
  exit /b 2
)
"%PYTHON%" -B "%~dp0app.py"
if errorlevel 1 (
  echo ANKA Finans baslatma hatasi.
  pause
)
endlocal
