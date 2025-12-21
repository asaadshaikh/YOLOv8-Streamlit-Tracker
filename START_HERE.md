# 🚀 START HERE - How to Run VisionTrack AI

## Quick Decision: Docker or Local?

### Option A: With Docker (Easier, Recommended)
**Requires**: Docker Desktop installed

1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Run: `.\run.bat` (or `docker compose up --build`)

### Option B: Without Docker (Local Python)
**Requires**: Python 3.10+ installed

1. Run: `.\run-local.ps1`
2. Then start API and UI in separate terminals (see instructions below)

---

## 🐳 Option A: Using Docker (If Installed)

### Step 1: Install Docker Desktop
- Download: https://www.docker.com/products/docker-desktop/
- Install and restart your computer
- Make sure Docker Desktop is running (icon in system tray)

### Step 2: Run the Project

**In PowerShell:**
```powershell
.\run.bat
```

**Or manually:**
```powershell
docker compose up --build
```

### Step 3: Access
- **UI**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

---

## 🐍 Option B: Without Docker (Local Setup)

### Step 1: Check Python
```powershell
python --version
```
Should show Python 3.10 or higher.

### Step 2: Run Setup Script
```powershell
.\run-local.ps1
```

This will:
- Create virtual environment
- Install all dependencies (~2GB, takes 5-10 minutes)
- Initialize database

### Step 3: Start Services

**Open Terminal 1 (API):**
```powershell
cd "D:\Projects\VisionTrack AI"
.\venv\Scripts\Activate.ps1
uvicorn api.main:app --reload --port 8000
```

**Open Terminal 2 (UI):**
```powershell
cd "D:\Projects\VisionTrack AI"
.\venv\Scripts\Activate.ps1
streamlit run streamlit_app.py --server.port 8501
```

### Step 4: Access
- **UI**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

---

## ⚠️ Troubleshooting

### "docker is not recognized"
- Install Docker Desktop OR use Option B (local setup)

### "python is not recognized"
- Install Python from https://www.python.org/downloads/
- Check "Add Python to PATH" during installation

### Execution Policy Error (PowerShell)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port Already in Use
- Change ports in commands (8001, 8502, etc.)
- Or stop other services using those ports

---

## 📚 What to Explore

Once running:

1. **UI (http://localhost:8501)**
   - Upload images for detection
   - Upload videos for tracking
   - Try live webcam
   - Check analytics dashboard

2. **API Docs (http://localhost:8000/docs)**
   - Interactive API explorer
   - Test authentication
   - Try image detection
   - See all endpoints

3. **Health Check (http://localhost:8000/health)**
   - System status
   - Model information

---

## 🎯 Quick Commands Reference

### Docker Commands
```powershell
docker compose up --build    # Start
docker compose down           # Stop
docker compose logs -f        # View logs
```

### Local Commands
```powershell
.\venv\Scripts\Activate.ps1   # Activate venv
uvicorn api.main:app --reload --port 8000  # Start API
streamlit run streamlit_app.py --server.port 8501  # Start UI
```

---

**Need help?** Check `RUN_WITHOUT_DOCKER.md` for detailed local setup instructions.

