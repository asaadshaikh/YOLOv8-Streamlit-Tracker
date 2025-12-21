#!/bin/bash

echo "========================================"
echo "  VisionTrack AI - Quick Start"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

echo "[1/3] Building and starting containers..."
echo "This may take 5-10 minutes on first run..."
echo ""

docker-compose up --build

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to start containers"
    echo "Check the error messages above"
    exit 1
fi

echo ""
echo "========================================"
echo "  Services Started Successfully!"
echo "========================================"
echo ""
echo "Access the application at:"
echo "  - UI:        http://localhost:8501"
echo "  - API Docs:  http://localhost:8000/docs"
echo "  - Health:    http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the services"
echo "========================================"

