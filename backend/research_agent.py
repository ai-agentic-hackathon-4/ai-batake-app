import os
import json
import time
import requests
import base64

import google.auth
import google.auth.transport.requests

# 構造化ロガーモジュールのインポート
try:
    from .logger import get_logger, info, debug, warning, error
except ImportError:
    from logger import get_logger, info, debug, warning, error

# ロガーの初期化
logger = get_logger()

# 認証ヘッダーを取得するヘルパー関数
# 環境変数 GEMINI_API_KEY があればそれを使用し、なければ ADC (Application Default Credentials) を試行します。
def get_auth_headers():
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        debug("Using GEMINI_API_KEY for authentication")
        return {"Content-Type": "application/json"}, f"?key={api_key}"
    
    # ADC (Application Default Credentials) を試行
    try:
        debug("Trying ADC for authentication")
        creds, project = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        auth_req = google.auth.transport.requests.Request()
        creds.refresh(auth_req)
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {creds.token}"
        }, ""
    except Exception as e:
        warning(f"Failed to get ADC credentials: {e}")
        return {"Content-Type": "application/json"}, ""

def request_with_retry(method, url, **kwargs):
    """
    リクエストを再試行するラッパー関数。
    APIレート制限 (429) やサーバーエラー (5xx) の場合に、指数バックオフ (exponential backoff) を用いて再試行します。
    """
    max_retries = 5
    backoff_factor = 2
    
    for i in range(max_retries):
        try:
            response = requests.request(method, url, **kwargs)
            
            # 429 (Too Many Requests) および 5xx (Server Error) の場合に再試行
            if response.status_code == 429 or (500 <= response.status_code < 600):
                sleep_time = (backoff_factor ** i) + (i * 0.5)  # 線形増加/ジッターを少し追加
                if i < max_retries - 1:
                    warning(f"Request failed with status {response.status_code}. Retrying in {sleep_time}s... (attempt {i+1}/{max_retries})")
                    time.sleep(sleep_time)
                    continue
            
            return response
            
        except requests.exceptions.RequestException as e:
            sleep_time = (backoff_factor ** i)
            if i < max_retries - 1:
                warning(f"Request exception: {e}. Retrying in {sleep_time}s... (attempt {i+1}/{max_retries})")
                time.sleep(sleep_time)
            elif i == max_retries - 1:
                # 最後の試行の場合は、ループを終了させて最後のリクエストを行う
                pass

    # 最後の試行、または利用可能な場合は最後のレスポンスを返す
    try:
        info(f"[LLM] 🔄 Final retry attempt for {method} {url[:80]}...")
        return requests.request(method, url, **kwargs)
    except requests.exceptions.RequestException as e:
        # 最後の試行も例外で失敗した場合、再送出するかNoneを返すか？
        # 呼び出し元のコードはレスポンスオブジェクトを期待しているか、レスポンス使用時にエラーを発生させる。
        # しかし requests.request は例外を発生させる。
        # 安全のためにログ記録して再送出するか、エラー状態のモックレスポンスを返すべきか？
        # 標準的な requests の振る舞いとして再送出する。
        error(f"Final request attempt failed: {e}")
        raise

def analyze_seed_packet(image_bytes: bytes) -> str:
    """
    種袋の画像を分析し、野菜の名前と育て方のポイントを抽出します。
    Gemini 3 Flash (Preview) の REST API を使用して画像解析を行います。
    """
    debug(f"Analyzing seed packet image ({len(image_bytes)} bytes)")
    headers, query_param = get_auth_headers()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent{query_param}"
    
    try:
        # 画像をbase64エンコード
        b64_image = base64.b64encode(image_bytes).decode('utf-8')
        debug(f"Image encoded to base64 ({len(b64_image)} chars)")
        
        prompt_text = """
        この画像の種の袋を分析してください。
        以下の情報を抽出してjson形式で返してください。
        1. 野菜の名前 (name)
           - 読み取れた場合はその名前のみを出力してください（例：「トマト」「小松菜」）。
           - 自信がない場合でも、最も可能性が高い名前を出力してください。
           - 「不明な野菜(小松菜)」のような形式ではなく、単に「小松菜」としてください。
        2. 画像から読み取れる育て方のポイント (visible_instructions)

        もし完全に読み取れない場合は、nameを "unknown" とし、visible_instructions に「野菜の名前を読み取れませんでした。種袋の文字がはっきり見えるように、もう一度撮影してください。」と出力してください。
        """

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt_text},
                    {"inline_data": {
                        "mime_type": "image/jpeg",
                        "data": b64_image
                    }}
                ]
            }]
        }
        
        headers = {"Content-Type": "application/json"}
        
        info("[LLM] 📸 Sending seed packet image to Gemini 3 Flash for analysis")
        response = request_with_retry("POST", url, headers=headers, json=payload)
        response.raise_for_status()
        
        result_json = response.json()
        
        result_json = response.json()
        
        # レスポンスからテキストを抽出
        # 構造: candidates[0].content.parts[0].text
        try:
            text = result_json['candidates'][0]['content']['parts'][0]['text']
            info(f"[LLM] Seed packet analysis completed successfully")
            info(f"[LLM] Analysis result preview: {text[:200]}...")
            return text
        except (KeyError, IndexError):
             error(f"Unexpected response format: {result_json}")
             return '{"name": "Error", "visible_instructions": "Response parsing failed"}'

    except Exception as e:
        error(f"Error in analyze_seed_packet: {e}", exc_info=True)
        return '{"name": "不明な野菜", "visible_instructions": "API Error"}'

