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
    
    @patch.dict(os.environ, {}, clear=False)
    @patch('research_agent.google.auth.default')
    def test_get_auth_headers_success_with_adc(self, mock_auth_default):
        """Test successful auth header retrieval with ADC"""
        # Remove GEMINI_API_KEY so ADC path is taken
        os.environ.pop('GEMINI_API_KEY', None)
        
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
    
    @patch('research_agent.requests.request')
    @patch('research_agent.time.sleep')
    def test_request_with_retry_retries_on_5xx(self, mock_sleep, mock_request):
        """Test retry behavior on 500/503 errors"""
        mock_fail_response_500 = Mock()
        mock_fail_response_500.status_code = 500
        
        mock_fail_response_503 = Mock()
        mock_fail_response_503.status_code = 503
        
        mock_success_response = Mock()
        mock_success_response.status_code = 200
        
        mock_request.side_effect = [mock_fail_response_500, mock_fail_response_503, mock_success_response]
        
        from research_agent import request_with_retry
        
        response = request_with_retry("GET", "https://example.com/api")
        
        assert response.status_code == 200
        assert mock_request.call_count == 3
        # Should sleep twice
        assert mock_sleep.call_count == 2

    @patch('research_agent.requests.request')
    @patch('research_agent.time.sleep')
    def test_request_with_retry_max_retries_exceeded(self, mock_sleep, mock_request):
        """Test max retries exceeded behavior"""
        mock_fail_response = Mock()
        mock_fail_response.status_code = 500
        
        mock_request.return_value = mock_fail_response
        
        from research_agent import request_with_retry
        
        response = request_with_retry("GET", "https://example.com/api")
        
        assert response.status_code == 500
        # 5 retries in loop (0..4)
        # i=0 (call 1) -> sleep 1
        # i=1 (call 2) -> sleep 2
        # i=2 (call 3) -> sleep 3
        # i=3 (call 4) -> sleep 4
        # i=4 (call 5) -> no sleep, return response
        
        assert mock_request.call_count == 5 
        assert mock_sleep.call_count == 4

    @patch('research_agent.requests.request')
    @patch('research_agent.time.sleep')
    def test_request_with_retry_no_retry_on_400(self, mock_sleep, mock_request):
        """Test no retry on 400 error"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_request.return_value = mock_response
        
        from research_agent import request_with_retry
        
        response = request_with_retry("GET", "https://example.com/api")
        
        assert response.status_code == 400
        assert mock_request.call_count == 1
        assert mock_sleep.call_count == 0


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


# ---------------------------------------------------------------------------
# Additional tests for 100% coverage
# ---------------------------------------------------------------------------


class TestGetAuthHeadersADCFailure:
    """Test ADC failure path in get_auth_headers (lines 37-39)"""

    @patch.dict(os.environ, {}, clear=False)
    @patch('research_agent.google.auth.default', side_effect=Exception("no creds"))
    def test_adc_failure_returns_empty_query_param(self, mock_auth):
        """When ADC fails, should return empty query_param."""
        os.environ.pop('GEMINI_API_KEY', None)
        from research_agent import get_auth_headers
        headers, query_param = get_auth_headers()
        assert query_param == ""
        assert headers["Content-Type"] == "application/json"


class TestRequestWithRetryRequestException:
    """Tests for RequestException branches in request_with_retry (lines 75-97)"""

    @patch('research_agent.requests.request')
    @patch('research_agent.time.sleep')
    def test_request_exception_retries_then_succeeds(self, mock_sleep, mock_request):
        """RequestException on first attempts, success on final."""
        import requests as req_lib
        mock_success = Mock()
        mock_success.status_code = 200
        mock_request.side_effect = [
            req_lib.exceptions.ConnectionError("conn err"),
            req_lib.exceptions.ConnectionError("conn err"),
            mock_success,  # final retry succeeds
        ]
        from research_agent import request_with_retry
        response = request_with_retry("GET", "https://example.com")
        assert response.status_code == 200

    @patch('research_agent.requests.request')
    @patch('research_agent.time.sleep')
    def test_request_exception_all_retries_exhausted_final_success(self, mock_sleep, mock_request):
        """All loop retries raise exception, but final attempt succeeds."""
        import requests as req_lib
        mock_success = Mock()
        mock_success.status_code = 200
        mock_request.side_effect = [
            req_lib.exceptions.ConnectionError("fail"),
            req_lib.exceptions.ConnectionError("fail"),
            req_lib.exceptions.ConnectionError("fail"),
            req_lib.exceptions.ConnectionError("fail"),
            req_lib.exceptions.ConnectionError("fail"),  # i=4 (last in loop)
            mock_success,  # final retry outside loop
        ]
        from research_agent import request_with_retry
        response = request_with_retry("GET", "https://example.com")
        assert response.status_code == 200

    @patch('research_agent.requests.request')
    @patch('research_agent.time.sleep')
    def test_request_exception_all_retries_and_final_fail(self, mock_sleep, mock_request):
        """All retries and final attempt all raise exception -> re-raise."""
        import requests as req_lib
        mock_request.side_effect = req_lib.exceptions.ConnectionError("permanent fail")
        from research_agent import request_with_retry
        with pytest.raises(req_lib.exceptions.ConnectionError, match="permanent fail"):
            request_with_retry("GET", "https://example.com")


class TestAnalyzeSeedPacketParseError:
    """Test analyze_seed_packet response parsing error (lines 141-143)"""

    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    def test_analyze_seed_packet_key_error(self, mock_headers, mock_request):
        """KeyError when response has unexpected structure."""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {"candidates": [{"content": {"parts": []}}]}
        mock_request.return_value = mock_resp
        from research_agent import analyze_seed_packet
        result = analyze_seed_packet(b"img")
        assert "Error" in result or "parsing failed" in result.lower()


class TestExtractStructuredResearchData:
    """Tests for extract_structured_research_data (lines 195-211)"""

    @patch('research_agent.request_with_retry')
    def test_extract_with_markdown_json(self, mock_request):
        """Test markdown cleanup (```json ... ```) path."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '```json\n{"name": "Tomato", "optimal_temp_range": "20-25C"}\n```'
                    }]
                }
            }]
        }
        mock_request.return_value = mock_resp
        from research_agent import extract_structured_research_data
        result = extract_structured_research_data(
            "Tomato", "report text", "?key=k",
            {"Content-Type": "application/json"},
            grounding_metadata={"sources": ["url1"]},
            raw_json_report='{"full": "report"}'
        )
        assert result["name"] == "Tomato"
        assert result["raw_report"] == '{"full": "report"}'
        assert result["grounding_metadata"] == {"sources": ["url1"]}

    @patch('research_agent.request_with_retry')
    def test_extract_with_plain_markdown(self, mock_request):
        """Test markdown cleanup (``` ... ```) without json label."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '```\n{"name": "Carrot", "summary_prompt": "grow"}\n```'
                    }]
                }
            }]
        }
        mock_request.return_value = mock_resp
        from research_agent import extract_structured_research_data
        result = extract_structured_research_data("Carrot", "report", "?key=k", {"Content-Type": "application/json"})
        assert result["name"] == "Carrot"
        assert result["raw_report"] == "report"  # No raw_json_report given

    @patch('research_agent.request_with_retry')
    def test_extract_parse_failure(self, mock_request):
        """Test error path when JSON parsing fails."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "not valid json at all"
                    }]
                }
            }]
        }
        mock_request.return_value = mock_resp
        from research_agent import extract_structured_research_data
        result = extract_structured_research_data("Tomato", "report", "?key=k", {"Content-Type": "application/json"})
        assert "error" in result
        assert result["name"] == "Tomato"


