# 🚀 Running Without Docker (Local Setup)

Since Docker is not installed, here's how to run the project locally with Python.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

## Step-by-Step Setup

### Step 1: Check Python Installation

```powershell
python --version
```

Should show Python 3.10 or higher. If not, download from [python.org](https://www.python.org/downloads/)

### Step 2: Create Virtual Environment

```powershell
python -m venv venv
```

### Step 3: Activate Virtual Environment

```powershell
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again.

### Step 4: Install Dependencies

```powershell
pip install -r requirements.txt
```

**Note**: This will take 5-10 minutes and download ~2GB of packages including PyTorch.

### Step 5: Initialize Database

```powershell
python scripts/init_db.py
```

### Step 6: Start the API Server

Open a **new PowerShell window** (keep the first one open), navigate to project folder, activate venv, then:

```powershell
cd "D:\Projects\VisionTrack AI"
.\venv\Scripts\Activate.ps1
uvicorn api.main:app --reload --port 8000
```

### Step 7: Start the UI

Open **another PowerShell window**, navigate to project folder, activate venv, then:

```powershell
cd "D:\Projects\VisionTrack AI"
.\venv\Scripts\Activate.ps1
streamlit run streamlit_app.py --server.port 8501
```

### Step 8: Access the Application

- **UI**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Quick Start Script (PowerShell)

Save this as `run-local.ps1`:

```powershell
# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python is not installed!" -ForegroundColor Red
    exit 1
}

# Create venv if not exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate venv
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies (this may take 5-10 minutes)..." -ForegroundColor Yellow
pip install -r requirements.txt

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
python scripts/init_db.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Now run these commands in separate terminals:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Terminal 1 (API):" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  uvicorn api.main:app --reload --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "Terminal 2 (UI):" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  streamlit run streamlit_app.py --server.port 8501" -ForegroundColor White
Write-Host ""
```

Run it with:
```powershell
.\run-local.ps1
```

## Troubleshooting

### "python is not recognized"
- Install Python from [python.org](https://www.python.org/downloads/)
- Make sure to check "Add Python to PATH" during installation

### Execution Policy Error
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port Already in Use
Change ports in the commands:
- API: `uvicorn api.main:app --reload --port 8001`
- UI: `streamlit run streamlit_app.py --server.port 8502`

### PyTorch Installation Issues
If PyTorch fails to install, try:
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Model File Missing
The `yolov8n.pt` file should be in the project root. If missing, it will download automatically on first run.

## Alternative: Install Docker Desktop

If you prefer Docker (easier for deployment):

1. Download Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Install and restart your computer
3. Then use: `docker compose up --build`

## What You'll See

Once running:
- **UI at http://localhost:8501**: Beautiful web interface for object detection
- **API Docs at http://localhost:8000/docs**: Interactive API documentation
- **Health at http://localhost:8000/health**: System status

Enjoy exploring your project! 🎉

