@echo off
title VaultKeeper - Password Manager Launcher
color 07

setlocal enabledelayedexpansion

REM Store the starting directory
set STARTDIR=%CD%

echo       VaultKeepe: Password Manager
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.11+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

REM Check Python version (must be 3.11+)
for /f "tokens=2 delims= " %%v in ('python --version') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("!PYVER!") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if !MAJOR! LSS 3 (
    echo [ERROR] Python 3.11+ is required. Detected: !PYVER!
    pause
    exit /b 1
)
if !MAJOR! EQU 3 if !MINOR! LSS 11 (
    echo [ERROR] Python 3.11+ is required. Detected: !PYVER!
    pause
    exit /b 1
)

echo [OK] Python found: !PYVER!
echo.

REM Check if Git is installed (for updates)
git --version >nul 2>&1
if errorlevel 1 (
    echo [WARN] Git not found. Updates will not work automatically.
    echo [INFO] You can still run the app, but to update you'll need to download manually.
    echo.
    set GIT_AVAILABLE=0
) else (
    echo [OK] Git found
    git --version
    set GIT_AVAILABLE=1
)
echo.

REM Check if this is a git repo and update if possible
if !GIT_AVAILABLE! EQU 1 (
    if exist ".git" (
        echo [UPDATE] Checking for updates...
        git pull origin main
        if errorlevel 1 (
            echo [WARN] Git pull failed, continuing with current version...
        ) else (
            echo [OK] Successfully updated to latest version
        )
        echo.
    )
)

echo [SETUP] Setting up Python virtual environment...

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        cd /d "%STARTDIR%"
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    cd /d "%STARTDIR%"
    pause
    exit /b 1
)

echo [OK] Virtual environment activated
echo.

REM Check for requirements.txt
if not exist requirements.txt (
    echo [ERROR] requirements.txt not found!
    echo Please make sure you are in the correct directory.
    cd /d "%STARTDIR%"
    pause
    exit /b 1
)

REM Install/upgrade dependencies
echo [INSTALL] Installing/updating dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install some dependencies!
    echo Trying to continue anyway...
) else (
    echo [OK] All dependencies installed successfully
)

echo.
echo [LAUNCH] Starting VaultKeeper...
echo.
echo    setup complete! starting app...
echo.

REM Start the application
python run.py

echo.
echo [DONE] VaultKeeper closed.
echo You can re-run this file anytime to update and launch the app.
echo Press any key to exit...
pause >nul

REM Return to original directory
cd /d "%STARTDIR%"
endlocal