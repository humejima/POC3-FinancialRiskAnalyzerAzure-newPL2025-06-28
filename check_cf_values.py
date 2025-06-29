from app import app, db
from models import StandardAccountBalance

with app.app_context():
    # CF標準勘定科目残高を取得
    balances = StandardAccountBalance.query.filter_by(
        ja_code='JA001',
        year=2025,
        statement_type='cf'
    ).order_by(StandardAccountBalance.standard_account_code).all()
    
    # 各残高の表示
    print(f"CFデータの標準勘定科目残高一覧 (全{len(balances)}件):")
    print(f"{'コード':<8}{'勘定科目名':<40}{'カテゴリ':<15}{'当期値':<15}{'前期値':<15}")
    print("-" * 90)
    
    for balance in balances:
        code = balance.standard_account_code
        name = balance.standard_account_name[:35]  # 長すぎる名前を切り詰める
        category = balance.statement_subtype
        current = balance.current_value if balance.current_value is not None else 0
        previous = balance.previous_value if balance.previous_value is not None else 0
        
        print(f"{code:<8}{name:<40}{category:<15}{current:<15,.1f}{previous:<15,.1f}")
