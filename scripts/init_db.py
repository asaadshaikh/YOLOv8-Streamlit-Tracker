#!/usr/bin/env python3
"""
Initialize database with tables
"""
from database import init_db, engine, Base
from config import settings
from utils.logger import logger

if __name__ == "__main__":
    logger.info("Initializing database...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized successfully at {settings.DATABASE_URL}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

