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
    max_retries=100,
    max_elapsed_seconds=1800,
    base_delay=2.0,
    max_delay=15.0,
    request_timeout=60,
):
    start_time = time.time()
    # Extract model name from URL for logging
    _model_name = "unknown"
    if "/models/" in url:
        _model_name = url.split("/models/")[1].split(":")[0]

    for attempt in range(max_retries):
        elapsed = time.time() - start_time
        if elapsed >= max_elapsed_seconds:
            error(f"[LLM] ⏰ Retry budget exceeded ({max_elapsed_seconds}s) for model={_model_name}")
            raise RuntimeError("Retry budget exceeded")

        if attempt > 0:
            info(f"[LLM] 🔄 Retry attempt {attempt+1}/{max_retries} for model={_model_name} (elapsed={elapsed:.0f}s)")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=request_timeout)

            if response.status_code == 200:
                elapsed_now = time.time() - start_time
                info(f"[LLM] ✅ API call succeeded: model={_model_name} elapsed={elapsed_now:.1f}s")
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

# Final hardcoded placeholder image (Base64 of a simple 1x1 green pixel or a small SVG-like data)
# In a real app, this should be a nice SVG or a small gardening icon. 
# For now, we use a slightly more meaningful placeholder if possible, or just a generic high-quality one.
# Let's use a simple green-themed placeholder.
DEFAULT_PLACEHOLDER_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==" # 1x1 green pixel as safe failover

def process_step(args):
    """Generates image for a single step (Parallel Execution Helper)"""
    # args tuple unpacking needed because map passes one argument
    step, primary_img_url, fallback_img_url, headers = args
    
    # Small start jitter to avoid hitting rate limit exactly simultaneously
    time.sleep(random.uniform(0.5, 1.5))
    
    info(f"[LLM] Generating image for step: {step['step_title']}")
    
    # Append style keywords to ensure consistency
    img_prompt = f"Generate an image of {step['image_prompt']}, {UNIFIED_STYLE}"
    img_payload = {
        "contents": [{ "role": "user", "parts": [{"text": img_prompt}] }],
        "generationConfig": {}
    }
    
    img_response = None
    
    try:
        # --- Primary Model ---
        try:
            img_response = call_api_with_backoff(
                primary_img_url,
                img_payload,
                headers,
                max_retries=6,
                max_elapsed_seconds=300,
                base_delay=1.5,
                max_delay=8.0,
                request_timeout=180,
            )
            if img_response.status_code != 200:
                warning(f"Image generation failed for '{step['step_title']}' (primary): {img_response.status_code}")
                img_response = None
        except Exception as e:
            warning(f"Primary model exception for '{step['step_title']}': {e}")
            img_response = None

        # --- Fallback Model ---
        if img_response is None and fallback_img_url:
            try:
                warning(f"Retrying with fallback model for '{step['step_title']}'")
                img_response = call_api_with_backoff(
                    fallback_img_url,
                    img_payload,
                    headers,
                    max_retries=4,
                    max_elapsed_seconds=240,
                    base_delay=1.5,
                    max_delay=8.0,
                    request_timeout=180,
                )
                if img_response.status_code != 200:
                    warning(f"Fallback also failed for '{step['step_title']}': {img_response.status_code}")
                    img_response = None
            except Exception as e:
                warning(f"Fallback image generation failed for '{step['step_title']}': {e}")
                img_response = None

        # --- Tertiary Fallback: Flash with Simplified Prompt ---
        if img_response is None and fallback_img_url:
            try:
                warning(f"Trying Tertiary (Flash + Simple Prompt) for '{step['step_title']}'")
                simple_prompt = f"A simple digital illustration of gardening, {step['step_title']}, clean white background"
                simple_payload = {
                    "contents": [{ "role": "user", "parts": [{"text": simple_prompt}] }],
                    "generationConfig": {}
                }
                img_response = call_api_with_backoff(
                    fallback_img_url,
                    simple_payload,
                    headers,
                    max_retries=3,
                    max_elapsed_seconds=180,
                    base_delay=1.0,
                    max_delay=5.0,
                    request_timeout=180,
                )
                if img_response.status_code != 200:
                    warning(f"Tertiary also failed for '{step['step_title']}': {img_response.status_code}")
                    img_response = None
            except Exception as e:
                warning(f"Tertiary fallback failed for '{step['step_title']}': {e}")
                img_response = None

        # --- Parse the successful response (whichever model succeeded) ---
        if img_response is not None and img_response.status_code == 200:
            img_resp_json = img_response.json()
            try:
                parts = img_resp_json['candidates'][0]['content']['parts']
                b64_data = None
                for part in parts:
                    if 'inlineData' in part:
                        b64_data = part['inlineData']['data']
                        break
                
                if b64_data:
                    info(f"[LLM] ✅ Image generated successfully for step: {step['step_title']}")
                    return {
                        "title": step['step_title'],
                        "description": step['description'],
                        "image_base64": b64_data
                    }
                else:
                    warning(f"No inline image data for step: {step['step_title']}. Using placeholder.")
            except Exception as e:
                error(f"Failed to parse image response for '{step['step_title']}': {e}")

        # --- All attempts failed or parsing failed: use placeholder ---
        warning(f"All AI generation attempts exhausted for '{step['step_title']}'. Using placeholder.")
        return {
            "title": step['step_title'],
            "description": step['description'],
            "image_base64": DEFAULT_PLACEHOLDER_B64,
            "error": "All generation attempts failed, used placeholder"
        }

    except Exception as e:
        error(f"Image request failed for '{step['step_title']}': {e}")
        return {
            "title": step['step_title'],
            "description": step['description'],
            "image_base64": DEFAULT_PLACEHOLDER_B64,
            "error": f"Request Failed: {str(e)}"
        }

