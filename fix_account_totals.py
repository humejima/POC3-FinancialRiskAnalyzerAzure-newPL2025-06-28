"""
勘定科目合計計算の修正スクリプト
特に現金及び預金（11000）などの合計科目の計算が正しく行われない問題を修正
"""
from app import app, db
from models import AccountFormula, StandardAccount
from account_calculator import AccountCalculator
import logging
import json

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_bs_account_formulas():
    """BS（貸借対照表）科目の計算式を修正・追加する"""
    with app.app_context():
        try:
            # 既存の計算式を確認
            existing_formulas = AccountFormula.query.filter_by(
                financial_statement="bs"
            ).all()
            
            logger.info(f"現在の計算式数: {len(existing_formulas)}")
            
            # 現金及び預金（11000）の計算式を確認・修正
            cash_deposits_formula = AccountFormula.query.filter_by(
                target_code="11000",
                financial_statement="bs"
            ).first()
            
            # 合計計算用の子科目を取得
            child_accounts = StandardAccount.query.filter_by(
                parent_code="11000",
                financial_statement="bs"
            ).all()
            
            if child_accounts:
                component_codes = [account.code for account in child_accounts]
                logger.info(f"11000（現金及び預金）の子科目: {component_codes}")
                
                if cash_deposits_formula:
                    # 既存の計算式を更新
                    cash_deposits_formula.components = json.dumps(component_codes)
                    cash_deposits_formula.formula_type = "sum"
                    cash_deposits_formula.operator = "+"
                    cash_deposits_formula.priority = 10
                    logger.info("現金及び預金（11000）の計算式を更新しました")
                else:
                    # 計算式を新規作成
                    AccountCalculator.create_formula(
                        target_code="11000",
                        target_name="現金及び預金",
                        financial_statement="bs",
                        formula_type="sum",
                        component_codes=component_codes,
                        operator="+",
                        description="現金及び預金の合計",
                        priority=10
                    )
                    logger.info("現金及び預金（11000）の計算式を新規作成しました")
            else:
                logger.warning("11000（現金及び預金）の子科目が見つかりませんでした")
            
            # 変更をコミット
            db.session.commit()
            
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"計算式の修正中にエラーが発生しました: {str(e)}")
            return False

def test_calculate_account_totals(ja_code, year):
    """
    勘定科目合計計算テスト実行
    
    Args:
        ja_code: JA code
        year: 年度
    """
    with app.app_context():
        try:
            # 計算式を修正
            fix_result = fix_bs_account_formulas()
            if not fix_result:
                logger.error("計算式の修正に失敗しました")
                return False
            
            # 勘定科目合計を計算
            count = AccountCalculator.calculate_account_totals(ja_code, year, "bs")
            logger.info(f"{count}件の勘定科目合計を計算しました")
            
            return True
        except Exception as e:
            logger.error(f"合計計算中にエラーが発生しました: {str(e)}")
            return False

if __name__ == "__main__":
    ja_code = "JA001"
    year = 2021
    
    logger.info(f"JA={ja_code}, 年度={year}の勘定科目合計計算を修正します")
    result = test_calculate_account_totals(ja_code, year)
    
    if result:
        logger.info("勘定科目合計計算の修正が完了しました")
    else:
        logger.error("勘定科目合計計算の修正に失敗しました")