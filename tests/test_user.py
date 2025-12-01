import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


class TestUserRegistration:
    """Test user registration functionality"""

    def test_register_user_success(self):
        """Test successful user registration"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPass123!"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "password" not in data
        assert "id" in data

    def test_register_user_duplicate_username(self):
        """Test registration with duplicate username"""
        user_data = {
            "username": "duplicate",
            "email": "first@example.com",
            "password": "Pass123!"
        }
        client.post("/api/auth/register", json=user_data)

        duplicate_data = {
            "username": "duplicate",
            "email": "second@example.com",
            "password": "Pass123!"
        }
        response = client.post("/api/auth/register", json=duplicate_data)
        assert response.status_code == 400

    def test_register_user_duplicate_email(self):
        """Test registration with duplicate email"""
        user_data = {
            "username": "user1",
            "email": "duplicate@example.com",
            "password": "Pass123!"
        }
        client.post("/api/auth/register", json=user_data)

        duplicate_data = {
            "username": "user2",
            "email": "duplicate@example.com",
            "password": "Pass123!"
        }
        response = client.post("/api/auth/register", json=duplicate_data)
        assert response.status_code == 400

    def test_register_user_invalid_email(self):
        """Test registration with invalid email format"""
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "Pass123!"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422

    def test_register_user_weak_password(self):
        """Test registration with weak password"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code in [400, 422]

    def test_register_user_missing_fields(self):
        """Test registration with missing required fields"""
        user_data = {"username": "testuser"}
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422


class TestUserLogin:
    """Test user login functionality"""

    def test_login_success(self):
        """Test successful user login"""
        user_data = {
            "username": "loginuser",
            "email": "login@example.com",
            "password": "LoginPass123!"
        }
        client.post("/api/auth/register", json=user_data)

        login_data = {
            "username": "loginuser",
            "password": "LoginPass123!"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self):
        """Test login with incorrect password"""
        login_data = {
            "username": "loginuser",
            "password": "WrongPassword"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        """Test login with non-existent username"""
        login_data = {"username": "nonexistent", "password": "Pass123!"}
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401