class TestPerformWebGroundingResearch:
    """Tests for perform_web_grounding_research (lines 221-285)"""

    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-key"})
    @patch('research_agent.get_auth_headers', return_value=({"Content-Type": "application/json"}, "?key=test-key"))
    @patch('research_agent.request_with_retry')
    def test_web_grounding_success(self, mock_request, mock_auth):
        """Test successful web grounding research."""
        # First call: web grounding
        mock_grounding_resp = Mock()
        mock_grounding_resp.status_code = 200
        mock_grounding_resp.raise_for_status = Mock()
        mock_grounding_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Tomato growing info from web"}]
                },
                "groundingMetadata": {"sources": ["url1"]}
            }]
        }
        # Second call: extraction
        mock_extract_resp = Mock()
        mock_extract_resp.status_code = 200
        mock_extract_resp.raise_for_status = Mock()
        mock_extract_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": '{"name": "Tomato", "summary_prompt": "grow tomato"}'}]
                }
            }]
        }
        mock_request.side_effect = [mock_grounding_resp, mock_extract_resp]
        from research_agent import perform_web_grounding_research
        result = perform_web_grounding_research("Tomato", "packet info")
        assert result["name"] == "Tomato"

    @patch.dict(os.environ, {}, clear=True)
    def test_web_grounding_no_api_key(self):
        """Test with missing SEED_GUIDE_GEMINI_KEY."""
        from research_agent import perform_web_grounding_research
        result = perform_web_grounding_research("Tomato", "info")
        assert "error" in result

    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-key"})
    @patch('research_agent.request_with_retry')
    def test_web_grounding_empty_candidates(self, mock_request):
        """Test with empty candidates in response."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {"candidates": []}
        mock_request.return_value = mock_resp
        from research_agent import perform_web_grounding_research
        result = perform_web_grounding_research("Tomato", "info")
        assert "error" in result

    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-key"})
    @patch('research_agent.request_with_retry')
    def test_web_grounding_parse_error(self, mock_request):
        """Test KeyError/IndexError when parsing response."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {"candidates": [{"content": {"parts": []}}]}
        mock_request.return_value = mock_resp
        from research_agent import perform_web_grounding_research
        result = perform_web_grounding_research("Tomato", "info")
        assert "error" in result

    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-key"})
    @patch('research_agent.request_with_retry')
    def test_web_grounding_request_exception(self, mock_request):
        """Test generic exception during web grounding."""
        mock_request.side_effect = Exception("network error")
        from research_agent import perform_web_grounding_research
        result = perform_web_grounding_research("Tomato", "info")
        assert "error" in result


