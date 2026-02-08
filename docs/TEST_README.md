# テスト実装

このディレクトリには、バックエンドとフロントエンドのテストコードが含まれています。

## バックエンド（Python/pytest）

### テスト実行方法

```bash
cd backend
pip install -r requirements.txt
pytest
```

### テスト構成

| ファイル | 説明 |
| :--- | :--- |
| `tests/test_main.py` | FastAPI エンドポイントのテスト |
| `tests/test_db.py` | データベース機能のテスト |
| `tests/test_agent.py` | エージェント機能のテスト |
| `tests/test_seed_service.py` | 種画像解析サービスのテスト |
| `tests/test_diary_service.py` | 日記サービステスト |
| `tests/test_research_agent.py` | 種袋解析・Deep Researchテスト **[NEW]** |
| `tests/test_image_service.py` | 絵日記画像生成テスト **[NEW]** |
| `tests/test_select_feature.py` | 指示選択機能のテスト |
| `tests/test_seed_guide_persistence.py` | 栽培ガイド永続化テスト |
| `tests/test_async_flow.py` | 非同期フローテスト |
| `tests/test_character_api.py` | キャラクター生成APIテスト **[NEW]** |
| `tests/test_logger.py` | ロガーテスト |
| `tests/test_utils.py` | ユーティリティ関数のテスト |

### テスト結果

- **総テスト数**: 71件（+4件追加）
- **成功**: 全件パス
- **成功率**: 100%

## フロントエンド（TypeScript/Jest）

### 概要

Next.js (App Router) のコンポーネントとユーティリティ関数のテスト。React Testing Libraryを使用。
**注意:** 現在、React 19とJest環境の互換性の問題により、一部のテスト（CharacterPage）はスキップされています。

### テスト実行方法

```bash
cd frontend
npm install --legacy-peer-deps
npm test
```

### テスト構成

| ファイル | 説明 |
| :--- | :--- |
| `__tests__/lib/utils.test.ts` | ユーティリティ関数のテスト |
| `__tests__/components/metric-card.test.tsx` | MetricCardコンポーネントのテスト |
| `__tests__/components/weather-card.test.tsx` | WeatherCardコンポーネントのテスト |
| `__tests__/components/growth-stage-card.test.tsx` | GrowthStageCardコンポーネントのテスト |
| `__tests__/components/plant-camera.test.tsx` | PlantCameraコンポーネントのテスト **[NEW]** |
| `__tests__/components/environment-chart.test.tsx` | EnvironmentChartコンポーネントのテスト **[NEW]** |
| `__tests__/CharacterPage.test.tsx` | キャラクター生成ページのテスト (Skipped) |

### テスト結果

- **総テスト数**: 42件
- **成功**: 42件
- **スキップ**: 1ファイル (CharacterPage)
- **成功率**: 100% (実行分)

## テストマトリクス

- [TEST_MATRIX.md](./TEST_MATRIX.md) - 詳細なテストケース一覧

## 総合結果

- **総テスト数**: 109件（+29件追加）
- **成功**: 全件パス
- **成功率**: 100%
