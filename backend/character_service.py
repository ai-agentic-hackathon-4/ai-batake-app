import os
import base64
import json
import requests
import google.auth
from google.auth.transport.requests import Request

# Import our structured logging module
try:
    from .logger import get_logger, info, debug, warning, error
except ImportError:
    from logger import get_logger, info, debug, warning, error

# Initialize logger
logger = get_logger()

async def analyze_seed_and_generate_character(image_bytes: bytes):
    """
    Analyzes a seed image, identifies the vegetable, and generates a character image.
    Uses Gemini 3 Pro (Text) and Gemini 3 Pro Image (nanoBanana).
    """
    info(f"Starting character generation ({len(image_bytes)} bytes)")

    # API Key Authentication
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("SEED_GUIDE_GEMINI_KEY")
    if not api_key:
        error("GEMINI_API_KEY environment variable not set")
        raise RuntimeError("GEMINI_API_KEY environment variable not set")
        
    headers = {"Content-Type": "application/json"}
    
    # Reuse module-level call_api_with_backoff if possible, but for now defining local helper
    # to match the pattern or simply use requests directly with retry logic similar to verified script.
    
    def call_api(url, payload, headers):
        import time
        import random
        base_delay = 2
        max_retries = 5
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429 or response.status_code >= 500:
                    time.sleep((base_delay * (2 ** attempt)) + random.uniform(0, 1))
                    continue
                else:
                    return response
            except requests.exceptions.RequestException:
                time.sleep((base_delay * (2 ** attempt)) + random.uniform(0, 1))
        raise RuntimeError(f"API call failed after {max_retries} retries")

    # 1. Identify Vegetable & Character Personality (Gemini 3 Pro)
    model_id = "gemini-3-pro-preview"
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    
    prompt_text = """
    このタネの画像を分析し、何の植物か特定してください。
    そして、その植物をモチーフにした「ゆるキャラ」の設定を考えてください。
    背景は必ず白にしてください。
    キャラクターは必ず1体のみ表示してください。
    
    
    以下のJSON形式で出力してください:
    {
        "name": "植物名（例：トマト）",
        "character_name": "キャラクター名（例：トマちゃん）",
        "personality": "性格や特徴（日本語で20文字程度）",
        "image_prompt": "A visual depiction of a cute [plant name] character, [traits], digital art style, white background"
    }
    """
    
    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": prompt_text},
                {"inlineData": {"mimeType": "image/jpeg", "data": image_b64}}
            ]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    # Use verified endpoint: generativelanguage.googleapis.com
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"
    
    try:
        resp = call_api(url, payload, headers)
        if resp.status_code != 200:
            raise RuntimeError(f"Analysis failed: {resp.text}")
            
        text_content = resp.json()['candidates'][0]['content']['parts'][0]['text']
        data = json.loads(text_content.strip())
        info(f"Character identified: {data.get('character_name')}")
        
    except Exception as e:
        error(f"Character analysis failed: {e}")
        raise e

    # 2. Generate Character Image (nanoBanana)
    img_model_id = "gemini-3-pro-image-preview" 
    img_url = f"https://generativelanguage.googleapis.com/v1beta/models/{img_model_id}:generateContent?key={api_key}"
    
    img_prompt = f"Generate an image of ONE single {data['image_prompt']}, solo character, centered, cute mascot character, simple design, white background, high quality, no other characters, single subject"
    img_payload = {
        "contents": [{ "role": "user", "parts": [{"text": img_prompt}] }],
        "generationConfig": {} 
    }
    
    try:
        img_resp = call_api(img_url, img_payload, headers)
        if img_resp.status_code != 200:
             raise RuntimeError(f"Image generation failed: {img_resp.text}")
             
        parts = img_resp.json()['candidates'][0]['content']['parts']
        b64_data = None
        for part in parts:
            if 'inlineData' in part:
                b64_data = part['inlineData']['data']
                break
        
        if b64_data:
            data['image_base64'] = b64_data
            return data
        else:
            raise RuntimeError("No image data returned")
            
    except Exception as e:
        error(f"Character image generation failed: {e}")
        raise e
