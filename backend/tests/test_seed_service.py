"""Tests for seed_service.py functions"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAnalyzeSeedAndGenerateGuide:
    """Tests for analyze_seed_and_generate_guide function"""
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-api-key"})
    @patch('seed_service.requests.post')
    async def test_analyze_seed_success(self, mock_post):
        """Test successful seed analysis and guide generation"""
        from seed_service import analyze_seed_and_generate_guide
        
        # Mock Gemini 3 Pro response (analysis)
        analysis_response = Mock()
        analysis_response.status_code = 200
        analysis_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '[{"step_title": "準備", "description": "土を準備します", "image_prompt": "Prepare soil"}]'
                    }]
                }
            }]
        }
        
        # Mock Nanobanana Pro response (image generation)
        image_response = Mock()
        image_response.status_code = 200
        image_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "inlineData": {
                            "data": "base64imagedata"
                        }
                    }]
                }
            }]
        }
        
        mock_post.side_effect = [analysis_response, image_response]
        
        image_bytes = b"fake image data"
        result = await analyze_seed_and_generate_guide(image_bytes)
        
        assert len(result) == 3
        guide_title, guide_description, steps = result
        assert len(steps) == 1
        assert steps[0]["title"] == "準備"
        assert steps[0]["description"] == "土を準備します"
        assert steps[0]["image_base64"] == "base64imagedata"
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {}, clear=True)
    async def test_analyze_seed_missing_api_key(self):
        """Test error when API key is missing"""
        from seed_service import analyze_seed_and_generate_guide
        
        image_bytes = b"fake image data"
        
        with pytest.raises(RuntimeError, match="SEED_GUIDE_GEMINI_KEY environment variable not set"):
            await analyze_seed_and_generate_guide(image_bytes)
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-api-key"})
    @patch('seed_service.time.sleep')
    @patch('seed_service.requests.post')
    async def test_analyze_seed_api_failure(self, mock_post, mock_sleep):
        """Test handling of API failure"""
        from seed_service import analyze_seed_and_generate_guide
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.headers = {}  # No Retry-After header
        mock_post.return_value = mock_response
        
        image_bytes = b"fake image data"
        
        with pytest.raises(RuntimeError):
            await analyze_seed_and_generate_guide(image_bytes)
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-api-key"})
    @patch('seed_service.requests.post')
    async def test_analyze_seed_with_progress_callback(self, mock_post):
        """Test seed analysis with progress callback"""
        from seed_service import analyze_seed_and_generate_guide
        
        # Mock successful responses
        analysis_response = Mock()
        analysis_response.status_code = 200
        analysis_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '[{"step_title": "Test", "description": "Test desc", "image_prompt": "Test prompt"}]'
                    }]
                }
            }]
        }
        
        image_response = Mock()
        image_response.status_code = 200
        image_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "inlineData": {
                            "data": "testdata"
                        }
                    }]
                }
            }]
        }
        
        mock_post.side_effect = [analysis_response, image_response]
        
        # Track progress callback calls
        progress_messages = []
        
        async def progress_callback(msg):
            progress_messages.append(msg)
        
        image_bytes = b"fake image data"
        result = await analyze_seed_and_generate_guide(image_bytes, progress_callback)
        
        assert len(progress_messages) > 0
        assert any("analyzing" in msg.lower() or "分析" in msg or "AI" in msg for msg in progress_messages)
        guide_title, guide_description, steps = result
        assert len(steps) == 1


# ---------------------------------------------------------------------------
# Additional tests for 100% coverage
# ---------------------------------------------------------------------------
from unittest.mock import MagicMock, call
import json


class TestGetAccessToken:
    """Tests for get_access_token (lines 27-29)"""

    @patch('seed_service.Request')
    @patch('seed_service.google.auth.default')
    def test_get_access_token_success(self, mock_auth, mock_req):
        """Test successful token retrieval."""
        from seed_service import get_access_token
        mock_creds = Mock()
        mock_creds.token = "test-token-123"
        mock_auth.return_value = (mock_creds, "project")
        result = get_access_token()
        assert result == "test-token-123"
        mock_creds.refresh.assert_called_once()


class TestCallApiWithBackoff:
    """Tests for call_api_with_backoff (lines 35-105)"""

    @patch('seed_service.time.sleep')
    @patch('seed_service.time.time', return_value=0)
    @patch('seed_service.requests.post')
    def test_retry_on_429_with_retry_after_header(self, mock_post, mock_time, mock_sleep):
        """Test 429 with Retry-After header."""
        from seed_service import call_api_with_backoff

        resp_429 = Mock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "3"}

        resp_200 = Mock()
        resp_200.status_code = 200

        mock_post.side_effect = [resp_429, resp_200]
        result = call_api_with_backoff("http://test", {}, {}, max_elapsed_seconds=60)
        assert result.status_code == 200

    @patch('seed_service.time.sleep')
    @patch('seed_service.time.time', return_value=0)
    @patch('seed_service.requests.post')
    def test_retry_on_429_with_invalid_retry_after(self, mock_post, mock_time, mock_sleep):
        """Test 429 with invalid Retry-After value (not a number)."""
        from seed_service import call_api_with_backoff

        resp_429 = Mock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "not-a-number"}

        resp_200 = Mock()
        resp_200.status_code = 200
        mock_post.side_effect = [resp_429, resp_200]
        result = call_api_with_backoff("http://test", {}, {}, max_elapsed_seconds=60)
        assert result.status_code == 200

    @patch('seed_service.time.sleep')
    @patch('seed_service.time.time')
    @patch('seed_service.requests.post')
    def test_retry_budget_exceeded(self, mock_post, mock_time, mock_sleep):
        """Test RuntimeError when retry budget exceeded."""
        from seed_service import call_api_with_backoff
        # First call = start_time=0, second call inside loop = 100 (exceeds budget)
        mock_time.side_effect = [0, 100, 200]
        with pytest.raises(RuntimeError, match="Retry budget exceeded"):
            call_api_with_backoff("http://test", {}, {}, max_elapsed_seconds=30)

    @patch('seed_service.time.sleep')
    @patch('seed_service.time.time', return_value=0)
    @patch('seed_service.requests.post')
    def test_non_retryable_error(self, mock_post, mock_time, mock_sleep):
        """Test 400 error is returned without retry."""
        from seed_service import call_api_with_backoff
        resp_400 = Mock()
        resp_400.status_code = 400
        mock_post.return_value = resp_400
        result = call_api_with_backoff("http://test", {}, {}, max_elapsed_seconds=60)
        assert result.status_code == 400

    @patch('seed_service.time.sleep')
    @patch('seed_service.time.time', return_value=0)
    @patch('seed_service.requests.post')
    def test_network_error_retry(self, mock_post, mock_time, mock_sleep):
        """Test network error triggers retry."""
        import requests as req_lib
        from seed_service import call_api_with_backoff

        resp_200 = Mock()
        resp_200.status_code = 200
        mock_post.side_effect = [req_lib.exceptions.ConnectionError("err"), resp_200]
        result = call_api_with_backoff("http://test", {}, {}, max_elapsed_seconds=60)
        assert result.status_code == 200

    @patch('seed_service.time.sleep')
    @patch('seed_service.time.time', return_value=0)
    @patch('seed_service.requests.post')
    def test_max_retries_exceeded(self, mock_post, mock_time, mock_sleep):
        """Test RuntimeError when max retries exceeded."""
        import requests as req_lib
        from seed_service import call_api_with_backoff
        mock_post.side_effect = req_lib.exceptions.ConnectionError("always fail")
        with pytest.raises(RuntimeError, match="Max retries"):
            call_api_with_backoff("http://test", {}, {}, max_retries=3, max_elapsed_seconds=999)


class TestProcessStep:
    """Tests for process_step (lines 110-227)"""

    @patch('seed_service.random.uniform', return_value=0.5)
    @patch('seed_service.time.sleep')
    @patch('seed_service.call_api_with_backoff')
    def test_process_step_success_primary(self, mock_api, mock_sleep, mock_rand):
        """Test successful image generation with pro model (no fallback)."""
        from seed_service import process_step
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"inlineData": {"data": "imgb64"}}]}}]
        }
        mock_api.return_value = mock_resp
        step = {"step_title": "Plant", "description": "Plant seeds", "image_prompt": "planting"}
        result = process_step((step, "http://pro", {}))
        assert result["image_base64"] == "imgb64"
        assert result["title"] == "Plant"


    @patch('seed_service.random.uniform', return_value=0.5)
    @patch('seed_service.time.sleep')
    @patch('seed_service.call_api_with_backoff')
    def test_process_step_all_fail_placeholder(self, mock_api, mock_sleep, mock_rand):
        """Test all attempts fail, returns placeholder (no fallback)."""
        from seed_service import process_step, DEFAULT_PLACEHOLDER_B64
        mock_api.side_effect = Exception("all fail")
        step = {"step_title": "Grow", "description": "Growing", "image_prompt": "growing"}
        result = process_step((step, "http://pro", {}))
        assert result["image_base64"] == DEFAULT_PLACEHOLDER_B64
        assert "error" in result

    @patch('seed_service.random.uniform', return_value=0.5)
    @patch('seed_service.time.sleep')
    @patch('seed_service.call_api_with_backoff')
    def test_process_step_primary_exception(self, mock_api, mock_sleep, mock_rand):
        """Test exception in pro model returns placeholder (no fallback)."""
        from seed_service import process_step, DEFAULT_PLACEHOLDER_B64
        mock_api.side_effect = RuntimeError("pro error")
        step = {"step_title": "Soil", "description": "Prep soil", "image_prompt": "soil"}
        result = process_step((step, "http://pro", {}))
        assert result["image_base64"] == DEFAULT_PLACEHOLDER_B64
        assert "error" in result

    @patch('seed_service.random.uniform', return_value=0.5)
    @patch('seed_service.time.sleep')
    @patch('seed_service.call_api_with_backoff')
    def test_process_step_no_inline_data(self, mock_api, mock_sleep, mock_rand):
        """Test response without inlineData uses placeholder."""
        from seed_service import process_step, DEFAULT_PLACEHOLDER_B64
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "no image"}]}}]
        }
        mock_api.return_value = mock_resp
        step = {"step_title": "Sun", "description": "Sunlight", "image_prompt": "sun"}
        result = process_step((step, "http://pro", {}))
        assert result["image_base64"] == DEFAULT_PLACEHOLDER_B64


class TestGenerateImagesParallel:
    """Tests for _generate_images_parallel (lines 236-246)"""

    @patch('seed_service.process_step')
    def test_generate_images_parallel(self, mock_process):
        """Test parallel image generation (no fallback)."""
        from seed_service import _generate_images_parallel
        mock_process.side_effect = lambda args: {"title": args[0]["step_title"], "image_base64": "img"}
        steps = [
            {"step_title": "S1", "description": "D1", "image_prompt": "P1"},
            {"step_title": "S2", "description": "D2", "image_prompt": "P2"},
        ]
        result = _generate_images_parallel(steps, "http://pro", {})
        assert len(result) == 2
        assert result[0]["title"] == "S1"


class TestGenerateSingleGuideImage:
    """Tests for _generate_single_guide_image (lines 297-361)"""


    @patch('seed_service.call_api_with_backoff')
    def test_success(self, mock_api):
        """Test pro model generates image successfully."""
        from seed_service import _generate_single_guide_image
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"inlineData": {"data": "guide_img"}}]}}]
        }
        mock_api.return_value = mock_resp
        result = _generate_single_guide_image("Tomato Guide", [{"step_title": "S1", "description": "D1"}], "key", {})
        assert result == "guide_img"


    @patch('seed_service.call_api_with_backoff')
    def test_all_fail_returns_none(self, mock_api):
        """Test all models fail returns None."""
        from seed_service import _generate_single_guide_image
        fail = Mock()
        fail.status_code = 500
        mock_api.return_value = fail
        result = _generate_single_guide_image("Guide", [{"step_title": "S1", "description": "D1"}], "key", {})
        assert result is None

    @patch('seed_service.call_api_with_backoff')
    def test_primary_exception_returns_none(self, mock_api):
        """Test exception in pro model returns None (no fallback)."""
        from seed_service import _generate_single_guide_image
        mock_api.side_effect = RuntimeError("pro error")
        result = _generate_single_guide_image("Guide", [{"step_title": "S1", "description": "D1"}], "key", {})
        assert result is None


    @patch('seed_service.call_api_with_backoff')
    def test_all_exceptions(self, mock_api):
        """Test all attempts raise exceptions, returns None."""
        from seed_service import _generate_single_guide_image
        mock_api.side_effect = RuntimeError("all fail")
        result = _generate_single_guide_image("Guide", [{"step_title": "S1", "description": "D1"}], "key", {})
        assert result is None


class TestExtractImageFromResponse:
    """Tests for _extract_image_from_response (lines 372-374)"""

    def test_extract_success(self):
        """Test successful image extraction."""
        from seed_service import _extract_image_from_response
        mock_resp = Mock()
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"inlineData": {"data": "b64data"}}]}}]
        }
        result = _extract_image_from_response(mock_resp)
        assert result == "b64data"

    def test_extract_no_inline_data(self):
        """Test extraction when no inlineData."""
        from seed_service import _extract_image_from_response
        mock_resp = Mock()
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "no image"}]}}]
        }
        result = _extract_image_from_response(mock_resp)
        assert result is None

    def test_extract_parse_error(self):
        """Test extraction with malformed response."""
        from seed_service import _extract_image_from_response
        mock_resp = Mock()
        mock_resp.json.return_value = {}
        result = _extract_image_from_response(mock_resp)
        assert result is None


class TestAnalyzeSeedGuidePerStepMode:
    """Tests for per-step image mode in analyze_seed_and_generate_guide (lines 537-577)"""


    @pytest.mark.asyncio
    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-api-key"})
    @patch('seed_service._generate_images_parallel')
    @patch('seed_service.requests.post')
    async def test_per_step_mode(self, mock_post, mock_parallel):
        """Test per-step image generation mode."""
        from seed_service import analyze_seed_and_generate_guide

        analysis_resp = Mock()
        analysis_resp.status_code = 200
        analysis_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "title": "Tomato Guide",
                            "description": "How to grow tomatoes",
                            "steps": [
                                {"step_title": "Plant", "description": "Plant seeds", "image_prompt": "planting"}
                            ]
                        })
                    }]
                }
            }]
        }
        mock_post.return_value = analysis_resp

        mock_parallel.return_value = [
            {"title": "Plant", "description": "Plant seeds", "image_base64": "step_img"}
        ]

        title, desc, steps = await analyze_seed_and_generate_guide(b"img", guide_image_mode="per_step")
        assert title == "Tomato Guide"
        assert steps[0]["image_base64"] == "step_img"

    # 削除: test_per_step_flash_model（image_model引数は廃止）


class TestAnalyzeSeedGuideSingleModeNoImage:
    """Tests for single mode when image generation fails."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-api-key"})
    @patch('seed_service._generate_single_guide_image', return_value=None)
    @patch('seed_service.requests.post')
    async def test_single_mode_no_image(self, mock_post, mock_gen):
        """Test single mode when guide image fails."""
        from seed_service import analyze_seed_and_generate_guide

        analysis_resp = Mock()
        analysis_resp.status_code = 200
        analysis_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "title": "Guide",
                            "description": "Desc",
                            "steps": [
                                {"step_title": "S1", "description": "D1", "image_prompt": "P1"},
                                {"step_title": "S2", "description": "D2", "image_prompt": "P2"}
                            ]
                        })
                    }]
                }
            }]
        }
        mock_post.return_value = analysis_resp

        title, desc, steps = await analyze_seed_and_generate_guide(b"img")
        assert len(steps) == 2
        assert "image_base64" not in steps[0]  # No image when generation fails

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-api-key"})
    @patch('seed_service.requests.post')
    async def test_response_parse_error(self, mock_post):
        """Test JSON parse failure from analysis response."""
        from seed_service import analyze_seed_and_generate_guide

        analysis_resp = Mock()
        analysis_resp.status_code = 200
        analysis_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "not valid json"}]
                }
            }]
        }
        mock_post.return_value = analysis_resp

        with pytest.raises(RuntimeError, match="parse"):
            await analyze_seed_and_generate_guide(b"img")

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-api-key"})
    @patch('seed_service._generate_single_guide_image', return_value="b64img")
    @patch('seed_service.requests.post')
    async def test_response_as_list(self, mock_post, mock_gen):
        """Test when analysis response returns list instead of dict."""
        from seed_service import analyze_seed_and_generate_guide

        analysis_resp = Mock()
        analysis_resp.status_code = 200
        analysis_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps([
                            {"step_title": "S1", "title": "トマトの育て方：水やり", "description": "D1", "image_prompt": "P1"}
                        ])
                    }]
                }
            }]
        }
        mock_post.return_value = analysis_resp

        title, desc, steps = await analyze_seed_and_generate_guide(b"img")
        assert len(steps) == 1

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-api-key"})
    @patch('seed_service._generate_single_guide_image', return_value="b64img")
    @patch('seed_service.requests.post')
    async def test_response_with_markdown(self, mock_post, mock_gen):
        """Test analysis response wrapped in markdown code blocks."""
        from seed_service import analyze_seed_and_generate_guide

        analysis_resp = Mock()
        analysis_resp.status_code = 200
        analysis_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '```json\n{"title": "Guide", "description": "D", "steps": [{"step_title": "S1", "description": "D1", "image_prompt": "P1"}]}\n```'
                    }]
                }
            }]
        }
        mock_post.return_value = analysis_resp

        title, desc, steps = await analyze_seed_and_generate_guide(b"img")
        assert title == "Guide"


