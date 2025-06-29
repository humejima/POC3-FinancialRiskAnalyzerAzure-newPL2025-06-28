"""
勘定科目の親子関係と計算式を修正するスクリプト
"""
from app import app, db
from models import StandardAccount, AccountFormula
from account_calculator import AccountCalculator
import logging
import json
import copy

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_parent_codes():
    """
    浮動小数点になっている親コードを整数値のテキストに修正
    """
    with app.app_context():
        try:
            # 浮動小数点の親コードを持つ勘定科目を検索
            accounts = StandardAccount.query.all()
            updated_count = 0
            
            for account in accounts:
                if account.parent_code and isinstance(account.parent_code, float):
                    # 浮動小数点から整数値のテキストに変換
                    old_parent_code = account.parent_code
                    new_parent_code = str(int(account.parent_code))
                    account.parent_code = new_parent_code
                    updated_count += 1
                    logger.info(f"更新: {account.code} - {account.name}, 親コード: {old_parent_code} → {new_parent_code}")
            
            # 変更をコミット
            db.session.commit()
            logger.info(f"{updated_count}件の勘定科目の親コードを修正しました")
            return updated_count
        except Exception as e:
            db.session.rollback()
            logger.error(f"親コードの修正中にエラーが発生しました: {str(e)}")
            return 0

def create_balance_formulas():
    """
    勘定科目合計計算のための計算式を作成
    """
    with app.app_context():
        try:
            # 親子関係に基づいて計算式を作成
            created_formulas = []
            
            # 親科目を検索（親コードがNullで、子科目を持つもの）
            parent_accounts = StandardAccount.query.filter_by(
                parent_code=None,
                financial_statement="bs"
            ).all()
            
            for parent in parent_accounts:
                # 子科目を検索
                child_accounts = StandardAccount.query.filter_by(
                    parent_code=parent.code,
                    financial_statement="bs"
                ).all()
                
                if child_accounts:
                    child_codes = [child.code for child in child_accounts]
                    logger.info(f"親科目: {parent.code} - {parent.name}, 子科目数: {len(child_codes)}")
                    
                    # 計算式を作成
                    formula = AccountCalculator.create_formula(
                        target_code=parent.code,
                        target_name=parent.name,
                        financial_statement="bs",
                        formula_type="sum",
                        component_codes=child_codes,
                        operator="+",
                        description=f"{parent.name}の合計",
                        priority=10
                    )
                    
                    if formula:
                        created_formulas.append(formula)
            
            # 第2レベルの親子関係も処理
            second_level_parents = StandardAccount.query.filter(
                StandardAccount.parent_code.isnot(None),
                StandardAccount.financial_statement == "bs"
            ).all()
            
            for parent in second_level_parents:
                # 子科目を検索
                child_accounts = StandardAccount.query.filter_by(
                    parent_code=parent.code,
                    financial_statement="bs"
                ).all()
                
                if child_accounts:
                    child_codes = [child.code for child in child_accounts]
                    logger.info(f"第2レベル親科目: {parent.code} - {parent.name}, 子科目数: {len(child_codes)}")
                    
                    # 計算式を作成
                    formula = AccountCalculator.create_formula(
                        target_code=parent.code,
                        target_name=parent.name,
                        financial_statement="bs",
                        formula_type="sum",
                        component_codes=child_codes,
                        operator="+",
                        description=f"{parent.name}の合計",
                        priority=5  # 第2レベルは優先度を下げる
                    )
                    
                    if formula:
                        created_formulas.append(formula)
            
            logger.info(f"{len(created_formulas)}件の計算式を作成しました")
            return len(created_formulas)
        except Exception as e:
            logger.error(f"計算式の作成中にエラーが発生しました: {str(e)}")
            return 0

def test_calculate_totals(ja_code, year):
    """
    修正後に合計計算をテスト
    """
    with app.app_context():
        try:
            count = AccountCalculator.calculate_account_totals(ja_code, year, "bs")
            logger.info(f"{count}件の勘定科目合計を計算しました")
            return count
        except Exception as e:
            logger.error(f"合計計算中にエラーが発生しました: {str(e)}")
            return 0

if __name__ == "__main__":
    logger.info("勘定科目の親子関係と計算式を修正します")
    
    # ステップ1: 親コードの修正
    fix_parent_codes()
    
    # ステップ2: 計算式の作成
    create_balance_formulas()
    
    # ステップ3: 合計計算のテスト
    ja_code = "JA001"
    year = 2021
    test_calculate_totals(ja_code, year)
    
    logger.info("修正が完了しました")