import os
import logging
import json
import time
import httpx
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

import google.auth
import google.auth.transport.requests

# Setup logging
try:
    from .logger import info, debug, error, warning
except ImportError:
    from logger import info, debug, error, warning

try:
    from .db import db, get_agent_execution_logs, get_sensor_history, get_latest_vegetable, get_edge_agent_config
    from .image_service import generate_picture_diary
except ImportError:
    from db import db, get_agent_execution_logs, get_sensor_history, get_latest_vegetable, get_edge_agent_config
    from image_service import generate_picture_diary


async def get_auth_headers_async():
    """Get authentication headers for Gemini API."""
    api_key = os.environ.get("SEED_GUIDE_GEMINI_KEY")
    if api_key:
        return {"Content-Type": "application/json"}, f"?key={api_key}"
    
    logging.warning("Please set SEED_GUIDE_GEMINI_KEY.")
    return {"Content-Type": "application/json"}, ""


async def request_with_retry_async(method: str, url: str, **kwargs) -> httpx.Response:
    """Make HTTP request with exponential backoff retry for rate limiting using httpx."""
    max_retries = 5
    backoff_factor = 2
    
    async with httpx.AsyncClient() as client:
        for i in range(max_retries):
            try:
                info(f"API Request attempt {i+1}/{max_retries}: {method} {url[:50]}...")
                response = await client.request(method, url, **kwargs)
                info(f"API Response status: {response.status_code}")
                
                if response.status_code == 429:
                    sleep_time = backoff_factor ** i
                    warning(f"429 Too Many Requests. Retrying in {sleep_time}s...")
                    await asyncio.sleep(sleep_time)
                    continue
                return response
            except httpx.RequestError as e:
                warning(f"Request failed: {e}. Retrying...")
                await asyncio.sleep(backoff_factor ** i)
        
        # Final attempt
        info("Final API Request attempt...")
        return await client.request(method, url, **kwargs)


async def get_agent_logs_for_date_async(target_date: date) -> List[Dict]:
    """Get agent execution logs for a specific date (async)."""
    if db is None:
        logging.warning("Database not available")
        return []
    
    try:
        # Note: get_agent_execution_logs is currently sync in db.py? 
        # Actually in main.py it's imported from db.py
        # Let's assume we use asyncio.to_thread if it's sync, or if db.py is updated.
        # Based on my view of main.py, it says "Firestore Client (Async)" but imports sync functions?
        # Re-checking db.py: it uses 'firestore.Client' (sync). 
        # Re-checking main.py: line 144 'db = firestore.AsyncClient(...)'.
        # This is a bit mixed. I will use asyncio.to_thread for now for safety or direct calls if async.
        
        all_logs = await asyncio.to_thread(get_agent_execution_logs, limit=1000)
        
        filtered_logs = []
        for log in all_logs:
            timestamp_str = log.get("timestamp", "")
            if timestamp_str:
                try:
                    log_date = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")).date()
                    if log_date == target_date:
                        filtered_logs.append(log)
                except (ValueError, TypeError):
                    continue
        
        return filtered_logs
    except Exception as e:
        logging.error(f"Error fetching agent logs for date: {e}")
        return []


async def get_sensor_data_for_date_async(target_date: date) -> List[Dict]:
    """Get sensor data for a specific date (async)."""
    if db is None:
        logging.warning("Database not available")
        return []
    
    try:
        # Calculate hours back to the start of the target date
        now = datetime.now()
        start_of_day = datetime.combine(target_date, datetime.min.time())
        hours_back_to_start = int((now - start_of_day).total_seconds() / 3600) + 1
        
        # Buffer to ensure we get everything
        info(f"Fetching sensor history for {target_date} (hours back: {hours_back_to_start})")
        all_data = await asyncio.to_thread(get_sensor_history, hours=max(hours_back_to_start, 24))
        
        filtered_data = []
        for reading in all_data:
            unix_ts = reading.get("unix_timestamp")
            if unix_ts:
                reading_date = datetime.fromtimestamp(unix_ts).date()
                if reading_date == target_date:
                    filtered_data.append(reading)
        
        info(f"Retrieved {len(filtered_data)} sensor records for {target_date}")
        return filtered_data
    except Exception as e:
        logging.error(f"Error fetching sensor data for date: {e}")
        return []


async def get_current_vegetable_async() -> Optional[Dict]:
    """Get information about the currently growing vegetable (async)."""
    try:
        # First try to get from edge agent config (active vegetable)
        config = await asyncio.to_thread(get_edge_agent_config)
        if config and config.get("vegetable_name"):
            # Return a dict that mimics the vegetable object, at least with the name
            # We might miss the ID if we don't look it up, but for the diary prompt, name is key.
            return {
                "name": config.get("vegetable_name"),
                "id": None, # ID is unknown without lookup, but acceptable for diary content
                "status": "active_in_config"
            }

        return await asyncio.to_thread(get_latest_vegetable)
    except Exception as e:
        logging.error(f"Error fetching current vegetable: {e}")
        return None


