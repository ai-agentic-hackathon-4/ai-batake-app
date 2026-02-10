"""Tests for database functions in db.py"""
from unittest.mock import Mock, patch
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
        
        # Mock doc_ref.get() which is called to merge existing result
        mock_existing_doc = Mock()
        mock_existing_doc.exists = True
        mock_existing_doc.to_dict.return_value = {"result": {"existing_key": "value"}}
        mock_doc_ref.get.return_value = mock_existing_doc
        
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
        # Verify result is merged with existing data
        assert call_args["result"]["existing_key"] == "value"
        assert call_args["result"]["data"] == "test"
    
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
        mock_doc1.id = "doc1"
        mock_doc2 = Mock()
        mock_doc2.to_dict.return_value = {"name": "Cucumber", "status": "processing"}
        mock_doc2.id = "doc2"
        
        mock_query = Mock()
        mock_query.stream.return_value = [mock_doc1, mock_doc2]
        
        mock_collection = Mock()
        mock_collection.order_by.return_value = mock_query
        
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


class TestGetAgentExecutionLogs:
    """Tests for get_agent_execution_logs function"""
    
    @patch('db.db')
    def test_get_agent_execution_logs_success(self, mock_db):
        """Test successful retrieval of agent logs"""
        from db import get_agent_execution_logs, firestore
        
        # Mock documents
        mock_doc1 = Mock()
        mock_doc1.to_dict.return_value = {"action": "Watering", "timestamp": "2024-01-01T12:00:00"}
        mock_doc1.id = "log1"
        
        mock_doc2 = Mock()
        mock_doc2.to_dict.return_value = {"action": "Monitoring", "timestamp": "2024-01-01T13:00:00"}
        mock_doc2.id = "log2"
        
        # Mock query chain
        mock_query = Mock()
        mock_query.limit.return_value.stream.return_value = [mock_doc1, mock_doc2]
        
        mock_collection = Mock()
        mock_collection.order_by.return_value = mock_query
        
        mock_db.collection.return_value = mock_collection
        
        result = get_agent_execution_logs(limit=10)
        
        # Verify collection and order
        mock_db.collection.assert_called_once_with("agent_execution_logs")
        mock_collection.order_by.assert_called_once_with("timestamp", direction=firestore.Query.DESCENDING)
        mock_query.limit.assert_called_once_with(10)
        
        assert len(result) == 2
        assert result[0]["id"] == "log1"
        assert result[1]["id"] == "log2"
        
    @patch('db.db')
    def test_get_agent_execution_logs_error(self, mock_db):
        """Test error handling when fetching logs"""
        from db import get_agent_execution_logs
        
        mock_db.collection.side_effect = Exception("Firestore error")
        
        result = get_agent_execution_logs()
        
        assert result == []
        
    @patch('db.db', None)
    def test_get_agent_execution_logs_no_db(self):
        """Test retrieval when db is None"""
        from db import get_agent_execution_logs
        
        result = get_agent_execution_logs()
        
        assert result == []
