"""
標準勘定科目を直接インポートするスクリプト
既存の標準勘定科目テーブルを初期化し、CSVファイルから新しいデータをインポートします
"""

import os
import pandas as pd
import logging
from app import app, db
from models import StandardAccount

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_standard_accounts(file_path, financial_statement, replace_existing=True):
    """
    CSVファイルから標準勘定科目をインポートする
    
    Args:
        file_path: CSVファイルのパス
        financial_statement: 財務諸表の種類 (bs, pl, cf)
        replace_existing: 既存のデータを置き換えるか
        
    Returns:
        tuple: (成功フラグ, メッセージ, インポート件数)
    """
    try:
        logger.info(f"Importing {financial_statement} standard accounts from {file_path}")
        
        # CSVファイルが存在するか確認
        if not os.path.exists(file_path):
            return False, f"CSVファイルが見つかりません: {file_path}", 0
        
        # CSVファイルを読み込む（エンコーディングを試行）
        encodings = ['utf-8-sig', 'utf-8', 'shift-jis', 'cp932', 'euc-jp']
        for encoding in encodings:
            try:
                logger.info(f"Trying to read CSV with encoding: {encoding}")
                df = pd.read_csv(file_path, encoding=encoding)
                logger.info(f"Successfully read CSV with encoding: {encoding}")
                break
            except Exception as e:
                logger.warning(f"Failed to read CSV with encoding {encoding}: {str(e)}")
                continue
        else:
            return False, "CSVファイルを読み込めませんでした。エンコーディングの問題が考えられます。", 0
        
        # 必要なカラムを確認
        required_columns = ['code', 'name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"CSVファイルに必要なカラムがありません: {', '.join(missing_columns)}", 0
        
        # 既存のデータを削除（指定された場合）
        if replace_existing:
            # まず関連するマッピング情報を取得
            try:
                from models import AccountMapping
                
                # マッピング情報をリセット
                mappings_to_clear = AccountMapping.query.filter_by(
                    financial_statement=financial_statement
                ).all()
                
                if mappings_to_clear:
                    # マッピング情報に関連するCSVデータのis_mappedフラグをリセット
                    try:
                        from models import CSVData
                        for mapping in mappings_to_clear:
                            csv_data = CSVData.query.filter(
                                CSVData.account_name == mapping.original_account_name,
                                CSVData.file_type == financial_statement
                            ).all()
                            
                            for data in csv_data:
                                data.is_mapped = False
                    except Exception as e:
                        logger.warning(f"CSVデータのリセット中にエラーが発生しました: {str(e)}")
                    
                    # マッピング情報を削除
                    mapping_count = AccountMapping.query.filter_by(
                        financial_statement=financial_statement
                    ).delete()
                    logger.info(f'{mapping_count}件のマッピング情報を削除しました')
            
            except Exception as e:
                logger.warning(f"マッピング情報の削除中にエラーが発生しました: {str(e)}")
            
            # 標準勘定科目を削除
            try:
                deleted_count = StandardAccount.query.filter_by(
                    financial_statement=financial_statement
                ).delete()
                logger.info(f'{deleted_count}件の標準勘定科目を削除しました')
                
                # 変更をコミット
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"標準勘定科目の削除中にエラーが発生しました: {str(e)}")
                return False, f"エラー: {str(e)}", 0
        
        # 標準勘定科目を登録
        imported_count = 0
        for _, row in df.iterrows():
            try:
                # 必須項目を取得
                code = str(row['code'])
                name = str(row['name'])
                
                # オプション項目を取得（デフォルト値を設定）
                category = str(row['category']) if 'category' in df.columns and pd.notna(row['category']) else name
                account_type = str(row['account_type']) if 'account_type' in df.columns and pd.notna(row['account_type']) else 'asset'
                display_order = int(row['display_order']) if 'display_order' in df.columns and pd.notna(row['display_order']) else int(code)
                parent_code = str(row['parent_code']) if 'parent_code' in df.columns and pd.notna(row['parent_code']) else None
                description = str(row['description']) if 'description' in df.columns and pd.notna(row['description']) else None
                statement_subtype = str(row['statement_subtype']) if 'statement_subtype' in df.columns and pd.notna(row['statement_subtype']) else None
                
                # 空文字列をNoneに変換
                parent_code = None if parent_code == '' or parent_code == 'nan' else parent_code
                description = None if description == '' or description == 'nan' else description
                statement_subtype = None if statement_subtype == '' or statement_subtype == 'nan' else statement_subtype
                
                # 新規レコードを作成
                new_account = StandardAccount(
                    code=code,
                    name=name,
                    financial_statement=financial_statement,
                    category=category,
                    account_type=account_type,
                    display_order=display_order,
                    parent_code=parent_code,
                    description=description
                )
                
                # statement_subtypeフィールドはモデルに存在しないため削除
                
                # セッションに追加
                db.session.add(new_account)
                imported_count += 1
                
                # 100件ごとにコミット（メモリ使用量を抑える）
                if imported_count % 100 == 0:
                    db.session.commit()
                    logger.info(f"{imported_count}件の標準勘定科目を登録しました")
            
            except Exception as e:
                logger.error(f"行 {imported_count+1} の処理中にエラーが発生しました: {str(e)}")
        
        # 最終コミット
        db.session.commit()
        logger.info(f"全{imported_count}件の標準勘定科目を{financial_statement}にインポートしました")
        
        return True, f"{imported_count}件の標準勘定科目を{financial_statement}にインポートしました", imported_count
    
    except Exception as e:
        db.session.rollback()
        logger.exception(f"標準勘定科目のインポート中にエラーが発生しました: {str(e)}")
        return False, f"エラー: {str(e)}", 0

def import_all_standard_accounts():
    """
    BS、PL、CFの標準勘定科目をすべてインポートする
    
    Returns:
        list: 各インポート処理の結果
    """
    results = []
    
    # アップロードフォルダを設定
    upload_folder = 'uploads'
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    # アップロードフォルダのパスを確認
    if not os.path.exists(upload_folder):
        try:
            os.makedirs(upload_folder)
            logger.info(f"アップロードフォルダを作成しました: {upload_folder}")
        except Exception as e:
            logger.error(f"アップロードフォルダの作成に失敗しました: {str(e)}")
            return [f"エラー: アップロードフォルダの作成に失敗しました: {str(e)}"]
    
    # BSのインポート
    bs_path = os.path.join(upload_folder, 'standard_bs_accounts.csv')
    if os.path.exists(bs_path):
        success, message, _ = import_standard_accounts(bs_path, 'bs')
        results.append(f"BS: {message}")
    else:
        results.append("BS: ファイルが見つかりません")
    
    # PLのインポート
    pl_path = os.path.join(upload_folder, 'standard_pl_accounts.csv')
    if os.path.exists(pl_path):
        success, message, _ = import_standard_accounts(pl_path, 'pl')
        results.append(f"PL: {message}")
    else:
        results.append("PL: ファイルが見つかりません")
    
    # CFのインポート
    cf_path = os.path.join(upload_folder, 'standard_cf_accounts.csv')
    if os.path.exists(cf_path):
        success, message, _ = import_standard_accounts(cf_path, 'cf')
        results.append(f"CF: {message}")
    else:
        results.append("CF: ファイルが見つかりません")
    
    return results

if __name__ == "__main__":
    # アプリケーションコンテキストを設定
    with app.app_context():
        # 全ての標準勘定科目をインポート
        results = import_all_standard_accounts()
        
        for result in results:
            print(result)