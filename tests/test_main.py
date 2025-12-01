import pytest
from fastapi.testclient import TestClient
from main import app
from datetime import datetime


client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check_returns_200(self):
        """Test that health endpoint returns 200 status"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_health_check_response_structure(self):
        """Test health endpoint response structure"""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert isinstance(data["status"], str)


class TestTodoEndpoints:
    """Test todo CRUD operations"""

    def test_create_todo_success(self):
        """Test creating a new todo item"""
        todo_data = {
            "title": "Test Todo",
            "description": "Test Description",
            "completed": False
        }
        response = client.post("/api/todos", json=todo_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == todo_data["title"]
        assert data["description"] == todo_data["description"]
        assert data["completed"] == False
        assert "id" in data

    def test_create_todo_missing_title(self):
        """Test creating todo without required title"""
        todo_data = {
            "description": "Test Description",
            "completed": False
        }
        response = client.post("/api/todos", json=todo_data)
        assert response.status_code == 422

    def test_create_todo_empty_title(self):
        """Test creating todo with empty title"""
        todo_data = {
            "title": "",
            "description": "Test Description",
            "completed": False
        }
        response = client.post("/api/todos", json=todo_data)
        assert response.status_code == 400

    def test_get_all_todos(self):
        """Test retrieving all todos"""
        response = client.get("/api/todos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_todo_by_id_success(self):
        """Test retrieving a specific todo by ID"""
        create_response = client.post("/api/todos", json={
            "title": "Test Todo",
            "description": "Test Description",
            "completed": False
        })
        todo_id = create_response.json()["id"]

        response = client.get(f"/api/todos/{todo_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == "Test Todo"

    def test_get_todo_by_id_not_found(self):
        """Test retrieving non-existent todo"""
        response = client.get("/api/todos/99999")
        assert response.status_code == 404

    def test_update_todo_success(self):
        """Test updating an existing todo"""
        create_response = client.post("/api/todos", json={
            "title": "Original Title",
            "description": "Original Description",
            "completed": False
        })
        todo_id = create_response.json()["id"]

        update_data = {
            "title": "Updated Title",
            "description": "Updated Description",
            "completed": True
        }
        response = client.put(f"/api/todos/{todo_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["completed"] == True

    def test_update_todo_not_found(self):
        """Test updating non-existent todo"""
        update_data = {
            "title": "Updated Title",
            "description": "Updated Description",
            "completed": True
        }
        response = client.put("/api/todos/99999", json=update_data)
        assert response.status_code == 404

    def test_delete_todo_success(self):
        """Test deleting a todo"""
        create_response = client.post("/api/todos", json={
            "title": "To Delete",
            "description": "Will be deleted",
            "completed": False
        })
        todo_id = create_response.json()["id"]

        response = client.delete(f"/api/todos/{todo_id}")
        assert response.status_code == 204

        get_response = client.get(f"/api/todos/{todo_id}")
        assert get_response.status_code == 404

    def test_delete_todo_not_found(self):
        """Test deleting non-existent todo"""
        response = client.delete("/api/todos/99999")
        assert response.status_code == 404

    def test_filter_todos_by_completed(self):
        """Test filtering todos by completion status"""
        client.post("/api/todos", json={"title": "Completed", "completed": True})
        client.post("/api/todos", json={"title": "Not Completed", "completed": False})

        response = client.get("/api/todos?completed=true")
        assert response.status_code == 200
        data = response.json()
        assert all(todo["completed"] for todo in data)

    def test_create_todo_with_null_description(self):
        """Test creating todo with null description"""
        todo_data = {"title": "Test", "completed": False}
        response = client.post("/api/todos", json=todo_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["title"] == "Test"