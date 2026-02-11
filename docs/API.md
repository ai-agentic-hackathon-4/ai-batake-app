# API Reference

AI Batake App が提供する全APIエンドポイントのリファレンスです。

## 基本情報

- **ベースURL**: `http://localhost:8081/api`
- **プロトコル**: HTTP/HTTPS
- **フォーマット**: JSON

---

## センサー・環境

### POST /api/weather

天気情報を取得します。

**リクエスト:**
```json
{
  "region": "東京"
}
```

**レスポンス:**
```json
{
  "result": "現在の東京の天気は晴れ..."
}
```

### GET /api/sensors/latest

最新のセンサーデータを取得します。

**レスポンス:**
```json
{
  "temperature": 25.5,
  "humidity": 60,
  "soil_moisture": 45.2,
  "illuminance": 150.0,
  "timestamp": "2025-02-10T12:00:00"
}
```

### GET /api/sensor-history

センサーデータの履歴を取得します。

**パラメータ:**
| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|----------|------|
| hours | int | 24 | 取得する時間範囲（時間単位） |

**レスポンス:**
```json
[
  {
    "temperature": 25.5,
    "humidity": 60,
    "timestamp": "2025-02-10T12:00:00"
  }
]
```

---

## 野菜・種袋

### POST /api/register-seed

種袋の画像を登録し、AIによる解析とDeep Researchを開始します。

**リクエスト:** `multipart/form-data`
| フィールド | 型 | 説明 |
|-----------|-----|------|
| file | File | 種袋の画像ファイル |
| research_mode | string | `"agent"` (Deep Research) or `"grounding"` (Google Search) |

**レスポンス:**
```json
{
  "id": "abc123",
  "vegetable_name": "ミニトマト",
  "status": "researching"
}
```

### GET /api/vegetables

登録された全野菜のリストを取得します。

**レスポンス:**
```json
[
  {
    "id": "abc123",
    "vegetable_name": "ミニトマト",
    "status": "completed",
    "created_at": "2025-02-10T12:00:00"
  }
]
```

### GET /api/vegetables/latest

最新の野菜データを取得します。

### POST /api/vegetables/{doc_id}/select

指定した野菜のDeep Research結果をエッジエージェントの指示として適用します。

**レスポンス:**
```json
{
  "status": "ok",
  "message": "Selected ミニトマト as active instruction"
}
```

### DELETE /api/vegetables/{doc_id}

野菜データを削除します。

### GET /api/plant-camera/latest

最新の植物カメラ画像をBase64エンコードで取得します。

**レスポンス:**
```json
{
  "image": "data:image/jpeg;base64,..."
}
```

### GET /api/agent-logs

エージェント実行ログを取得します。

### GET /api/agent-logs/oldest

最古のエージェントログを取得します（播種日数の計算に使用）。

---

## 栽培ガイド (非同期ジョブ)

### POST /api/seed-guide/jobs

種袋画像から栽培ガイド生成ジョブを作成します。

**リクエスト:** `multipart/form-data`
| フィールド | 型 | 説明 |
|-----------|-----|------|
| file | File | 種袋の画像ファイル |
| guide_image_mode | string | `"single"` (1枚生成) or `"all"` (全ステップ生成) |

**レスポンス:**
```json
{
  "job_id": "guide-abc123",
  "status": "pending"
}
```

### GET /api/seed-guide/jobs/{job_id}

ジョブのステータスと結果を取得します。

**ジョブステータス:**
- `PENDING`: 処理待ち
- `PROCESSING`: 処理中
- `COMPLETED`: 完了
- `FAILED`: 失敗

**レスポンス (完了時):**
```json
{
  "job_id": "guide-abc123",
  "status": "COMPLETED",
  "result": {
    "title": "ミニトマトの育て方",
    "steps": [
      {
        "title": "種まき",
        "description": "...",
        "image_url": "/api/seed-guide/image/guide-abc123/0"
      }
    ]
  }
}
```

