"""
参照マッピング機能をテストするためのスクリプト
"""

from app import app, db
from models import CSVData, AccountMapping, StandardAccount
from reference_mapping import apply_reference_mapping
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_reference_mapping():
    """
    参照マッピング機能のテスト
    1. JA007のテストデータが作成されていることを前提とする
    2. JA007のテストデータに対して参照マッピングを実行
    3. マッピング結果を確認
    """
    with app.app_context():
        # まずJA007のデータが存在することを確認
        target_ja_code = "JA007"
        target_year = 2025
        file_type = "bs"
        
        # 未マッピング科目の数を確認
        unmapped_count = CSVData.query.filter_by(
            ja_code=target_ja_code, 
            year=target_year, 
            file_type=file_type, 
            is_mapped=False
        ).count()
        
        logger.info(f"参照マッピング前の未マッピング科目数: {unmapped_count}")
        
        if unmapped_count == 0:
            logger.warning("未マッピング科目がありません。create_test_data_final.pyを先に実行してください。")
            return "未マッピング科目がありません"
        
        # 参照マッピングを実行
        confidence_threshold = 0.7
        result = apply_reference_mapping(
            target_ja_code=target_ja_code,
            target_year=target_year,
            file_type=file_type,
            confidence_threshold=confidence_threshold
        )
        
        logger.info(f"参照マッピング結果: {result}")
        
        # 結果を確認
        new_unmapped_count = CSVData.query.filter_by(
            ja_code=target_ja_code, 
            year=target_year, 
            file_type=file_type, 
            is_mapped=False
        ).count()
        
        mapped_count = unmapped_count - new_unmapped_count
        
        logger.info(f"参照マッピング後の未マッピング科目数: {new_unmapped_count}")
        logger.info(f"新たにマッピングされた科目数: {mapped_count}")
        
        # 作成されたマッピングを表示
        new_mappings = AccountMapping.query.filter_by(
            ja_code=target_ja_code,
            financial_statement=file_type
        ).all()
        
        logger.info(f"JA007のマッピング総数: {len(new_mappings)}")
        
        # 最初の5件を表示
        for i, mapping in enumerate(new_mappings[:5]):
            logger.info(f"マッピング #{i+1}: {mapping.original_account_name} → {mapping.standard_account_name} (信頼度: {mapping.confidence})")
        
        return f"テスト完了: 未マッピング={new_unmapped_count}, マッピング済={mapped_count}"

if __name__ == "__main__":
    # テストデータ作成スクリプトを実行してから、このスクリプトを実行する
    # python create_test_data_final.py
    # python test_reference_mapping.py
    result = test_reference_mapping()
    print(result)