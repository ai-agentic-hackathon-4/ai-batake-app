"""
Tests for async seed guide generation flow.
Tests the end-to-end async generation and persistence of seed guides.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_async_generation_flow():
    """
    End-to-end test for the async seed guide generation and persistence flow.
    """
    # 1. Start generation (mocking file upload)
    files = {"file": ("test_seed.jpg", b"fake_image_content", "image/jpeg")}
    response = client.post("/api/seed-guide/generate", files=files)
    assert response.status_code == 200

    data = response.json()
    job_id = data.get("job_id")
    assert job_id is not None
    assert data.get("status") == "PENDING"

    # 2. Verify it exists in "Saved Guides" immediately
    response = client.get(f"/api/seed-guide/saved/{job_id}")
    assert response.status_code == 200

    guide = response.json()
    # Ensure we got back a guide with a valid status
    expected_statuses = ["PENDING", "PROCESSING", "COMPLETED", "FAILED"]
    assert guide.get("status") in expected_statuses
    assert guide.get("id") == job_id


def test_async_generation_appears_in_list():
    """Test that a generated guide appears in the saved guides list."""
    # 1. Start generation
    files = {"file": ("test_seed2.jpg", b"fake_image_content_2", "image/jpeg")}
    response = client.post("/api/seed-guide/generate", files=files)
    assert response.status_code == 200
    
    job_id = response.json().get("job_id")
    assert job_id is not None
    
    # 2. Verify it appears in the list
    response = client.get("/api/seed-guide/saved")
    assert response.status_code == 200
    
    guides = response.json()
    found = any(g['id'] == job_id for g in guides)
    assert found, "Generated guide should appear in saved guides list"


def test_invalid_file_upload():
    """Test uploading an invalid file."""
    # Test with missing file parameter
    response = client.post("/api/seed-guide/generate")
    assert response.status_code == 422  # Validation error
