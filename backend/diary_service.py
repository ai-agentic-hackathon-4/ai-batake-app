"""
Diary Service - Auto-generates daily growing diaries from agent and sensor logs.

This service collects data from the edge agent execution logs and sensor readings,
then uses Gemini AI to generate a natural language diary entry summarizing the day's
farming activities and plant status.
"""

import os
import logging
import json
import time
import requests
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

import google.auth
import google.auth.transport.requests

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Try importing db functions
try:
    from .db import db, get_agent_execution_logs, get_sensor_history, get_latest_vegetable
except ImportError:
    from db import db, get_agent_execution_logs, get_sensor_history, get_latest_vegetable


def get_auth_headers():
    """Get authentication headers for Gemini API."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("SEED_GUIDE_GEMINI_KEY")
    if api_key:
        return {"Content-Type": "application/json"}, f"?key={api_key}"
    
    # Try ADC (Application Default Credentials)
    try:
        creds, project = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        auth_req = google.auth.transport.requests.Request()
        creds.refresh(auth_req)
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {creds.token}"
        }, ""
    except Exception as e:
        logging.warning(f"Failed to get ADC credentials: {e}")
        return {"Content-Type": "application/json"}, ""


def request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    """Make HTTP request with exponential backoff retry for rate limiting."""
    max_retries = 5
    backoff_factor = 2
    
    for i in range(max_retries):
        try:
            response = requests.request(method, url, **kwargs)
            if response.status_code == 429:
                sleep_time = backoff_factor ** i
                logging.warning(f"429 Too Many Requests. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
                continue
            return response
        except requests.exceptions.RequestException as e:
            logging.warning(f"Request failed: {e}. Retrying...")
            time.sleep(backoff_factor ** i)
    
    # Final attempt
    return requests.request(method, url, **kwargs)


def get_agent_logs_for_date(target_date: date) -> List[Dict]:
    """
    Get agent execution logs for a specific date.
    
    Args:
        target_date: The date to retrieve logs for.
        
    Returns:
        List of agent log entries for the specified date.
    """
    if db is None:
        logging.warning("Database not available")
        return []
    
    try:
        # Calculate start and end timestamps for the day
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())
        
        # Get all logs and filter by date
        # Note: We use ISO format strings for comparison as stored in Firestore
        all_logs = get_agent_execution_logs(limit=1000)  # Get a large batch
        
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


def get_sensor_data_for_date(target_date: date) -> List[Dict]:
    """
    Get sensor data for a specific date.
    
    Args:
        target_date: The date to retrieve sensor data for.
        
    Returns:
        List of sensor readings for the specified date.
    """
    if db is None:
        logging.warning("Database not available")
        return []
    
    try:
        # Calculate hours since midnight
        now = datetime.now()
        date_diff = now.date() - target_date
        hours_back = date_diff.days * 24 + 24  # Go back to start of target date
        
        # Get sensor history
        all_data = get_sensor_history(hours=hours_back + 24)
        
        # Filter to only the target date
        filtered_data = []
        for reading in all_data:
            unix_ts = reading.get("unix_timestamp")
            if unix_ts:
                reading_date = datetime.fromtimestamp(unix_ts).date()
                if reading_date == target_date:
                    filtered_data.append(reading)
        
        return filtered_data
        
    except Exception as e:
        logging.error(f"Error fetching sensor data for date: {e}")
        return []


def get_current_vegetable() -> Optional[Dict]:
    """
    Get information about the currently growing vegetable.
    
    Returns:
        Dictionary with vegetable information or None.
    """
    try:
        return get_latest_vegetable()
    except Exception as e:
        logging.error(f"Error fetching current vegetable: {e}")
        return None


def get_plant_image_for_date(target_date: date) -> Optional[str]:
    """
    Get the plant camera image URL for a specific date.
    
    Args:
        target_date: The date to get the image for.
        
    Returns:
        URL string or None if no image available.
    """
    # For now, return None - can be extended to fetch from GCS
    return None


def calculate_statistics(sensor_data: List[Dict]) -> Dict:
    """
    Calculate statistics from sensor data.
    
    Args:
        sensor_data: List of sensor readings.
        
    Returns:
        Dictionary with min/max/avg statistics for temp, humidity, soil moisture.
    """
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
    """
    Extract key events from agent execution logs.
    
    Args:
        agent_logs: List of agent log entries.
        max_events: Maximum number of events to return.
        
    Returns:
        List of key event dictionaries.
    """
    events = []
    
    for log in agent_logs:
        log_data = log.get("data", {})
        timestamp = log.get("timestamp", "")
        
        # Extract operation events
        if "operation" in log_data:
            for device, op in log_data["operation"].items():
                action = op.get("action", "") if isinstance(op, dict) else str(op)
                # Only include active operations
                if any(keyword in action for keyword in ["ON", "OFF", "起動", "停止", "開始", "終了"]):
                    events.append({
                        "time": timestamp,
                        "type": "action",
                        "device": device,
                        "action": action
                    })
        
        # Extract warnings and alerts
        comment = log_data.get("comment", "")
        if "異常" in comment or "エラー" in comment:
            events.append({
                "time": timestamp,
                "type": "alert",
                "action": comment
            })
        elif "警告" in comment or "注意" in comment:
            events.append({
                "time": timestamp,
                "type": "warning",
                "action": comment
            })
        elif comment and "action" not in [e.get("action") for e in events[-3:] if e]:
            # Include other comments as info events (avoid duplicates)
            events.append({
                "time": timestamp,
                "type": "info",
                "action": comment[:100]  # Truncate long comments
            })
    
    return events[:max_events]


def build_diary_prompt(
    date_str: str,
    statistics: Dict,
    events: List[Dict],
    vegetable_info: Optional[Dict]
) -> str:
    """
    Build the prompt for AI diary generation.
    
    Args:
        date_str: The date string (ISO format).
        statistics: Calculated statistics dictionary.
        events: List of key events.
        vegetable_info: Information about the growing vegetable.
        
    Returns:
        Prompt string for the AI.
    """
    veg_name = vegetable_info.get("name", "野菜") if vegetable_info else "野菜"
    
    # Build event summary
    event_summary = "\n".join([
        f"- {e.get('time', 'N/A')}: {e.get('device', '')} {e['action']}"
        for e in events[:10]
    ])
    
    prompt = f"""あなたは植物栽培の専門家です。以下のデータをもとに、育成日記を作成してください。

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
    
    return prompt


