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

### テスト結果

- **総テスト数**: 40件
- **成功**: 37件
- **失敗**: 3件（非同期処理モックの課題）
- **成功率**: 92.5%

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

詳細なテストケース一覧は [docs/TEST_MATRIX.md](../docs/TEST_MATRIX.md) を参照してください。

## 総合結果

- **総テスト数**: 70件
- **成功**: 67件
- **成功率**: 95.7%