def extract_structured_research_data(vegetable_name: str, report_text: str, query_param: str, headers: dict, grounding_metadata: dict = None, raw_json_report: str = None) -> dict:
    """
    調査レポートから、アプリで利用しやすいJSON形式のデータを抽出します。
    """
    debug(f"Extracting structured data for {vegetable_name}")
    # Raw report logging
    info(f"[LLM] Raw report for extraction ({vegetable_name}):\n{report_text}")
    extraction_prompt = f"""
    以下の調査レポートに基づいて、野菜「{vegetable_name}」の育て方情報を抽出してJSON形式でまとめてください。
    特にsummary_promptには最適な気温、湿度、土壌水分量、水やり頻度、日照条件について数値を含めてこれだけで野菜を育てることができるほど詳しく記載してください。

    ---レポート---
    {report_text}
    -------------
    
    出力フォーマット(JSON):
    {{
        "name": "{vegetable_name}",
        "optimal_temp_range": "...",
        "optimal_humidity_range": "...",
        "soil_moisture_standard": "...",
        "watering_instructions": "...",
        "light_requirements": "...",
        "care_tips": "...",
        "summary_prompt": "..."
    }}
    """
    
    # 抽出には通常の Gemini 3 Flash を使用 (AI Studio or Vertex depending on context, but here we use the default for research_agent)
    # 既存のロジックに合わせて AI Studio (generativelanguage) を使用
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent{query_param}"
    gen_payload = {
        "contents": [{"parts": [{"text": extraction_prompt}]}],
        "generation_config": {"response_mime_type": "application/json"}
    }
    
    try:
        info(f"[LLM] 📝 Extracting structured data via Gemini 3 Flash for: {vegetable_name}")
        gen_resp = request_with_retry("POST", gen_url, headers=headers, json=gen_payload)
        gen_resp.raise_for_status()
        
        gen_data = gen_resp.json()
        extracted_text = gen_data['candidates'][0]['content']['parts'][0]['text']
        
        # Clean up markdown if present
        if "```json" in extracted_text:
            extracted_text = extracted_text.split("```json")[1].split("```")[0].strip()
        elif "```" in extracted_text:
            extracted_text = extracted_text.split("```")[1].split("```")[0].strip()
            
        result = json.loads(extracted_text)
        
        # Preserve original report (JSON or Text) and metadata
        result["raw_report"] = raw_json_report if raw_json_report else report_text
        if grounding_metadata:
            result["grounding_metadata"] = grounding_metadata
            
        debug(f"Successfully extracted research data for {vegetable_name}")
        return result
    except Exception as e:
        error(f"Failed to parse extraction result for {vegetable_name}: {e}. Text: {extracted_text if 'extracted_text' in locals() else 'N/A'}")
        # Return partial data so frontend can still show what was found
        return {
            "name": vegetable_name, 
            "raw_report": raw_json_report if raw_json_report else report_text,
            "error": f"Extraction Parsing Failed: {str(e)}"
        }

