"""
古い安全性指標を削除し、正しいコードを使って再計算するスクリプト
"""
import logging
from app import app, db
from models import AnalysisResult
from financial_indicators import FinancialIndicators

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def delete_all_safety_indicators():
    """全JAの安全性指標データを削除して再計算する"""
    ja_codes = ['JA001', 'JA002', 'JA003', 'JA004', 'JA005']
    year = 2025
    
    with app.app_context():
        for ja_code in ja_codes:
            logger.info(f"=== {ja_code}, {year}年の安全性指標を処理 ===")
            
            # 安全性指標データを削除
            try:
                deleted = AnalysisResult.query.filter_by(
                    ja_code=ja_code,
                    year=year,
                    analysis_type='safety'
                ).delete()
                
                db.session.commit()
                logger.info(f"{deleted}件の安全性指標データを削除しました")
            except Exception as e:
                logger.error(f"データ削除中にエラーが発生しました: {str(e)}")
                db.session.rollback()
                continue
            
            # 安全性指標を再計算
            try:
                result = FinancialIndicators.calculate_safety_indicators(ja_code, year)
                if result['status'] == 'success':
                    logger.info(f"安全性指標の再計算が成功しました")
                    
                    # 再計算後のデータを確認
                    indicators = result['indicators']
                    equity_ratio = indicators.get('equity_ratio', {}).get('value', 0)
                    debt_ratio = indicators.get('debt_ratio', {}).get('value', 0)
                    debt_to_equity = indicators.get('debt_to_equity', {}).get('value', 0)
                    
                    logger.info(f"自己資本比率: {equity_ratio:.2f}%")
                    logger.info(f"負債比率: {debt_ratio:.2f}%")
                    logger.info(f"負債資本比率: {debt_to_equity:.2f}%")
                else:
                    logger.error(f"再計算に失敗しました: {result.get('message', '不明なエラー')}")
            except Exception as e:
                logger.error(f"安全性指標の再計算中にエラーが発生しました: {str(e)}")
                continue

if __name__ == "__main__":
    delete_all_safety_indicators()