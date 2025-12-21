"""
FastAPI REST API for VisionTrack AI
Production-ready API with authentication, rate limiting, WebSocket support, and more
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
from pathlib import Path

from config import settings
from database import get_db, DatabaseService, init_db
from services.detection_service import DetectionService
from utils.logger import logger
from utils.rate_limiter import RateLimitMiddleware
from utils.metrics import metrics

# Import routers
from api.routers import auth, detection, jobs, websocket, metrics as metrics_router, analytics

# Initialize database on startup
init_db()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    Production-ready RESTful API for object detection and tracking using YOLOv8 and DeepSORT.
    
    ## Features
    
    * 🔐 **Authentication** - JWT-based authentication
    * 🚀 **Real-time Processing** - WebSocket support for live updates
    * 📊 **Analytics** - Comprehensive metrics and monitoring
    * ⚡ **Background Jobs** - Async video processing with Celery
    * 🔒 **Rate Limiting** - API protection and throttling
    * 📦 **Batch Processing** - Process multiple images at once
    
    ## Authentication
    
    Most endpoints require authentication. Register at `/api/v1/auth/register` 
    and login at `/api/v1/auth/login` to get an access token.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if hasattr(settings, 'CORS_ORIGINS') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Include routers
app.include_router(auth.router)
app.include_router(detection.router)
app.include_router(jobs.router)
app.include_router(websocket.router)
app.include_router(metrics_router.router)
app.include_router(analytics.router)

# Initialize detection service
detection_service = DetectionService()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "api_version": "v1",
        "features": [
            "authentication",
            "real-time_processing",
            "background_jobs",
            "batch_processing",
            "websocket_support",
            "metrics_and_monitoring"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status"""
    model_loaded = detection_service.model is not None
    db_status = "connected"
    redis_status = "unknown"
    
    try:
        from sqlalchemy import text
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check Redis/Celery availability
    try:
        from services.job_service import celery_app
        if celery_app is not None:
            redis_status = "available"
        else:
            redis_status = "unavailable"
    except Exception:
        redis_status = "unavailable"
    
    return {
        "status": "healthy" if model_loaded and db_status == "connected" else "degraded",
        "model_loaded": model_loaded,
        "database": db_status,
        "redis": redis_status,
        "version": settings.APP_VERSION
    }


@app.get("/api/v1/model/info")
async def get_model_info():
    """Get information about the loaded model"""
    try:
        info = detection_service.get_model_info()
        metrics.increment("api_requests_total", labels={"endpoint": "model_info"})
        return info
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        metrics.increment("api_errors_total", labels={"endpoint": "model_info"})
        raise HTTPException(status_code=500, detail=str(e))


# Detection endpoints moved to routers/detection.py


# Video detection moved to routers/detection.py


@app.get("/api/v1/output/{filename}")
async def get_output(filename: str):
    """Get output file (image or video)"""
    file_path = settings.OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if filename.endswith(".mp4"):
        return FileResponse(str(file_path), media_type="video/mp4")
    else:
        return FileResponse(str(file_path), media_type="image/jpeg")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)

