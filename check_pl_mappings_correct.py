from app import app, db
from models import CSVData, AccountMapping

with app.app_context():
    # PLマッピング情報を確認
    ja_code = "JA001"
    
    mappings = AccountMapping.query.filter_by(
        ja_code=ja_code,
        financial_statement="pl"
    ).all()
    
    print(f"PLマッピング数: {len(mappings)}")
    if len(mappings) > 0:
        print("PLマッピングサンプル:")
        for mapping in mappings[:10]:
            print(f"元科目: {mapping.original_account_name}, 標準科目: {mapping.standard_account_name} ({mapping.standard_account_code})")

