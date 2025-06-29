import logging
from app import app, db
from models import JA, AnalysisResult
from financial_indicators import FinancialIndicators

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recalculate_all_ja_efficiency(year=2025):
    """すべてのJAの効率性指標を削除して再計算する"""
    with app.app_context():
        # すべてのJAコードを取得
        ja_list = JA.query.all()
        
        for ja in ja_list:
            ja_code = ja.ja_code
            
            # 既存の効率性指標データを削除
            deleted_count = AnalysisResult.query.filter_by(
                ja_code=ja_code,
                year=year,
                analysis_type='efficiency'
            ).delete()
            
            logger.info(f"JA {ja_code}: {deleted_count}件の効率性指標データを削除しました。")
            
            # 再計算を実行
            try:
                result = FinancialIndicators.calculate_efficiency_indicators(ja_code, year)
                logger.info(f"JA {ja_code}: 効率性指標の再計算が完了しました。")
            except Exception as e:
                logger.error(f"JA {ja_code}: 効率性指標の再計算中にエラーが発生しました: {str(e)}")
                continue
        
        # 変更をコミット
        db.session.commit()
        logger.info(f"すべてのJAの効率性指標の再計算が完了しました。")
        
        # 各JAの効率性スコアを確認
        for ja in ja_list:
            ja_code = ja.ja_code
            
            # 効率性スコアを確認
            results = AnalysisResult.query.filter_by(
                ja_code=ja_code,
                year=year,
                analysis_type='efficiency'
            ).all()
            
            print(f"=== JA {ja_code} の効率性指標 ===")
            if not results:
                print("データがありません")
                continue
                
            for result in results:
                print(f"指標名: {result.indicator_name}")
                print(f"値: {result.indicator_value}")
                print(f"リスクスコア: {result.risk_score}")
                print(f"リスクレベル: {result.risk_level}")
                print("-" * 30)

if __name__ == '__main__':
    recalculate_all_ja_efficiency()