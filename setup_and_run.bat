@echo off
REM USB PD Parser - Windows Setup Script

echo ==========================================
echo USB PD Parser - Setup Script (Windows)
echo ==========================================
echo.

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.8 or higher.
    pause
    exit /b 1
)
echo [OK] Python found
echo.

REM Create directory structure
echo Creating project directories...
if not exist "data" mkdir data
if not exist "examples" mkdir examples
if not exist "tests" mkdir tests
type nul > data\.gitkeep
echo [OK] Directories created
echo.

REM Create virtual environment
echo Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [INFO] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip upgraded
echo.

REM Install dependencies
echo Installing dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo [OK] Dependencies installed
) else (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b 1
)
echo.

echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next Steps:
echo 1. Place your PDF in the 'data' folder
echo 2. Run: python usb_pd_parser.py data\your_spec.pdf
echo.
pause