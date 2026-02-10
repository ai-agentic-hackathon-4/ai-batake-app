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
DEFAULT_CHARACTER_IMAGE_PATH = "character_image/image.png"
DIARY_IMAGES_PATH = "diaries/"
PROJECT_ID = "ai-agentic-hackathon-4"

# Final hardcoded placeholder image (Base64 of a simple 1x1 green pixel as safe failover)
DEFAULT_PLACEHOLDER_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

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
        info(f"[LLM] 🎨 Starting picture diary generation for {date_str}...")
        
        # 1. Configuration & Auth
        api_key = os.environ.get("SEED_GUIDE_GEMINI_KEY")
        if not api_key:
            error("SEED_GUIDE_GEMINI_KEY not found in environment variables.")
            return None

        # 2. Download Reference image from GCS
        # Resolve character image path from Firestore (selected character)
        # Use the shared db client from db.py which has the correct project/database config
        character_image_path = DEFAULT_CHARACTER_IMAGE_PATH
        try:
            from .db import db as firestore_db
        except ImportError:
            from db import db as firestore_db
        try:
            if firestore_db is None:
                info("Firestore not available, using default character image.")
            else:
                char_doc = firestore_db.collection("growing_diaries").document("Character").get()
                if char_doc.exists:
                    char_data = char_doc.to_dict()
                    image_uri = char_data.get("image_uri", "")
                    if image_uri:
                        # Convert GCS URL or gs:// URI to blob path
                        gcs_https_prefix = f"https://storage.googleapis.com/{BUCKET_NAME}/"
                        gs_prefix = f"gs://{BUCKET_NAME}/"
                        if image_uri.startswith(gcs_https_prefix):
                            character_image_path = image_uri[len(gcs_https_prefix):]
                            info(f"Using selected character image: {character_image_path}")
                        elif image_uri.startswith(gs_prefix):
                            character_image_path = image_uri[len(gs_prefix):]
                            info(f"Using selected character image (gs): {character_image_path}")
                        else:
                            info(f"image_uri format unknown, using default: {image_uri}")
                    else:
                        info("No image_uri in Character doc, using default character image.")
                else:
                    info("No Character doc in Firestore, using default character image.")
        except Exception as e:
            warning(f"Failed to fetch selected character from Firestore, using default: {e}")

        storage_client = get_storage_client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(character_image_path)
        
        if not blob.exists():
            error(f"Character image not found: gs://{BUCKET_NAME}/{character_image_path}")
            # Try default as fallback
            if character_image_path != DEFAULT_CHARACTER_IMAGE_PATH:
                warning(f"Falling back to default character image: {DEFAULT_CHARACTER_IMAGE_PATH}")
                blob = bucket.blob(DEFAULT_CHARACTER_IMAGE_PATH)
                if not blob.exists():
                    error(f"Default character image not found either.")
                    return None
            else:
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
        
        info(f"[LLM] 🎨 Requesting diary image generation (Primary: {primary_model_id})...")
        
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
            info(f"[LLM] 🔄 Retrying with fallback model: {fallback_model_id}...")
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
                warning(f"Fallback model execution failed: {e}")
                # Try tertiary fallback

        # Tertiary Fallback: Flash with Simplified Prompt
        if not response or response.status_code != 200:
            try:
                info(f"[LLM] 🔄 Trying tertiary (Flash + simple prompt) for diary...")
                simple_prompt = f"A simple garden diary illustration, {summary}, soft colors"
                simple_payload = {
                    "contents": [{ "role": "user", "parts": [{"text": simple_prompt}] }],
                    "generationConfig": {}
                }
                response = call_api_with_backoff(
                    fallback_url,
                    simple_payload,
                    headers,
                    max_retries=3,
                    max_elapsed_seconds=45,
                    base_delay=1.0,
                    max_delay=5.0
                )
            except Exception as e:
                warning(f"Tertiary fallback failed for diary: {e}")

        # Final check before parsing/placeholder
        if not response or response.status_code != 200:
            status = response.status_code if response else "Unknown"
            warning(f"All AI generation attempts failed for diary (status: {status}). Using placeholder.")
            generated_bytes = base64.b64decode(DEFAULT_PLACEHOLDER_B64)
        else:
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
                    warning("No image data returned from AI. Using placeholder.")
                    generated_bytes = base64.b64decode(DEFAULT_PLACEHOLDER_B64)
                else:
                    generated_bytes = base64.b64decode(generated_b64)
            except (KeyError, IndexError) as e:
                warning(f"Failed to parse AI response: {e}. Using placeholder.")
                generated_bytes = base64.b64decode(DEFAULT_PLACEHOLDER_B64)

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
