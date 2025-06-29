from app import app, db
from models import StandardAccount, CSVData, AccountMapping

with app.app_context():
    # CSVデータとマッピング情報を確認
    ja_code = "JA0001"
    year = 2025
    
    csv_data = CSVData.query.filter_by(
        ja_code=ja_code,
        year=year,
        file_type="pl"
    ).all()
    
    print(f"PL CSV データ数: {len(csv_data)}")
    
    mapped_count = CSVData.query.filter_by(
        ja_code=ja_code,
        year=year,
        file_type="pl",
        is_mapped=True
    ).count()
    
    print(f"マッピング済みPLデータ数: {mapped_count}")
    
    mappings = AccountMapping.query.filter_by(
        ja_code=ja_code,
        financial_statement="pl"
    ).all()
    
    print(f"PLマッピング数: {len(mappings)}")
    if len(mappings) > 0:
        print("PLマッピングサンプル:")
        for mapping in mappings[:5]:
            print(f"元科目: {mapping.original_account_name}, 標準科目: {mapping.standard_account_name} ({mapping.standard_account_code})")

