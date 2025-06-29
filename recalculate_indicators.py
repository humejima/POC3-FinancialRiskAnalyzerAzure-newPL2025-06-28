"""
既存の収益性指標の分析結果を削除し、新しい基準で再計算するスクリプト
"""
from app import app, db
from models import AnalysisResult
from financial_indicators import FinancialIndicators
import logging

# ロギングを設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recalculate_indicators(ja_code, year, analysis_type='profitability'):
    """
    特定のJAと年度の財務指標を再計算する
    
    Args:
        ja_code: JA code
        year: Financial year
        analysis_type: 指標タイプ（profitability, liquidity, safety, efficiency, cash_flow）
    """
    with app.app_context():
        # 既存の指標を削除
        deleted = db.session.query(AnalysisResult).filter_by(
            ja_code=ja_code,
            year=year,
            analysis_type=analysis_type
        ).delete()
        
        db.session.commit()
        logger.info(f"削除した{analysis_type}指標の数: {deleted}")
        
        # 新しい基準で指定された指標を再計算
        result = None
        if analysis_type == 'profitability':
            result = FinancialIndicators.calculate_profitability_indicators(ja_code, year)
        elif analysis_type == 'liquidity':
            result = FinancialIndicators.calculate_liquidity_indicators(ja_code, year)
        elif analysis_type == 'safety':
            result = FinancialIndicators.calculate_safety_indicators(ja_code, year)
        elif analysis_type == 'efficiency':
            result = FinancialIndicators.calculate_efficiency_indicators(ja_code, year)
        
        db.session.commit()
        
        logger.info(f"{analysis_type}指標の再計算結果: {result}")
        
        # 新しく計算された指標を確認
        new_indicators = db.session.query(AnalysisResult).filter_by(
            ja_code=ja_code,
            year=year,
            analysis_type=analysis_type
        ).all()
        
        for indicator in new_indicators:
            logger.info(f"指標: {indicator.indicator_name}, 値: {indicator.indicator_value}, 計算: {indicator.calculation}")
        
        return {
            'status': 'success',
            'message': f"{len(new_indicators)}個の{analysis_type}指標を再計算しました",
            'indicator_count': len(new_indicators)
        }

if __name__ == "__main__":
    # JA001の2021年度の収益性指標を再計算
    recalculate_indicators('JA001', 2021, 'profitability')