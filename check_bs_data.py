"""
BSデータの確認スクリプト
流動資産関連の勘定科目データが正しく取得できているかを確認します
"""
from app import app, db
from models import StandardAccountBalance
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_bs_data(ja_code='JA001', year=2025):
    """
    BSデータの流動資産関連の勘定科目を確認する
    """
    with app.app_context():
        try:
            # BSデータを取得
            bs_data = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                statement_type='bs'
            ).all()
            
            logger.info(f"BSデータ数: {len(bs_data)}")
            
            # 流動資産関連の科目コード
            liquid_asset_codes = ['1010', '1020', '1600', '1700', '1800', '1900']
            
            # 流動資産関連のデータを表示
            found_assets = []
            for code in liquid_asset_codes:
                asset = StandardAccountBalance.query.filter_by(
                    ja_code=ja_code,
                    year=year,
                    statement_type='bs',
                    standard_account_code=code
                ).first()
                
                if asset:
                    logger.info(f"科目 {code}: {asset.standard_account_name} = {asset.current_value:,.0f}")
                    found_assets.append(code)
                else:
                    logger.warning(f"科目 {code} が見つかりません")
            
            # すべての科目コードを表示（デバッグ用）
            logger.info("全BSデータの科目コード一覧:")
            for i, record in enumerate(bs_data[:30]):  # 最初の30件を表示
                logger.info(f"{i+1}. {record.standard_account_code}: {record.standard_account_name} = {record.current_value:,.0f}")
            
            return True
            
        except Exception as e:
            logger.error(f"BSデータの確認中にエラーが発生しました: {str(e)}")
            return False

if __name__ == "__main__":
    check_bs_data('JA001', 2025)