# ---------------------------------------------------------------------------
# Additional coverage: uncovered lines 187-188, 213-214, 225-227, 297, 326, 466-467
# ---------------------------------------------------------------------------

class TestProcessStepAdditional:
    """Cover remaining uncovered lines in process_step / generate_step_image_with_fallback."""

    @patch('seed_service.random.uniform', return_value=0.5)
    @patch('seed_service.time.sleep')
    @patch('seed_service.call_api_with_backoff')
    def test_pro_non200_returns_placeholder(self, mock_api, mock_sleep, mock_rand):
        """Pro model returns non-200 -> placeholder."""
        from seed_service import process_step, DEFAULT_PLACEHOLDER_B64
        fail_resp = Mock()
        fail_resp.status_code = 429

        mock_api.return_value = fail_resp
        step = {"step_title": "Prune", "description": "Prune plant", "image_prompt": "pruning"}
        result = process_step((step, "http://pro", {}))
        assert result["image_base64"] == DEFAULT_PLACEHOLDER_B64
        assert "error" in result

    @patch('seed_service.random.uniform', return_value=0.5)
    @patch('seed_service.time.sleep')
    @patch('seed_service.call_api_with_backoff')
    def test_no_inline_data_in_parsed_response(self, mock_api, mock_sleep, mock_rand):
        """Cover L213-214: response is 200 but no inlineData in parts -> warning + placeholder."""
        from seed_service import process_step, DEFAULT_PLACEHOLDER_B64
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "no image here"}]}}]
        }
        mock_api.return_value = mock_resp
        step = {"step_title": "Sun", "description": "Sunlight", "image_prompt": "sun"}
        result = process_step((step, "http://pro", {}))
        assert result["image_base64"] == DEFAULT_PLACEHOLDER_B64
        assert "error" in result


