import os
import logging
import json
import time
import requests
import base64

import google.auth
import google.auth.transport.requests

# Helper for Auth
def get_auth_headers():
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return {"Content-Type": "application/json"}, f"?key={api_key}"
    
    # Try ADC
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

def analyze_seed_packet(image_bytes: bytes) -> str:
    """
    Analyzes the seed packet image using Gemini 3 Flash via REST API.
    """
    headers, query_param = get_auth_headers()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent{query_param}"
    
    try:
        # Encode image to base64
        b64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        prompt_text = """
        この画像の種の袋を分析してください。
        以下の情報を抽出してjson形式で返してください。
        1. 野菜の名前 (name)
        2. 画像から読み取れる育て方のポイント (visible_instructions)
        もし読み取れない場合は "unknown" としてください。
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
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result_json = response.json()
        
        # Extract text from response
        # Structure: candidates[0].content.parts[0].text
        try:
            text = result_json['candidates'][0]['content']['parts'][0]['text']
            return text
        except (KeyError, IndexError):
             logging.error(f"Unexpected response format: {result_json}")
             return '{"name": "Error", "visible_instructions": "Response parsing failed"}'

    except Exception as e:
        logging.error(f"Error in analyze_seed_packet: {e}")
        return '{"name": "不明な野菜", "visible_instructions": "API Error"}'

def perform_deep_research(vegetable_name: str, packet_info: str) -> dict:
    """
    Performs deep research using REST API for Deep Research Agent.
    """
    headers, query_param = get_auth_headers()

    research_topic = f"「{vegetable_name}」の育て方について、家庭菜園や農業の専門的な情報を詳しく調べてください。特に最適な気温、湿度、土壌の『体積含水率(%)』、水やり頻度、日照条件について数値を含めて調査してください（pF値ではなく体積含水率を優先）。"
    if packet_info:
        research_topic += f" また、種の袋には以下の情報がありました: {packet_info}"

    try:
        # 1. Start Interaction (POST)
        base_url = "https://generativelanguage.googleapis.com/v1beta/interactions"
        start_url = f"{base_url}{query_param}"
        
        payload = {
            "input": research_topic,
            "agent": "deep-research-pro-preview-12-2025",
            "background": True
        }
        
        logging.info(f"Starting Deep Research (REST) for: {vegetable_name}")
        response = requests.post(start_url, headers=headers, json=payload)
        
        if response.status_code != 200:
             logging.error(f"Deep Research start failed: {response.text}")
             return {"name": vegetable_name, "error": f"Start failed: {response.status_code} - {response.text}"}
             
        interaction_data = response.json()
        interaction_name = interaction_data.get("name") 
        
        logging.info(f"Research started: {interaction_name}")
        
        # 2. Poll (GET)
        poll_url = f"https://generativelanguage.googleapis.com/v1beta/{interaction_name}{query_param}"
        
        max_retries = 60
        final_text = ""
        
        for _ in range(max_retries):
            poll_resp = requests.get(poll_url, headers=headers)
            if poll_resp.status_code != 200:
                logging.warning(f"Poll failed: {poll_resp.status_code}")
                # Don't break immediately on temp error, but interaction 404 might be bad.
                time.sleep(5)
                continue
                
            data = poll_resp.json()
            status = data.get("status")
            
            logging.info(f"Polling status: {status}")
            
            if status == "completed":
                outputs = data.get("outputs", [])
                if outputs:
                    final_text = outputs[-1].get("text", "")
                break
            elif status == "failed":
                return {"name": vegetable_name, "error": f"Research failed: {data.get('error')}"}
                
            time.sleep(10)
        else:
            return {"name": vegetable_name, "error": "Research Timeout"}

        # 3. Extraction (REST)
        extraction_prompt = f"""
        以下の調査レポートに基づいて、野菜「{vegetable_name}」の育て方情報を抽出してJSON形式でまとめてください。
        
        ---レポート---
        {final_text}
        -------------
        
        【抽出ルール】
        1. 土壌水分量はpF値ではなく「体積含水率(%)」での目安を抽出・計算してください。
        2. pHの情報は不要です。
        3. 「complete_support_prompt」には、この野菜を自律エージェントが育てるために必要な全ての条件（気温、湿度、水分率、光量、水やり頻度、注意点など）を網羅した、包括的な指示プロンプトを作成してください。
        
        出力フォーマット(JSON):
        {{
            "name": "{vegetable_name}",
            "optimal_temp_range": "...",
            "optimal_humidity_range": "...",
            "volumetric_water_content": "...",
            "watering_instructions": "...",
            "light_requirements": "...",
            "care_tips": "...",
            "summary_prompt": "...",
            "complete_support_prompt": "..."
        }}
        """
        
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent{query_param}"
        gen_payload = {
            "contents": [{"parts": [{"text": extraction_prompt}]}],
            "generation_config": {"response_mime_type": "application/json"}
        }
        
        gen_resp = requests.post(gen_url, headers=headers, json=gen_payload)
        gen_resp.raise_for_status()
        
        gen_data = gen_resp.json()
        try:
            extracted_text = gen_data['candidates'][0]['content']['parts'][0]['text']
            return json.loads(extracted_text)
        except:
             return {"name": vegetable_name, "raw_research": final_text, "error": "Extraction Parsing Failed"}

    except Exception as e:
        logging.error(f"Error in perform_deep_research (REST): {e}")
        return {"name": vegetable_name, "error": str(e)}
