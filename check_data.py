"""
指定したJAコード、年度、データタイプのデータを確認するスクリプト
"""
from models import CSVData, StandardAccount, AccountMapping, StandardAccountBalance
from app import app, db

def check_ja_data(ja_code, year, file_type):
    """指定したJA、年度、財務諸表タイプのデータを確認"""
    with app.app_context():
        # CSV元データの確認
        csv_data = CSVData.query.filter_by(
            ja_code=ja_code,
            year=year,
            file_type=file_type
        ).all()
        
        print(f"===== CSVデータ: JA={ja_code}, 年度={year}, タイプ={file_type} =====")
        print(f"件数: {len(csv_data)}")
        for i, data in enumerate(csv_data[:5]):  # 最初の5件だけ表示
            print(f"{i+1}. 科目名={data.account_name}, 値={data.current_value}, マッピング済み={data.is_mapped}")
            
        # マッピングデータの確認
        mappings = AccountMapping.query.filter_by(
            ja_code=ja_code,
            financial_statement=file_type
        ).all()
        
        print(f"\n===== マッピングデータ: JA={ja_code}, タイプ={file_type} =====")
        print(f"件数: {len(mappings)}")
        for i, mapping in enumerate(mappings[:5]):  # 最初の5件だけ表示
            print(f"{i+1}. 元科目名={mapping.original_account_name}, 標準コード={mapping.standard_account_code}")
            
        # 標準勘定科目残高の確認
        balances = StandardAccountBalance.query.filter_by(
            ja_code=ja_code,
            year=year,
            statement_type=file_type
        ).all()
        
        print(f"\n===== 標準勘定科目残高: JA={ja_code}, 年度={year}, タイプ={file_type} =====")
        print(f"件数: {len(balances)}")
        for i, balance in enumerate(balances[:5]):  # 最初の5件だけ表示
            print(f"{i+1}. コード={balance.standard_account_code}, 名前={balance.standard_account_name}, 値={balance.current_value}")

        # 標準勘定科目の確認
        standard_accounts = StandardAccount.query.filter_by(
            financial_statement=file_type
        ).all()
        
        print(f"\n===== 標準勘定科目: タイプ={file_type} =====")
        print(f"件数: {len(standard_accounts)}")
        for i, account in enumerate(standard_accounts[:5]):  # 最初の5件だけ表示
            print(f"{i+1}. コード={account.code}, 名前={account.name}, 親コード={account.parent_code}")

if __name__ == "__main__":
    # JA001の2021年BSデータを確認
    check_ja_data("JA001", 2021, "bs")