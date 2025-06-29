from app import app, db
from models import StandardAccount, StandardAccountBalance

with app.app_context():
    # JA北海道のPL残高レコード数を確認
    ja_code = "JA0001"
    year = 2025
    pl_balances = StandardAccountBalance.query.filter_by(
        ja_code=ja_code,
        year=year,
        statement_type="pl"
    ).all()
    
    print(f"PL残高レコード数: {len(pl_balances)}")
    if len(pl_balances) > 0:
        print("PL残高サンプル:")
        for balance in pl_balances[:5]:
            print(f"コード: {balance.standard_account_code}, 名称: {balance.standard_account_name}, 当期: {balance.current_value}")

