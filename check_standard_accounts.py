from app import app
from models import StandardAccount

with app.app_context():
    # BSの科目数をチェック
    bs_count = StandardAccount.query.filter_by(financial_statement='bs').count()
    print(f'BS科目数: {bs_count}')
    
    # 表示順で最初の20件を確認
    bs_first = StandardAccount.query.filter_by(financial_statement='bs').order_by(StandardAccount.display_order).limit(20).all()
    print('BS科目（最初の20件）:')
    for account in bs_first:
        print(f'コード: {account.code}, 名前: {account.name}, 表示順: {account.display_order}')
    
    # 表示順で最後の10件を確認
    bs_last = StandardAccount.query.filter_by(financial_statement='bs').order_by(StandardAccount.display_order.desc()).limit(10).all()
    print('\nBS科目（最後の10件）:')
    for account in reversed(bs_last):
        print(f'コード: {account.code}, 名前: {account.name}, 表示順: {account.display_order}')