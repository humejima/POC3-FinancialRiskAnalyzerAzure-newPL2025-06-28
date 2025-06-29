"""
参照マッピング機能のテストデータを作成するスクリプト
このスクリプトは参照マッピング機能をテストするために、未マッピングの科目を持つサンプルJAデータを作成します。
"""

import logging
import sys
from app import app, db
from models import JA, CSVData, StandardAccount, AccountMapping
from ensure_ja_exists import ensure_ja_exists

# ロガー設定
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger(__name__)

def create_test_data(test_ja_code="JA007", source_ja_code="JA001", year=2025):
    """
    参照マッピング機能をテストするためのデータを作成する
    ソースJAの科目をコピーして、一部を未マッピング状態にする
    
    Args:
        test_ja_code: テスト用JAコード
        source_ja_code: コピー元JAコード
        year: 対象年度
    """
    with app.app_context():
        # テスト用JAが存在するか確認し、なければ作成
        ensure_ja_exists(test_ja_code, year)
        logger.info(f"テスト用JA {test_ja_code} の存在を確認しました")
        
        # ソースJAから科目データをコピー
        for file_type in ['bs', 'pl', 'cf']:
            # 既存のCSVデータを確認
            existing_data = CSVData.query.filter_by(ja_code=test_ja_code, year=year, file_type=file_type).count()
            
            if existing_data > 0:
                logger.info(f"{test_ja_code}の{file_type}データは既に{existing_data}件存在します")
                continue
                
            # ソースJAのCSVデータを取得
            source_data = CSVData.query.filter_by(ja_code=source_ja_code, year=year, file_type=file_type).all()
            
            if not source_data:
                logger.warning(f"ソースJA {source_ja_code} の {file_type} データが見つかりません")
                continue
                
            logger.info(f"{source_ja_code}から{test_ja_code}に{len(source_data)}件の{file_type}データをコピーします")
            
            # データをコピーしてマッピング状態をリセット
            for i, data in enumerate(source_data):
                new_data = CSVData(
                    ja_code=test_ja_code,
                    year=year,
                    file_type=file_type,
                    row_number=data.row_number,
                    account_name=data.account_name,
                    account_code=data.account_code,
                    value=data.value,
                    is_mapped=False,  # すべて未マッピング状態にする
                    standard_account_code=None  # 標準勘定科目コードをクリア
                )
                db.session.add(new_data)
            
            # 既存のマッピングデータを削除
            existing_mappings = AccountMapping.query.filter_by(ja_code=test_ja_code, year=year, file_type=file_type).all()
            if existing_mappings:
                for mapping in existing_mappings:
                    db.session.delete(mapping)
                logger.info(f"{test_ja_code}の既存の{file_type}マッピング{len(existing_mappings)}件を削除しました")
            
            # 半分の科目を手動でマッピング状態にする（参照マッピングのテスト用）
            all_data = CSVData.query.filter_by(ja_code=test_ja_code, year=year, file_type=file_type).all()
            half_count = len(all_data) // 2
            
            logger.info(f"{half_count}件の{file_type}科目を手動マッピング状態にします")
            
            for i, data in enumerate(all_data[:half_count]):
                # 元のJAのマッピングデータを取得
                source_mapping = AccountMapping.query.filter_by(
                    ja_code=source_ja_code,
                    year=year,
                    file_type=file_type,
                    original_name=data.account_name
                ).first()
                
                if source_mapping:
                    # マッピングデータをコピー
                    data.is_mapped = True
                    data.standard_account_code = source_mapping.standard_account_code
                    
                    # マッピングレコードを作成
                    new_mapping = AccountMapping(
                        ja_code=test_ja_code,
                        year=year,
                        file_type=file_type,
                        original_name=data.account_name,
                        standard_account_code=source_mapping.standard_account_code,
                        standard_account_id=source_mapping.standard_account_id,
                        confidence=0.95,  # 手動マッピングなので高い信頼度
                        mapping_method="manual",
                        rationale="テスト用手動マッピング"
                    )
                    db.session.add(new_mapping)
            
            db.session.commit()
            logger.info(f"{test_ja_code}の{file_type}データの準備が完了しました")
        
        # 確認用の統計情報を表示
        for file_type in ['bs', 'pl', 'cf']:
            total = CSVData.query.filter_by(ja_code=test_ja_code, year=year, file_type=file_type).count()
            mapped = CSVData.query.filter_by(ja_code=test_ja_code, year=year, file_type=file_type, is_mapped=True).count()
            unmapped = total - mapped
            
            logger.info(f"{test_ja_code}の{file_type}データ統計: 合計={total}件, マッピング済={mapped}件, 未マッピング={unmapped}件")
        
        return "テストデータの作成が完了しました"

if __name__ == "__main__":
    print("参照マッピング機能テスト用データを作成します...")
    result = create_test_data()
    print(result)