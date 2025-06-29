import logging
from app import app, db
from models import AnalysisResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_efficiency_indicators():
    """効率性指標のリスクスコアを確認"""
    with app.app_context():
        results = AnalysisResult.query.filter_by(
            ja_code='JA002',
            year=2025,
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
    check_efficiency_indicators()