# JA財務リスク分析システム - Pythonプログラム一覧表

## コアシステム・アプリケーション基盤

| ファイル名 | 主要機能 | 備考 |
|-----------|---------|------|
| app.py | Flaskアプリケーション設定・データベース初期化 | システム基盤 |
| main.py | アプリケーションエントリーポイント | Gunicorn起動用 |
| models.py | データベースモデル定義 | 全テーブル定義 |
| routes.py | Webルーティング・画面表示制御 | 主要画面制御 |

## 財務分析・計算エンジン

| ファイル名 | 主要機能 | 備考 |
|-----------|---------|------|
| financial_indicators.py | 財務指標計算エンジン | 5カテゴリ指標計算 |
| risk_analyzer.py | リスクスコア算出・評価分析 | 総合リスク評価 |
| account_calculator.py | 勘定科目合計値計算 | 計算式エンジン |

## データ処理・インポート

| ファイル名 | 主要機能 | 備考 |
|-----------|---------|------|
| data_processor.py | CSVデータ処理・インポート | データ検証含む |
| create_account_balances.py | 標準勘定科目残高データ作成 | 残高データ生成 |

## AI・自動マッピング機能

| ファイル名 | 主要機能 | 備考 |
|-----------|---------|------|
| ai_account_mapper.py | AI支援勘定科目自動マッピング | Azure OpenAI連携 |
| ai_mapping_rules.py | JA預金科目マッピングルール | ルールベース判定 |
| batch_mapping.py | バッチ処理一括マッピング | 大量データ対応 |
| direct_sql_mapping.py | SQL直接マッピング処理 | 高速処理 |

## バックアップ・データ保護

| ファイル名 | 主要機能 | 備考 |
|-----------|---------|------|
| backup_system.py | データバックアップ・リストア | JSON形式保存 |
| backup_api.py | バックアップ機能API | 2段階確認付き |

## API・エンドポイント

| ファイル名 | 主要機能 | 備考 |
|-----------|---------|------|
| api_endpoints.py | REST APIエンドポイント定義 | 主要API群 |
| clear_cache_route.py | キャッシュクリア機能 | 特殊ルート |

## 勘定科目管理・追加

| ファイル名 | 主要機能 | 備考 |
|-----------|---------|------|
| add_current_assets.py | 流動資産科目追加 | 親子関係設定 |
| add_total_accounts.py | BS合計科目追加 | 標準勘定科目マスタ |

## データ確認・検証ツール

| ファイル名 | 主要機能 | 備考 |
|-----------|---------|------|
| check_data.py | JA・年度データ状態確認 | 汎用データチェック |
| check_balance_data.py | 残高データ状態確認 | 財務諸表別確認 |
| check_profitability_data.py | 収益性指標データ確認 | 利益関連科目チェック |
| check_safety_indicators_for_chart.py | レーダーチャート用安全性指標確認 | チャート表示検証 |
| check_ja_data.py | JAデータ・CSV状態確認 | データ連携確認 |
| check_accounts_display_order.py | 勘定科目表示順序確認 | 表示制御 |
| check_analysis_results.py | 分析結果確認 | 計算結果検証 |
| check_and_fix_ja004.py | JA004安全性指標確認・修正 | 特定JA対応 |
| check_api_endpoints.py | APIエンドポイント確認 | API動作確認 |
| check_available_data.py | 利用可能データ確認 | データ可用性チェック |
| check_balances.py | 勘定科目残高確認 | 残高値チェック |
| check_bs_data.py | BSデータ確認 | 貸借対照表データ |
| check_cf_account_display.py | CF勘定科目表示確認 | キャッシュフロー表示 |
| check_cf_accounts.py | CF勘定科目確認 | CF科目チェック |
| check_cf_balances.py | CF残高確認 | CF残高値 |
| check_cf_data.py | CFデータ確認 | キャッシュフロー全般 |
| check_cf_data_updated.py | CF更新データ確認 | CF更新状況 |
| check_cf_values.py | CF値確認 | CF計算値 |
| check_correct_code.py | 正確なコード確認 | コード整合性 |
| check_csv_data_category.py | CSVデータカテゴリ確認 | データ分類確認 |
| check_db.py | データベース確認 | DB状態チェック |
| check_debt_ratio.py | 負債比率確認 | 安全性指標 |
| check_efficiency_indicators.py | 効率性指標確認 | 効率性評価 |
| check_indicators_json.py | 指標JSON構造確認 | 計算結果構造 |
| check_ja004_efficiency.py | JA004効率性指標確認 | 特定JA効率性 |
| check_liquidity_balances.py | 流動性指標残高確認 | 流動性関連データ |
| check_mappings.py | マッピング状況確認 | マッピング調査 |
| check_net_income.py | 当期利益確認 | 収益性計算要素 |
| check_parent_child_structure.py | 親子関係構造確認 | 階層構造診断 |
| check_pl.py | PLデータ確認 | 損益計算書 |
| check_pl_balances.py | PL残高確認 | PL残高値 |
| check_pl_data.py | PLデータ詳細確認 | PL全般チェック |
| check_pl_mappings.py | PLマッピング確認 | PL科目マッピング |
| check_pl_mappings_correct.py | PL正確マッピング確認 | PL精度チェック |
| check_pl_net_income.py | PL当期純利益確認 | PL利益科目 |
| check_pl_parents.py | PL親勘定科目確認 | PL階層構造 |
| check_risk_scores.py | リスクスコア確認 | リスク評価値 |
| check_safety_accounts_ui.py | 安全性指標UI確認 | UI表示検証 |
| check_safety_data.py | 安全性データ確認 | 安全性指標データ |
| check_safety_indicator_data.py | 安全性指標データ詳細 | 安全性計算要素 |
| check_standard_accounts.py | 標準勘定科目確認 | 標準科目チェック |
| check_total_accounts.py | 合計勘定科目確認 | 合計科目チェック |

