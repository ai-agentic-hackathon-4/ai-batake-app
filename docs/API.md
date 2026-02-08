# API ドキュメント

## キャラクター生成

### POST /api/seed-guide/character

種袋の画像からキャラクターを生成するバックグラウンドジョブを開始します。

**リクエスト:** `multipart/form-data`
- `file`: 画像ファイル (jpeg, png)

**レスポンス:**
```json
{
  "job_id": "uuid-string",
  "status": "PENDING"
}
```

### GET /api/seed-guide/jobs/{job_id}

キャラクター生成ジョブのステータスをポーリングします。

**レスポンス:**
```json
{
  "job_id": "uuid-string",
  "status": "PROCESSING | COMPLETED | FAILED",
  "result": {
    "name": "キャラクター名",
    "personality": "性格の説明...",
    "image_url": "/api/character/image?path=..."
  }
}
```

### GET /api/character

最新の生成されたキャラクターのメタデータを取得します。

**レスポンス:**
```json
{
  "name": "キャラクター名",
  "personality": "性格の説明...",
  "image_uri": "/api/character/image?path=..."
}
```

### GET /api/character/image

Google Cloud Storage からキャラクター画像をプロキシ経由で配信します。

**クエリパラメータ:**
- `path`: GCS内の画像への相対パス（URLエンコード済み）。

**レスポンス:** 画像バイナリ (image/png)。
