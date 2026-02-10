"""Tests for character_service.py - character generation via Gemini API"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAnalyzeSeedAndGenerateCharacter:
    """Tests for analyze_seed_and_generate_character"""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch('character_service.requests.post')
    @patch('time.sleep')
    @patch('random.uniform', return_value=0.5)
    async def test_success(self, mock_rand, mock_sleep, mock_post):
        """Test successful character analysis and image generation."""
        from character_service import analyze_seed_and_generate_character

        # First call: text analysis
        text_resp = Mock()
        text_resp.status_code = 200
        text_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "name": "トマト",
                            "character_name": "トマちゃん",
                            "personality": "明るくて元気",
                            "image_prompt": "A cute tomato character"
                        })
                    }]
                }
            }]
        }

        # Second call: image generation
        img_resp = Mock()
        img_resp.status_code = 200
        img_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "inlineData": {"data": "base64imagedata"}
                    }]
                }
            }]
        }

        mock_post.side_effect = [text_resp, img_resp]

        result = await analyze_seed_and_generate_character(b"fake_image")

        assert result["name"] == "トマト"
        assert result["character_name"] == "トマちゃん"
        assert result["image_base64"] == "base64imagedata"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {}, clear=True)
    async def test_missing_api_key(self):
        """Test RuntimeError when API key is missing."""
        from character_service import analyze_seed_and_generate_character

        with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
            await analyze_seed_and_generate_character(b"fake")

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"SEED_GUIDE_GEMINI_KEY": "test-key2"})
    @patch('character_service.requests.post')
    @patch('time.sleep')
    @patch('random.uniform', return_value=0.1)
    async def test_uses_seed_guide_gemini_key(self, mock_rand, mock_sleep, mock_post):
        """Test that SEED_GUIDE_GEMINI_KEY is used as fallback."""
        from character_service import analyze_seed_and_generate_character

        text_resp = Mock()
        text_resp.status_code = 200
        text_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "name": "Cucumber",
                            "character_name": "Cucuちゃん",
                            "personality": "cool",
                            "image_prompt": "A cute cucumber"
                        })
                    }]
                }
            }]
        }
        img_resp = Mock()
        img_resp.status_code = 200
        img_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"inlineData": {"data": "imgdata"}}]
                }
            }]
        }
        mock_post.side_effect = [text_resp, img_resp]

        result = await analyze_seed_and_generate_character(b"img")
        assert result["character_name"] == "Cucuちゃん"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch('character_service.requests.post')
    @patch('time.sleep')
    @patch('random.uniform', return_value=0.1)
    async def test_analysis_api_failure(self, mock_rand, mock_sleep, mock_post):
        """Test when text analysis API returns non-200."""
        from character_service import analyze_seed_and_generate_character

        fail_resp = Mock()
        fail_resp.status_code = 500
        fail_resp.text = "Server Error"
        mock_post.return_value = fail_resp

        with pytest.raises(RuntimeError, match="retries"):
            await analyze_seed_and_generate_character(b"img")

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch('character_service.requests.post')
    @patch('time.sleep')
    @patch('random.uniform', return_value=0.1)
    async def test_image_generation_failure(self, mock_rand, mock_sleep, mock_post):
        """Test when image generation API returns non-200."""
        from character_service import analyze_seed_and_generate_character

        text_resp = Mock()
        text_resp.status_code = 200
        text_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "name": "Tomato",
                            "character_name": "T",
                            "personality": "p",
                            "image_prompt": "prompt"
                        })
                    }]
                }
            }]
        }
        img_fail = Mock()
        img_fail.status_code = 500
        img_fail.text = "fail"

        # 100 retries + budget exceeded
        mock_post.side_effect = [text_resp] + [img_fail] * 101

        with pytest.raises(RuntimeError, match="retry budget exceeded|retries"):
            await analyze_seed_and_generate_character(b"img")

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch('character_service.requests.post')
    @patch('time.sleep')
    @patch('random.uniform', return_value=0.1)
    async def test_no_image_data_in_response(self, mock_rand, mock_sleep, mock_post):
        """Test when image response has no inlineData."""
        from character_service import analyze_seed_and_generate_character

        text_resp = Mock()
        text_resp.status_code = 200
        text_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "name": "T",
                            "character_name": "TC",
                            "personality": "p",
                            "image_prompt": "pr"
                        })
                    }]
                }
            }]
        }
        img_resp = Mock()
        img_resp.status_code = 200
        img_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "no image here"}]
                }
            }]
        }
        mock_post.side_effect = [text_resp, img_resp]

        with pytest.raises(RuntimeError, match="No image data"):
            await analyze_seed_and_generate_character(b"img")

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch('character_service.requests.post')
    @patch('time.sleep')
    @patch('random.uniform', return_value=0.1)
    async def test_call_api_429_retries(self, mock_rand, mock_sleep, mock_post):
        """Test that 429 responses trigger retries."""
        from character_service import analyze_seed_and_generate_character

        rate_limit_resp = Mock()
        rate_limit_resp.status_code = 429

        success_resp = Mock()
        success_resp.status_code = 200
        success_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "name": "T",
                            "character_name": "TC",
                            "personality": "p",
                            "image_prompt": "pr"
                        })
                    }]
                }
            }]
        }
        img_resp = Mock()
        img_resp.status_code = 200
        img_resp.json.return_value = {
            "candidates": [{
                "content": {"parts": [{"inlineData": {"data": "img"}}]}
            }]
        }

        mock_post.side_effect = [rate_limit_resp, success_resp, img_resp]

        result = await analyze_seed_and_generate_character(b"img")
        assert result["image_base64"] == "img"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch('character_service.requests.post')
    @patch('time.sleep')
    @patch('random.uniform', return_value=0.1)
    async def test_call_api_request_exception_retry(self, mock_rand, mock_sleep, mock_post):
        """Test that RequestException triggers retry."""
        import requests as req_lib
        from character_service import analyze_seed_and_generate_character

        success_resp = Mock()
        success_resp.status_code = 200
        success_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "name": "T",
                            "character_name": "TC",
                            "personality": "p",
                            "image_prompt": "pr"
                        })
                    }]
                }
            }]
        }
        img_resp = Mock()
        img_resp.status_code = 200
        img_resp.json.return_value = {
            "candidates": [{
                "content": {"parts": [{"inlineData": {"data": "img"}}]}
            }]
        }

        mock_post.side_effect = [
            req_lib.exceptions.ConnectionError("conn err"),
            success_resp,
            img_resp,
        ]

        result = await analyze_seed_and_generate_character(b"img")
        assert result["image_base64"] == "img"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch('character_service.requests.post')
    @patch('time.sleep')
    @patch('random.uniform', return_value=0.1)
    async def test_call_api_non_retryable_error(self, mock_rand, mock_sleep, mock_post):
        """Test that 400 error is returned without retry."""
        from character_service import analyze_seed_and_generate_character

        bad_resp = Mock()
        bad_resp.status_code = 400
        bad_resp.text = "Bad Request"
        mock_post.return_value = bad_resp

        with pytest.raises(RuntimeError, match="Analysis failed"):
            await analyze_seed_and_generate_character(b"img")


class TestImageGenerationNonRetryableError:
    """Cover L117: image generation returns non-retryable non-200 status."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch('backend.character_service.requests.post')
    @patch('time.sleep')
    @patch('random.uniform', return_value=0.1)
    async def test_image_api_400_error(self, mock_rand, mock_sleep, mock_post):
        """Cover L117: image API returns 400 -> RuntimeError('Image generation failed')."""
        from backend.character_service import analyze_seed_and_generate_character

        # Analysis succeeds
        text_resp = Mock()
        text_resp.status_code = 200
        text_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "name": "Tomato",
                            "character_name": "T",
                            "personality": "p",
                            "image_prompt": "prompt"
                        })
                    }]
                }
            }]
        }

        # Image generation returns 400 (non-retryable)
        img_bad = Mock()
        img_bad.status_code = 400
        img_bad.text = "Bad image request"

        mock_post.side_effect = [text_resp, img_bad]

        with pytest.raises(RuntimeError, match="Image generation failed"):
            await analyze_seed_and_generate_character(b"img")
