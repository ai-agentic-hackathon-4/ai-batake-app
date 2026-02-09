"""
Tests for seed guide persistence functionality.
Tests the save, list, and get detail endpoints for seed guides.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_save_seed_guide():
    """Test saving a seed guide to the database."""
    mock_steps = [
        {
            "title": "Test Step 1",
            "description": "Plant the seed deep.",
            "image_base64": "mock_base64_string",
            "image_prompt": "A seed in dirt"
        },
        {
            "title": "Test Step 2",
            "description": "Water it well.",
            "image_base64": "mock_base64_string_2",
            "image_prompt": "Watering can"
        }
    ]
    
    payload = {
        "title": "Test Guide",
        "description": "A test guide for verification.",
        "steps": mock_steps,
        "original_image": "mock_original_image_b64"
    }
    
    response = client.post("/api/seed-guide/save", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert data["id"] is not None
    
    return data["id"]


def test_list_saved_guides():
    """Test listing all saved seed guides."""
    # First save a guide
    doc_id = test_save_seed_guide()
    
    # Then list all guides
    response = client.get("/api/seed-guide/saved")
    assert response.status_code == 200
    
    guides = response.json()
    assert isinstance(guides, list)
    
    # Verify our saved guide is in the list
    found = any(g['id'] == doc_id for g in guides)
    assert found, "Saved guide should be in the list"


def test_get_seed_guide_detail():
    """Test getting a specific seed guide by ID."""
    # First save a guide
    doc_id = test_save_seed_guide()
    
    # Then get its details
    response = client.get(f"/api/seed-guide/saved/{doc_id}")
    assert response.status_code == 200
    
    detail = response.json()
    assert detail.get('title') == "Test Guide"
    assert len(detail.get('steps', [])) == 2
    assert detail.get('steps')[0]['title'] == "Test Step 1"


def test_get_nonexistent_guide():
    """Test getting a guide that doesn't exist."""
    response = client.get("/api/seed-guide/saved/nonexistent-id")
    assert response.status_code == 404
