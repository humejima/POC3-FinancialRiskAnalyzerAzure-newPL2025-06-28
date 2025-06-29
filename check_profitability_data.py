from app import app, db
from models import FinancialIndicator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_profitability_indicators(ja_code='JA001', year=2021):
    """
    収益性指標の計算に使用されている科目コードと値を確認する
    特に総資産利益率の計算に使用している当期純利益と総資産のコードを確認
    """
    with app.app_context():
        try:
            # 総資産利益率の指標を取得
            roa_indicator = FinancialIndicator.query.filter_by(
                ja_code=ja_code,
                year=year,
                indicator_code='roa'
            ).first()
            
            if roa_indicator:
                logger.info(f"総資産利益率(ROA)の値: {roa_indicator.value:.2f}%")
                logger.info(f"計算式: {roa_indicator.formula}")
                logger.info(f"使用科目: {roa_indicator.accounts_used}")
            else:
                logger.warning(f"総資産利益率(ROA)の指標が見つかりませんでした")
            
            # 収益性関連の全指標を確認
            profitability_indicators = FinancialIndicator.query.filter_by(
                ja_code=ja_code,
                year=year,
                indicator_type='profitability'
            ).all()
            
            logger.info(f"収益性指標の数: {len(profitability_indicators)}")
            
            for indicator in profitability_indicators:
                logger.info(f"指標: {indicator.indicator_name} ({indicator.indicator_code})")
                logger.info(f"  値: {indicator.value:.2f}%")
                logger.info(f"  計算式: {indicator.formula}")
                logger.info(f"  使用科目: {indicator.accounts_used}")
                logger.info("----------")
            
            return True
            
        except Exception as e:
            logger.error(f"収益性指標の確認中にエラーが発生しました: {str(e)}")
            return False

if __name__ == "__main__":
    check_profitability_indicators('JA001', 2021)