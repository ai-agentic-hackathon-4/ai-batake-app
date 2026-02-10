# テスト実装

このディレクトリには、バックエンドとフロントエンドのテストコードが含まれています。

## バックエンド（Python/pytest）

### テスト実行方法

```bash
cd backend
pip install -r requirements.txt
pytest
```

### カバレッジ付き実行

```bash
cd /path/to/project
venv/bin/python -m pytest backend/tests/ --cov=backend --cov-config=backend/pytest.ini --cov-report=term-missing
```

### テスト構成

| ファイル | テスト数 | 説明 |
| :--- | ---: | :--- |
| `tests/test_main.py` | 131 | FastAPI エンドポイント、ミドルウェア、バックグラウンドタスク |
| `tests/test_db.py` | 75 | Firestore データベース操作 |
| `tests/test_diary_service.py` | 71 | 日記サービス（データ収集・AI生成・保存） |
| `tests/test_seed_service.py` | 38 | 種画像解析・ガイド画像生成サービス |
| `tests/test_research_agent.py` | 37 | 種袋解析・Deep Research・Web Grounding |
| `tests/test_logger.py` | 34 | 構造化ロギング・JSON Formatter |
| `tests/test_image_service.py` | 27 | 絵日記画像生成（GCS・Gemini連携） |
| `tests/test_agent.py` | 24 | AIエージェント（セッション・クエリ・SSE） |
| `tests/test_character_service.py` | 10 | キャラクター生成サービス |
| `tests/test_select_feature.py` | 5 | 指示選択機能 |
| `tests/test_seed_guide_persistence.py` | 4 | 種ガイド永続化 |
| `tests/test_character_api.py` | 4 | キャラクター生成API |
| `tests/test_vegetable_config.py` | 4 | 野菜設定・日記生成優先順位 |
| `tests/test_utils.py` | 4 | ユーティリティ関数 |
| `tests/test_async_flow.py` | 3 | 非同期フロー |

### テスト結果

- **総テスト数**: 473件
- **成功**: 全件パス ✅
- **成功率**: 100%

### コードカバレッジ

| ファイル | Stmts | Miss | Cover |
| :--- | ---: | ---: | ---: |
| `__init__.py` | 0 | 0 | 100% |
| `agent.py` | 131 | 5 | 96% |
| `character_service.py` | 71 | 2 | 97% |
| `db.py` | 322 | 9 | 97% |
| `diary_service.py` | 290 | 9 | 97% |
| `image_service.py` | 157 | 4 | 97% |
| `logger.py` | 115 | 0 | 100% |
| `main.py` | 976 | 57 | 94% |
| `research_agent.py` | 190 | 2 | 99% |
| `seed_service.py` | 261 | 9 | 97% |
| **合計** | **2513** | **97** | **96%** |

> **注記**: 未カバーの約97行の大部分は、インポートフォールバック（`except ImportError`パス）、重複エンドポイント（デッドコード）、`if __name__ == "__main__"`ガードなど、構造的にカバーが困難なコードです。

## フロントエンド（TypeScript/Jest）

### 概要

Next.js (App Router) のコンポーネントとユーティリティ関数のテスト。React Testing Libraryを使用。

### テスト実行方法

```bash
cd frontend
npm install --legacy-peer-deps
npm test
```

### ウォッチモード

```bash
npm run test:watch
```

### テスト構成

| ファイル | 説明 |
| :--- | :--- |
| `__tests__/lib/utils.test.ts` | ユーティリティ関数のテスト |
| `__tests__/components/metric-card.test.tsx` | MetricCardコンポーネントのテスト |
| `__tests__/components/weather-card.test.tsx` | WeatherCardコンポーネントのテスト |
| `__tests__/components/growth-stage-card.test.tsx` | GrowthStageCardコンポーネントのテスト |
| `__tests__/components/plant-camera.test.tsx` | PlantCameraコンポーネントのテスト |
| `__tests__/components/environment-chart.test.tsx` | EnvironmentChartコンポーネントのテスト |

### テスト結果

- **テストスイート**: 6件 すべてパス
- **総テスト数**: 42件
- **成功**: 42件
- **成功率**: 100%

## テストマトリクス

- [TEST_MATRIX.md](./TEST_MATRIX.md) - 詳細なテストケース一覧

## 総合結果

| | バックエンド | フロントエンド | 合計 |
| :--- | ---: | ---: | ---: |
| テスト数 | 473 | 42 | **515** |
| 成功 | 473 | 42 | **515** |
| 成功率 | 100% | 100% | **100%** |
| カバレッジ | 96% | — | — |
