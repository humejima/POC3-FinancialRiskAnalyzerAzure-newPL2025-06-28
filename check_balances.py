from app import app, db
from models import StandardAccountBalance

def check_account_balances(ja_code, year, statement_type):
    with app.app_context():
        balances = StandardAccountBalance.query.filter_by(
            ja_code=ja_code, 
            year=year, 
            statement_type=statement_type
        ).all()
        
        print(f'{ja_code}/{year}の{statement_type}残高データ件数: {len(balances)}')
        
        if len(balances) > 0:
            for b in balances[:20]:
                print(f'{b.standard_account_code}: {b.standard_account_name} = {b.current_value}')
        
        # 流動資産と流動負債の値を特に確認
        current_assets = StandardAccountBalance.query.filter_by(
            ja_code=ja_code, 
            year=year, 
            statement_type=statement_type,
            standard_account_code='1'  # 流動資産（合計）のコード
        ).first()
        
        current_liabilities = StandardAccountBalance.query.filter_by(
            ja_code=ja_code, 
            year=year, 
            statement_type=statement_type,
            standard_account_code='2000'  # 流動負債（合計）のコード
        ).first()
        
        print("\n特定の重要科目:")
        print(f"流動資産（合計）: {current_assets.current_value if current_assets else 'なし'}")
        print(f"流動負債（合計）: {current_liabilities.current_value if current_liabilities else 'なし'}")

# JA001の2021年のBS残高をチェック
check_account_balances('JA001', 2021, 'bs')