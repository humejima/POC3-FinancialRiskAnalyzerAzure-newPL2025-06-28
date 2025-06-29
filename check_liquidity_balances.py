"""
流動性指標に関連する残高データを確認するスクリプト
流動資産・流動負債が正しく取得できているか検証
"""

from app import app, db
from models import StandardAccountBalance
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_liquidity_balances(ja_code='JA001', year=2021):
    """
    特定のJAの流動性指標に関わる残高データを確認する
    
    Args:
        ja_code: JA code
        year: Financial year
    """
    with app.app_context():
        try:
            # 流動資産（コード：11000）の残高を確認
            current_assets = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                standard_account_code='11000'
            ).first()
            
            if current_assets:
                logger.info(f"流動資産(11000): JA={ja_code}, 年度={year}, 値={current_assets.current_value:,}円")
            else:
                logger.warning(f"流動資産(11000)の残高データが見つかりません: JA={ja_code}, 年度={year}")
            
            # 現金預け金（コード：1010, 1020）の残高を確認
            cash = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                standard_account_code='1010'
            ).first()
            
            deposits = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                standard_account_code='1020'
            ).first()
            
            cash_value = cash.current_value if cash else 0
            deposits_value = deposits.current_value if deposits else 0
            
            logger.info(f"現金(1010): JA={ja_code}, 年度={year}, 値={cash_value:,}円")
            logger.info(f"預け金(1020): JA={ja_code}, 年度={year}, 値={deposits_value:,}円")
            logger.info(f"現金預け金合計: {cash_value + deposits_value:,}円")
            
            # 流動負債（コード：21000）の残高を確認
            current_liabilities = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                standard_account_code='21000'
            ).first()
            
            if current_liabilities:
                logger.info(f"流動負債(21000): JA={ja_code}, 年度={year}, 値={current_liabilities.current_value:,}円")
            else:
                logger.warning(f"流動負債(21000)の残高データが見つかりません: JA={ja_code}, 年度={year}")
            
            return True
            
        except Exception as e:
            logger.error(f"残高データの確認中にエラーが発生しました: {str(e)}")
            return False

if __name__ == "__main__":
    check_liquidity_balances('JA001', 2021)