### POST /api/seed-guide/save

栽培ガイドを保存します。

### GET /api/seed-guide/saved

保存済みガイドの一覧を取得します。

### GET /api/seed-guide/saved/{doc_id}

保存済みガイドを取得します（画像はBase64にハイドレートされます）。

### DELETE /api/seed-guide/saved/{doc_id}

保存済みガイドを削除します。

### GET /api/seed-guide/image/{job_id}/{step_index}

ガイドのステップ画像をGCSからプロキシして返します。

---

## キャラクター

### POST /api/seed-guide/character

種袋画像からキャラクター生成ジョブを作成します。

**リクエスト:** `multipart/form-data`
| フィールド | 型 | 説明 |
|-----------|-----|------|
| file | File | 種袋の画像ファイル |

**レスポンス:**
```json
{
  "job_id": "char-abc123",
  "status": "pending"
}
```

### GET /api/seed-guide/character/{job_id}

キャラクター生成ジョブのステータスを取得します。

### GET /api/characters

完了したキャラクターの一覧を取得します。

### POST /api/characters/{job_id}/select

指定したキャラクターをアクティブキャラクターとして選択します（日記に使用）。

### GET /api/character

現在アクティブなキャラクター情報を取得します。

### GET /api/character/image

キャラクター画像をGCSからプロキシして返します。

---

## 統合シード機能

### POST /api/unified/start

Research、Guide、Character 生成を一括で開始します。

**リクエスト:** `multipart/form-data`
| フィールド | 型 | 説明 |
|-----------|-----|------|
| file | File | 種袋の画像ファイル |
| research_mode | string | `"agent"` or `"grounding"` |
| guide_image_mode | string | `"single"` or `"all"` |

**レスポンス:**
```json
{
  "job_id": "unified-abc123",
  "research_doc_id": null,
  "guide_job_id": "guide-xyz",
  "character_job_id": "char-xyz",
  "status": "PROCESSING"
}
```

### GET /api/unified/jobs/{job_id}

統合ジョブの全体ステータスを取得します。

**レスポンス:**
```json
{
  "job_id": "unified-abc123",
  "overall_status": "COMPLETED",
  "research": { "status": "completed", "vegetable_name": "ミニトマト" },
  "guide": { "status": "COMPLETED", "result": {...} },
  "character": { "status": "COMPLETED", "result": {...} }
}
```

---

## 栽培日記

### POST /api/diary/auto-generate

Cloud Schedulerによる栽培日記自動生成エンドポイント。

**認証:** クエリパラメータ `key` でAPIキーを検証

```
POST /api/diary/auto-generate?key=YOUR_DIARY_API_KEY
```

**レスポンス:**
```json
{
  "status": "accepted",
  "date": "2025-02-10",
  "message": "日記生成を開始しました"
}
```

### POST /api/diary/generate-manual

手動で日記を生成します。SSE (Server-Sent Events) でリアルタイム進捗を返します。

**リクエスト:**
```json
{
  "date": "2025-02-10"
}
```

**レスポンス:** `text/event-stream`
```
data: {"event": "progress", "message": "データ収集中..."}
data: {"event": "progress", "message": "AI日記生成中..."}
data: {"event": "done", "result": {...}}
```

### POST /api/diary/generate-daily

日次日記生成（バックグラウンドタスク）。

### GET /api/diary/list

栽培日記の一覧を取得します。

**パラメータ:**
| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|----------|------|
| limit | int | 30 | 取得件数 |
| offset | int | 0 | オフセット |

### GET /api/diary/{date}

指定日の栽培日記を取得します。

**レスポンス:**
```json
{
  "date": "2025-02-10",
  "title": "今日のミニトマト日記",
  "content": "...",
  "generation_status": "completed",
  "image_url": "/api/diary/2025-02-10/image"
}
```

### GET /api/diary/{date}/image

日記の絵日記画像をGCSからプロキシして返します。
