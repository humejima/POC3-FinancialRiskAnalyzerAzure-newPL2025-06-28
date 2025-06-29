# デプロイメントガイド

## プロジェクト構成

### コアファイル
- `main.py` - アプリケーションエントリーポイント
- `app.py` - Flask アプリケーション設定
- `models.py` - データベースモデル定義
- `routes.py` - メインルーティング（176KB）

### 機能モジュール
- `ja_management.py` - JA管理機能
- `api_endpoints.py` - API エンドポイント
- `performance_enhancer.py` - パフォーマンス最適化
- `risk_analyzer.py` - リスク分析エンジン
- `ai_account_mapper.py` - AI支援マッピング
- `reference_mapping.py` - 参照マッピング機能

### UI・テンプレート
- `templates/` - Jinja2テンプレート（24ファイル）
- `static/` - CSS/JavaScript/画像
- `attached_assets/` - アップロード済みファイル

### 設定ファイル
- `.replit` - Replit設定
- `pyproject.toml` - Python依存関係
- `README.md` - プロジェクト説明書
- `.gitignore` - Git除外設定

## 環境変数

### 必須設定
```
DATABASE_URL=postgresql://...
SESSION_SECRET=your-session-secret
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_DEPLOYMENT=your-deployment
```

## GitHubとの同期

### 同期対象ファイル
1. 全Pythonソースコード（176ファイル）
2. テンプレート・静的ファイル
3. 設定ファイル
4. ドキュメント

### 除外ファイル
- `__pycache__/`
- `.pythonlibs/`
- `app.log`
- `uploads/` （アップロードファイル）
- `data_backups/` （バックアップファイル）

## 機能確認済み項目

### JA管理
✓ JA登録・編集・削除
✓ 年度別データ表示（2021/2022）
✓ 操作ボタン年度引き継ぎ修正済み
✓ パフォーマンス最適化（1.76秒読み込み）

### 財務分析
✓ BS/PL/CF データ取り込み
✓ リスク分析（5指標）
✓ レーダーチャート表示
✓ 前年比較機能

### AI機能
✓ 勘定科目自動マッピング
✓ 参照マッピング
✓ バッチ処理最適化

## デプロイ手順

1. 環境変数設定
2. PostgreSQLデータベース準備
3. 依存関係インストール
4. データベース初期化
5. アプリケーション起動

```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## 現在の稼働状況
- システム稼働中
- 全機能動作確認済み
- パフォーマンス最適化完了
- セキュリティ対策実装済み