"""Tests for select vegetable instruction feature"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Firestore before importing main/db
with patch('google.cloud.firestore.AsyncClient'):
    from main import app
    import db

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

class TestSelectInstructionDB:
    """Tests for db.select_vegetable_instruction"""

    @patch('db.db')
    @patch('db.update_edge_agent_config')
    def test_select_success_with_instructions(self, mock_update_config, mock_db):
        """Test successful selection with existing instructions"""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "name": "Tomato", 
            "instructions": {
                "summary_prompt": "Grow checks", 
                "volumetric_water_content": "40%"
            }
        }
        
        mock_collection = Mock()
        mock_collection.document.return_value.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        
        # Call function
        result = db.select_vegetable_instruction("test-id")
        
        assert result is True
        mock_update_config.assert_called_once()
        args = mock_update_config.call_args[0][0]
        assert args["summary_prompt"] == "Grow checks"
        assert args["name"] == "Tomato" # Should be preserved/added

    @patch('db.db')
    def test_select_not_found(self, mock_db):
        """Test selection when document does not exist"""
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_collection = Mock()
        mock_collection.document.return_value.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        
        result = db.select_vegetable_instruction("test-id")
        
        assert result is False

    @patch('db.db')
    def test_select_no_instructions(self, mock_db):
        """Test selection when document has no instructions field"""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"name": "Tomato"} # No instructions
        
        mock_collection = Mock()
        mock_collection.document.return_value.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        
        result = db.select_vegetable_instruction("test-id")
        
        assert result is False

class TestSelectInstructionEndpoint:
    """Tests for POST /api/vegetables/{id}/select endpoint"""

    @patch('backend.db.select_vegetable_instruction')
    def test_endpoint_success(self, mock_select, client):
        """Test endpoint returns 200 on success"""
        mock_select.return_value = True
        
        # Attempt to patch where main.py imports it. 
        # Since main.py does 'from backend.db import ...' or 'from db import ...'
        # We might need to patch 'main.select_vegetable_instruction' if it was imported at top level,
        # but the endpoint does a local import.
        # However, sys.modules cache might affect it. 
        # Using patch on 'db.select_vegetable_instruction' (since we imported db above) might work if main uses the same module object.
        # Let's try patching the function where it is DEFINED.
        
        with patch('db.select_vegetable_instruction', return_value=True):
             response = client.post("/api/vegetables/test-id/select")
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    @patch('db.select_vegetable_instruction')
    def test_endpoint_failure(self, mock_select, client):
        """Test endpoint returns 404 on failure"""
        mock_select.return_value = False
        
        response = client.post("/api/vegetables/test-id/select")
        
        assert response.status_code == 404
