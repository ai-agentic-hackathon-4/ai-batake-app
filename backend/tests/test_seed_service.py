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
    @patch('seed_service.requests.post')
    async def test_analyze_seed_api_failure(self, mock_post):
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