class TestPerformDeepResearchAdditional:
    """Additional tests for perform_deep_research edge cases (lines 319-363)"""

    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    @patch('research_agent.time.sleep')
    def test_poll_404_returns_error(self, mock_sleep, mock_headers, mock_request):
        """Test 404 during polling returns error."""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")
        mock_start = Mock()
        mock_start.status_code = 200
        mock_start.json.return_value = {"name": "interactions/i1"}
        mock_poll_404 = Mock()
        mock_poll_404.status_code = 404
        mock_request.side_effect = [mock_start, mock_poll_404]
        from research_agent import perform_deep_research
        result = perform_deep_research("Tomato", "info")
        assert "error" in result
        assert "404" in result["error"]

    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    @patch('research_agent.time.sleep')
    def test_poll_status_failed(self, mock_sleep, mock_headers, mock_request):
        """Test status='failed' during polling."""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")
        mock_start = Mock()
        mock_start.status_code = 200
        mock_start.json.return_value = {"name": "interactions/i1"}
        mock_poll = Mock()
        mock_poll.status_code = 200
        mock_poll.json.return_value = {"status": "failed", "error": "timeout"}
        mock_request.side_effect = [mock_start, mock_poll]
        from research_agent import perform_deep_research
        result = perform_deep_research("Tomato", "info")
        assert "error" in result

    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    @patch('research_agent.time.sleep')
    def test_poll_timeout(self, mock_sleep, mock_headers, mock_request):
        """Test polling timeout after max retries."""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")
        mock_start = Mock()
        mock_start.status_code = 200
        mock_start.json.return_value = {"name": "interactions/i1"}
        mock_poll = Mock()
        mock_poll.status_code = 200
        mock_poll.json.return_value = {"status": "running"}
        mock_request.side_effect = [mock_start] + [mock_poll] * 180
        from research_agent import perform_deep_research
        result = perform_deep_research("Tomato", "info")
        assert "error" in result
        assert "Timeout" in result["error"]

    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    def test_generic_exception(self, mock_headers, mock_request):
        """Test generic exception handling."""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")
        mock_request.side_effect = Exception("network fail")
        from research_agent import perform_deep_research
        result = perform_deep_research("Tomato", "info")
        assert "error" in result

    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    @patch('research_agent.time.sleep')
    def test_interaction_id_fallback(self, mock_sleep, mock_headers, mock_request):
        """Test interaction name construction from 'id' field."""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")
        mock_start = Mock()
        mock_start.status_code = 200
        mock_start.json.return_value = {"id": "abc123"}  # 'id' instead of 'name'
        mock_poll = Mock()
        mock_poll.status_code = 200
        mock_poll.json.return_value = {"status": "completed", "outputs": [{"text": "result"}]}
        mock_extract = Mock()
        mock_extract.status_code = 200
        mock_extract.raise_for_status = Mock()
        mock_extract.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": '{"name": "Tomato"}'}]}}]
        }
        mock_request.side_effect = [mock_start, mock_poll, mock_extract]
        from research_agent import perform_deep_research
        result = perform_deep_research("Tomato", "info")
        assert result["name"] == "Tomato"

    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    @patch('research_agent.time.sleep')
    def test_poll_non_200_non_404_retries(self, mock_sleep, mock_headers, mock_request):
        """Test non-200/non-404 poll response triggers sleep and retry."""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")
        mock_start = Mock()
        mock_start.status_code = 200
        mock_start.json.return_value = {"name": "interactions/i1"}
        mock_poll_500 = Mock()
        mock_poll_500.status_code = 500
        mock_poll_success = Mock()
        mock_poll_success.status_code = 200
        mock_poll_success.json.return_value = {"status": "completed", "outputs": [{"text": "data"}]}
        mock_extract = Mock()
        mock_extract.status_code = 200
        mock_extract.raise_for_status = Mock()
        mock_extract.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": '{"name": "Tomato"}'}]}}]
        }
        mock_request.side_effect = [mock_start, mock_poll_500, mock_poll_success, mock_extract]
        from research_agent import perform_deep_research
        result = perform_deep_research("Tomato", "info")
        assert result["name"] == "Tomato"


