import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestOptimizationController:
    """Test cases for optimization API endpoints"""
    
    def test_get_optimization_status_returns_status(self):
        """Test that get optimization status returns proper status structure"""
        response = client.get("/optimization/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert isinstance(data["status"], str)