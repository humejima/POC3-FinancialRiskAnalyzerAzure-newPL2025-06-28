"""
PLの親勘定科目コードを確認するスクリプト
"""
from models import StandardAccount
from app import app, db

def check_pl_parent_codes():
    """PLの親勘定科目コードを確認"""
    with app.app_context():
        pl_parents = StandardAccount.query.filter_by(
            financial_statement='pl',
            parent_code=None
        ).all()
        
        print("PLの親勘定科目:")
        for account in pl_parents:
            print(f"{account.code}: {account.name}")
        
        # 特に以下のコードが標準勘定科目マスタに存在するか確認
        important_codes = ['40000', '41000', '50000', '51000', '55000', '60000']
        for code in important_codes:
            account = StandardAccount.query.filter_by(code=code).first()
            if account:
                print(f"確認: {code} = {account.name}, タイプ={account.financial_statement}")
            else:
                print(f"確認: {code} は存在しません")

if __name__ == "__main__":
    check_pl_parent_codes()