"""
参照マッピング機能の問題を調査するスクリプト
既存のマッピングデータを確認し、特定の科目（「系統出資」や「金融機関貸付」など）の
マッピング状況を調べます。
"""

from app import app, db
from models import AccountMapping, CSVData
import logging

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_account_name(name):
    """勘定科目名を正規化する（空白、全角/半角、カッコなどを処理）"""
    import re
    if name is None:
        return ""
    
    # 空白文字の正規化（全ての種類の空白を半角スペースに変換し、連続する空白を1つにまとめる）
    name = re.sub(r'\s+', ' ', name)
    
    # 括弧と括弧内の内容を削除
    name = re.sub(r'[\(（].*?[\)）]', '', name)
    
    # 先頭と末尾の空白を削除
    name = name.strip()
    
    return name

def check_reference_mappings():
    """
    参照マッピング機能の問題を調査する
    特に「系統出資」や「金融機関貸付」などのマッピング状況を確認
    """
    with app.app_context():
        # JA001のマッピング状況を確認
        ja001_mappings = AccountMapping.query.filter_by(ja_code='JA001').all()
        logger.info(f"JA001のマッピング数: {len(ja001_mappings)}")
        
        # 特定の科目を検索
        search_terms = ['系統出資', '金融機関貸付']
        for term in search_terms:
            mappings = AccountMapping.query.filter(
                AccountMapping.original_account_name.like(f'%{term}%')
            ).all()
            logger.info(f"科目 '{term}' に関連するマッピング:")
            for mapping in mappings:
                logger.info(f"  JA: {mapping.ja_code}, 元の科目名: {mapping.original_account_name}")
                logger.info(f"  マッピング先: {mapping.standard_account_code} ({mapping.standard_account_name})")
                logger.info(f"  信頼度: {mapping.confidence}, 財務諸表: {mapping.financial_statement}")
        
        # JA007の未マッピング科目を確認
        unmapped_accounts = db.session.query(CSVData).filter(
            CSVData.ja_code == 'JA007',
            CSVData.year == 2021,
            CSVData.file_type == 'bs',
            CSVData.is_mapped == False  # 未マッピングのみ
        ).all()
        logger.info(f"JA007の未マッピング科目数: {len(unmapped_accounts)}")
        
        # 未マッピング科目のうち、JA001でマッピングされている科目を確認
        for csv_data in unmapped_accounts:
            norm_name = normalize_account_name(csv_data.account_name)
            
            # JA001の同じ科目名でマッピングされているかチェック
            ja001_mapping = AccountMapping.query.filter(
                AccountMapping.ja_code == 'JA001',
                AccountMapping.original_account_name == csv_data.account_name
            ).first()
            
            if ja001_mapping:
                logger.info(f"JA007の未マッピング科目 '{csv_data.account_name}' は、JA001では既にマッピングされています:")
                logger.info(f"  マッピング先: {ja001_mapping.standard_account_code} ({ja001_mapping.standard_account_name})")
                logger.info(f"  信頼度: {ja001_mapping.confidence}, 財務諸表: {ja001_mapping.financial_statement}")
        
        # 正規化名の比較
        logger.info("正規化名の比較:")
        for csv_data in unmapped_accounts[:5]:  # 最初の5件のみ
            norm_name = normalize_account_name(csv_data.account_name)
            logger.info(f"  元の名前: '{csv_data.account_name}', 正規化後: '{norm_name}'")

if __name__ == "__main__":
    check_reference_mappings()