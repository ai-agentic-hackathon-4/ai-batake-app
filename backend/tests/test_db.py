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


class TestFirestoreInitialization:
    """Tests for module-level Firestore initialization (lines 22-28)"""

    def test_init_generic_exception(self):
        """Test Firestore init falls back to None on generic Exception"""
        import importlib
        import db
        with patch.object(db.firestore, 'Client', side_effect=RuntimeError("some error")):
            importlib.reload(db)
            assert db.db is None
        # Reload to restore normal state
        importlib.reload(db)

    def test_init_default_credentials_error(self):
        """Test Firestore init handles DefaultCredentialsError"""
        import importlib
        import db
        import google.auth.exceptions
        with patch.object(db.firestore, 'Client', side_effect=google.auth.exceptions.DefaultCredentialsError("no creds")):
            importlib.reload(db)
            assert db.db is None
        importlib.reload(db)


class TestUpdateVegetableStatusError:
    """Tests for update_vegetable_status error path (lines 73-74)"""

    @patch('db.db')
    def test_update_vegetable_status_exception(self, mock_db):
        """Test error handling when update raises an exception"""
        from db import update_vegetable_status

        mock_db.collection.side_effect = Exception("Firestore error")

        # Should not raise, error is logged
        update_vegetable_status("test-id", "completed", {"data": "test"})


class TestGetAllVegetablesError:
    """Tests for get_all_vegetables error path (line 92-94)"""

    @patch('db.db')
    def test_get_all_vegetables_error(self, mock_db):
        """Test error handling when fetching all vegetables fails"""
        from db import get_all_vegetables

        mock_db.collection.side_effect = Exception("Firestore error")

        result = get_all_vegetables()
        assert result == []

    @patch('db.db')
    def test_get_all_vegetables_with_datetime(self, mock_db):
        """Test that datetime created_at is converted to isoformat"""
        from db import get_all_vegetables
        from datetime import datetime

        mock_doc = Mock()
        mock_doc.id = "doc1"
        dt = datetime(2024, 1, 1, 12, 0, 0)
        mock_doc.to_dict.return_value = {"name": "Tomato", "created_at": dt}

        mock_query = Mock()
        mock_query.stream.return_value = [mock_doc]
        mock_collection = Mock()
        mock_collection.order_by.return_value = mock_query
        mock_db.collection.return_value = mock_collection

        result = get_all_vegetables()
        assert len(result) == 1
        assert result[0]["created_at"] == dt.isoformat()


class TestSaveGrowingInstructions:
    """Tests for save_growing_instructions function"""

    @patch('db.db')
    def test_save_growing_instructions_success(self, mock_db):
        """Test successful save of growing instructions"""
        from db import save_growing_instructions

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc_ref.id = "new-doc-id"
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        result = save_growing_instructions("Tomato", {"temp": "25C"})

        assert result == "new-doc-id"
        mock_db.collection.assert_called_once_with("vegetables")
        mock_doc_ref.set.assert_called_once()
        call_args = mock_doc_ref.set.call_args[0][0]
        assert call_args["name"] == "Tomato"
        assert call_args["instructions"] == {"temp": "25C"}

    @patch('db.db', None)
    def test_save_growing_instructions_no_db(self):
        """Test save when db is None"""
        from db import save_growing_instructions

        result = save_growing_instructions("Tomato", {"temp": "25C"})
        assert result == "mock-id-firestore-unavailable"

    @patch('db.db')
    def test_save_growing_instructions_error(self, mock_db):
        """Test error handling when save fails"""
        from db import save_growing_instructions
        import pytest

        mock_db.collection.side_effect = Exception("Firestore error")

        with pytest.raises(Exception, match="Firestore error"):
            save_growing_instructions("Tomato", {"temp": "25C"})


