import logging
from app import app, db
from financial_indicators import FinancialIndicators

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_bs_account_values():
    """BS勘定科目の値を確認するスクリプト"""
    ja_code = "JA002"
    year = 2025
    
    with app.app_context():
        logger.info(f"=== {ja_code}, {year}年のBS勘定科目値確認 ===")
        
        # 変更前のコード
        total_assets_old, name_old = FinancialIndicators.get_account_value(ja_code, year, "bs", "2999")
        total_liab_old, liab_name_old = FinancialIndicators.get_account_value(ja_code, year, "bs", "4999")
        
        # 変更後の正しいコード
        total_assets, name = FinancialIndicators.get_account_value(ja_code, year, "bs", "2900")
        total_liab, liab_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "4900")
        total_equity, equity_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "5900")
        
        logger.info("変更前のコード:")
        logger.info(f"科目: 2999 (資産の部合計), 値: {total_assets_old:,.0f}, 名前: {name_old}")
        logger.info(f"科目: 4999 (負債の部合計), 値: {total_liab_old:,.0f}, 名前: {liab_name_old}")
        
        logger.info("\n変更後の正しいコード:")
        logger.info(f"科目: 2900 (資産の部合計), 値: {total_assets:,.0f}, 名前: {name}")
        logger.info(f"科目: 4900 (負債の部合計), 値: {total_liab:,.0f}, 名前: {liab_name}")
        logger.info(f"科目: 5900 (純資産の部合計), 値: {total_equity:,.0f}, 名前: {equity_name}")
        
        # 安全性指標の手動計算
        equity_ratio = (total_equity / total_assets) * 100 if total_assets > 0 else 0
        debt_ratio = (total_liab / total_assets) * 100 if total_assets > 0 else 0
        debt_to_equity = (total_liab / total_equity) * 100 if total_equity > 0 else 0
        
        logger.info("\n手動計算の安全性指標:")
        logger.info(f"自己資本比率: {equity_ratio:.2f}%")
        logger.info(f"負債比率: {debt_ratio:.2f}%")
        logger.info(f"負債資本比率: {debt_to_equity:.2f}%")

if __name__ == "__main__":
    test_bs_account_values()