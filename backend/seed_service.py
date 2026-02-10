import os
import base64
import json
import requests
import google.auth
import asyncio
from google.auth.transport.requests import Request
import concurrent.futures
import random
import time
import sys

# Import our structured logging module
try:
    from .logger import get_logger, info, debug, warning, error
except ImportError:
    from logger import get_logger, info, debug, warning, error

# Initialize logger
logger = get_logger()

# Configuration
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "ai-agentic-hackathon-4")
API_ENDPOINT = "aiplatform.googleapis.com"

def get_access_token():
    credentials, _ = google.auth.default()
    credentials.refresh(Request())
    return credentials.token

# Helper for Exponential Backoff (Sync)
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

# Define a consistent style for all images
UNIFIED_STYLE = "soft digital illustration, warm sunlight, gentle pastel colors, white background, home gardening context, consistent character design, high quality"

def process_step(args):
    """Generates image for a single step (Parallel Execution Helper)"""
    # args tuple unpacking needed because map passes one argument
    step, primary_img_url, fallback_img_url, headers = args
    
    # Small start jitter to avoid hitting rate limit exactly simultaneously
    time.sleep(random.uniform(0.5, 1.5))
    
    debug(f"Generating Image for step: {step['step_title']}")
    
    # Append style keywords to ensure consistency
    img_prompt = f"Generate an image of {step['image_prompt']}, {UNIFIED_STYLE}"
    img_payload = {
        "contents": [{ "role": "user", "parts": [{"text": img_prompt}] }],
        "generationConfig": {} # responseMimeType removed
    }
    
    try:
        img_response = call_api_with_backoff(
            primary_img_url,
            img_payload,
            headers,
            max_retries=6,
            max_elapsed_seconds=90,
            base_delay=1.5,
            max_delay=8.0,
        )
        
        if img_response.status_code != 200:
            warning(
                f"Image generation failed for '{step['step_title']}' (primary): "
                f"{img_response.status_code}"
            )
            if fallback_img_url:
                try:
                    warning(
                        f"Retrying image generation with fallback model for "
                        f"'{step['step_title']}'"
                    )
                    img_response = call_api_with_backoff(
                        fallback_img_url,
                        img_payload,
                        headers,
                        max_retries=4,
                        max_elapsed_seconds=60,
                        base_delay=1.5,
                        max_delay=8.0,
                    )
                except Exception as e:
                    warning(
                        f"Fallback image generation failed for '{step['step_title']}': {e}"
                    )
                    return {
                        "title": step['step_title'],
                        "description": step['description'],
                        "image_base64": None,
                        "error": f"API Error: {img_response.status_code}"
                    }

            if img_response.status_code != 200:
                return {
                    "title": step['step_title'],
                    "description": step['description'],
                    "image_base64": None,
                    "error": f"API Error: {img_response.status_code}"
                }
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
                    debug(f"Image generated successfully for step: {step['step_title']}")
                    return {
                        "title": step['step_title'],
                        "description": step['description'],
                        "image_base64": b64_data
                    }
                else:
                    warning(f"No inline image data for step: {step['step_title']}")
                    return {
                        "title": step['step_title'],
                        "description": step['description'],
                        "image_base64": None,
                        "error": "No image data returned"
                    }
            except Exception as e:
                error(f"Failed to parse image response for '{step['step_title']}': {e}")
                return {
                    "title": step['step_title'],
                    "description": step['description'],
                    "image_base64": None,
                    "error": f"Parse Error: {str(e)}"
                }

    except Exception as e:
        error(f"Image request failed for '{step['step_title']}': {e}")
        return {
            "title": step['step_title'],
            "description": step['description'],
            "image_base64": None,
            "error": f"Request Failed: {str(e)}"
        }

def _generate_images_parallel(steps, primary_img_url, fallback_img_url, headers):
    """Sync function to handle parallel execution waiting."""
    info(f"Starting parallel image generation for {len(steps)} steps...")
    
    # Prepare args for map
    # We need to pass img_url and headers to each thread
    map_args = [(step, primary_img_url, fallback_img_url, headers) for step in steps]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # map preserves the order of results corresponding to 'steps'
        final_steps = list(executor.map(process_step, map_args))
        
    return final_steps

