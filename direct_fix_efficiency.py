from app import app, db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_efficiency_indicators_directly():
    """直接SQLを使って効率性指標のリスクスコアを修正"""
    with app.app_context():
        try:
            # リスクスコアの更新: 総資産回転率（asset_turnover）
            # 値が低いほどリスクが高い（スコア1）ように修正
            update_asset_turnover_sql = text('''
                UPDATE analysis_result 
                SET risk_score = CASE
                    WHEN indicator_value > 0.7 THEN 5
                    WHEN indicator_value > 0.5 THEN 4
                    WHEN indicator_value > 0.3 THEN 3
                    WHEN indicator_value > 0.1 THEN 2
                    ELSE 1
                END,
                risk_level = CASE
                    WHEN indicator_value > 0.7 THEN '極めて低い'
                    WHEN indicator_value > 0.5 THEN '低い'
                    WHEN indicator_value > 0.3 THEN '中程度'
                    WHEN indicator_value > 0.1 THEN '高い'
                    ELSE '極めて高い'
                END
                WHERE analysis_type = 'efficiency' 
                AND indicator_name = 'asset_turnover'
            ''')
            
            result = db.session.execute(update_asset_turnover_sql)
            updated_rows = result.rowcount
            logger.info(f"{updated_rows}件の総資産回転率のリスクスコアを更新しました")
            
            # 変更をコミット
            db.session.commit()
            
            # 現在のスコアを確認
            check_sql = text('''
                SELECT ja_code, indicator_name, indicator_value, risk_score, risk_level
                FROM analysis_result
                WHERE analysis_type = 'efficiency' AND indicator_name = 'asset_turnover'
                ORDER BY ja_code
            ''')
            
            results = db.session.execute(check_sql).fetchall()
            
            print("=== 更新後の総資産回転率のリスクスコア ===")
            for row in results:
                print(f"JA: {row[0]}, 指標: {row[1]}, 値: {row[2]}, リスクスコア: {row[3]}, リスクレベル: {row[4]}")
            
            return True
            
        except Exception as e:
            logger.error(f"効率性指標の更新中にエラーが発生しました: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    fix_efficiency_indicators_directly()