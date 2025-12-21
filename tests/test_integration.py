"""
Integration tests for end-to-end workflows
"""
import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient
from io import BytesIO
from PIL import Image

from api.main import app
from database import init_db, engine, Base


@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    """Get auth token"""
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    
    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def sample_image():
    """Create a sample test image"""
    img = np.zeros((640, 640, 3), dtype=np.uint8)
    img[100:200, 100:200] = [255, 255, 255]  # White square
    img_bytes = cv2.imencode('.jpg', img)[1].tobytes()
    return BytesIO(img_bytes)


def test_image_detection_workflow(client, auth_token, sample_image):
    """Test complete image detection workflow"""
    # Upload and detect
    response = client.post(
        "/api/v1/detect/image",
        files={"file": ("test.jpg", sample_image, "image/jpeg")},
        params={"confidence": 0.3},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "detections" in data
    assert "total_detections" in data


def test_batch_processing(client, auth_token, sample_image):
    """Test batch image processing"""
    files = [
        ("files", ("test1.jpg", sample_image, "image/jpeg")),
        ("files", ("test2.jpg", sample_image, "image/jpeg"))
    ]
    
    response = client.post(
        "/api/v1/detect/batch",
        files=files,
        params={"confidence": 0.3},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 2


def test_analytics_endpoint(client, auth_token):
    """Test analytics endpoint"""
    response = client.get(
        "/api/v1/analytics",
        params={"days": 7},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total_sessions" in data
    assert "total_detections" in data


def test_metrics_endpoint(client):
    """Test metrics endpoint"""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    # Should return Prometheus format
    assert "visiontrack" in response.text or "counter" in response.text

