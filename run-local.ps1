# VisionTrack AI - Local Setup Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VisionTrack AI - Local Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python is not installed!" -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

$pythonVersion = python --version
Write-Host "Found: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Create venv if not exists
if (-not (Test-Path "venv")) {
    Write-Host "[1/4] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "[1/4] Virtual environment already exists" -ForegroundColor Green
}

# Activate venv
Write-Host "[2/4] Activating virtual environment..." -ForegroundColor Yellow
try {
    & .\venv\Scripts\Activate.ps1
} catch {
    Write-Host "ERROR: Could not activate virtual environment" -ForegroundColor Red
    Write-Host "Try running: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}

# Install dependencies
Write-Host "[3/4] Installing dependencies (this may take 5-10 minutes)..." -ForegroundColor Yellow
Write-Host "This will download ~2GB of packages including PyTorch..." -ForegroundColor Gray
pip install --upgrade pip
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Initialize database
Write-Host "[4/4] Initializing database..." -ForegroundColor Yellow
python scripts/init_db.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to initialize database" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open TWO separate PowerShell windows and run:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Terminal 1 - Start API Server:" -ForegroundColor White
Write-Host "  cd `"D:\Projects\VisionTrack AI`"" -ForegroundColor Gray
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "  uvicorn api.main:app --reload --port 8000" -ForegroundColor Gray
Write-Host ""
Write-Host "Terminal 2 - Start UI:" -ForegroundColor White
Write-Host "  cd `"D:\Projects\VisionTrack AI`"" -ForegroundColor Gray
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "  streamlit run streamlit_app.py --server.port 8501" -ForegroundColor Gray
Write-Host ""
Write-Host "Then open in browser:" -ForegroundColor Cyan
Write-Host "  - UI:        http://localhost:8501" -ForegroundColor White
Write-Host "  - API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Health:    http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Green

