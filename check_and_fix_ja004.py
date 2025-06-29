"""
JA004の安全性指標データを確認して修正するスクリプト
"""
from app import app, db
from models import AnalysisResult
from financial_indicators import FinancialIndicators
import json
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_fix_safety_data():
    """JA004の安全性指標データを確認して修正"""
    ja_code = 'JA004'
    year = 2025
    
    with app.app_context():
        # 現在のデータを確認
        results = AnalysisResult.query.filter_by(
            ja_code=ja_code,
            year=year,
            analysis_type='safety'
        ).all()
        
        logger.info(f"現在の安全性指標データ数: {len(results)}")
        for r in results:
            logger.info(f"指標: {r.indicator_name}, 値: {r.indicator_value}")
            
            # 使用科目コードを確認
            if r.accounts_used:
                try:
                    accounts = json.loads(r.accounts_used)
                    for k, v in accounts.items():
                        code = v.get('code', 'N/A')
                        name = v.get('name', 'N/A')
                        logger.info(f"  → {k}: コード={code}, 名前={name}")
                except:
                    logger.error(f"accounts_used解析エラー: {r.accounts_used[:100]}...")
        
        # データを削除するか確認
        confirm = input("これらの安全性指標データを削除して再計算しますか？(yes/no): ")
        
        if confirm.lower() == 'yes':
            # 安全性指標データを削除
            try:
                deleted = AnalysisResult.query.filter_by(
                    ja_code=ja_code,
                    year=year,
                    analysis_type='safety'
                ).delete()
                
                db.session.commit()
                logger.info(f"{deleted}件の安全性指標データを削除しました")
            except Exception as e:
                logger.error(f"データ削除中にエラーが発生しました: {str(e)}")
                db.session.rollback()
                return
            
            # 安全性指標を再計算
            try:
                logger.info("安全性指標を再計算しています...")
                result = FinancialIndicators.calculate_safety_indicators(ja_code, year)
                
                if result['status'] == 'success':
                    db.session.commit()
                    logger.info("安全性指標の再計算が成功しました")
                    
                    # 再計算後のデータを確認
                    indicators = result['indicators']
                    for name, data in indicators.items():
                        logger.info(f"指標: {name}, 値: {data['value']}")
                        
                        # 使用科目を確認
                        for comp_name, comp in data.get('components', {}).items():
                            code = comp.get('code', 'N/A')
                            comp_name = comp.get('name', 'N/A')
                            logger.info(f"  → {comp_name}: コード={code}, 名前={comp_name}")
                else:
                    logger.error(f"再計算に失敗しました: {result.get('message', '不明なエラー')}")
            except Exception as e:
                logger.error(f"安全性指標の再計算中にエラーが発生しました: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.info("処理をキャンセルしました")

if __name__ == "__main__":
    check_and_fix_safety_data()