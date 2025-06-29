"""
すべてのJAの安全性指標データを削除して再計算するスクリプト
"""
from app import app, db
from models import AnalysisResult, JA
from financial_indicators import FinancialIndicators
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_all_safety_indicators():
    """すべてのJAの安全性指標データを削除して再計算する"""
    year = 2025
    
    with app.app_context():
        # 全JAのコードを取得
        jas = JA.query.all()
        ja_codes = [ja.code for ja in jas]
        
        if not ja_codes:
            ja_codes = ['JA001', 'JA002', 'JA003', 'JA004', 'JA005']  # デフォルト値
        
        logger.info(f"処理対象のJA: {ja_codes}")
        
        total_deleted = 0
        total_recalculated = 0
        
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
                total_deleted += deleted
                logger.info(f"{deleted}件の安全性指標データを削除しました")
            except Exception as e:
                logger.error(f"データ削除中にエラーが発生しました: {str(e)}")
                db.session.rollback()
                continue
            
            # 安全性指標を再計算
            try:
                logger.info(f"{ja_code}の安全性指標を再計算しています...")
                result = FinancialIndicators.calculate_safety_indicators(ja_code, year)
                
                if result['status'] == 'success':
                    db.session.commit()
                    total_recalculated += 1
                    logger.info(f"{ja_code}の安全性指標の再計算が成功しました")
                    
                    # 再計算後の指標値を表示
                    indicators = result['indicators']
                    for name, data in indicators.items():
                        value = data.get('value', 0)
                        logger.info(f"  - {name}: {value:.2f}")
                        
                else:
                    logger.error(f"{ja_code}の再計算に失敗しました: {result.get('message', '不明なエラー')}")
            except Exception as e:
                logger.error(f"{ja_code}の安全性指標の再計算中にエラーが発生しました: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        logger.info(f"===== 処理完了 =====")
        logger.info(f"合計 {total_deleted}件のデータを削除し、{total_recalculated}件のJAデータを再計算しました")

if __name__ == "__main__":
    update_all_safety_indicators()