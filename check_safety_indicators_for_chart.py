"""
レーダーチャート表示のための安全性指標データを確認するスクリプト
"""
from app import app, db
from models import AnalysisResult
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_safety_indicators():
    """レーダーチャート用の安全性指標データを確認する"""
    with app.app_context():
        # 安全性指標データを確認
        safety_results = AnalysisResult.query.filter_by(
            ja_code='JA002',
            year=2025,
            analysis_type='safety'
        ).all()
        
        print(f"安全性指標データ件数: {len(safety_results)}")
        
        # データ詳細を表示
        for result in safety_results:
            print(f"指標名: {result.indicator_name}, 値: {result.indicator_value}, リスクスコア: {result.risk_score}")

if __name__ == "__main__":
    check_safety_indicators()