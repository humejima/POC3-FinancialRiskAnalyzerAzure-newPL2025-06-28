"""
勘定科目の親子関係を確認し、現在の科目合計の問題を診断するスクリプト
"""
from app import app, db
from models import StandardAccount, AccountFormula
import logging

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_parent_child_accounts():
    """
    標準勘定科目の親子関係を確認
    """
    with app.app_context():
        # 特に現金及び預金（11000）の構造を確認
        parent_account = StandardAccount.query.filter_by(
            code="11000",
            financial_statement="bs"
        ).first()
        
        if parent_account:
            logger.info(f"親科目: {parent_account.code} - {parent_account.name}")
            # 子科目を確認
            child_accounts = StandardAccount.query.filter_by(
                parent_code="11000",
                financial_statement="bs"
            ).all()
            
            if child_accounts:
                logger.info(f"子科目数: {len(child_accounts)}")
                for account in child_accounts:
                    logger.info(f"  {account.code} - {account.name}")
            else:
                logger.warning("子科目が見つかりません")
                # 親コードが設定されていない可能性がある子科目を探す
                potential_child_accounts = StandardAccount.query.filter(
                    StandardAccount.code.like("111%"),
                    StandardAccount.financial_statement == "bs"
                ).all()
                
                if potential_child_accounts:
                    logger.info("コード体系から想定される子科目:")
                    for account in potential_child_accounts:
                        logger.info(f"  {account.code} - {account.name} (親コード: {account.parent_code})")
        else:
            logger.warning("親科目（11000 - 現金及び預金）が見つかりません")
            # 対象科目があるか確認
            accounts = StandardAccount.query.filter(
                StandardAccount.code.like("11%"),
                StandardAccount.financial_statement == "bs"
            ).all()
            
            if accounts:
                logger.info("コード11で始まる科目:")
                for account in accounts:
                    logger.info(f"  {account.code} - {account.name} (親コード: {account.parent_code})")
        
        # 計算式の確認
        formulas = AccountFormula.query.filter_by(
            financial_statement="bs"
        ).all()
        
        if formulas:
            logger.info(f"計算式数: {len(formulas)}")
            for formula in formulas:
                logger.info(f"  {formula.target_code} - {formula.target_name} ({formula.formula_type}): {formula.components}")
        else:
            logger.warning("計算式が登録されていません")

if __name__ == "__main__":
    check_parent_child_accounts()