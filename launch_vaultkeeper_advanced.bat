@echo off
title VaultKeeper - Password Manager Launcher
color 07

setlocal enabledelayedexpansion

set STARTDIR=%CD%
set VERSION=3.1.0

echo    VaultKeeper v%VERSION%
echo    Secure Offline Password Manager
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.11+ from:
    echo https://python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("!PYVER!") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if !MAJOR! LSS 3 (
    echo [ERROR] Python 3.11+ required. Found: !PYVER!
    pause
    exit /b 1
)
if !MAJOR! EQU 3 if !MINOR! LSS 11 (
    echo [ERROR] Python 3.11+ required. Found: !PYVER!
    pause
    exit /b 1
)

echo [OK] Python !PYVER!
echo.

REM Check for existing vault
if exist "vaultkeeper.db" (
    echo [INFO] Existing vault found with %~zi bytes
) else (
    echo [INFO] No existing vault found - will create on first unlock
)
echo.

REM Setup virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
)

call venv\Scripts\activate.bat

REM Install dependencies
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo [OK] Dependencies ready
echo.

REM Launch
echo Starting VaultKeeper...
echo.
python run.py

echo.
echo VaultKeeper closed.
timeout /t 2 >nul