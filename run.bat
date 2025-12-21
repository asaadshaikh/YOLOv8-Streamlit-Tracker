@echo off
echo ========================================
echo   VisionTrack AI - Quick Start
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not in PATH!
    echo.
    echo Option 1: Install Docker Desktop from https://www.docker.com/products/docker-desktop/
    echo Option 2: Run without Docker using: run-local.ps1
    echo.
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/3] Building and starting containers...
echo This may take 5-10 minutes on first run...
echo.

REM Try docker compose (v2) first, fallback to docker-compose (v1)
docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose up --build
) else (
    docker compose up --build
)

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start containers
    echo Check the error messages above
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Services Started Successfully!
echo ========================================
echo.
echo Access the application at:
echo   - UI:        http://localhost:8501
echo   - API Docs:  http://localhost:8000/docs
echo   - Health:    http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the services
echo ========================================