async def get_plant_image_for_date_async(target_date: date) -> Optional[str]:
    """Get the plant camera image URL for a specific date (async)."""
    return None


async def get_selected_character_async() -> Optional[Dict]:
    """Get the selected character from Firestore (growing_diaries/Character) (async)."""
    if db is None:
        logging.warning("Database not available for character lookup")
        return None
    try:
        doc = await asyncio.to_thread(
            lambda: db.collection("growing_diaries").document("Character").get()
        )
        if doc.exists:
            data = doc.to_dict()
            info(f"Selected character found: {data.get('name')}")
            return data
        else:
            info("No selected character found in growing_diaries/Character")
            return None
    except Exception as e:
        logging.error(f"Error fetching selected character: {e}")
        return None


def calculate_statistics(sensor_data: List[Dict]) -> Dict:
    """Calculate statistics from sensor data."""
    if not sensor_data:
        return {
            "temperature": {"min": 0, "max": 0, "avg": 0},
            "humidity": {"min": 0, "max": 0, "avg": 0},
            "soil_moisture": {"min": 0, "max": 0, "avg": 0},
        }
    
    temps = [d.get("temperature", 0) for d in sensor_data if d.get("temperature") is not None]
    humids = [d.get("humidity", 0) for d in sensor_data if d.get("humidity") is not None]
    soils = [d.get("soil_moisture", 0) for d in sensor_data if d.get("soil_moisture") is not None]
    
    return {
        "temperature": {
            "min": round(min(temps), 1) if temps else 0,
            "max": round(max(temps), 1) if temps else 0,
            "avg": round(sum(temps) / len(temps), 1) if temps else 0,
        },
        "humidity": {
            "min": round(min(humids), 1) if humids else 0,
            "max": round(max(humids), 1) if humids else 0,
            "avg": round(sum(humids) / len(humids), 1) if humids else 0,
        },
        "soil_moisture": {
            "min": round(min(soils), 1) if soils else 0,
            "max": round(max(soils), 1) if soils else 0,
            "avg": round(sum(soils) / len(soils), 1) if soils else 0,
        },
    }


def extract_key_events(agent_logs: List[Dict], max_events: int = 10) -> List[Dict]:
    """Extract key events from agent execution logs."""
    events = []
    
    for log in agent_logs:
        log_data = log.get("data", {})
        timestamp = log.get("timestamp", "")
        
        if "operation" in log_data:
            for device, op in log_data["operation"].items():
                action = op.get("action", "") if isinstance(op, dict) else str(op)
                if any(keyword in action for keyword in ["ON", "OFF", "起動", "停止", "開始", "終了"]):
                    events.append({
                        "time": timestamp,
                        "type": "action",
                        "device": device,
                        "action": action
                    })
        
        comment = log_data.get("comment", "")
        if "異常" in comment or "エラー" in comment:
            events.append({"time": timestamp, "type": "alert", "action": comment})
        elif "警告" in comment or "注意" in comment:
            events.append({"time": timestamp, "type": "warning", "action": comment})
        elif comment and comment not in [e.get("action") for e in events[-3:] if e]:
            events.append({"time": timestamp, "type": "info", "action": comment[:100]})
    
    return events[:max_events]


