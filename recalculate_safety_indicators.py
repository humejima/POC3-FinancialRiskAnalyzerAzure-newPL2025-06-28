"""
安全性指標を再計算するスクリプト
JA002の2025年の安全性指標データを再計算します
"""

from main import app
from models import db, StandardAccount, StandardAccountBalance, AnalysisResult
from financial_indicators import FinancialIndicators
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def recalculate_safety_indicators(ja_code, year):
    """安全性指標を再計算する"""
    logger.info(f"=== JA{ja_code}, {year}年の安全性指標再計算 ===")
    
    try:
        # 科目コード2900と4900の残高データを確認
        logger.info("\n科目コード2900と4900の残高データ")
        account_codes = ['2900', '4900', '5000', '5900']
        balances = db.session.query(StandardAccountBalance).filter(
            StandardAccountBalance.ja_code == ja_code,
            StandardAccountBalance.year == year,
            StandardAccountBalance.statement_type == 'bs',
            StandardAccountBalance.standard_account_code.in_(account_codes)
        ).all()
        
        if not balances:
            logger.error("BS主要科目残高データがありません")
            return "BSデータが不足しています"
            
        for balance in balances:
            logger.info(f"科目: {balance.standard_account_code} ({balance.standard_account_name}), 値: {balance.current_value:,.0f}")
            
        # 安全性指標を手動で計算
        # 総資産の取得
        total_assets_balance = db.session.query(StandardAccountBalance).filter_by(
            ja_code=ja_code,
            year=year,
            statement_type='bs',
            standard_account_code='2900'
        ).first()
        
        # 負債合計の取得
        total_liabilities_balance = db.session.query(StandardAccountBalance).filter_by(
            ja_code=ja_code,
            year=year,
            statement_type='bs',
            standard_account_code='4900'
        ).first()
        
        # 純資産合計の取得
        total_equity_balance = db.session.query(StandardAccountBalance).filter_by(
            ja_code=ja_code,
            year=year,
            statement_type='bs',
            standard_account_code='5900'
        ).first()
        
        if not total_equity_balance:
            # 純資産を直接取得できない場合は5000を試す
            total_equity_balance = db.session.query(StandardAccountBalance).filter_by(
                ja_code=ja_code,
                year=year,
                statement_type='bs',
                standard_account_code='5000'
            ).first()
        
        # 総資産値
        total_assets = total_assets_balance.current_value if total_assets_balance else 0
        total_assets_name = total_assets_balance.standard_account_name if total_assets_balance else "資産合計"
        
        # 負債合計値
        total_liabilities = total_liabilities_balance.current_value if total_liabilities_balance else 0
        total_liabilities_name = total_liabilities_balance.standard_account_name if total_liabilities_balance else "負債合計"
        
        # 純資産値
        total_equity = total_equity_balance.current_value if total_equity_balance else 0
        total_equity_name = total_equity_balance.standard_account_name if total_equity_balance else "純資産合計"
        
        # データがない場合は差額で計算
        if total_equity == 0 and total_assets > 0 and total_liabilities > 0:
            total_equity = total_assets - total_liabilities
            total_equity_name = "純資産（資産 - 負債）"
        
        logger.info(f"総資産: {total_assets:,.0f} ({total_assets_name})")
        logger.info(f"負債合計: {total_liabilities:,.0f} ({total_liabilities_name})")
        logger.info(f"純資産: {total_equity:,.0f} ({total_equity_name})")
        
        # 自己資本比率の計算
        equity_ratio = (total_equity / total_assets) * 100 if total_assets > 0 else 0
        # 負債比率の計算
        debt_ratio = (total_liabilities / total_assets) * 100 if total_assets > 0 else 0
        # 負債資本比率の計算
        debt_to_equity = (total_liabilities / total_equity) * 100 if total_equity > 0 else 0
        
        logger.info(f"手動計算の安全性指標:")
        logger.info(f"自己資本比率: {equity_ratio:.2f}%")
        logger.info(f"負債比率: {debt_ratio:.2f}%")
        logger.info(f"負債資本比率: {debt_to_equity:.2f}%")
        
        # 分析結果テーブルを直接検査
        logger.info("\n現在の分析結果テーブルの状態:")
        current_results = AnalysisResult.query.filter_by(
            ja_code=ja_code, 
            year=year, 
            analysis_type='safety'
        ).all()
        
        for res in current_results:
            logger.info(f"指標: {res.indicator_name}, 値: {res.indicator_value}, 使用勘定科目: {res.accounts_used}")
            
        # 現在の安全性指標の分析結果を削除
        deleted = AnalysisResult.query.filter_by(
            ja_code=ja_code,
            year=year,
            analysis_type='safety'
        ).delete()
        
        logger.info(f"{deleted}件の既存安全性指標データを削除しました")
        db.session.commit()
        
        # 安全性指標を再計算
        result = FinancialIndicators.calculate_safety_indicators(ja_code, year)
        logger.info(f"安全性指標再計算結果: {result}")
        
        # 再計算後のデータを確認
        results = AnalysisResult.query.filter_by(
            ja_code=ja_code,
            year=year,
            analysis_type='safety'
        ).all()
        
        logger.info(f"再計算後の安全性指標レコード数: {len(results)}")
        for result in results:
            logger.info(f"指標: {result.indicator_name}, 値: {result.indicator_value:.2f}, リスクスコア: {result.risk_score}")
        
        return f"JA{ja_code}の{year}年の安全性指標を再計算しました。"
    
    except Exception as e:
        logger.error(f"再計算中にエラーが発生しました: {str(e)}")
        db.session.rollback()
        return f"エラー: {str(e)}"

# アプリケーションコンテキスト内で実行
with app.app_context():
    # JA002の2025年の安全性指標データを再計算
    result = recalculate_safety_indicators('JA002', 2025)
    print(result)