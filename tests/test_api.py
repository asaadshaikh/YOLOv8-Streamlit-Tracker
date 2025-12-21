"""
Integration tests for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app
from database import init_db, engine, Base

# Initialize test database
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


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "status" in data


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_model_info(client):
    """Test model info endpoint"""
    response = client.get("/api/v1/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "model_path" in data
    assert "model_name" in data
    assert "num_classes" in data


def test_analytics_endpoint(client):
    """Test analytics endpoint"""
    response = client.get("/api/v1/analytics?days=7")
    assert response.status_code == 200
    data = response.json()
    assert "total_sessions" in data
    assert "total_detections" in data