async def analyze_seed_and_generate_guide(image_bytes: bytes, progress_callback=None):
    """
    Analyzes a seed image and generates a step-by-step planting guide with images using Vertex AI REST API.
    Args:
        image_bytes: The image content.
        progress_callback: Optional async function(message: str) to report progress.
    """
    info(f"Starting seed analysis and guide generation ({len(image_bytes)} bytes)")
    if progress_callback: await progress_callback("🌱 AI is analyzing the seed image (Gemini 3 Pro)...")

    # API Key Authentication
    api_key = os.environ.get("SEED_GUIDE_GEMINI_KEY")
    if not api_key:
        error("SEED_GUIDE_GEMINI_KEY environment variable not set")
        raise RuntimeError("SEED_GUIDE_GEMINI_KEY environment variable not set")
        
    # Headers: API Key mode does not use Bearer Token usually, but requires Content-Type
    headers = {
        "Content-Type": "application/json"
    }

    # 1. Analyze with Gemini 3 Pro (gemini-3-pro-preview)
    # Using User's Reference Config (Thinking, Tools) and Endpoint Structure
    model_id = "gemini-3-pro-preview"
    steps = []
    
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

    prompt_text = """
    このタネの画像を分析し、何の植物のタネか特定してください。
    そして、家庭菜園（プランターや庭）でこのタネを育てるための手順を教えてください。
    
    特に詳しく教えて欲しい点は以下です：
    1. 必要な道具（プランターのサイズ、土の種類など）
    2. 種まきの詳細な手順（深さ、間隔、数など具体的に）
    
    以下のJSON形式で出力してください。
    
    出力フォーマット(JSON):
    {
        "title": "植物名を含むガイドのタイトル（例：小松菜の育て方）",
        "description": "ガイドの簡単な概要（1-2文）",
        "steps": [
            {
                "step_title": "ステップのタイトル",
                "description": "具体的な手順の説明（日本語）。種まきの際は深さや定規なども言及してください。",
                "image_prompt": "A visual depiction of [description] for [plant name], [UNIFIED_STYLE]"
            }
        ]
    }
    
    注意:
    - 日本語で出力してください。
    - image_promptは画像生成AI(Nanobanana Pro)に入力するため、英語で具体的に記述してください。
    - 家庭菜園初心者にもわかりやすく説明してください。
    - JSONオブジェクトのみを出力してください。Markdownコードブロックは不要です。
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

    # Endpoint: Use aiplatform.googleapis.com (generateContent)
    url = (
        f"https://{API_ENDPOINT}/v1/publishers/google/"
        f"models/{model_id}:generateContent?key={api_key}"
    )
    
    debug(f"Requesting Gemini 3 Pro Analysis: {url.split('?')[0]}?key=***")
    
    try:
        # User dedicated executor to avoid default loop executor issues
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            response = await loop.run_in_executor(pool, lambda: call_api_with_backoff(url, payload, headers))
        
        if response.status_code != 200:
            error(f"Gemini 3 Pro Analysis failed: {response.text[:500]}...")
            raise RuntimeError(f"Gemini 3 Pro Analysis failed: {response.status_code} {response.text}")
            
        resp_json = response.json()
        
        guide_title = "Generated Guide"
        guide_description = ""
        steps = []
        
        try:
            # Parse response.
            text_content = resp_json['candidates'][0]['content']['parts'][0]['text']
            
            # Clean up JSON markdown
            text = text_content.strip()
            if text.startswith("```json"): text = text[7:]
            if text.endswith("```"): text = text[:-3]
            
            data = json.loads(text.strip())
            
            # Handle both list (old format fallback) and object (new format)
            if isinstance(data, list):
                steps = data
                # Infer title from first step or default
                if steps and "title" in steps[0]:
                     guide_title = steps[0]["title"].split("：")[0] + "の育て方"
                else:
                     guide_title = "Seed Guide"
            elif isinstance(data, dict):
                steps = data.get("steps", [])
                guide_title = data.get("title", "Seed Guide")
                guide_description = data.get("description", "")
            
            info(f"Seed analysis completed: {guide_title}, {len(steps)} steps identified")
            
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            error(f"Failed to parse Gemini 3 Pro response: {e}")
            raise RuntimeError(f"Failed to parse Gemini 3 Pro response: {e}")
            
    except Exception as e:
        error(f"Seed analysis failed: {e}", exc_info=True)
        raise e

    if progress_callback: await progress_callback(f"🎨 Generating illustrations for {len(steps)} steps (Nanobanana Pro)...")

    # 2. Generate Images with primary model + fallback
    primary_img_model_id = "gemini-3-pro-image-preview"
    fallback_img_model_id = "gemini-2.5-flash-image"
    
    # Url: https://aiplatform.googleapis.com/v1/publishers/google/models/{img_model_id}:generateContent?key={API_KEY}
    primary_img_url = (
        f"https://{API_ENDPOINT}/v1/publishers/google/"
        f"models/{primary_img_model_id}:generateContent?key={api_key}"
    )
    fallback_img_url = (
        f"https://{API_ENDPOINT}/v1/publishers/google/"
        f"models/{fallback_img_model_id}:generateContent?key={api_key}"
    )
    
    # Offload parallel image generation to thread
    final_steps = await asyncio.to_thread(
        _generate_images_parallel,
        steps,
        primary_img_url,
        fallback_img_url,
        headers
    )
    
    successful_images = sum(1 for step in final_steps if step.get('image_base64'))
    info(f"Guide generation complete: {len(final_steps)} steps, {successful_images} images generated")
    
    if progress_callback: await progress_callback("✨ Guide generation complete!")
            
    return guide_title, guide_description, final_steps