def perform_web_grounding_research(vegetable_name: str, packet_info: str) -> dict:
    """
    Vertex AI の Google Search Grounding を使用して、野菜の詳細な育て方を調査します。
    """
    debug(f"Starting Web Grounding research for: {vegetable_name}")
    
    # Web Grounding 用に特定のキーを取得
    api_key = os.environ.get("SEED_GUIDE_GEMINI_KEY")
    if not api_key:
        error("SEED_GUIDE_GEMINI_KEY not found in environment variables")
        return {"name": vegetable_name, "error": "API Key missing"}

    query_param = f"?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    # 検証済みのエンドポイントとモデル
    model_id = "gemini-3-flash-preview"
    url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{model_id}:generateContent{query_param}"

    research_topic = f"「{vegetable_name}」の育て方について、WEBの情報調査を行い家庭菜園や農業の専門的な情報を詳しく調べてください。特に最適な気温、湿度、土壌水分量、水やり頻度、日照条件について数値を含めて調査してください。"
    if packet_info:
        research_topic += f" また、種の袋には以下の情報がありました: {packet_info}"

    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"text": research_topic}]
        }],
        "tools": [
            {"googleSearch": {}}
        ]
    }

    try:
        info(f"[LLM] 📡 Sending Web Grounding request (gemini-3-flash-preview) for: {vegetable_name}")
        response = request_with_retry("POST", url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                error(f"No candidates in response: {data}")
                return {"name": vegetable_name, "error": "Empty response from AI"}
            
            grounding_text = candidates[0]['content']['parts'][0]['text']
            grounding_metadata = candidates[0].get("groundingMetadata")
            
            # Prepare full JSON response for logging/storage
            full_response_json = json.dumps(data, ensure_ascii=False)
            
            # Log raw response for traceability
            info(f"[LLM] Full Web Grounding Response for {vegetable_name}: {full_response_json}")
            
            debug(f"Web Grounding research completed for {vegetable_name}")
            
            # AI Studio のクエリパラメータを使用して構造化データを抽出 (互換性のため)
            _, studio_query_param = get_auth_headers()
            # 保存用に生レポートテキトではなく JSON 全体を渡す
            return extract_structured_research_data(vegetable_name, grounding_text, studio_query_param, headers, grounding_metadata=grounding_metadata, raw_json_report=full_response_json)
            
        except (KeyError, IndexError) as e:
            error(f"Failed to parse Web Grounding response: {e}, Data: {data}")
            return {"name": vegetable_name, "error": "Response parsing failed"}

    except Exception as e:
        error(f"Error in perform_web_grounding_research for {vegetable_name}: {e}", exc_info=True)
        return {"name": vegetable_name, "error": str(e)}

def perform_deep_research(vegetable_name: str, packet_info: str) -> dict:
    """
    Deep Research Agent の REST API を使用して、野菜の詳細な育て方を調査します。
    """
    debug(f"Starting deep research for: {vegetable_name}")
    headers, query_param = get_auth_headers()

    research_topic = f"「{vegetable_name}」の育て方について、家庭菜園や農業の専門的な情報を詳しく調べてください。特に最適な気温、湿度、土壌水分量、水やり頻度、日照条件について数値を含めて調査してください。"
    if packet_info:
        research_topic += f" また、種の袋には以下の情報がありました: {packet_info}"

    try:
        # 1. インタラクションの開始 (POST)
        base_url = "https://generativelanguage.googleapis.com/v1beta/interactions"
        start_url = f"{base_url}{query_param}"
        
        payload = {
            "input": research_topic,
            "agent": "deep-research-pro-preview-12-2025",
            "background": True
        }
        
        info(f"[LLM] 🔬 Starting Deep Research interaction (deep-research-pro-preview) for: {vegetable_name}")
        response = request_with_retry("POST", start_url, headers=headers, json=payload)
        
        if response.status_code != 200:
             error(f"Deep Research start failed: {response.text}")
             return {"name": vegetable_name, "error": f"Start failed: {response.status_code} - {response.text}"}
             
        interaction_data = response.json()
        interaction_name = interaction_data.get("name")
        if not interaction_name:
            interaction_id = interaction_data.get("id")
            if interaction_id:
                interaction_name = f"interactions/{interaction_id}"

        debug(f"Research started: {interaction_name}")
        
        # 2. ポーリング (GET)
        poll_url = f"https://generativelanguage.googleapis.com/v1beta/{interaction_name}{query_param}"
        
        max_retries = 180
        final_text = ""
        
        for i in range(max_retries):
            poll_resp = request_with_retry("GET", poll_url, headers=headers)
            if poll_resp.status_code != 200:
                if poll_resp.status_code == 404:
                     return {"name": vegetable_name, "error": "Research failed: Interaction not found (404)"}
                time.sleep(10)
                continue
                
            data = poll_resp.json()
            status = data.get("status")
            
            if status == "completed":
                outputs = data.get("outputs", [])
                if outputs:
                    final_text = outputs[-1].get("text", "")
                    debug(f"Research completed for {vegetable_name}")
                break
            elif status == "failed":
                error_msg = data.get('error')
                return {"name": vegetable_name, "error": f"Research failed: {error_msg}"}
                
            time.sleep(10)
        else:
            return {"name": vegetable_name, "error": "Research Timeout"}

        # 3. データ抽出 (REST)
        # Deep Research の全レスポンスデータを JSON 文字列として保持
        full_json = json.dumps(data, ensure_ascii=False)
        return extract_structured_research_data(vegetable_name, final_text, query_param, headers, raw_json_report=full_json)

    except Exception as e:
        error(f"Error in perform_deep_research for {vegetable_name}: {e}", exc_info=True)
        return {"name": vegetable_name, "error": str(e)}
