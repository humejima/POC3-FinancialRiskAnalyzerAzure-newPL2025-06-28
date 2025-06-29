"""
流動負債（21000）のデータが足りない問題を修正するスクリプト
流動負債が0の場合、リスク分析で正しい計算ができないため、25,000,000円を設定する
"""
from app import app, db
from models import StandardAccountBalance
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_flow_liabilities(ja_code='JA001', year=2021):
    """流動負債のデータを更新・設定する"""
    with app.app_context():
        try:
            # 流動負債の残高を確認
            flow_liabilities = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                standard_account_code='21000'
            ).first()
            
            if not flow_liabilities:
                # 流動負債のデータがなければ作成
                flow_liabilities = StandardAccountBalance(
                    ja_code=ja_code,
                    year=year,
                    statement_type='bs',
                    statement_subtype='BS負債',
                    standard_account_code='21000',
                    standard_account_name='流動負債',
                    current_value=25000000.0  # デモデータとして適切な値を設定
                )
                db.session.add(flow_liabilities)
                logger.info(f"流動負債(21000)を新規作成: 25,000,000円")
            elif flow_liabilities.current_value == 0:
                # 流動負債が0の場合、値を更新
                flow_liabilities.current_value = 25000000.0
                logger.info(f"流動負債(21000)を更新: 0円 → 25,000,000円")
            else:
                logger.info(f"既存の流動負債(21000): {flow_liabilities.current_value}円")
                
            db.session.commit()
            logger.info("流動負債データを正常に更新しました")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"流動負債の更新中にエラーが発生しました: {str(e)}")
            return False

if __name__ == "__main__":
    update_flow_liabilities()