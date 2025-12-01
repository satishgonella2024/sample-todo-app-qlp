import pytest
from fastapi.testclient import TestClient
from main import app
import json


client = TestClient(app)


class TestUserTodoIntegration:
    """Integration tests for user and todo workflows"""

    def test_user_registration_and_login_flow(self):
        """Test complete user registration and login flow"""
        # Register new user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        register_response = client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]
        assert user_id is not None

        # Login with credentials
        login_data = {
            "username": "testuser",
            "password": "SecurePass123!"
        }
        login_response = client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        assert token is not None
        assert len(token) > 0

    def test_authenticated_user_create_todo(self):
        """Test authenticated user creating a todo"""
        # Register and login
        user_data = {
            "username": "todouser",
            "email": "todouser@example.com",
            "password": "Pass123!"
        }
        client.post("/api/auth/register", json=user_data)
        login_response = client.post("/api/auth/login", json={
            "username": "todouser",
            "password": "Pass123!"
        })
        token = login_response.json()["access_token"]

        # Create todo with authentication
        headers = {"Authorization": f"Bearer {token}"}
        todo_data = {
            "title": "Authenticated Todo",
            "description": "Created by authenticated user",
            "completed": False
        }
        response = client.post("/api/todos", json=todo_data, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Authenticated Todo"

    def test_unauthenticated_user_cannot_create_todo(self):
        """Test that unauthenticated users cannot create todos"""
        todo_data = {
            "title": "Unauthorized Todo",
            "description": "Should fail",
            "completed": False
        }
        response = client.post("/api/todos", json=todo_data)
        assert response.status_code in [401, 403]

    def test_complete_todo_workflow(self):
        """Test complete todo lifecycle: create, read, update, delete"""
        # Create
        create_data = {
            "title": "Workflow Todo",
            "description": "Testing complete workflow",
            "completed": False
        }
        create_response = client.post("/api/todos", json=create_data)
        assert create_response.status_code == 201
        todo_id = create_response.json()["id"]

        # Read
        read_response = client.get(f"/api/todos/{todo_id}")
        assert read_response.status_code == 200
        assert read_response.json()["title"] == "Workflow Todo"

        # Update
        update_data = {
            "title": "Updated Workflow Todo",
            "description": "Updated description",
            "completed": True
        }
        update_response = client.put(f"/api/todos/{todo_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["completed"] == True

        # Delete
        delete_response = client.delete(f"/api/todos/{todo_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        verify_response = client.get(f"/api/todos/{todo_id}")
        assert verify_response.status_code == 404

    def test_multiple_users_separate_todos(self):
        """Test that different users have separate todo lists"""
        # User 1
        user1_data = {
            "username": "user1",
            "email": "user1@example.com",
            "password": "Pass123!"
        }
        client.post("/api/auth/register", json=user1_data)
        login1 = client.post("/api/auth/login", json={
            "username": "user1",
            "password": "Pass123!"
        })
        token1 = login1.json()["access_token"]

        # User 2
        user2_data = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "Pass123!"
        }
        client.post("/api/auth/register", json=user2_data)
        login2 = client.post("/api/auth/login", json={
            "username": "user2",
            "password": "Pass123!"
        })
        token2 = login2.json()["access_token"]

        # User 1 creates todo
        headers1 = {"Authorization": f"Bearer {token1}"}
        client.post("/api/todos", json={"title": "User 1 Todo"}, headers=headers1)

        # User 2 creates todo
        headers2 = {"Authorization": f"Bearer {token2}"}
        client.post("/api/todos", json={"title": "User 2 Todo"}, headers=headers2)

        # Verify separation
        todos1 = client.get("/api/todos", headers=headers1).json()
        todos2 = client.get("/api/todos", headers=headers2).json()

        assert any(t["title"] == "User 1 Todo" for t in todos1)
        assert not any(t["title"] == "User 2 Todo" for t in todos1)
        assert any(t["title"] == "User 2 Todo" for t in todos2)
        assert not any(t["title"] == "User 1 Todo" for t in todos2)

    def test_bulk_todo_operations(self):
        """Test creating and managing multiple todos"""
        todo_titles = ["Todo 1", "Todo 2", "Todo 3", "Todo 4", "Todo 5"]
        created_ids = []

        # Create multiple todos
        for title in todo_titles:
            response = client.post("/api/todos", json={
                "title": title,
                "completed": False
            })
            assert response.status_code == 201
            created_ids.append(response.json()["id"])

        # Verify all created
        all_todos = client.get("/api/todos").json()
        assert len([t for t in all_todos if t["id"] in created_ids]) == 5

        # Mark some as completed
        for todo_id in created_ids[:3]:
            response = client.put(f"/api/todos/{todo_id}", json={
                "completed": True
            })
            assert response.status_code == 200

        # Verify completion status
        completed_todos = client.get("/api/todos?completed=true").json()
        assert len([t for t in completed_todos if t["id"] in created_ids[:3]]) == 3