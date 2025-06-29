import logging
from app import app, db
from models import AnalysisResult
from financial_indicators import FinancialIndicators

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recalculate_efficiency_indicators(ja_code='JA002', year=2025):
    """効率性指標の分析結果を削除して再計算する"""
    with app.app_context():
        # 既存の効率性指標データを削除
        deleted_count = AnalysisResult.query.filter_by(
            ja_code=ja_code,
            year=year,
            analysis_type='efficiency'
        ).delete()
        
        logger.info(f"{deleted_count}件の効率性指標データを削除しました。")
        
        # 再計算を実行
        result = FinancialIndicators.calculate_efficiency_indicators(ja_code, year)
        
        # 変更をコミット
        db.session.commit()
        
        logger.info(f"効率性指標の再計算が完了しました: {result}")
        
        # 再計算後のデータを確認
        results = AnalysisResult.query.filter_by(
            ja_code=ja_code,
            year=year,
            analysis_type='efficiency'
        ).all()
        
        for result in results:
            print(f"指標名: {result.indicator_name}")
            print(f"値: {result.indicator_value}")
            print(f"リスクスコア: {result.risk_score}")
            print(f"リスクレベル: {result.risk_level}")
            print(f"分析結果: {result.analysis_result}")
            print("-" * 50)

if __name__ == '__main__':
    recalculate_efficiency_indicators()