# ============================================================
# Additional tests for 100% coverage
# ============================================================


class TestGetAuthHeadersADCFailure:
    """Tests for get_auth_headers ADC failure path (lines 37-39)"""

    @patch.dict(os.environ, {}, clear=False)
    @patch('research_agent.google.auth.default', side_effect=Exception("ADC unavailable"))
    def test_get_auth_headers_adc_exception(self, mock_auth_default):
        """When GEMINI_API_KEY is unset and ADC raises, return empty query_param"""
        os.environ.pop('GEMINI_API_KEY', None)

        from research_agent import get_auth_headers

        headers, query_param = get_auth_headers()

        assert headers == {"Content-Type": "application/json"}
        assert query_param == ""
        mock_auth_default.assert_called_once()


class TestRequestWithRetryExceptionPaths:
    """Tests for request_with_retry RequestException handling (lines 75-97)"""

    @patch('research_agent.requests.request')
    @patch('research_agent.time.sleep')
    def test_request_exception_retries_then_succeeds(self, mock_sleep, mock_request):
        """RequestException on first attempts, then success on final retry"""
        import requests as real_requests

        mock_success = Mock()
        mock_success.status_code = 200

        mock_request.side_effect = [
            real_requests.exceptions.RequestException("conn error"),
            real_requests.exceptions.RequestException("conn error"),
            mock_success,  # 3rd attempt inside loop succeeds
        ]

        from research_agent import request_with_retry

        response = request_with_retry("GET", "https://example.com")
        assert response.status_code == 200
        assert mock_sleep.call_count == 2

    @patch('research_agent.requests.request')
    @patch('research_agent.time.sleep')
    def test_request_exception_all_retries_then_final_success(self, mock_sleep, mock_request):
        """RequestException for all 5 loop iterations, final retry succeeds"""
        import requests as real_requests

        mock_success = Mock()
        mock_success.status_code = 200

        # 5 failures in the loop + 1 success in the final retry
        mock_request.side_effect = [
            real_requests.exceptions.RequestException("err"),
            real_requests.exceptions.RequestException("err"),
            real_requests.exceptions.RequestException("err"),
            real_requests.exceptions.RequestException("err"),
            real_requests.exceptions.RequestException("err"),
            mock_success,
        ]

        from research_agent import request_with_retry

        response = request_with_retry("GET", "https://example.com")
        assert response.status_code == 200
        # sleep called for i=0..3 (4 times), i=4 is last so no sleep
        assert mock_sleep.call_count == 4
        # 5 in loop + 1 final = 6
        assert mock_request.call_count == 6

    @patch('research_agent.requests.request')
    @patch('research_agent.time.sleep')
    def test_request_exception_all_retries_final_also_fails(self, mock_sleep, mock_request):
        """RequestException for all attempts including final retry → raises"""
        import requests as real_requests

        mock_request.side_effect = real_requests.exceptions.RequestException("persistent failure")

        from research_agent import request_with_retry

        with pytest.raises(real_requests.exceptions.RequestException, match="persistent failure"):
            request_with_retry("GET", "https://example.com")

        # 5 in loop + 1 final = 6
        assert mock_request.call_count == 6