def build_diary_prompt(date_str: str, statistics: Dict, events: List[Dict], vegetable_info: Optional[Dict], character_info: Optional[Dict] = None) -> str:
    """Build the prompt for AI diary generation."""
    veg_name = vegetable_info.get("name", "野菜") if vegetable_info else "野菜"
    event_summary = "\n".join([f"- {e.get('time', 'N/A')}: {e.get('device', '')} {e['action']}" for e in events[:10]])
    
    # Build character instruction
    char_name = None
    char_personality = None
    if character_info:
        char_name = character_info.get("name")
        char_personality = character_info.get("personality")
    
    if char_name and char_personality:
        role_instruction = f"""あなたは「{char_name}」という名前の{veg_name}のキャラクターです。
性格は「{char_personality}」です。
このキャラクターになりきって、一人称で育成日記を書いてください。
キャラクターの性格や口調を反映した、親しみやすい文体で書いてください。"""
    elif char_name:
        role_instruction = f"""あなたは「{char_name}」という名前の{veg_name}のキャラクターです。
このキャラクターになりきって、一人称で親しみやすい育成日記を書いてください。"""
    else:
        role_instruction = "あなたは植物栽培の専門家です。以下のデータをもとに、育成日記を作成してください。"

    return f"""{role_instruction}

【日付】
{date_str}

【育成中の植物】
{veg_name}

【環境データ統計】
温度: 最低 {statistics['temperature']['min']}°C / 最高 {statistics['temperature']['max']}°C / 平均 {statistics['temperature']['avg']}°C
湿度: 最低 {statistics['humidity']['min']}% / 最高 {statistics['humidity']['max']}% / 平均 {statistics['humidity']['avg']}%
土壌水分: 最低 {statistics['soil_moisture']['min']}% / 最高 {statistics['soil_moisture']['max']}% / 平均 {statistics['soil_moisture']['avg']}%

【主要イベント】
{event_summary if event_summary else "特になし"}

以下の3つのセクションに分けて日記を作成してください：

1. **今日の要約** (200-300文字)
   - 1日の環境状態と全体的な様子を要約
   - データから読み取れる特徴的な点を記載

2. **成長観察** (100-200文字)
   - 植物の状態について推測される観察
   - 環境データから判断できる成長の進捗

3. **明日への提案** (100-150文字)
   - データに基づく改善提案
   - 次のステップや注意点

出力フォーマット（必ず以下のJSON形式で返してください）：
```json
{{
  "summary": "今日の要約文...",
  "observations": "成長観察文...",
  "recommendations": "明日への提案文..."
}}
```

日記は親しみやすく、専門的すぎない文体で書いてください。
"""


def parse_diary_response(text: str) -> Dict[str, str]:
    """Parse the AI response into structured diary content."""
    try:
        clean_text = text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0]
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0]
        
        parsed = json.loads(clean_text.strip())
        return {
            "summary": parsed.get("summary", ""),
            "observations": parsed.get("observations", ""),
            "recommendations": parsed.get("recommendations", "")
        }
    except Exception as e:
        error(f"Failed to parse AI response: {e}")
        return {
            "summary": text[:300] if text else "データを分析中です。",
            "observations": "データを分析中です。",
            "recommendations": "引き続き観察を続けます。"
        }


