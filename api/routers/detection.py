"""
Detection endpoints
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import cv2
import numpy as np
import tempfile
import os
import uuid
from pathlib import Path
import time

from config import settings
from database import get_db, DatabaseService
from services.detection_service import DetectionService
from services.auth_service import get_current_user
from services.job_service import JobService
from database import User
from utils.logger import logger
from utils.metrics import metrics

router = APIRouter(prefix="/api/v1", tags=["detection"])

# Initialize detection service
detection_service = DetectionService()


@router.post("/detect/image")
async def detect_image(
    file: UploadFile = File(...),
    confidence: float = settings.DEFAULT_CONFIDENCE_THRESHOLD,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Detect objects in an uploaded image
    
    - **file**: Image file (jpg, png, jpeg)
    - **confidence**: Confidence threshold (0.0-1.0)
    """
    start_time = time.time()
    metrics.increment("api_requests_total", labels={"endpoint": "detect_image"})
    
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode image")
        
        # Create session
        session_id = str(uuid.uuid4())
        DatabaseService.create_session(
            db=db,
            session_id=session_id,
            session_type="image",
            model_name=Path(settings.MODEL_PATH).stem,
            confidence_threshold=confidence
        )
        
        # Detect objects
        annotated_image, detections = detection_service.detect_objects(image, confidence)
        
        # Save detections to database
        for det in detections:
            DatabaseService.add_detection(
                db=db,
                session_id=session_id,
                class_id=det["class_id"],
                class_name=det["class_name"],
                confidence=det["confidence"],
                bbox=det["bbox"]
            )
        
        # Update session
        processing_time = time.time() - start_time
        DatabaseService.update_session(
            db=db,
            session_id=session_id,
            total_detections=len(detections),
            total_frames=1,
            processing_time=processing_time,
            status="completed"
        )
        db.commit()
        
        # Record metrics
        metrics.record_timing("api_request_duration_seconds", start_time, 
                            labels={"endpoint": "detect_image"})
        metrics.increment("detections_total", value=len(detections))
        
        # Save annotated image
        output_path = settings.OUTPUT_DIR / f"{session_id}_annotated.jpg"
        cv2.imwrite(str(output_path), annotated_image)
        
        return {
            "session_id": session_id,
            "detections": detections,
            "total_detections": len(detections),
            "processing_time": processing_time,
            "annotated_image_url": f"/api/v1/output/{session_id}_annotated.jpg"
        }
    
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        metrics.increment("api_errors_total", labels={"endpoint": "detect_image"})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect/video")
async def detect_video(
    file: UploadFile = File(...),
    confidence: float = settings.DEFAULT_CONFIDENCE_THRESHOLD,
    track: bool = True,
    async_processing: bool = False,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Detect and optionally track objects in an uploaded video
    
    - **file**: Video file (mp4, avi, mov, mkv)
    - **confidence**: Confidence threshold (0.0-1.0)
    - **track**: Enable object tracking
    - **async_processing**: Process video in background (recommended for large files)
    """
    metrics.increment("api_requests_total", labels={"endpoint": "detect_video"})
    
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    try:
        # Save uploaded video
        session_id = str(uuid.uuid4())
        temp_dir = tempfile.gettempdir()
        file_suffix = Path(file.filename).suffix
        temp_path = os.path.join(temp_dir, f"{session_id}{file_suffix}")
        
        contents = await file.read()
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        # Create session
        DatabaseService.create_session(
            db=db,
            session_id=session_id,
            session_type="video",
            model_name=Path(settings.MODEL_PATH).stem,
            confidence_threshold=confidence
        )
        db.commit()
        
        # Process asynchronously if requested
        if async_processing:
            try:
                task_id = JobService.submit_video_job(
                    video_path=temp_path,
                    session_id=session_id,
                    confidence=confidence,
                    track=track
                )
                return {
                    "session_id": session_id,
                    "task_id": task_id,
                    "status": "processing",
                    "message": "Video processing started in background. Use /api/v1/jobs/{task_id} to check status."
                }
            except RuntimeError as e:
                logger.warning(f"Async processing not available: {e}. Falling back to synchronous processing.")
                # Fall through to synchronous processing
        
        # Synchronous processing (for small videos)
        start_time = time.time()
        cap = cv2.VideoCapture(temp_path)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Could not open video file")
        
        # Video writer setup
        output_path = settings.OUTPUT_DIR / f"{session_id}_output.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        tracker = detection_service.create_tracker() if track else None
        frame_count = 0
        total_detections = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if track and tracker:
                annotated_frame, detections, _ = detection_service.track_objects(
                    frame, tracker, confidence
                )
            else:
                annotated_frame, detections = detection_service.detect_objects(frame, confidence)
            
            # Save detections
            for det in detections:
                DatabaseService.add_detection(
                    db=db,
                    session_id=session_id,
                    class_id=det["class_id"],
                    class_name=det["class_name"],
                    confidence=det["confidence"],
                    bbox=det["bbox"],
                    frame_number=frame_count,
                    track_id=det.get("track_id")
                )
                total_detections += 1
            
            out.write(annotated_frame)
            frame_count += 1
        
        cap.release()
        out.release()
        processing_time = time.time() - start_time
        
        # Update session
        DatabaseService.update_session(
            db=db,
            session_id=session_id,
            total_detections=total_detections,
            total_frames=frame_count,
            processing_time=processing_time,
            status="completed"
        )
        db.commit()
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        metrics.record_timing("api_request_duration_seconds", start_time,
                            labels={"endpoint": "detect_video"})
        
        return {
            "session_id": session_id,
            "total_frames": frame_count,
            "total_detections": total_detections,
            "processing_time": processing_time,
            "output_video_url": f"/api/v1/output/{session_id}_output.mp4"
        }
    
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        metrics.increment("api_errors_total", labels={"endpoint": "detect_video"})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect/batch")
async def detect_batch(
    files: List[UploadFile] = File(...),
    confidence: float = settings.DEFAULT_CONFIDENCE_THRESHOLD,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Batch process multiple images
    
    - **files**: List of image files
    - **confidence**: Confidence threshold (0.0-1.0)
    """
    if len(files) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 files per batch")
    
    results = []
    for file in files:
        try:
            if not file.content_type or not file.content_type.startswith("image/"):
                results.append({"filename": file.filename, "error": "Not an image"})
                continue
            
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                results.append({"filename": file.filename, "error": "Could not decode"})
                continue
            
            annotated_image, detections = detection_service.detect_objects(image, confidence)
            results.append({
                "filename": file.filename,
                "detections": detections,
                "total_detections": len(detections)
            })
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})
    
    return {"results": results, "total_processed": len(results)}

