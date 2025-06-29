"""
分析画面で流動負債の残高が正しく表示されない問題を修正するスクリプト
"""
import json
import logging
from app import app, db
from models import AnalysisResult, StandardAccountBalance

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_analysis_display(ja_code, year):
    """
    分析結果の表示用データを修正する
    
    Args:
        ja_code: JA code
        year: Financial year
    """
    with app.app_context():
        try:
            # 流動比率の分析結果を取得
            analysis_result = AnalysisResult.query.filter_by(
                ja_code=ja_code,
                year=year,
                analysis_type="liquidity",
                indicator_name="current_ratio"
            ).first()
            
            if not analysis_result:
                logger.warning(f"流動性分析の結果が見つかりません（JA={ja_code}, 年度={year}）")
                return False
            
            # 流動資産（11000）と流動負債（21000）の値をデータベースから直接取得
            current_assets = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                statement_type="bs",
                standard_account_code="11000"
            ).first()
            
            current_liabilities = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                statement_type="bs",
                standard_account_code="21000"
            ).first()
            
            if not current_assets:
                logger.warning(f"流動資産のデータが見つかりません（JA={ja_code}, 年度={year}）")
                current_assets_value = 0
            else:
                current_assets_value = current_assets.current_value or 0
                logger.info(f"流動資産の値: {current_assets_value}")
                
            if not current_liabilities:
                logger.warning(f"流動負債のデータが見つかりません（JA={ja_code}, 年度={year}）")
                current_liabilities_value = 0
            else:
                current_liabilities_value = current_liabilities.current_value or 0
                logger.info(f"流動負債の値: {current_liabilities_value}")
            
            # 現在のaccounts_usedを取得して修正
            accounts_used = json.loads(analysis_result.accounts_used) if analysis_result.accounts_used else {}
            
            # 流動資産と流動負債の表示データを更新
            accounts_used["流動資産"] = {
                "name": "流動資産(合計)",
                "value": current_assets_value
            }
            
            accounts_used["流動負債"] = {
                "name": "流動負債(合計)",
                "value": current_liabilities_value
            }
            
            # 正しい計算式を保存
            calculation = f"({current_assets_value:,.0f} ÷ {current_liabilities_value:,.0f}) × 100 = {analysis_result.indicator_value:.2f}%"
            
            # 分析結果を更新
            analysis_result.calculation = calculation
            analysis_result.accounts_used = json.dumps(accounts_used)
            
            # 変更をコミット
            db.session.commit()
            logger.info("分析結果の表示データを更新しました")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"表示データの修正中にエラーが発生しました: {str(e)}")
            return False

if __name__ == "__main__":
    ja_code = "JA001"
    year = 2021
    
    logger.info(f"JA={ja_code}, 年度={year}の分析結果表示データを修正します")
    result = fix_analysis_display(ja_code, year)
    
    if result:
        logger.info("表示データの修正が完了しました")
    else:
        logger.error("表示データの修正に失敗しました")