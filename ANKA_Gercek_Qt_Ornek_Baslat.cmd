@echo off
setlocal
set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
set "PYTHONUTF8=1"
set "QT_QPA_PLATFORM=windows"
cd /d "%~dp0"
if not exist "%PYTHON%" (
 echo Python 3.14 bulunamadi.
 pause
 exit /b 2
)
"%PYTHON%" -B "scripts\anka_professional_toolchain_demo.py"
if errorlevel 1 (
 echo ANKA Finans Qt demo baslatilamadi.
 pause
)
endlocal