class TestAnalyzeSeedPacketResponseParsing:
    """Tests for analyze_seed_packet KeyError/IndexError catch (lines 141-143)"""

    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    def test_analyze_seed_packet_malformed_response(self, mock_headers, mock_request):
        """Response JSON missing candidates → returns error JSON"""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"bad": "structure"}
        mock_request.return_value = mock_response

        from research_agent import analyze_seed_packet

        result = analyze_seed_packet(b"fake image")
        assert "Error" in result
        assert "Response parsing failed" in result

    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    def test_analyze_seed_packet_empty_candidates(self, mock_headers, mock_request):
        """candidates list is empty → IndexError caught"""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"candidates": []}
        mock_request.return_value = mock_response

        from research_agent import analyze_seed_packet

        result = analyze_seed_packet(b"fake image")
        assert "Response parsing failed" in result


class TestExtractStructuredResearchData:
    """Tests for extract_structured_research_data (lines 195-211)"""

    @patch('research_agent.request_with_retry')
    def test_extract_markdown_json_cleanup(self, mock_request):
        """Response contains ```json ... ``` markers → cleaned properly"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '```json\n{"name": "Daikon", "summary_prompt": "info"}\n```'
                    }]
                }
            }]
        }
        mock_request.return_value = mock_response

        from research_agent import extract_structured_research_data

        result = extract_structured_research_data(
            "Daikon", "report text", "?key=k",
            {"Content-Type": "application/json"},
            grounding_metadata={"sources": ["a"]},
            raw_json_report='{"raw": true}',
        )
        assert result["name"] == "Daikon"
        assert result["raw_report"] == '{"raw": true}'
        assert result["grounding_metadata"] == {"sources": ["a"]}

    @patch('research_agent.request_with_retry')
    def test_extract_generic_markdown_cleanup(self, mock_request):
        """Response wrapped in ``` ... ``` (no json tag) → cleaned"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '```\n{"name": "Carrot", "summary_prompt": "grow"}\n```'
                    }]
                }
            }]
        }
        mock_request.return_value = mock_response

        from research_agent import extract_structured_research_data

        result = extract_structured_research_data(
            "Carrot", "report text", "?key=k",
            {"Content-Type": "application/json"},
        )
        assert result["name"] == "Carrot"
        # No raw_json_report supplied → falls back to report_text
        assert result["raw_report"] == "report text"
        # No grounding_metadata supplied → key absent
        assert "grounding_metadata" not in result

    @patch('research_agent.request_with_retry')
    def test_extract_error_path(self, mock_request):
        """Extraction fails (invalid JSON) → returns partial data with error"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "NOT VALID JSON AT ALL"}]
                }
            }]
        }
        mock_request.return_value = mock_response

        from research_agent import extract_structured_research_data

        result = extract_structured_research_data(
            "Onion", "report text", "?key=k",
            {"Content-Type": "application/json"},
            raw_json_report='{"raw": "data"}',
        )
        assert result["name"] == "Onion"
        assert "error" in result
        assert "Extraction Parsing Failed" in result["error"]
        assert result["raw_report"] == '{"raw": "data"}'

    @patch('research_agent.request_with_retry')
    def test_extract_error_path_no_raw_json(self, mock_request):
        """Extraction fails without raw_json_report → raw_report = report_text"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "INVALID"}]
                }
            }]
        }
        mock_request.return_value = mock_response

        from research_agent import extract_structured_research_data

        result = extract_structured_research_data(
            "Leek", "original report", "?key=k",
            {"Content-Type": "application/json"},
        )
        assert result["raw_report"] == "original report"
        assert "error" in result