async def generate_diary_with_ai_async(
    date_str: str,
    statistics: Dict,
    events: List[Dict],
    vegetable_info: Optional[Dict],
    character_info: Optional[Dict] = None
) -> Dict[str, str]:
    """Generate diary content using Gemini AI (async)."""
    api_key = os.environ.get("SEED_GUIDE_GEMINI_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logging.error("No API Key found")
        return {
            "summary": "AIサービスが利用できません (API Key Missing)。",
            "observations": "データ収集は正常に完了しました。",
            "recommendations": "手動で観察記録を追加してください。"
        }
    
    headers = {"Content-Type": "application/json"}
    prompt = build_diary_prompt(date_str, statistics, events, vegetable_info, character_info)
    url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/gemini-3-flash-preview:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.9,
            "maxOutputTokens": 4000,
            "responseMimeType": "application/json"
        }
    }
    
    try:
        response = await request_with_retry_async("POST", url, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            error(f"Gemini API error: {response.status_code} - {response.text}")
            return {"summary": f"AI生成エラー (HTTP {response.status_code})", "observations": "エラーが発生しました。", "recommendations": "再度お試しください。"}
        
        result = response.json()
        generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
        return parse_diary_response(generated_text)
    except Exception as e:
        error(f"Error calling Gemini API: {e}")
        return {"summary": "AI生成中にエラーが発生しました。", "observations": "データ収集は正常に完了しました。", "recommendations": "手動で観察記録を追加してください。"}


async def collect_daily_data_async(target_date: date, progress_callback=None) -> Dict[str, Any]:
    """Collect all data needed for diary generation (async)."""
    async def update(msg: str):
        if progress_callback:
            if asyncio.iscoroutinefunction(progress_callback):
                await progress_callback(msg)
            else:
                progress_callback(msg)

    await update("ログを取得中...")
    agent_logs = await get_agent_logs_for_date_async(target_date)
    
    await update("センサーデータを確認中...")
    sensor_data = await get_sensor_data_for_date_async(target_date)
    
    await update("植物情報を取得中...")
    vegetable = await get_current_vegetable_async()
    
    await update("キャラクター情報を取得中...")
    character = await get_selected_character_async()
    
    plant_image = await get_plant_image_for_date_async(target_date)
    
    return {
        "date": target_date.isoformat(),
        "agent_logs": agent_logs,
        "sensor_data": sensor_data,
        "vegetable": vegetable,
        "character": character,
        "plant_image": plant_image
    }


async def init_diary_status_async(diary_id: str):
    """Initialize diary generation status in Firestore (async)."""
    if db is None: return
    try:
        await asyncio.to_thread(db.collection("growing_diaries").document(diary_id).set, {
            "generation_status": "processing",
            "created_at": datetime.now()
        })
    except Exception as e:
        logging.error(f"Error initializing diary status: {e}")


async def save_diary_async(diary_id: str, data: Dict):
    """Save the generated diary to Firestore (async)."""
    if db is None: return
    try:
        await asyncio.to_thread(db.collection("growing_diaries").document(diary_id).set, data)
        info(f"Diary saved: {diary_id}")
    except Exception as e:
        error(f"Error saving diary: {e}")


async def mark_diary_failed_async(diary_id: str, error_msg: str):
    """Mark diary generation as failed (async)."""
    if db is None: return
    try:
        await asyncio.to_thread(db.collection("growing_diaries").document(diary_id).update, {
            "generation_status": "failed",
            "error_message": error_msg,
            "updated_at": datetime.now()
        })
    except Exception as e:
        logging.error(f"Error marking diary failed: {e}")


async def process_daily_diary(target_date_str: str, progress_callback=None):
    """Main diary generation process (async)."""
    import asyncio
    async def update_progress(msg: str):
        if progress_callback:
            if asyncio.iscoroutinefunction(progress_callback):
                await progress_callback(msg)
            else:
                progress_callback(msg)

    start_time = time.time()
    diary_id = target_date_str
    
    try:
        target_date = date.fromisoformat(target_date_str)
        info(f"Starting diary generation for {target_date_str}...")
        
        await update_progress("データ収集中...")
        await init_diary_status_async(diary_id)
        
        daily_data = await collect_daily_data_async(target_date, progress_callback)
        
        await update_progress("生育状況を分析中...")
        statistics = calculate_statistics(daily_data["sensor_data"])
        events = extract_key_events(daily_data["agent_logs"])
        
        await update_progress("成長記録を執筆中...")
        ai_content = await generate_diary_with_ai_async(
            target_date_str, statistics, events, daily_data["vegetable"], daily_data.get("character")
        )
        
        try:
            await update_progress("絵日記のイラストを生成中...")
            # Note: generate_picture_diary is sync, using to_thread
            generated_image_url = await asyncio.to_thread(generate_picture_diary, target_date_str, ai_content["summary"])
            if generated_image_url:
                daily_data["plant_image"] = generated_image_url
        except Exception as img_err:
            error(f"Failed to generate picture diary image: {img_err}")
        
        await update_progress("保存しています...")
        generation_time_ms = int((time.time() - start_time) * 1000)
        
        diary_data = {
            "date": target_date_str,
            "created_at": datetime.now(),
            "vegetable_id": daily_data["vegetable"].get("id") if daily_data["vegetable"] else None,
            "vegetable_name": daily_data["vegetable"].get("name") if daily_data["vegetable"] else None,
            "statistics": statistics,
            "events": events,
            "ai_summary": ai_content["summary"],
            "observations": ai_content["observations"],
            "recommendations": ai_content["recommendations"],
            "plant_image_url": daily_data["plant_image"],
            "generation_status": "completed",
            "generation_time_ms": generation_time_ms,
            "agent_actions_count": len(daily_data["agent_logs"])
        }
        
        await save_diary_async(diary_id, diary_data)
        info(f"Diary generated successfully for {target_date_str} in {generation_time_ms}ms")
        
    except Exception as e:
        error(f"Failed to generate diary for {target_date_str}: {e}")
        await mark_diary_failed_async(diary_id, str(e))


def get_all_diaries(limit: int = 30, offset: int = 0) -> List[Dict]:
    """Get all diaries from Firestore (sync)."""
    if db is None: return []
    try:
        query = db.collection("growing_diaries").where("generation_status", "==", "completed").limit(limit)
        if offset > 0: query = query.offset(offset)
        docs = query.stream()
        diaries = []
        for doc in docs:
            diary = doc.to_dict()
            diary['id'] = doc.id
            if 'created_at' in diary and hasattr(diary['created_at'], 'isoformat'):
                diary['created_at'] = diary['created_at'].isoformat()
            diaries.append(diary)
        diaries.sort(key=lambda x: x.get('date', ''), reverse=True)
        return diaries
    except Exception as e:
        error(f"Error fetching diaries: {e}")
        return []


def get_diary_by_date(date_str: str) -> Optional[Dict]:
    """Get a specific diary by date (sync)."""
    if db is None: return None
    try:
        doc = db.collection("growing_diaries").document(date_str).get()
        if not doc.exists: return None
        diary = doc.to_dict()
        diary['id'] = doc.id
        if 'created_at' in diary and hasattr(diary['created_at'], 'isoformat'):
            diary['created_at'] = diary['created_at'].isoformat()
        return diary
    except Exception as e:
        logging.error(f"Error fetching diary: {e}")
        return None
