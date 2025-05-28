import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestOptimizationController:
    """Test cases for optimization API endpoints"""
    
    @patch('app.api.optimization_controller.requests.get')
    def test_get_optimization_status_returns_status(self, mock_get):
        """Test that get optimization status returns proper status structure"""
        # Mock the Django API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "idle"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        response = client.get("/optimization/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert isinstance(data["status"], str)
        assert data["status"] == "idle"