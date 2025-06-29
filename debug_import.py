"""
標準勘定科目インポート機能のデバッグ用スクリプト
CSVファイルを直接読み込んで処理するため、インポート時のエラーを特定しやすくする
"""
import os
import pandas as pd
import logging
from app import app, db
from models import StandardAccount

# ロギング設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_import_standard_accounts(filepath, financial_statement):
    """
    標準勘定科目CSVをインポートするデバッグ関数
    
    Args:
        filepath: CSVファイルのパス
        financial_statement: 財務諸表タイプ(bs, pl, cf)
    """
    try:
        logger.info(f"ファイル {filepath} から{financial_statement}の標準勘定科目をインポート開始")
        
        # ファイルの存在チェック
        if not os.path.exists(filepath):
            logger.error(f"ファイル {filepath} が存在しません")
            return
        
        # エンコーディングを自動検出して読み込み
        try:
            df = pd.read_csv(filepath, encoding='utf-8-sig')
        except:
            try:
                df = pd.read_csv(filepath, encoding='utf-8')
            except:
                try:
                    df = pd.read_csv(filepath, encoding='shift-jis')
                except Exception as e:
                    logger.error(f"CSVファイル読み込みエラー: {str(e)}")
                    return
        
        logger.info(f"CSVファイル読み込み成功: {len(df)}行")
        logger.info(f"列名: {', '.join(df.columns)}")
        
        # 必要なカラムを確認
        required_columns = ['code', 'name', 'category']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"必要なカラムがありません: {', '.join(missing_columns)}")
            return
            
        # データサンプルを表示
        logger.info("データサンプル:")
        for idx, row in df.head(3).iterrows():
            logger.info(f"  {idx}: {dict(row)}")
        
        # 重複データをチェック
        duplicated_codes = df[df.duplicated('code')]['code'].tolist()
        if duplicated_codes:
            logger.warning(f"重複するコードがあります: {', '.join(map(str, duplicated_codes))}")
        
        # インポート処理
        imported_count = 0
        
        with app.app_context():
            # 既存の標準勘定科目を取得
            existing_accounts = {account.code: account for account in StandardAccount.query.filter_by(
                financial_statement=financial_statement
            ).all()}
            
            logger.info(f"既存の標準勘定科目: {len(existing_accounts)}件")
            
            # インポート行数をログに出力
            logger.info(f"インポート対象: {len(df)}行")
            
            # 行ごとに処理
            for idx, row in df.iterrows():
                try:
                    account_code = str(row['code']).strip()
                    account_name = str(row['name']).strip()
                    account_category = str(row['category']).strip()
                    
                    # オプションのフィールド
                    account_type = str(row.get('account_type', '')).strip() if 'account_type' in row else ''
                    parent_code = str(row.get('parent_code', '')).strip() if 'parent_code' in row and not pd.isna(row['parent_code']) else None
                    display_order = int(row.get('display_order', idx + 1)) if 'display_order' in row and not pd.isna(row['display_order']) else idx + 1
                    
                    logger.info(f"処理: {account_code} - {account_name} ({account_category})")
                    
                    # 既存のアカウントがあるかチェック
                    if account_code in existing_accounts:
                        # 既存アカウントを更新
                        account = existing_accounts[account_code]
                        account.name = account_name
                        account.category = account_category
                        if account_type:
                            account.account_type = account_type
                        if parent_code:
                            account.parent_code = parent_code
                        account.display_order = display_order
                        logger.info(f"  既存アカウント更新: {account_code}")
                    else:
                        # 新しいアカウントを作成
                        new_account = StandardAccount(
                            code=account_code,
                            name=account_name,
                            category=account_category,
                            account_type=account_type,
                            parent_code=parent_code,
                            display_order=display_order,
                            financial_statement=financial_statement
                        )
                        db.session.add(new_account)
                        logger.info(f"  新規アカウント追加: {account_code}")
                    
                    imported_count += 1
                    
                    # 10件ごとにコミット
                    if imported_count % 10 == 0:
                        db.session.commit()
                        logger.info(f"  {imported_count}件をコミット")
                
                except Exception as e:
                    import traceback
                    logger.error(f"行 {idx} の処理中にエラー: {str(e)}")
                    logger.error(traceback.format_exc())
                    db.session.rollback()
            
            # 残りの変更をコミット
            db.session.commit()
            logger.info(f"合計 {imported_count} 件の標準勘定科目をインポートしました")
    
    except Exception as e:
        import traceback
        logger.error(f"インポート処理全体でエラーが発生: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # BSの標準勘定科目をインポート
    debug_import_standard_accounts('uploads/standard_bs_accounts.csv', 'bs')
    # PLの標準勘定科目をインポート
    # debug_import_standard_accounts('uploads/standard_pl_accounts.csv', 'pl')
    # CFの標準勘定科目をインポート
    # debug_import_standard_accounts('uploads/standard_cf_accounts.csv', 'cf')