
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

# Adjust path to import backend modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import update_edge_agent_config, get_edge_agent_config
from diary_service import get_current_vegetable_async

# --- DB Tests ---

@patch("db.db")
def test_update_edge_agent_config(mock_db):
    """Test that vegetable_name is saved to the edge_agent config."""
    # Setup mock
    mock_doc_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_doc_ref
    
    # Execute
    research_data = {
        "name": "Test Soybeans",
        "summary_prompt": "Support growing soybeans..."
    }
    update_edge_agent_config(research_data)
    
    # Verify
    mock_db.collection.assert_called_with("configurations")
    mock_db.collection.return_value.document.assert_called_with("edge_agent")
    
    # Check set call arguments
    args, kwargs = mock_doc_ref.set.call_args
    assert kwargs.get("merge") is True
    saved_data = args[0]
    assert saved_data["vegetable_name"] == "Test Soybeans"
    assert saved_data["instruction"] == "Support growing soybeans..."
    assert "updated_at" in saved_data

@patch("db.db")
def test_get_edge_agent_config(mock_db):
    """Test retrieving the edge_agent config."""
    # Setup mock
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"vegetable_name": "Radish", "instruction": "Grow it."}
    
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
    
    # Execute
    config = get_edge_agent_config()
    
    # Verify
    assert config["vegetable_name"] == "Radish"
    assert config["instruction"] == "Grow it."


# --- Diary Service Tests ---

@pytest.mark.asyncio
async def test_get_current_vegetable_prioritizes_config():
    """Test that config vegetable name is used over latest vegetable if present."""
    
    with patch("diary_service.get_edge_agent_config") as mock_get_config, \
         patch("diary_service.get_latest_vegetable") as mock_get_latest:
        
        # Setup mocks
        mock_get_config.return_value = {"vegetable_name": "Configured Veggie"}
        mock_get_latest.return_value = {"name": "Latest Created Veggie"}
        
        # Execute
        result = await get_current_vegetable_async()
        
        # Verify
        assert result["name"] == "Configured Veggie"
        # Should not have called get_latest_vegetable if config was sufficient? 
        # Actually logic is: if config and config.get("vegetable_name")... return mimic dict.
        # So get_latest_vegetable should NOT be called? 
        # Wait, the current implementation uses asyncio.to_thread for get_latest_vegetable in the fallback.
        # But if the first part returns, the second part is unreachable.
        # However, asyncio.to_thread is awaited.
        # Re-checking diary_service.py logic:
        # config = await asyncio.to_thread(get_edge_agent_config)
        # if config ... return ...
        # return await asyncio.to_thread(get_latest_vegetable)
        
        # So mock_get_latest should NOT be called.
        mock_get_latest.assert_not_called()


@pytest.mark.asyncio
async def test_get_current_vegetable_fallback():
    """Test fallback to get_latest_vegetable if config has no name."""
    
    with patch("diary_service.get_edge_agent_config") as mock_get_config, \
         patch("diary_service.get_latest_vegetable") as mock_get_latest:
        
        # Setup mocks
        mock_get_config.return_value = {} # Empty config
        mock_get_latest.return_value = {"name": "Latest Veggie"}
        
        # Execute
        result = await get_current_vegetable_async()
        
        # Verify
        assert result["name"] == "Latest Veggie"
        mock_get_latest.assert_called_once()