def _generate_images_parallel(steps, primary_img_url, fallback_img_url, headers):
    """Sync function to handle parallel execution waiting."""
    info(f"Starting parallel image generation for {len(steps)} steps...")
    
    # Prepare args for map
    # We need to pass img_url and headers to each thread
    map_args = [(step, primary_img_url, fallback_img_url, headers) for step in steps]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # map preserves the order of results corresponding to 'steps'
        final_steps = list(executor.map(process_step, map_args))
        
    return final_steps


def _generate_single_guide_image(guide_title, steps, api_key, headers):
    """Generates a single infographic-style image summarizing all steps using NanoBanana Pro."""
    info(f"Generating single guide image for: {guide_title} ({len(steps)} steps)")
    
    # Build a comprehensive prompt from all steps
    steps_description = "\n".join(
        f"Step {i+1}: {s.get('step_title', s.get('title', ''))} - {s.get('description', '')[:100]}"
        for i, s in enumerate(steps)
    )
    
    prompt = (
        f"Create a beautiful, detailed infographic-style illustration for a home gardening guide: '{guide_title}'.\n"
        f"The image should show the complete growing process in a single visual, with numbered steps arranged in a clear flow.\n"
        f"Steps:\n{steps_description}\n\n"
        f"Style: Soft watercolor illustration, warm pastel colors, numbered steps with small icons, "
        f"clean white background, Japanese home gardening context, cute and friendly style, "
        f"high quality infographic layout, step numbers clearly visible, "
        f"arrows or flow lines connecting each step."
    )
    
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {}
    }
    
    # --- Primary: gemini-3-pro-image-preview ---
    primary_model = "gemini-3-pro-image-preview"
    primary_url = (
        f"https://{API_ENDPOINT}/v1/publishers/google/"
        f"models/{primary_model}:generateContent?key={api_key}"
    )
    
    try:
        info(f"Trying primary model ({primary_model}) for single guide image")
        response = call_api_with_backoff(
            primary_url, payload, headers,
            max_retries=4,
            max_elapsed_seconds=300,
            base_delay=2.0,
            max_delay=10.0,
            request_timeout=180,
        )
        
        if response.status_code == 200:
            b64_data = _extract_image_from_response(response)
            if b64_data:
                info(f"Single guide image generated successfully (primary) for: {guide_title}")
                return b64_data
            warning(f"No inline image data in primary response for: {guide_title}")
        else:
            warning(f"Primary model failed for single guide image: {response.status_code}")
    except Exception as e:
        warning(f"Primary model exception for single guide image: {e}")
    
    # --- Fallback: gemini-2.5-flash-image ---
    fallback_model = "gemini-2.5-flash-image"
    fallback_url = (
        f"https://{API_ENDPOINT}/v1/publishers/google/"
        f"models/{fallback_model}:generateContent?key={api_key}"
    )
    
    try:
        warning(f"Retrying with fallback model ({fallback_model}) for single guide image")
        response = call_api_with_backoff(
            fallback_url, payload, headers,
            max_retries=3,
            max_elapsed_seconds=240,
            base_delay=2.0,
            max_delay=8.0,
            request_timeout=180,
        )
        
        if response.status_code == 200:
            b64_data = _extract_image_from_response(response)
            if b64_data:
                info(f"Single guide image generated successfully (fallback) for: {guide_title}")
                return b64_data
            warning(f"No inline image data in fallback response for: {guide_title}")
        else:
            warning(f"Fallback model also failed for single guide image: {response.status_code}")
    except Exception as e:
        warning(f"Fallback model exception for single guide image: {e}")
    
    # --- Tertiary: Flash with simplified prompt ---
    try:
        simple_prompt = (
            f"A simple, cute digital illustration showing the gardening process for {guide_title}. "
            f"Clean white background, soft pastel colors, numbered steps."
        )
        simple_payload = {
            "contents": [{"role": "user", "parts": [{"text": simple_prompt}]}],
            "generationConfig": {}
        }
        warning(f"Trying tertiary (Flash + simple prompt) for single guide image")
        response = call_api_with_backoff(
            fallback_url, simple_payload, headers,
            max_retries=2,
            max_elapsed_seconds=180,
            base_delay=1.5,
            max_delay=6.0,
            request_timeout=180,
        )
        
        if response.status_code == 200:
            b64_data = _extract_image_from_response(response)
            if b64_data:
                info(f"Single guide image generated successfully (tertiary) for: {guide_title}")
                return b64_data
    except Exception as e:
        error(f"All single guide image generation attempts failed: {e}")
    
    error(f"Single guide image generation exhausted all attempts for: {guide_title}")
    return None


