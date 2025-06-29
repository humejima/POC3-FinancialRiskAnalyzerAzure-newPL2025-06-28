from app import app, db
from models import StandardAccount

with app.app_context():
    # CFの標準勘定科目の数を確認
    cf_accounts = StandardAccount.query.filter_by(financial_statement='cf').all()
    print(f'CF標準勘定科目数: {len(cf_accounts)}')
    if len(cf_accounts) > 0:
        print('CF標準勘定科目サンプル:')
        for account in cf_accounts[:5]:  # 最初の5件を表示
            print(f'コード: {account.code}, 名称: {account.name}, カテゴリ: {account.category}')
