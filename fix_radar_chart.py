"""
レーダーチャートの表示問題を修正するスクリプト
"""
from app import app, db
from models import AnalysisResult
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_risk_data():
    """リスク評価データを確認・表示する"""
    with app.app_context():
        # JA002の2025年の分析結果を取得
        results = AnalysisResult.query.filter_by(
            ja_code='JA002',
            year=2025
        ).all()
        
        # 分析タイプごとにグループ化
        risk_by_category = {}
        for result in results:
            if result.analysis_type not in risk_by_category:
                risk_by_category[result.analysis_type] = []
            
            if result.risk_score is not None:
                risk_by_category[result.analysis_type].append(result.risk_score)
        
        # カテゴリごとの平均スコアを計算
        category_scores = {}
        for category, scores in risk_by_category.items():
            if scores:
                category_scores[category] = sum(scores) / len(scores)
            else:
                category_scores[category] = 3.0  # デフォルト値
        
        print(f"カテゴリスコア: {json.dumps(category_scores, indent=2)}")
        
        # レーダーチャート用にスコアを反転（5が最も安全、1が最もリスク大）
        inverted_scores = {}
        categories = ['liquidity', 'safety', 'profitability', 'efficiency', 'cash_flow']
        
        print("\nレーダーチャート用データ:")
        print("カテゴリ名 | 元のスコア | 反転スコア")
        print("-" * 40)
        
        for category in categories:
            score = category_scores.get(category, 3.0)
            inverted_score = 6 - score
            inverted_scores[category] = inverted_score
            print(f"{category:12} | {score:10.2f} | {inverted_score:10.2f}")
        
        print("\nJavaScriptのレーダーチャート表示用データ:")
        labels = ['流動性', '安全性', '収益性', '効率性', 'キャッシュフロー']
        values = [inverted_scores.get(cat, 3.0) for cat in categories]
        
        print("{")
        print("  labels:", json.dumps(labels, ensure_ascii=False))
        print("  values:", json.dumps(values))
        print("}")

if __name__ == "__main__":
    check_risk_data()