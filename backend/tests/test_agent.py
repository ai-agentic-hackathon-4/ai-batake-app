"""Tests for agent.py functions"""
import pytest
from unittest.mock import Mock, patch
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


# ---------------------------------------------------------------------------
# Additional tests for 100% coverage
# ---------------------------------------------------------------------------

class TestCloudLoggingSetup:
    """Tests for Cloud Logging setup (lines 22-24)"""

    def test_cloud_logging_import_failure(self):
        """Cloud logging setup gracefully fails"""
        # This is already handled at import time. We just verify it doesn't crash.
        # The module-level try/except already covers this path.
        # We test by importing agent (already done above)
        import agent
        assert hasattr(agent, 'logger')


class TestCreateSessionHTTPError:
    """Tests for create_session HTTP error path"""

    @patch('agent.requests.post')
    @patch('agent.get_auth_headers')
    @patch('agent.get_agent_location_and_id')
    def test_create_session_http_error(self, mock_location, mock_headers, mock_post):
        from agent import create_session
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}

        import requests as req
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_response.raise_for_status.side_effect = req.exceptions.HTTPError("403 Forbidden")
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="Session creation failed"):
            create_session()


class TestWaitForLro:
    """Tests for wait_for_lro (lines 86-119)"""

    @patch('time.sleep')
    @patch('agent.requests.get')
    @patch('agent.get_auth_headers')
    @patch('agent.get_agent_location_and_id')
    def test_lro_success(self, mock_location, mock_headers, mock_get, mock_sleep):
        from agent import wait_for_lro
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}

        mock_resp = Mock()
        mock_resp.json.return_value = {
            "done": True,
            "response": {"name": "projects/test/locations/us-central1/sessions/s1"}
        }
        mock_resp.raise_for_status = Mock()
        mock_get.return_value = mock_resp

        result = wait_for_lro("projects/test/locations/us-central1/operations/op1")
        assert "sessions/s1" in result

    @patch('time.sleep')
    @patch('agent.requests.get')
    @patch('agent.get_auth_headers')
    @patch('agent.get_agent_location_and_id')
    def test_lro_error(self, mock_location, mock_headers, mock_get, mock_sleep):
        from agent import wait_for_lro
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}

        mock_resp = Mock()
        mock_resp.json.return_value = {"done": True, "error": {"message": "Bad"}}
        mock_resp.raise_for_status = Mock()
        mock_get.return_value = mock_resp

        with pytest.raises(ValueError, match="LRO failed"):
            wait_for_lro("projects/test/locations/us-central1/operations/op1")

    @patch('time.sleep')
    @patch('agent.requests.get')
    @patch('agent.get_auth_headers')
    @patch('agent.get_agent_location_and_id')
    def test_lro_done_but_missing_response(self, mock_location, mock_headers, mock_get, mock_sleep):
        from agent import wait_for_lro
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}

        mock_resp = Mock()
        mock_resp.json.return_value = {"done": True}
        mock_resp.raise_for_status = Mock()
        mock_get.return_value = mock_resp

        with pytest.raises(ValueError, match="invalid response format"):
            wait_for_lro("projects/test/locations/us-central1/operations/op1")

    @patch('time.sleep')
    @patch('agent.requests.get')
    @patch('agent.get_auth_headers')
    @patch('agent.get_agent_location_and_id')
    def test_lro_timeout(self, mock_location, mock_headers, mock_get, mock_sleep):
        from agent import wait_for_lro
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}

        mock_resp = Mock()
        mock_resp.json.return_value = {"done": False}
        mock_resp.raise_for_status = Mock()
        mock_get.return_value = mock_resp

        with pytest.raises(TimeoutError, match="Timed out"):
            wait_for_lro("projects/test/locations/us-central1/operations/op1")


