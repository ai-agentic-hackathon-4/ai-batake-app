"""Tests for image_service.py - picture diary generation"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import base64

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGetStorageClient:
    """Tests for get_storage_client function"""
    
    @patch('image_service.storage.Client')
    def test_get_storage_client_returns_client(self, mock_client_class):
        """Test that get_storage_client returns a storage client"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        from image_service import get_storage_client
        
        result = get_storage_client()
        
        assert result is not None
        mock_client_class.assert_called_once()


class TestGeneratePictureDiary:
    """Tests for generate_picture_diary function"""
    
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': ''})
    def test_generate_picture_diary_no_api_key(self):
        """Test diary generation without API key"""
        from image_service import generate_picture_diary
        
        result = generate_picture_diary("2025-01-01", "Test summary")
        
        assert result is None
    
    @patch('image_service.get_storage_client')
    @patch('image_service.requests.post')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_generate_picture_diary_character_image_not_found(self, mock_post, mock_get_client):
        """Test diary generation when character image is not found"""
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        mock_bucket.blob.return_value = mock_blob
        
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client
        
        from image_service import generate_picture_diary
        
        result = generate_picture_diary("2025-01-01", "Test summary")
        
        assert result is None
    
    @patch('image_service.get_storage_client')
    @patch('image_service.requests.post')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_generate_picture_diary_api_error(self, mock_post, mock_get_client):
        """Test diary generation with API error"""
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"fake image"
        mock_bucket.blob.return_value = mock_blob
        
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_post.return_value = mock_response
        
        from image_service import generate_picture_diary
        
        result = generate_picture_diary("2025-01-01", "Test summary")
        
        assert result is None
    
    @patch('image_service.get_storage_client')
    @patch('image_service.requests.post')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_generate_picture_diary_success(self, mock_post, mock_get_client):
        """Test successful diary generation"""
        # Mock storage client
        mock_bucket = Mock()
        mock_character_blob = Mock()
        mock_character_blob.exists.return_value = True
        mock_character_blob.download_as_bytes.return_value = b"fake character image"
        
        mock_output_blob = Mock()
        
        def mock_blob(path):
            if "character_image" in path:
                return mock_character_blob
            return mock_output_blob
        
        mock_bucket.blob.side_effect = mock_blob
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client
        
        # Mock API response
        generated_image_b64 = base64.b64encode(b"generated image").decode()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"inlineData": {"data": generated_image_b64}}]
                }
            }]
        }
        mock_post.return_value = mock_response
        
        from image_service import generate_picture_diary
        
        result = generate_picture_diary("2025-01-01", "Test summary")
        
        assert result is not None
        assert "gs://" in result
        mock_output_blob.upload_from_string.assert_called_once()
    
    @patch('image_service.get_storage_client')
    @patch('image_service.requests.post')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_generate_picture_diary_no_image_in_response(self, mock_post, mock_get_client):
        """Test diary generation when API returns no image"""
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"fake image"
        mock_bucket.blob.return_value = mock_blob
        
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client
        
        # API response without inlineData
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "No image generated"}]
                }
            }]
        }
        mock_post.return_value = mock_response
        
        from image_service import generate_picture_diary
        
        result = generate_picture_diary("2025-01-01", "Test summary")
        
        assert result is None
