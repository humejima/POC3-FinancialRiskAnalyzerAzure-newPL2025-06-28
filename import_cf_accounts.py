import pandas as pd
from app import app, db
from models import StandardAccount

def import_cf_accounts(csv_file):
    """
    Import CF standard accounts from CSV file and replace existing CF accounts
    
    Args:
        csv_file: Path to CSV file
    
    Returns:
        int: Number of accounts imported
    """
    with app.app_context():
        # Delete only existing CF accounts
        db.session.query(StandardAccount).filter_by(financial_statement='cf').delete()
        db.session.commit()
        
        # CSVファイルの読み込み
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        
        # アカウント追加
        count = 0
        for _, row in df.iterrows():
            try:
                # Skip header row if it exists
                if row['科目コード'] == '科目コード':
                    continue
                    
                # 小数点以下を削除して整数部分のみを保持
                code_raw = str(row['科目コード'])
                if '.' in code_raw:
                    code = code_raw.split('.')[0]
                else:
                    code = code_raw
                    
                name = row['科目名']
                account_type = row['科目区分']
                
                try:
                    display_order = int(row['表示順位']) if pd.notna(row['表示順位']) else 999
                except ValueError:
                    display_order = 999
                    
                # Determine category based on description
                if '営業活動' in row['財務諸表表示項目']:
                    category = '営業活動'
                elif '投資活動' in row['財務諸表表示項目']:
                    category = '投資活動'
                elif '財務活動' in row['財務諸表表示項目']:
                    category = '財務活動'
                elif '現金及び現金同等物' in row['財務諸表表示項目']:
                    category = '現金及び現金同等物'
                else:
                    category = 'その他'
                
                description = row['財務諸表表示項目'] if pd.notna(row['財務諸表表示項目']) else ''
                
                # Create standard account
                account = StandardAccount(
                    code=code,
                    name=name,
                    category=category,
                    financial_statement='cf',
                    account_type=account_type,
                    display_order=display_order,
                    description=description
                )
                
                db.session.add(account)
                count += 1
                print(f"Added CF account: {code} - {name}")
                
            except Exception as e:
                print(f"Error importing CF row: {row.to_dict()}\nError: {str(e)}")
                continue
        
        db.session.commit()
        print(f"Imported {count} CF standard accounts.")
        return count

if __name__ == "__main__":
    import_cf_accounts("attached_assets/標準科目テーブルCF.csv")