# JA財務リスク分析システム 基本設計書

## 1. システム概要

### 1.1 目的
本システムは、JA（日本農業協同組合）の財務諸表データを分析し、経営リスクを評価するためのシステムである。財務データの取り込み、標準勘定科目へのマッピング、財務指標の計算、リスク分析を行い、JAの経営状態を可視化する。

### 1.2 システムの全体像
本システムは、以下の4つの主要機能から構成される：
1. データ取込機能：CSVファイルから財務データを取り込み、データベースに格納する
2. 勘定科目マッピング機能：取り込んだデータを標準勘定科目に紐付ける
3. 財務指標計算機能：標準化されたデータから各種財務指標を計算する
4. リスク評価機能：財務指標に基づいてリスク評価を行い、改善提案を提示する

### 1.3 対象ユーザー
- JA経営分析担当者
- JA経営コンサルタント
- 金融機関融資担当者

## 2. システム機能設計

### 2.1 画面構成
システムは以下の画面から構成される：
1. ログイン画面
2. データ管理画面
   - データインポート機能
   - データ一覧表示
3. マッピング画面
   - 勘定科目マッピング機能
   - AI支援マッピング機能
4. 勘定科目一覧画面
   - 標準勘定科目残高の表示
5. 分析画面
   - 財務指標の計算結果表示
   - リスク評価結果表示
6. 設定画面
   - ユーザー管理
   - 標準勘定科目の管理

### 2.2 主要機能詳細

#### 2.2.1 データ取込機能
- CSV/Excel形式の財務データファイルをアップロード
- ファイル形式の自動判別（BS/PL/CF）
- データの整合性チェック
- JAコード、年度、データ種別でのデータ管理

#### 2.2.2 勘定科目マッピング機能
- 取り込んだ勘定科目の標準科目へのマッピング
- AIによる自動マッピング提案
  - OpenAI APIを活用した高精度マッピング
  - 文字列類似度によるマッピング
  - 過去のマッピング履歴の活用
- マッピング結果の手動修正・確認機能
- 勘定科目の階層関係の管理

#### 2.2.3 財務指標計算機能
以下のカテゴリの財務指標を計算する：
1. 流動性指標
   - 流動比率
   - 当座比率
   - 現金比率
2. 安全性指標
   - 自己資本比率
   - 負債比率
   - 固定比率
3. 収益性指標
   - ROA（総資産利益率）
   - ROE（自己資本利益率）
   - 売上高利益率
4. 効率性指標
   - 総資産回転率
   - 売上債権回転日数
5. キャッシュフロー指標
   - CF対負債比率
   - CF対売上比率
   - CF対純利益比率
   - フリーキャッシュフロー

#### 2.2.4 リスク評価機能
- 指標ごとのリスクスコア計算（1-5段階）
- カテゴリごとの総合リスク評価
- 改善提案の自動生成
- 前年度との比較分析
- 複数JAの比較分析

### 2.3 非機能要件

#### 2.3.1 性能要件
- 画面応答時間：3秒以内
- 同時アクセスユーザー数：最大20ユーザー
- データ処理容量：年間1,000件のJAデータ

#### 2.3.2 セキュリティ要件
- ユーザー認証機能
- ロールベースのアクセス制御
- データベース暗号化
- セキュアなAPI通信（HTTPS）

#### 2.3.3 可用性要件
- システム稼働時間：24時間365日
- バックアップ：日次
- 障害復旧時間：4時間以内

## 3. データベース設計

### 3.1 ER図
主要テーブル間の関連を以下に示す：
```
JA(ja_code) <-- CSVData(ja_code)
JA(ja_code) <-- StandardAccountBalance(ja_code)
JA(ja_code) <-- AnalysisResult(ja_code)
StandardAccount <-- StandardAccountBalance(standard_account_code)
```

### 3.2 テーブル構成

