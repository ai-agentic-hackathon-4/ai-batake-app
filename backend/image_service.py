import os
import io
import base64
import requests
import json
import logging
from datetime import datetime, timedelta
import random
import time
from google.cloud import storage

# Setup logger
try:
    from .logger import info, debug, error, warning
except ImportError:
    from logger import info, debug, error, warning

# Constants
BUCKET_NAME = "ai-agentic-hackathon-4-bk"
CHARACTER_IMAGE_PATH = "character_image/image.png"
DIARY_IMAGES_PATH = "diaries/"
PROJECT_ID = "ai-agentic-hackathon-4"

def get_storage_client():
    return storage.Client()

# Helper for Exponential Backoff (Sync) - Duplicated from seed_service.py
def call_api_with_backoff(
    url,
    payload,
    headers,
    max_retries=5,
    max_elapsed_seconds=30,
    base_delay=1.0,
    max_delay=6.0,
):
    start_time = time.time()

    for attempt in range(max_retries):
        elapsed = time.time() - start_time
        if elapsed >= max_elapsed_seconds:
            error(f"Retry budget exceeded ({max_elapsed_seconds}s).")
            raise RuntimeError("Retry budget exceeded")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                return response
            if response.status_code in (429,) or response.status_code >= 500:
                # Honor Retry-After when present
                retry_after = response.headers.get("Retry-After")
                if retry_after is not None:
                    try:
                        delay = min(float(retry_after), max_delay)
                    except ValueError:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                else:
                    delay = min(base_delay * (2 ** attempt), max_delay)

                # Add small jitter
                delay += random.uniform(0, 0.5)
                warning(
                    f"API {response.status_code}. Retrying in {delay:.2f}s... "
                    f"(Attempt {attempt+1}/{max_retries})"
                )
                time.sleep(delay)
                continue

            # Other errors (400, 403, etc) - do not retry
            return response
        except requests.exceptions.RequestException as e:
            # Network error - retry
            delay = min(base_delay * (2 ** attempt), max_delay) + random.uniform(0, 0.5)
            warning(
                f"Network Error: {e}. Retrying in {delay:.2f}s... "
                f"(Attempt {attempt+1}/{max_retries})"
            )
            time.sleep(delay)

    error(f"Max retries ({max_retries}) exceeded.")
    raise RuntimeError(f"Max retries ({max_retries}) exceeded.")

def generate_picture_diary(date_str: str, summary: str):
    """
    Generates a picture diary image using NanoBanana-pro (gemini-3-pro-image-preview).
    """
    try:
        info(f"Starting picture diary generation for {date_str} using NanoBanana-pro...")
        
        # 1. Configuration & Auth
        api_key = os.environ.get("SEED_GUIDE_GEMINI_KEY")
        if not api_key:
            error("SEED_GUIDE_GEMINI_KEY not found in environment variables.")
            return None

        # 2. Download Reference image from GCS
        storage_client = get_storage_client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(CHARACTER_IMAGE_PATH)
        
        if not blob.exists():
            error(f"Character image not found: gs://{BUCKET_NAME}/{CHARACTER_IMAGE_PATH}")
            return None
            
        image_bytes = blob.download_as_bytes()
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        # 3. Call NanoBanana-pro (gemini-3-pro-image-preview)
        # Endpoint structure from seed_service.py
        # 3. Call NanoBanana-pro (gemini-3-pro-image-preview) with Fallback
        # Endpoint structure from seed_service.py
        primary_model_id = "gemini-3-pro-image-preview"
        fallback_model_id = "gemini-2.5-flash-image"
        
        primary_url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{primary_model_id}:generateContent?key={api_key}"
        fallback_url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{fallback_model_id}:generateContent?key={api_key}"
        
        # Prompt based on Seed Service and User requirement
        prompt_text = f"NanoBanana-pro. Please generate a picture diary style illustration for the date {date_str}. Based on this character image, create an illustration that depicts the following event: {summary}. Maintain the character's appearance. Soft digital illustration style."

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt_text},
                        {"inlineData": {"mimeType": "image/png", "data": image_b64}}
                    ]
                }
            ],
            "generationConfig": {}
        }

        headers = {"Content-Type": "application/json"}
        
        info(f"Requesting NanoBanana-pro image generation (Primary: {primary_model_id})...")
        
        response = None
        primary_failed = False

        try:
            response = call_api_with_backoff(
                primary_url,
                payload,
                headers,
                max_retries=6,
                max_elapsed_seconds=90,
                base_delay=1.5,
                max_delay=8.0
            )
            
            if response.status_code != 200:
                warning(f"Primary model failed with status: {response.status_code}")
                primary_failed = True
                
        except Exception as e:
            warning(f"Primary model execution failed: {e}")
            primary_failed = True

        if primary_failed:
            info(f"Retrying with fallback model: {fallback_model_id}...")
            try:
                response = call_api_with_backoff(
                    fallback_url,
                    payload,
                    headers,
                    max_retries=4,
                    max_elapsed_seconds=60,
                    base_delay=1.5,
                    max_delay=8.0
                )
            except Exception as e:
                error(f"Fallback model execution failed: {e}")
                return None
                
        if response is None or response.status_code != 200:
            status = response.status_code if response else "Unknown"
            text = response.text if response else "No response"
            error(f"Image generation failed after fallback: {status} - {text}")
            return None

        resp_json = response.json()
        
        # Parse inlineData (Image Output)
        try:
            parts = resp_json['candidates'][0]['content']['parts']
            generated_b64 = None
            for part in parts:
                if 'inlineData' in part:
                    generated_b64 = part['inlineData']['data']
                    break
            
            if not generated_b64:
                error("No image data returned from NanoBanana-pro.")
                return None
                
            generated_bytes = base64.b64decode(generated_b64)
            
        except (KeyError, IndexError) as e:
            error(f"Failed to parse NanoBanana-pro response: {e}")
            return None

        # 4. Save to GCS
        output_filename = f"{DIARY_IMAGES_PATH}{date_str}.png"
        output_blob = bucket.blob(output_filename)
        output_blob.upload_from_string(generated_bytes, content_type="image/png")
        
        info(f"Generated image saved to gs://{BUCKET_NAME}/{output_filename}")

        # Return the GCS path to be stored in Firestore
        return f"gs://{BUCKET_NAME}/{output_filename}"

    except Exception as e:
        error(f"Error in picture diary generation: {e}")
        return None
