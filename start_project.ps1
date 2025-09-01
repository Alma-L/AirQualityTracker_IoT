# Air Quality Tracker IoT - PowerShell Startup Script
Write-Host "🌬️  Air Quality Tracker IoT - Starting up..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.7+ and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if required packages are installed
Write-Host "🔍 Checking dependencies..." -ForegroundColor Blue
try {
    python -c "import uvicorn, fastapi" 2>$null
    Write-Host "✅ All required packages are installed" -ForegroundColor Green
} catch {
    Write-Host "📦 Installing required packages..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install packages" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Start the project using the simple startup script
Write-Host "🚀 Starting Air Quality Tracker IoT..." -ForegroundColor Green
python start_simple.py

Write-Host ""
Write-Host "✅ Project startup initiated!" -ForegroundColor Green
Write-Host "💡 Check the new terminal windows that opened" -ForegroundColor Yellow
Read-Host "Press Enter to exit"
