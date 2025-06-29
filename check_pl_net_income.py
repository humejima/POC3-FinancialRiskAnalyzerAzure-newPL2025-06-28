"""
PLデータで当期純利益（Net Income）の科目を確認するスクリプト
"""
from models import StandardAccountBalance
from app import app, db

def check_pl_net_income_account(ja_code, year):
    """
    PLデータ（損益計算書）で当期純利益に関連する科目を確認
    
    Args:
        ja_code: JA code
        year: Financial year
    """
    with app.app_context():
        # PLデータを取得
        pl_accounts = db.session.query(StandardAccountBalance).filter_by(
            ja_code=ja_code, 
            year=year, 
            statement_type='pl'
        ).all()
        
        print(f"\nPL科目数: {len(pl_accounts)}")
        
        # 科目コード9900(旧コード)と33000(新コード)の確認
        for code in ['33000', '9900', '24000', '25000', '26000']:
            account = db.session.query(StandardAccountBalance).filter_by(
                ja_code=ja_code, 
                year=year, 
                statement_type='pl',
                standard_account_code=code
            ).first()
            
            if account:
                print(f"科目 {code}: {account.standard_account_name} = {account.current_value}")
            else:
                print(f"科目 {code} は存在しません")
        
        # 当期純利益に関連する可能性のある科目をキーワードで検索
        keywords = ['当期純利益', '当期利益', '当期', '純利益', '利益', '純']
        print("\n当期純利益に関連する可能性のある科目:")
        for keyword in keywords:
            matches = [a for a in pl_accounts if keyword in a.standard_account_name]
            for account in matches:
                print(f"科目 {account.standard_account_code}: {account.standard_account_name} = {account.current_value}")

if __name__ == "__main__":
    check_pl_net_income_account('JA001', 2021)