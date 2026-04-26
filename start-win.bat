@echo off

set VENV_DIR=.venv

:: check for python installation

python --version 2>NUL
cls
if errorlevel 1 goto noPython

:: venv/install

IF NOT EXIST "%VENV_DIR%\Scripts\activate.bat" (
    echo.Creating virtual environment...
    echo.

    python -m venv "%VENV_DIR%"
)

:: update

echo.Installing Dependencies...
echo.

"%VENV_DIR%\Scripts\python.exe" -m pip install -U pip
"%VENV_DIR%\Scripts\pip.exe" install -r "requirements.txt"

cls
echo.Starting server...
echo.(Press CTRL+C to Stop)

"%VENV_DIR%\Scripts\python.exe" -m streamlit run "main.py"

cls
echo.Server stopped.
echo.
pause
exit

:: alert to install python

:noPython

echo.Please install Python at the link below, then run this file again.
echo.https://www.python.org/downloads/
echo.
pause
exit