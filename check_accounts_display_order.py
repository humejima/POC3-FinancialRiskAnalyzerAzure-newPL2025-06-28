from app import app
from models import StandardAccount

with app.app_context():
    total_accounts = StandardAccount.query.filter(
        StandardAccount.code.in_(['2900', '4900', '5900', '5950', '5951'])
    ).all()
    
    print('合計科目一覧（表示順付き）:')
    for account in total_accounts:
        print(f'コード: {account.code}, 名前: {account.name}, タイプ: {account.financial_statement}, 表示順: {account.display_order}')