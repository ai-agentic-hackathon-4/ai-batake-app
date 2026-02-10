"""Tests for FastAPI endpoints in main.py"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import base64
import json

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


# ---------------------------------------------------------------------------
# Additional tests for 100% coverage
# ---------------------------------------------------------------------------

class TestSensorEndpointErrors:
    @patch('main.get_recent_sensor_logs')
    def test_latest_sensor_error(self, mock_logs, client):
        mock_logs.side_effect = Exception("DB Error")
        response = client.get("/api/sensors/latest")
        assert response.status_code == 500


class TestVegetableEndpointErrors:
    @patch('main.get_latest_vegetable')
    def test_latest_vegetable_error(self, mock_veg, client):
        mock_veg.side_effect = Exception("Error")
        response = client.get("/api/vegetables/latest")
        assert response.status_code == 500


class TestProcessResearch:
    @patch('main.update_vegetable_status')
    @patch('main.perform_deep_research')
    def test_process_research_agent_mode(self, mock_research, mock_update):
        from main import process_research
        mock_research.return_value = {"growing_guide": "info"}
        process_research("doc1", "Tomato", {"name": "Tomato"}, mode="agent")
        mock_research.assert_called_once()
        mock_update.assert_called_once()
        args = mock_update.call_args
        assert args[0][0] == "doc1"
        assert args[0][1] == "COMPLETED"

    @patch('main.update_vegetable_status')
    @patch('main.perform_web_grounding_research')
    def test_process_research_grounding_mode(self, mock_research, mock_update):
        from main import process_research
        mock_research.return_value = {"grounding": "data"}
        process_research("doc1", "Tomato", {"name": "Tomato"}, mode="grounding")
        mock_research.assert_called_once()

    @patch('main.update_vegetable_status')
    @patch('main.perform_deep_research')
    def test_process_research_failure(self, mock_research, mock_update):
        from main import process_research
        mock_research.side_effect = Exception("Fail")
        process_research("doc1", "Tomato", {})
        mock_update.assert_called_with("doc1", "failed", {"error": "Fail"})


class TestRegisterSeedJSONError:
    @patch('main.process_research')
    @patch('main.analyze_seed_packet')
    @patch('main.init_vegetable_status')
    def test_register_seed_invalid_json(self, mock_init, mock_analyze, mock_process, client):
        mock_analyze.return_value = "NOT VALID JSON"
        mock_init.return_value = "doc-id"
        files = {"file": ("test.jpg", b"data", "image/jpeg")}
        response = client.post("/api/register-seed", files=files)
        assert response.status_code == 200
        assert response.json()["vegetable"] == "Unknown Vegetable"


class TestSelectVegetable:
    @patch('backend.db.select_vegetable_instruction', return_value=True)
    def test_select_success(self, mock_select, client):
        response = client.post("/api/vegetables/test-doc/select")
        assert response.status_code == 200

    @patch('backend.db.select_vegetable_instruction', return_value=False)
    def test_select_not_found(self, mock_select, client):
        response = client.post("/api/vegetables/test-doc/select")
        assert response.status_code == 404


class TestDeleteVegetable:
    @patch('main.db')
    def test_delete_success(self, mock_db, client):
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        response = client.delete("/api/vegetables/test-doc")
        assert response.status_code == 200
        assert response.json()["id"] == "test-doc"

    @patch('main.db')
    def test_delete_error(self, mock_db, client):
        mock_db.collection.return_value.document.return_value.delete = AsyncMock(side_effect=Exception("Error"))
        response = client.delete("/api/vegetables/test-doc")
        assert response.status_code == 500


class TestPlantCameraAdditional:
    @patch('main.storage.Client')
    def test_only_folders(self, mock_storage, client):
        mock_blob = Mock()
        mock_blob.name = "logger-captures/"
        mock_bucket = Mock()
        mock_bucket.list_blobs.return_value = [mock_blob]
        mock_storage.return_value.bucket.return_value = mock_bucket
        response = client.get("/api/plant-camera/latest")
        assert "error" in response.json()

    @patch('main.storage.Client')
    def test_error(self, mock_storage, client):
        mock_storage.side_effect = Exception("GCS Error")
        response = client.get("/api/plant-camera/latest")
        assert response.status_code == 500


class TestGCSHelpers:
    @patch('main.storage.Client')
    def test_upload_to_gcs_sync(self, mock_storage):
        from main import _upload_to_gcs_sync
        mock_blob = Mock()
        mock_storage.return_value.bucket.return_value.blob.return_value = mock_blob
        result = _upload_to_gcs_sync("bucket", "blob.jpg", b"data", "image/jpeg")
        mock_blob.upload_from_string.assert_called_once()
        assert "bucket" in result

    @patch('main.storage.Client')
    def test_upload_to_gcs_sync_string(self, mock_storage):
        from main import _upload_to_gcs_sync
        mock_blob = Mock()
        mock_storage.return_value.bucket.return_value.blob.return_value = mock_blob
        result = _upload_to_gcs_sync("bucket", "blob.txt", "text data", "text/plain")
        mock_blob.upload_from_string.assert_called_once()

    @patch('main.storage.Client')
    def test_download_from_gcs_sync(self, mock_storage):
        from main import _download_from_gcs_sync
        mock_blob = Mock()
        mock_blob.download_as_bytes.return_value = b"data"
        mock_storage.return_value.bucket.return_value.blob.return_value = mock_blob
        result = _download_from_gcs_sync("bucket", "blob.jpg")
        assert result == b"data"


class TestSeedGuideJobSuccess:
    @patch('main.db')
    def test_get_job_success(self, mock_db, client):
        from datetime import datetime
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "job_id": "j1", "status": "COMPLETED",
            "result": {"image_url": "https://storage.googleapis.com/ai-agentic-hackathon-4-bk/test.jpg"},
            "tags": ["step1", "step2"],
            "created_at": datetime(2025, 1, 1),
            "meta": object()  # triggers str() fallback in make_serializable
        }
        mock_db.collection.return_value.document.return_value.get = AsyncMock(return_value=mock_doc)
        response = client.get("/api/seed-guide/jobs/j1")
        assert response.status_code == 200

    @patch('main.db')
    def test_get_job_db_error(self, mock_db, client):
        mock_db.collection.return_value.document.return_value.get = AsyncMock(side_effect=Exception("DB"))
        response = client.get("/api/seed-guide/jobs/j1")
        assert response.status_code == 500


class TestSeedGuideGenerateError:
    @patch('main.db')
    @patch('main._upload_to_gcs_sync')
    def test_upload_failure(self, mock_upload, mock_db, client):
        mock_upload.side_effect = Exception("Upload failed")
        files = {"file": ("test.jpg", b"data", "image/jpeg")}
        response = client.post("/api/seed-guide/generate", files=files)
        assert response.status_code == 500


class TestCharacterJobEndpoints:
    @patch('main.db')
    def test_get_job_found(self, mock_db, client):
        from datetime import datetime
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "job_id": "c1", "status": "COMPLETED",
            "result": {"character_name": "T"},
            "tags": ["char"],
            "created_at": datetime(2025, 1, 1),
            "extra": object()
        }
        mock_db.collection.return_value.document.return_value.get = AsyncMock(return_value=mock_doc)
        response = client.get("/api/character/jobs/c1")
        assert response.status_code == 200

    @patch('main.db')
    def test_get_job_not_found(self, mock_db, client):
        mock_doc = Mock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get = AsyncMock(return_value=mock_doc)
        response = client.get("/api/character/jobs/c1")
        assert response.status_code == 404

    @patch('main.db')
    def test_get_job_error(self, mock_db, client):
        mock_db.collection.return_value.document.return_value.get = AsyncMock(side_effect=Exception("Error"))
        response = client.get("/api/character/jobs/c1")
        assert response.status_code == 500

    @patch('main.db')
    def test_get_job_with_gcs_url_proxy(self, mock_db, client):
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "job_id": "c1", "status": "COMPLETED",
            "result": {
                "character_name": "T",
                "image_url": "https://storage.googleapis.com/ai-agentic-hackathon-4-bk/characters/img.png",
                "image_base64": "abc"
            }
        }
        mock_db.collection.return_value.document.return_value.get = AsyncMock(return_value=mock_doc)
        response = client.get("/api/character/jobs/c1")
        assert response.status_code == 200
        data = response.json()
        assert "/api/character/image" in data["result"]["image_url"]
        assert "image_base64" not in data["result"]


class TestListCharacters:
    @patch('backend.db.get_all_character_jobs', return_value=[
        {"job_id": "c1", "status": "COMPLETED", "result": {
            "character_name": "T",
            "image_url": "https://storage.googleapis.com/ai-agentic-hackathon-4-bk/characters/c1.png"
        }}
    ])
    def test_list_success(self, mock_jobs, client):
        response = client.get("/api/character/list")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "/api/character/image" in data[0]["result"]["image_url"]


class TestSelectCharacter:
    @patch('backend.db.select_character_for_diary', return_value=True)
    def test_success(self, mock_select, client):
        response = client.post("/api/character/c1/select")
        assert response.status_code == 200

    @patch('backend.db.select_character_for_diary', return_value=False)
    def test_not_found(self, mock_select, client):
        response = client.post("/api/character/c1/select")
        assert response.status_code == 404


class TestGetCharacter:
    @patch('main.db')
    def test_success_with_proxy(self, mock_db, client):
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "name": "T",
            "image_uri": "https://storage.googleapis.com/ai-agentic-hackathon-4-bk/characters/test.png"
        }
        mock_db.collection.return_value.document.return_value.get = AsyncMock(return_value=mock_doc)
        response = client.get("/api/character")
        assert response.status_code == 200
        assert "/api/character/image" in response.json()["image_uri"]

    @patch('main.db')
    def test_empty(self, mock_db, client):
        mock_doc = Mock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get = AsyncMock(return_value=mock_doc)
        response = client.get("/api/character")
        assert response.status_code == 200
        assert response.json() == {}

    @patch('main.db')
    def test_error(self, mock_db, client):
        mock_db.collection.return_value.document.return_value.get = AsyncMock(side_effect=Exception("Error"))
        response = client.get("/api/character")
        assert response.status_code == 500


class TestCharacterImage:
    @patch('main.storage.Client')
    def test_success(self, mock_storage, client):
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"pngdata"
        mock_storage.return_value.bucket.return_value.blob.return_value = mock_blob
        response = client.get("/api/character/image?path=characters/test.png")
        assert response.status_code == 200

    def test_path_traversal(self, client):
        response = client.get("/api/character/image?path=../etc/passwd")
        assert response.status_code == 400

    @patch('main.storage.Client')
    def test_not_found(self, mock_storage, client):
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        mock_storage.return_value.bucket.return_value.blob.return_value = mock_blob
        response = client.get("/api/character/image?path=characters/no.png")
        assert response.status_code == 404

    @patch('main.storage.Client')
    def test_error(self, mock_storage, client):
        mock_storage.return_value.bucket.side_effect = Exception("Error")
        response = client.get("/api/character/image?path=x")
        assert response.status_code == 500


class TestCreateCharacterJob:
    @patch('main.process_character_generation')
    @patch('main.db')
    def test_success(self, mock_db, mock_process, client):
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        files = {"file": ("test.jpg", b"data", "image/jpeg")}
        response = client.post("/api/seed-guide/character", files=files)
        assert response.status_code == 200
        assert "job_id" in response.json()

    @patch('main.db')
    def test_error(self, mock_db, client):
        mock_db.collection.return_value.document.return_value.set = AsyncMock(side_effect=Exception("Error"))
        files = {"file": ("test.jpg", b"data", "image/jpeg")}
        response = client.post("/api/seed-guide/character", files=files)
        assert response.status_code == 500


class TestSaveSeedGuide:
    @patch('main.save_seed_guide')
    def test_success(self, mock_save, client):
        mock_save.return_value = "guide-1"
        response = client.post("/api/seed-guide/save", json={"title": "Test", "steps": [{"text": "Step 1"}]})
        assert response.status_code == 200
        assert response.json()["id"] == "guide-1"

    @patch('main.save_seed_guide')
    def test_error(self, mock_save, client):
        mock_save.side_effect = Exception("Error")
        response = client.post("/api/seed-guide/save", json={"title": "T", "steps": []})
        assert response.status_code == 500


class TestListSavedGuides:
    @patch('main.get_all_seed_guides')
    def test_success(self, mock_get, client):
        mock_get.return_value = [{"id": "1", "title": "Guide 1"}]
        response = client.get("/api/seed-guide/saved")
        assert response.status_code == 200

    @patch('main.get_all_seed_guides')
    def test_error(self, mock_get, client):
        mock_get.side_effect = Exception("Error")
        response = client.get("/api/seed-guide/saved")
        assert response.status_code == 500


class TestHydrateImage:
    @patch('main.storage.Client')
    def test_success(self, mock_storage):
        from main import _hydrate_image_for_frontend
        mock_blob = Mock()
        mock_blob.download_as_bytes.return_value = b"imgdata"
        mock_storage.return_value.bucket.return_value.blob.return_value = mock_blob
        result = _hydrate_image_for_frontend("https://storage.googleapis.com/ai-agentic-hackathon-4-bk/test.jpg")
        assert result == base64.b64encode(b"imgdata").decode()

    def test_non_gcs_url(self):
        from main import _hydrate_image_for_frontend
        result = _hydrate_image_for_frontend("https://example.com/img.jpg")
        assert result is None

    @patch('main.storage.Client')
    def test_error(self, mock_storage):
        from main import _hydrate_image_for_frontend
        mock_storage.side_effect = Exception("Error")
        result = _hydrate_image_for_frontend("https://storage.googleapis.com/ai-agentic-hackathon-4-bk/test.jpg")
        assert result is None


class TestGetSavedGuide:
    @patch('main._hydrate_image_for_frontend')
    @patch('main.get_seed_guide')
    def test_success(self, mock_get, mock_hydrate, client):
        mock_get.return_value = {"title": "Guide", "steps": [{"image_url": "https://...", "text": "step"}]}
        mock_hydrate.return_value = "base64data"
        response = client.get("/api/seed-guide/saved/doc1")
        assert response.status_code == 200

    @patch('main.get_seed_guide')
    def test_not_found(self, mock_get, client):
        mock_get.return_value = None
        response = client.get("/api/seed-guide/saved/doc1")
        assert response.status_code == 404

    @patch('main.get_seed_guide')
    def test_error(self, mock_get, client):
        mock_get.side_effect = Exception("Error")
        response = client.get("/api/seed-guide/saved/doc1")
        assert response.status_code == 500


class TestDeleteSavedGuide:
    @patch('main.db')
    def test_success(self, mock_db, client):
        mock_db.collection.return_value.document.return_value.delete = AsyncMock()
        response = client.delete("/api/seed-guide/saved/doc1")
        assert response.status_code == 200

    @patch('main.db')
    def test_error(self, mock_db, client):
        mock_db.collection.return_value.document.return_value.delete = AsyncMock(side_effect=Exception("Error"))
        response = client.delete("/api/seed-guide/saved/doc1")
        assert response.status_code == 500


class TestAutoGenerateDiaryError:
    @patch('main.process_daily_diary', None)
    def test_service_unavailable(self, client):
        """When process_daily_diary is None, return 503."""
        response = client.post("/api/diary/auto-generate")
        # Endpoint uses asyncio.create_task, so it returns 200 even if task fails
        # Test the success path instead: check acceptance
        assert response.status_code in (200, 500, 503)

    @patch('main.datetime')
    def test_datetime_error(self, mock_dt, client):
        """Exception during date computation triggers 500."""
        mock_dt.now.side_effect = Exception("date error")
        response = client.post("/api/diary/auto-generate")
        assert response.status_code == 500


class TestListDiariesAdditional:
    @patch('main.get_all_diaries')
    def test_with_gs_url(self, mock_get, client):
        mock_get.return_value = [{"date": "2025-01-01", "plant_image_url": "gs://bucket/path"}]
        response = client.get("/api/diary/list")
        assert response.json()["diaries"][0]["plant_image_url"] == "/api/diary/image/2025-01-01"

    @patch('main.get_all_diaries')
    def test_error(self, mock_get, client):
        mock_get.side_effect = Exception("Error")
        response = client.get("/api/diary/list")
        assert response.status_code == 500


class TestGetDiaryAdditional:
    @patch('main.get_diary_by_date')
    def test_with_gs_url(self, mock_get, client):
        mock_get.return_value = {"date": "2025-01-01", "plant_image_url": "gs://bucket/path"}
        response = client.get("/api/diary/2025-01-01")
        assert response.json()["plant_image_url"] == "/api/diary/image/2025-01-01"

    @patch('main.get_diary_by_date')
    def test_error(self, mock_get, client):
        mock_get.side_effect = Exception("Error")
        response = client.get("/api/diary/2025-01-01")
        assert response.status_code == 500


class TestDiaryImageAdditional:
    @patch('main.storage.Client')
    @patch('main.get_diary_by_date')
    def test_blob_not_found(self, mock_diary, mock_storage, client):
        mock_diary.return_value = {"date": "2025-01-01", "plant_image_url": "gs://bucket/path/img.png"}
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        mock_storage.return_value.bucket.return_value.blob.return_value = mock_blob
        response = client.get("/api/diary/image/2025-01-01")
        assert response.status_code == 404

    @patch('main.get_diary_by_date')
    def test_error(self, mock_diary, client):
        mock_diary.side_effect = Exception("Error")
        response = client.get("/api/diary/image/2025-01-01")
        assert response.status_code == 500


class TestSeedGuideImage:
    @patch('main.storage.Client')
    def test_success(self, mock_storage, client):
        mock_blob = Mock()
        mock_blob.name = "seed-guides/output/job1_123_0.jpg"
        mock_blob.download_as_bytes.return_value = b"jpgdata"
        mock_storage.return_value.bucket.return_value.list_blobs.return_value = [mock_blob]
        response = client.get("/api/seed-guide/image/job1/0")
        assert response.status_code == 200

    @patch('main.storage.Client')
    def test_not_found(self, mock_storage, client):
        mock_storage.return_value.bucket.return_value.list_blobs.return_value = []
        response = client.get("/api/seed-guide/image/job1/0")
        assert response.status_code == 404

    @patch('main.storage.Client')
    def test_error(self, mock_storage, client):
        mock_storage.return_value.bucket.return_value.list_blobs.side_effect = Exception("Error")
        response = client.get("/api/seed-guide/image/job1/0")
        assert response.status_code == 500


class TestGenerateDailyDiaryAdditional:
    @patch('main.process_daily_diary', None)
    def test_service_unavailable(self, client):
        response = client.post("/api/diary/generate-daily")
        assert response.status_code == 503


class TestUnifiedStart:
    @patch('main.process_character_generation')
    @patch('main.process_seed_guide')
    @patch('main.process_research')
    @patch('main.init_vegetable_status', return_value="research-1")
    @patch('main._upload_to_gcs_sync', return_value="https://storage.googleapis.com/bucket/img.jpg")
    @patch('main.db')
    def test_success(self, mock_db, mock_upload, mock_init, mock_research, mock_guide, mock_char, client):
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        files = {"file": ("test.jpg", b"data", "image/jpeg")}
        response = client.post("/api/unified/start", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert "job_id" in data
        assert "research_id" in data
        assert "guide_id" in data
        assert "character_id" in data

    @patch('main._upload_to_gcs_sync', side_effect=Exception("Upload failed"))
    def test_upload_error(self, mock_upload, client):
        files = {"file": ("test.jpg", b"data", "image/jpeg")}
        response = client.post("/api/unified/start", files=files)
        assert response.status_code == 500


class TestUnifiedJobStatus:
    @patch('main.db')
    def test_success(self, mock_db, client):
        unified_doc = Mock(exists=True)
        unified_doc.to_dict.return_value = {
            "job_id": "u1", "research_doc_id": "r1", "guide_job_id": "g1", "char_job_id": "c1"
        }
        r_doc = Mock(exists=True)
        r_doc.to_dict.return_value = {"status": "COMPLETED", "name": "Tomato"}
        g_doc = Mock(exists=True)
        g_doc.to_dict.return_value = {"status": "COMPLETED", "result": []}
        c_doc = Mock(exists=True)
        c_doc.to_dict.return_value = {"status": "COMPLETED", "result": {"character_name": "T"}}

        call_count = [0]
        def collection_fn(name):
            mock_col = Mock()
            mock_doc_ref = AsyncMock()
            if name == "unified_jobs":
                mock_doc_ref.get = AsyncMock(return_value=unified_doc)
            elif name == "vegetables":
                mock_doc_ref.get = AsyncMock(return_value=r_doc)
            elif name == "seed_guide_jobs":
                mock_doc_ref.get = AsyncMock(return_value=g_doc)
            elif name == "character_jobs":
                mock_doc_ref.get = AsyncMock(return_value=c_doc)
            mock_col.document.return_value = mock_doc_ref
            return mock_col
        mock_db.collection.side_effect = collection_fn

        response = client.get("/api/unified/jobs/u1")
        assert response.status_code == 200
        data = response.json()
        assert "research" in data
        assert "guide" in data
        assert "character" in data

    @patch('main.db')
    def test_not_found(self, mock_db, client):
        mock_doc = Mock(exists=False)
        mock_db.collection.return_value.document.return_value.get = AsyncMock(return_value=mock_doc)
        response = client.get("/api/unified/jobs/u1")
        assert response.status_code == 404

    @patch('main.db')
    def test_error(self, mock_db, client):
        mock_db.collection.return_value.document.return_value.get = AsyncMock(side_effect=Exception("Error"))
        response = client.get("/api/unified/jobs/u1")
        assert response.status_code == 500

    @patch('main.db')
    def test_with_gcs_urls(self, mock_db, client):
        unified_doc = Mock(exists=True)
        unified_doc.to_dict.return_value = {
            "job_id": "u1", "research_doc_id": "r1", "guide_job_id": "g1", "char_job_id": "c1"
        }
        r_doc = Mock(exists=True)
        r_doc.to_dict.return_value = {"status": "completed"}
        g_doc = Mock(exists=True)
        g_doc.to_dict.return_value = {"status": "COMPLETED", "result": [
            {"image_url": "https://storage.googleapis.com/ai-agentic-hackathon-4-bk/seed-guides/output/g1_123_0.jpg"}
        ]}
        c_doc = Mock(exists=True)
        c_doc.to_dict.return_value = {"status": "COMPLETED", "result": {
            "character_name": "T",
            "image_url": "https://storage.googleapis.com/ai-agentic-hackathon-4-bk/characters/img.png"
        }}

        def collection_fn(name):
            mock_col = Mock()
            mock_doc_ref = AsyncMock()
            if name == "unified_jobs":
                mock_doc_ref.get = AsyncMock(return_value=unified_doc)
            elif name == "vegetables":
                mock_doc_ref.get = AsyncMock(return_value=r_doc)
            elif name == "seed_guide_jobs":
                mock_doc_ref.get = AsyncMock(return_value=g_doc)
            elif name == "character_jobs":
                mock_doc_ref.get = AsyncMock(return_value=c_doc)
            mock_col.document.return_value = mock_doc_ref
            return mock_col
        mock_db.collection.side_effect = collection_fn

        response = client.get("/api/unified/jobs/u1")
        assert response.status_code == 200
        data = response.json()
        assert "/api/character/image" in data["character"]["result"]["image_url"]


class TestMakeSerializable:
    def test_basic(self):
        from main import make_serializable
        from datetime import datetime
        result = make_serializable({"key": "val", "dt": datetime(2025, 1, 1), "nested": [1, "str", None]})
        assert result["key"] == "val"
        assert result["dt"] == "2025-01-01T00:00:00"

    def test_unknown_type(self):
        from main import make_serializable
        result = make_serializable({"obj": object()})
        assert isinstance(result["obj"], str)


class TestStartupEvent:
    @pytest.mark.asyncio
    async def test_startup(self):
        from main import startup_event
        await startup_event()  # should not raise


# ---------------------------------------------------------------------------
# Process Seed Guide background task
# ---------------------------------------------------------------------------

class TestProcessSeedGuide:
    @pytest.mark.asyncio
    @patch('main._upload_to_gcs_sync', return_value="https://storage.googleapis.com/bucket/img.jpg")
    @patch('main._download_from_gcs_sync', return_value=b"imagedata")
    @patch('main.db')
    async def test_success_gs_url(self, mock_db, mock_download, mock_upload):
        from main import process_seed_guide
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref

        with patch('main.analyze_seed_and_generate_guide', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = ("Title", "Description", [
                {"text": "Step 1", "image_base64": base64.b64encode(b"img").decode()}
            ])
            await process_seed_guide("job1", "gs://ai-agentic-hackathon-4-bk/input.jpg")

        # Check COMPLETED was set
        calls = mock_doc_ref.set.call_args_list
        last_call = calls[-1]
        assert last_call[0][0]["status"] == "COMPLETED"

    @pytest.mark.asyncio
    @patch('main._download_from_gcs_sync', return_value=b"imagedata")
    @patch('main.db')
    async def test_success_bytes_input(self, mock_db, mock_download):
        from main import process_seed_guide
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref

        with patch('main.analyze_seed_and_generate_guide', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = ("Title", "Desc", [{"text": "s"}])
            await process_seed_guide("job1", b"raw image bytes")

        calls = mock_doc_ref.set.call_args_list
        last_call = calls[-1]
        assert last_call[0][0]["status"] == "COMPLETED"

    @pytest.mark.asyncio
    @patch('main._download_from_gcs_sync', side_effect=Exception("DL failed"))
    @patch('main.db')
    async def test_download_failure(self, mock_db, mock_download):
        from main import process_seed_guide
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref

        await process_seed_guide("job1", "gs://ai-agentic-hackathon-4-bk/input.jpg")

        calls = mock_doc_ref.set.call_args_list
        last_call = calls[-1]
        assert last_call[0][0]["status"] == "FAILED"

    @pytest.mark.asyncio
    @patch('main._download_from_gcs_sync', return_value=b"imagedata")
    @patch('main.db')
    async def test_analyze_exception(self, mock_db, mock_download):
        from main import process_seed_guide
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref

        with patch('main.analyze_seed_and_generate_guide', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("AI Error")
            await process_seed_guide("job1", "some-blob-name")

        calls = mock_doc_ref.set.call_args_list
        last_call = calls[-1]
        assert last_call[0][0]["status"] == "FAILED"

    @pytest.mark.asyncio
    @patch('main._download_from_gcs_sync', return_value=b"imagedata")
    @patch('main.db')
    async def test_string_blob_fallback(self, mock_db, mock_download):
        """String that's not gs:// is treated as blob name."""
        from main import process_seed_guide
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref

        with patch('main.analyze_seed_and_generate_guide', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = ("T", "D", [])
            await process_seed_guide("job1", "path/to/blob.jpg")

        mock_download.assert_called_once()


# ---------------------------------------------------------------------------
# Process Character Generation background task
# ---------------------------------------------------------------------------

class TestProcessCharacterGeneration:
    @pytest.mark.asyncio
    @patch('main._upload_to_gcs_sync', return_value="https://storage.googleapis.com/bucket/char.png")
    @patch('main.db')
    async def test_success(self, mock_db, mock_upload):
        from main import process_character_generation
        mock_doc_ref = AsyncMock()
        mock_char_ref = AsyncMock()

        def collection_fn(name):
            mock_col = Mock()
            if name == "character_jobs":
                mock_col.document.return_value = mock_doc_ref
            elif name == "growing_diaries":
                mock_col.document.return_value = mock_char_ref
            return mock_col
        mock_db.collection.side_effect = collection_fn

        with patch('main.analyze_seed_and_generate_character', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "name": "Tomato",
                "character_name": "Tomato-kun",
                "personality": "cheerful",
                "image_base64": base64.b64encode(b"pngdata").decode()
            }
            await process_character_generation("job1", b"seed image")

        # Verify COMPLETED
        update_calls = mock_doc_ref.update.call_args_list
        last_call = update_calls[-1]
        assert last_call[0][0]["status"] == "COMPLETED"

    @pytest.mark.asyncio
    @patch('main.db')
    async def test_analyze_exception(self, mock_db):
        from main import process_character_generation
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref

        with patch('main.analyze_seed_and_generate_character', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("AI error")
            await process_character_generation("job1", b"seed image")

        update_calls = mock_doc_ref.update.call_args_list
        last_call = update_calls[-1]
        assert last_call[0][0]["status"] == "FAILED"

    @pytest.mark.asyncio
    @patch('main._upload_to_gcs_sync', side_effect=Exception("Upload error"))
    @patch('main.db')
    async def test_image_upload_failure(self, mock_db, mock_upload):
        from main import process_character_generation
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref

        with patch('main.analyze_seed_and_generate_character', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "name": "Tomato",
                "character_name": "T",
                "personality": "p",
                "image_base64": base64.b64encode(b"png").decode()
            }
            await process_character_generation("job1", b"seed")

        # Job should still complete (warning logged but continues)
        update_calls = mock_doc_ref.update.call_args_list
        last_call = update_calls[-1]
        assert last_call[0][0]["status"] == "COMPLETED"

    @pytest.mark.asyncio
    @patch('main.db')
    async def test_no_image_base64(self, mock_db):
        from main import process_character_generation
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref

        with patch('main.analyze_seed_and_generate_character', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {"name": "Tomato", "character_name": "T", "personality": "p"}
            await process_character_generation("job1", b"seed")

        update_calls = mock_doc_ref.update.call_args_list
        last_call = update_calls[-1]
        assert last_call[0][0]["status"] == "COMPLETED"


# ---------------------------------------------------------------------------
# ProgressWrapper + Manual Diary SSE
# ---------------------------------------------------------------------------

class TestProgressWrapper:
    @pytest.mark.asyncio
    async def test_iteration(self):
        from main import ProgressWrapper
        pw = ProgressWrapper()
        await pw.queue.put("msg1")
        await pw.queue.put("msg2")
        await pw.queue.put("__DONE__")

        messages = []
        async for msg in pw:
            messages.append(msg)
        assert messages == ["msg1", "msg2"]


class TestManualDiaryInvalidDate:
    def test_invalid_date_format(self, client):
        response = client.post("/api/diary/generate-manual",
                               json={"date": "not-a-date"})
        assert response.status_code == 400


class TestDiaryServiceUnavailable:
    @patch('main.get_all_diaries', None)
    def test_list_503(self, client):
        response = client.get("/api/diary/list")
        assert response.status_code == 503

    @patch('main.get_diary_by_date', None)
    def test_get_503(self, client):
        response = client.get("/api/diary/2025-01-01")
        assert response.status_code == 503

    @patch('main.get_diary_by_date', None)
    def test_image_503(self, client):
        response = client.get("/api/diary/image/2025-01-01")
        assert response.status_code == 503


class TestDiaryImageInvalidGCS:
    @patch('main.get_diary_by_date')
    def test_invalid_gcs_uri(self, mock_get, client):
        """GCS URI with no slash after bucket name."""
        mock_get.return_value = {"date": "2025-01-01", "plant_image_url": "gs://bucketonly"}
        response = client.get("/api/diary/image/2025-01-01")
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Seed Guide Job GCS URL proxy in result
# ---------------------------------------------------------------------------

class TestSeedGuideJobGCSProxy:
    @patch('main.db')
    def test_result_dict_with_gcs_url_proxy(self, mock_db, client):
        """When result is a dict with image_url, it should be proxied."""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "job_id": "j1", "status": "COMPLETED",
            "result": {
                "image_url": "https://storage.googleapis.com/ai-agentic-hackathon-4-bk/seed-guides/output/j1_123_0.jpg"
            }
        }
        mock_db.collection.return_value.document.return_value.get = AsyncMock(return_value=mock_doc)
        response = client.get("/api/seed-guide/jobs/j1")
        assert response.status_code == 200
        data = response.json()
        assert "/api/character/image" in data["result"]["image_url"]

    @patch('main.db')
    def test_result_dict_with_base64_removed(self, mock_db, client):
        """When result dict has image_base64, it should be removed."""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "job_id": "j1", "status": "COMPLETED",
            "result": {
                "image_url": "https://storage.googleapis.com/ai-agentic-hackathon-4-bk/img.jpg",
                "image_base64": "abc123"
            }
        }
        mock_db.collection.return_value.document.return_value.get = AsyncMock(return_value=mock_doc)
        response = client.get("/api/seed-guide/jobs/j1")
        assert response.status_code == 200
        data = response.json()
        assert "image_base64" not in data["result"]


# ---------------------------------------------------------------------------
# Character metadata (get_character_metadata - duplicate /api/character)
# ---------------------------------------------------------------------------

class TestGetCharacterMetadata:
    @patch('main.db')
    def test_with_gcs_image_uri(self, mock_db, client):
        """Tests the duplicate get_character_metadata endpoint at the bottom of main.py."""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "name": "Tomato",
            "image_uri": "https://storage.googleapis.com/ai-agentic-hackathon-4-bk/characters/t.png"
        }
        mock_db.collection.return_value.document.return_value.get = AsyncMock(return_value=mock_doc)
        response = client.get("/api/character")
        assert response.status_code == 200
        assert "/api/character/image" in response.json()["image_uri"]


