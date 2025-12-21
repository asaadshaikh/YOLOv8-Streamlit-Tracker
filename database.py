"""
Database models and session management
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional
import json

from config import settings

Base = declarative_base()


class DetectionSession(Base):
    """Stores detection session metadata"""
    __tablename__ = "detection_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    session_type = Column(String)  # 'image', 'video', 'webcam'
    model_name = Column(String)
    confidence_threshold = Column(Float)
    total_detections = Column(Integer, default=0)
    total_frames = Column(Integer, default=0)
    processing_time = Column(Float)  # in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="completed")  # 'processing', 'completed', 'failed'
    metadata = Column(JSON)  # Additional metadata


class Detection(Base):
    """Stores individual detection records"""
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    frame_number = Column(Integer, nullable=True)
    track_id = Column(Integer, nullable=True)
    class_id = Column(Integer)
    class_name = Column(String)
    confidence = Column(Float)
    bbox_x1 = Column(Float)
    bbox_y1 = Column(Float)
    bbox_x2 = Column(Float)
    bbox_y2 = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)


class Analytics(Base):
    """Stores aggregated analytics data"""
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, index=True)
    total_sessions = Column(Integer, default=0)
    total_detections = Column(Integer, default=0)
    avg_confidence = Column(Float)
    most_detected_class = Column(String)
    avg_processing_time = Column(Float)
    metadata = Column(JSON)


class User(Base):
    """User management (for future authentication)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


# Database setup
engine = create_engine(
    settings.DATABASE_URL.replace("sqlite:///", "sqlite:///") if "sqlite" in settings.DATABASE_URL else settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseService:
    """Service layer for database operations"""
    
    @staticmethod
    def create_session(
        db: Session,
        session_id: str,
        session_type: str,
        model_name: str,
        confidence_threshold: float,
        metadata: Optional[dict] = None
    ) -> DetectionSession:
        """Create a new detection session"""
        session = DetectionSession(
            session_id=session_id,
            session_type=session_type,
            model_name=model_name,
            confidence_threshold=confidence_threshold,
            metadata=metadata or {}
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def add_detection(
        db: Session,
        session_id: str,
        class_id: int,
        class_name: str,
        confidence: float,
        bbox: tuple,
        frame_number: Optional[int] = None,
        track_id: Optional[int] = None,
        metadata: Optional[dict] = None
    ) -> Detection:
        """Add a detection record"""
        detection = Detection(
            session_id=session_id,
            frame_number=frame_number,
            track_id=track_id,
            class_id=class_id,
            class_name=class_name,
            confidence=confidence,
            bbox_x1=bbox[0],
            bbox_y1=bbox[1],
            bbox_x2=bbox[2],
            bbox_y2=bbox[3],
            metadata=metadata or {}
        )
        db.add(detection)
        return detection
    
    @staticmethod
    def update_session(
        db: Session,
        session_id: str,
        total_detections: Optional[int] = None,
        total_frames: Optional[int] = None,
        processing_time: Optional[float] = None,
        status: Optional[str] = None
    ):
        """Update session statistics"""
        session = db.query(DetectionSession).filter(
            DetectionSession.session_id == session_id
        ).first()
        if session:
            if total_detections is not None:
                session.total_detections = total_detections
            if total_frames is not None:
                session.total_frames = total_frames
            if processing_time is not None:
                session.processing_time = processing_time
            if status is not None:
                session.status = status
            db.commit()
    
    @staticmethod
    def get_session_stats(db: Session, session_id: str) -> Optional[dict]:
        """Get statistics for a session"""
        session = db.query(DetectionSession).filter(
            DetectionSession.session_id == session_id
        ).first()
        if not session:
            return None
        
        detections = db.query(Detection).filter(
            Detection.session_id == session_id
        ).all()
        
        return {
            "session_id": session.session_id,
            "session_type": session.session_type,
            "total_detections": len(detections),
            "total_frames": session.total_frames,
            "processing_time": session.processing_time,
            "created_at": session.created_at.isoformat(),
            "class_distribution": DatabaseService._get_class_distribution(detections),
            "avg_confidence": sum(d.confidence for d in detections) / len(detections) if detections else 0
        }
    
    @staticmethod
    def _get_class_distribution(detections: list) -> dict:
        """Calculate class distribution from detections"""
        distribution = {}
        for det in detections:
            distribution[det.class_name] = distribution.get(det.class_name, 0) + 1
        return distribution
    
    @staticmethod
    def get_analytics(db: Session, days: int = 7) -> dict:
        """Get analytics for the last N days"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        sessions = db.query(DetectionSession).filter(
            DetectionSession.created_at >= cutoff_date
        ).all()
        
        detections = db.query(Detection).join(DetectionSession).filter(
            DetectionSession.created_at >= cutoff_date
        ).all()
        
        if not sessions:
            return {
                "total_sessions": 0,
                "total_detections": 0,
                "avg_confidence": 0,
                "class_distribution": {},
                "sessions_by_type": {}
            }
        
        class_dist = {}
        sessions_by_type = {}
        confidences = []
        
        for det in detections:
            class_dist[det.class_name] = class_dist.get(det.class_name, 0) + 1
            confidences.append(det.confidence)
        
        for sess in sessions:
            sessions_by_type[sess.session_type] = sessions_by_type.get(sess.session_type, 0) + 1
        
        return {
            "total_sessions": len(sessions),
            "total_detections": len(detections),
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "class_distribution": class_dist,
            "sessions_by_type": sessions_by_type,
            "avg_processing_time": sum(s.processing_time or 0 for s in sessions) / len(sessions) if sessions else 0
        }