#### 3.2.1 JA（農協基本情報）
| フィールド名 | データ型 | 説明 |
|------------|---------|------|
| ja_code | VARCHAR(10) | JAコード（PK） |
| name | VARCHAR(100) | JA名称 |
| prefecture | VARCHAR(20) | 都道府県 |
| last_updated | DATETIME | 最終更新日時 |
| year | INTEGER | 年度 |
| available_data | VARCHAR(10) | 利用可能データ種別（bs,pl,cf） |

#### 3.2.2 CSVData（インポートCSVデータ）
| フィールド名 | データ型 | 説明 |
|------------|---------|------|
| id | INTEGER | ID（PK） |
| ja_code | VARCHAR(10) | JAコード（FK） |
| year | INTEGER | 年度 |
| file_type | VARCHAR(2) | ファイル種別（bs/pl/cf） |
| row_number | INTEGER | 行番号 |
| account_name | VARCHAR(100) | 勘定科目名 |
| category | VARCHAR(50) | カテゴリ |
| current_value | FLOAT | 当期値 |
| previous_value | FLOAT | 前期値 |
| is_mapped | BOOLEAN | マッピング済みフラグ |
| created_at | DATETIME | 作成日時 |

#### 3.2.3 StandardAccount（標準勘定科目）
| フィールド名 | データ型 | 説明 |
|------------|---------|------|
| id | INTEGER | ID（PK） |
| code | VARCHAR(10) | 勘定科目コード（UK） |
| name | VARCHAR(100) | 勘定科目名 |
| category | VARCHAR(50) | カテゴリ |
| financial_statement | VARCHAR(2) | 財務諸表種別（bs/pl/cf） |
| account_type | VARCHAR(20) | 勘定科目タイプ |
| display_order | INTEGER | 表示順 |
| parent_code | VARCHAR(10) | 親科目コード |
| description | TEXT | 説明 |

#### 3.2.4 StandardAccountBalance（標準勘定科目残高）
| フィールド名 | データ型 | 説明 |
|------------|---------|------|
| id | INTEGER | ID（PK） |
| ja_code | VARCHAR(10) | JAコード（FK） |
| year | INTEGER | 年度 |
| statement_type | VARCHAR(2) | 財務諸表種別（bs/pl/cf） |
| statement_subtype | VARCHAR(20) | 財務諸表サブタイプ |
| standard_account_code | VARCHAR(10) | 標準勘定科目コード |
| standard_account_name | VARCHAR(100) | 標準勘定科目名 |
| current_value | FLOAT | 当期値 |
| previous_value | FLOAT | 前期値 |
| created_at | DATETIME | 作成日時 |

#### 3.2.5 AccountMapping（勘定科目マッピング）
| フィールド名 | データ型 | 説明 |
|------------|---------|------|
| id | INTEGER | ID（PK） |
| ja_code | VARCHAR(10) | JAコード |
| original_account_name | VARCHAR(100) | 原勘定科目名 |
| standard_account_code | VARCHAR(10) | 標準勘定科目コード |
| standard_account_name | VARCHAR(100) | 標準勘定科目名 |
| financial_statement | VARCHAR(2) | 財務諸表種別（bs/pl/cf） |
| confidence | FLOAT | 信頼度 |
| rationale | TEXT | 根拠 |
| created_at | DATETIME | 作成日時 |

#### 3.2.6 AnalysisResult（分析結果）
| フィールド名 | データ型 | 説明 |
|------------|---------|------|
| id | INTEGER | ID（PK） |
| ja_code | VARCHAR(10) | JAコード（FK） |
| year | INTEGER | 年度 |
| analysis_type | VARCHAR(20) | 分析タイプ |
| indicator_name | VARCHAR(50) | 指標名 |
| indicator_value | FLOAT | 指標値 |
| benchmark | FLOAT | ベンチマーク値 |
| risk_score | INTEGER | リスクスコア（1-5） |
| risk_level | VARCHAR(10) | リスクレベル |
| analysis_result | TEXT | 分析結果 |
| formula | VARCHAR(500) | 計算式 |
| calculation | TEXT | 計算過程 |
| accounts_used | TEXT | 使用勘定科目（JSON） |
| created_at | DATETIME | 作成日時 |