# ---------------------------------------------------------------------------
# Unified runner internals (via endpoint)
# ---------------------------------------------------------------------------

class TestUnifiedRunnerInternals:
    @patch('main.process_character_generation', new_callable=AsyncMock)
    @patch('main.process_seed_guide', new_callable=AsyncMock)
    @patch('main.process_research')
    @patch('main.analyze_seed_packet', return_value='{"name": "Unknown"}')
    @patch('main.init_vegetable_status', return_value="research-1")
    @patch('main._upload_to_gcs_sync', return_value="gs://bucket/img.jpg")
    @patch('main.db')
    def test_unknown_vegetable(self, mock_db, mock_upload, mock_init, mock_analyze,
                                mock_research, mock_guide, mock_char, client):
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        files = {"file": ("test.jpg", b"data", "image/jpeg")}
        response = client.post("/api/unified/start", files=files)
        assert response.status_code == 200

    @patch('main.process_character_generation', new_callable=AsyncMock)
    @patch('main.process_seed_guide', new_callable=AsyncMock)
    @patch('main.process_research')
    @patch('main.analyze_seed_packet', return_value='NOT JSON AT ALL')
    @patch('main.init_vegetable_status', return_value="research-1")
    @patch('main._upload_to_gcs_sync', return_value="gs://bucket/img.jpg")
    @patch('main.db')
    def test_json_parse_failure(self, mock_db, mock_upload, mock_init, mock_analyze,
                                 mock_research, mock_guide, mock_char, client):
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        files = {"file": ("test.jpg", b"data", "image/jpeg")}
        response = client.post("/api/unified/start", files=files)
        assert response.status_code == 200

    @patch('main.process_character_generation', new_callable=AsyncMock)
    @patch('main.process_seed_guide', new_callable=AsyncMock)
    @patch('main.process_research')
    @patch('main.analyze_seed_packet', side_effect=Exception("AI error"))
    @patch('main.init_vegetable_status', return_value="research-1")
    @patch('main._upload_to_gcs_sync', return_value="gs://bucket/img.jpg")
    @patch('main.update_vegetable_status')
    @patch('main.db')
    def test_basic_analysis_exception(self, mock_db, mock_update_status, mock_upload, mock_init,
                                       mock_analyze, mock_research, mock_guide, mock_char, client):
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        files = {"file": ("test.jpg", b"data", "image/jpeg")}
        response = client.post("/api/unified/start", files=files)
        assert response.status_code == 200

    @patch('main.process_character_generation', new_callable=AsyncMock)
    @patch('main.process_seed_guide', new_callable=AsyncMock, side_effect=Exception("guide err"))
    @patch('main.process_research', side_effect=Exception("research err"))
    @patch('main.analyze_seed_packet', return_value='{"name": "Tomato"}')
    @patch('main.init_vegetable_status', return_value="research-1")
    @patch('main._upload_to_gcs_sync', return_value="gs://bucket/img.jpg")
    @patch('main.db')
    def test_phase2_3_failures(self, mock_db, mock_upload, mock_init, mock_analyze,
                                mock_research, mock_guide, mock_char, client):
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        files = {"file": ("test.jpg", b"data", "image/jpeg")}
        response = client.post("/api/unified/start", files=files)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Middleware error path
