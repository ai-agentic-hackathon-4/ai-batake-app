# テスト実装ドキュメント

Saib-AI のテスト実装に関するドキュメントです。

## テスト概要

| 項目 | バックエンド | フロントエンド | 合計 |
|------|------------|-------------|------|
| テスト数 | 473 | 42 | **515** |
| 合格率 | 100% | 100% | **100%** |
| カバレッジ | 96% | — | — |

## バックエンドテスト (Python/pytest)

### 実行方法

```bash
cd backend
pip install pytest pytest-asyncio httpx
pytest
```

### カバレッジレポート

```bash
pytest --cov=. --cov-report=html
```

### テストファイル一覧

| ファイル | テスト数 | テスト対象 |
|---------|---------|----------|
| `tests/test_main.py` | 131 | 全APIエンドポイント |
| `tests/test_db.py` | 75 | Firestoreデータベース操作 |
| `tests/test_diary_service.py` | 71 | 日記生成サービス |
| `tests/test_seed_service.py` | 38 | 栽培ガイド生成サービス |
| `tests/test_research_agent.py` | 37 | 種袋解析・Deep Research |
| `tests/test_logger.py` | 34 | 構造化ロギング |
| `tests/test_image_service.py` | 27 | 絵日記画像生成 |
| `tests/test_agent.py` | 24 | Vertex AIエージェント連携 |
| `tests/test_character_service.py` | 10 | キャラクター生成 |
| `tests/test_select_feature.py` | 5 | 野菜選択機能 |
| `tests/test_seed_guide_persistence.py` | 4 | ガイド永続化 |
| `tests/test_character_api.py` | 4 | キャラクターAPI |
| `tests/test_vegetable_config.py` | 4 | 野菜設定・優先順位 |
| `tests/test_utils.py` | 4 | ユーティリティ関数 |
| `tests/test_async_flow.py` | 3 | 非同期フロー |
| `conftest.py` | — | テスト共通フィクスチャ |
| **合計** | **473** | |

### テスト設定 (pytest.ini)

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

## フロントエンドテスト (TypeScript/Jest)

### 実行方法

```bash
cd frontend
npm test
```

### テストファイル一覧

| ファイル | テスト数 | テスト対象 |
|---------|---------|----------|
| `__tests__/utils.test.ts` | 7 | cn()ユーティリティ関数 |
| `__tests__/metric-card.test.tsx` | 5 | MetricCardコンポーネント |
| `__tests__/weather-card.test.tsx` | 9 | WeatherCardコンポーネント |
| `__tests__/growth-stage-card.test.tsx` | 9 | GrowthStageCardコンポーネント |
| `__tests__/plant-camera.test.tsx` | 6 | PlantCameraコンポーネント |
| `__tests__/environment-chart.test.tsx` | 6 | EnvironmentChartコンポーネント |
| **合計** | **42** | |

### Lintチェック

```bash
npm run lint
```

## 検証スクリプト

バックエンドには、APIの動作検証用のスクリプトも用意されています。

```bash
cd backend
python test_api.py <image_path>           # API基本テスト
python verify_unified_api.py              # 統合APIフロー検証
python verify_character_gen.py            # キャラクター生成検証
python verify_save_logic.py              # 保存ロジック検証
python verify_proxy.py                   # プロキシ動作検証
```
