import pandas as pd
from app import app, db
from models import StandardAccount
import logging

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_cf_accounts_new(csv_file):
    """
    Import CF standard accounts from new format CSV file and replace existing CF accounts
    
    Args:
        csv_file: Path to CSV file
    
    Returns:
        int: Number of accounts imported
    """
    with app.app_context():
        # Delete only existing CF accounts
        db.session.query(StandardAccount).filter_by(financial_statement='cf').delete()
        db.session.commit()
        logger.info("Deleted existing CF accounts")
        
        # CSVファイルの読み込み
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        logger.info(f"Loaded CSV file with {len(df)} rows")
        
        # アカウント追加
        count = 0
        for _, row in df.iterrows():
            try:
                # Skip header row if it exists
                if row['科目コード'] == '科目コード':
                    continue
                    
                code = str(row['科目コード'])
                name = row['科目名']
                category = row['科目区分']
                
                # 財務諸表区分が'CF'であることを確認
                if row['財務諸表区分'] != 'CF':
                    logger.warning(f"Skipping non-CF entry: {code} - {name}")
                    continue
                    
                # 表示順は科目コードの数値を使用
                display_order = int(code)
                
                # 上位科目コードを説明に使用し、parent_codeフィールドに設定
                parent_code = row.get('上位科目コード', '')
                description = f"上位科目コード: {parent_code}" if parent_code else "最上位科目"
                
                # Create standard account
                account = StandardAccount(
                    code=code,
                    name=name,
                    category=category,
                    financial_statement='cf',  # 財務諸表区分を小文字に変換
                    account_type=category,     # 科目区分をアカウントタイプとして使用
                    display_order=display_order,
                    description=description,
                    parent_code=parent_code if parent_code else None  # 親コードを設定
                )
                
                db.session.add(account)
                count += 1
                logger.info(f"Added CF account: {code} - {name}")
                
            except Exception as e:
                logger.error(f"Error importing CF row: {row.to_dict()}\nError: {str(e)}")
                continue
        
        db.session.commit()
        logger.info(f"Imported {count} CF standard accounts.")
        return count

if __name__ == "__main__":
    import_cf_accounts_new("attached_assets/キャッシュフロー計算書標準科目テーブル.csv")