class TestGenerateSingleGuideImageAdditional:
    """Cover L297 and L326 in _generate_single_guide_image."""

    @patch('seed_service.call_api_with_backoff')
    def test_pro_non200_returns_none(self, mock_api):
        """Pro model returns non-200 status -> None."""
        from seed_service import _generate_single_guide_image
        fail_resp = Mock()
        fail_resp.status_code = 429
        mock_api.return_value = fail_resp
        result = _generate_single_guide_image("Guide", [{"step_title": "S1", "description": "D1"}], "key", {})
        assert result is None

    @patch('seed_service.call_api_with_backoff')
    def test_pro_exception_returns_none(self, mock_api):
        """Pro model raises exception -> None."""
        from seed_service import _generate_single_guide_image
        mock_api.side_effect = RuntimeError("pro error")
        result = _generate_single_guide_image("Guide", [{"step_title": "S1", "description": "D1"}], "key", {})
        assert result is None


class TestAnalyzeSeedGuideFailure:
    """Cover L466-467: Gemini analysis response non-200."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "fake-key"})
    @patch('seed_service.call_api_with_backoff')
    async def test_analysis_non200_raises(self, mock_api):
        """Cover L466-467: status_code != 200 raises RuntimeError."""
        from seed_service import analyze_seed_and_generate_guide
        fail_resp = Mock()
        fail_resp.status_code = 400
        fail_resp.text = "Bad request error message"

        mock_api.return_value = fail_resp

        with pytest.raises(RuntimeError, match="Gemini 3 Pro Analysis failed"):
            await analyze_seed_and_generate_guide(b"imgdata")
