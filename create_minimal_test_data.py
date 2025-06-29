"""
参照マッピング機能の最小限のテストデータを作成するスクリプト
タイムアウトを回避するため、必要最小限のデータのみを作成
"""

from app import app, db
from models import JA, CSVData, StandardAccount, AccountMapping
from ensure_ja_exists import ensure_ja_exists
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_minimal_test_data():
    """
    参照マッピング機能を最小限で検証するためのテストデータを作成
    JAコード: JA007
    - 2つの未マッピング科目を作成
    - 1つのマッピング済み科目を作成
    """
    with app.app_context():
        ja_code = "JA007"
        year = 2025
        file_type = 'bs'
        
        # JA007が存在することを確認
        ensure_ja_exists(ja_code, year)
        logger.info(f"JA {ja_code} の存在を確認しました")
        
        # 既存のデータを削除
        CSVData.query.filter_by(ja_code=ja_code, year=year, file_type=file_type).delete()
        AccountMapping.query.filter_by(ja_code=ja_code, financial_statement=file_type).delete()
        db.session.commit()
        logger.info(f"{ja_code}の既存データを削除しました")
        
        # 標準勘定科目を1つだけ取得
        standard_account = StandardAccount.query.filter_by(financial_statement=file_type).first()
        
        if not standard_account:
            logger.error("標準勘定科目が見つかりません")
            return "標準勘定科目が見つかりません"
        
        logger.info(f"標準勘定科目を取得: {standard_account.code} {standard_account.name}")
        
        # 未マッピング科目を2つ作成
        for i in range(2):
            account_name = f"テスト未マッピング科目_{i+1}"
            csv_data = CSVData(
                ja_code=ja_code,
                year=year,
                file_type=file_type,
                row_number=i+1,
                account_name=account_name,
                category="資産",
                current_value=1000000 * (i+1),
                previous_value=800000 * (i+1),
                is_mapped=False
            )
            db.session.add(csv_data)
        
        # マッピング済み科目を1つ作成
        mapped_account_name = "テストマッピング済み科目"
        csv_data = CSVData(
            ja_code=ja_code,
            year=year,
            file_type=file_type,
            row_number=3,
            account_name=mapped_account_name,
            category="資産",
            current_value=3000000,
            previous_value=2500000,
            is_mapped=True
        )
        db.session.add(csv_data)
        
        # マッピングレコードを作成
        mapping = AccountMapping(
            ja_code=ja_code,
            original_account_name=mapped_account_name,
            standard_account_code=standard_account.code,
            standard_account_name=standard_account.name,
            financial_statement=file_type,
            confidence=0.95,
            rationale="テスト用マッピング"
        )
        db.session.add(mapping)
        
        # コミット
        db.session.commit()
        
        # 確認
        total = CSVData.query.filter_by(ja_code=ja_code, year=year, file_type=file_type).count()
        mapped = CSVData.query.filter_by(ja_code=ja_code, year=year, file_type=file_type, is_mapped=True).count()
        unmapped = total - mapped
        
        logger.info(f"作成したテストデータ: 合計={total}件, マッピング済={mapped}件, 未マッピング={unmapped}件")
        return f"テストデータ作成完了: 合計={total}件, マッピング済={mapped}件, 未マッピング={unmapped}件"

if __name__ == "__main__":
    result = create_minimal_test_data()
    print(result)