def _extract_image_from_response(response):
    """Extract base64 image data from a Gemini API response."""
    try:
        resp_json = response.json()
        parts = resp_json['candidates'][0]['content']['parts']
        for part in parts:
            if 'inlineData' in part:
                return part['inlineData']['data']
    except (KeyError, IndexError, Exception) as e:
        warning(f"Failed to extract image from response: {e}")
    return None

async def analyze_seed_and_generate_guide(image_bytes: bytes, progress_callback=None, image_model: str = "pro", guide_image_mode: str = "single"):
    """
    Analyzes a seed image and generates a step-by-step planting guide with images using Vertex AI REST API.
    Args:
        image_bytes: The image content.
        progress_callback: Optional async function(message: str) to report progress.
        image_model: "pro" for gemini-3-pro-image-preview or "flash" for gemini-2.5-flash-image
        guide_image_mode: "single" for one infographic image (NanoBanana Pro), "per_step" for per-step images
    """
    info(f"Starting seed analysis and guide generation ({len(image_bytes)} bytes, model={image_model})")
    if progress_callback: await progress_callback("🌱 AI is analyzing the seed image (Gemini 3 Pro)...")
    
    # ... (rest of authentication and analysis logic stays same)
    api_key = os.environ.get("SEED_GUIDE_GEMINI_KEY")
    if not api_key:
        error("SEED_GUIDE_GEMINI_KEY environment variable not set")
        raise RuntimeError("SEED_GUIDE_GEMINI_KEY environment variable not set")
        
    headers = {
        "Content-Type": "application/json"
    }

    # 1. Analyze with Gemini 3 Pro (gemini-3-flash-preview)
    model_id = "gemini-3-flash-preview"
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
    - image_promptは画像生成AIに入力するため、英語で具体的に記述してください。
    - 家庭菜園初心者にもわかりやすく説明してください。
    - JSONオブジェクトのみを出力してください。Markdownコードブロックは不要です。
    """

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

    url = (
        f"https://{API_ENDPOINT}/v1/publishers/google/"
        f"models/{model_id}:generateContent?key={api_key}"
    )
    
    try:
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
            text_content = resp_json['candidates'][0]['content']['parts'][0]['text']
            text = text_content.strip()
            if text.startswith("```json"): text = text[7:]
            if text.endswith("```"): text = text[:-3]
            
            data = json.loads(text.strip())
            
            if isinstance(data, list):
                steps = data
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

    if guide_image_mode == "single":
        # --- Single Image Mode: Generate one infographic using NanoBanana Pro ---
        if progress_callback: await progress_callback("🎨 NanoBanana Pro で栽培ガイド画像を生成中...")
        
        info(f"Using SINGLE image mode (NanoBanana Pro) for guide: {guide_title}")
        
        single_image_b64 = await asyncio.to_thread(
            _generate_single_guide_image,
            guide_title,
            steps,
            api_key,
            headers
        )
        
        # Build final steps with text only, attach single image to first step
        final_steps = []
        for i, step in enumerate(steps):
            step_data = {
                "title": step.get('step_title', step.get('title', f'Step {i+1}')),
                "description": step.get('description', ''),
            }
            if i == 0 and single_image_b64:
                step_data["image_base64"] = single_image_b64
            final_steps.append(step_data)
        
        has_image = single_image_b64 is not None
        info(f"Single image guide complete: {len(final_steps)} steps, image={'yes' if has_image else 'no'}")
        
        if progress_callback: await progress_callback("✨ Guide generation complete!")
        return guide_title, guide_description, final_steps
    
    else:
        # --- Per-Step Image Mode (Original): Generate image for each step ---
        if progress_callback: await progress_callback(f"🎨 Generating illustrations for {len(steps)} steps...")

        # 2. Generate Images based on selected model
        if image_model == "flash":
            primary_img_model_id = "gemini-2.5-flash-image"
            fallback_img_model_id = "gemini-3-pro-image-preview"  # Fallback to Pro if Flash fails
            model_name_for_log = "Gemini 2.5 Flash Image (with Pro fallback)"
        else:
            # Default to pro
            primary_img_model_id = "gemini-3-pro-image-preview"
            fallback_img_model_id = "gemini-2.5-flash-image"
            model_name_for_log = "Gemini 3 Pro Image (with Flash fallback)"
            
        info(f"Using {model_name_for_log} for image generation")
        
        primary_img_url = (
            f"https://{API_ENDPOINT}/v1/publishers/google/"
            f"models/{primary_img_model_id}:generateContent?key={api_key}"
        )
        fallback_img_url = None
        if fallback_img_model_id:
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
