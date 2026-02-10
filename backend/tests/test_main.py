"""Tests for FastAPI endpoints in main.py"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
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
    
    @patch('main.process_research')
    @patch('main.analyze_seed_packet')
    @patch('main.init_vegetable_status')
    def test_register_seed_success(self, mock_init, mock_analyze, mock_process, client):
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
    
    @patch('main.process_seed_guide')
    @patch('main._upload_to_gcs_sync', return_value='https://storage.googleapis.com/bucket/test.jpg')
    @patch('main.db')
    def test_create_seed_guide_job_success(self, mock_db, mock_upload, mock_process, client):
        """Test successful seed guide job creation"""
        # Mock the async Firestore client
        mock_collection = Mock()
        mock_doc_ref = AsyncMock()
        mock_doc_ref.set = AsyncMock()
        
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref
        
        files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
        
        response = client.post("/api/seed-guide/generate", files=files)
        
        assert response.status_code == 200
        assert "job_id" in response.json()
    
    @patch('main.db')
    def test_get_seed_guide_job_not_found(self, mock_db, client):
        """Test getting non-existent job"""
        mock_collection = Mock()
        mock_doc_ref = AsyncMock()
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref
        mock_doc_ref.get = AsyncMock(return_value=mock_doc)
        
        response = client.get("/api/seed-guide/jobs/non-existent-id")
        
        assert response.status_code == 404


class TestAgentLogsEndpoint:
    """Tests for /api/agent-logs endpoint"""
    
    @patch('main.get_agent_execution_logs')
    def test_get_agent_logs_success(self, mock_get_logs, client):
        """Test successful agent logs retrieval"""
        mock_data = [
            {"id": "1", "action": "test", "timestamp": "2024-01-01"}
        ]
        mock_get_logs.return_value = mock_data
        
        response = client.get("/api/agent-logs")
        
        assert response.status_code == 200
        assert response.json() == {"logs": mock_data}
        mock_get_logs.assert_called_once_with(limit=20)
        
    @patch('main.get_agent_execution_logs')
    def test_get_agent_logs_error(self, mock_get_logs, client):
        """Test error handling in agent logs endpoint"""
        mock_get_logs.side_effect = Exception("Internal Error")
        
        response = client.get("/api/agent-logs")
        
        assert response.status_code == 500
        assert "detail" in response.json()


class TestDiaryEndpoints:
    """Tests for /api/diary/* endpoints"""
    
    @patch('main.get_all_diaries')
    def test_list_diaries_success(self, mock_get_diaries, client):
        """Test successful diary list retrieval"""
        mock_diaries = [
            {"id": "2025-01-01", "date": "2025-01-01", "ai_summary": "Test summary"}
        ]
        mock_get_diaries.return_value = mock_diaries
        
        response = client.get("/api/diary/list")
        
        assert response.status_code == 200
        assert response.json() == {"diaries": mock_diaries}
        mock_get_diaries.assert_called_once_with(limit=30, offset=0)
    
    @patch('main.get_all_diaries')
    def test_list_diaries_with_pagination(self, mock_get_diaries, client):
        """Test diary list with pagination parameters"""
        mock_get_diaries.return_value = []
        
        response = client.get("/api/diary/list?limit=10&offset=5")
        
        assert response.status_code == 200
        mock_get_diaries.assert_called_once_with(limit=10, offset=5)
    
    @patch('main.get_diary_by_date')
    def test_get_diary_success(self, mock_get_diary, client):
        """Test successful diary retrieval by date"""
        mock_diary = {
            "id": "2025-01-01",
            "date": "2025-01-01",
            "ai_summary": "Test summary",
            "observations": "Test observations",
            "recommendations": "Test recommendations"
        }
        mock_get_diary.return_value = mock_diary
        
        response = client.get("/api/diary/2025-01-01")
        
        assert response.status_code == 200
        assert response.json() == mock_diary
        mock_get_diary.assert_called_once_with("2025-01-01")
    
    @patch('main.get_diary_by_date')
    def test_get_diary_not_found(self, mock_get_diary, client):
        """Test diary not found error"""
        mock_get_diary.return_value = None
        
        response = client.get("/api/diary/2025-01-01")
        
        assert response.status_code == 404
        assert "detail" in response.json()
    
    @patch('main.process_daily_diary')
    def test_generate_daily_diary_success(self, mock_process, client):
        """Test successful daily diary generation trigger"""
        response = client.post("/api/diary/generate-daily")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "accepted"
        assert "date" in result
    
    @patch('main.process_daily_diary', new_callable=AsyncMock)
    def test_generate_manual_diary_success(self, mock_process, client):
        """Test successful manual diary generation (SSE streaming response)"""
        response = client.post(
            "/api/diary/generate-manual",
            json={"date": "2025-01-15"}
        )
        
        assert response.status_code == 200
        # Endpoint returns SSE stream, not JSON
        assert 'text/event-stream' in response.headers.get('content-type', '')
        body = response.text
        assert 'completed' in body or 'processing' in body
    
    def test_generate_manual_diary_invalid_date(self, client):
        """Test manual diary generation with invalid date"""
        response = client.post(
            "/api/diary/generate-manual",
            json={"date": "invalid-date"}
        )
        
        assert response.status_code == 400
        assert "Invalid date format" in response.json()["detail"]


class TestPlantCameraEndpoint:
    """Tests for /api/plant-camera/latest endpoint"""
    
    @patch('main.storage.Client')
    def test_get_latest_plant_image_success(self, mock_storage, client):
        """Test successful retrieval of latest plant camera image"""
        mock_blob = Mock()
        mock_blob.name = "logger-captures/test.jpg"
        mock_blob.time_created = Mock(isoformat=Mock(return_value="2025-01-01T12:00:00"))
        mock_blob.download_as_bytes.return_value = b"fake image data"
        mock_blob.content_type = "image/jpeg"
        
        mock_bucket = Mock()
        mock_bucket.list_blobs.return_value = [mock_blob]
        
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_storage.return_value = mock_client
        
        response = client.get("/api/plant-camera/latest")
        
        assert response.status_code == 200
        data = response.json()
        assert "image" in data
        assert "timestamp" in data
    
    @patch('main.storage.Client')
    def test_get_latest_plant_image_no_images(self, mock_storage, client):
        """Test when no plant images are found"""
        mock_bucket = Mock()
        mock_bucket.list_blobs.return_value = []
        
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_storage.return_value = mock_client
        
        response = client.get("/api/plant-camera/latest")
        
        assert response.status_code == 200
        assert "error" in response.json()


class TestAutoGenerateDiaryEndpoint:
    """Tests for /api/diary/auto-generate endpoint"""
    
    @patch('main.process_daily_diary')
    @patch.dict('os.environ', {'DIARY_API_KEY': 'test-key'})
    def test_auto_generate_diary_success(self, mock_process, client):
        """Test successful auto diary generation with correct key"""
        response = client.post("/api/diary/auto-generate?key=test-key")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "accepted"
        assert "date" in result
    
    @patch.dict('os.environ', {'DIARY_API_KEY': 'test-key'})
    def test_auto_generate_diary_unauthorized(self, client):
        """Test unauthorized access with wrong key"""
        response = client.post("/api/diary/auto-generate?key=wrong-key")
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Unauthorized"
    
    @patch('main.process_daily_diary')
    @patch.dict('os.environ', {}, clear=True)
    def test_auto_generate_diary_no_key_required(self, mock_process, client):
        """Test access allowed when no API key is configured"""
        response = client.post("/api/diary/auto-generate")
        
        assert response.status_code == 200


class TestDiaryImageEndpoint:
    """Tests for /api/diary/image/{date} endpoint"""
    
    @patch('main.get_diary_by_date')
    def test_get_diary_image_not_found(self, mock_get_diary, client):
        """Test diary image not found"""
        mock_get_diary.return_value = None
        
        response = client.get("/api/diary/image/2025-01-01")
        
        assert response.status_code == 404
    
    @patch('main.get_diary_by_date')
    def test_get_diary_image_no_image_url(self, mock_get_diary, client):
        """Test diary exists but has no image URL"""
        mock_get_diary.return_value = {"date": "2025-01-01", "plant_image_url": None}
        
        response = client.get("/api/diary/image/2025-01-01")
        
        assert response.status_code == 404
    
    @patch('main.storage.Client')
    @patch('main.get_diary_by_date')
    def test_get_diary_image_success(self, mock_get_diary, mock_storage, client):
        """Test successful diary image retrieval"""
        mock_get_diary.return_value = {
            "date": "2025-01-01",
            "plant_image_url": "gs://test-bucket/path/to/image.png"
        }
        
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"fake png data"
        
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_storage.return_value = mock_client
        
        response = client.get("/api/diary/image/2025-01-01")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
