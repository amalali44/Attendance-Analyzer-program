@echo off
REM Training Attendance Analyzer - Windows Launcher
REM Double-click this file to run the application

title Training Attendance Analyzer

echo.
echo ============================================================
echo Training Attendance Analyzer
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please download and install Python from:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

REM Check if requirements are installed
python -c "import flask, openpyxl" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies
        echo.
        pause
        exit /b 1
    )
)

echo Starting application...
echo.
echo The web interface will open in your browser.
echo If it doesn't, visit: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server.
echo ============================================================
echo.

REM Run the application
python run.py

pause
