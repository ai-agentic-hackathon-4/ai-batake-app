"""
Tests for seed guide persistence functionality.
Tests the save, list, and get detail endpoints for seed guides.
All Firestore operations are mocked to prevent real connections.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Firestore before importing main
with patch('google.cloud.firestore.AsyncClient'):
    from main import app

client = TestClient(app)


class TestSaveSeedGuide:
    """Tests for POST /api/seed-guide/save endpoint"""

    @patch('main.save_seed_guide')
    def test_save_seed_guide(self, mock_save):
        """Test saving a seed guide to the database."""
        mock_save.return_value = "test-doc-id"

        payload = {
            "title": "Test Guide",
            "description": "A test guide for verification.",
            "steps": [
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
        }

        response = client.post("/api/seed-guide/save", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "id" in data
        assert data["id"] == "test-doc-id"


class TestListSavedGuides:
    """Tests for GET /api/seed-guide/saved endpoint"""

    @patch('main.get_all_seed_guides')
    def test_list_saved_guides(self, mock_get_all):
        """Test listing all saved seed guides."""
        mock_get_all.return_value = [
            {"id": "doc1", "title": "Guide 1"},
            {"id": "doc2", "title": "Guide 2"},
        ]

        response = client.get("/api/seed-guide/saved")
        assert response.status_code == 200

        guides = response.json()
        assert isinstance(guides, list)
        assert len(guides) == 2
        assert guides[0]["id"] == "doc1"


class TestGetSeedGuideDetail:
    """Tests for GET /api/seed-guide/saved/{doc_id} endpoint"""

    @patch('main.get_seed_guide')
    def test_get_seed_guide_detail(self, mock_get):
        """Test getting a specific seed guide by ID."""
        mock_get.return_value = {
            "title": "Test Guide",
            "steps": [
                {"title": "Test Step 1", "description": "Plant the seed deep."},
                {"title": "Test Step 2", "description": "Water it well."},
            ]
        }

        response = client.get("/api/seed-guide/saved/test-doc-id")
        assert response.status_code == 200

        detail = response.json()
        assert detail.get("title") == "Test Guide"
        assert len(detail.get("steps", [])) == 2
        assert detail.get("steps")[0]["title"] == "Test Step 1"

    @patch('main.get_seed_guide')
    def test_get_nonexistent_guide(self, mock_get):
        """Test getting a guide that doesn't exist."""
        mock_get.return_value = None

        response = client.get("/api/seed-guide/saved/nonexistent-id")
        assert response.status_code == 404
