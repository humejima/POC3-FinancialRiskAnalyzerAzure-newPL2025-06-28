"""
収益性指標の計算で使用されるPLデータの「税引前当期利益」と
BSデータの「総資産」「純資産」の有無を確認するスクリプト
"""
from app import app, db
from models import StandardAccountBalance, AnalysisResult
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_profitability_data(ja_code='JA001', year=2025):
    """
    収益性指標の計算に使用される重要な科目の値を確認する
    """
    with app.app_context():
        try:
            # 1. PLデータの「93000: 税引前当期利益」を確認
            net_income = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                statement_type='pl',
                standard_account_code='93000'
            ).first()
            
            if net_income:
                logger.info(f"税引前当期利益(93000)の値: {net_income.current_value:,.0f}")
            else:
                logger.warning(f"税引前当期利益(93000)のデータがありません")
                
                # 代替PLデータを検索
                pl_data = StandardAccountBalance.query.filter_by(
                    ja_code=ja_code,
                    year=year,
                    statement_type='pl'
                ).all()
                
                logger.info(f"PLデータ数: {len(pl_data)}")
                for account in pl_data:
                    if '当期' in account.standard_account_name and '利益' in account.standard_account_name:
                        logger.info(f"当期利益の可能性がある科目: {account.standard_account_code} - {account.standard_account_name}: {account.current_value:,.0f}")
            
            # 2. BSデータの「10000: 総資産」を確認
            total_assets = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                statement_type='bs',
                standard_account_code='10000'
            ).first()
            
            if total_assets:
                logger.info(f"総資産(10000)の値: {total_assets.current_value:,.0f}")
            else:
                logger.warning(f"総資産(10000)のデータがありません")
                
                # 代替BSデータとして負債純資産合計(5950)を検索
                alt_assets = StandardAccountBalance.query.filter_by(
                    ja_code=ja_code,
                    year=year,
                    statement_type='bs',
                    standard_account_code='5950'
                ).first()
                
                if alt_assets:
                    logger.info(f"負債純資産合計(5950)の値: {alt_assets.current_value:,.0f}")
                else:
                    logger.warning(f"負債純資産合計(5950)のデータもありません")
            
            # 3. BSデータの「30000: 純資産」を確認
            equity = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                statement_type='bs',
                standard_account_code='30000'
            ).first()
            
            if equity:
                logger.info(f"純資産(30000)の値: {equity.current_value:,.0f}")
            else:
                logger.warning(f"純資産(30000)のデータがありません")
                
                # 代替として「資本合計」などのキーワードを含む科目を検索
                bs_data = StandardAccountBalance.query.filter_by(
                    ja_code=ja_code,
                    year=year,
                    statement_type='bs'
                ).all()
                
                for account in bs_data:
                    if '資本' in account.standard_account_name and ('合計' in account.standard_account_name or '計' in account.standard_account_name):
                        logger.info(f"資本合計の可能性がある科目: {account.standard_account_code} - {account.standard_account_name}: {account.current_value:,.0f}")
            
            # 4. 分析結果テーブルの収益性指標を確認
            profitability_results = AnalysisResult.query.filter_by(
                ja_code=ja_code,
                year=year,
                analysis_type='profitability'
            ).all()
            
            logger.info(f"収益性指標の数: {len(profitability_results)}")
            for result in profitability_results:
                logger.info(f"指標: {result.indicator_name}")
                logger.info(f"  値: {result.indicator_value}")
                logger.info(f"  計算式: {result.formula}")
                logger.info(f"  計算過程: {result.calculation}")
                logger.info(f"  使用科目: {result.accounts_used}")
                logger.info("----------")
            
            return True
            
        except Exception as e:
            logger.error(f"データ確認中にエラーが発生しました: {str(e)}")
            return False

if __name__ == "__main__":
    check_profitability_data('JA001', 2025)