@echo off
echo 🌬️  Air Quality Tracker IoT - Starting up...
echo ==================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if required packages are installed
echo 🔍 Checking dependencies...
python -c "import uvicorn, fastapi" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing required packages...
    pip install -r requirements.txt
)

REM Start the project using the simple startup script
echo 🚀 Starting Air Quality Tracker IoT...
python start_simple.py

echo.
echo ✅ Project startup initiated!
echo 💡 Check the new terminal windows that opened
pause
