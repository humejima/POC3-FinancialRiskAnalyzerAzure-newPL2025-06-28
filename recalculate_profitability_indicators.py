"""
収益性指標を削除して再計算するスクリプト
"""
from app import app, db
from models import AnalysisResult
from financial_indicators import FinancialIndicators
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_and_recalculate_profitability(ja_code, year):
    """
    指定されたJAと年度の収益性指標を削除して再計算する
    
    Args:
        ja_code: JA code
        year: Financial year
    """
    with app.app_context():
        # 収益性指標の削除
        deleted = AnalysisResult.query.filter_by(
            ja_code=ja_code, 
            year=year,
            analysis_type='profitability'
        ).delete()
        
        db.session.commit()
        logger.info(f"{ja_code}の{year}年度の収益性指標を{deleted}件削除しました")
        
        # 収益性指標の再計算
        result = FinancialIndicators.calculate_profitability_indicators(ja_code, year)
        
        if result.get('status') == 'success':
            logger.info(f"{ja_code}の{year}年度の収益性指標を再計算しました")
            logger.info(f"結果: {result.get('indicators', {}).keys()}")
            return True
        else:
            logger.error(f"再計算に失敗しました: {result.get('message')}")
            return False

if __name__ == "__main__":
    # JA002の2025年度の収益性指標を再計算
    success = delete_and_recalculate_profitability("JA002", 2025)
    print(f"処理完了: {'成功' if success else '失敗'}")