"""Tests for research_agent.py - seed packet analysis and deep research"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGetAuthHeaders:
    """Tests for get_auth_headers function"""
    
    @patch('research_agent.google.auth.default')
    def test_get_auth_headers_success_with_adc(self, mock_auth_default):
        """Test successful auth header retrieval with ADC"""
        mock_credentials = Mock()
        mock_credentials.token = "test-token"
        mock_credentials.valid = True
        mock_auth_default.return_value = (mock_credentials, "test-project")
        
        from research_agent import get_auth_headers
        
        headers, query_param = get_auth_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-token"
        assert query_param == ""
    
    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-api-key'})
    def test_get_auth_headers_with_api_key(self):
        """Test auth header with API key"""
        from research_agent import get_auth_headers
        
        headers, query_param = get_auth_headers()
        
        assert "Content-Type" in headers
        assert "?key=test-api-key" in query_param


class TestRequestWithRetry:
    """Tests for request_with_retry function"""
    
    @patch('research_agent.requests.request')
    def test_request_with_retry_success_first_attempt(self, mock_request):
        """Test successful request on first attempt"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        from research_agent import request_with_retry
        
        response = request_with_retry("GET", "https://example.com/api")
        
        assert response.status_code == 200
        mock_request.assert_called_once()
    
    @patch('research_agent.requests.request')
    @patch('research_agent.time.sleep')
    def test_request_with_retry_retries_on_429(self, mock_sleep, mock_request):
        """Test retry behavior on 429 rate limit"""
        mock_fail_response = Mock()
        mock_fail_response.status_code = 429
        
        mock_success_response = Mock()
        mock_success_response.status_code = 200
        
        mock_request.side_effect = [mock_fail_response, mock_success_response]
        
        from research_agent import request_with_retry
        
        response = request_with_retry("GET", "https://example.com/api")
        
        assert response.status_code == 200
        assert mock_request.call_count == 2


class TestAnalyzeSeedPacket:
    """Tests for analyze_seed_packet function"""
    
    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    def test_analyze_seed_packet_success(self, mock_headers, mock_request):
        """Test successful seed packet analysis"""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=test")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": '{"name": "Tomato", "visible_instructions": "Plant in spring"}'}]
                }
            }]
        }
        mock_request.return_value = mock_response
        
        from research_agent import analyze_seed_packet
        
        result = analyze_seed_packet(b"fake image bytes")
        
        assert "Tomato" in result
    
    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    def test_analyze_seed_packet_api_error(self, mock_headers, mock_request):
        """Test seed packet analysis with API error"""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "")
        
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_request.return_value = mock_response
        
        from research_agent import analyze_seed_packet
        
        # Should return error JSON instead of raising
        result = analyze_seed_packet(b"fake image bytes")
        assert "API Error" in result or "不明な野菜" in result


class TestPerformDeepResearch:
    """Tests for perform_deep_research function"""
    
    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    @patch('research_agent.time.sleep')
    def test_perform_deep_research_success(self, mock_sleep, mock_headers, mock_request):
        """Test successful deep research"""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=test")
        
        # First call: start interaction
        mock_start_response = Mock()
        mock_start_response.status_code = 200
        mock_start_response.json.return_value = {
            "name": "interactions/test-123"
        }
        
        # Second call: poll (completed)
        mock_poll_response = Mock()
        mock_poll_response.status_code = 200
        mock_poll_response.json.return_value = {
            "status": "completed",
            "outputs": [{"text": "Research results for Tomato"}]
        }
        
        # Third call: extraction
        mock_extract_response = Mock()
        mock_extract_response.status_code = 200
        mock_extract_response.raise_for_status = Mock()
        mock_extract_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '{"name": "Tomato", "summary_prompt": "Grow at 20-25C"}'
                    }]
                }
            }]
        }
        
        mock_request.side_effect = [mock_start_response, mock_poll_response, mock_extract_response]
        
        from research_agent import perform_deep_research
        
        result = perform_deep_research("Tomato", "Plant in spring")
        
        assert result is not None
        assert result.get("name") == "Tomato"
    
    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    def test_perform_deep_research_start_failure(self, mock_headers, mock_request):
        """Test deep research when start fails"""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "")
        
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        mock_request.return_value = mock_response
        
        from research_agent import perform_deep_research
        
        result = perform_deep_research("Tomato", "Plant info")
        
        assert "error" in result
