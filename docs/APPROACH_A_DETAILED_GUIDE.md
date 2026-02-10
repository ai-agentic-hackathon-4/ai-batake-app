# アプローチA詳細実装ガイド: Cloud Scheduler + HTTP Endpoint

## 📋 目次

1. [概要](#概要)
2. [実装の全体像](#実装の全体像)
3. [詳細実装手順](#詳細実装手順)
4. [コード実装例](#コード実装例)
5. [セキュリティ設定](#セキュリティ設定)
6. [テスト方法](#テスト方法)
7. [運用・監視](#運用監視)
8. [トラブルシューティング](#トラブルシューティング)

---

## 概要

### なぜアプローチAが最適か

**Cloud Scheduler + HTTP Endpoint** は、以下の理由で育成日記自動生成に最適です：

1. **既存インフラの活用**
   - 既にCloud Run上でFastAPIが稼働中
   - 新しいサービスやインフラ不要
   - デプロイフロー変更なし

2. **シンプルな構成**
   - HTTP POSTリクエスト1つでトリガー
   - Background Tasksで非同期処理
   - Cloud Loggingで一元管理

3. **低コスト**
   - Cloud Scheduler: $0.10/月
   - Vertex AI Gemini 3 Pro: ~$1-2/月
   - 追加のCompute費用: ほぼなし

4. **高い信頼性**
   - Googleマネージドサービス
   - 自動リトライ機能
   - SLA 99.9%

### システムフロー詳細

```
┌─────────────────────────────────────────────────────────────────┐
│                     Cloud Scheduler                              │
│  ・毎日23:50 JST（Asia/Tokyo）                                   │
│  ・Cron式: "50 23 * * *"                                        │
│  ・タイムゾーン: Asia/Tokyo                                      │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ HTTP POST /api/diary/generate-daily
             │ Authorization: Bearer [OIDC Token]
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI (Cloud Run)                            │
│                                                                   │
│  1. OIDC トークン検証                                            │
│     └─ サービスアカウント確認                                    │
│                                                                   │
│  2. 対象日付計算                                                 │
│     └─ 前日の日付を取得（23:50実行のため）                      │
│                                                                   │
│  3. Background Task キュー                                       │
│     └─ 即座にHTTP 202 Acceptedを返却                            │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Background Task
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Diary Generation Service                            │
│                                                                   │
│  Step 1: データ収集 (5-10秒)                                     │
│  ├─ agent_execution_logs から1日分のログ取得                    │
│  ├─ sensor_logs から1日分のデータ取得                           │
│  ├─ vegetables から現在育成中の野菜情報取得                     │
│  └─ plant_camera から最新画像取得                               │
│                                                                   │
│  Step 2: データ加工 (1-2秒)                                      │
│  ├─ 統計計算（温度・湿度・土壌水分の min/max/avg）              │
│  ├─ 主要イベント抽出（デバイス操作、警告、アラート）            │
│  └─ タイムライン整理                                            │
│                                                                   │
│  Step 3: AI日記生成 (10-15秒)                                    │
│  ├─ プロンプト構築                                              │
│  ├─ Vertex AI Gemini 3 Pro 呼び出し                            │
│  ├─ レスポンスパース（JSON抽出）                                │
│  └─ エラーハンドリング（429対応の指数バックオフリトライ）      │
│                                                                   │
│  Step 4: 保存 (1秒)                                              │
│  └─ Firestore growing_diaries コレクションに保存               │
│                                                                   │
│  合計所要時間: 約20-30秒                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Vertex AI Gemini 3 Proの利点

このアプローチでは **Vertex AI Gemini 3 Pro** を使用します：

1. **エンタープライズグレードの信頼性**
   - Google Cloud統合によるSLA保証
   - 自動スケーリングとロードバランシング
   - リージョナルデプロイメント対応

2. **統一されたアクセス管理**
   - Google Cloud IAMによる権限管理
   - サービスアカウントベースの認証
   - API Keyではなくアクセストークン認証

3. **高度なクォータ管理**
   - プロジェクト単位でのクォータ管理
   - Cloud Consoleから簡単に確認・増加可能
   - レート制限の可視化

4. **コスト最適化**
   - 使用量に応じた課金
   - 無料枠の活用
   - 詳細な使用状況トラッキング

5. **429エラー対策の重要性**
   - レート制限は避けられない場合がある
   - 指数バックオフリトライで自動復旧
   - ランダムジッターでリクエスト分散
   - 最大5回のリトライで高い成功率

---

## 実装の全体像

### ファイル構成

```
ai-batake-app/
├── backend/
│   ├── main.py                          # ← 新規エンドポイント追加
│   ├── diary_service.py                 # ← 新規作成（日記生成ロジック）
│   ├── db.py                            # ← 既存（日記保存関数追加）
│   ├── requirements.txt                 # ← 依存関係追加の可能性
│   └── tests/
│       └── test_diary_service.py        # ← 新規作成（テスト）
│
├── frontend/
│   └── app/
│       └── diary/
│           └── page.tsx                 # ← 新規作成（日記一覧ページ）
│
├── scripts/
│   └── setup_cloud_scheduler.sh         # ← 新規作成（セットアップスクリプト）
│
└── docs/
    └── APPROACH_A_DETAILED_GUIDE.md     # ← このファイル
```

### 必要な権限

#### GCP IAM権限

1. **Cloud Scheduler用サービスアカウント**
   - `roles/run.invoker` - Cloud Runエンドポイント呼び出し

2. **Cloud Run用サービスアカウント**（既存）
   - `roles/datastore.user` - Firestore読み書き
   - `roles/aiplatform.user` - Vertex AI API利用（Gemini 3 Pro）

---

## 詳細実装手順

### Phase 1: インフラ設定（30分）

#### 1.1 サービスアカウント作成

```bash
#!/bin/bash
# scripts/setup_cloud_scheduler.sh

PROJECT_ID="ai-agentic-hackathon-4"
REGION="us-central1"
SERVICE_NAME="ai-batake-app"

echo "Step 1: Creating service account for Cloud Scheduler..."

# サービスアカウント作成
gcloud iam service-accounts create scheduler-invoker \
    --display-name="Cloud Scheduler Service Account for Diary Generation" \
    --description="Service account used by Cloud Scheduler to invoke diary generation endpoint" \
    --project=$PROJECT_ID

# 作成確認
gcloud iam service-accounts list \
    --filter="email:scheduler-invoker@${PROJECT_ID}.iam.gserviceaccount.com" \
    --project=$PROJECT_ID
```

#### 1.2 権限付与

```bash
echo "Step 2: Granting Cloud Run Invoker role..."

# Cloud Run Invoker ロールを付与
gcloud run services add-iam-policy-binding $SERVICE_NAME \
    --member="serviceAccount:scheduler-invoker@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/run.invoker" \
    --region=$REGION \
    --project=$PROJECT_ID

# 権限確認
gcloud run services get-iam-policy $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID
```

#### 1.3 Cloud Scheduler ジョブ作成

```bash
echo "Step 3: Creating Cloud Scheduler job..."

# サービスURLを取得
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(status.url)')

echo "Service URL: $SERVICE_URL"

# Schedulerジョブ作成
gcloud scheduler jobs create http daily-diary-generator \
    --schedule="50 23 * * *" \
    --uri="${SERVICE_URL}/api/diary/generate-daily" \
    --http-method=POST \
    --oidc-service-account-email=scheduler-invoker@${PROJECT_ID}.iam.gserviceaccount.com \
    --location=$REGION \
    --time-zone="Asia/Tokyo" \
    --description="Daily growing diary generation at 23:50 JST" \
    --attempt-deadline=300s \
    --max-retry-attempts=3 \
    --min-backoff=5s \
    --max-backoff=60s \
    --project=$PROJECT_ID

echo "✓ Cloud Scheduler job created successfully!"
```

#### 1.4 設定確認

```bash
echo "Step 4: Verifying configuration..."

# ジョブ一覧確認
gcloud scheduler jobs list \
    --location=$REGION \
    --project=$PROJECT_ID

# ジョブ詳細確認
gcloud scheduler jobs describe daily-diary-generator \
    --location=$REGION \
    --project=$PROJECT_ID
```

### Phase 2: バックエンド実装（2-3日）

#### 2.1 diary_service.py 作成

```python
# backend/diary_service.py
"""
育成日記生成サービス

このモジュールは以下の機能を提供します：
1. エージェントログとセンサーデータの収集
2. 統計情報の計算
3. Vertex AI Gemini 3 Proを使用した日記生成
4. Firestoreへの保存
"""

import os
import logging
import json
import time
import random
from datetime import datetime, timedelta, date as date_type
from typing import Dict, List, Any, Optional
from google.cloud import firestore
import google.auth
from google.auth.transport.requests import Request
import requests

# Import from existing modules
try:
    from .db import db
except ImportError:
    from db import db

# Configuration
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "ai-agentic-hackathon-4")
LOCATION = "us-central1"
GEMINI_MODEL = "gemini-3-flash-preview"  # Vertex AI Gemini 3 Pro
VERTEX_AI_ENDPOINT = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{GEMINI_MODEL}:generateContent"

logger = logging.getLogger(__name__)


def get_vertex_ai_access_token():
    """
    Vertex AI用のアクセストークンを取得
    
    Returns:
        アクセストークン文字列
    """
    credentials, _ = google.auth.default()
    credentials.refresh(Request())
    return credentials.token


# ============================================================
# データ収集関数
# ============================================================

async def collect_daily_data(target_date: date_type) -> Dict[str, Any]:
    """
    指定日の全データを収集
    
    Args:
        target_date: 対象日付
    
    Returns:
        収集したデータの辞書
        {
            "date": "2025-02-04",
            "agent_logs": [...],
            "sensor_data": [...],
            "vegetable": {...},
            "plant_image": "https://..."
        }
    """
    logger.info(f"Starting data collection for {target_date}")
    
    # 日付範囲の設定（0:00:00 - 23:59:59）
    start_time = datetime.combine(target_date, datetime.min.time())
    end_time = datetime.combine(target_date, datetime.max.time())
    
    # 並行でデータ取得
    agent_logs = await get_agent_logs_for_date(start_time, end_time)
    sensor_data = await get_sensor_data_for_date(start_time, end_time)
    current_vegetable = await get_current_vegetable()
    plant_image = await get_plant_image_for_date(target_date)
    
    logger.info(f"Data collection complete: {len(agent_logs)} agent logs, {len(sensor_data)} sensor readings")
    
    return {
        "date": target_date.isoformat(),
        "agent_logs": agent_logs,
        "sensor_data": sensor_data,
        "vegetable": current_vegetable,
        "plant_image": plant_image
    }


async def get_agent_logs_for_date(start: datetime, end: datetime) -> List[Dict]:
    """指定期間のエージェントログを取得"""
    if db is None:
        logger.warning("Database not available")
        return []
    
    try:
        # Firestoreクエリ: タイムスタンプで範囲検索
        docs = db.collection("agent_execution_logs") \
            .where("timestamp", ">=", start.isoformat()) \
            .where("timestamp", "<=", end.isoformat()) \
            .order_by("timestamp") \
            .stream()
        
        logs = []
        for doc in docs:
            log_data = doc.to_dict()
            log_data['id'] = doc.id
            logs.append(log_data)
        
        logger.info(f"Retrieved {len(logs)} agent logs")
        return logs
        
    except Exception as e:
        logger.error(f"Error fetching agent logs: {e}", exc_info=True)
        return []


async def get_sensor_data_for_date(start: datetime, end: datetime) -> List[Dict]:
    """指定期間のセンサーデータを取得"""
    if db is None:
        logger.warning("Database not available")
        return []
    
    try:
        # Unix timestampに変換
        start_unix = int(start.timestamp())
        end_unix = int(end.timestamp())
        
        # Firestoreクエリ
        docs = db.collection("sensor_logs") \
            .where("unix_timestamp", ">=", start_unix) \
            .where("unix_timestamp", "<=", end_unix) \
            .order_by("unix_timestamp") \
            .stream()
        
        data = []
        for doc in docs:
            sensor_log = doc.to_dict()
            sensor_log['id'] = doc.id
            data.append(sensor_log)
        
        logger.info(f"Retrieved {len(data)} sensor readings")
        return data
        
    except Exception as e:
        logger.error(f"Error fetching sensor data: {e}", exc_info=True)
        return []


async def get_current_vegetable() -> Optional[Dict]:
    """現在育成中の野菜情報を取得"""
    if db is None:
        return None
    
    try:
        # edge_agent設定から取得するか、最新の野菜を取得
        docs = db.collection("vegetables") \
            .where("status", "==", "completed") \
            .order_by("created_at", direction=firestore.Query.DESCENDING) \
            .limit(1) \
            .stream()
        
        for doc in docs:
            veg_data = doc.to_dict()
            veg_data['id'] = doc.id
            return veg_data
        
        return None
        
    except Exception as e:
        logger.error(f"Error fetching vegetable info: {e}", exc_info=True)
        return None


async def get_plant_image_for_date(target_date: date_type) -> Optional[str]:
    """指定日の植物画像URLを取得"""
    if db is None:
        return None
    
    try:
        # plant_cameraコレクションから最新画像を取得
        # 実装は既存のget_latest_plant_camera関数を参照
        # ここではプレースホルダー
        return None
        
    except Exception as e:
        logger.error(f"Error fetching plant image: {e}", exc_info=True)
        return None


# ============================================================
# データ加工関数
# ============================================================

def calculate_statistics(sensor_data: List[Dict]) -> Dict:
    """
    センサーデータから統計を計算
    
    Args:
        sensor_data: センサーデータのリスト
    
    Returns:
        統計情報の辞書
    """
    if not sensor_data:
        logger.warning("No sensor data available for statistics")
        return {
            "temperature": {"min": 0, "max": 0, "avg": 0},
            "humidity": {"min": 0, "max": 0, "avg": 0},
            "soil_moisture": {"min": 0, "max": 0, "avg": 0},
        }
    
    # データ抽出
    temps = [d.get("temperature", 0) for d in sensor_data if d.get("temperature") is not None]
    humids = [d.get("humidity", 0) for d in sensor_data if d.get("humidity") is not None]
    soils = [d.get("soil_moisture", 0) for d in sensor_data if d.get("soil_moisture") is not None]
    
    # 統計計算
    stats = {
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
    
    logger.info(f"Statistics calculated: temp {stats['temperature']['avg']}°C, humidity {stats['humidity']['avg']}%")
    
    return stats


def extract_key_events(agent_logs: List[Dict], max_events: int = 15) -> List[Dict]:
    """
    重要なイベントを抽出
    
    Args:
        agent_logs: エージェントログのリスト
        max_events: 最大イベント数
    
    Returns:
        イベントのリスト
    """
    events = []
    
    for log in agent_logs:
        log_data = log.get("data", {})
        timestamp = log.get("timestamp", "")
        
        # 操作イベント（デバイス制御）
        if "operation" in log_data:
            for device, op in log_data["operation"].items():
                action = op.get("action", "")
                
                # アクティブな操作のみ抽出
                if any(keyword in action for keyword in ["ON", "OFF", "起動", "停止", "変更"]):
                    events.append({
                        "time": timestamp,
                        "type": "action",
                        "device": device,
                        "action": action
                    })
        
        # 警告・アラート
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
    
    # 最大件数まで（新しいものから）
    events_sorted = sorted(events, key=lambda x: x.get("time", ""), reverse=True)
    result = events_sorted[:max_events]
    
    logger.info(f"Extracted {len(result)} key events from {len(agent_logs)} logs")
    
    return result


# ============================================================
# AI日記生成
# ============================================================

def build_diary_prompt(
    date_str: str,
    statistics: Dict,
    events: List[Dict],
    vegetable_info: Optional[Dict]
) -> str:
    """
    日記生成用プロンプトを構築
    
    Args:
        date_str: 日付文字列
        statistics: 統計情報
        events: イベントリスト
        vegetable_info: 野菜情報
    
    Returns:
        プロンプト文字列
    """
    veg_name = vegetable_info.get("name", "野菜") if vegetable_info else "野菜"
    
    # イベント要約（時刻順に並び替え）
    events_sorted = sorted(events, key=lambda x: x.get("time", ""))
    event_lines = []
    for e in events_sorted[:10]:  # 最大10件
        time_str = e.get("time", "")
        try:
            # ISO形式からHH:MMに変換
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            time_display = dt.strftime("%H:%M")
        except:
            time_display = time_str
        
        device = e.get("device", "")
        action = e.get("action", "")
        event_lines.append(f"- {time_display}: {device} {action}" if device else f"- {time_display}: {action}")
    
    event_summary = "\n".join(event_lines) if event_lines else "特になし"
    
    # プロンプト構築
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
{event_summary}

以下の3つのセクションに分けて日記を作成してください：

1. **今日の要約** (200-300文字)
   - 1日の環境状態と全体的な様子を要約
   - データから読み取れる特徴的な点を記載
   - 親しみやすい文体で

2. **成長観察** (100-200文字)
   - 植物の状態について推測される観察
   - 環境データから判断できる成長の進捗
   - 具体的な観察ポイント

3. **明日への提案** (100-150文字)
   - データに基づく改善提案
   - 次のステップや注意点
   - 実践的なアドバイス

**重要**: 必ず以下のJSON形式で返してください（他のテキストは含めないこと）：
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


async def generate_diary_with_ai(
    date_str: str,
    statistics: Dict,
    events: List[Dict],
    vegetable_info: Optional[Dict],
    max_retries: int = 5
) -> Dict[str, str]:
    """
    Vertex AI Gemini 3 Proを使用して日記を生成（429対応の指数バックオフリトライ付き）
    
    Args:
        date_str: 日付文字列
        statistics: 統計情報
        events: イベントリスト
        vegetable_info: 野菜情報
        max_retries: 最大リトライ回数（デフォルト5回）
    
    Returns:
        生成された日記の辞書
        {
            "summary": "...",
            "observations": "...",
            "recommendations": "..."
        }
    
    Raises:
        RuntimeError: API呼び出し失敗時
    """
    # プロンプト構築
    prompt = build_diary_prompt(date_str, statistics, events, vegetable_info)
    
    # APIリクエストペイロード（Vertex AI形式）
    payload = {
        "contents": [{
            "role": "user",
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.95,
            "topK": 40,
            "maxOutputTokens": 2048,
            "candidateCount": 1
        },
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH"
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH"
            }
        ]
    }
    
    # 指数バックオフリトライループ
    base_delay = 2
    for attempt in range(max_retries):
        try:
            # アクセストークン取得（毎回更新して有効性を確保）
            access_token = get_vertex_ai_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Calling Vertex AI Gemini 3 Pro (attempt {attempt + 1}/{max_retries})...")
            
            response = requests.post(
                VERTEX_AI_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # レスポンスからテキスト抽出
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        generated_text = candidate["content"]["parts"][0].get("text", "")
                        
                        logger.info(f"Successfully generated diary text ({len(generated_text)} chars)")
                        
                        # パースしてJSON抽出
                        return parse_diary_response(generated_text)
                
                raise RuntimeError("Unexpected API response format")
            
            elif response.status_code == 429:
                # レート制限エラー: 指数バックオフでリトライ
                # 計算式: (base_delay * 2^attempt) + ランダムジッター
                jitter = random.uniform(0, 1)
                wait_time = (base_delay * (2 ** attempt)) + jitter
                
                logger.warning(
                    f"Rate limit (429) hit. Waiting {wait_time:.2f}s before retry "
                    f"(attempt {attempt + 1}/{max_retries})..."
                )
                
                time.sleep(wait_time)
                continue
            
            elif response.status_code >= 500:
                # サーバーエラー: リトライ
                jitter = random.uniform(0, 1)
                wait_time = (base_delay * (2 ** attempt)) + jitter
                
                logger.warning(
                    f"Server error ({response.status_code}). Waiting {wait_time:.2f}s before retry "
                    f"(attempt {attempt + 1}/{max_retries})..."
                )
                
                time.sleep(wait_time)
                continue
            
            else:
                # その他のエラー（400, 403など）: リトライしない
                error_msg = f"API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        
        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                jitter = random.uniform(0, 1)
                wait_time = (base_delay * (2 ** attempt)) + jitter
                time.sleep(wait_time)
                continue
            else:
                logger.error("API request timeout after all retries")
                # フォールバック: テンプレートベース
                return generate_fallback_diary(date_str, statistics, events)
        
        except Exception as e:
            logger.error(f"Unexpected error during API call: {e}", exc_info=True)
            if attempt == max_retries - 1:
                logger.error(f"Failed to generate diary after {max_retries} attempts")
                # フォールバック: テンプレートベース
                return generate_fallback_diary(date_str, statistics, events)
            
            jitter = random.uniform(0, 1)
            wait_time = (base_delay * (2 ** attempt)) + jitter
            time.sleep(wait_time)
    
    # 全リトライ失敗: フォールバック
    logger.error("All retry attempts exhausted, using fallback")
    return generate_fallback_diary(date_str, statistics, events)


def parse_diary_response(text: str) -> Dict[str, str]:
    """
    AI応答をパースしてJSONを抽出
    
    Args:
        text: AI生成テキスト
    
    Returns:
        パースされた日記の辞書
    """
    try:
        # JSONコードブロックを抽出
        clean_text = text.strip()
        
        # ```json ... ``` を削除
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0]
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0]
        
        # JSON パース
        parsed = json.loads(clean_text.strip())
        
        # 必須フィールド確認
        result = {
            "summary": parsed.get("summary", ""),
            "observations": parsed.get("observations", ""),
            "recommendations": parsed.get("recommendations", "")
        }
        
        # 空文字列チェック
        if not all(result.values()):
            raise ValueError("Empty fields in parsed response")
        
        logger.info("Successfully parsed AI response")
        return result
    
    except Exception as e:
        logger.error(f"Failed to parse AI response: {e}")
        logger.debug(f"Raw text: {text[:200]}...")
        
        # フォールバック: テキストを要約として使用
        return {
            "summary": text[:300] if len(text) <= 300 else text[:297] + "...",
            "observations": "AIによる詳細な観察を生成中です。",
            "recommendations": "引き続き環境を監視します。"
        }


def generate_fallback_diary(
    date_str: str,
    statistics: Dict,
    events: List[Dict]
) -> Dict[str, str]:
    """
    フォールバック用のテンプレートベース日記生成
    
    Args:
        date_str: 日付
        statistics: 統計情報
        events: イベントリスト
    
    Returns:
        生成された日記
    """
    logger.warning("Using fallback template for diary generation")
    
    temp_avg = statistics['temperature']['avg']
    humid_avg = statistics['humidity']['avg']
    soil_avg = statistics['soil_moisture']['avg']
    
    # イベント数カウント
    action_count = sum(1 for e in events if e.get("type") == "action")
    alert_count = sum(1 for e in events if e.get("type") == "alert")
    
    summary = f"""本日（{date_str}）の栽培環境は、平均気温{temp_avg}°C、湿度{humid_avg}%、土壌水分{soil_avg}%で推移しました。
エージェントによる自動制御が{action_count}回実行され、環境を適切に管理しました。"""
    
    if alert_count > 0:
        summary += f" {alert_count}件の警告が記録されています。"
    
    observations = f"""現在の環境データから判断すると、植物は{"良好" if temp_avg > 20 and temp_avg < 30 else "注意が必要"}な状態です。
温度と湿度のバランスが{"適切" if humid_avg > 50 and humid_avg < 80 else "調整が必要"}に保たれています。"""
    
    recommendations = f"""明日も引き続き環境監視を継続します。
{"気温の変動に注意し、" if statistics['temperature']['max'] - statistics['temperature']['min'] > 10 else ""}
適切な水分管理を心がけてください。"""
    
    return {
        "summary": summary,
        "observations": observations,
        "recommendations": recommendations
    }


# ============================================================
# Firestore保存
# ============================================================

async def init_diary_status(diary_id: str):
    """日記生成ステータスを初期化"""
    if db is None:
        logger.warning("Database not available")
        return
    
    try:
        db.collection("growing_diaries").document(diary_id).set({
            "generation_status": "processing",
            "created_at": datetime.now()
        })
        logger.info(f"Initialized diary status for {diary_id}")
    except Exception as e:
        logger.error(f"Failed to initialize diary status: {e}")


async def save_diary(diary_id: str, data: Dict):
    """日記をFirestoreに保存"""
    if db is None:
        logger.warning("Database not available, cannot save diary")
        return
    
    try:
        db.collection("growing_diaries").document(diary_id).set(data)
        logger.info(f"Diary saved successfully: {diary_id}")
    except Exception as e:
        logger.error(f"Failed to save diary: {e}")
        raise


async def mark_diary_failed(diary_id: str, error_message: str):
    """日記生成失敗をマーク"""
    if db is None:
        return
    
    try:
        db.collection("growing_diaries").document(diary_id).update({
            "generation_status": "failed",
            "error_message": error_message,
            "updated_at": datetime.now()
        })
        logger.error(f"Marked diary as failed: {diary_id} - {error_message}")
    except Exception as e:
        logger.error(f"Failed to mark diary as failed: {e}")


# ============================================================
# メイン処理
# ============================================================

async def process_daily_diary(target_date_str: str):
    """
    日記生成のメイン処理
    
    Args:
        target_date_str: 対象日付（ISO 8601形式）
    
    この関数はBackground Taskとして実行されます。
    """
    start_time = time.time()
    diary_id = target_date_str
    
    try:
        logger.info(f"=== Starting diary generation for {target_date_str} ===")
        
        # 日付パース
        target_date = date_type.fromisoformat(target_date_str)
        
        # ステータス初期化
        await init_diary_status(diary_id)
        
        # Step 1: データ収集
        logger.info("Step 1: Collecting daily data...")
        daily_data = await collect_daily_data(target_date)
        
        # Step 2: 統計計算・イベント抽出
        logger.info("Step 2: Calculating statistics and extracting events...")
        statistics = calculate_statistics(daily_data["sensor_data"])
        events = extract_key_events(daily_data["agent_logs"])
        
        # Step 3: AI日記生成
        logger.info("Step 3: Generating diary with AI...")
        ai_content = await generate_diary_with_ai(
            target_date_str,
            statistics,
            events,
            daily_data["vegetable"]
        )
        
        # Step 4: 保存
        logger.info("Step 4: Saving diary to Firestore...")
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
            "generation_time_ms": generation_time_ms
        }
        
        await save_diary(diary_id, diary_data)
        
        logger.info(f"=== Diary generation completed successfully in {generation_time_ms}ms ===")
        
    except Exception as e:
        logger.error(f"=== Diary generation failed: {e} ===", exc_info=True)
        await mark_diary_failed(diary_id, str(e))
        raise
```

#### 2.2 main.py にエンドポイント追加

```python
# backend/main.py の既存コードに以下を追加

from fastapi import BackgroundTasks, Request, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from datetime import datetime, timedelta

# Import diary service
try:
    from .diary_service import process_daily_diary
except ImportError:
    from diary_service import process_daily_diary


def verify_scheduler_token(request: Request):
    """
    Cloud Schedulerからのリクエストを検証
    
    OIDCトークンをチェックして、正しいサービスアカウントからの
    リクエストであることを確認します。
    
    Args:
        request: FastAPI Request オブジェクト
    
    Raises:
        HTTPException: 認証失敗時
    """
    try:
        # Authorizationヘッダー取得
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=403, detail="Missing or invalid Authorization header")
        
        # トークン抽出
        token = auth_header.replace('Bearer ', '')
        
        # OIDCトークン検証
        claim = id_token.verify_oauth2_token(
            token,
            google_requests.Request()
        )
        
        # サービスアカウント確認
        expected_email = "scheduler-invoker@ai-agentic-hackathon-4.iam.gserviceaccount.com"
        if claim.get('email') != expected_email:
            logging.warning(f"Unauthorized service account: {claim.get('email')}")
            raise HTTPException(status_code=403, detail="Unauthorized service account")
        
        logging.info(f"Verified request from: {claim.get('email')}")
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=403, detail=f"Invalid token: {str(e)}")


@app.post("/api/diary/generate-daily")
async def generate_daily_diary(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    日次日記生成エンドポイント
    
    Cloud Schedulerから毎日23:50に呼び出されます。
    前日の日記を生成します。
    
    Returns:
        202 Accepted: ジョブが受け付けられました
        403 Forbidden: 認証失敗
        500 Internal Server Error: サーバーエラー
    """
    # Cloud Schedulerからのリクエストか検証
    verify_scheduler_token(request)
    
    # 前日の日付を計算（23:50実行のため）
    target_date = (datetime.now() - timedelta(hours=1)).date()
    
    logging.info(f"Diary generation request accepted for {target_date.isoformat()}")
    
    # Background Taskとしてキュー
    background_tasks.add_task(
        process_daily_diary,
        target_date.isoformat()
    )
    
    return {
        "status": "accepted",
        "date": target_date.isoformat(),
        "message": "Diary generation started in background"
    }


@app.post("/api/diary/generate-manual")
async def generate_manual_diary(
    background_tasks: BackgroundTasks,
    date: str
):
    """
    手動日記生成エンドポイント（テスト・再生成用）
    
    Args:
        date: 対象日付（YYYY-MM-DD形式）
    
    Returns:
        202 Accepted: ジョブが受け付けられました
        400 Bad Request: 日付フォーマットエラー
    """
    try:
        # 日付バリデーション
        from datetime import date as date_module
        target_date = date_module.fromisoformat(date)
        
        logging.info(f"Manual diary generation request for {date}")
        
        background_tasks.add_task(
            process_daily_diary,
            date
        )
        
        return {
            "status": "accepted",
            "date": date,
            "message": "Manual diary generation started"
        }
    
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )


@app.get("/api/diary/list")
async def list_diaries(limit: int = 30, offset: int = 0):
    """
    育成日記一覧取得
    
    Args:
        limit: 取得件数（デフォルト30）
        offset: オフセット
    
    Returns:
        日記のリスト
    """
    if db is None:
        return {"diaries": []}
    
    try:
        docs = db.collection("growing_diaries") \
            .where("generation_status", "==", "completed") \
            .order_by("date", direction=firestore.Query.DESCENDING) \
            .limit(limit) \
            .offset(offset) \
            .stream()
        
        diaries = []
        for doc in docs:
            diary = doc.to_dict()
            diary['id'] = doc.id
            diaries.append(diary)
        
        return {"diaries": diaries, "count": len(diaries)}
    
    except Exception as e:
        logging.error(f"Error fetching diaries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/diary/{date}")
async def get_diary(date: str):
    """
    特定日の日記取得
    
    Args:
        date: 日付（YYYY-MM-DD）
    
    Returns:
        日記データ
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    try:
        doc = db.collection("growing_diaries").document(date).get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Diary not found")
        
        diary = doc.to_dict()
        diary['id'] = doc.id
        return diary
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching diary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Phase 3: テスト（1日）

#### 3.1 手動トリガーテスト

```bash
# Cloud Schedulerジョブを手動実行
gcloud scheduler jobs run daily-diary-generator \
    --location=us-central1 \
    --project=ai-agentic-hackathon-4

# ログ確認
gcloud logging read \
    'resource.type="cloud_run_revision" AND textPayload:"diary"' \
    --limit=50 \
    --format=json \
    --project=ai-agentic-hackathon-4
```

#### 3.2 ローカルテスト

```bash
# backend/test_diary_local.py
import asyncio
from datetime import date, timedelta
from diary_service import process_daily_diary

async def test_generate_diary():
    # 昨日の日記を生成
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    print(f"Generating diary for {yesterday}...")
    
    await process_daily_diary(yesterday)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(test_generate_diary())
```

実行:
```bash
cd backend
python test_diary_local.py
```

---

## セキュリティ設定

### OIDC認証の仕組み

```
┌─────────────────────┐
│  Cloud Scheduler    │
│                     │
│ 1. JWTトークン生成  │
│    (scheduler SA)   │
└──────────┬──────────┘
           │
           │ POST + Bearer Token
           │
           ▼
┌─────────────────────────────────────┐
│  FastAPI Endpoint                   │
│                                     │
│ 2. Authorizationヘッダー確認        │
│ 3. google.oauth2.id_token で検証   │
│ 4. claim.email を確認               │
│    └─ scheduler-invoker@ のみ許可  │
└─────────────────────────────────────┘
```

### IP制限（オプション）

より厳格なセキュリティが必要な場合：

```python
ALLOWED_IPS = [
    # Google Cloud Scheduler IP ranges
    # https://cloud.google.com/scheduler/docs/reference/rest
]

def verify_ip(request: Request):
    client_ip = request.client.host
    if client_ip not in ALLOWED_IPS:
        raise HTTPException(status_code=403, detail="IP not allowed")
```

---

## 運用・監視

### Cloud Loggingクエリ

```bash
# 日記生成の成功ログ
resource.type="cloud_run_revision"
severity="INFO"
textPayload:"Diary generation completed successfully"

# 日記生成の失敗ログ
resource.type="cloud_run_revision"
severity="ERROR"
textPayload:"Diary generation failed"

# Vertex AI Gemini 3 Pro呼び出し
resource.type="cloud_run_revision"
textPayload:"Calling Vertex AI Gemini 3 Pro"

# 429レート制限エラー
resource.type="cloud_run_revision"
textPayload:"Rate limit (429) hit"
```

### Cloud Monitoringメトリクス

カスタムメトリクスを追加:

```python
from google.cloud import monitoring_v3
import time

def record_diary_metric(success: bool, duration_ms: int):
    """日記生成メトリクスを記録"""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/ai-agentic-hackathon-4"
    
    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/diary/generation_duration"
    series.resource.type = "global"
    
    point = monitoring_v3.Point()
    point.value.int64_value = duration_ms
    point.interval.end_time.seconds = int(time.time())
    
    series.points = [point]
    
    client.create_time_series(name=project_name, time_series=[series])
```

### アラート設定

```bash
# Cloud Monitoring アラートポリシー作成例
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="Diary Generation Failure Alert" \
    --condition-display-name="Diary generation failed" \
    --condition-threshold-value=1 \
    --condition-threshold-duration=300s \
    --condition-filter='resource.type="cloud_run_revision" AND severity="ERROR" AND textPayload:"Diary generation failed"'
```

---

## トラブルシューティング

### 問題1: Schedulerジョブが実行されない

**症状**: 23:50になってもエンドポイントが呼ばれない

**確認項目**:
```bash
# ジョブステータス確認
gcloud scheduler jobs describe daily-diary-generator \
    --location=us-central1

# 最近の実行履歴
gcloud scheduler jobs describe daily-diary-generator \
    --location=us-central1 \
    --format="value(state, scheduleTime, status)"
```

**解決策**:
- ジョブが有効化されているか確認
- スケジュール式が正しいか確認
- タイムゾーン設定確認

### 問題2: 403 Forbidden エラー

**症状**: エンドポイントは呼ばれるが403エラー

**確認項目**:
```bash
# IAM権限確認
gcloud run services get-iam-policy ai-batake-app \
    --region=us-central1 \
    --format=json
```

**解決策**:
```bash
# 権限を再付与
gcloud run services add-iam-policy-binding ai-batake-app \
    --member="serviceAccount:scheduler-invoker@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker" \
    --region=us-central1
```

### 問題3: Vertex AI Gemini API タイムアウト

**症状**: 日記生成が途中で失敗

**ログ例**:
```
ERROR: API request timeout after retries
```

**解決策**:
- リトライ回数を増やす（`max_retries=5`がデフォルト）
- タイムアウト時間を延長（90秒 → 120秒）
- フォールバック日記生成が正しく動作するか確認
- Vertex AI APIのクォータ確認

### 問題4: 429 レート制限エラー

**症状**: 429エラーが頻発

**ログ例**:
```
WARNING: Rate limit (429) hit. Waiting 4.5s before retry (attempt 2/5)...
```

**確認項目**:
- Vertex AI APIのクォータ設定を確認
- 同時実行数が多すぎないか確認
- リトライ設定が適切か確認

**解決策**:
```bash
# Vertex AIのクォータを確認
gcloud services list --enabled | grep aiplatform

# クォータの増加リクエスト（必要に応じて）
# Google Cloud Console > IAM & Admin > Quotas
```

指数バックオフ（base_delay=2秒、max_retries=5）により：
- 1回目リトライ: 2-3秒待機
- 2回目リトライ: 4-5秒待機
- 3回目リトライ: 8-9秒待機
- 4回目リトライ: 16-17秒待機
- 5回目リトライ: 32-33秒待機

合計最大約65秒のリトライ期間があります。

### 問題5: データが取得できない

**症状**: センサーログまたはエージェントログが0件

**確認項目**:
```python
# Firestoreクエリをテスト
from google.cloud import firestore
db = firestore.Client()

# センサーログ確認
sensor_logs = db.collection("sensor_logs").limit(5).stream()
for log in sensor_logs:
    print(log.to_dict())

# エージェントログ確認
agent_logs = db.collection("agent_execution_logs").limit(5).stream()
for log in agent_logs:
    print(log.to_dict())
```

**解決策**:
- コレクション名が正しいか確認
- インデックスが作成されているか確認（Firestoreコンソール）
- 日付範囲クエリの条件を確認

---

## まとめ

### 実装完了チェックリスト

#### インフラ設定
- [ ] サービスアカウント作成完了
- [ ] IAM権限付与完了
- [ ] Cloud Schedulerジョブ作成完了
- [ ] 手動実行テスト成功

#### バックエンド
- [ ] `diary_service.py` 実装完了
- [ ] `main.py` エンドポイント追加完了
- [ ] OIDC認証実装完了
- [ ] エラーハンドリング実装完了

#### テスト
- [ ] 手動トリガーテスト成功
- [ ] ローカルテスト成功
- [ ] 日記データがFirestoreに保存確認
- [ ] ログが正しく出力されているか確認

#### 運用準備
- [ ] Cloud Loggingクエリ作成
- [ ] アラート設定完了
- [ ] ドキュメント整備完了

### 次のステップ

1. **フロントエンド実装**: `/diary` ページの作成
2. **UI/UX改善**: カレンダービュー、フィルター機能
3. **機能拡張**: 週次・月次レポート、PDF出力
4. **パフォーマンス最適化**: キャッシング、ページネーション

---

**作成日**: 2025-02-04  
**バージョン**: 1.0  
**ステータス**: 実装準備完了
