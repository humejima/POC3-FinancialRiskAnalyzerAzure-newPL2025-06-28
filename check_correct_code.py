from app import app, db
from models import StandardAccount, StandardAccountBalance, JA, CSVData

with app.app_context():
    # 正確なJAコードで再確認
    ja_code = "JA001"
    year = 2025
    
    csv_data = CSVData.query.filter_by(
        ja_code=ja_code,
        year=year,
        file_type="pl"
    ).all()
    
    print(f"PL CSV データ数: {len(csv_data)}")
    if len(csv_data) > 0:
        print("PLデータサンプル:")
        for data in csv_data[:5]:
            print(f"科目名: {data.account_name}, 当期: {data.current_value}, マッピング済: {data.is_mapped}")
    
    # 標準勘定科目残高を確認
    balances = StandardAccountBalance.query.filter_by(
        ja_code=ja_code,
        year=year,
        statement_type="pl"
    ).all()
    
    print(f"PL残高レコード数: {len(balances)}")
    if len(balances) > 0:
        print("PL残高サンプル:")
        for balance in balances[:5]:
            print(f"コード: {balance.standard_account_code}, 名称: {balance.standard_account_name}, 当期: {balance.current_value}")

