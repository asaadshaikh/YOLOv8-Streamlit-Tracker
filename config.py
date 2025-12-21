"""
Configuration management for VisionTrack AI
Handles environment variables, settings, and application configuration
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "VisionTrack AI"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_PREFIX: str = "/api/v1"
    
    # Streamlit
    STREAMLIT_PORT: int = Field(default=8501, env="STREAMLIT_PORT")
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./visiontrack.db",
        env="DATABASE_URL"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Model
    MODEL_PATH: str = Field(default="yolov8n.pt", env="MODEL_PATH")
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.3
    SUPPORTED_MODELS: list = ["yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x"]
    
    # Tracking
    DEEPSORT_MAX_AGE: int = 30
    DEEPSORT_N_INIT: int = 3
    DEEPSORT_NMS_MAX_OVERLAP: float = 1.0
    
    # Storage
    UPLOAD_DIR: Path = Path("./uploads")
    OUTPUT_DIR: Path = Path("./outputs")
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = "visiontrack.log"
    
    # Redis (for caching and queues)
    REDIS_URL: Optional[str] = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # CORS
    CORS_ORIGINS: list = Field(default=["*"], env="CORS_ORIGINS")
    
    # Performance
    MAX_WORKERS: int = Field(default=4, env="MAX_WORKERS")
    ENABLE_GPU: bool = Field(default=True, env="ENABLE_GPU")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

# Create necessary directories
settings.UPLOAD_DIR.mkdir(exist_ok=True)
settings.OUTPUT_DIR.mkdir(exist_ok=True)

