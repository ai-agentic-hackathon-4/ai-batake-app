# 🌿 AI Batake App - Frontend

Next.js 16 (App Router) で構築されたAI Batake Appのフロントエンドアプリケーションです。

## 📋 概要

リアルタイムの環境モニタリング、AI栽培支援、栽培日記の表示を提供するダッシュボード型のWebアプリケーションです。

### 主な画面

| 画面 | パス | 説明 |
|------|-----|------|
| ランディング | `/` | アプリ紹介と各機能へのナビゲーション |
| ダッシュボード | `/dashboard` | センサーデータ・天気・成長段階・AIアクティビティログの表示 |
| Research Agent | `/research_agent` | 種袋画像をアップロードしてDeep Research実行 |
| Seed Guide | `/seed_guide` | 非同期栽培ガイド生成とプレビュー |
| 統合シード機能 | `/unified` | Research・Guide・Characterをワンクリックで統合実行 |
| 栽培日記 | `/diary` | 自動生成された栽培日記の閲覧 |
| キャラクター | `/character` | AI生成キャラクターの管理・閲覧 |

## 🛠️ 技術スタック

| 技術 | バージョン | 用途 |
|------|----------|------|
| Next.js | 16 | React フレームワーク (App Router) |
| React | 19 | UI ライブラリ |
| TypeScript | 5 | 型安全な開発 |
| Tailwind CSS | 4 | スタイリング |
| Radix UI | - | アクセシブルなUIプリミティブ |
| Recharts | - | グラフ描画 |
| Lucide React | - | アイコン |
| tw-animate-css | - | アニメーション |

## 📁 ファイル構成

```
frontend/
├── app/                        # Next.js App Router
│   ├── layout.tsx             # ルートレイアウト
│   ├── page.tsx               # ランディングページ
│   ├── globals.css            # グローバルスタイル
│   ├── api/                   # API Route (SSEプロキシ等)
│   ├── dashboard/
│   │   └── page.tsx           # ダッシュボード
│   ├── research_agent/
│   │   └── page.tsx           # Research Agent
│   ├── seed_guide/
│   │   └── page.tsx           # Seed Guide
│   ├── unified/
│   │   └── page.tsx           # 統合シード機能
│   ├── diary/
│   │   └── page.tsx           # 栽培日記
│   └── character/
│       └── page.tsx           # キャラクター管理
│
├── components/                 # React コンポーネント
│   ├── ui/                    # 基本UIプリミティブ (Radix UI)
│   │   ├── button.tsx        # ボタン
│   │   ├── card.tsx          # カード
│   │   ├── badge.tsx         # バッジ
│   │   ├── dialog.tsx        # ダイアログ
│   │   ├── progress.tsx      # プログレスバー
│   │   ├── scroll-area.tsx   # スクロールエリア
│   │   ├── separator.tsx     # セパレーター
│   │   └── tabs.tsx          # タブ
│   ├── metric-card.tsx        # センサーメトリクスカード
│   ├── weather-card.tsx       # 天気情報カード
│   ├── growth-stage-card.tsx  # 成長段階カード
│   ├── environment-chart.tsx  # 環境データチャート
│   ├── plant-camera.tsx       # 植物カメラ表示
│   ├── ai-activity-log.tsx    # AIアクティビティログ
│   └── step-card.tsx          # 栽培手順カード
│
├── lib/                        # ユーティリティ
│   └── utils.ts               # 共通ユーティリティ関数
│
├── __tests__/                  # テスト (42テスト)
│   ├── utils.test.ts          # ユーティリティテスト
│   ├── metric-card.test.tsx   # MetricCard テスト
│   ├── weather-card.test.tsx  # WeatherCard テスト
│   ├── growth-stage-card.test.tsx # GrowthStageCard テスト
│   ├── plant-camera.test.tsx  # PlantCamera テスト
│   └── environment-chart.test.tsx # EnvironmentChart テスト
│
├── package.json              # Node.js 依存関係
├── tsconfig.json             # TypeScript 設定
├── next.config.ts            # Next.js 設定
└── README.md                 # このファイル
```

## 🚀 セットアップ

### 前提条件

- Node.js 18以上
- npm または yarn

### インストール

```bash
cd frontend
npm install --legacy-peer-deps
```

### 開発サーバーの起動

```bash
npm run dev
```

ブラウザで http://localhost:3000 にアクセスしてください。

### ビルド

```bash
npm run build
```

## 🔌 API 連携

フロントエンドはバックエンドAPI（`:8081`）と通信します。Next.js の `rewrites` 設定により、`/api/*` へのリクエストが自動的にバックエンドにプロキシされます。

### next.config.ts の設定

```typescript
rewrites: async () => [
  {
    source: "/api/:path*",
    destination: "http://localhost:8081/api/:path*",
  },
]
```

### SSE (Server-Sent Events) プロキシ

日記のリアルタイム進捗表示には、`app/api/` のAPI Routeを経由してSSEストリームをプロキシしています。これにより、`rewrites` のバッファリング問題を回避しています。

## 🎨 スタイリング

### デザインシステム

- **カラーパレット**: ダークモード対応、HSLカスタムプロパティ
- **タイポグラフィ**: `Geist` / `Geist Mono` フォント
- **コンポーネント**: Radix UI をベースにカスタマイズ
- **アニメーション**: tw-animate-css によるスムーズなトランジション

### レスポンシブデザイン

- モバイル対応のグリッドレイアウト
- ブレイクポイント: `sm:640px`, `md:768px`, `lg:1024px`, `xl:1280px`

## 🧪 テスト

```bash
# テスト実行
npm test

# カバレッジ付き
npm test -- --coverage

# Lint チェック
npm run lint
```

### テスト構成 (42テスト)

| コンポーネント | テスト数 | 内容 |
|--------------|---------|------|
| utils.ts | 7 | ユーティリティ関数の動作確認 |
| MetricCard | 5 | メトリクスカードの表示・プロパティテスト |
| WeatherCard | 9 | 天気カードの各種状態テスト |
| GrowthStageCard | 9 | 成長段階カードの表示テスト |
| PlantCamera | 6 | カメラ画像コンポーネントテスト |
| EnvironmentChart | 6 | 環境チャートの表示テスト |

## ❓ トラブルシューティング

### `npm install` でエラーが発生する
React 19 との依存関係の互換性問題です。`--legacy-peer-deps` フラグを使用してください：
```bash
npm install --legacy-peer-deps
```

### API リクエストが 404 になる
バックエンドサーバーが `:8081` で起動しているか確認してください。

### 画像が表示されない
バックエンドの画像プロキシエンドポイント (`/api/seed-guide/image/*`, `/api/diary/*/image`, `/api/character/image`) が利用可能か確認してください。