class TestUpdateEdgeAgentConfig:
    """Tests for update_edge_agent_config function"""

    @patch('db.db')
    def test_update_edge_agent_config_with_summary_prompt(self, mock_db):
        """Test update with summary_prompt present"""
        from db import update_edge_agent_config

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        research_data = {
            "name": "Tomato",
            "summary_prompt": "Grow tomatoes at 25C"
        }
        update_edge_agent_config(research_data)

        mock_db.collection.assert_called_once_with("configurations")
        mock_collection.document.assert_called_once_with("edge_agent")
        call_args = mock_doc_ref.set.call_args
        assert call_args[0][0]["instruction"] == "Grow tomatoes at 25C"
        assert call_args[0][0]["vegetable_name"] == "Tomato"
        assert call_args[1] == {"merge": True}

    @patch('db.db')
    def test_update_edge_agent_config_with_complete_support_prompt(self, mock_db):
        """Test update uses complete_support_prompt when summary_prompt is missing"""
        from db import update_edge_agent_config

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        research_data = {
            "name": "Cucumber",
            "complete_support_prompt": "Support cucumber growing"
        }
        update_edge_agent_config(research_data)

        call_args = mock_doc_ref.set.call_args[0][0]
        assert call_args["instruction"] == "Support cucumber growing"

    @patch('db.db')
    def test_update_edge_agent_config_fallback_construction(self, mock_db):
        """Test fallback prompt construction when both prompts are missing"""
        from db import update_edge_agent_config

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        research_data = {
            "name": "Pepper",
            "optimal_temp_range": "20-30C",
            "volumetric_water_content": "40%"
        }
        update_edge_agent_config(research_data)

        call_args = mock_doc_ref.set.call_args[0][0]
        assert "Pepper" in call_args["instruction"]
        assert "20-30C" in call_args["instruction"]
        assert "40%" in call_args["instruction"]

    @patch('db.db')
    def test_update_edge_agent_config_fallback_no_fields(self, mock_db):
        """Test fallback with empty research_data (no name, temp, water)"""
        from db import update_edge_agent_config

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        update_edge_agent_config({})

        call_args = mock_doc_ref.set.call_args[0][0]
        assert "Unknown Plant" in call_args["instruction"]

    @patch('db.db')
    def test_update_edge_agent_config_error(self, mock_db):
        """Test error handling when update fails"""
        from db import update_edge_agent_config

        mock_db.collection.side_effect = Exception("Firestore error")

        # Should not raise
        update_edge_agent_config({"name": "Tomato", "summary_prompt": "test"})

    @patch('db.db', None)
    def test_update_edge_agent_config_no_db(self):
        """Test update when db is None"""
        from db import update_edge_agent_config

        # Should return immediately without error
        update_edge_agent_config({"name": "Tomato"})


class TestSelectVegetableInstruction:
    """Tests for select_vegetable_instruction function"""

    @patch('db.update_edge_agent_config')
    @patch('db.db')
    def test_select_vegetable_instruction_success(self, mock_db, mock_update_config):
        """Test successful selection of vegetable instruction"""
        from db import select_vegetable_instruction

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "name": "Tomato",
            "instructions": {"summary_prompt": "Grow tomatoes", "name": "Tomato"}
        }
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        result = select_vegetable_instruction("doc-1")

        assert result is True
        mock_update_config.assert_called_once()

    @patch('db.db')
    def test_select_vegetable_instruction_not_found(self, mock_db):
        """Test selection when document doesn't exist"""
        from db import select_vegetable_instruction

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = False
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        result = select_vegetable_instruction("non-existent")

        assert result is False

    @patch('db.db')
    def test_select_vegetable_instruction_no_instructions(self, mock_db):
        """Test selection when doc has no instructions"""
        from db import select_vegetable_instruction

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"name": "Tomato", "instructions": None}
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        result = select_vegetable_instruction("doc-1")

        assert result is False

    @patch('db.update_edge_agent_config')
    @patch('db.db')
    def test_select_vegetable_instruction_no_name_in_instructions(self, mock_db, mock_update_config):
        """Test that name is added to instructions if not present"""
        from db import select_vegetable_instruction

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "name": "Carrot",
            "instructions": {"summary_prompt": "Grow carrots"}
        }
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        result = select_vegetable_instruction("doc-2")

        assert result is True
        called_instructions = mock_update_config.call_args[0][0]
        assert called_instructions["name"] == "Carrot"

    @patch('db.db')
    def test_select_vegetable_instruction_error(self, mock_db):
        """Test error handling during selection"""
        from db import select_vegetable_instruction

        mock_db.collection.side_effect = Exception("Firestore error")

        result = select_vegetable_instruction("doc-1")

        assert result is False

    @patch('db.db', None)
    def test_select_vegetable_instruction_no_db(self):
        """Test selection when db is None"""
        from db import select_vegetable_instruction

        result = select_vegetable_instruction("doc-1")

        assert result is False


