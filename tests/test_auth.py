"""
Tests for authentication service
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from services.auth_service import AuthService
from database import get_db, User, init_db, engine, Base


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
def test_user(test_db):
    """Create test user"""
    db = next(get_db())
    user = AuthService.create_user(
        db=db,
        username="testuser",
        email="test@example.com",
        password="testpassword123"
    )
    db.commit()
    db.close()
    return user


def test_register_user(client):
    """Test user registration"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"


def test_login(client, test_user):
    """Test user login"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401


def test_get_current_user(client, test_user):
    """Test getting current user info"""
    # Login first
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Get user info
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"


def test_protected_endpoint_without_auth(client):
    """Test accessing protected endpoint without auth"""
    response = client.get("/api/v1/analytics")
    assert response.status_code == 401