def parse_diary_response(text: str) -> Dict[str, str]:
    """
    Parse the AI response into structured diary content.
    
    Args:
        text: Raw text response from the AI.
        
    Returns:
        Dictionary with summary, observations, and recommendations.
    """
    try:
        # Extract JSON from markdown code block if present
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
        logging.error(f"Failed to parse AI response: {e}")
        # Fallback: use text as summary
        return {
            "summary": text[:300] if text else "データを分析中です。",
            "observations": "データを分析中です。",
            "recommendations": "引き続き観察を続けます。"
        }


async def generate_diary_with_ai(
    date_str: str,
    statistics: Dict,
    events: List[Dict],
    vegetable_info: Optional[Dict]
) -> Dict[str, str]:
    """
    Generate diary content using Gemini AI.
    
    Args:
        date_str: Date string for the diary.
        statistics: Calculated statistics.
        events: Key events list.
        vegetable_info: Vegetable information.
        
    Returns:
        Dictionary with AI-generated diary content.
    """
    headers, query_param = get_auth_headers()
    
    if not query_param and "Authorization" not in headers:
        logging.error("No API key or credentials available for Gemini API")
        return {
            "summary": "AIサービスが利用できません。",
            "observations": "データ収集は正常に完了しました。",
            "recommendations": "手動で観察記録を追加してください。"
        }
    
    # Build prompt
    prompt = build_diary_prompt(date_str, statistics, events, vegetable_info)
    
    # Gemini API call
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent{query_param}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.9,
            "maxOutputTokens": 1000
        }
    }
    
    try:
        response = request_with_retry("POST", url, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            logging.error(f"Gemini API error: {response.status_code} - {response.text}")
            return {
                "summary": f"AI生成エラー (HTTP {response.status_code})",
                "observations": "エラーが発生しました。",
                "recommendations": "再度お試しください。"
            }
        
        result = response.json()
        generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
        
        return parse_diary_response(generated_text)
        
    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        return {
            "summary": "AI生成中にエラーが発生しました。",
            "observations": "データ収集は正常に完了しました。",
            "recommendations": "手動で観察記録を追加してください。"
        }


async def collect_daily_data(target_date: date) -> Dict[str, Any]:
    """
    Collect all data needed for diary generation.
    
    Args:
        target_date: The date to collect data for.
        
    Returns:
        Dictionary containing all collected data.
    """
    return {
        "date": target_date.isoformat(),
        "agent_logs": get_agent_logs_for_date(target_date),
        "sensor_data": get_sensor_data_for_date(target_date),
        "vegetable": get_current_vegetable(),
        "plant_image": get_plant_image_for_date(target_date)
    }


async def init_diary_status(diary_id: str):
    """Initialize diary generation status in Firestore."""
    if db is None:
        return
    
    try:
        db.collection("growing_diaries").document(diary_id).set({
            "generation_status": "processing",
            "created_at": datetime.now()
        })
    except Exception as e:
        logging.error(f"Error initializing diary status: {e}")


async def save_diary(diary_id: str, data: Dict):
    """Save the generated diary to Firestore."""
    if db is None:
        logging.warning("DB not available, cannot save diary")
        return
    
    try:
        db.collection("growing_diaries").document(diary_id).set(data)
        logging.info(f"Diary saved: {diary_id}")
    except Exception as e:
        logging.error(f"Error saving diary: {e}")


async def mark_diary_failed(diary_id: str, error: str):
    """Mark diary generation as failed."""
    if db is None:
        return
    
    try:
        db.collection("growing_diaries").document(diary_id).update({
            "generation_status": "failed",
            "error_message": error,
            "updated_at": datetime.now()
        })
    except Exception as e:
        logging.error(f"Error marking diary failed: {e}")


async def process_daily_diary(target_date_str: str):
    """
    Main diary generation process.
    
    Args:
        target_date_str: ISO format date string for the diary.
    """
    start_time = time.time()
    diary_id = target_date_str
    
    try:
        target_date = date.fromisoformat(target_date_str)
        
        # Initialize status
        logging.info(f"Starting diary generation for {target_date_str}...")
        await init_diary_status(diary_id)
        
        # 1. Collect data
        logging.info(f"Collecting data for {target_date_str}...")
        daily_data = await collect_daily_data(target_date)
        
        # 2. Calculate statistics
        statistics = calculate_statistics(daily_data["sensor_data"])
        events = extract_key_events(daily_data["agent_logs"])
        
        logging.info(f"Collected {len(daily_data['sensor_data'])} sensor readings and {len(daily_data['agent_logs'])} agent logs")
        
        # 3. Generate AI diary
        logging.info(f"Generating diary with AI for {target_date_str}...")
        ai_content = await generate_diary_with_ai(
            target_date_str,
            statistics,
            events,
            daily_data["vegetable"]
        )
        
        # 4. Save to Firestore
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
        
        await save_diary(diary_id, diary_data)
        
        logging.info(f"Diary generated successfully for {target_date_str} in {generation_time_ms}ms")
        
    except Exception as e:
        logging.error(f"Failed to generate diary for {target_date_str}: {e}")
        await mark_diary_failed(diary_id, str(e))


def get_all_diaries(limit: int = 30, offset: int = 0) -> List[Dict]:
    """
    Get all diaries from Firestore.
    
    Args:
        limit: Maximum number of diaries to return.
        offset: Number of diaries to skip.
        
    Returns:
        List of diary dictionaries.
    """
    if db is None:
        return []
    
    try:
        from google.cloud import firestore as fs
        
        query = db.collection("growing_diaries") \
            .where("generation_status", "==", "completed") \
            .order_by("date", direction=fs.Query.DESCENDING) \
            .limit(limit)
        
        if offset > 0:
            query = query.offset(offset)
        
        docs = query.stream()
        
        diaries = []
        for doc in docs:
            diary = doc.to_dict()
            diary['id'] = doc.id
            # Convert datetime objects to ISO strings
            if 'created_at' in diary and hasattr(diary['created_at'], 'isoformat'):
                diary['created_at'] = diary['created_at'].isoformat()
            diaries.append(diary)
        
        return diaries
        
    except Exception as e:
        logging.error(f"Error fetching diaries: {e}")
        return []


def get_diary_by_date(date_str: str) -> Optional[Dict]:
    """
    Get a specific diary by date.
    
    Args:
        date_str: ISO format date string.
        
    Returns:
        Diary dictionary or None if not found.
    """
    if db is None:
        return None
    
    try:
        doc = db.collection("growing_diaries").document(date_str).get()
        
        if not doc.exists:
            return None
        
        diary = doc.to_dict()
        diary['id'] = doc.id
        
        # Convert datetime objects to ISO strings
        if 'created_at' in diary and hasattr(diary['created_at'], 'isoformat'):
            diary['created_at'] = diary['created_at'].isoformat()
        
        return diary
        
    except Exception as e:
        logging.error(f"Error fetching diary: {e}")
        return None
