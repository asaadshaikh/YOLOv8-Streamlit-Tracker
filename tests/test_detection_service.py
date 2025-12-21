"""
Unit tests for DetectionService
"""
import pytest
import numpy as np
import cv2
from services.detection_service import DetectionService
from config import settings


@pytest.fixture
def detection_service():
    """Fixture for DetectionService"""
    return DetectionService()


@pytest.fixture
def sample_image():
    """Create a sample test image"""
    return np.zeros((640, 640, 3), dtype=np.uint8)


def test_detection_service_initialization(detection_service):
    """Test that DetectionService initializes correctly"""
    assert detection_service.model is not None
    assert detection_service.box_annotator is not None
    assert detection_service.label_annotator is not None


def test_detect_objects(detection_service, sample_image):
    """Test object detection on sample image"""
    annotated_image, detections = detection_service.detect_objects(
        sample_image, 
        confidence=0.3
    )
    
    assert annotated_image is not None
    assert isinstance(detections, list)
    assert annotated_image.shape == sample_image.shape


def test_create_tracker(detection_service):
    """Test tracker creation"""
    tracker = detection_service.create_tracker()
    assert tracker is not None


def test_get_model_info(detection_service):
    """Test model info retrieval"""
    info = detection_service.get_model_info()
    
    assert "model_path" in info
    assert "model_name" in info
    assert "num_classes" in info
    assert "class_names" in info
    assert isinstance(info["class_names"], list)


def test_track_objects(detection_service, sample_image):
    """Test object tracking on sample frame"""
    tracker = detection_service.create_tracker()
    annotated_frame, detections, fps = detection_service.track_objects(
        sample_image,
        tracker,
        confidence=0.3
    )
    
    assert annotated_frame is not None
    assert isinstance(detections, list)
    assert isinstance(fps, float)
    assert fps >= 0
    assert annotated_frame.shape == sample_image.shape

