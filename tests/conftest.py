import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import json


@pytest.fixture(scope="session")
def test_database():
    """Create test database engine"""
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture(scope="function")
def db_session(test_database):
    """Create a new database session for each test"""
    from database import Base

    Base.metadata.create_all(bind=test_database)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_database)
    session = TestingSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=test_database)


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database session override"""
    from main import app, get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Provide sample user data for tests"""
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test User"
    }


@pytest.fixture
def sample_todo_data():
    """Provide sample todo data for tests"""
    return {
        "title": "Test Todo Item",
        "description": "This is a test todo description",
        "completed": False,
        "priority": "medium"
    }


@pytest.fixture
def authenticated_user(client, sample_user_data):
    """Create and authenticate a user, return token"""
    client.post("/api/auth/register", json=sample_user_data)
    login_response = client.post("/api/auth/login", json={
        "username": sample_user_data["username"],
        "password": sample_user_data["password"]
    })
    token = login_response.json()["access_token"]
    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }