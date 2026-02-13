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
    max_retries=500,
    max_elapsed_seconds=1800,
    base_delay=1.0,
    max_delay=5.0,
    exp_base=1.1,
):
    start_time = time.time()

    for attempt in range(max_retries):
        elapsed = time.time() - start_time
        if elapsed >= max_elapsed_seconds:
            error(f"Retry budget exceeded ({max_elapsed_seconds}s).")
            raise RuntimeError("Retry budget exceeded")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=240)

            if response.status_code == 200:
                return response
            if response.status_code in (429,) or response.status_code >= 500:
                # Honor Retry-After when present
                retry_after = response.headers.get("Retry-After")
                if retry_after is not None:
                    try:
                        delay = min(float(retry_after), max_delay)
                    except ValueError:
                        delay = min(base_delay * (exp_base ** attempt), max_delay)
                else:
                    delay = min(base_delay * (exp_base ** attempt), max_delay)

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
            delay = min(base_delay * (exp_base ** attempt), max_delay) + random.uniform(0, 0.5)
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
            from .db import db as firestore_db, col
        except ImportError:
            from db import db as firestore_db, col
        try:
            if firestore_db is None:
                info("Firestore not available, using default character image.")
            else:
                char_doc = firestore_db.collection(col("growing_diaries")).document("Character").get()
                if char_doc.exists:
                    char_data = char_doc.to_dict()
                    image_uri = char_data.get("image_uri", "")
                    if image_uri:
                        # Convert GCS URL or gs:// URI to blob path
                        gcs_https_prefix = f"https://storage.googleapis.com/{BUCKET_NAME}/"
                        gs_prefix = f"gs://{BUCKET_NAME}/"
                        if image_uri.startswith(gcs_https_prefix):
                            character_image_path = image_uri[len(gcs_https_prefix):]
                            debug(f"Using selected character image: {character_image_path}")
                        elif image_uri.startswith(gs_prefix):
                            character_image_path = image_uri[len(gs_prefix):]
                            debug(f"Using selected character image (gs): {character_image_path}")
                        else:
                            debug(f"image_uri format unknown, using default: {image_uri}")
                    else:
                        debug("No image_uri in Character doc, using default character image.")
                else:
                    debug("No Character doc in Firestore, using default character image.")
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
        model_id = "gemini-3-pro-image-preview"
        
        # Fallback Key
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        
        # Primary: Vertex AI
        vertex_url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{model_id}:generateContent?key={api_key}"
        # Fallback: Gemini API
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={gemini_api_key}"
        
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
        
        info(f"[LLM] 🎨 Requesting diary image generation (model: {model_id})...")
        
        response = None
        
        # Attempt 1: Vertex AI
        try:
            info(f"[LLM] 🎨 Attempting Primary (Vertex AI)...")
            response = call_api_with_backoff(
                vertex_url,
                payload,
                headers,
                max_retries=3, # Reduced retries for primary to fail faster to fallback
                max_elapsed_seconds=60,
                base_delay=1.0,
                max_delay=5.0
            )
        except Exception as e:
            warning(f"Primary (Vertex AI) failed with exception: {e}")
            response = None # Ensure we trigger fallback

        # Check if primary failed (either exception or non-200)
        if not response or response.status_code != 200:
            status = response.status_code if response else "Exception"
            warning(f"Primary (Vertex AI) failed (status: {status}). Switching to Fallback (Gemini API)...")
            
            # Attempt 2: Gemini API
            try:
                response = call_api_with_backoff(
                    gemini_url,
                    payload,
                    headers,
                    max_retries=5,
                    max_elapsed_seconds=120,
                    base_delay=1.0,
                    max_delay=5.0
                )
                if response and response.status_code == 200:
                    info(f"[LLM] 🎨 Fallback (Gemini API) succeeded!")
                else:
                    status = response.status_code if response else "Unknown"
                    warning(f"Fallback (Gemini API) also failed (status: {status}).")
            except Exception as e:
                 warning(f"Fallback (Gemini API) failed with exception: {e}")

        if not response or response.status_code != 200:
            status = response.status_code if response else "Unknown"
            warning(f"AI generation failed for diary (status: {status}). Using placeholder.")
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
        
        debug(f"Generated image saved to gs://{BUCKET_NAME}/{output_filename}")

        # Return the GCS path to be stored in Firestore
        return f"gs://{BUCKET_NAME}/{output_filename}"

    except Exception as e:
        error(f"Error in picture diary generation: {e}")
        return None
