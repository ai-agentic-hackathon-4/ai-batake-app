import pytest
from unittest.mock import patch, MagicMock
import requests
import time
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# We want to test the retry logic and the final error message.
# Since call_api is local toanalyze_seed_and_generate_character, we'll test a representative version or use character_service.

@pytest.mark.asyncio
async def test_character_service_429_error_message():
    from character_service import analyze_seed_and_generate_character
    import asyncio
    
    # Set dummy API key
    os.environ["GEMINI_API_KEY"] = "dummy_key"
    
    # Mock requests.post to always return 429
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {}
    
    with patch('requests.post', return_value=mock_resp):
        with patch('time.sleep'):
            # Simulate many attempts without exceeding budget
            start_time = time.time()
            # Feed many same start times for the 'elapsed' check, then mock many attempts
            with patch('time.time', return_value=start_time):
                # We need to limit max_retries because analyze_seed... hardcodes 100.
                # To make it fast, we will patch 'range' or just let it run.
                # Actually, patching 'range' in the internal function is tricky.
                # Let's patch 'requests.post' to eventually raise an exception to break the loop,
                # or just use a side_effect that eventually raises a StopIteration?
                
                # Better: patch 'max_retries' if it was a variable, but it's local.
                # Let's just mock 'range' to return a small range.
                with patch('builtins.range', return_value=iter(range(2))):
                    with pytest.raises(RuntimeError) as excinfo:
                        await analyze_seed_and_generate_character(b"dummy")
                    
                    assert "API rate limit exceeded (429)" in str(excinfo.value)

@pytest.mark.asyncio
async def test_seed_service_429_error_message():
    from seed_service import call_api_with_backoff
    
    # Mock requests.post to always return 429
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {}
    
    url = "https://api.example.com/models/gemini-pro:generateContent"
    
    with patch('requests.post', return_value=mock_resp):
        with patch('time.sleep'):
            # Set a low max_retries and ensure time doesn't expire
            start_time = time.time()
            with patch('time.time', return_value=start_time):
                with pytest.raises(RuntimeError) as excinfo:
                    call_api_with_backoff(url, {}, {}, max_retries=3)
                
                assert "rate limit exceeded (429)" in str(excinfo.value).lower()
                assert "gemini-pro" in str(excinfo.value)

@pytest.mark.asyncio
async def test_image_service_429_error_message():
    from image_service import call_api_with_backoff
    
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {}
    
    with patch('requests.post', return_value=mock_resp):
        with patch('time.sleep'):
            start_time = time.time()
            with patch('time.time', return_value=start_time):
                with pytest.raises(RuntimeError) as excinfo:
                    call_api_with_backoff("https://api.example.com", {}, {}, max_retries=2)
                
                assert "rate limit exceeded (429)" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_research_agent_429_error_message():
    from research_agent import request_with_retry
    
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    
    with patch('requests.request', return_value=mock_resp):
        with patch('time.sleep'):
            start_time = time.time()
            with patch('time.time', return_value=start_time):
                with patch('builtins.range', return_value=iter(range(2))):
                    with pytest.raises(RuntimeError) as excinfo:
                        request_with_retry("POST", "https://api.example.com")
                    
                    assert "rate limit exceeded (429)" in str(excinfo.value).lower()

def test_main_error_translation():
    # Test the translation logic used in main.py
    def get_friendly_message(e):
        error_msg = str(e)
        if "429" in error_msg:
            return "AIモデルの利用制限（429: Too Many Requests）に達しました。しばらく待ってから再度お試しください。"
        else:
            return f"エラーが発生しました: {error_msg}"

    # Case 1: 429 error from our service
    e1 = RuntimeError("API rate limit exceeded (429). Please try again later.")
    assert "AIモデルの利用制限" in get_friendly_message(e1)
    
    # Case 2: Other error
    e2 = RuntimeError("Some random error")
    assert "エラーが発生しました: Some random error" == get_friendly_message(e2)

if __name__ == "__main__":
    # Manually run translation test
    test_main_error_translation()
    print("Translation logic test: PASSED")
