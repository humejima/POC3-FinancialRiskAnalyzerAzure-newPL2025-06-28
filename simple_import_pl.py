"""
PLの標準勘定科目を直接インポートするシンプルなスクリプト
より単純な方法でCSVからデータをインポートします
"""

import os
import pandas as pd
import logging
from app import app, db
from models import StandardAccount

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def simple_import_pl():
    """
    PLの標準勘定科目を直接インポートする
    
    Returns:
        tuple: (成功フラグ, メッセージ)
    """
    try:
        # CSVファイルのパス
        csv_path = 'uploads/standard_pl_accounts.csv'
        
        # 既存のPL勘定科目を削除
        deleted_count = StandardAccount.query.filter_by(financial_statement='pl').delete()
        logger.info(f"{deleted_count}件のPL標準勘定科目を削除しました")
        db.session.commit()
        
        # CSVファイルを読み込む
        df = pd.read_csv(csv_path)
        logger.info(f"CSVファイル読み込み完了: {len(df)}行")
        
        # データをインポート
        count = 0
        for _, row in df.iterrows():
            try:
                # 必須項目を取得
                code = str(row['code'])
                name = str(row['name'])
                category = str(row['category'])
                account_type = str(row['account_type'])
                display_order = int(row['display_order'])
                
                # オプション項目を取得
                parent_code = str(row['parent_code']) if 'parent_code' in df.columns and pd.notna(row['parent_code']) and str(row['parent_code']) != '' else None
                description = str(row['description']) if 'description' in df.columns and pd.notna(row['description']) and str(row['description']) != '' else None
                
                # レコードを作成
                account = StandardAccount()
                account.code = code
                account.name = name
                account.category = category
                account.financial_statement = 'pl'
                account.account_type = account_type
                account.display_order = display_order
                account.parent_code = parent_code
                account.description = description
                
                # 追加
                db.session.add(account)
                count += 1
                
                # 20件ごとにコミット
                if count % 20 == 0:
                    db.session.commit()
                    logger.info(f"{count}件のPL標準勘定科目を登録しました")
            
            except Exception as e:
                logger.error(f"PLインポート中にエラーが発生しました (行 {_+1}): {str(e)}")
        
        # 最終コミット
        db.session.commit()
        logger.info(f"合計{count}件のPL標準勘定科目を登録しました")
        
        return True, f"{count}件のPL標準勘定科目を登録しました"
    
    except Exception as e:
        db.session.rollback()
        logger.exception(f"PL標準勘定科目のインポートに失敗しました: {str(e)}")
        return False, f"エラー: {str(e)}"

def simple_import_cf():
    """
    CFの標準勘定科目を直接インポートする
    
    Returns:
        tuple: (成功フラグ, メッセージ)
    """
    try:
        # CSVファイルのパス
        csv_path = 'uploads/standard_cf_accounts.csv'
        
        # 既存のCF勘定科目を削除
        deleted_count = StandardAccount.query.filter_by(financial_statement='cf').delete()
        logger.info(f"{deleted_count}件のCF標準勘定科目を削除しました")
        db.session.commit()
        
        # CSVファイルを読み込む
        df = pd.read_csv(csv_path)
        logger.info(f"CSVファイル読み込み完了: {len(df)}行")
        
        # データをインポート
        count = 0
        for _, row in df.iterrows():
            try:
                # 必須項目を取得
                code = str(row['code'])
                name = str(row['name'])
                category = str(row['category'])
                account_type = str(row['account_type'])
                display_order = int(row['display_order'])
                
                # オプション項目を取得
                parent_code = str(row['parent_code']) if 'parent_code' in df.columns and pd.notna(row['parent_code']) and str(row['parent_code']) != '' else None
                description = str(row['description']) if 'description' in df.columns and pd.notna(row['description']) and str(row['description']) != '' else None
                
                # レコードを作成
                account = StandardAccount()
                account.code = code
                account.name = name
                account.category = category
                account.financial_statement = 'cf'
                account.account_type = account_type
                account.display_order = display_order
                account.parent_code = parent_code
                account.description = description
                
                # 追加
                db.session.add(account)
                count += 1
                
                # 20件ごとにコミット
                if count % 20 == 0:
                    db.session.commit()
                    logger.info(f"{count}件のCF標準勘定科目を登録しました")
            
            except Exception as e:
                logger.error(f"CFインポート中にエラーが発生しました (行 {_+1}): {str(e)}")
        
        # 最終コミット
        db.session.commit()
        logger.info(f"合計{count}件のCF標準勘定科目を登録しました")
        
        return True, f"{count}件のCF標準勘定科目を登録しました"
    
    except Exception as e:
        db.session.rollback()
        logger.exception(f"CF標準勘定科目のインポートに失敗しました: {str(e)}")
        return False, f"エラー: {str(e)}"

if __name__ == "__main__":
    # アプリケーションコンテキストを設定
    with app.app_context():
        # PLの標準勘定科目をインポート
        success_pl, message_pl = simple_import_pl()
        print(message_pl)
        
        # CFの標準勘定科目をインポート
        success_cf, message_cf = simple_import_cf()
        print(message_cf)