"""Tests for image_service.py - picture diary generation"""
import pytest
import time
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
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key', 'GEMINI_API_KEY': 'fallback-key'})
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
        
        # Verify calls were made to both endpoints
        assert mock_api_call.call_count == 2
        
        # First call should be to Vertex AI with test-key
        args1, _ = mock_api_call.call_args_list[0]
        assert "aiplatform.googleapis.com" in args1[0]
        assert "key=test-key" in args1[0]
        
        # Second call should be to Gemini API with fallback-key
        args2, _ = mock_api_call.call_args_list[1]
        assert "generativelanguage.googleapis.com" in args2[0]
        assert "key=fallback-key" in args2[0]

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


# ---------------------------------------------------------------------------
# Additional tests for 100% coverage
# ---------------------------------------------------------------------------

class TestCallApiWithBackoff:
    """Tests for call_api_with_backoff (lines 40-85)"""

    @patch('image_service.requests.post')
    def test_success_first_attempt(self, mock_post):
        from image_service import call_api_with_backoff
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp
        result = call_api_with_backoff("http://test", {}, {})
        assert result.status_code == 200

    @patch('image_service.time.sleep')
    @patch('image_service.time.time', return_value=0)
    @patch('image_service.random.uniform', return_value=0)
    @patch('image_service.requests.post')
    def test_retry_on_429_with_retry_after(self, mock_post, mock_rand, mock_time, mock_sleep):
        from image_service import call_api_with_backoff
        resp_429 = Mock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "2"}
        resp_200 = Mock()
        resp_200.status_code = 200
        mock_post.side_effect = [resp_429, resp_200]
        result = call_api_with_backoff("http://test", {}, {})
        assert result.status_code == 200

    @patch('image_service.time.sleep')
    @patch('image_service.time.time', return_value=0)
    @patch('image_service.random.uniform', return_value=0)
    @patch('image_service.requests.post')
    def test_retry_on_429_invalid_retry_after(self, mock_post, mock_rand, mock_time, mock_sleep):
        from image_service import call_api_with_backoff
        resp_429 = Mock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "invalid"}
        resp_200 = Mock()
        resp_200.status_code = 200
        mock_post.side_effect = [resp_429, resp_200]
        result = call_api_with_backoff("http://test", {}, {})
        assert result.status_code == 200

    @patch('image_service.time.sleep')
    @patch('image_service.time.time', return_value=0)
    @patch('image_service.random.uniform', return_value=0)
    @patch('image_service.requests.post')
    def test_retry_on_500(self, mock_post, mock_rand, mock_time, mock_sleep):
        from image_service import call_api_with_backoff
        resp_500 = Mock()
        resp_500.status_code = 500
        resp_500.headers = {}
        resp_200 = Mock()
        resp_200.status_code = 200
        mock_post.side_effect = [resp_500, resp_200]
        result = call_api_with_backoff("http://test", {}, {})
        assert result.status_code == 200

    @patch('image_service.requests.post')
    def test_non_retryable_error(self, mock_post):
        from image_service import call_api_with_backoff
        resp_400 = Mock()
        resp_400.status_code = 400
        mock_post.return_value = resp_400
        result = call_api_with_backoff("http://test", {}, {})
        assert result.status_code == 400

    @patch('image_service.time.sleep')
    @patch('image_service.time.time', return_value=0)
    @patch('image_service.random.uniform', return_value=0)
    @patch('image_service.requests.post')
    def test_network_error_retry(self, mock_post, mock_rand, mock_time, mock_sleep):
        import requests as req
        from image_service import call_api_with_backoff
        resp_200 = Mock()
        resp_200.status_code = 200
        mock_post.side_effect = [req.exceptions.ConnectionError("net err"), resp_200]
        result = call_api_with_backoff("http://test", {}, {})
        assert result.status_code == 200

    @patch('image_service.time.sleep')
    @patch('image_service.time.time', return_value=0)
    @patch('image_service.random.uniform', return_value=0)
    @patch('image_service.requests.post')
    def test_max_retries_exceeded(self, mock_post, mock_rand, mock_time, mock_sleep):
        import requests as req
        from image_service import call_api_with_backoff
        mock_post.side_effect = req.exceptions.ConnectionError("always fail")
        with pytest.raises(RuntimeError, match="Max retries"):
            call_api_with_backoff("http://test", {}, {}, max_retries=2)

    @patch('image_service.requests.post')
    def test_retry_budget_exceeded(self, mock_post):
        from image_service import call_api_with_backoff
        # Patch time.time to return values that exceed the budget after first check
        original_time = time.time
        call_count = [0]
        def fake_time():
            call_count[0] += 1
            if call_count[0] <= 1:
                return 0  # start_time
            return 100  # elapsed exceeds budget
        with patch('image_service.time.time', side_effect=fake_time):
            with pytest.raises(RuntimeError, match="Retry budget exceeded"):
                call_api_with_backoff("http://test", {}, {}, max_elapsed_seconds=1)


