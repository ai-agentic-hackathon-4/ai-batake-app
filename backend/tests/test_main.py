"""Tests for FastAPI endpoints in main.py"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Firestore before importing main
with patch('google.cloud.firestore.AsyncClient'):
    from main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestWeatherEndpoint:
    """Tests for /api/weather endpoint"""
    
    @patch('main.get_weather_from_agent')
    def test_weather_success(self, mock_weather, client):
        """Test successful weather request"""
        mock_weather.return_value = "Weather is sunny"
        
        response = client.post("/api/weather", json={"region": "Tokyo"})
        
        assert response.status_code == 200
        assert "message" in response.json()
        assert response.json()["message"] == "Weather is sunny"
        mock_weather.assert_called_once_with("Tokyo")
    
    @patch('main.get_weather_from_agent')
    def test_weather_error(self, mock_weather, client):
        """Test weather request error handling"""
        mock_weather.side_effect = Exception("API Error")
        
        response = client.post("/api/weather", json={"region": "Tokyo"})
        
        assert response.status_code == 500
        assert "detail" in response.json()


class TestSensorEndpoints:
    """Tests for sensor-related endpoints"""
    
    @patch('main.get_recent_sensor_logs')
    def test_get_latest_sensor_log_success(self, mock_logs, client):
        """Test successful retrieval of latest sensor log"""
        mock_logs.return_value = [{"temperature": 25, "humidity": 60}]
        
        response = client.get("/api/sensors/latest")
        
        assert response.status_code == 200
        assert response.json() == {"temperature": 25, "humidity": 60}
    
    @patch('main.get_recent_sensor_logs')
    def test_get_latest_sensor_log_empty(self, mock_logs, client):
        """Test empty sensor log retrieval"""
        mock_logs.return_value = []
        
        response = client.get("/api/sensors/latest")
        
        assert response.status_code == 200
        assert response.json() == {}
    
    @patch('main.get_sensor_history')
    def test_get_sensor_history_success(self, mock_history, client):
        """Test successful sensor history retrieval"""
        mock_history.return_value = [{"timestamp": "2024-01-01", "temp": 20}]
        
        response = client.get("/api/sensor-history?hours=24")
        
        assert response.status_code == 200
        assert "data" in response.json()
        mock_history.assert_called_once_with(hours=24)
    
    @patch('main.get_sensor_history')
    def test_get_sensor_history_error(self, mock_history, client):
        """Test sensor history error handling"""
        mock_history.side_effect = Exception("Database Error")
        
        response = client.get("/api/sensor-history")
        
        assert response.status_code == 500


class TestVegetableEndpoints:
    """Tests for vegetable-related endpoints"""
    
    @patch('main.get_latest_vegetable')
    def test_get_latest_vegetable_success(self, mock_vegetable, client):
        """Test successful latest vegetable retrieval"""
        mock_vegetable.return_value = {"name": "Tomato", "status": "completed"}
        
        response = client.get("/api/vegetables/latest")
        
        assert response.status_code == 200
        assert response.json()["name"] == "Tomato"
    
    @patch('main.get_latest_vegetable')
    def test_get_latest_vegetable_empty(self, mock_vegetable, client):
        """Test empty latest vegetable retrieval"""
        mock_vegetable.return_value = None
        
        response = client.get("/api/vegetables/latest")
        
        assert response.status_code == 200
        assert response.json() == {}
    
    @patch('main.get_all_vegetables')
    def test_list_vegetables_success(self, mock_vegetables, client):
        """Test successful vegetables list retrieval"""
        mock_vegetables.return_value = [
            {"name": "Tomato", "status": "completed"},
            {"name": "Cucumber", "status": "processing"}
        ]
        
        response = client.get("/api/vegetables")
        
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestRegisterSeedEndpoint:
    """Tests for /api/register-seed endpoint"""
    
    @patch('main.analyze_seed_packet')
    @patch('main.init_vegetable_status')
    def test_register_seed_success(self, mock_init, mock_analyze, client):
        """Test successful seed registration"""
        mock_analyze.return_value = '{"name": "Tomato", "visible_instructions": "test"}'
        mock_init.return_value = "test-doc-id"
        
        # Create a fake image file
        files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
        
        response = client.post("/api/register-seed", files=files)
        
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"
        assert response.json()["document_id"] == "test-doc-id"
        assert "vegetable" in response.json()
    
    @patch('main.analyze_seed_packet')
    def test_register_seed_analysis_error(self, mock_analyze, client):
        """Test seed registration with analysis error"""
        mock_analyze.side_effect = Exception("Analysis failed")
        
        files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
        
        response = client.post("/api/register-seed", files=files)
        
        assert response.status_code == 500


class TestSeedGuideJobEndpoints:
    """Tests for /api/seed-guide/jobs endpoints"""
    
    @pytest.mark.asyncio
    @patch('main.db')
    async def test_create_seed_guide_job_success(self, mock_db, client):
        """Test successful seed guide job creation"""
        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref
        
        files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
        
        response = client.post("/api/seed-guide/jobs", files=files)
        
        assert response.status_code == 200
        assert "job_id" in response.json()
    
    @pytest.mark.asyncio
    @patch('main.db')
    async def test_get_seed_guide_job_not_found(self, mock_db, client):
        """Test getting non-existent job"""
        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref
        mock_doc_ref.get.return_value = mock_doc
        
        response = client.get("/api/seed-guide/jobs/non-existent-id")
        
        assert response.status_code == 404
