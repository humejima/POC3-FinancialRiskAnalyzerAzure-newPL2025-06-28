"""
参照マッピング機能の本番環境をテストするための簡易スクリプト
"""

from app import app, db
from models import JA, CSVData, AccountMapping, StandardAccount
from reference_mapping import apply_reference_mapping, normalize_account_name
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_reference_mapping():
    """
    参照マッピング機能のテスト（本番データ使用）
    既存のJAデータに対して参照マッピングを実行して結果を確認
    """
    with app.app_context():
        # 既存のJAとマッピング状況確認
        # JA model might have different structure, getting JA codes from CSVData instead
        ja_codes = db.session.query(CSVData.ja_code).distinct().all()
        ja_codes = [code[0] for code in ja_codes]
        
        # 既存のJAごとにマッピング状況確認
        for ja_code in ja_codes[:3]:  # 最初の3件のみ確認
            # マッピング状況を確認
            bs_total = CSVData.query.filter_by(ja_code=ja_code, file_type='bs').count()
            bs_mapped = CSVData.query.filter_by(ja_code=ja_code, file_type='bs', is_mapped=True).count()
            
            pl_total = CSVData.query.filter_by(ja_code=ja_code, file_type='pl').count()
            pl_mapped = CSVData.query.filter_by(ja_code=ja_code, file_type='pl', is_mapped=True).count()
            
            logger.info(f"JA {ja_code}: BS {bs_mapped}/{bs_total} マッピング済み, PL {pl_mapped}/{pl_total} マッピング済み")
        
        # JA002のマッピング情報を取得して参照マッピングに使用
        reference_ja = "JA002"
        reference_mappings = AccountMapping.query.filter_by(ja_code=reference_ja).all()
        
        reference_dict = {}
        for mapping in reference_mappings:
            normalized_name = normalize_account_name(mapping.original_account_name)
            reference_dict[normalized_name] = (mapping.standard_account_code, mapping.confidence)
        
        logger.info(f"参照用マッピング {reference_ja}: {len(reference_dict)}件")
        
        # 実際に参照マッピングを実行する代わりに、JA001の未マッピング科目数を確認するだけにする
        target_ja = "JA001"
        target_year = 2021
        file_type = "bs"
        
        unmapped = CSVData.query.filter_by(
            ja_code=target_ja, 
            year=target_year, 
            file_type=file_type,
            is_mapped=False
        ).count()
        
        logger.info(f"JA001の未マッピング科目数: {unmapped}件")
        
        # 参照マッピングを実行
        if unmapped > 0:
            logger.info(f"参照マッピングを実行: {target_ja} ({target_year})")
            try:
                result = apply_reference_mapping(
                    target_ja_code=target_ja,
                    target_year=target_year,
                    file_type=file_type
                )
                logger.info(f"参照マッピング結果: {result}")
                
                # マッピング後の状態確認
                new_unmapped = CSVData.query.filter_by(
                    ja_code=target_ja, 
                    year=target_year, 
                    file_type=file_type,
                    is_mapped=False
                ).count()
                
                logger.info(f"参照マッピング後の未マッピング科目数: {new_unmapped}件 (元: {unmapped}件)")
            except Exception as e:
                logger.error(f"参照マッピング実行中にエラーが発生: {e}")
        else:
            logger.info("未マッピング科目がないため、参照マッピングをスキップ")
        
        return "テスト完了"

if __name__ == "__main__":
    # 本番データを使った参照マッピングのテスト
    result = test_reference_mapping()
    print(result)