class TestPerformWebGroundingResearch:
    """Tests for perform_web_grounding_research (lines 221-285)"""

    @patch('research_agent.extract_structured_research_data')
    @patch('research_agent.get_auth_headers')
    @patch('research_agent.request_with_retry')
    @patch.dict(os.environ, {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_web_grounding_success(self, mock_request, mock_get_headers, mock_extract):
        """Full successful web grounding flow"""
        mock_get_headers.return_value = ({"Content-Type": "application/json"}, "?key=test-key")

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Web grounding results for Spinach"}]
                },
                "groundingMetadata": {"sources": ["url1"]}
            }]
        }
        mock_request.return_value = mock_response

        mock_extract.return_value = {"name": "Spinach", "summary_prompt": "details"}

        from research_agent import perform_web_grounding_research

        result = perform_web_grounding_research("Spinach", "packet info")
        assert result["name"] == "Spinach"
        mock_extract.assert_called_once()

    @patch.dict(os.environ, {}, clear=False)
    def test_web_grounding_missing_api_key(self):
        """SEED_GUIDE_GEMINI_KEY not set → returns error"""
        os.environ.pop('SEED_GUIDE_GEMINI_KEY', None)

        from research_agent import perform_web_grounding_research

        result = perform_web_grounding_research("Spinach", "info")
        assert result["error"] == "API Key missing"

    @patch('research_agent.request_with_retry')
    @patch.dict(os.environ, {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_web_grounding_empty_candidates(self, mock_request):
        """Response has no candidates → returns error"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"candidates": []}
        mock_request.return_value = mock_response

        from research_agent import perform_web_grounding_research

        result = perform_web_grounding_research("Eggplant", "info")
        assert "error" in result
        assert "Empty response" in result["error"]

    @patch('research_agent.request_with_retry')
    @patch.dict(os.environ, {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_web_grounding_parse_error(self, mock_request):
        """Response missing expected keys → KeyError/IndexError caught"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": []}}]
        }
        mock_request.return_value = mock_response

        from research_agent import perform_web_grounding_research

        result = perform_web_grounding_research("Pepper", "info")
        assert "error" in result
        assert "parsing failed" in result["error"]

    @patch('research_agent.request_with_retry')
    @patch.dict(os.environ, {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_web_grounding_request_exception(self, mock_request):
        """HTTP request raises exception → caught and returned"""
        mock_request.side_effect = Exception("Network error")

        from research_agent import perform_web_grounding_research

        result = perform_web_grounding_research("Lettuce", "info")
        assert result["error"] == "Network error"

    @patch('research_agent.extract_structured_research_data')
    @patch('research_agent.get_auth_headers')
    @patch('research_agent.request_with_retry')
    @patch.dict(os.environ, {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_web_grounding_no_packet_info(self, mock_request, mock_get_headers, mock_extract):
        """packet_info is empty string → topic does not include packet info"""
        mock_get_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "results"}]
                },
                "groundingMetadata": None
            }]
        }
        mock_request.return_value = mock_response
        mock_extract.return_value = {"name": "Basil"}

        from research_agent import perform_web_grounding_research

        result = perform_web_grounding_research("Basil", "")
        assert result["name"] == "Basil"


