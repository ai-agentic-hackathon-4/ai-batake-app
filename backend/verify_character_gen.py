import os
import sys
import json
import base64
import requests
import time
import random

# Configuration
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    # Try finding it in .env file directly if load_dotenv() failed or env var is missing
    # This is a fallback often needed in some environments
    try:
        # Try current dir first
        env_path = '.env'
        # print(f"Checking for .env at: {os.path.abspath(env_path)}")
        if not os.path.exists(env_path):
            # print("  Not found.")
            # Try parent dir
            env_path = '../.env'
            # print(f"Checking for .env at: {os.path.abspath(env_path)}")
            
        if os.path.exists(env_path):
            # print(f"  Found .env at: {env_path}")
            with open(env_path) as f:
                content = f.read()
                # print(f"  File content length: {len(content)}")
                for line in content.splitlines():
                    if 'GEMINI_API_KEY' in line:
                        # print(f"  Found key in line: {line[:25]}...")
                        if '=' in line:
                            key_part = line.split('=', 1)[1].strip()
                            API_KEY = key_part.strip('"').strip("'")
                            # print("  Extracted key.")
                        break
        else:
            print("  .env file not found in current or parent directory.")
    except Exception as e:
        print(f"  Error reading .env: {e}")
        pass

if not API_KEY:
    print("Error: GEMINI_API_KEY not found in environment or .env file.")
    sys.exit(1)

IMAGE_PATH = sys.argv[1] if len(sys.argv) > 1 else "../frontend/public/healthy-green-tomato-plant-in-smart-greenhouse-wit.jpg"

def call_api_with_backoff(url, payload, headers, max_retries=5):
    base_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                print(f"  Rate limited (429). Retrying in {delay:.2f}s...")
                time.sleep(delay)
                continue
            elif response.status_code >= 500:
                delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                print(f"  Server error ({response.status_code}). Retrying in {delay:.2f}s...")
                time.sleep(delay)
                continue
            else:
                return response
        except requests.exceptions.RequestException as e:
            delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
            print(f"  Network error ({e}). Retrying in {delay:.2f}s...")
            time.sleep(delay)
    
    raise RuntimeError(f"Max retries ({max_retries}) exceeded.")

def analyze_and_generate_character(image_path):
    print(f"Analyzing image: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        return

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    headers = {"Content-Type": "application/json"}
    
    # 1. Identify Vegetable & Character Personality (Gemini 3 Pro)
    print("\n1. Calling Gemini 3 Pro (Analysis)...")
    model_id = "gemini-3-flash-preview"
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    
    prompt_text = """
    このタネの画像を分析し、何の植物か特定してください。
    そして、その植物をモチーフにした「ゆるキャラ」の設定を考えてください。
    
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
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={API_KEY}"
    
    try:
        resp = call_api_with_backoff(url, payload, headers)
        if resp.status_code != 200:
            print(f"Error in Step 1: {resp.status_code} {resp.text}")
            return
            
        text_content = resp.json()['candidates'][0]['content']['parts'][0]['text']
        data = json.loads(text_content.strip())
        print(f"  Success! Identified: {data.get('name')}")
        print(f"  Character Name: {data.get('character_name')}")
        print(f"  Personality: {data.get('personality')}")
        
    except Exception as e:
        print(f"Exception in Step 1: {e}")
        return

    # 2. Generate Character Image (nanoBanana)
    print("\n2. Calling gemini-3-pro-image-preview (nanoBanana)...")
    img_model_id = "gemini-3-pro-image-preview" 
    img_url = f"https://generativelanguage.googleapis.com/v1beta/models/{img_model_id}:generateContent?key={API_KEY}"
    
    img_prompt = f"Generate an image of {data['image_prompt']}, cute mascot character, simple design, white background, high quality"
    img_payload = {
        "contents": [{ "role": "user", "parts": [{"text": img_prompt}] }],
        "generationConfig": {} 
    }
    
    try:
        img_resp = call_api_with_backoff(img_url, img_payload, headers)
        if img_resp.status_code != 200:
             print(f"Error in Step 2: {img_resp.status_code} {img_resp.text}")
             return
             
        parts = img_resp.json()['candidates'][0]['content']['parts']
        b64_data = None
        for part in parts:
            if 'inlineData' in part:
                b64_data = part['inlineData']['data']
                break
        
        if b64_data:
            print("  Success! Image generated.")
            output_filename = f"generated_character_{int(time.time())}.jpg"
            with open(output_filename, "wb") as f:
                f.write(base64.b64decode(b64_data))
            print(f"  Saved image to: {output_filename}")
        else:
            print("  Error: No inline image data returned.")
            
    except Exception as e:
        print(f"Exception in Step 2: {e}")
        return

if __name__ == "__main__":
    analyze_and_generate_character(IMAGE_PATH)
