"""
Background job processing service
Handles async video processing using Celery
"""
from celery import Celery
from typing import Optional
import cv2
import os
from pathlib import Path
import uuid
from sqlalchemy.orm import Session

from config import settings
from database import get_db, DatabaseService
from services.detection_service import DetectionService
from utils.logger import logger

# Initialize Celery (only if Redis is available)
celery_app = None
try:
    celery_app = Celery(
        "visiontrack",
        broker=settings.REDIS_URL or "redis://localhost:6379/0",
        backend=settings.REDIS_URL or "redis://localhost:6379/0"
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,  # 1 hour max
        worker_prefetch_multiplier=1,
    )
except Exception as e:
    logger.warning(f"Celery initialization failed (Redis may not be available): {e}")
    logger.warning("Background job processing will be disabled. Install Redis to enable async processing.")


# Define task function (will be decorated if Celery is available)
def _process_video_task_impl(
    video_path: str,
    session_id: str,
    confidence: float,
    track: bool = True,
    task_context=None
):
    """
    Background task to process video
    task_context: Celery task context (self) if running as Celery task, None otherwise
    """
    try:
        task_id = task_context.request.id if task_context else "sync"
        logger.info(f"Starting video processing task {task_id} for session {session_id}")
        
        # Get database session
        from database import SessionLocal
        db = SessionLocal()
        
        try:
            # Update session status
            DatabaseService.update_session(
                db=db,
                session_id=session_id,
                status="processing"
            )
            db.commit()
            
            # Initialize detection service
            detection_service = DetectionService()
            tracker = detection_service.create_tracker() if track else None
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("Could not open video file")
            
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Setup output video
            output_path = settings.OUTPUT_DIR / f"{session_id}_output.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
            frame_count = 0
            total_detections = 0
            
            # Process frames
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Update progress (only if running as Celery task)
                if total_frames > 0 and task_context:
                    progress = (frame_count / total_frames) * 100
                    task_context.update_state(
                        state="PROGRESS",
                        meta={
                            "current": frame_count,
                            "total": total_frames,
                            "progress": progress,
                            "status": f"Processing frame {frame_count}/{total_frames}"
                        }
                    )
                elif frame_count % 30 == 0:  # Log progress every 30 frames
                    progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                    logger.info(f"Task {task_id}: Processing frame {frame_count}/{total_frames} ({progress:.1f}%)")
                
                # Process frame
                if track and tracker:
                    annotated_frame, detections, _ = detection_service.track_objects(
                        frame, tracker, confidence
                    )
                else:
                    annotated_frame, detections = detection_service.detect_objects(
                        frame, confidence
                    )
                
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
            
            # Update session
            DatabaseService.update_session(
                db=db,
                session_id=session_id,
                total_detections=total_detections,
                total_frames=frame_count,
                status="completed"
            )
            db.commit()
            
            logger.info(f"Video processing completed for session {session_id}")
            
            return {
                "session_id": session_id,
                "total_frames": frame_count,
                "total_detections": total_detections,
                "output_path": str(output_path),
                "status": "completed"
            }
        
        finally:
            db.close()
            # Cleanup temp file
            if os.path.exists(video_path) and "tmp" in video_path:
                try:
                    os.remove(video_path)
                except Exception as e:
                    logger.warning(f"Could not remove temp file {video_path}: {e}")
    
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        # Update session status
        try:
            from database import SessionLocal
            db = SessionLocal()
            DatabaseService.update_session(
                db=db,
                session_id=session_id,
                status="failed"
            )
            db.commit()
            db.close()
        except:
            pass
        
        raise


# Decorate task if Celery is available
if celery_app is not None:
    @celery_app.task(bind=True, name="process_video")
    def process_video_task(self, video_path, session_id, confidence, track=True):
        """Celery task wrapper"""
        return _process_video_task_impl(video_path, session_id, confidence, track, task_context=self)
else:
    # Fallback function if Celery is not available
    def process_video_task(*args, **kwargs):
        raise RuntimeError("Celery is not initialized. Redis may not be available.")


class JobService:
    """Service for managing background jobs"""
    
    @staticmethod
    def submit_video_job(
        video_path: str,
        session_id: str,
        confidence: float,
        track: bool = True
    ) -> str:
        """Submit a video processing job"""
        if celery_app is None:
            raise RuntimeError("Celery is not initialized. Redis may not be available.")
        task = process_video_task.delay(
            video_path=video_path,
            session_id=session_id,
            confidence=confidence,
            track=track
        )
        return task.id
    
    @staticmethod
    def get_job_status(task_id: str) -> dict:
        """Get status of a background job"""
        if celery_app is None:
            raise RuntimeError("Celery is not initialized. Redis may not be available.")
        task = celery_app.AsyncResult(task_id)
        
        if task.state == "PENDING":
            return {
                "task_id": task_id,
                "status": "pending",
                "progress": 0
            }
        elif task.state == "PROGRESS":
            return {
                "task_id": task_id,
                "status": "processing",
                "progress": task.info.get("progress", 0),
                "current": task.info.get("current", 0),
                "total": task.info.get("total", 0),
                "message": task.info.get("status", "")
            }
        elif task.state == "SUCCESS":
            return {
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "result": task.result
            }
        else:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(task.info) if task.info else "Unknown error"
            }

