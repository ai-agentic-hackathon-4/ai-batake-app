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
    info(f"[LLM] 🎭 Starting character generation ({len(image_bytes)} bytes)")

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
        max_delay = 15.0
        max_retries = 100
        max_elapsed_seconds = 1800  # 30 minutes
        start_time = time.time()
        
        last_status_code = None
        for attempt in range(max_retries):
            elapsed = time.time() - start_time
            if elapsed >= max_elapsed_seconds:
                raise RuntimeError(f"API call failed: retry budget exceeded ({max_elapsed_seconds}s). Last status: {last_status_code}")
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                last_status_code = response.status_code
                if response.status_code == 200:
                    return response
                elif response.status_code == 429 or response.status_code >= 500:
                    delay = min(base_delay * (2 ** attempt), max_delay) + random.uniform(0, 1)
                    warning(f"API {response.status_code}. Retrying in {delay:.1f}s... (attempt {attempt+1}/{max_retries}, elapsed={elapsed:.0f}s)")
                    time.sleep(delay)
                    continue
                else:
                    return response
            except requests.exceptions.RequestException as e:
                delay = min(base_delay * (2 ** attempt), max_delay) + random.uniform(0, 1)
                warning(f"Request error: {e}. Retrying in {delay:.1f}s... (attempt {attempt+1}/{max_retries}, elapsed={elapsed:.0f}s)")
                time.sleep(delay)
        
        if last_status_code == 429:
            raise RuntimeError("API rate limit exceeded (429). Please try again later.")
        raise RuntimeError(f"API call failed after {max_retries} retries. Last status: {last_status_code}")

    # 1. Identify Vegetable & Character Personality (Gemini 3 Pro)
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
    
    # Use verified endpoint: generativelanguage.googleapis.com
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"
    
    try:
        resp = call_api(url, payload, headers)
        if resp.status_code != 200:
            raise RuntimeError(f"Analysis failed: {resp.text}")
            
        text_content = resp.json()['candidates'][0]['content']['parts'][0]['text']
        data = json.loads(text_content.strip())
        info(f"[LLM] ✅ Character identified: {data.get('character_name')}")
        
    except Exception as e:
        error(f"Character analysis failed: {e}")
        raise e

    # 2. Generate Character Image (nanoBanana)
    img_model_id = "gemini-3-pro-image-preview" 
    img_url = f"https://generativelanguage.googleapis.com/v1beta/models/{img_model_id}:generateContent?key={api_key}"
    
    img_prompt = (
        f"Generate an image of exactly ONE single {data['image_prompt']}. "
        "STRICT RULES: "
        "1. The background MUST be pure white (#FFFFFF), no patterns, no gradients, no scenery. "
        "2. There MUST be exactly ONE character only, no duplicates, no other characters, no companions. "
        "Solo character, centered composition, cute mascot character, simple clean design, "
        "high quality, digital art style, single subject, isolated on white background."
    )
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


def generate_character_message(character_data: dict, sensor_data: dict, weather_data: dict = None) -> str:
    """
    Generates a contextual message from the character based on sensor and weather data.
    
    Args:
        character_data: Dict with character_name, personality, vegetable_name
        sensor_data: Dict with temperature, humidity, soil_moisture, illuminance
        weather_data: Optional dict with forecast information
        
    Returns:
        A friendly message string from the character
    """
    info(f"[LLM] 💬 Generating message for character: {character_data.get('name', 'Unknown')}")
    
    # API Key Authentication
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("SEED_GUIDE_GEMINI_KEY")
    if not api_key:
        error("GEMINI_API_KEY environment variable not set")
        return "こんにちは！今日も元気に育てていこうね！"
    
    character_name = character_data.get("name", "お友達")
    personality = character_data.get("personality", "明るくて元気")
    vegetable_name = character_data.get("vegetable_name", "野菜")
    
    # Build context from sensor data
    temp = sensor_data.get("temperature", "--")
    humidity = sensor_data.get("humidity", "--")
    soil_moisture = sensor_data.get("soil_moisture", "--")
    illuminance = sensor_data.get("illuminance", "--")
    
    # Build weather context if available
    weather_context = ""
    if weather_data:
        weather_context = f"\n天気予報: {weather_data.get('condition', '情報なし')}, 気温{weather_data.get('temp', '--')}°C"
        if weather_data.get('forecast'):
            forecast_items = weather_data['forecast']
            for item in forecast_items:
                if item.get('icon') == 'CloudRain':
                    weather_context += f"\n{item['time']}から雨が降りそうです"
                    break
    
    prompt = f"""
あなたは「{character_name}」という名前のかわいいキャラクターです。
性格: {personality}
あなたは{vegetable_name}をモチーフにしています。

現在の環境データ:
- 気温: {temp}°C
- 湿度: {humidity}%
- 土壌水分: {soil_moisture}%
- 照度: {illuminance}lx{weather_context}

このデータを見て、ユーザーに今日の栽培アドバイスや注意点を親しみやすく伝えてください。
あなたの性格と、{vegetable_name}らしさを活かして、1-2文で簡潔にメッセージを作ってください。
絵文字も適度に使って、楽しく親しみやすい雰囲気にしてください。

例:
- 「こんにちは！今日は気温が26°Cで快適だね🌱でも18時から雨が降るみたい☔湿度が上がるから注意してね！」
- 「気温が{temp}°Cだよ！{vegetable_name}にとってちょうどいい感じ✨水やりは土の様子を見てからにしようね💧」

メッセージのみを出力してください（説明や前置きは不要です）:
"""
    
    headers = {"Content-Type": "application/json"}
    model_id = "gemini-3-flash-preview"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        message = result['candidates'][0]['content']['parts'][0]['text'].strip()
        
        info(f"[LLM] ✅ Message generated: {message[:50]}...")
        return message
        
    except Exception as e:
        error(f"Failed to generate character message: {e}", exc_info=True)
        # Return a friendly fallback message
        return f"こんにちは！今日も{vegetable_name}を元気に育てていこうね🌱✨"