class TestGetRecentSensorLogs:
    """Tests for get_recent_sensor_logs function"""

    @patch('db.db')
    def test_get_recent_sensor_logs_success(self, mock_db):
        """Test successful retrieval of sensor logs"""
        from db import get_recent_sensor_logs, firestore

        mock_doc1 = Mock()
        mock_doc1.to_dict.return_value = {"temperature": 25.0, "humidity": 60}
        mock_doc1.id = "log1"
        mock_doc2 = Mock()
        mock_doc2.to_dict.return_value = {"temperature": 22.0, "humidity": 55}
        mock_doc2.id = "log2"

        mock_query = Mock()
        mock_query.limit.return_value.stream.return_value = [mock_doc1, mock_doc2]
        mock_collection = Mock()
        mock_collection.order_by.return_value = mock_query
        mock_db.collection.return_value = mock_collection

        result = get_recent_sensor_logs(limit=5)

        mock_db.collection.assert_called_once_with("sensor_logs")
        mock_collection.order_by.assert_called_once_with("unix_timestamp", direction=firestore.Query.DESCENDING)
        mock_query.limit.assert_called_once_with(5)
        assert len(result) == 2
        assert result[0]["id"] == "log1"

    @patch('db.db')
    def test_get_recent_sensor_logs_error(self, mock_db):
        """Test error handling when fetch fails"""
        from db import get_recent_sensor_logs

        mock_db.collection.side_effect = Exception("Firestore error")

        result = get_recent_sensor_logs()
        assert result == []

    @patch('db.db', None)
    def test_get_recent_sensor_logs_no_db(self):
        """Test retrieval when db is None"""
        from db import get_recent_sensor_logs

        result = get_recent_sensor_logs()
        assert result == []


class TestGetSensorHistory:
    """Tests for get_sensor_history function"""

    @patch('db.db')
    def test_get_sensor_history_success(self, mock_db):
        """Test successful retrieval of sensor history"""
        from db import get_sensor_history, firestore

        mock_doc = Mock()
        mock_doc.to_dict.return_value = {"temperature": 23.0, "unix_timestamp": 1704100000}
        mock_doc.id = "hist1"

        mock_query = Mock()
        mock_query.order_by.return_value.stream.return_value = [mock_doc]
        mock_collection = Mock()
        mock_collection.where.return_value = mock_query
        mock_db.collection.return_value = mock_collection

        result = get_sensor_history(hours=24)

        mock_db.collection.assert_called_once_with("sensor_logs")
        assert len(result) == 1
        assert result[0]["id"] == "hist1"

    @patch('db.db')
    def test_get_sensor_history_error(self, mock_db):
        """Test error handling when fetch fails"""
        from db import get_sensor_history

        mock_db.collection.side_effect = Exception("Firestore error")

        result = get_sensor_history()
        assert result == []

    @patch('db.db', None)
    def test_get_sensor_history_no_db(self):
        """Test retrieval when db is None"""
        from db import get_sensor_history

        result = get_sensor_history()
        assert result == []


