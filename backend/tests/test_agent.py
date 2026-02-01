"""Tests for agent.py functions"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGetAuthHeaders:
    """Tests for get_auth_headers function"""
    
    @patch('agent.google.auth.default')
    def test_get_auth_headers_success(self, mock_auth):
        """Test successful auth header retrieval"""
        from agent import get_auth_headers
        
        mock_creds = Mock()
        mock_creds.token = "test-token"
        mock_auth.return_value = (mock_creds, "test-project")
        
        headers = get_auth_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-token"
        assert headers["Content-Type"] == "application/json"


class TestGetAgentLocationAndId:
    """Tests for get_agent_location_and_id function"""
    
    @patch.dict(os.environ, {"AGENT_ENDPOINT": "projects/test/locations/us-central1/agents/test-agent"})
    def test_get_agent_location_and_id_success(self):
        """Test successful parsing of agent endpoint"""
        from agent import get_agent_location_and_id
        
        location, agent_id = get_agent_location_and_id()
        
        assert location == "us-central1"
        assert agent_id == "projects/test/locations/us-central1/agents/test-agent"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_agent_location_and_id_missing_env(self):
        """Test error when AGENT_ENDPOINT is not set"""
        from agent import get_agent_location_and_id
        
        with pytest.raises(ValueError, match="AGENT_ENDPOINT environment variable is not set"):
            get_agent_location_and_id()
    
    @patch.dict(os.environ, {"AGENT_ENDPOINT": "invalid/format"})
    def test_get_agent_location_and_id_invalid_format(self):
        """Test error with invalid endpoint format"""
        from agent import get_agent_location_and_id
        
        with pytest.raises(ValueError, match="Invalid AGENT_ENDPOINT format"):
            get_agent_location_and_id()


class TestCreateSession:
    """Tests for create_session function"""
    
    @patch('agent.requests.post')
    @patch('agent.get_auth_headers')
    @patch('agent.get_agent_location_and_id')
    def test_create_session_immediate_success(self, mock_location, mock_headers, mock_post):
        """Test immediate session creation (no LRO)"""
        from agent import create_session
        
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "name": "projects/test/locations/us-central1/sessions/test-session"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = create_session()
        
        assert result == "projects/test/locations/us-central1/sessions/test-session"
    
    @patch('agent.wait_for_lro')
    @patch('agent.requests.post')
    @patch('agent.get_auth_headers')
    @patch('agent.get_agent_location_and_id')
    def test_create_session_with_lro(self, mock_location, mock_headers, mock_post, mock_wait):
        """Test session creation with Long Running Operation"""
        from agent import create_session
        
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "name": "projects/test/locations/us-central1/operations/test-op"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        mock_wait.return_value = "projects/test/locations/us-central1/sessions/test-session"
        
        result = create_session()
        
        assert result == "projects/test/locations/us-central1/sessions/test-session"
        mock_wait.assert_called_once()


class TestQuerySession:
    """Tests for query_session function"""
    
    @patch('agent.requests.post')
    @patch('agent.get_auth_headers')
    @patch('agent.get_agent_location_and_id')
    def test_query_session_success(self, mock_location, mock_headers, mock_post):
        """Test successful session query"""
        from agent import query_session
        
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}
        
        # Mock SSE stream response
        mock_response = Mock()
        mock_response.iter_lines.return_value = [
            b'data: {"content": {"parts": [{"text": "Weather is"}]}}',
            b'data: {"content": {"parts": [{"text": " sunny"}]}}'
        ]
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = query_session("projects/test/locations/us-central1/sessions/test", "weather query")
        
        assert result == "Weather is sunny"
    
    @patch('agent.requests.post')
    @patch('agent.get_auth_headers')
    @patch('agent.get_agent_location_and_id')
    def test_query_session_empty_response(self, mock_location, mock_headers, mock_post):
        """Test query with empty response"""
        from agent import query_session
        
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}
        
        mock_response = Mock()
        mock_response.iter_lines.return_value = []
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = query_session("projects/test/locations/us-central1/sessions/test", "test")
        
        assert result == ""


class TestGetWeatherFromAgent:
    """Tests for get_weather_from_agent function"""
    
    @patch('agent.query_session')
    @patch('agent.create_session')
    def test_get_weather_success(self, mock_create, mock_query):
        """Test successful weather retrieval"""
        from agent import get_weather_from_agent
        
        mock_create.return_value = "test-session"
        mock_query.return_value = "Tokyo weather is sunny"
        
        result = get_weather_from_agent("Tokyo")
        
        assert result == "Tokyo weather is sunny"
        # Query should include Japanese text, but we can't test exact match due to encoding
        mock_query.assert_called_once()
    
    @patch('agent.create_session')
    def test_get_weather_error(self, mock_create):
        """Test error handling in weather retrieval"""
        from agent import get_weather_from_agent
        
        mock_create.side_effect = Exception("Connection error")
        
        result = get_weather_from_agent("Tokyo")
        
        # Check that error message is returned (in Japanese)
        assert "エラー" in result or "error" in result.lower()
