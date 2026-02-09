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
        debug(f"Final retry attempt for {method} {url}")
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
    info(f"Analyzing seed packet image ({len(image_bytes)} bytes)")
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
        
        debug("Sending request to Gemini 3 Flash for seed packet analysis")
        response = request_with_retry("POST", url, headers=headers, json=payload)
        response.raise_for_status()
        
        result_json = response.json()
        
        result_json = response.json()
        
        # レスポンスからテキストを抽出
        # 構造: candidates[0].content.parts[0].text
        try:
            text = result_json['candidates'][0]['content']['parts'][0]['text']
            info(f"Seed packet analysis completed successfully")
            debug(f"Analysis result preview: {text[:200]}...")
            return text
        except (KeyError, IndexError):
             error(f"Unexpected response format: {result_json}")
             return '{"name": "Error", "visible_instructions": "Response parsing failed"}'

    except Exception as e:
        error(f"Error in analyze_seed_packet: {e}", exc_info=True)
        return '{"name": "不明な野菜", "visible_instructions": "API Error"}'

def perform_deep_research(vegetable_name: str, packet_info: str) -> dict:
    """
    Deep Research Agent の REST API を使用して、野菜の詳細な育て方を調査します。
    
    プロセスは以下の3ステップで構成されます：
    1. 調査インタラクションの開始 (POST /interactions)
    2. 完了までのポーリング (GET /interactions/{id})
    3. 調査結果からの構造化データ抽出 (Gemini generateContent)
    """
    info(f"Starting deep research for: {vegetable_name}")
    headers, query_param = get_auth_headers()

    research_topic = f"「{vegetable_name}」の育て方について、家庭菜園や農業の専門的な情報を詳しく調べてください。特に最適な気温、湿度、土壌水分量、水やり頻度、日照条件について数値を含めて調査してください。"
    if packet_info:
        research_topic += f" また、種の袋には以下の情報がありました: {packet_info}"

    try:
        # 1. インタラクションの開始 (POST)
        # Deep Research Agent に調査トピックを送信し、バックグラウンドでの調査を開始します。
        base_url = "https://generativelanguage.googleapis.com/v1beta/interactions"
        start_url = f"{base_url}{query_param}"
        
        payload = {
            "input": research_topic,
            "agent": "deep-research-pro-preview-12-2025",
            "background": True
        }
        
        debug(f"Starting Deep Research interaction for: {vegetable_name}")
        response = request_with_retry("POST", start_url, headers=headers, json=payload)
        
        if response.status_code != 200:
             error(f"Deep Research start failed: {response.text}")
             return {"name": vegetable_name, "error": f"Start failed: {response.status_code} - {response.text}"}
             
        interaction_data = response.json()
        # レスポンスが大きい場合のためデバッグ出力を制限
        interaction_str = json.dumps(interaction_data, ensure_ascii=False)
        debug(f"Interaction data received: {interaction_str[:500] if len(interaction_str) > 500 else interaction_str}...")
        interaction_name = interaction_data.get("name")
        if not interaction_name:
            # フォールバック: リソース名はIDから構築される可能性がある
            interaction_id = interaction_data.get("id")
            if interaction_id:
                # APIは通常 "interactions/<ID>" または単にIDを返す
                # ドキュメントに基づき、名前がない場合は 'interactions/{id}' と仮定する
                interaction_name = f"interactions/{interaction_id}"
                debug(f"Constructed interaction_name from ID: {interaction_name}")

        
        info(f"Research started: {interaction_name}")
        
        
        # 2. ポーリング (GET)
        # 調査が完了するまで、定期的にステータスを確認します。
        poll_url = f"https://generativelanguage.googleapis.com/v1beta/{interaction_name}{query_param}"
        debug(f"Poll URL: {poll_url.split('?')[0]}...")
        
        if not interaction_name:
             error("Interaction Name is None or Empty!")
             return {"name": vegetable_name, "error": "Interaction Name missing"}
        
        max_retries = 180
        final_text = ""
        status = "unknown"
        
        start_time = time.time()
        for i in range(max_retries):
            current_time = time.time()
            elapsed = current_time - start_time
            
            # ログのスパムを減らすため、10回ごとに進捗をログ出力
            if i % 10 == 0:
                debug(f"Polling iteration {i+1}/{max_retries}. Elapsed: {elapsed:.2f}s")

            poll_resp = request_with_retry("GET", poll_url, headers=headers)
            if poll_resp.status_code != 200:
                warning(f"Poll failed: {poll_resp.status_code} - {poll_resp.text[:200]}...")
                
                # 404 (Interaction not found) の場合は停止
                if poll_resp.status_code == 404:
                     error(f"Interaction not found (404). Aborting poll for {interaction_name}")
                     return {"name": vegetable_name, "error": f"Research failed: Interaction not found (404)"}

                # 一時的なエラー (500系など) の場合はすぐに中断しない
                time.sleep(10)
                continue
                
            data = poll_resp.json()
            status = data.get("status")
            
            if status == "completed":
                outputs = data.get("outputs", [])
                if outputs:
                    final_text = outputs[-1].get("text", "")
                    info(f"Research completed for {vegetable_name}. Output length: {len(final_text)}")
                else:
                    warning("Research completed but no outputs found.")
                break
            elif status == "failed":
                error_msg = data.get('error')
                error(f"Research failed for {vegetable_name}. Error: {error_msg}")
                return {"name": vegetable_name, "error": f"Research failed: {error_msg}"}
                
            time.sleep(10)
        else:
            error(f"Research timed out for {vegetable_name} after {max_retries} retries ({max_retries * 10}s). Last status: {status}")
            return {"name": vegetable_name, "error": "Research Timeout"}

        # 3. データ抽出 (REST)
        # 調査レポート (自由記述テキスト) から、アプリで利用しやすいJSON形式のデータを抽出します。
        info(f"Extracting structured data for {vegetable_name}")
        extraction_prompt = f"""
        以下の調査レポートに基づいて、野菜「{vegetable_name}」の育て方情報を抽出してJSON形式でまとめてください。
        特にsummary_promptには最適な気温、湿度、土壌水分量、水やり頻度、日照条件について数値を含めてこれだけで野菜を育てることができるほど詳しく記載してください。

        ---レポート---
        {final_text}
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
        
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent{query_param}"
        gen_payload = {
            "contents": [{"parts": [{"text": extraction_prompt}]}],
            "generation_config": {"response_mime_type": "application/json"}
        }
        
        # 抽出リクエストの送信
        gen_resp = request_with_retry("POST", gen_url, headers=headers, json=gen_payload)
        gen_resp.raise_for_status()
        
        gen_data = gen_resp.json()
        try:
            extracted_text = gen_data['candidates'][0]['content']['parts'][0]['text']
            result = json.loads(extracted_text)
            info(f"Successfully extracted research data for {vegetable_name}")
            return result
        except:
             warning(f"Failed to parse extraction result for {vegetable_name}")
             return {"name": vegetable_name, "raw_research": final_text, "error": "Extraction Parsing Failed"}

    except Exception as e:
        error(f"Error in perform_deep_research for {vegetable_name}: {e}", exc_info=True)
        return {"name": vegetable_name, "error": str(e)}