class TestSaveSeedGuide:
    """Tests for save_seed_guide function"""

    @patch('db.db')
    def test_save_seed_guide_with_doc_id(self, mock_db):
        """Test updating existing seed guide by doc_id"""
        from db import save_seed_guide

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        result = save_seed_guide({"title": "Tomato Guide"}, doc_id="existing-id")

        assert result == "existing-id"
        mock_collection.document.assert_called_once_with("existing-id")
        mock_doc_ref.set.assert_called_once()
        call_args, call_kwargs = mock_doc_ref.set.call_args
        assert call_kwargs == {"merge": True}

    @patch('db.db')
    def test_save_seed_guide_without_doc_id(self, mock_db):
        """Test creating a new seed guide (auto-id)"""
        from db import save_seed_guide

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc_ref.id = "auto-generated-id"
        mock_db.collection.return_value = mock_collection
        mock_collection.add.return_value = (Mock(), mock_doc_ref)

        result = save_seed_guide({"title": "Cucumber Guide"})

        assert result == "auto-generated-id"
        mock_collection.add.assert_called_once()

    @patch('db.db')
    def test_save_seed_guide_error(self, mock_db):
        """Test error handling when save fails"""
        from db import save_seed_guide
        import pytest

        mock_db.collection.side_effect = Exception("Firestore error")

        with pytest.raises(Exception, match="Firestore error"):
            save_seed_guide({"title": "Fail Guide"})

    @patch('db.db', None)
    def test_save_seed_guide_no_db(self):
        """Test save when db is None"""
        from db import save_seed_guide

        result = save_seed_guide({"title": "Offline Guide"})
        assert result == "mock-id-firestore-unavailable"


class TestUpdateSeedGuideStatus:
    """Tests for update_seed_guide_status function"""

    @patch('db.db')
    def test_update_seed_guide_status_success(self, mock_db):
        """Test successful status update"""
        from db import update_seed_guide_status

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        update_seed_guide_status("doc-1", "completed")

        mock_collection.document.assert_called_once_with("doc-1")
        call_args = mock_doc_ref.set.call_args[0][0]
        assert call_args["status"] == "completed"
        assert "message" not in call_args
        assert "steps" not in call_args

    @patch('db.db')
    def test_update_seed_guide_status_with_message(self, mock_db):
        """Test status update with message"""
        from db import update_seed_guide_status

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        update_seed_guide_status("doc-1", "error", message="Something failed")

        call_args = mock_doc_ref.set.call_args[0][0]
        assert call_args["status"] == "error"
        assert call_args["message"] == "Something failed"

    @patch('db.db')
    def test_update_seed_guide_status_with_result(self, mock_db):
        """Test status update with result (steps)"""
        from db import update_seed_guide_status

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        steps = [{"step": 1, "action": "Plant seed"}]
        update_seed_guide_status("doc-1", "completed", result=steps)

        call_args = mock_doc_ref.set.call_args[0][0]
        assert call_args["steps"] == steps

    @patch('db.db')
    def test_update_seed_guide_status_error(self, mock_db):
        """Test error handling when update fails"""
        from db import update_seed_guide_status

        mock_db.collection.side_effect = Exception("Firestore error")

        # Should not raise
        update_seed_guide_status("doc-1", "completed")

    @patch('db.db', None)
    def test_update_seed_guide_status_no_db(self):
        """Test update when db is None"""
        from db import update_seed_guide_status

        # Should return immediately
        update_seed_guide_status("doc-1", "completed")