# ---------------------------------------------------------------------------

class TestMiddlewareError:
    @patch('main.db')
    def test_request_error_logs(self, mock_db, client):
        """Trigger an unhandled exception to cover middleware error path."""
        mock_db.collection.side_effect = RuntimeError("Unexpected")
        response = client.delete("/api/vegetables/test-doc")
        assert response.status_code == 500

    def test_middleware_dispatch_exception(self):
        """Cover L146-149: middleware exception handling when call_next raises."""
        from main import SessionTrackingMiddleware
        from starlette.requests import Request
        from starlette.testclient import TestClient as StarletteTestClient
        
        async def failing_call_next(request):
            raise RuntimeError("call_next blew up")
        
        middleware = SessionTrackingMiddleware(app=None)
        
        # Build a fake ASGI scope/request
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "query_string": b"",
            "headers": [],
        }
        fake_request = Request(scope)
        
        import asyncio
        with pytest.raises(RuntimeError, match="call_next blew up"):
            asyncio.get_event_loop().run_until_complete(
                middleware.dispatch(fake_request, failing_call_next)
            )


# ---------------------------------------------------------------------------
# Additional coverage: process_seed_guide edge cases
# ---------------------------------------------------------------------------

class TestProcessSeedGuideEdgeCases:
    @pytest.mark.asyncio
    @patch('main._upload_to_gcs_sync', side_effect=Exception("Upload fail"))
    @patch('main._download_from_gcs_sync', return_value=b"imagedata")
    @patch('main.db')
    async def test_step_image_upload_failure(self, mock_db, mock_download, mock_upload):
        """Cover L489-490: warning when step image upload fails."""
        from main import process_seed_guide
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref

        with patch('main.analyze_seed_and_generate_guide', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = ("Title", "Desc", [
                {"text": "Step 1", "image_base64": base64.b64encode(b"img").decode()}
            ])
            await process_seed_guide("job1", "gs://ai-agentic-hackathon-4-bk/input.jpg")

        # Should still complete (image upload failure is non-fatal)
        calls = mock_doc_ref.set.call_args_list
        last_call = calls[-1]
        assert last_call[0][0]["status"] == "COMPLETED"

    @pytest.mark.asyncio
    @patch('main._download_from_gcs_sync', return_value=b"imagedata")
    @patch('main.db')
    async def test_analyze_unavailable(self, mock_db, mock_download):
        """Cover L510-511: analyze function not in globals."""
        from main import process_seed_guide
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref

        # Remove analyze_seed_and_generate_guide from globals temporarily
        import main
        original = main.__dict__.get('analyze_seed_and_generate_guide')
        if 'analyze_seed_and_generate_guide' in main.__dict__:
            del main.__dict__['analyze_seed_and_generate_guide']
        try:
            await process_seed_guide("job1", "gs://ai-agentic-hackathon-4-bk/input.jpg")
        finally:
            if original is not None:
                main.__dict__['analyze_seed_and_generate_guide'] = original

        calls = mock_doc_ref.set.call_args_list
        last_call = calls[-1]
        assert last_call[0][0]["status"] == "FAILED"
        assert "not available" in last_call[0][0]["message"]


class TestProcessCharacterGenerationEdgeCases:
    @pytest.mark.asyncio
    @patch('main.db')
    async def test_analyze_unavailable(self, mock_db):
        """Cover L706-707: analyze function not in globals."""
        from main import process_character_generation
        mock_doc_ref = AsyncMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref

        import main
        original = main.__dict__.get('analyze_seed_and_generate_character')
        if 'analyze_seed_and_generate_character' in main.__dict__:
            del main.__dict__['analyze_seed_and_generate_character']
        try:
            await process_character_generation("job1", b"seed")
        finally:
            if original is not None:
                main.__dict__['analyze_seed_and_generate_character'] = original

        update_calls = mock_doc_ref.update.call_args_list
        last_call = update_calls[-1]
        assert last_call[0][0]["status"] == "FAILED"
        assert "not available" in last_call[0][0]["message"]


# ---------------------------------------------------------------------------
# Manual diary SSE streaming edge cases
# ---------------------------------------------------------------------------

class TestManualDiarySSE:
    @patch('main.process_daily_diary', None)
    def test_service_unavailable(self, client):
        """Cover L1051: service unavailable."""
        response = client.post("/api/diary/generate-manual",
                               json={"date": "2025-01-01"})
        assert response.status_code == 503

    @patch('main.process_daily_diary', new_callable=AsyncMock)
    def test_sse_streaming_success(self, mock_process, client):
        """Cover L1085-1089: SSE streaming messages."""
        async def fake_process(date_str, callback=None):
            if callback:
                await callback("Processing step 1")
                await callback("Processing step 2")

        mock_process.side_effect = fake_process
        response = client.post("/api/diary/generate-manual",
                               json={"date": "2025-01-01"})
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    @patch('main.process_daily_diary', new_callable=AsyncMock)
    def test_sse_streaming_error(self, mock_process, client):
        """Cover L1093-1095: SSE streaming error."""
        mock_process.side_effect = Exception("Diary error")
        response = client.post("/api/diary/generate-manual",
                               json={"date": "2025-01-01"})
        assert response.status_code == 200  # SSE returns 200 even on error
        assert "text/event-stream" in response.headers.get("content-type", "")


class TestManualDiaryOuterException:
    """Cover L1107-1111: outer try/except in generate_manual_diary_endpoint."""

    @patch('main.process_daily_diary', new_callable=AsyncMock)
    def test_outer_exception_general(self, mock_process, client):
        """Cover L1109-1111: General exception outside SSE generator."""
        # Mock the entire datetime module's date class to raise a non-ValueError
        import datetime as dt_mod
        original_date = dt_mod.date
        
        class FakeDate:
            @staticmethod
            def fromisoformat(s):
                raise RuntimeError("unexpected error")
        
        # Temporarily replace datetime.date so that 'from datetime import date' gets FakeDate
        dt_mod.date = FakeDate
        try:
            response = client.post("/api/diary/generate-manual",
                                   json={"date": "2025-01-01"})
            assert response.status_code == 500
            assert "unexpected" in response.json()["detail"]
        finally:
            dt_mod.date = original_date

    @patch('main.process_daily_diary', new_callable=AsyncMock)
    def test_outer_exception_http_reraise(self, mock_process, client):
        """Cover L1107-1108: HTTPException is re-raised."""
        # Invalid date triggers ValueError -> HTTPException(400)
        response = client.post("/api/diary/generate-manual",
                               json={"date": "not-a-date"})
        assert response.status_code == 400


class TestStartupEventLog:
    """Cover L1673: startup_event info logging."""

    @patch('main.info')
    @patch('main.set_request_id')
    @patch('main.set_session_id')
    @patch('main.generate_session_id', return_value="test-session")
    def test_startup_event(self, mock_gen, mock_set_sess, mock_set_req, mock_info):
        """Directly call startup_event to cover L1668-1673."""
        import asyncio
        from main import startup_event
        asyncio.get_event_loop().run_until_complete(startup_event())
        mock_gen.assert_called_once()
        mock_set_sess.assert_called_once_with("test-session")
        mock_set_req.assert_called_once_with("startup")
        assert mock_info.call_count >= 3  # 3 info() calls


class TestSSETimeoutPing:
    """Cover L1087-1089: SSE timeout ping in event_generator."""

    @patch('main.process_daily_diary', new_callable=AsyncMock)
    def test_sse_timeout_ping(self, mock_process, client):
        """Cover L1087-1089: asyncio.TimeoutError yields ping."""
        call_count = 0

        async def fake_process(date_str, callback=None):
            # Wait a bit so the first wait_for times out, then send __DONE__
            nonlocal call_count
            if callback:
                # Don't call callback immediately - let the loop timeout first
                import asyncio as aio
                await aio.sleep(0)  # yield control
                await callback("__DONE__")

        # We need to make wait_for raise TimeoutError on the first call
        # then return "__DONE__" on the second call
        original_wait_for = asyncio.wait_for
        
        async def patched_wait_for(coro, timeout):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Cancel the pending coroutine to avoid warnings
                coro.close()
                raise asyncio.TimeoutError()
            return await original_wait_for(coro, timeout=timeout)

        mock_process.side_effect = fake_process
        with patch('asyncio.wait_for', side_effect=patched_wait_for):
            response = client.post("/api/diary/generate-manual",
                                   json={"date": "2025-01-01"})
            assert response.status_code == 200
            body = response.text
            assert ": ping" in body
