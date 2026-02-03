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

- `tests/test_db.py` - データベース機能のテスト
- `tests/test_agent.py` - エージェント機能のテスト
- `tests/test_main.py` - FastAPI エンドポイントのテスト
- `tests/test_seed_service.py` - 種画像解析サービスのテスト
- `tests/test_utils.py` - ユーティリティ関数のテスト
- `tests/test_select_feature.py` - 指示選択機能のテスト

### テスト結果

- **総テスト数**: 42件
- **成功**: 42件
- **失敗**: 0件
- **成功率**: 100%

## フロントエンド（TypeScript/Jest）

### テスト実行方法

```bash
cd frontend
npm install --legacy-peer-deps
npm test
```

### テスト構成

- `__tests__/lib/utils.test.ts` - ユーティリティ関数のテスト
- `__tests__/components/metric-card.test.tsx` - MetricCardコンポーネントのテスト
- `__tests__/components/weather-card.test.tsx` - WeatherCardコンポーネントのテスト
- `__tests__/components/growth-stage-card.test.tsx` - GrowthStageCardコンポーネントのテスト

### テスト結果

- **総テスト数**: 30件
- **成功**: 30件
- **失敗**: 0件
- **成功率**: 100%

## テストマトリクス

詳細なテストケース一覧は [TEST_MATRIX.md](TEST_MATRIX.md) を参照してください。

## 総合結果

- **総テスト数**: 72件
- **成功**: 72件
- **成功率**: 100%