class TestGetAllSeedGuides:
    """Tests for get_all_seed_guides function"""

    @patch('db.db')
    def test_get_all_seed_guides_success(self, mock_db):
        """Test successful retrieval of seed guides"""
        from db import get_all_seed_guides

        mock_doc = Mock()
        mock_doc.id = "guide1"
        mock_doc.to_dict.return_value = {"title": "Tomato Guide", "status": "completed"}

        mock_query = Mock()
        mock_query.stream.return_value = [mock_doc]
        mock_collection = Mock()
        mock_collection.order_by.return_value = mock_query
        mock_db.collection.return_value = mock_collection

        result = get_all_seed_guides()

        assert len(result) == 1
        assert result[0]["id"] == "guide1"
        assert result[0]["title"] == "Tomato Guide"

    @patch('db.db')
    def test_get_all_seed_guides_with_datetime_conversion(self, mock_db):
        """Test that datetime fields are converted to isoformat"""
        from db import get_all_seed_guides
        from datetime import datetime

        dt_created = datetime(2024, 6, 1, 10, 0, 0)
        dt_updated = datetime(2024, 6, 2, 12, 0, 0)
        mock_doc = Mock()
        mock_doc.id = "guide2"
        mock_doc.to_dict.return_value = {
            "title": "Carrot Guide",
            "created_at": dt_created,
            "updated_at": dt_updated
        }

        mock_query = Mock()
        mock_query.stream.return_value = [mock_doc]
        mock_collection = Mock()
        mock_collection.order_by.return_value = mock_query
        mock_db.collection.return_value = mock_collection

        result = get_all_seed_guides()

        assert result[0]["created_at"] == dt_created.isoformat()
        assert result[0]["updated_at"] == dt_updated.isoformat()

    @patch('db.db')
    def test_get_all_seed_guides_error(self, mock_db):
        """Test error handling when fetch fails"""
        from db import get_all_seed_guides

        mock_db.collection.side_effect = Exception("Firestore error")

        result = get_all_seed_guides()
        assert result == []

    @patch('db.db', None)
    def test_get_all_seed_guides_no_db(self):
        """Test retrieval when db is None"""
        from db import get_all_seed_guides

        result = get_all_seed_guides()
        assert result == []


class TestGetSeedGuide:
    """Tests for get_seed_guide function"""

    @patch('db.db')
    def test_get_seed_guide_success(self, mock_db):
        """Test successful retrieval of a seed guide"""
        from db import get_seed_guide

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.id = "guide-1"
        mock_doc.to_dict.return_value = {"title": "Tomato Guide", "status": "completed"}
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        result = get_seed_guide("guide-1")

        assert result is not None
        assert result["id"] == "guide-1"
        assert result["title"] == "Tomato Guide"

    @patch('db.db')
    def test_get_seed_guide_with_datetime(self, mock_db):
        """Test that datetime fields are converted to isoformat"""
        from db import get_seed_guide
        from datetime import datetime

        dt_created = datetime(2024, 3, 15, 9, 0, 0)
        dt_updated = datetime(2024, 3, 16, 10, 0, 0)
        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.id = "guide-dt"
        mock_doc.to_dict.return_value = {
            "title": "Date Guide",
            "created_at": dt_created,
            "updated_at": dt_updated
        }
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        result = get_seed_guide("guide-dt")

        assert result["created_at"] == dt_created.isoformat()
        assert result["updated_at"] == dt_updated.isoformat()

    @patch('db.db')
    def test_get_seed_guide_not_found(self, mock_db):
        """Test retrieval when document doesn't exist"""
        from db import get_seed_guide

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = False
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        result = get_seed_guide("non-existent")

        assert result is None

    @patch('db.db')
    def test_get_seed_guide_error(self, mock_db):
        """Test error handling when fetch fails"""
        from db import get_seed_guide

        mock_db.collection.side_effect = Exception("Firestore error")

        result = get_seed_guide("guide-1")
        assert result is None

    @patch('db.db', None)
    def test_get_seed_guide_no_db(self):
        """Test retrieval when db is None"""
        from db import get_seed_guide

        result = get_seed_guide("guide-1")
        assert result is None


