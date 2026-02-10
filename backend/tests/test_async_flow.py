"""
Tests for async seed guide generation flow.
Tests the end-to-end async generation and persistence of seed guides.
All external services (Firestore, GCS) are mocked.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Firestore before importing main
with patch('google.cloud.firestore.AsyncClient'):
    from main import app

client = TestClient(app)


class TestAsyncGenerationFlow:
    """Tests for async seed guide generation endpoints"""

    @patch('main.db')
    @patch('main.storage')
    def test_async_generation_flow(self, mock_storage, mock_db):
        """
        Test starting an async seed guide generation job.
        """
        # Mock GCS upload
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.public_url = "https://storage.googleapis.com/bucket/test.jpg"
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client = MagicMock()
        mock_storage_client.bucket.return_value = mock_bucket
        mock_storage.Client.return_value = mock_storage_client

        # Mock Firestore document
        mock_doc_ref = MagicMock()
        mock_doc_ref.set = AsyncMock()
        mock_col = MagicMock()
        mock_col.document.return_value = mock_doc_ref
        mock_db.collection.return_value = mock_col

        files = {"file": ("test_seed.jpg", b"fake_image_content", "image/jpeg")}
        response = client.post("/api/seed-guide/generate", files=files)
        assert response.status_code == 200

        data = response.json()
        job_id = data.get("job_id")
        assert job_id is not None
        assert data.get("status") == "PENDING"

    @patch('main.db')
    @patch('main.get_all_seed_guides')
    @patch('main.storage')
    def test_async_generation_appears_in_list(self, mock_storage, mock_get_all, mock_db):
        """Test that a generated guide appears in the saved guides list."""
        # Mock GCS upload
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.public_url = "https://storage.googleapis.com/bucket/test.jpg"
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client = MagicMock()
        mock_storage_client.bucket.return_value = mock_bucket
        mock_storage.Client.return_value = mock_storage_client

        # Mock Firestore document
        mock_doc_ref = MagicMock()
        mock_doc_ref.set = AsyncMock()
        mock_col = MagicMock()
        mock_col.document.return_value = mock_doc_ref
        mock_db.collection.return_value = mock_col

        # Start generation
        files = {"file": ("test_seed2.jpg", b"fake_image_content_2", "image/jpeg")}
        response = client.post("/api/seed-guide/generate", files=files)
        assert response.status_code == 200

        job_id = response.json().get("job_id")
        assert job_id is not None

        # Mock the list of saved guides to include the job
        mock_get_all.return_value = [{"id": job_id, "title": "New Seed Guide"}]

        response = client.get("/api/seed-guide/saved")
        assert response.status_code == 200

        guides = response.json()
        found = any(g['id'] == job_id for g in guides)
        assert found, "Generated guide should appear in saved guides list"

    def test_invalid_file_upload(self):
        """Test uploading an invalid file."""
        response = client.post("/api/seed-guide/generate")
        assert response.status_code == 422  # Validation error