#### 3.2.7 User（ユーザー情報）
| フィールド名 | データ型 | 説明 |
|------------|---------|------|
| id | INTEGER | ID（PK） |
| username | VARCHAR(64) | ユーザー名（UK） |
| email | VARCHAR(120) | メールアドレス（UK） |
| password_hash | VARCHAR(256) | パスワードハッシュ |
| role | VARCHAR(20) | ロール（admin/analyst/viewer） |

## 4. 処理フロー

### 4.1 データインポートフロー
1. ユーザーがCSVファイルをアップロード
2. システムがファイル形式を判別（BS/PL/CF）
3. データの整合性をチェック
4. データをCSVDataテーブルに格納
5. マッピング状況の初期化

### 4.2 勘定科目マッピングフロー
1. CSVDataからマッピング未実施のデータを抽出
2. 完全一致マッピングの実行
3. AI支援マッピングの実行
   a. 文字列類似度による提案
   b. OpenAI APIによる提案
4. ユーザーによる確認・修正
5. マッピング結果の保存
6. 標準勘定科目残高の計算・更新

### 4.3 財務指標計算フロー
1. 標準勘定科目残高からデータを取得
2. 流動性指標の計算
3. 安全性指標の計算
4. 収益性指標の計算
5. 効率性指標の計算
6. キャッシュフロー指標の計算
7. 計算結果の保存

### 4.4 リスク評価フロー
1. 財務指標データの取得
2. 指標ごとのリスクスコア計算
3. カテゴリごとの総合リスク評価
4. 改善提案の生成
5. 評価結果の表示

## 5. 外部連携

### 5.1 OpenAI API連携
- 機能：勘定科目マッピング支援
- 利用モデル：GPT-4o
- 入力：勘定科目名、財務諸表種別、標準勘定科目リスト
- 出力：マッピング提案（標準勘定科目コード、信頼度、根拠）

### 5.2 データエクスポート機能
- エクスポート形式：CSV、Excel、PDF
- 対象データ：財務指標一覧、リスク評価結果、標準勘定科目残高

## 6. 特記事項

### 6.1 特別な計算ロジック
- 親勘定科目（例：流動資産）の値がゼロの場合、子勘定科目の合計を計算
- フリーキャッシュフローの計算式：事業活動によるキャッシュ・フロー - 投資活動によるキャッシュ・フロー
- 流動資産は、1000（現金預け金）、1600（有価証券）、1700（貸出金）、1800（外国為替）、1900（その他資産）の合計

### 6.2 キャッシュフロー指標の特記事項
- 事業活動キャッシュフロー（コード11000）を使用して以下の指標を計算
  - CF対負債比率：事業活動CF ÷ 負債の部合計
  - CF対売上比率：事業活動CF ÷ 経常収益
  - CF対純利益比率：事業活動CF ÷ 当期純利益
  - フリーキャッシュフロー：事業活動CF - 投資活動CF

### 6.3 システム運用上の注意点
- 標準勘定科目コードは小数点を含まない整数
- 「△」（三角）記号はマイナス値として処理
- 勘定科目の親子関係は適切に管理し、合計値の再計算が必要
- AIマッピングの信頼度が70%未満の場合は手動確認が必要

## 7. 今後の拡張計画

### 7.1 短期拡張計画（6ヶ月以内）
- 複数年度データの時系列分析機能
- JAグループ間の比較分析機能
- レポート自動生成機能

### 7.2 中長期拡張計画（1-2年）
- 予測分析機能（機械学習活用）
- モバイルアプリ対応
- 外部データ連携機能の拡充

## 8. 用語集

| 用語 | 説明 |
|-----|------|
| JA | 日本農業協同組合（Japan Agricultural Cooperatives） |
| BS | 貸借対照表（Balance Sheet） |
| PL | 損益計算書（Profit and Loss Statement） |
| CF | キャッシュフロー計算書（Cash Flow Statement） |
| ROA | 総資産利益率（Return on Assets） |
| ROE | 自己資本利益率（Return on Equity） |