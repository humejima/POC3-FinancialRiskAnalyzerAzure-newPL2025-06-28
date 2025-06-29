"""
参照マッピング機能の簡易テストデータを作成するスクリプト（修正版）
AccountMappingモデルのフィールド名を正しく使用
"""

from app import app, db
from models import JA, CSVData, StandardAccount, AccountMapping
from ensure_ja_exists import ensure_ja_exists

def create_simple_test_data():
    """最小限のテストデータを作成"""
    with app.app_context():
        # JA007が存在することを確認
        ja_code = "JA007"
        year = 2025
        ensure_ja_exists(ja_code, year)
        print(f"JA {ja_code} の存在を確認しました")
        
        # 既存のCSVデータがあれば削除
        file_type = 'bs'  # テスト用に貸借対照表のみに絞る
        CSVData.query.filter_by(ja_code=ja_code, year=year, file_type=file_type).delete()
        print(f"{ja_code}の既存{file_type}データを削除しました")
        
        # 既存のマッピングデータがあれば削除（AccountMappingの正しいフィールド名を使用）
        AccountMapping.query.filter_by(ja_code=ja_code, financial_statement=file_type).delete()
        print(f"{ja_code}の既存マッピングデータを削除しました")
        
        # 標準勘定科目から最初の10件を取得
        standard_accounts = StandardAccount.query.filter_by(financial_statement='bs').limit(10).all()
        
        if not standard_accounts:
            print("標準勘定科目が見つかりません")
            return
        
        print(f"取得した標準勘定科目: {len(standard_accounts)}件")
        
        # テスト用のCSVデータを作成（BS貸借対照表のみ）
        for i, std_account in enumerate(standard_accounts):
            # 科目名に少し変更を加えてテストデータを作成
            account_name = f"{std_account.name}_TEST"
            
            # CSV行データを作成
            csv_data = CSVData(
                ja_code=ja_code,
                year=year,
                file_type='bs',
                row_number=i+1,
                account_name=account_name,
                account_code=f"T{i+1:04d}",
                value=1000000 * (i+1),
                is_mapped=False,  # すべて未マッピング状態
                standard_account_code=None
            )
            db.session.add(csv_data)
        
        # 半分のデータは手動でマッピング済みにする
        csv_data_list = CSVData.query.filter_by(
            ja_code=ja_code, year=year, file_type='bs'
        ).limit(5).all()
        
        for i, csv_data in enumerate(csv_data_list):
            # 対応する標準勘定科目を取得
            std_account = standard_accounts[i]
            
            # CSVデータをマッピング済みにする
            csv_data.is_mapped = True
            csv_data.standard_account_code = std_account.code
            
            # マッピングレコードを作成（AccountMappingの正しいフィールド名を使用）
            mapping = AccountMapping(
                ja_code=ja_code,
                original_account_name=csv_data.account_name,  # フィールド名修正
                standard_account_code=std_account.code,
                standard_account_name=std_account.name,
                financial_statement='bs',  # フィールド名修正
                confidence=0.95,
                rationale="テスト用手動マッピング"
            )
            db.session.add(mapping)
        
        db.session.commit()
        
        # 確認のための出力
        total = CSVData.query.filter_by(ja_code=ja_code, year=year, file_type='bs').count()
        mapped = CSVData.query.filter_by(ja_code=ja_code, year=year, file_type='bs', is_mapped=True).count()
        unmapped = total - mapped
        
        print(f"作成したテストデータ: 合計={total}件, マッピング済={mapped}件, 未マッピング={unmapped}件")
        return "テストデータ作成完了"

if __name__ == "__main__":
    result = create_simple_test_data()
    print(result)