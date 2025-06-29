from app import app, db
from models import StandardAccountBalance

with app.app_context():
    # CF標準勘定科目残高を取得
    balances = StandardAccountBalance.query.filter_by(
        statement_type='cf',
        ja_code='JA001',
        year=2025
    ).order_by(StandardAccountBalance.standard_account_code).all()
    
    print(f"CF標準勘定科目残高データ件数: {len(balances)}件")
    
    # カテゴリごとのカウント
    categories = {}
    for balance in balances:
        if balance.statement_subtype not in categories:
            categories[balance.statement_subtype] = 0
        categories[balance.statement_subtype] += 1
    
    print("\nカテゴリごとの件数:")
    for category, count in categories.items():
        print(f"{category}: {count}件")
    
    # 詳細データの表示
    print("\n詳細データ (最初の10件):")
    for i, balance in enumerate(balances):
        if i >= 10:
            break
        print(f"{balance.standard_account_code}: {balance.standard_account_name} - {balance.statement_subtype} - 当期: {balance.current_value}, 前期: {balance.previous_value}")
