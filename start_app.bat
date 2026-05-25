@echo off
echo ===========================================
echo   Alumni Portal - Automated Startup Script
echo ===========================================

:: Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in the system PATH.
    echo Please install Python 3.10+ from python.org and try again.
    pause
    exit /b 1
)

:: Create Virtual Environment if it doesn't exist
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [+] Creating a new Python virtual environment...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [+] Virtual environment created successfully.
)

:: Activate Virtual Environment
echo [+] Activating virtual environment...
call venv\Scripts\activate.bat

:: Upgrade pip
echo [+] Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

:: Install Dependencies
echo [+] Installing required dependencies from requirements.txt...
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [+] Dependencies installed successfully.

:: Run the Flask Application
echo [+] Starting the Alumni Portal...
echo ===========================================
python app.py

:: Keep window open if the app crashes or stops
pause
