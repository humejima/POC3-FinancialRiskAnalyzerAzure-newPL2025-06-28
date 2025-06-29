from app import app, db
from models import StandardAccount

with app.app_context():
    cf_accounts = StandardAccount.query.filter_by(financial_statement='cf').all()
    print(f'CF標準勘定科目数: {len(cf_accounts)}件')
    
    # 営業活動、投資活動、財務活動ごとのカテゴリ別カウント
    categories = {}
    for account in cf_accounts:
        if account.category not in categories:
            categories[account.category] = 0
        categories[account.category] += 1
    
    for category, count in categories.items():
        print(f'カテゴリ「{category}」: {count}件')