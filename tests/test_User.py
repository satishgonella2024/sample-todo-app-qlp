import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


class TestUserProfile:
    """Test user profile management"""

    def test_get_user_profile_authenticated(self):
        """Test retrieving authenticated user profile"""
        user_data = {
            "username": "profileuser",
            "email": "profile@example.com",
            "password": "Pass123!"
        }
        client.post("/api/auth/register", json=user_data)
        login_response = client.post("/api/auth/login", json={
            "username": "profileuser",
            "password": "Pass123!"
        })
        token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/users/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "profileuser"
        assert data["email"] == "profile@example.com"
        assert "password" not in data

    def test_get_user_profile_unauthenticated(self):
        """Test retrieving profile without authentication"""
        response = client.get("/api/users/me")
        assert response.status_code in [401, 403]

    def test_update_user_profile(self):
        """Test updating user profile"""
        user_data = {
            "username": "updateuser",
            "email": "update@example.com",
            "password": "Pass123!"
        }
        client.post("/api/auth/register", json=user_data)
        login_response = client.post("/api/auth/login", json={
            "username": "updateuser",
            "password": "Pass123!"
        })
        token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        update_data = {
            "email": "newemail@example.com",
            "full_name": "Updated Name"
        }
        response = client.put("/api/users/me", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@example.com"

    def test_get_user_by_id(self):
        """Test retrieving user by ID"""
        user_data = {
            "username": "iduser",
            "email": "iduser@example.com",
            "password": "Pass123!"
        }
        register_response = client.post("/api/auth/register", json=user_data)
        user_id = register_response.json()["id"]

        response = client.get(f"/api/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == "iduser"

    def test_get_user_by_id_not_found(self):
        """Test retrieving non-existent user"""
        response = client.get("/api/users/99999")
        assert response.status_code == 404


class TestUserValidation:
    """Test user input validation"""

    def test_username_too_short(self):
        """Test username minimum length validation"""
        user_data = {
            "username": "ab",
            "email": "test@example.com",
            "password": "Pass123!"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code in [400, 422]

    def test_username_too_long(self):
        """Test username maximum length validation"""
        user_data = {
            "username": "a" * 51,
            "email": "test@example.com",
            "password": "Pass123!"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code in [400, 422]

    def test_username_special_characters(self):
        """Test username with invalid special characters"""
        user_data = {
            "username": "user@#$%",
            "email": "test@example.com",
            "password": "Pass123!"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code in [400, 422]

    def test_email_format_validation(self):
        """Test various email format validations"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "user@example"
        ]

        for email in invalid_emails:
            user_data = {
                "username": f"user{invalid_emails.index(email)}",
                "email": email,
                "password": "Pass123!"
            }
            response = client.post("/api/auth/register", json=user_data)
            assert response.status_code == 422

    def test_password_null_value(self):
        """Test registration with null password"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": None
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422