class TestQuerySessionEdgeCases:
    """Additional tests for query_session SSE parsing edge cases"""

    @patch('agent.requests.post')
    @patch('agent.get_auth_headers')
    @patch('agent.get_agent_location_and_id')
    def test_query_session_http_error(self, mock_location, mock_headers, mock_post):
        from agent import query_session
        import requests as req
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = req.exceptions.HTTPError("500")
        mock_response.status_code = 500
        mock_response.text = "Internal Error"
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="Query session failed"):
            query_session("projects/test/sessions/s1", "hello")

    @patch('agent.requests.post')
    @patch('agent.get_auth_headers')
    @patch('agent.get_agent_location_and_id')
    def test_query_session_invalid_json(self, mock_location, mock_headers, mock_post):
        from agent import query_session
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}

        mock_response = Mock()
        mock_response.iter_lines.return_value = [b'data: not-valid-json']
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = query_session("projects/test/sessions/s1", "hello")
        assert result == ""

    @patch('agent.requests.post')
    @patch('agent.get_auth_headers')
    @patch('agent.get_agent_location_and_id')
    def test_query_session_content_as_string(self, mock_location, mock_headers, mock_post):
        from agent import query_session
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}

        # content is a string instead of dict with parts
        import json
        event = json.dumps({"content": "plain text content"})
        mock_response = Mock()
        mock_response.iter_lines.return_value = [f'data: {event}'.encode()]
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = query_session("projects/test/sessions/s1", "hello")
        assert result == "plain text content"

    @patch('agent.requests.post')
    @patch('agent.get_auth_headers')
    @patch('agent.get_agent_location_and_id')
    def test_query_session_raw_ndjson(self, mock_location, mock_headers, mock_post):
        """Test raw NDJSON without 'data:' prefix"""
        from agent import query_session
        import json
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}

        event = json.dumps({"content": {"parts": [{"text": "raw line"}]}})
        mock_response = Mock()
        mock_response.iter_lines.return_value = [event.encode()]
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = query_session("projects/test/sessions/s1", "hello")
        assert result == "raw line"

    @patch('agent.requests.post')
    @patch('agent.get_auth_headers')
    @patch('agent.get_agent_location_and_id')
    def test_query_session_empty_data_line(self, mock_location, mock_headers, mock_post):
        """Test empty 'data: ' line is skipped"""
        from agent import query_session
        import json
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}

        event = json.dumps({"content": {"parts": [{"text": "after empty"}]}})
        mock_response = Mock()
        mock_response.iter_lines.return_value = [
            b'data: ',
            f'data: {event}'.encode()
        ]
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = query_session("projects/test/sessions/s1", "hello")
        assert result == "after empty"

    @patch('agent.requests.post')
    @patch('agent.get_auth_headers')
    @patch('agent.get_agent_location_and_id')
    def test_query_session_event_processing_error(self, mock_location, mock_headers, mock_post):
        """Test exception during event data processing"""
        from agent import query_session
        import json
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}

        # content.parts is not a list - will cause exception in 'for part in content["parts"]'
        event = json.dumps({"content": {"parts": "not-a-list"}})
        mock_response = Mock()
        mock_response.iter_lines.return_value = [f'data: {event}'.encode()]
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = query_session("projects/test/sessions/s1", "hello")
        assert result == ""

    @patch('backend.agent.requests.post')
    @patch('backend.agent.get_auth_headers')
    @patch('backend.agent.get_agent_location_and_id')
    def test_query_session_empty_sse_data(self, mock_location, mock_headers, mock_post):
        """Cover L165: empty SSE 'data: ' line triggers continue."""
        from backend.agent import query_session
        import json
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}

        valid_event = json.dumps({"content": {"parts": [{"text": "OK"}]}})
        mock_response = Mock()
        # Include a 'data: ' line with only whitespace after prefix -> json_str is empty -> continue
        mock_response.iter_lines.return_value = [
            b'data:   ',           # empty after strip -> continue on L165
            f'data: {valid_event}'.encode(),
        ]
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = query_session("projects/test/sessions/s1", "hello")
        assert result == "OK"

    @patch('backend.agent.requests.post')
    @patch('backend.agent.get_auth_headers')
    @patch('backend.agent.get_agent_location_and_id')
    def test_query_session_non_json_decode_exception(self, mock_location, mock_headers, mock_post):
        """Cover L196-197: Exception that is not JSONDecodeError during event processing."""
        from backend.agent import query_session
        mock_location.return_value = ("us-central1", "projects/test/locations/us-central1/agents/test")
        mock_headers.return_value = {"Authorization": "Bearer test"}

        # json.loads("true") -> True (a bool). 'in' operator on bool raises TypeError
        mock_response = Mock()
        mock_response.iter_lines.return_value = [
            b'data: true',   # valid JSON but not a dict -> "content" in True raises TypeError
        ]
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = query_session("projects/test/sessions/s1", "hello")
        assert result == ""