class TestGeneratePictureDiaryCharacterResolution:
    """Tests for character image resolution branches (lines 123-147)"""

    @patch('image_service.call_api_with_backoff')
    @patch('image_service.get_storage_client')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_gs_prefix_image_uri(self, mock_get_client, mock_api_call):
        """Test gs:// prefix resolution for character image"""
        mock_char_doc = Mock()
        mock_char_doc.exists = True
        mock_char_doc.to_dict.return_value = {
            "image_uri": "gs://ai-agentic-hackathon-4-bk/characters/gs-char.png"
        }
        mock_firestore_db = Mock()
        mock_firestore_db.collection.return_value.document.return_value.get.return_value = mock_char_doc

        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"img"
        mock_output_blob = Mock()

        blob_paths = []
        def blob_fn(path):
            blob_paths.append(path)
            if "diaries/" in path:
                return mock_output_blob
            return mock_blob

        mock_bucket.blob.side_effect = blob_fn
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client

        gen_b64 = base64.b64encode(b"gen").decode()
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"candidates": [{"content": {"parts": [{"inlineData": {"data": gen_b64}}]}}]}
        mock_api_call.return_value = mock_resp

        with patch('db.db', mock_firestore_db):
            from image_service import generate_picture_diary
            result = generate_picture_diary("2025-01-01", "Test")

        assert result is not None
        assert "characters/gs-char.png" in blob_paths

    @patch('image_service.call_api_with_backoff')
    @patch('image_service.get_storage_client')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_unknown_image_uri_format(self, mock_get_client, mock_api_call):
        """Test unknown image_uri format falls back to default"""
        mock_char_doc = Mock()
        mock_char_doc.exists = True
        mock_char_doc.to_dict.return_value = {
            "image_uri": "http://unknown.example.com/img.png"
        }
        mock_firestore_db = Mock()
        mock_firestore_db.collection.return_value.document.return_value.get.return_value = mock_char_doc

        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"img"
        mock_output_blob = Mock()

        blob_paths = []
        def blob_fn(path):
            blob_paths.append(path)
            if "diaries/" in path:
                return mock_output_blob
            return mock_blob

        mock_bucket.blob.side_effect = blob_fn
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client

        gen_b64 = base64.b64encode(b"gen").decode()
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"candidates": [{"content": {"parts": [{"inlineData": {"data": gen_b64}}]}}]}
        mock_api_call.return_value = mock_resp

        with patch('db.db', mock_firestore_db):
            from image_service import generate_picture_diary
            result = generate_picture_diary("2025-01-01", "Test")

        assert result is not None
        assert "character_image/image.png" in blob_paths

    @patch('image_service.call_api_with_backoff')
    @patch('image_service.get_storage_client')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_no_image_uri_in_char_doc(self, mock_get_client, mock_api_call):
        """Test character doc with no image_uri"""
        mock_char_doc = Mock()
        mock_char_doc.exists = True
        mock_char_doc.to_dict.return_value = {"name": "test"}
        mock_firestore_db = Mock()
        mock_firestore_db.collection.return_value.document.return_value.get.return_value = mock_char_doc

        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"img"
        mock_output_blob = Mock()

        def blob_fn(path):
            if "diaries/" in path:
                return mock_output_blob
            return mock_blob

        mock_bucket.blob.side_effect = blob_fn
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client

        gen_b64 = base64.b64encode(b"gen").decode()
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"candidates": [{"content": {"parts": [{"inlineData": {"data": gen_b64}}]}}]}
        mock_api_call.return_value = mock_resp

        with patch('db.db', mock_firestore_db):
            from image_service import generate_picture_diary
            result = generate_picture_diary("2025-01-01", "Test")

        assert result is not None

    @patch('image_service.get_storage_client')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_firestore_exception_uses_default(self, mock_get_client):
        """Test Firestore exception falls back to default path"""
        mock_firestore_db = Mock()
        mock_firestore_db.collection.side_effect = Exception("Firestore error")

        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        mock_bucket.blob.return_value = mock_blob
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client

        with patch('db.db', mock_firestore_db):
            from image_service import generate_picture_diary
            result = generate_picture_diary("2025-01-01", "Test")

        assert result is None  # character image not found

    @patch('image_service.call_api_with_backoff')
    @patch('image_service.get_storage_client')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_character_blob_not_found_fallback_to_default(self, mock_get_client, mock_api_call):
        """Test character blob not found, fallback to default succeeds"""
        mock_char_doc = Mock()
        mock_char_doc.exists = True
        mock_char_doc.to_dict.return_value = {
            "image_uri": "gs://ai-agentic-hackathon-4-bk/characters/missing.png"
        }
        mock_firestore_db = Mock()
        mock_firestore_db.collection.return_value.document.return_value.get.return_value = mock_char_doc

        mock_bucket = Mock()
        call_count = [0]
        mock_output_blob = Mock()

        def blob_fn(path):
            if "diaries/" in path:
                return mock_output_blob
            b = Mock()
            if call_count[0] == 0:
                b.exists.return_value = False  # first blob (custom) not found
                call_count[0] += 1
            else:
                b.exists.return_value = True  # default blob exists
                b.download_as_bytes.return_value = b"default img"
            return b

        mock_bucket.blob.side_effect = blob_fn
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client

        gen_b64 = base64.b64encode(b"gen").decode()
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"candidates": [{"content": {"parts": [{"inlineData": {"data": gen_b64}}]}}]}
        mock_api_call.return_value = mock_resp

        with patch('db.db', mock_firestore_db):
            from image_service import generate_picture_diary
            result = generate_picture_diary("2025-01-01", "Test")

        assert result is not None

    @patch('image_service.call_api_with_backoff')
    @patch('image_service.get_storage_client')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_character_blob_not_found_default_also_missing(self, mock_get_client, mock_api_call):
        """Test character blob and default blob both missing"""
        mock_char_doc = Mock()
        mock_char_doc.exists = True
        mock_char_doc.to_dict.return_value = {
            "image_uri": "gs://ai-agentic-hackathon-4-bk/characters/missing.png"
        }
        mock_firestore_db = Mock()
        mock_firestore_db.collection.return_value.document.return_value.get.return_value = mock_char_doc

        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        mock_bucket.blob.return_value = mock_blob
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client

        with patch('db.db', mock_firestore_db):
            from image_service import generate_picture_diary
            result = generate_picture_diary("2025-01-01", "Test")

        assert result is None


