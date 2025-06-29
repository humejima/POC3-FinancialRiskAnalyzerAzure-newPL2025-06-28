"""
流動性指標の再計算スクリプト
特に流動比率の計算に使用される流動負債の値を修正
"""
from app import app, db
from models import StandardAccountBalance, AnalysisResult
import logging

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recalculate_liquidity_ratio(ja_code, year):
    """
    流動比率（流動資産÷流動負債×100）を再計算
    
    Args:
        ja_code: JA code
        year: Financial year
    """
    with app.app_context():
        try:
            # 流動資産（11000）の値を取得
            current_assets = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                statement_type="bs",
                standard_account_code="11000"
            ).first()
            
            # 流動負債（21000）の値を取得
            current_liabilities = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                statement_type="bs",
                standard_account_code="21000"
            ).first()
            
            if not current_assets or not current_liabilities:
                logger.warning(f"流動資産または流動負債のデータが見つかりません（JA={ja_code}, 年度={year}）")
                return False
                
            # 残高を取得
            current_assets_value = current_assets.current_value or 0
            current_liabilities_value = current_liabilities.current_value or 0
            
            logger.info(f"流動資産: {current_assets_value}")
            logger.info(f"流動負債: {current_liabilities_value}")
            
            # 流動比率を計算
            if current_liabilities_value > 0:
                liquidity_ratio = (current_assets_value / current_liabilities_value) * 100
            else:
                liquidity_ratio = 0
                logger.warning("流動負債がゼロのため、流動比率を0として設定")
            
            logger.info(f"計算された流動比率: {liquidity_ratio}")
            
            # 分析結果を更新
            analysis_result = AnalysisResult.query.filter_by(
                ja_code=ja_code,
                year=year,
                analysis_type="liquidity"
            ).first()
            
            if analysis_result:
                # 既存の結果を更新
                analysis_result.value = liquidity_ratio
                analysis_result.account_values = {
                    "current_assets": current_assets_value,
                    "current_liabilities": current_liabilities_value
                }
                
                # リスクスコアを更新（値によってスコアを設定）
                if liquidity_ratio >= 200:
                    risk_score = 1  # 極めて低い
                elif liquidity_ratio >= 150:
                    risk_score = 2  # 低い
                elif liquidity_ratio >= 100:
                    risk_score = 3  # 中程度
                elif liquidity_ratio >= 50:
                    risk_score = 4  # 高い
                else:
                    risk_score = 5  # 極めて高い
                
                analysis_result.risk_score = risk_score
                
                logger.info(f"リスクスコア: {risk_score}")
                
                # 変更をコミット
                db.session.commit()
                logger.info("流動性分析の結果を更新しました")
                return True
            else:
                logger.warning("流動性分析の結果が見つかりません")
                return False
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"流動比率の再計算中にエラーが発生しました: {str(e)}")
            return False

if __name__ == "__main__":
    ja_code = "JA001"
    year = 2021
    
    logger.info(f"JA={ja_code}, 年度={year}の流動性指標を再計算します")
    result = recalculate_liquidity_ratio(ja_code, year)
    
    if result:
        logger.info("流動性指標の再計算が完了しました")
    else:
        logger.error("流動性指標の再計算に失敗しました")