class TestGetAllCharacterJobs:
    """Tests for get_all_character_jobs function"""

    @patch('db.db')
    def test_get_all_character_jobs_success(self, mock_db):
        """Test successful retrieval of character jobs"""
        from db import get_all_character_jobs

        mock_doc = Mock()
        mock_doc.id = "job1"
        mock_doc.to_dict.return_value = {
            "status": "COMPLETED",
            "result": {"character_name": "Tomatoちゃん"}
        }

        mock_query = Mock()
        mock_query.stream.return_value = [mock_doc]
        mock_collection = Mock()
        mock_collection.where.return_value = mock_query
        mock_db.collection.return_value = mock_collection

        result = get_all_character_jobs()

        assert len(result) == 1
        assert result[0]["id"] == "job1"

    @patch('db.db')
    def test_get_all_character_jobs_with_timestamp_sorting(self, mock_db):
        """Test that results are sorted by created_at descending"""
        from db import get_all_character_jobs
        from datetime import datetime

        dt1 = datetime(2024, 1, 1, 10, 0, 0)
        dt2 = datetime(2024, 6, 1, 10, 0, 0)

        mock_doc1 = Mock()
        mock_doc1.id = "job-old"
        mock_doc1.to_dict.return_value = {
            "status": "COMPLETED",
            "created_at": dt1,
            "updated_at": dt1
        }

        mock_doc2 = Mock()
        mock_doc2.id = "job-new"
        mock_doc2.to_dict.return_value = {
            "status": "COMPLETED",
            "created_at": dt2,
            "updated_at": dt2
        }

        mock_query = Mock()
        mock_query.stream.return_value = [mock_doc1, mock_doc2]
        mock_collection = Mock()
        mock_collection.where.return_value = mock_query
        mock_db.collection.return_value = mock_collection

        result = get_all_character_jobs()

        assert len(result) == 2
        # job-new should be first (more recent)
        assert result[0]["id"] == "job-new"
        assert result[1]["id"] == "job-old"
        # Verify datetime conversion via hasattr
        assert result[0]["created_at"] == dt2.isoformat()
        assert result[0]["updated_at"] == dt2.isoformat()

    @patch('db.db')
    def test_get_all_character_jobs_error(self, mock_db):
        """Test error handling when fetch fails"""
        from db import get_all_character_jobs

        mock_db.collection.side_effect = Exception("Firestore error")

        result = get_all_character_jobs()
        assert result == []

    @patch('db.db', None)
    def test_get_all_character_jobs_no_db(self):
        """Test retrieval when db is None"""
        from db import get_all_character_jobs

        result = get_all_character_jobs()
        assert result == []


class TestSelectCharacterForDiary:
    """Tests for select_character_for_diary function"""

    @patch('db.db')
    def test_select_character_for_diary_success(self, mock_db):
        """Test successful character selection for diary"""
        from db import select_character_for_diary

        # Mock character_jobs collection
        mock_job_doc = Mock()
        mock_job_doc.exists = True
        mock_job_doc.to_dict.return_value = {
            "status": "COMPLETED",
            "result": {
                "character_name": "Tomatoちゃん",
                "image_url": "gs://bucket/image.png",
                "personality": "cheerful"
            }
        }

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_job_doc
        mock_collection.document.return_value = mock_doc_ref
        mock_db.collection.return_value = mock_collection

        result = select_character_for_diary("job-1")

        assert result is True
        # Verify growing_diaries/Character was updated
        assert mock_db.collection.call_count == 2

    @patch('db.db')
    def test_select_character_for_diary_not_found(self, mock_db):
        """Test selection when job doesn't exist"""
        from db import select_character_for_diary

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = False
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        result = select_character_for_diary("non-existent")

        assert result is False

    @patch('db.db')
    def test_select_character_for_diary_not_completed(self, mock_db):
        """Test selection when job is not completed"""
        from db import select_character_for_diary

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"status": "PROCESSING", "result": {}}
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        result = select_character_for_diary("job-1")

        assert result is False

    @patch('db.db')
    def test_select_character_for_diary_no_result(self, mock_db):
        """Test selection when job has no result"""
        from db import select_character_for_diary

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"status": "COMPLETED", "result": None}
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        result = select_character_for_diary("job-1")

        assert result is False

    @patch('db.db')
    def test_select_character_for_diary_error(self, mock_db):
        """Test error handling during selection"""
        from db import select_character_for_diary

        mock_db.collection.side_effect = Exception("Firestore error")

        result = select_character_for_diary("job-1")

        assert result is False

    @patch('db.db', None)
    def test_select_character_for_diary_no_db(self):
        """Test selection when db is None"""
        from db import select_character_for_diary

        result = select_character_for_diary("job-1")

        assert result is False


