"""Tests for database functions in db.py"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestInitVegetableStatus:
    """Tests for init_vegetable_status function"""
    
    @patch('db.db')
    def test_init_vegetable_status_success(self, mock_db):
        """Test successful vegetable status initialization"""
        from db import init_vegetable_status
        
        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc_ref.id = "test-doc-id"
        
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref
        
        result = init_vegetable_status("Tomato")
        
        assert result == "test-doc-id"
        mock_db.collection.assert_called_once_with("vegetables")
        mock_doc_ref.set.assert_called_once()
        
        # Verify the data passed to set()
        call_args = mock_doc_ref.set.call_args[0][0]
        assert call_args["name"] == "Tomato"
        assert call_args["status"] == "processing"
    
    @patch('db.db', None)
    def test_init_vegetable_status_no_db(self):
        """Test initialization when db is None (offline mode)"""
        from db import init_vegetable_status
        
        result = init_vegetable_status("Tomato")
        
        assert result == "mock-id-processing"
    
    @patch('db.db')
    def test_init_vegetable_status_error(self, mock_db):
        """Test error handling in initialization"""
        from db import init_vegetable_status
        
        mock_db.collection.side_effect = Exception("Database error")
        
        result = init_vegetable_status("Tomato")
        
        assert result == "error-id"


class TestUpdateVegetableStatus:
    """Tests for update_vegetable_status function"""
    
    @patch('db.db')
    def test_update_vegetable_status_success(self, mock_db):
        """Test successful status update"""
        from db import update_vegetable_status
        
        mock_collection = Mock()
        mock_doc_ref = Mock()
        
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref
        
        update_vegetable_status("test-id", "completed", {"data": "test"})
        
        mock_db.collection.assert_called_once_with("vegetables")
        mock_collection.document.assert_called_once_with("test-id")
        mock_doc_ref.update.assert_called_once()
        
        # Verify update data
        call_args = mock_doc_ref.update.call_args[0][0]
        assert call_args["status"] == "completed"
        assert call_args["instructions"] == {"data": "test"}
    
    @patch('db.db')
    def test_update_vegetable_status_without_data(self, mock_db):
        """Test status update without additional data"""
        from db import update_vegetable_status
        
        mock_collection = Mock()
        mock_doc_ref = Mock()
        
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref
        
        update_vegetable_status("test-id", "failed")
        
        call_args = mock_doc_ref.update.call_args[0][0]
        assert call_args["status"] == "failed"
        assert "instructions" not in call_args
    
    @patch('db.db', None)
    def test_update_vegetable_status_no_db(self):
        """Test update when db is None (offline mode)"""
        from db import update_vegetable_status
        
        # Should not raise an exception
        update_vegetable_status("test-id", "completed")


class TestGetAllVegetables:
    """Tests for get_all_vegetables function"""
    
    @patch('db.db')
    def test_get_all_vegetables_success(self, mock_db):
        """Test successful retrieval of all vegetables"""
        from db import get_all_vegetables
        
        mock_doc1 = Mock()
        mock_doc1.to_dict.return_value = {"name": "Tomato", "status": "completed"}
        mock_doc2 = Mock()
        mock_doc2.to_dict.return_value = {"name": "Cucumber", "status": "processing"}
        
        mock_collection = Mock()
        mock_collection.stream.return_value = [mock_doc1, mock_doc2]
        
        mock_db.collection.return_value = mock_collection
        
        result = get_all_vegetables()
        
        assert len(result) == 2
        assert result[0]["name"] == "Tomato"
        assert result[1]["name"] == "Cucumber"
    
    @patch('db.db', None)
    def test_get_all_vegetables_no_db(self):
        """Test retrieval when db is None (offline mode)"""
        from db import get_all_vegetables
        
        result = get_all_vegetables()
        
        assert result == []


class TestGetLatestVegetable:
    """Tests for get_latest_vegetable function"""
    
    @patch('db.db')
    def test_get_latest_vegetable_success(self, mock_db):
        """Test successful retrieval of latest vegetable"""
        from db import get_latest_vegetable
        
        mock_doc = Mock()
        mock_doc.to_dict.return_value = {"name": "Tomato", "status": "completed"}
        
        mock_query = Mock()
        mock_query.limit.return_value.stream.return_value = [mock_doc]
        
        mock_collection = Mock()
        mock_collection.order_by.return_value = mock_query
        
        mock_db.collection.return_value = mock_collection
        
        result = get_latest_vegetable()
        
        assert result["name"] == "Tomato"
    
    @patch('db.db')
    def test_get_latest_vegetable_empty(self, mock_db):
        """Test retrieval when no vegetables exist"""
        from db import get_latest_vegetable
        
        mock_query = Mock()
        mock_query.limit.return_value.stream.return_value = []
        
        mock_collection = Mock()
        mock_collection.order_by.return_value = mock_query
        
        mock_db.collection.return_value = mock_collection
        
        result = get_latest_vegetable()
        
        assert result is None
    
    @patch('db.db', None)
    def test_get_latest_vegetable_no_db(self):
        """Test retrieval when db is None (offline mode)"""
        from db import get_latest_vegetable
        
        result = get_latest_vegetable()
        
        assert result is None
