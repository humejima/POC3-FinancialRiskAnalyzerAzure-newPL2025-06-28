from app import app, db
from models import StandardAccount

with app.app_context():
    # PLの標準勘定科目の数を確認
    pl_accounts = StandardAccount.query.filter_by(financial_statement="pl").all()
    print(f"PL標準勘定科目数: {len(pl_accounts)}")
    if len(pl_accounts) > 0:
        print("PL標準勘定科目サンプル:")
        for account in pl_accounts[:5]:  # 最初の5件を表示
            print(f"コード: {account.code}, 名称: {account.name}, 親コード: {account.parent_code}")

