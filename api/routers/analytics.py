"""
Analytics and session management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import csv
from io import StringIO

from database import get_db, DatabaseService, Detection, DetectionSession
from services.auth_service import get_current_user
from database import User

router = APIRouter(prefix="/api/v1", tags=["analytics"])


@router.get("/session/{session_id}")
async def get_session(
    session_id: str, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get session statistics"""
    stats = DatabaseService.get_session_stats(db, session_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Session not found")
    return stats


@router.get("/analytics")
async def get_analytics(
    days: int = 7, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get analytics data"""
    return DatabaseService.get_analytics(db, days)


@router.get("/export/{session_id}")
async def export_session(
    session_id: str, 
    format: str = "json", 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Export session data in various formats"""
    session = db.query(DetectionSession).filter(
        DetectionSession.session_id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    detections = db.query(Detection).filter(
        Detection.session_id == session_id
    ).all()
    
    data = {
        "session_id": session.session_id,
        "session_type": session.session_type,
        "created_at": session.created_at.isoformat(),
        "total_detections": len(detections),
        "detections": [
            {
                "frame_number": d.frame_number,
                "track_id": d.track_id,
                "class_name": d.class_name,
                "confidence": d.confidence,
                "bbox": [d.bbox_x1, d.bbox_y1, d.bbox_x2, d.bbox_y2]
            }
            for d in detections
        ]
    }
    
    if format == "json":
        return JSONResponse(content=data)
    elif format == "csv":
        output = StringIO()
        writer = csv.DictWriter(
            output, 
            fieldnames=["frame_number", "track_id", "class_name", "confidence", 
                       "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2"]
        )
        writer.writeheader()
        for d in detections:
            writer.writerow({
                "frame_number": d.frame_number,
                "track_id": d.track_id,
                "class_name": d.class_name,
                "confidence": d.confidence,
                "bbox_x1": d.bbox_x1,
                "bbox_y1": d.bbox_y1,
                "bbox_x2": d.bbox_x2,
                "bbox_y2": d.bbox_y2
            })
        return JSONResponse(content={"csv": output.getvalue()})
    else:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported format. Use 'json' or 'csv'"
        )

