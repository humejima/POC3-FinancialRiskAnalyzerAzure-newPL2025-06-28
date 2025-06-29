import logging
from app import app, db
from financial_indicators import FinancialIndicators
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_safety_indicators():
    """安全性指標の計算結果を確認するスクリプト"""
    ja_code = "JA002"
    year = 2025
    
    with app.app_context():
        logger.info(f"=== {ja_code}, {year}年の安全性指標計算テスト ===")
        
        # 安全性指標計算メソッドを呼び出す
        result = FinancialIndicators.calculate_safety_indicators(ja_code, year)
        
        # 結果を表示
        logger.info(f"安全性指標計算結果: {result['status']}")
        
        if result['status'] == 'success':
            indicators = result['indicators']
            
            # 自己資本比率
            equity_ratio = indicators['equity_ratio']['value']
            equity_components = indicators['equity_ratio']['components']
            logger.info(f"自己資本比率: {equity_ratio}%")
            logger.info(f"  - 使用科目: {json.dumps(equity_components, ensure_ascii=False)}")
            
            # 負債比率
            debt_ratio = indicators['debt_ratio']['value']
            debt_components = indicators['debt_ratio']['components']
            logger.info(f"負債比率: {debt_ratio}%")
            logger.info(f"  - 使用科目: {json.dumps(debt_components, ensure_ascii=False)}")
            
            # 負債資本比率
            debt_to_equity = indicators['debt_to_equity']['value']
            dte_components = indicators['debt_to_equity']['components']
            logger.info(f"負債資本比率: {debt_to_equity}%")
            logger.info(f"  - 使用科目: {json.dumps(dte_components, ensure_ascii=False)}")
        else:
            logger.error(f"エラー: {result['message']}")

if __name__ == "__main__":
    test_safety_indicators()