class TestPerformDeepResearchAdditional:
    """Additional tests for perform_deep_research uncovered paths"""

    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    @patch('research_agent.time.sleep')
    def test_deep_research_poll_404(self, mock_sleep, mock_headers, mock_request):
        """Polling returns 404 → returns error immediately (lines 319-321)"""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")

        mock_start = Mock()
        mock_start.status_code = 200
        mock_start.json.return_value = {"name": "interactions/abc"}

        mock_poll = Mock()
        mock_poll.status_code = 404

        mock_request.side_effect = [mock_start, mock_poll]

        from research_agent import perform_deep_research

        result = perform_deep_research("Tomato", "info")
        assert "error" in result
        assert "404" in result["error"]

    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    @patch('research_agent.time.sleep')
    def test_deep_research_status_failed(self, mock_sleep, mock_headers, mock_request):
        """Poll returns status 'failed' → returns error (lines 334-337)"""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")

        mock_start = Mock()
        mock_start.status_code = 200
        mock_start.json.return_value = {"name": "interactions/abc"}

        mock_poll = Mock()
        mock_poll.status_code = 200
        mock_poll.json.return_value = {
            "status": "failed",
            "error": "Internal processing error"
        }

        mock_request.side_effect = [mock_start, mock_poll]

        from research_agent import perform_deep_research

        result = perform_deep_research("Carrot", "")
        assert "error" in result
        assert "Research failed" in result["error"]
        assert "Internal processing error" in result["error"]

    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    @patch('research_agent.time.sleep')
    def test_deep_research_timeout(self, mock_sleep, mock_headers, mock_request):
        """All 180 polls return 'running' → timeout error (lines 348-354)"""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")

        mock_start = Mock()
        mock_start.status_code = 200
        mock_start.json.return_value = {"name": "interactions/abc"}

        mock_poll = Mock()
        mock_poll.status_code = 200
        mock_poll.json.return_value = {"status": "running"}

        mock_request.side_effect = [mock_start] + [mock_poll] * 180

        from research_agent import perform_deep_research

        result = perform_deep_research("Radish", "")
        assert "error" in result
        assert "Timeout" in result["error"]
        assert mock_sleep.call_count == 180

    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    def test_deep_research_generic_exception(self, mock_headers, mock_request):
        """Unexpected exception during research → caught (lines 361-363)"""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")

        mock_request.side_effect = RuntimeError("unexpected failure")

        from research_agent import perform_deep_research

        result = perform_deep_research("Corn", "info")
        assert result["name"] == "Corn"
        assert result["error"] == "unexpected failure"

    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    @patch('research_agent.time.sleep')
    def test_deep_research_interaction_id_fallback(self, mock_sleep, mock_headers, mock_request):
        """Start response has 'id' instead of 'name' → builds interaction_name"""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")

        mock_start = Mock()
        mock_start.status_code = 200
        mock_start.json.return_value = {"id": "xyz-456"}

        mock_poll = Mock()
        mock_poll.status_code = 200
        mock_poll.json.return_value = {
            "status": "completed",
            "outputs": [{"text": "Research done"}]
        }

        mock_extract = Mock()
        mock_extract.status_code = 200
        mock_extract.raise_for_status = Mock()
        mock_extract.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": '{"name": "Bean", "summary_prompt": "x"}'}]
                }
            }]
        }

        mock_request.side_effect = [mock_start, mock_poll, mock_extract]

        from research_agent import perform_deep_research

        result = perform_deep_research("Bean", "")
        assert result is not None
        # Verify poll URL was constructed with interactions/xyz-456
        poll_call = mock_request.call_args_list[1]
        assert "interactions/xyz-456" in poll_call[0][1]

    @patch('research_agent.request_with_retry')
    @patch('research_agent.get_auth_headers')
    @patch('research_agent.time.sleep')
    def test_deep_research_poll_non_200_non_404_retries(self, mock_sleep, mock_headers, mock_request):
        """Poll returns non-200/non-404 (e.g. 500) → sleeps and continues polling"""
        mock_headers.return_value = ({"Content-Type": "application/json"}, "?key=k")

        mock_start = Mock()
        mock_start.status_code = 200
        mock_start.json.return_value = {"name": "interactions/abc"}

        mock_poll_500 = Mock()
        mock_poll_500.status_code = 500

        mock_poll_ok = Mock()
        mock_poll_ok.status_code = 200
        mock_poll_ok.json.return_value = {
            "status": "completed",
            "outputs": [{"text": "done"}]
        }

        mock_extract = Mock()
        mock_extract.status_code = 200
        mock_extract.raise_for_status = Mock()
        mock_extract.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": '{"name": "Pea", "summary_prompt": "y"}'}]
                }
            }]
        }

        mock_request.side_effect = [mock_start, mock_poll_500, mock_poll_ok, mock_extract]

        from research_agent import perform_deep_research

        result = perform_deep_research("Pea", "")
        assert result["name"] == "Pea"
        # One sleep for the 500 poll
        assert mock_sleep.call_count >= 1
