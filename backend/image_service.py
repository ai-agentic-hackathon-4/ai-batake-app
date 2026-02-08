import os
import io
import base64
import requests
import json
import logging
from datetime import datetime, timedelta
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
LOCATION = "us-central1"

def get_storage_client():
    return storage.Client()

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
        model_id = "gemini-3-pro-image-preview"
        url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{model_id}:generateContent?key={api_key}"
        
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
        
        info(f"Requesting NanoBanana-pro image generation...")
        response = requests.post(url, headers=headers, json=payload, timeout=120)

        if response.status_code != 200:
            error(f"NanoBanana-pro request failed: {response.status_code} - {response.text}")
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
