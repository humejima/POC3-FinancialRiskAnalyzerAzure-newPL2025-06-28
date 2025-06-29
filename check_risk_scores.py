import logging
from app import app
from risk_analyzer import RiskAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_risk_scores(ja_code='JA002', year=2025):
    """リスクスコアをカテゴリごとに確認"""
    with app.app_context():
        risk_assessment = RiskAnalyzer.get_overall_risk_score(ja_code, year)
        
        if risk_assessment.get('status') == 'success':
            print("カテゴリ別リスクスコア:")
            for category, score in risk_assessment.get('category_scores', {}).items():
                print(f"{category}: {score}")
            
            print(f"\n総合リスクスコア: {risk_assessment.get('overall_score')}")
            print(f"総合リスクレベル: {risk_assessment.get('overall_risk_level')}")
        else:
            print(f"エラー: {risk_assessment.get('message')}")

if __name__ == '__main__':
    check_risk_scores()