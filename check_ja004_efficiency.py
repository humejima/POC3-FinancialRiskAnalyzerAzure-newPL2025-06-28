import logging
from app import app, db
from models import AnalysisResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_ja004_efficiency(ja_code='JA004', year=2025):
    """JA004の効率性指標を確認する"""
    with app.app_context():
        results = AnalysisResult.query.filter_by(
            ja_code=ja_code,
            year=year,
            analysis_type='efficiency'
        ).all()
        
        print(f"=== JA {ja_code} の効率性指標 ===")
        if not results:
            print(f"JA {ja_code} の効率性指標データはありません")
            return
            
        for result in results:
            print(f"指標名: {result.indicator_name}")
            print(f"値: {result.indicator_value}")
            print(f"リスクスコア: {result.risk_score}")
            print(f"リスクレベル: {result.risk_level}")
            print(f"分析結果: {result.analysis_result}")
            print("-" * 50)

if __name__ == '__main__':
    check_ja004_efficiency()