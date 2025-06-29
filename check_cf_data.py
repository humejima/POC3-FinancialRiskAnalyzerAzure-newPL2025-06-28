from app import app, db
from models import CSVData, AccountMapping, StandardAccountBalance

with app.app_context():
    # CF CSV データの確認
    csv_data = CSVData.query.filter_by(file_type='cf').all()
    print(f'CF CSVデータ件数: {len(csv_data)}件')
    
    # マッピングデータの確認
    mappings = AccountMapping.query.filter_by(financial_statement='cf').all()
    print(f'CF マッピング件数: {len(mappings)}件')
    
    # 標準勘定科目残高の確認
    balances = StandardAccountBalance.query.filter_by(statement_type='cf').all()
    print(f'CF 標準勘定科目残高件数: {len(balances)}件')
    
    # JAと年度ごとの件数
    ja_years = {}
    for data in csv_data:
        key = f"{data.ja_code}_{data.year}"
        if key not in ja_years:
            ja_years[key] = 0
        ja_years[key] += 1
    
    print("\nJAコードと年度ごとのCFデータ件数:")
    for key, count in ja_years.items():
        print(f"{key}: {count}件")