## デバッグ・トラブルシューティング

| ファイル名 | 主要機能 | 備考 |
|-----------|---------|------|
| debug_csv_values.py | CSV値デバッグ | CSV内容確認 |
| debug_direct_mapping.py | 直接マッピングデバッグ | マッピング処理確認 |
| debug_exact_match.py | 完全一致デバッグ | 一致処理確認 |
| debug_import.py | インポートデバッグ | データ取込確認 |
| debug_mapping.py | マッピングデバッグ | マッピング全般 |
| debug_safety_indicators.py | 安全性指標デバッグ | 安全性計算確認 |
| debug_utils.py | デバッグユーティリティ | 共通デバッグ機能 |

## データ修正・メンテナンス

| ファイル名 | 主要機能 | 備考 |
|-----------|---------|------|
| fix_account_parent_codes.py | 勘定科目親コード修正 | 階層構造修正 |
| fix_account_totals.py | 勘定科目合計修正 | 合計値修正 |
| fix_accounts_display.py | 勘定科目表示修正 | 表示制御修正 |
| fix_ai_mapping.py | AIマッピング修正 | AI処理修正 |
| fix_all_liquidity_displays.py | 流動性表示修正 | 流動性UI修正 |
| fix_analysis_results.py | 分析結果修正 | 計算結果修正 |
| fix_available_data.py | 利用可能データ修正 | データ可用性修正 |
| fix_balance_data.py | 残高データ修正 | 残高値修正 |
| fix_bs_parent_codes.py | BS親コード修正 | BS階層修正 |
| fix_cash_deposits_total.py | 現金預金合計修正 | 流動資産修正 |
| fix_cf_operating.py | CF営業活動修正 | CF計算修正 |
| fix_cf_totals.py | CF合計修正 | CF総計修正 |
| fix_cf_triangle_minus.py | CF三角マイナス修正 | CF表示修正 |
| fix_chart_labels.py | チャートラベル修正 | 表示文字修正 |
| fix_current_assets_code.py | 流動資産コード修正 | 科目コード修正 |
| delete_and_recalculate.py | 削除・再計算処理 | データリセット |

## 機能追加・データ作成

| ファイル名 | 主要機能 | 備考 |
|-----------|---------|------|
| ensure_ja006.py | JA006データ保証 | 特定JAデータ確認 |
| ensure_ja_exists.py | JA存在保証 | JA登録確認 |
| demo_data_setup.py | デモデータ設定 | 初期データ作成 |

## 直接修正・最適化

| ファイル名 | 主要機能 | 備考 |
|-----------|---------|------|
| direct_fix_ai_endpoints.py | AI APIエンドポイント直接修正 | API修正 |
| direct_fix_efficiency.py | 効率性指標直接修正 | 効率性計算修正 |
| direct_fix_indicators.py | 指標直接修正 | 指標計算修正 |
| direct_fix_pl_balances.py | PL残高直接修正 | PL値修正 |
| direct_import_bs.py | BS直接インポート | BSデータ取込 |
| direct_import_pl_cf.py | PL・CF直接インポート | PL・CFデータ取込 |

## テストデータ作成

| ファイル名 | 主要機能 | 備考 |
|-----------|---------|------|
| create_minimal_test_data.py | 最小限テストデータ作成 | テスト用最小データ |
| create_reference_mapping_test_data.py | 参照マッピングテストデータ | マッピング機能テスト |
| create_simple_test_data.py | 簡易テストデータ作成 | 基本テストデータ |
| create_simple_test_data_fixed.py | 修正版簡易テストデータ | 修正済みテストデータ |
| create_test_data_final.py | 最終版テストデータ | 完成版テストデータ |
| create_test_data_schema_correct.py | スキーマ正確テストデータ | DB構造準拠テストデータ |

## システム統計

- **総ファイル数**: 100+ Python ファイル
- **主要カテゴリ**: 11カテゴリ
- **コア機能**: 財務分析、AI マッピング、データ保護
- **技術スタック**: Python 3.11 + Flask + PostgreSQL + Azure OpenAI