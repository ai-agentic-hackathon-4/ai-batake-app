import os
import base64
import json
import requests
import google.auth
from google.auth.transport.requests import Request

# Configuration
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "ai-agentic-hackathon-4")
LOCATION =  "us-central1"
API_ENDPOINT = f"https://{LOCATION}-aiplatform.googleapis.com/v1"

def get_access_token():
    credentials, _ = google.auth.default()
    credentials.refresh(Request())
    return credentials.token

async def analyze_seed_and_generate_guide(image_bytes: bytes):
    """
    Analyzes a seed image and generates a step-by-step planting guide with images using Vertex AI REST API.
    """
    # API Key Authentication
    api_key = os.environ.get("SEED_GUIDE_GEMINI_KEY")
    if not api_key:
        raise RuntimeError("SEED_GUIDE_GEMINI_KEY environment variable not set")
        
    # Headers: API Key mode does not use Bearer Token usually, but requires Content-Type
    headers = {
        "Content-Type": "application/json"
    }

    # Helper for Exponential Backoff
    def call_api_with_backoff(url, payload, headers, max_retries=5):
        import time
        import random
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=120)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    # 429 Resource Exhausted
                    delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                    print(f"API 429 (Resource Exhausted). Retrying in {delay:.2f}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(delay)
                    continue
                elif response.status_code >= 500:
                    # Server Error - also retry
                    delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                    print(f"API {response.status_code}. Retrying in {delay:.2f}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    # Other errors (400, 403, etc) - do not retry
                    return response
            except requests.exceptions.RequestException as e:
                # Network error - retry
                delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                print(f"Network Error: {e}. Retrying in {delay:.2f}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(delay)
        
        raise RuntimeError(f"Max retries ({max_retries}) exceeded.")

    # 1. Analyze with Gemini 3 Pro (gemini-3-pro-preview)
    # Using User's Reference Config (Thinking, Tools) and Endpoint Structure
    model_id = "gemini-3-pro-preview"
    steps = []
    
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

    prompt_text = """
    このタネの画像を分析し、何の植物のタネか特定してください。
    そして、このタネを植えてから発芽、成長させるまでの手順をステップバイステップで説明してください。
    各ステップについて、以下のJSON形式で出力してください。
    
    出力フォーマット(JSON):
    [
        {
            "step_title": "ステップのタイトル",
            "description": "具体的な手順の説明（日本語）",
            "image_prompt": "An illustration of [description] for [plant name], photorealistic, high quality"
        },
        ...
    ]
    
    注意:
    - 日本語で出力してください。
    - image_promptは画像生成AI(Nanobanana Pro)に入力するため、英語で具体的に記述してください。
    - JSONリストのみを出力してください。Markdownコードブロックは不要です。
    """

    # User Reference Configuration
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt_text},
                    {"inlineData": {"mimeType": "image/jpeg", "data": image_b64}}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "thinkingConfig": {
                "thinkingLevel": "HIGH"
            }
        },
        "tools": [
            { "googleSearch": {} }
        ]
    }

    # Endpoint: https://aiplatform.googleapis.com/v1/publishers/google/models/{model_id}:generateContent?key={API_KEY}
    url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{model_id}:generateContent?key={api_key}"
    
    print(f"Requesting Gemini 3 Pro Analysis (API Key): {url.split('?')[0]}?key=***")
    
    try:
        response = call_api_with_backoff(url, payload, headers)
        
        if response.status_code != 200:
            print(f"Global Endpoint failed: {response.text}")
            raise RuntimeError(f"Gemini 3 Pro Analysis failed: {response.status_code} {response.text}")
            
        resp_json = response.json()
        try:
            # Parse response.
            text_content = resp_json['candidates'][0]['content']['parts'][0]['text']
            
            # Clean up JSON markdown
            text = text_content.strip()
            if text.startswith("```json"): text = text[7:]
            if text.endswith("```"): text = text[:-3]
            steps = json.loads(text.strip())
            
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to parse Gemini 3 Pro response: {e}")
            
    except Exception as e:
        print(f"Analysis failed: {e}")
        raise e

    # 2. Generate Images with Nanobanana Pro (gemini-3-pro-image-preview)
    img_model_id = "gemini-3-pro-image-preview" 
    
    final_steps = []
    
    # Url: https://aiplatform.googleapis.com/v1/publishers/google/models/{img_model_id}:generateContent?key={API_KEY}
    img_url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{img_model_id}:generateContent?key={api_key}"
    
    import time
    
    for step in steps:
        time.sleep(1) # Basic interval
        print(f"Generating Image with Nanobanana Pro ({img_model_id}) for: {step['image_prompt']}")
        image_generated = False
        
        img_prompt = f"Generate an image of {step['image_prompt']}"
        
        img_payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": img_prompt}]
                }
            ],
            # Minimal config for Image Gen
            "generationConfig": {
                 # "responseMimeType": "image/jpeg" # Removed: Unsupported by Nanobanana Pro
            }
        }
        
        try:
            img_response = call_api_with_backoff(img_url, img_payload, headers, max_retries=5)
            
            if img_response.status_code != 200:
                print(f"Nanobanana Pro Generation failed: {img_response.status_code} - {img_response.text}")
            else:
                img_resp_json = img_response.json()
                try:
                    parts = img_resp_json['candidates'][0]['content']['parts']
                    b64_data = None
                    for part in parts:
                        if 'inlineData' in part:
                            b64_data = part['inlineData']['data']
                            break
                    
                    if b64_data:
                        final_steps.append({
                            "title": step['step_title'],
                            "description": step['description'],
                            "image_base64": b64_data
                        })
                        image_generated = True
                    else:
                        print(f"No inline image data in Nanobanana response: {img_resp_json}")
                except Exception as e:
                    print(f"Failed to parse Nanobanana response: {e}")

        except Exception as e:
            print(f"Image request failed: {e}")
        
        if not image_generated:
             final_steps.append({
                "title": step['step_title'],
                "description": step['description'],
                "image_base64": None,
                "error": "Image generation failed (Nanobanana Pro)"
            })
            
    return final_steps
