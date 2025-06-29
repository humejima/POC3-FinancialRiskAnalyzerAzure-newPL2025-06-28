"""
PLの標準勘定科目のみをCSVからインポートするスクリプト
"""

import pandas as pd
import logging
from app import app, db
from models import StandardAccount

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_pl_from_csv():
    """
    PLの標準勘定科目をCSVからインポートする
    
    Returns:
        tuple: (成功フラグ, メッセージ)
    """
    try:
        # CSVファイルのパス
        csv_path = 'uploads/standard_pl_updated.csv'
        
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
                account = StandardAccount()
                account.code = str(row['code'])
                account.name = str(row['name'])
                account.category = str(row['category'])
                account.financial_statement = 'pl'
                account.account_type = str(row['account_type'])
                account.display_order = int(row['display_order'])
                
                # parent_codeがある場合のみ設定
                if pd.notna(row.get('parent_code', None)) and str(row['parent_code']) != '':
                    account.parent_code = str(row['parent_code'])
                else:
                    account.parent_code = None
                
                # descriptionがある場合のみ設定
                if pd.notna(row.get('description', None)) and str(row['description']) != '':
                    account.description = str(row['description'])
                else:
                    account.description = None
                
                db.session.add(account)
                count += 1
                
                # 10件ごとにコミット (少ない単位でコミット)
                if count % 10 == 0:
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

if __name__ == "__main__":
    with app.app_context():
        # PLの標準勘定科目をインポート
        success_pl, message_pl = import_pl_from_csv()
        print(message_pl)