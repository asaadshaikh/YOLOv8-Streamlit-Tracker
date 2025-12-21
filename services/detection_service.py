"""
Detection service layer - handles all detection and tracking logic
"""
import cv2
import numpy as np
import time
from typing import Tuple, List, Optional, Dict
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import supervision as sv
from pathlib import Path

from config import settings


class DetectionService:
    """Service for object detection and tracking"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or settings.MODEL_PATH
        self.model = None
        self._load_model()
        self._setup_annotators()
    
    def _load_model(self):
        """Load YOLO model"""
        try:
            self.model = YOLO(self.model_path)
            _ = self.model.model.names  # Verify model is loaded
        except Exception as e:
            raise RuntimeError(f"Error loading YOLO model '{self.model_path}': {e}")
    
    def _setup_annotators(self):
        """Setup supervision annotators"""
        try:
            colors = sv.ColorPalette.DEFAULT
            self.box_annotator = sv.BoxAnnotator(color=colors, thickness=2)
            self.label_annotator = sv.LabelAnnotator(
                color=colors, 
                text_color="white", 
                text_scale=0.5, 
                text_thickness=1
            )
        except AttributeError:
            # Fallback for different supervision versions
            self.box_annotator = sv.BoxAnnotator(color="white", thickness=2)
            self.label_annotator = sv.LabelAnnotator(
                color="white", 
                text_color="red", 
                text_scale=0.5, 
                text_thickness=1
            )
    
    def detect_objects(
        self, 
        image: np.ndarray, 
        confidence: float = None
    ) -> Tuple[np.ndarray, List[Dict]]:
        """
        Detect objects in an image
        
        Returns:
            annotated_image: Image with bounding boxes
            detections_list: List of detection dictionaries
        """
        confidence = confidence or settings.DEFAULT_CONFIDENCE_THRESHOLD
        results = self.model.predict(image, conf=confidence, verbose=False)
        result = results[0]
        detections = sv.Detections.from_ultralytics(result)
        
        annotated_image = image.copy()
        detections_list = []
        
        if len(detections) > 0 and detections.class_id is not None:
            labels = []
            for i in range(len(detections)):
                class_id = detections.class_id[i]
                conf = detections.confidence[i]
                bbox = detections.xyxy[i]
                
                if class_id in self.model.model.names:
                    class_name = self.model.model.names[class_id]
                    labels.append(f"{class_name} {conf:0.2f}")
                    
                    detections_list.append({
                        "class_id": int(class_id),
                        "class_name": class_name,
                        "confidence": float(conf),
                        "bbox": [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])]
                    })
            
            annotated_image = self.box_annotator.annotate(
                scene=annotated_image, 
                detections=detections
            )
            if len(labels) == len(detections):
                annotated_image = self.label_annotator.annotate(
                    scene=annotated_image, 
                    detections=detections, 
                    labels=labels
                )
        
        return annotated_image, detections_list
    
    def track_objects(
        self,
        frame: np.ndarray,
        tracker: DeepSort,
        confidence: float = None
    ) -> Tuple[np.ndarray, List[Dict], float]:
        """
        Track objects in a frame
        
        Returns:
            annotated_frame: Frame with tracking annotations
            detections_list: List of detection dictionaries with track IDs
            fps: Frames per second
        """
        confidence = confidence or settings.DEFAULT_CONFIDENCE_THRESHOLD
        start_time = time.time()
        
        # Run detection
        results = self.model.predict(frame, conf=confidence, verbose=False)
        detections = sv.Detections.from_ultralytics(results[0])
        
        # Format detections for DeepSORT
        formatted_detections = []
        if len(detections) > 0:
            for i in range(len(detections)):
                bbox = detections.xyxy[i]
                conf = detections.confidence[i]
                cls_id = detections.class_id[i]
                if len(bbox) == 4:
                    formatted_detections.append((bbox, conf, int(cls_id)))
        
        # Convert to DeepSORT format
        deepsort_detections = []
        for bbox_xyxy, conf, cls_id in formatted_detections:
            x1, y1, x2, y2 = bbox_xyxy
            w, h = x2 - x1, y2 - y1
            if w > 0 and h > 0:
                deepsort_detections.append(([int(x1), int(y1), int(w), int(h)], conf, cls_id))
        
        # Update tracker
        tracks = []
        if deepsort_detections:
            try:
                tracks = tracker.update_tracks(deepsort_detections, frame=frame)
            except Exception:
                pass
        
        # Process tracks
        tracked_bboxes_xyxy = []
        track_ids = []
        track_class_ids = []
        detections_list = []
        
        for track in tracks:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue
            
            track_id = track.track_id
            ltrb = track.to_ltrb()
            class_id = track.get_det_class()
            
            if ltrb is not None and class_id is not None and class_id in self.model.model.names:
                tracked_bboxes_xyxy.append(ltrb)
                track_ids.append(track_id)
                track_class_ids.append(class_id)
                
                detections_list.append({
                    "track_id": int(track_id),
                    "class_id": int(class_id),
                    "class_name": self.model.model.names[class_id],
                    "bbox": [float(ltrb[0]), float(ltrb[1]), float(ltrb[2]), float(ltrb[3])]
                })
        
        # Annotate frame
        tracked_detections = sv.Detections.empty()
        if tracked_bboxes_xyxy:
            tracked_detections = sv.Detections(xyxy=np.array(tracked_bboxes_xyxy))
        
        annotated_frame = frame.copy()
        if len(tracked_detections) > 0:
            labels = [
                f"#{track_id} {self.model.model.names[cls_id]}"
                for track_id, cls_id in zip(track_ids, track_class_ids)
            ]
            annotated_frame = self.box_annotator.annotate(
                scene=annotated_frame, 
                detections=tracked_detections
            )
            if len(labels) == len(tracked_detections):
                annotated_frame = self.label_annotator.annotate(
                    scene=annotated_frame, 
                    detections=tracked_detections, 
                    labels=labels
                )
        
        # Calculate FPS
        end_time = time.time()
        fps = 1 / (end_time - start_time) if (end_time - start_time) > 0 else 0
        cv2.putText(
            annotated_frame, 
            f"FPS: {fps:.2f}", 
            (20, 45), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (0, 0, 255), 
            2, 
            cv2.LINE_AA
        )
        
        return annotated_frame, detections_list, fps
    
    def create_tracker(self) -> DeepSort:
        """Create a new DeepSORT tracker instance"""
        return DeepSort(
            max_age=settings.DEEPSORT_MAX_AGE,
            n_init=settings.DEEPSORT_N_INIT,
            nms_max_overlap=settings.DEEPSORT_NMS_MAX_OVERLAP
        )
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        return {
            "model_path": self.model_path,
            "model_name": Path(self.model_path).stem,
            "num_classes": len(self.model.model.names),
            "class_names": list(self.model.model.names.values())
        }