class TestGetEdgeAgentConfig:
    """Tests for get_edge_agent_config function (additional coverage)"""

    @patch('db.db')
    def test_get_edge_agent_config_success(self, mock_db):
        """Test successful retrieval of edge agent config"""
        from db import get_edge_agent_config

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"instruction": "Grow tomatoes", "vegetable_name": "Tomato"}
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        result = get_edge_agent_config()
        assert result == {"instruction": "Grow tomatoes", "vegetable_name": "Tomato"}
        mock_db.collection.assert_called_once_with("configurations")
        mock_collection.document.assert_called_once_with("edge_agent")

    @patch('db.db')
    def test_get_edge_agent_config_not_found(self, mock_db):
        """Test retrieval when document doesn't exist"""
        from db import get_edge_agent_config

        mock_collection = Mock()
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = False
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        result = get_edge_agent_config()
        assert result == {}

    @patch('db.db')
    def test_get_edge_agent_config_error(self, mock_db):
        """Test error handling when fetch fails"""
        from db import get_edge_agent_config

        mock_db.collection.side_effect = Exception("Firestore error")

        result = get_edge_agent_config()
        assert result == {}

    @patch('db.db', None)
    def test_get_edge_agent_config_no_db(self):
        """Test retrieval when db is None"""
        from db import get_edge_agent_config

        result = get_edge_agent_config()
        assert result == {}


class TestGetLatestVegetableError:
    """Tests for get_latest_vegetable error path"""

    @patch('db.db')
    def test_get_latest_vegetable_error(self, mock_db):
        """Test error handling when fetch fails"""
        from db import get_latest_vegetable

        mock_db.collection.side_effect = Exception("Firestore error")

        result = get_latest_vegetable()
        assert result is None


class TestUpdateVegetableStatusWithExistingDocNoResult:
    """Additional coverage for update_vegetable_status edge cases"""

    @patch('db.db')
    def test_update_vegetable_status_existing_doc_no_result(self, mock_db):
        """Test merge when existing doc has no result field"""
        from db import update_vegetable_status

        mock_collection = Mock()
        mock_doc_ref = Mock()

        mock_existing_doc = Mock()
        mock_existing_doc.exists = True
        mock_existing_doc.to_dict.return_value = {"name": "Tomato"}
        mock_doc_ref.get.return_value = mock_existing_doc

        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        update_vegetable_status("test-id", "completed", {"new_data": "value"})

        call_args = mock_doc_ref.update.call_args[0][0]
        assert call_args["result"]["new_data"] == "value"

    @patch('db.db')
    def test_update_vegetable_status_doc_not_exists(self, mock_db):
        """Test merge when existing doc doesn't exist"""
        from db import update_vegetable_status

        mock_collection = Mock()
        mock_doc_ref = Mock()

        mock_existing_doc = Mock()
        mock_existing_doc.exists = False
        mock_doc_ref.get.return_value = mock_existing_doc

        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        update_vegetable_status("test-id", "completed", {"new_data": "value"})

        call_args = mock_doc_ref.update.call_args[0][0]
        assert call_args["result"]["new_data"] == "value"
