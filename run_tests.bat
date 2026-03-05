@echo off
REM Quick test runner for Abulafia Test Suite
REM Run this batch file to execute all CLI tests

echo ==========================================
echo   Abulafia Test Suite Runner
echo ==========================================
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo No virtual environment found, using system Python
)

echo.
echo Running test suite...
echo.

python test_suite.py

echo.
echo ==========================================
echo   Test run complete
echo ==========================================

REM Keep window open if double-clicked
if "%1"=="" pause