class TestGeneratePictureDiaryPrimaryNon200:
    """Test primary model returning non-200 triggers fallback (lines 199-200)"""

    @patch('db.db', None)
    @patch('image_service.call_api_with_backoff')
    @patch('image_service.get_storage_client')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_primary_non_200_fallback_success(self, mock_get_client, mock_api_call):
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"img"
        mock_output_blob = Mock()
        def blob_fn(path):
            if "diaries/" in path:
                return mock_output_blob
            return mock_blob
        mock_bucket.blob.side_effect = blob_fn
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client

        gen_b64 = base64.b64encode(b"gen").decode()
        resp_fail = Mock()
        resp_fail.status_code = 400
        resp_success = Mock()
        resp_success.status_code = 200
        resp_success.json.return_value = {"candidates": [{"content": {"parts": [{"inlineData": {"data": gen_b64}}]}}]}
        mock_api_call.side_effect = [resp_fail, resp_success]

        from image_service import generate_picture_diary
        result = generate_picture_diary("2025-01-01", "Test")
        assert result is not None


class TestGeneratePictureDiaryResponseParsing:
    """Test response parsing edge cases (lines 264-266)"""

    @patch('db.db', None)
    @patch('image_service.call_api_with_backoff')
    @patch('image_service.get_storage_client')
    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_parse_error_uses_placeholder(self, mock_get_client, mock_api_call):
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"img"
        mock_output_blob = Mock()
        def blob_fn(path):
            if "diaries/" in path:
                return mock_output_blob
            return mock_blob
        mock_bucket.blob.side_effect = blob_fn
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_get_client.return_value = mock_client

        resp = Mock()
        resp.status_code = 200
        resp.json.return_value = {"candidates": []}  # IndexError when accessing [0]
        mock_api_call.return_value = resp

        from image_service import generate_picture_diary
        result = generate_picture_diary("2025-01-01", "Test")
        assert result is not None
        mock_output_blob.upload_from_string.assert_called_once()


class TestGeneratePictureDiaryOuterException:
    """Test outer exception handling (lines 278-280)"""

    @patch.dict('os.environ', {'SEED_GUIDE_GEMINI_KEY': 'test-key'})
    def test_storage_client_exception(self):
        """Test exception in get_storage_client"""
        with patch('db.db', None):
            with patch('image_service.get_storage_client', side_effect=Exception("GCS error")):
                from image_service import generate_picture_diary
                result = generate_picture_diary("2025-01-01", "Test")
                assert result is None
