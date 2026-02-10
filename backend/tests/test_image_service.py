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
    
    @patch('db.db', None)
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
    
    @patch('db.db', None)
    @patch('image_service.call_api_with_backoff')
    @patch('image_service.get_storage_client')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_generate_picture_diary_api_error(self, mock_get_client, mock_api_call):
        """Test diary generation with API error - all attempts fail, placeholder saved"""
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"fake image"
        
        mock_output_blob = Mock()
        
        def mock_blob_fn(path):
            if "diaries/" in path:
                return mock_output_blob
            return mock_blob
        
        mock_bucket.blob.side_effect = mock_blob_fn
        
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client
        
        mock_api_call.side_effect = RuntimeError("Max retries exceeded")
        
        from image_service import generate_picture_diary
        
        result = generate_picture_diary("2025-01-01", "Test summary")
        
        assert result is not None
        assert "diaries/2025-01-01.png" in result
        mock_output_blob.upload_from_string.assert_called_once()
    
    @patch('db.db', None)
    @patch('image_service.call_api_with_backoff')
    @patch('image_service.get_storage_client')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_generate_picture_diary_success(self, mock_get_client, mock_api_call):
        """Test successful diary generation"""
        mock_bucket = Mock()
        mock_character_blob = Mock()
        mock_character_blob.exists.return_value = True
        mock_character_blob.download_as_bytes.return_value = b"fake character image"
        
        mock_output_blob = Mock()
        
        def mock_blob(path):
            if "diaries/" in path:
                return mock_output_blob
            return mock_character_blob
        
        mock_bucket.blob.side_effect = mock_blob
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client
        
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
        mock_api_call.return_value = mock_response
        
        from image_service import generate_picture_diary
        
        result = generate_picture_diary("2025-01-01", "Test summary")
        
        assert result is not None
        assert "gs://" in result
        mock_output_blob.upload_from_string.assert_called_once()
    
    @patch('db.db', None)
    @patch('image_service.call_api_with_backoff')
    @patch('image_service.get_storage_client')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_generate_picture_diary_no_image_in_response(self, mock_get_client, mock_api_call):
        """Test diary generation when API returns no image - placeholder saved"""
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"fake image"
        
        mock_output_blob = Mock()
        
        def mock_blob_fn(path):
            if "diaries/" in path:
                return mock_output_blob
            return mock_blob
        
        mock_bucket.blob.side_effect = mock_blob_fn
        
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "No image generated"}]
                }
            }]
        }
        mock_api_call.return_value = mock_response
        
        from image_service import generate_picture_diary
        
        result = generate_picture_diary("2025-01-01", "Test summary")
        
        assert result is not None
        assert "diaries/2025-01-01.png" in result
        mock_output_blob.upload_from_string.assert_called_once()

    @patch('db.db', None)
    @patch('image_service.call_api_with_backoff')
    @patch('image_service.get_storage_client')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_generate_picture_diary_fallback_success(self, mock_get_client, mock_api_call):
        """Test diary generation with primary failing, fallback succeeding"""
        mock_bucket = Mock()
        mock_character_blob = Mock()
        mock_character_blob.exists.return_value = True
        mock_character_blob.download_as_bytes.return_value = b"fake image"
        
        mock_output_blob = Mock()
        
        def mock_blob_side_effect(path):
            if "diaries/" in path:
                return mock_output_blob
            return mock_character_blob
            
        mock_bucket.blob.side_effect = mock_blob_side_effect
        
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client
        
        generated_image_b64 = base64.b64encode(b"generated image").decode()
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"inlineData": {"data": generated_image_b64}}]
                }
            }]
        }
        
        mock_api_call.side_effect = [
            RuntimeError("Primary failed"),
            mock_response_success
        ]
        
        from image_service import generate_picture_diary
        
        result = generate_picture_diary("2025-01-01", "Test summary")
        
        assert result is not None
        assert "gs://" in result
        mock_output_blob.upload_from_string.assert_called_once()

    @patch('db.db', None)
    @patch('image_service.call_api_with_backoff')
    @patch('image_service.get_storage_client')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_generate_picture_diary_fallback_all_fail(self, mock_get_client, mock_api_call):
        """Test diary generation when all attempts fail - placeholder saved"""
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"fake image"
        
        mock_output_blob = Mock()
        
        def mock_blob_fn(path):
            if "diaries/" in path:
                return mock_output_blob
            return mock_blob
        
        mock_bucket.blob.side_effect = mock_blob_fn
        
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client
        
        mock_api_call.side_effect = RuntimeError("All retries failed")
        
        from image_service import generate_picture_diary
        
        result = generate_picture_diary("2025-01-01", "Test summary")
        
        assert result is not None
        assert "diaries/2025-01-01.png" in result
        mock_output_blob.upload_from_string.assert_called_once()


class TestGeneratePictureDiaryWithCharacter:
    """Tests for generate_picture_diary with selected character from Firestore"""
    
    @patch('image_service.call_api_with_backoff')
    @patch('image_service.get_storage_client')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_uses_selected_character_image(self, mock_get_client, mock_api_call):
        """Test that selected character image from Firestore is used"""
        mock_char_doc = Mock()
        mock_char_doc.exists = True
        mock_char_doc.to_dict.return_value = {
            "name": "test-char",
            "image_uri": "https://storage.googleapis.com/ai-agentic-hackathon-4-bk/characters/test-char.png",
            "personality": "friendly"
        }
        
        mock_firestore_db = Mock()
        mock_firestore_db.collection.return_value.document.return_value.get.return_value = mock_char_doc
        
        mock_bucket = Mock()
        mock_character_blob = Mock()
        mock_character_blob.exists.return_value = True
        mock_character_blob.download_as_bytes.return_value = b"character image bytes"
        
        mock_output_blob = Mock()
        
        blob_paths_called = []
        def mock_blob_fn(path):
            blob_paths_called.append(path)
            if "diaries/" in path:
                return mock_output_blob
            return mock_character_blob
        
        mock_bucket.blob.side_effect = mock_blob_fn
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client
        
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
        mock_api_call.return_value = mock_response
        
        with patch('db.db', mock_firestore_db):
            from image_service import generate_picture_diary
            result = generate_picture_diary("2025-01-01", "Test summary")
        
        assert result is not None
        assert "characters/test-char.png" in blob_paths_called
    
    @patch('image_service.call_api_with_backoff')
    @patch('image_service.get_storage_client')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_falls_back_to_default_when_no_character(self, mock_get_client, mock_api_call):
        """Test fallback to default character when no character selected"""
        mock_char_doc = Mock()
        mock_char_doc.exists = False
        
        mock_firestore_db = Mock()
        mock_firestore_db.collection.return_value.document.return_value.get.return_value = mock_char_doc
        
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"default image bytes"
        
        mock_output_blob = Mock()
        
        blob_paths_called = []
        def mock_blob_fn(path):
            blob_paths_called.append(path)
            if "diaries/" in path:
                return mock_output_blob
            return mock_blob
        
        mock_bucket.blob.side_effect = mock_blob_fn
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client
        
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
        mock_api_call.return_value = mock_response
        
        with patch('db.db', mock_firestore_db):
            from image_service import generate_picture_diary
            result = generate_picture_diary("2025-01-01", "Test summary")
        
        assert result is not None
        assert "character_image/image.png" in blob_paths_called
