

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add parent directory to path to import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Firestore before importing main
with patch('google.cloud.firestore.AsyncClient'):
    from main import app

client = TestClient(app)


class TestCreateCharacterJob:
    """Tests for POST /api/seed-guide/character endpoint"""

    @patch('main.process_character_generation', new_callable=AsyncMock)
    @patch('main.db')
    def test_create_character_job_success(self, mock_db, mock_process):
        """Test successful character job creation"""
        mock_doc_ref = MagicMock()
        mock_doc_ref.set = AsyncMock()

        mock_col = MagicMock()
        mock_col.document.return_value = mock_doc_ref

        mock_db.collection.return_value = mock_col

        files = {'file': ('test.jpg', b'fake_image_content', 'image/jpeg')}

        response = client.post("/api/seed-guide/character", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

        mock_db.collection.assert_called_with("character_jobs")
        mock_doc_ref.set.assert_called_once()


class TestGetJobStatus:
    """Tests for GET /api/seed-guide/jobs/{job_id} endpoint"""

    @patch('main.db')
    def test_get_job_status_completed(self, mock_db):
        """Test getting a completed job status"""
        job_id = "test-job-id"

        mock_doc_snapshot = MagicMock()
        mock_doc_snapshot.exists = True
        mock_doc_snapshot.to_dict.return_value = {
            "job_id": job_id,
            "status": "COMPLETED",
            "result": {
                "character_name": "Test Char",
                "image_url": "https://storage.googleapis.com/ai-agentic-hackathon-4-bk/characters/test.png"
            }
        }

        mock_doc_ref = MagicMock()
        mock_doc_ref.get = AsyncMock(return_value=mock_doc_snapshot)

        mock_col = MagicMock()
        mock_col.document.return_value = mock_doc_ref

        mock_db.collection.return_value = mock_col

        response = client.get(f"/api/seed-guide/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"


class TestGetCharacterMetadata:
    """Tests for GET /api/character endpoint"""

    @patch('main.db')
    def test_get_character_metadata(self, mock_db):
        """Test getting character metadata"""
        mock_doc_snapshot = MagicMock()
        mock_doc_snapshot.exists = True
        mock_doc_snapshot.to_dict.return_value = {
            "name": "Test Char",
            "image_uri": "https://storage.googleapis.com/ai-agentic-hackathon-4-bk/char.png"
        }

        mock_doc_ref = MagicMock()
        mock_doc_ref.get = AsyncMock(return_value=mock_doc_snapshot)

        mock_col = MagicMock()
        mock_col.document.return_value = mock_doc_ref

        mock_db.collection.return_value = mock_col

        response = client.get("/api/character")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Char"


class TestGetCharacterImageProxy:
    """Tests for GET /api/character/image endpoint"""

    @patch('google.cloud.storage.Client')
    def test_get_character_image_proxy(self, mock_storage_client_cls):
        """Test proxying character image from GCS"""
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()

        mock_storage_client_cls.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"fake_image_bytes"

        path = "characters/test.png"
        response = client.get("/api/character/image", params={"path": path})

        assert response.status_code == 200
        assert response.content == b"fake_image_bytes"
        mock_bucket.blob.assert_called_with(path)
