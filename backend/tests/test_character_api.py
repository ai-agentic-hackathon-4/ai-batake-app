

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add parent directory to path to import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

@pytest.fixture
def mock_firestore():
    with patch("main.db") as mock_db:
        # Configure collection().document() chain to return AsyncMock for async methods
        mock_doc_ref = MagicMock()
        mock_doc_ref.set = AsyncMock()
        mock_doc_ref.get = AsyncMock()
        mock_doc_ref.update = AsyncMock()
        
        mock_col = MagicMock()
        mock_col.document.return_value = mock_doc_ref
        
        mock_db.collection.return_value = mock_col
        yield mock_db

@pytest.fixture
def mock_storage():
    with patch("main.storage") as mock_storage:
        yield mock_storage

def test_create_character_job_success(mock_firestore):
    # Setup
    mock_doc_ref = mock_firestore.collection.return_value.document.return_value
    
    # Create a dummy image file
    files = {'file': ('test.jpg', b'fake_image_content', 'image/jpeg')}
    
    response = client.post("/api/seed-guide/character", files=files)
    
    if response.status_code != 200:
        print(response.json())
        
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    
    # Verify Firestore was called
    mock_firestore.collection.assert_called_with("seed_guide_jobs")
    mock_doc_ref.set.assert_called_once()

def test_get_job_status_completed(mock_firestore):
    job_id = "test-job-id"
    
    # Mock Firestore get return value
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
    
    mock_doc_ref = mock_firestore.collection.return_value.document.return_value
    mock_doc_ref.get.return_value = mock_doc_snapshot
    
    response = client.get(f"/api/seed-guide/jobs/{job_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert "image_url" in data["result"]
    # Check proxy transformation
    assert "/api/character/image?path=" in data["result"]["image_url"]

def test_get_character_metadata(mock_firestore):
    # Mock Firestore get for character
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True
    mock_doc_snapshot.to_dict.return_value = {
        "name": "Test Char",
        "image_uri": "https://storage.googleapis.com/bucket/char.png"
    }
    
    mock_doc_ref = mock_firestore.collection.return_value.document.return_value
    mock_doc_ref.get.return_value = mock_doc_snapshot
    
    response = client.get("/api/character")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Char"
    # Check proxy transformation
    assert "/api/character/image?path=" in data["image_uri"]

def test_get_character_image_proxy(mock_storage):
    # Mock GCS download (Sync)
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    
    mock_storage.Client.return_value = mock_client
    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    
    mock_blob.exists.return_value = True
    mock_blob.download_as_bytes.return_value = b"fake_image_bytes"
    
    path = "characters/test.png"
    # Note: encoded path might be needed if using client, but TestClient handles query params
    response = client.get(f"/api/character/image", params={"path": path})
    
    assert response.status_code == 200
    assert response.content == b"fake_image_bytes"
    mock_bucket.blob.assert_called_with(path)
